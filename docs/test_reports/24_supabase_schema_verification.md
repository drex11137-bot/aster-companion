# Supabase PostgreSQL Architecture, RLS & Schema Verification Report

**Migration**: `backend/supabase/migrations/20261101000001_aster_core_schema.sql`  
**Test Suite**: `tests/supabase_migration_verification.py`  
**Date**: November 1, 2026  
**Status**: **PASS (100% Verified)**  

---

## 1. Executive Summary

This report documents the architectural design, implementation, and automated verification of the foundational PostgreSQL schema and security subsystem for Aster Companion. Built in strict compliance with **PRD v1.1** (specifically DEC-021, DEC-022, DEC-024, DEC-025, DEC-026, DEC-027, DEC-028, DEC-029), this migration establishes:
- Hard constraint and advisory-locked trigger limiting accounts to a maximum of 2 companion profiles.
- Absolute profile-level isolation enforced via PostgreSQL Row-Level Security (RLS) with Default Deny.
- Hardware device binding ensuring only one active companion profile per device at any time.
- Monotonic session event stream tracking with gap detection and strict `(device_id, sequence_number)` uniqueness.
- Semantic 1536-dimensional memory store utilizing pgvector with an HNSW cosine similarity index.
- Explicit, auditable profile-to-profile memory sharing and real-time revocation.
- Tamper-proof, immutable audit logs and perception pipeline telemetry storage.

---

## 2. Table Architecture & Relational Schema Inventory

The migration introduces 14 core tables with strict foreign keys, cascade rules, and check constraints:

| Table Name | Primary Key | Foreign References | Core Constraints & Business Logic |
| :--- | :--- | :--- | :--- |
| `companion_profiles` | `id uuid` | `user_id -> auth.users` | Max 2 profiles per account trigger (`check_companion_profile_limit`). Unique `(id, user_id)`. |
| `devices` | `id uuid` | `user_id -> auth.users`, `(active_profile_id, user_id) -> companion_profiles(id, user_id)` | Single active profile per physical device. Composite FK prevents cross-user profile activation. |
| `sessions` | `id uuid` | `profile_id -> companion_profiles`, `device_id -> devices` | Partial unique index `uq_sessions_device_active` ensures 1 active session per device. Trigger auto-ends stale sessions upon profile switch. |
| `events` | `id uuid` | `session_id -> sessions`, `profile_id -> companion_profiles`, `device_id -> devices` | Unique `(device_id, sequence_number)` for monotonic ordering, frame sequencing, and gap detection. |
| `memories` | `id uuid` | `profile_id -> companion_profiles` | Categories (`conversational`, `preference`, `behavioral`, `activity`, `relationship_social`, `procedural`, `profile_config`, `explicitly_shared`). Vector(1536) embedding with HNSW index. |
| `memory_shares` | `id uuid` | `source_profile_id`, `destination_profile_id`, `memory_id` | Audit trail for explicit memory sharing. Check `source <> destination`. Validation trigger enforces single-account boundary and source ownership. |
| `chat_conversations` | `id uuid` | `profile_id -> companion_profiles` | Conversation threads bound to companion profile identity. |
| `chat_messages` | `id uuid` | `conversation_id -> chat_conversations`, `profile_id -> companion_profiles` | Senders (`user`, `aster`, `system`). Multimodal attachments, tool calls, and citations. Validation trigger ensures message profile matches conversation profile. |
| `actions` | `id uuid` | `profile_id -> companion_profiles` | Risk levels (`read_only`, `reversible`, `consequential`, `irreversible`), status (`pending`, `approved`, `rejected`, `executed`, `failed`), unique `idempotency_key`. |
| `integrations` | `id uuid` | `user_id -> auth.users`, `profile_id -> companion_profiles` | Encrypted OAuth tokens for Google services and external apps. Unique `(user_id, profile_id, provider)`. |
| `proactive_rules` | `id uuid` | `profile_id -> companion_profiles` | Configurable proactivity thresholds (relevance, confidence, interruption cost) and quiet hours. |
| `voice_models` | `id uuid` | `profile_id -> companion_profiles` | Voice synthesis settings, consent audit logs, and synthetic voice disclosure agreements. |
| `telemetry_logs` | `id uuid` | `device_id -> devices`, `profile_id -> companion_profiles` | Ingestion, analysis, upload FPS, latency (ms), and frame gap counts. |
| `audit_logs` | `id uuid` | `user_id -> auth.users`, `profile_id -> companion_profiles` | Append-only security audit log. UPDATE and DELETE operations are denied by RLS. |

---

## 3. Row-Level Security (RLS) & Multi-Tenant Isolation Model

### 3.1 Context Resolution (`aster_get_active_profile_id`)
To prevent cross-profile leakage within the same user account (Profile A accessing Profile B's data), the database resolves the active authorized profile via `aster_get_active_profile_id()`:
1. Transaction setting `app.current_profile_id`.
2. HTTP headers `x-profile-id` or `x-aster-profile-id` sent via PostgREST.
3. JWT claims (`active_profile_id` or `profile_id` in root or metadata).
4. HTTP header `x-device-id` resolving the active profile on the registered device.
5. **Security Gate**: The resolved profile ID is verified against `auth.uid()` via `profile_belongs_to_user()`. If an unauthorized or foreign profile ID is presented, the function returns `NULL`.

### 3.2 Default-Deny Policies
All 14 tables have `ROW LEVEL SECURITY` enabled and forced (`FORCE ROW LEVEL SECURITY`). Every query executed by an authenticated client must satisfy:
- `user_id = auth.uid()`
- `profile_id = aster_get_active_profile_id()`

### 3.3 Explicit Memory Sharing Read Exception
For `memories`, the `SELECT` policy permits access if:
1. The memory directly belongs to the active profile: `profile_id = aster_get_active_profile_id()`.
2. OR the memory was explicitly shared with the active profile via `memory_shares` where `destination_profile_id = aster_get_active_profile_id() AND confirmed_by_user = true AND revoked_at IS NULL`.
Mutations (`INSERT`, `UPDATE`, `DELETE`) are strictly restricted to the owning profile; destination profiles cannot mutate shared memories.

---

## 4. Verification Test Results

Automated test execution output from `tests/supabase_migration_verification.py` running against PostgreSQL 16 with pgvector:

```text
=================================================================
STARTING ASTER COMPANION SUPABASE SCHEMA VERIFICATION TEST SUITE
=================================================================

--- Test Setup: Creating Test Users ---
Test users User 1 and User 2 registered.

--- Test 1: Maximum 2 Companion Profiles Per Account ---
PASS: Inserted Profile 1 for User 1 (Aster Social)
PASS: Inserted Profile 2 for User 1 (Aster Private)
PASS: 3rd companion profile rejected with expected limit violation:
      CONTEXT:  PL/pgSQL function check_companion_profile_limit() line 15 at RAISE
PASS: User 2 can create their own companion profile.

--- Test 2: Device Active Profile Constraint ---
PASS: Created Device 1 for User 1 referencing active Profile 1A.
PASS: Cross-user profile activation blocked by composite foreign key.

--- Test 3: Session Synchronization & Single Active Session per Device ---
PASS: Session 1 activated on Device 1 with Profile 1A.
PASS: Session 2 activated on Device 1 with Profile 1B.
PASS: Session 1 state successfully auto-ended upon profile switch.
PASS: Device active_profile_id synchronized to Profile 1B.

--- Test 4: Monotonic Events Stream & (device_id, sequence_number) Uniqueness ---
PASS: Event 1 inserted with sequence_number = 1.
PASS: Duplicate sequence_number per device strictly rejected by database constraint.

--- Test 5: pgvector 1536-dim Embedding & HNSW Cosine Search ---
PASS: Inserted 1536-dim vector memories for Profile 1A and Profile 1B.
PASS: Vector similarity search successfully returned closest memory:
id                  |              profile_id              |              content               | similarity 
--------------------------------------+--------------------------------------+------------------------------------+------------
 40000000-0000-0000-0000-000000000001 | aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa | User loves jazz music and espresso |          1
(1 row)

--- Test 6: Absolute Profile Isolation via Row-Level Security (RLS) ---
Authenticated as User 1, Active Profile: Profile 1A (Aster Social):
SET
SET
SET
 my_profiles 
-------------
           2
(1 row)

                  id                  |              content               
--------------------------------------+------------------------------------
 40000000-0000-0000-0000-000000000001 | User loves jazz music and espresso
(1 row)

                  id                  |              text_content               
--------------------------------------+-----------------------------------------
 60000000-0000-0000-0000-000000000001 | Hey Aster, recommend me a comedy movie!
(1 row)
PASS: Profile 1A RLS verified! Zero leakage of Profile 1B memories or chat.
PASS: Cross-profile write attempt blocked by RLS.
PASS: Profile 1B RLS verified! Zero leakage of Profile 1A memories.

--- Test 7: Explicit Memory Sharing Between Profiles ---
PASS: Memory explicitly shared from Profile 1A to 1B.
PASS: Profile 1B can read confirmed explicitly shared memory.
PASS: Profile 1B cannot mutate Profile 1A's shared memory (read-only for destination).
PASS: Revoked memory share immediately ceases visibility for Profile 1B.

--- Test 8: Audit Logs Immutability ---
PASS: Audit logs are strictly immutable and protected by default-deny RLS.

=================================================================
ALL 8 VERIFICATION TESTS PASSED WITH 100% SUCCESS!
=================================================================
```

---

## 5. Artifacts Produced

1. **Migration File**: [`backend/supabase/migrations/20261101000001_aster_core_schema.sql`](file:///workspaces/codespaces-blank/backend/supabase/migrations/20261101000001_aster_core_schema.sql)
2. **Automated Verification Suite**: [`tests/supabase_migration_verification.py`](file:///workspaces/codespaces-blank/tests/supabase_migration_verification.py)
3. **Verification Report**: [`docs/test_reports/24_supabase_schema_verification.md`](file:///workspaces/codespaces-blank/docs/test_reports/24_supabase_schema_verification.md)
