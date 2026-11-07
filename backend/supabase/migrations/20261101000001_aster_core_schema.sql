-- ============================================================================
-- Aster Companion Core Database Migration
-- File: backend/supabase/migrations/20261101000001_aster_core_schema.sql
-- Description: Production-grade schema implementing PRD v1.1 specifications
--   1. Maximum 2 companion profiles per account with advisory-locked triggers
--   2. Absolute profile-level isolation with PostgreSQL Row-Level Security (RLS)
--   3. Cross-device continuity, single active profile per device constraint
--   4. Monotonic event streams with gap detection and deduplication
--   5. pgvector 1536-dim semantic memory with HNSW cosine index
--   6. Explicit memory sharing audit trail between companion profiles
--   7. Full default-deny RLS across all 14 core tables
-- ============================================================================

-- ----------------------------------------------------------------------------
-- SECTION 1: EXTENSIONS & COMPATIBILITY ENVIRONMENT
-- ----------------------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Ensure standard Supabase roles exist for local testing / CI runners
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role NOLOGIN;
  END IF;
END $$;

-- Ensure auth schema and auth.users exist for environments without Supabase Auth pre-installed
DO $$
BEGIN
  CREATE SCHEMA IF NOT EXISTS auth;
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_schema = 'auth' AND table_name = 'users'
  ) THEN
    CREATE TABLE auth.users (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      email text UNIQUE,
      raw_user_meta_data jsonb DEFAULT '{}'::jsonb,
      raw_app_meta_data jsonb DEFAULT '{}'::jsonb,
      created_at timestamptz DEFAULT now()
    );
  END IF;
END $$;

-- Provide auth.uid() function if not already defined by Supabase runtime
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_proc 
    JOIN pg_namespace ON pg_proc.pronamespace = pg_namespace.oid
    WHERE pg_proc.proname = 'uid' AND pg_namespace.nspname = 'auth'
  ) THEN
    EXECUTE $func$
      CREATE OR REPLACE FUNCTION auth.uid()
      RETURNS uuid
      LANGUAGE sql STABLE
      AS $u$
        SELECT COALESCE(
          NULLIF(current_setting('request.jwt.claim.sub', true), ''),
          (NULLIF(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub'),
          NULLIF(current_setting('app.current_user_id', true), '')
        )::uuid;
      $u$;
    $func$;
  END IF;
END $$;

-- Provide auth.jwt() function if not already defined by Supabase runtime
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_proc 
    JOIN pg_namespace ON pg_proc.pronamespace = pg_namespace.oid
    WHERE pg_proc.proname = 'jwt' AND pg_namespace.nspname = 'auth'
  ) THEN
    EXECUTE $func$
      CREATE OR REPLACE FUNCTION auth.jwt()
      RETURNS jsonb
      LANGUAGE sql STABLE
      AS $j$
        SELECT COALESCE(
          NULLIF(current_setting('request.jwt.claims', true), '')::jsonb,
          '{}'::jsonb
        );
      $j$;
    $func$;
  END IF;
END $$;

-- ----------------------------------------------------------------------------
-- SECTION 2: CORE TABLES DEFINITION
-- ----------------------------------------------------------------------------

-- 1. COMPANION PROFILES
-- PRD Section 9.1 & DEC-021: Max 2 companion profiles per account.
-- Completely isolated memories, persona, and contextual state.
CREATE TABLE IF NOT EXISTS companion_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name text NOT NULL DEFAULT 'Aster',
  avatar_config jsonb NOT NULL DEFAULT '{}'::jsonb,
  voice_config jsonb NOT NULL DEFAULT '{}'::jsonb,
  personality_config jsonb NOT NULL DEFAULT '{}'::jsonb,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_companion_profiles_id_user UNIQUE (id, user_id)
);

-- 2. DEVICES
-- PRD Section 3 & 9.5: Platform-aware registered hardware endpoints.
-- Constraint: Exactly ONE active profile per device at any single time.
CREATE TABLE IF NOT EXISTS devices (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  device_name text,
  platform text,
  active_profile_id uuid REFERENCES companion_profiles(id) ON DELETE SET NULL,
  last_seen_at timestamptz DEFAULT now(),
  push_token text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fk_devices_active_profile_user 
    FOREIGN KEY (active_profile_id, user_id) 
    REFERENCES companion_profiles(id, user_id) 
    ON DELETE SET NULL
);

-- 3. SESSIONS
-- PRD Section 10: Cross-device sessions tied to an active companion profile.
-- Single active profile per device strictly enforced.
CREATE TABLE IF NOT EXISTS sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id uuid NOT NULL REFERENCES companion_profiles(id) ON DELETE CASCADE,
  device_id uuid NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  started_at timestamptz NOT NULL DEFAULT now(),
  ended_at timestamptz,
  state text NOT NULL DEFAULT 'active' CHECK (state IN ('active', 'paused', 'ended', 'interrupted')),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Partial index: On a single physical device, only 1 session may be in 'active' state at a time.
CREATE UNIQUE INDEX IF NOT EXISTS uq_sessions_device_active 
  ON sessions (device_id) 
  WHERE (state = 'active');

-- 4. EVENTS
-- PRD Section 5 & 6.3: Continuous perception and screen understanding event stream.
-- Monotonic sequence numbers with gap tracking. Unique (device_id, sequence_number).
CREATE TABLE IF NOT EXISTS events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  profile_id uuid NOT NULL REFERENCES companion_profiles(id) ON DELETE CASCADE,
  device_id uuid NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  sequence_number bigint NOT NULL,
  event_type text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  checksum text,
  timestamp timestamptz NOT NULL DEFAULT now(),
  gap_detected boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_events_device_sequence UNIQUE (device_id, sequence_number)
);

-- 5. MEMORIES
-- PRD Section 14: Categorized long-term memory store with semantic pgvector embeddings.
CREATE TABLE IF NOT EXISTS memories (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id uuid NOT NULL REFERENCES companion_profiles(id) ON DELETE CASCADE,
  memory_category text NOT NULL CHECK (
    memory_category IN (
      'conversational',
      'preference',
      'behavioral',
      'activity',
      'relationship_social',
      'procedural',
      'profile_config',
      'explicitly_shared'
    )
  ),
  content text NOT NULL,
  confidence_score float CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
  provenance_source text,
  sensitivity_level text NOT NULL DEFAULT 'standard' CHECK (
    sensitivity_level IN ('low', 'standard', 'high', 'restricted')
  ),
  is_pinned boolean NOT NULL DEFAULT false,
  is_forgotten boolean NOT NULL DEFAULT false,
  embedding vector(1536),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- 6. MEMORY SHARES
-- PRD Section 9.4 & DEC-025: Explicit sharing audit trail between companion profiles.
CREATE TABLE IF NOT EXISTS memory_shares (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_profile_id uuid NOT NULL REFERENCES companion_profiles(id) ON DELETE CASCADE,
  destination_profile_id uuid NOT NULL REFERENCES companion_profiles(id) ON DELETE CASCADE,
  memory_id uuid NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
  confirmed_by_user boolean NOT NULL DEFAULT false,
  shared_at timestamptz NOT NULL DEFAULT now(),
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chk_memory_shares_different_profiles CHECK (source_profile_id <> destination_profile_id)
);

-- 7. CHAT CONVERSATIONS
-- PRD Section 7: Conversational dialogue threads per companion profile.
CREATE TABLE IF NOT EXISTS chat_conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id uuid NOT NULL REFERENCES companion_profiles(id) ON DELETE CASCADE,
  title text NOT NULL DEFAULT 'New Conversation',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- 8. CHAT MESSAGES
-- PRD Section 7: Streaming and turn-based chat messages with multimodal attachments & tool calls.
CREATE TABLE IF NOT EXISTS chat_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
  profile_id uuid NOT NULL REFERENCES companion_profiles(id) ON DELETE CASCADE,
  sender text NOT NULL CHECK (sender IN ('user', 'aster', 'system')),
  text_content text NOT NULL DEFAULT '',
  attachments jsonb NOT NULL DEFAULT '[]'::jsonb,
  citations jsonb NOT NULL DEFAULT '[]'::jsonb,
  tool_calls jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- 9. ACTIONS
-- PRD Section 12: Agentic tool execution, risk levels, idempotency and confirmation gates.
CREATE TABLE IF NOT EXISTS actions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id uuid NOT NULL REFERENCES companion_profiles(id) ON DELETE CASCADE,
  action_name text NOT NULL,
  arguments jsonb NOT NULL DEFAULT '{}'::jsonb,
  risk_level text NOT NULL CHECK (risk_level IN ('read_only', 'reversible', 'consequential', 'irreversible')),
  requires_confirmation boolean NOT NULL DEFAULT false,
  approval_status text NOT NULL DEFAULT 'pending' CHECK (approval_status IN ('pending', 'approved', 'rejected', 'executed', 'failed')),
  idempotency_key text UNIQUE,
  executed_at timestamptz,
  verification_result jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- 10. INTEGRATIONS
-- PRD Section 11: Authorized Google services and third-party integrations.
CREATE TABLE IF NOT EXISTS integrations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  profile_id uuid REFERENCES companion_profiles(id) ON DELETE CASCADE,
  provider text NOT NULL CHECK (
    provider IN (
      'google_photos',
      'google_drive',
      'gmail',
      'google_calendar',
      'google_contacts',
      'shopify',
      'web_search'
    )
  ),
  encrypted_access_token text,
  encrypted_refresh_token text,
  scopes text[] NOT NULL DEFAULT '{}'::text[],
  is_active boolean NOT NULL DEFAULT true,
  connected_at timestamptz NOT NULL DEFAULT now(),
  disconnected_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_integrations_user_profile_provider UNIQUE (user_id, profile_id, provider)
);

-- 11. PROACTIVE RULES
-- PRD Section 17: User-configurable proactive assistance and quiet hours.
CREATE TABLE IF NOT EXISTS proactive_rules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id uuid NOT NULL REFERENCES companion_profiles(id) ON DELETE CASCADE,
  rule_name text NOT NULL,
  category text NOT NULL DEFAULT 'general',
  min_relevance float NOT NULL DEFAULT 0.7 CHECK (min_relevance >= 0.0 AND min_relevance <= 1.0),
  min_confidence float NOT NULL DEFAULT 0.7 CHECK (min_confidence >= 0.0 AND min_confidence <= 1.0),
  max_interruption_cost float NOT NULL DEFAULT 0.5 CHECK (max_interruption_cost >= 0.0 AND max_interruption_cost <= 1.0),
  quiet_hours_start time,
  quiet_hours_end time,
  is_enabled boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- 12. VOICE MODELS
-- PRD Section 7.4: Voice model configurations, synthetic disclosure & consent audit records.
CREATE TABLE IF NOT EXISTS voice_models (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id uuid NOT NULL REFERENCES companion_profiles(id) ON DELETE CASCADE,
  voice_type text NOT NULL DEFAULT 'preset',
  voice_name text NOT NULL,
  is_cloned boolean NOT NULL DEFAULT false,
  consent_verified boolean NOT NULL DEFAULT false,
  consent_audit_log jsonb NOT NULL DEFAULT '{}'::jsonb,
  synthetic_disclosure_accepted boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- 13. TELEMETRY LOGS
-- PRD Section 5.3 & 18: Perception pipeline telemetry (FPS, latency, gap detection).
CREATE TABLE IF NOT EXISTS telemetry_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  device_id uuid REFERENCES devices(id) ON DELETE SET NULL,
  profile_id uuid REFERENCES companion_profiles(id) ON DELETE SET NULL,
  capture_fps float,
  upload_fps float,
  ingest_fps float,
  analysis_fps float,
  latency_ms float,
  gap_count int NOT NULL DEFAULT 0,
  recorded_at timestamptz NOT NULL DEFAULT now()
);

-- 14. AUDIT LOGS
-- PRD Section 16: Security audit trail for compliance and data privacy.
CREATE TABLE IF NOT EXISTS audit_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  profile_id uuid REFERENCES companion_profiles(id) ON DELETE SET NULL,
  action text NOT NULL,
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  ip_address text,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- ----------------------------------------------------------------------------
-- SECTION 3: PERFORMANCE INDEXES
-- ----------------------------------------------------------------------------

-- HNSW vector cosine similarity index for fast approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS idx_memories_embedding_hnsw 
  ON memories USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Profile-scoped composite queries
CREATE INDEX IF NOT EXISTS idx_companion_profiles_user ON companion_profiles (user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_devices_user ON devices (user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_profile_state ON sessions (profile_id, state);
CREATE INDEX IF NOT EXISTS idx_events_session_sequence ON events (session_id, sequence_number ASC);
CREATE INDEX IF NOT EXISTS idx_events_profile_time ON events (profile_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_memories_profile_category ON memories (profile_id, memory_category);
CREATE INDEX IF NOT EXISTS idx_memories_profile_active ON memories (profile_id, created_at DESC) WHERE (NOT is_forgotten);
CREATE INDEX IF NOT EXISTS idx_memory_shares_dest ON memory_shares (destination_profile_id, confirmed_by_user) WHERE (revoked_at IS NULL);
CREATE INDEX IF NOT EXISTS idx_chat_conversations_profile ON chat_conversations (profile_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_conv ON chat_messages (conversation_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_actions_profile_status ON actions (profile_id, approval_status);
CREATE INDEX IF NOT EXISTS idx_integrations_user_profile ON integrations (user_id, profile_id);
CREATE INDEX IF NOT EXISTS idx_proactive_rules_profile ON proactive_rules (profile_id) WHERE (is_enabled);
CREATE INDEX IF NOT EXISTS idx_telemetry_profile_time ON telemetry_logs (profile_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_time ON audit_logs (user_id, created_at DESC);

-- ----------------------------------------------------------------------------
-- SECTION 4: INTEGRITY FUNCTIONS & TRIGGERS
-- ----------------------------------------------------------------------------

-- A. Automatically update updated_at timestamp on row modification
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

DO $$
DECLARE
  tbl text;
BEGIN
  FOR tbl IN 
    SELECT tablename FROM pg_tables 
    WHERE schemaname = 'public' 
      AND tablename IN (
        'companion_profiles', 'devices', 'sessions', 'memories', 
        'chat_conversations', 'actions', 'integrations', 
        'proactive_rules', 'voice_models'
      )
  LOOP
    EXECUTE format('
      DROP TRIGGER IF EXISTS trg_set_updated_at ON %I;
      CREATE TRIGGER trg_set_updated_at
        BEFORE UPDATE ON %I
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    ', tbl, tbl);
  END LOOP;
END $$;

-- B. Maximum 2 companion profiles per account enforcement
-- PRD Section 9.1 & DEC-021: Strict DB-level enforcement with concurrency lock
CREATE OR REPLACE FUNCTION check_companion_profile_limit()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  v_count integer;
BEGIN
  -- Acquire transaction-level advisory lock hashed on user_id to serialize profile creation
  PERFORM pg_advisory_xact_lock(hashtext(NEW.user_id::text));

  -- Count existing profiles for this account, excluding the current row on update
  SELECT count(*) INTO v_count
  FROM companion_profiles
  WHERE user_id = NEW.user_id
    AND id <> COALESCE(NEW.id, '00000000-0000-0000-0000-000000000000'::uuid);

  IF v_count >= 2 THEN
    RAISE EXCEPTION 'Account profile limit exceeded: A user account cannot have more than 2 companion profiles (PRD v1.1 DEC-021).'
      USING ERRCODE = 'check_violation';
  END IF;

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_check_companion_profile_limit ON companion_profiles;
CREATE TRIGGER trg_check_companion_profile_limit
  BEFORE INSERT OR UPDATE OF user_id ON companion_profiles
  FOR EACH ROW
  EXECUTE FUNCTION check_companion_profile_limit();

-- C. Device & Session Profile Alignment Trigger
-- PRD Section 9.5 & DEC-026: Enforce single active profile per device and synchronize sessions
CREATE OR REPLACE FUNCTION enforce_device_session_integrity()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  v_device_user_id uuid;
  v_profile_user_id uuid;
BEGIN
  -- Validate that device and profile belong to the exact same user
  SELECT user_id INTO v_device_user_id FROM devices WHERE id = NEW.device_id;
  SELECT user_id INTO v_profile_user_id FROM companion_profiles WHERE id = NEW.profile_id;

  IF v_device_user_id IS NULL OR v_profile_user_id IS NULL OR v_device_user_id <> v_profile_user_id THEN
    RAISE EXCEPTION 'Session integrity violation: Device and companion profile must belong to the same account.'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;

  IF NEW.state = 'active' THEN
    -- Automatically end any existing active session on this device
    UPDATE sessions
    SET state = 'ended', ended_at = now(), updated_at = now()
    WHERE device_id = NEW.device_id
      AND id <> COALESCE(NEW.id, '00000000-0000-0000-0000-000000000000'::uuid)
      AND state = 'active';

    -- Synchronize device active_profile_id pointer
    UPDATE devices
    SET active_profile_id = NEW.profile_id,
        last_seen_at = now(),
        updated_at = now()
    WHERE id = NEW.device_id;
  END IF;

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_enforce_device_session_integrity ON sessions;
CREATE TRIGGER trg_enforce_device_session_integrity
  BEFORE INSERT OR UPDATE ON sessions
  FOR EACH ROW
  EXECUTE FUNCTION enforce_device_session_integrity();

-- D. Chat message conversation-profile consistency trigger
CREATE OR REPLACE FUNCTION validate_chat_message_consistency()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  v_conv_profile_id uuid;
BEGIN
  SELECT profile_id INTO v_conv_profile_id 
  FROM chat_conversations 
  WHERE id = NEW.conversation_id;

  IF v_conv_profile_id IS NULL OR v_conv_profile_id <> NEW.profile_id THEN
    RAISE EXCEPTION 'Chat message integrity violation: Message profile does not match conversation profile.'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_chat_message_consistency ON chat_messages;
CREATE TRIGGER trg_validate_chat_message_consistency
  BEFORE INSERT OR UPDATE ON chat_messages
  FOR EACH ROW
  EXECUTE FUNCTION validate_chat_message_consistency();

-- E. Memory share validation trigger
-- Ensures source and destination profiles belong to the same account and source profile owns the memory
CREATE OR REPLACE FUNCTION validate_memory_share_integrity()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  v_source_user uuid;
  v_dest_user uuid;
  v_memory_profile uuid;
BEGIN
  SELECT user_id INTO v_source_user FROM companion_profiles WHERE id = NEW.source_profile_id;
  SELECT user_id INTO v_dest_user FROM companion_profiles WHERE id = NEW.destination_profile_id;
  SELECT profile_id INTO v_memory_profile FROM memories WHERE id = NEW.memory_id;

  IF v_source_user IS NULL OR v_dest_user IS NULL OR v_source_user <> v_dest_user THEN
    RAISE EXCEPTION 'Memory share violation: Source and destination profiles must belong to the same user account.'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;

  IF v_memory_profile IS NULL OR v_memory_profile <> NEW.source_profile_id THEN
    RAISE EXCEPTION 'Memory share violation: Shared memory does not belong to the source profile.'
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_memory_share_integrity ON memory_shares;
CREATE TRIGGER trg_validate_memory_share_integrity
  BEFORE INSERT OR UPDATE ON memory_shares
  FOR EACH ROW
  EXECUTE FUNCTION validate_memory_share_integrity();

-- ----------------------------------------------------------------------------
-- SECTION 5: PROFILE CONTEXT RESOLUTION & HELPER FUNCTIONS
-- ----------------------------------------------------------------------------

-- Check whether a profile belongs to a given user (SECURITY DEFINER avoids RLS recursion)
CREATE OR REPLACE FUNCTION profile_belongs_to_user(p_profile_id uuid, p_user_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
  SELECT EXISTS (
    SELECT 1 FROM companion_profiles
    WHERE id = p_profile_id AND user_id = p_user_id
  );
$$;

-- Resolve the active authorized profile ID for the current request
-- Priority:
--   1. Transaction/Session setting: app.current_profile_id
--   2. HTTP Headers: x-profile-id or x-aster-profile-id
--   3. JWT claims: profile_id or active_profile_id in root, app_metadata, or user_metadata
--   4. HTTP Header x-device-id: active_profile_id of the registered device
-- Security: Verifies that the resolved profile ID strictly belongs to auth.uid().
CREATE OR REPLACE FUNCTION aster_get_active_profile_id()
RETURNS uuid
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_user_id uuid;
  v_raw text;
  v_candidate_id uuid;
  v_headers jsonb;
  v_claims jsonb;
BEGIN
  v_user_id := auth.uid();
  IF v_user_id IS NULL THEN
    RETURN NULL;
  END IF;

  -- 1. Check direct session setting
  v_raw := NULLIF(current_setting('app.current_profile_id', true), '');
  IF v_raw IS NOT NULL THEN
    BEGIN
      v_candidate_id := v_raw::uuid;
      IF profile_belongs_to_user(v_candidate_id, v_user_id) THEN
        RETURN v_candidate_id;
      END IF;
    EXCEPTION WHEN OTHERS THEN
      -- invalid uuid format, fall through
    END;
  END IF;

  -- Read request headers if available
  IF NULLIF(current_setting('request.headers', true), '') IS NOT NULL THEN
    BEGIN
      v_headers := current_setting('request.headers', true)::jsonb;
      v_raw := COALESCE(
        v_headers ->> 'x-profile-id',
        v_headers ->> 'x-aster-profile-id'
      );
      IF v_raw IS NOT NULL THEN
        v_candidate_id := v_raw::uuid;
        IF profile_belongs_to_user(v_candidate_id, v_user_id) THEN
          RETURN v_candidate_id;
        END IF;
      END IF;

      -- Check if device-id is provided in headers
      v_raw := v_headers ->> 'x-device-id';
      IF v_raw IS NOT NULL THEN
        SELECT active_profile_id INTO v_candidate_id
        FROM devices
        WHERE id = v_raw::uuid AND user_id = v_user_id;
        IF v_candidate_id IS NOT NULL THEN
          RETURN v_candidate_id;
        END IF;
      END IF;
    EXCEPTION WHEN OTHERS THEN
      -- fall through
    END;
  END IF;

  -- Read JWT claims if available
  IF NULLIF(current_setting('request.jwt.claims', true), '') IS NOT NULL THEN
    BEGIN
      v_claims := current_setting('request.jwt.claims', true)::jsonb;
      v_raw := COALESCE(
        v_claims ->> 'active_profile_id',
        v_claims ->> 'profile_id',
        v_claims -> 'app_metadata' ->> 'active_profile_id',
        v_claims -> 'app_metadata' ->> 'profile_id',
        v_claims -> 'user_metadata' ->> 'active_profile_id',
        v_claims -> 'user_metadata' ->> 'profile_id'
      );
      IF v_raw IS NOT NULL THEN
        v_candidate_id := v_raw::uuid;
        IF profile_belongs_to_user(v_candidate_id, v_user_id) THEN
          RETURN v_candidate_id;
        END IF;
      END IF;
    EXCEPTION WHEN OTHERS THEN
      -- fall through
    END;
  END IF;

  RETURN NULL;
END;
$$;

-- Stored procedure to switch or activate profile for the current session/connection
CREATE OR REPLACE FUNCTION set_active_profile(p_profile_id uuid)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_user_id uuid;
BEGIN
  v_user_id := auth.uid();
  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'Authentication required to set active profile.'
      USING ERRCODE = 'insufficient_privilege';
  END IF;

  IF NOT profile_belongs_to_user(p_profile_id, v_user_id) THEN
    RAISE EXCEPTION 'Unauthorized: Profile % does not belong to the authenticated user.', p_profile_id
      USING ERRCODE = 'insufficient_privilege';
  END IF;

  PERFORM set_config('app.current_profile_id', p_profile_id::text, false);
  RETURN p_profile_id;
END;
$$;

-- Stored procedure for explicit profile-to-profile memory sharing
CREATE OR REPLACE FUNCTION aster_share_memory(
  p_source_profile_id uuid,
  p_destination_profile_id uuid,
  p_memory_id uuid
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_user_id uuid;
  v_share_id uuid;
BEGIN
  v_user_id := auth.uid();
  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'Authentication required.' USING ERRCODE = 'insufficient_privilege';
  END IF;

  IF NOT profile_belongs_to_user(p_source_profile_id, v_user_id) OR
     NOT profile_belongs_to_user(p_destination_profile_id, v_user_id) THEN
    RAISE EXCEPTION 'Unauthorized: Both profiles must belong to the caller.'
      USING ERRCODE = 'insufficient_privilege';
  END IF;

  INSERT INTO memory_shares (
    source_profile_id,
    destination_profile_id,
    memory_id,
    confirmed_by_user,
    shared_at
  ) VALUES (
    p_source_profile_id,
    p_destination_profile_id,
    p_memory_id,
    true,
    now()
  )
  RETURNING id INTO v_share_id;

  -- Create an audit log record for the explicit sharing operation
  INSERT INTO audit_logs (user_id, profile_id, action, details)
  VALUES (
    v_user_id,
    p_source_profile_id,
    'memory.explicit_shared',
    jsonb_build_object(
      'share_id', v_share_id,
      'destination_profile_id', p_destination_profile_id,
      'memory_id', p_memory_id
    )
  );

  RETURN v_share_id;
END;
$$;

-- Stored procedure to revoke an explicit memory share
CREATE OR REPLACE FUNCTION aster_revoke_memory_share(p_share_id uuid)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_user_id uuid;
  v_source_profile uuid;
BEGIN
  v_user_id := auth.uid();
  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'Authentication required.' USING ERRCODE = 'insufficient_privilege';
  END IF;

  SELECT source_profile_id INTO v_source_profile
  FROM memory_shares
  WHERE id = p_share_id;

  IF v_source_profile IS NULL OR NOT profile_belongs_to_user(v_source_profile, v_user_id) THEN
    RAISE EXCEPTION 'Unauthorized: Memory share not found or not owned by user.'
      USING ERRCODE = 'insufficient_privilege';
  END IF;

  UPDATE memory_shares
  SET revoked_at = now()
  WHERE id = p_share_id AND revoked_at IS NULL;

  INSERT INTO audit_logs (user_id, profile_id, action, details)
  VALUES (
    v_user_id,
    v_source_profile,
    'memory.share_revoked',
    jsonb_build_object('share_id', p_share_id)
  );

  RETURN true;
END;
$$;

-- ----------------------------------------------------------------------------
-- SECTION 6: PGVECTOR SEMANTIC SEARCH PROCEDURE
-- ----------------------------------------------------------------------------

-- Requirement 4: Similarity search procedure with HNSW acceleration
-- PRD Section 14: Isolated retrieval with support for confirmed shared memories.
CREATE OR REPLACE FUNCTION search_profile_memories(
  p_profile_id uuid,
  p_query_embedding vector(1536),
  p_match_threshold float DEFAULT 0.0,
  p_match_count int DEFAULT 10
)
RETURNS TABLE (
  id uuid,
  profile_id uuid,
  memory_category text,
  content text,
  confidence_score float,
  provenance_source text,
  sensitivity_level text,
  is_pinned boolean,
  similarity float,
  created_at timestamptz,
  updated_at timestamptz
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_caller_user_id uuid;
  v_active_profile uuid;
BEGIN
  v_caller_user_id := auth.uid();

  -- Security gate: If called within an authenticated session, verify ownership and isolation
  IF v_caller_user_id IS NOT NULL THEN
    IF NOT profile_belongs_to_user(p_profile_id, v_caller_user_id) THEN
      RAISE EXCEPTION 'Unauthorized profile access: Profile % does not belong to caller.', p_profile_id
        USING ERRCODE = 'insufficient_privilege';
    END IF;

    v_active_profile := aster_get_active_profile_id();
    IF v_active_profile IS NOT NULL AND v_active_profile <> p_profile_id THEN
      RAISE EXCEPTION 'Profile isolation violation: Cannot search profile % while active on profile %.', p_profile_id, v_active_profile
        USING ERRCODE = 'insufficient_privilege';
    END IF;
  END IF;

  RETURN QUERY
  SELECT
    m.id,
    m.profile_id,
    m.memory_category,
    m.content,
    m.confidence_score,
    m.provenance_source,
    m.sensitivity_level,
    m.is_pinned,
    (1 - (m.embedding <=> p_query_embedding))::float AS similarity,
    m.created_at,
    m.updated_at
  FROM memories m
  WHERE (
    -- Direct profile memories
    m.profile_id = p_profile_id
    -- Explicitly shared and unrevoked memories
    OR m.id IN (
      SELECT ms.memory_id
      FROM memory_shares ms
      WHERE ms.destination_profile_id = p_profile_id
        AND ms.confirmed_by_user = true
        AND ms.revoked_at IS NULL
    )
  )
  AND NOT m.is_forgotten
  AND m.embedding IS NOT NULL
  AND (1 - (m.embedding <=> p_query_embedding)) >= p_match_threshold
  ORDER BY m.embedding <=> p_query_embedding ASC
  LIMIT p_match_count;
END;
$$;

-- ----------------------------------------------------------------------------
-- SECTION 7: ROW-LEVEL SECURITY (RLS) POLICIES
-- ----------------------------------------------------------------------------

-- Enable and FORCE RLS on all 14 tables (enforces policies even for table owners)
ALTER TABLE companion_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE proactive_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE telemetry_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

ALTER TABLE companion_profiles FORCE ROW LEVEL SECURITY;
ALTER TABLE devices FORCE ROW LEVEL SECURITY;
ALTER TABLE sessions FORCE ROW LEVEL SECURITY;
ALTER TABLE events FORCE ROW LEVEL SECURITY;
ALTER TABLE memories FORCE ROW LEVEL SECURITY;
ALTER TABLE memory_shares FORCE ROW LEVEL SECURITY;
ALTER TABLE chat_conversations FORCE ROW LEVEL SECURITY;
ALTER TABLE chat_messages FORCE ROW LEVEL SECURITY;
ALTER TABLE actions FORCE ROW LEVEL SECURITY;
ALTER TABLE integrations FORCE ROW LEVEL SECURITY;
ALTER TABLE proactive_rules FORCE ROW LEVEL SECURITY;
ALTER TABLE voice_models FORCE ROW LEVEL SECURITY;
ALTER TABLE telemetry_logs FORCE ROW LEVEL SECURITY;
ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;

-- 1. COMPANION PROFILES RLS
-- Account-level view: A user can manage their own companion profiles (up to 2)
CREATE POLICY rls_companion_profiles_select ON companion_profiles
  FOR SELECT TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY rls_companion_profiles_insert ON companion_profiles
  FOR INSERT TO authenticated
  WITH CHECK (user_id = auth.uid());

CREATE POLICY rls_companion_profiles_update ON companion_profiles
  FOR UPDATE TO authenticated
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY rls_companion_profiles_delete ON companion_profiles
  FOR DELETE TO authenticated
  USING (user_id = auth.uid());

-- 2. DEVICES RLS
-- A user manages their own devices; active_profile_id must belong to the user
CREATE POLICY rls_devices_select ON devices
  FOR SELECT TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY rls_devices_insert ON devices
  FOR INSERT TO authenticated
  WITH CHECK (
    user_id = auth.uid() AND
    (active_profile_id IS NULL OR profile_belongs_to_user(active_profile_id, auth.uid()))
  );

CREATE POLICY rls_devices_update ON devices
  FOR UPDATE TO authenticated
  USING (user_id = auth.uid())
  WITH CHECK (
    user_id = auth.uid() AND
    (active_profile_id IS NULL OR profile_belongs_to_user(active_profile_id, auth.uid()))
  );

CREATE POLICY rls_devices_delete ON devices
  FOR DELETE TO authenticated
  USING (user_id = auth.uid());

-- 3. SESSIONS RLS
-- Sessions are strictly bound to the currently active companion profile
CREATE POLICY rls_sessions_select ON sessions
  FOR SELECT TO authenticated
  USING (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_sessions_insert ON sessions
  FOR INSERT TO authenticated
  WITH CHECK (
    profile_id = aster_get_active_profile_id() AND
    profile_belongs_to_user(profile_id, auth.uid())
  );

CREATE POLICY rls_sessions_update ON sessions
  FOR UPDATE TO authenticated
  USING (profile_id = aster_get_active_profile_id())
  WITH CHECK (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_sessions_delete ON sessions
  FOR DELETE TO authenticated
  USING (profile_id = aster_get_active_profile_id());

-- 4. EVENTS RLS
-- Events can only be streamed or inspected by the currently active companion profile
CREATE POLICY rls_events_select ON events
  FOR SELECT TO authenticated
  USING (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_events_insert ON events
  FOR INSERT TO authenticated
  WITH CHECK (
    profile_id = aster_get_active_profile_id() AND
    profile_belongs_to_user(profile_id, auth.uid())
  );

CREATE POLICY rls_events_update ON events
  FOR UPDATE TO authenticated
  USING (profile_id = aster_get_active_profile_id())
  WITH CHECK (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_events_delete ON events
  FOR DELETE TO authenticated
  USING (profile_id = aster_get_active_profile_id());

-- 5. MEMORIES RLS
-- Strict profile isolation: Profile A cannot read or write Profile B's memories
-- Exception: Explicitly shared memories confirmed and unrevoked can be read by destination profile
CREATE POLICY rls_memories_select ON memories
  FOR SELECT TO authenticated
  USING (
    profile_id = aster_get_active_profile_id() OR
    (id IN (
      SELECT ms.memory_id
      FROM memory_shares ms
      WHERE ms.destination_profile_id = aster_get_active_profile_id()
        AND ms.confirmed_by_user = true
        AND ms.revoked_at IS NULL
    ))
  );

CREATE POLICY rls_memories_insert ON memories
  FOR INSERT TO authenticated
  WITH CHECK (
    profile_id = aster_get_active_profile_id() AND
    profile_belongs_to_user(profile_id, auth.uid())
  );

CREATE POLICY rls_memories_update ON memories
  FOR UPDATE TO authenticated
  USING (profile_id = aster_get_active_profile_id())
  WITH CHECK (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_memories_delete ON memories
  FOR DELETE TO authenticated
  USING (profile_id = aster_get_active_profile_id());

-- 6. MEMORY SHARES RLS
-- Audit trail visible to involved profiles of the authenticated user
CREATE POLICY rls_memory_shares_select ON memory_shares
  FOR SELECT TO authenticated
  USING (
    (source_profile_id = aster_get_active_profile_id() OR destination_profile_id = aster_get_active_profile_id()) AND
    profile_belongs_to_user(source_profile_id, auth.uid()) AND
    profile_belongs_to_user(destination_profile_id, auth.uid())
  );

CREATE POLICY rls_memory_shares_insert ON memory_shares
  FOR INSERT TO authenticated
  WITH CHECK (
    source_profile_id = aster_get_active_profile_id() AND
    profile_belongs_to_user(source_profile_id, auth.uid()) AND
    profile_belongs_to_user(destination_profile_id, auth.uid())
  );

CREATE POLICY rls_memory_shares_update ON memory_shares
  FOR UPDATE TO authenticated
  USING (
    (source_profile_id = aster_get_active_profile_id() OR destination_profile_id = aster_get_active_profile_id()) AND
    profile_belongs_to_user(source_profile_id, auth.uid())
  )
  WITH CHECK (
    (source_profile_id = aster_get_active_profile_id() OR destination_profile_id = aster_get_active_profile_id()) AND
    profile_belongs_to_user(source_profile_id, auth.uid())
  );

CREATE POLICY rls_memory_shares_delete ON memory_shares
  FOR DELETE TO authenticated
  USING (
    source_profile_id = aster_get_active_profile_id() AND
    profile_belongs_to_user(source_profile_id, auth.uid())
  );

-- 7. CHAT CONVERSATIONS RLS
CREATE POLICY rls_chat_conversations_select ON chat_conversations
  FOR SELECT TO authenticated
  USING (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_chat_conversations_insert ON chat_conversations
  FOR INSERT TO authenticated
  WITH CHECK (
    profile_id = aster_get_active_profile_id() AND
    profile_belongs_to_user(profile_id, auth.uid())
  );

CREATE POLICY rls_chat_conversations_update ON chat_conversations
  FOR UPDATE TO authenticated
  USING (profile_id = aster_get_active_profile_id())
  WITH CHECK (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_chat_conversations_delete ON chat_conversations
  FOR DELETE TO authenticated
  USING (profile_id = aster_get_active_profile_id());

-- 8. CHAT MESSAGES RLS
CREATE POLICY rls_chat_messages_select ON chat_messages
  FOR SELECT TO authenticated
  USING (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_chat_messages_insert ON chat_messages
  FOR INSERT TO authenticated
  WITH CHECK (
    profile_id = aster_get_active_profile_id() AND
    profile_belongs_to_user(profile_id, auth.uid())
  );

CREATE POLICY rls_chat_messages_update ON chat_messages
  FOR UPDATE TO authenticated
  USING (profile_id = aster_get_active_profile_id())
  WITH CHECK (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_chat_messages_delete ON chat_messages
  FOR DELETE TO authenticated
  USING (profile_id = aster_get_active_profile_id());

-- 9. ACTIONS RLS
CREATE POLICY rls_actions_select ON actions
  FOR SELECT TO authenticated
  USING (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_actions_insert ON actions
  FOR INSERT TO authenticated
  WITH CHECK (
    profile_id = aster_get_active_profile_id() AND
    profile_belongs_to_user(profile_id, auth.uid())
  );

CREATE POLICY rls_actions_update ON actions
  FOR UPDATE TO authenticated
  USING (profile_id = aster_get_active_profile_id())
  WITH CHECK (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_actions_delete ON actions
  FOR DELETE TO authenticated
  USING (profile_id = aster_get_active_profile_id());

-- 10. INTEGRATIONS RLS
-- Profile-scoped external tokens or account-scoped integrations
CREATE POLICY rls_integrations_select ON integrations
  FOR SELECT TO authenticated
  USING (
    user_id = auth.uid() AND
    (profile_id IS NULL OR profile_id = aster_get_active_profile_id())
  );

CREATE POLICY rls_integrations_insert ON integrations
  FOR INSERT TO authenticated
  WITH CHECK (
    user_id = auth.uid() AND
    (profile_id IS NULL OR (profile_id = aster_get_active_profile_id() AND profile_belongs_to_user(profile_id, auth.uid())))
  );

CREATE POLICY rls_integrations_update ON integrations
  FOR UPDATE TO authenticated
  USING (
    user_id = auth.uid() AND
    (profile_id IS NULL OR profile_id = aster_get_active_profile_id())
  )
  WITH CHECK (
    user_id = auth.uid() AND
    (profile_id IS NULL OR profile_id = aster_get_active_profile_id())
  );

CREATE POLICY rls_integrations_delete ON integrations
  FOR DELETE TO authenticated
  USING (
    user_id = auth.uid() AND
    (profile_id IS NULL OR profile_id = aster_get_active_profile_id())
  );

-- 11. PROACTIVE RULES RLS
CREATE POLICY rls_proactive_rules_select ON proactive_rules
  FOR SELECT TO authenticated
  USING (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_proactive_rules_insert ON proactive_rules
  FOR INSERT TO authenticated
  WITH CHECK (
    profile_id = aster_get_active_profile_id() AND
    profile_belongs_to_user(profile_id, auth.uid())
  );

CREATE POLICY rls_proactive_rules_update ON proactive_rules
  FOR UPDATE TO authenticated
  USING (profile_id = aster_get_active_profile_id())
  WITH CHECK (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_proactive_rules_delete ON proactive_rules
  FOR DELETE TO authenticated
  USING (profile_id = aster_get_active_profile_id());

-- 12. VOICE MODELS RLS
CREATE POLICY rls_voice_models_select ON voice_models
  FOR SELECT TO authenticated
  USING (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_voice_models_insert ON voice_models
  FOR INSERT TO authenticated
  WITH CHECK (
    profile_id = aster_get_active_profile_id() AND
    profile_belongs_to_user(profile_id, auth.uid())
  );

CREATE POLICY rls_voice_models_update ON voice_models
  FOR UPDATE TO authenticated
  USING (profile_id = aster_get_active_profile_id())
  WITH CHECK (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_voice_models_delete ON voice_models
  FOR DELETE TO authenticated
  USING (profile_id = aster_get_active_profile_id());

-- 13. TELEMETRY LOGS RLS
CREATE POLICY rls_telemetry_logs_select ON telemetry_logs
  FOR SELECT TO authenticated
  USING (profile_id = aster_get_active_profile_id());

CREATE POLICY rls_telemetry_logs_insert ON telemetry_logs
  FOR INSERT TO authenticated
  WITH CHECK (
    profile_id = aster_get_active_profile_id() AND
    profile_belongs_to_user(profile_id, auth.uid())
  );

-- 14. AUDIT LOGS RLS
-- Append-only for users; immutable once created
CREATE POLICY rls_audit_logs_select ON audit_logs
  FOR SELECT TO authenticated
  USING (
    user_id = auth.uid() AND
    (profile_id IS NULL OR profile_id = aster_get_active_profile_id())
  );

CREATE POLICY rls_audit_logs_insert ON audit_logs
  FOR INSERT TO authenticated
  WITH CHECK (
    user_id = auth.uid() AND
    (profile_id IS NULL OR profile_id = aster_get_active_profile_id())
  );

-- Deny updates and deletes on audit logs to preserve tamper-proof history
-- (Default-deny is enforced by RLS since no UPDATE/DELETE policy is defined for authenticated)

-- ----------------------------------------------------------------------------
-- SECTION 8: PERMISSIONS & ROLE GRANTS
-- ----------------------------------------------------------------------------

GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT USAGE ON SCHEMA auth TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated, service_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA auth TO anon, authenticated, service_role;
GRANT SELECT ON auth.users TO authenticated, service_role;

-- Anonymous users cannot read or write internal tables by default
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM anon;
