-- ============================================================================
-- Aster Companion - Memory Engine Extensions Migration
-- File: backend/supabase/migrations/20261101000002_memory_engine_extensions.sql
-- Description:
--   1. Temporal bitemporal schema extensions (valid_time ranges, supersession, versioning)
--   2. Epistemic fact categorization (explicit_fact vs inference)
--   3. Confidence-gated admission statuses (active vs tentative_inference)
--   4. Memory sharing link to destination copy and confirmation metadata
--   5. pgvector cosine distance similarity search procedure with strict profile isolation
-- ============================================================================

-- 1. Extend memories table with bitemporal and epistemic attributes
ALTER TABLE memories 
  ADD COLUMN IF NOT EXISTS fact_type text NOT NULL DEFAULT 'explicit_fact' 
    CHECK (fact_type IN ('explicit_fact', 'inference')),
  ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'active' 
    CHECK (status IN ('active', 'tentative_inference', 'superseded', 'forgotten')),
  ADD COLUMN IF NOT EXISTS version integer NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS valid_time_start timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS valid_time_end timestamptz,
  ADD COLUMN IF NOT EXISTS root_memory_id uuid REFERENCES memories(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS superseded_by_id uuid REFERENCES memories(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS supersedes_id uuid REFERENCES memories(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS metadata jsonb NOT NULL DEFAULT '{}'::jsonb;

-- 2. Extend memory_shares table with destination copy link & confirmation metadata
ALTER TABLE memory_shares
  ADD COLUMN IF NOT EXISTS destination_memory_id uuid REFERENCES memories(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS confirmation_metadata jsonb NOT NULL DEFAULT '{}'::jsonb;

-- 3. Additional performance and isolation indexes
CREATE INDEX IF NOT EXISTS idx_memories_profile_status 
  ON memories (profile_id, status) 
  WHERE (NOT is_forgotten);

CREATE INDEX IF NOT EXISTS idx_memories_valid_time 
  ON memories (profile_id, valid_time_start, valid_time_end);

CREATE INDEX IF NOT EXISTS idx_memories_lineage 
  ON memories (root_memory_id, version);

CREATE INDEX IF NOT EXISTS idx_memory_shares_destination_mem 
  ON memory_shares (destination_memory_id) 
  WHERE (revoked_at IS NULL);

-- 4. Stored Procedure for pgvector Cosine Distance Search with Strict Profile Isolation
-- Filter: WHERE profile_id = :profileId AND is_forgotten = false AND status = 'active'
CREATE OR REPLACE FUNCTION search_active_memories(
  p_profile_id uuid,
  p_query_embedding vector(1536),
  p_match_threshold float DEFAULT 0.0,
  p_match_count int DEFAULT 10,
  p_include_shared boolean DEFAULT false
)
RETURNS TABLE (
  id uuid,
  profile_id uuid,
  memory_category text,
  content text,
  confidence_score float,
  provenance_source text,
  sensitivity_level text,
  fact_type text,
  status text,
  version integer,
  valid_time_start timestamptz,
  valid_time_end timestamptz,
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
BEGIN
  v_caller_user_id := auth.uid();

  -- Profile isolation authorization check
  IF v_caller_user_id IS NOT NULL THEN
    IF NOT EXISTS (
      SELECT 1 FROM companion_profiles cp
      WHERE cp.id = p_profile_id AND cp.user_id = v_caller_user_id
    ) THEN
      RAISE EXCEPTION 'Access Denied: Caller does not own target profile %', p_profile_id
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
    m.fact_type,
    m.status,
    m.version,
    m.valid_time_start,
    m.valid_time_end,
    m.is_pinned,
    (1 - (m.embedding <=> p_query_embedding))::float AS similarity,
    m.created_at,
    m.updated_at
  FROM memories m
  WHERE (
    -- Strict Profile Isolation WHERE filter
    m.profile_id = p_profile_id
    OR (
      p_include_shared = true 
      AND m.id IN (
        SELECT ms.memory_id 
        FROM memory_shares ms 
        WHERE ms.destination_profile_id = p_profile_id 
          AND ms.confirmed_by_user = true 
          AND ms.revoked_at IS NULL
      )
    )
  )
  AND m.is_forgotten = false
  AND m.status = 'active'
  AND m.embedding IS NOT NULL
  AND (1 - (m.embedding <=> p_query_embedding)) >= p_match_threshold
  ORDER BY m.embedding <=> p_query_embedding ASC
  LIMIT p_match_count;
END;
$$;
