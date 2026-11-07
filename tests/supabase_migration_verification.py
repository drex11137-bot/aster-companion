#!/usr/bin/env python3
"""
Comprehensive Automated Verification Test Suite for Aster Companion Supabase Core Schema
Migration: backend/supabase/migrations/20261101000001_aster_core_schema.sql
Verifies:
  1. Constraint: Maximum 2 companion profiles per account.
  2. Device-profile foreign key validation and single active profile.
  3. Session-device alignment and single active session per device.
  4. Monotonic event sequence deduplication on (device_id, sequence_number).
  5. pgvector 1536-dim cosine similarity search with HNSW index via search_profile_memories.
  6. Absolute Profile-Level Row Security (RLS) default-deny isolation between Profile A and Profile B.
  7. Explicit memory sharing audit trail and revocation.
  8. Audit logs append-only immutability.
"""

import sys
import subprocess
import json

def run_psql(sql: str) -> str:
    cmd = [
        "psql",
        "-h", "localhost",
        "-U", "postgres",
        "-d", "postgres",
        "-v", "ON_ERROR_STOP=1",
        "-c", sql
    ]
    env = {"PGPASSWORD": "postgres"}
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"PSQL Error:\n{res.stderr}\nCommand:\n{sql}")
    return res.stdout.strip()

def run_psql_expect_error(sql: str, expected_snippet: str) -> str:
    cmd = [
        "psql",
        "-h", "localhost",
        "-U", "postgres",
        "-d", "postgres",
        "-c", sql
    ]
    env = {"PGPASSWORD": "postgres"}
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if res.returncode == 0:
        raise AssertionError(f"Expected error containing '{expected_snippet}', but SQL succeeded:\n{sql}\nOutput:\n{res.stdout}")
    combined = res.stderr + res.stdout
    if expected_snippet.lower() not in combined.lower():
        raise AssertionError(f"Expected snippet '{expected_snippet}' not found in output:\n{combined}")
    return combined

def main():
    print("=================================================================")
    print("STARTING ASTER COMPANION SUPABASE SCHEMA VERIFICATION TEST SUITE")
    print("=================================================================")

    # Setup test users in auth.users
    print("\n--- Test Setup: Creating Test Users ---")
    setup_sql = """
    TRUNCATE auth.users, companion_profiles, devices, sessions, events, memories, memory_shares, chat_conversations, chat_messages, actions, integrations, proactive_rules, voice_models, telemetry_logs, audit_logs CASCADE;
    INSERT INTO auth.users (id, email) VALUES
      ('11111111-1111-1111-1111-111111111111', 'user1@aster.test'),
      ('22222222-2222-2222-2222-222222222222', 'user2@aster.test')
    ON CONFLICT (id) DO NOTHING;
    """
    run_psql(setup_sql)
    print("Test users User 1 and User 2 registered.")

    # 1. TEST MAX 2 COMPANION PROFILES PER ACCOUNT
    print("\n--- Test 1: Maximum 2 Companion Profiles Per Account ---")
    p1_sql = """
    INSERT INTO companion_profiles (id, user_id, name, personality_config)
    VALUES ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111', 'Aster Social', '{"humor": 0.9}'::jsonb);
    """
    run_psql(p1_sql)
    print("PASS: Inserted Profile 1 for User 1 (Aster Social)")

    p2_sql = """
    INSERT INTO companion_profiles (id, user_id, name, personality_config)
    VALUES ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '11111111-1111-1111-1111-111111111111', 'Aster Private', '{"reserved": 0.9}'::jsonb);
    """
    run_psql(p2_sql)
    print("PASS: Inserted Profile 2 for User 1 (Aster Private)")

    # Attempt to insert 3rd profile for User 1 -> MUST FAIL
    p3_fail_sql = """
    INSERT INTO companion_profiles (id, user_id, name)
    VALUES ('cccccccc-cccc-cccc-cccc-cccccccccccc', '11111111-1111-1111-1111-111111111111', 'Aster Third Profile');
    """
    err = run_psql_expect_error(p3_fail_sql, "Account profile limit exceeded")
    print(f"PASS: 3rd companion profile rejected with expected limit violation:\n      {err.splitlines()[-1]}")

    # Verify User 2 can create profiles independently
    u2_p1_sql = """
    INSERT INTO companion_profiles (id, user_id, name)
    VALUES ('dddddddd-dddd-dddd-dddd-dddddddddddd', '22222222-2222-2222-2222-222222222222', 'Aster User2 Companion');
    """
    run_psql(u2_p1_sql)
    print("PASS: User 2 can create their own companion profile.")

    # 2. TEST DEVICE ACTIVE PROFILE INTEGRITY
    print("\n--- Test 2: Device Active Profile Constraint ---")
    dev1_sql = """
    INSERT INTO devices (id, user_id, device_name, platform, active_profile_id)
    VALUES ('10000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'Pixel 9 Pro', 'android', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa');
    """
    run_psql(dev1_sql)
    print("PASS: Created Device 1 for User 1 referencing active Profile 1A.")

    # Attempt to create Device for User 1 referencing Profile belonging to User 2 -> MUST FAIL
    dev_spoof_sql = """
    INSERT INTO devices (id, user_id, device_name, platform, active_profile_id)
    VALUES ('10000000-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111', 'Hacked iPad', 'ios', 'dddddddd-dddd-dddd-dddd-dddddddddddd');
    """
    err = run_psql_expect_error(dev_spoof_sql, "violates foreign key constraint")
    print("PASS: Cross-user profile activation blocked by composite foreign key.")

    # 3. TEST SESSION & SINGLE ACTIVE PROFILE PER DEVICE
    print("\n--- Test 3: Session Synchronization & Single Active Session per Device ---")
    sess1_sql = """
    INSERT INTO sessions (id, profile_id, device_id, state)
    VALUES ('20000000-0000-0000-0000-000000000001', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '10000000-0000-0000-0000-000000000001', 'active');
    """
    run_psql(sess1_sql)
    print("PASS: Session 1 activated on Device 1 with Profile 1A.")

    # Starting a new active session on same device with Profile 1B triggers automatic ending of Session 1
    sess2_sql = """
    INSERT INTO sessions (id, profile_id, device_id, state)
    VALUES ('20000000-0000-0000-0000-000000000002', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '10000000-0000-0000-0000-000000000001', 'active');
    """
    run_psql(sess2_sql)
    print("PASS: Session 2 activated on Device 1 with Profile 1B.")

    # Verify session 1 was automatically transitioned to 'ended'
    check_sess1 = run_psql("SELECT state FROM sessions WHERE id = '20000000-0000-0000-0000-000000000001';")
    if "ended" not in check_sess1:
        raise AssertionError(f"Expected Session 1 to be ended, got: {check_sess1}")
    print("PASS: Session 1 state successfully auto-ended upon profile switch.")

    # Verify Device 1 active_profile_id pointer was synchronized to Profile 1B
    check_dev = run_psql("SELECT active_profile_id FROM devices WHERE id = '10000000-0000-0000-0000-000000000001';")
    if "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb" not in check_dev:
        raise AssertionError(f"Expected Device 1 active profile to be Profile 1B, got: {check_dev}")
    print("PASS: Device active_profile_id synchronized to Profile 1B.")

    # 4. TEST EVENTS MONOTONIC SEQUENCE & DEDUPLICATION
    print("\n--- Test 4: Monotonic Events Stream & (device_id, sequence_number) Uniqueness ---")
    event1_sql = """
    INSERT INTO events (id, session_id, profile_id, device_id, sequence_number, event_type, payload)
    VALUES ('30000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000002', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '10000000-0000-0000-0000-000000000001', 1, 'screen_frame_captured', '{"fps": 60}'::jsonb);
    """
    run_psql(event1_sql)
    print("PASS: Event 1 inserted with sequence_number = 1.")

    # Duplicate sequence number for same device -> MUST FAIL
    event_dup_sql = """
    INSERT INTO events (id, session_id, profile_id, device_id, sequence_number, event_type)
    VALUES ('30000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000002', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '10000000-0000-0000-0000-000000000001', 1, 'duplicate_event');
    """
    err = run_psql_expect_error(event_dup_sql, "violates unique constraint")
    print("PASS: Duplicate sequence_number per device strictly rejected by database constraint.")

    # 5. TEST PGVECTOR & HNSW SEMANTIC RETRIEVAL
    print("\n--- Test 5: pgvector 1536-dim Embedding & HNSW Cosine Search ---")
    # Generate synthetic 1536-dim vector string: [0.1, 0.0, ...]
    vec_a = "[" + ",".join(["0.05"] * 1536) + "]"
    vec_b = "[" + ",".join(["-0.05"] * 1536) + "]"
    vec_query = "[" + ",".join(["0.05"] * 1536) + "]"

    mem_insert_sql = f"""
    INSERT INTO memories (id, profile_id, memory_category, content, confidence_score, embedding)
    VALUES
      ('40000000-0000-0000-0000-000000000001', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'preference', 'User loves jazz music and espresso', 0.95, '{vec_a}'::vector),
      ('40000000-0000-0000-0000-000000000002', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'conversational', 'Private journal entry about career goals', 0.99, '{vec_b}'::vector);
    """
    run_psql(mem_insert_sql)
    print("PASS: Inserted 1536-dim vector memories for Profile 1A and Profile 1B.")

    # Query search_profile_memories for Profile 1A
    search_sql = f"""
    SELECT id, profile_id, content, similarity
    FROM search_profile_memories('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '{vec_query}'::vector, 0.5, 5);
    """
    search_res = run_psql(search_sql)
    if "User loves jazz music" not in search_res:
        raise AssertionError(f"Expected memory match in search, got:\n{search_res}")
    print(f"PASS: Vector similarity search successfully returned closest memory:\n{search_res}")

    # 6. TEST ROW-LEVEL SECURITY (RLS) DEFAULT-DENY & PROFILE ISOLATION
    print("\n--- Test 6: Absolute Profile Isolation via Row-Level Security (RLS) ---")
    # Create test chat conversation and messages
    chat_setup_sql = """
    INSERT INTO chat_conversations (id, profile_id, title) VALUES
      ('50000000-0000-0000-0000-000000000001', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Social Chat Thread'),
      ('50000000-0000-0000-0000-000000000002', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Private Reflections');

    INSERT INTO chat_messages (id, conversation_id, profile_id, sender, text_content) VALUES
      ('60000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'user', 'Hey Aster, recommend me a comedy movie!'),
      ('60000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000002', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'user', 'Confidential thoughts on project roadmap.');
    """
    run_psql(chat_setup_sql)

    # Now simulate authenticated client session for User 1 with Profile 1A active
    rls_test_1a = """
    SET ROLE authenticated;
    SET LOCAL "request.jwt.claim.sub" = '11111111-1111-1111-1111-111111111111';
    SET LOCAL "request.headers" = '{"x-profile-id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}';

    -- 1. Check companion_profiles: User can see both profiles they own
    SELECT count(*) AS my_profiles FROM companion_profiles;

    -- 2. Check memories: Profile 1A MUST ONLY see Profile 1A memories
    SELECT id, content FROM memories;

    -- 3. Check chat messages: Profile 1A MUST ONLY see Profile 1A messages
    SELECT id, text_content FROM chat_messages;
    """
    out_1a = run_psql(rls_test_1a)
    print(f"Authenticated as User 1, Active Profile: Profile 1A (Aster Social):\n{out_1a}")

    if "Confidential thoughts" in out_1a:
        raise AssertionError("RLS VIOLATION: Profile 1A was able to read Profile 1B's chat messages!")
    if "Private journal entry" in out_1a:
        raise AssertionError("RLS VIOLATION: Profile 1A was able to read Profile 1B's memories!")
    if "User loves jazz music" not in out_1a:
        raise AssertionError("Profile 1A could not read its own memory!")
    print("PASS: Profile 1A RLS verified! Zero leakage of Profile 1B memories or chat.")

    # Attempt to write to Profile 1B while active on Profile 1A -> MUST FAIL
    malicious_write_sql = """
    SET ROLE authenticated;
    SET LOCAL "request.jwt.claim.sub" = '11111111-1111-1111-1111-111111111111';
    SET LOCAL "request.headers" = '{"x-profile-id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}';

    -- Attempt to insert memory belonging to Profile 1B
    INSERT INTO memories (profile_id, memory_category, content)
    VALUES ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'preference', 'Injected memory by Profile 1A');
    """
    err = run_psql_expect_error(malicious_write_sql, "violates row-level security policy")
    print(f"PASS: Cross-profile write attempt blocked by RLS:\n      {err.splitlines()[-1]}")

    # Switch active profile to Profile 1B
    rls_test_1b = """
    SET ROLE authenticated;
    SET LOCAL "request.jwt.claim.sub" = '11111111-1111-1111-1111-111111111111';
    SET LOCAL "request.headers" = '{"x-profile-id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}';

    SELECT id, content FROM memories;
    """
    out_1b = run_psql(rls_test_1b)
    if "User loves jazz music" in out_1b:
        raise AssertionError("RLS VIOLATION: Profile 1B was able to read Profile 1A's memories!")
    if "Private journal entry" not in out_1b:
        raise AssertionError("Profile 1B could not read its own memory!")
    print("PASS: Profile 1B RLS verified! Zero leakage of Profile 1A memories.")

    # 7. TEST EXPLICIT MEMORY SHARING AUDIT TRAIL
    print("\n--- Test 7: Explicit Memory Sharing Between Profiles ---")
    share_sql = """
    SET ROLE authenticated;
    SET LOCAL "request.jwt.claim.sub" = '11111111-1111-1111-1111-111111111111';
    SET LOCAL "request.headers" = '{"x-profile-id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}';

    -- User explicitly shares Memory 40000000-...-0001 (jazz & espresso) with Profile 1B
    SELECT aster_share_memory(
      'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      '40000000-0000-0000-0000-000000000001'
    ) AS share_id;
    """
    share_res = run_psql(share_sql)
    print(f"PASS: Memory explicitly shared from Profile 1A to 1B: {share_res}")

    # Check that when active on Profile 1B, the shared memory is now accessible
    check_shared_sql = """
    SET ROLE authenticated;
    SET LOCAL "request.jwt.claim.sub" = '11111111-1111-1111-1111-111111111111';
    SET LOCAL "request.headers" = '{"x-profile-id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}';

    SELECT id, content FROM memories WHERE id = '40000000-0000-0000-0000-000000000001';
    """
    shared_out = run_psql(check_shared_sql)
    if "User loves jazz music" not in shared_out:
        raise AssertionError(f"Expected Profile 1B to read explicitly shared memory, got:\n{shared_out}")
    print("PASS: Profile 1B can read confirmed explicitly shared memory.")

    # Verify Profile 1B CANNOT update or delete Profile 1A's shared memory!
    unauthorized_update_sql = """
    SET ROLE authenticated;
    SET LOCAL "request.jwt.claim.sub" = '11111111-1111-1111-1111-111111111111';
    SET LOCAL "request.headers" = '{"x-profile-id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}';

    UPDATE memories
    SET content = 'Tampered content by Profile 1B'
    WHERE id = '40000000-0000-0000-0000-000000000001';
    """
    run_psql(unauthorized_update_sql)
    check_untampered = run_psql("SELECT content FROM memories WHERE id = '40000000-0000-0000-0000-000000000001';")
    if "Tampered" in check_untampered:
        raise AssertionError("SECURITY BREACH: Profile 1B was able to update Profile 1A's shared memory!")
    print("PASS: Profile 1B cannot mutate Profile 1A's shared memory (read-only for destination).")

    # Revoke share and verify it disappears from Profile 1B
    revoke_sql = """
    SET ROLE authenticated;
    SET LOCAL "request.jwt.claim.sub" = '11111111-1111-1111-1111-111111111111';
    SET LOCAL "request.headers" = '{"x-profile-id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}';

    UPDATE memory_shares
    SET revoked_at = now()
    WHERE source_profile_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
    """
    run_psql(revoke_sql)

    check_revoked_sql = """
    SET ROLE authenticated;
    SET LOCAL "request.jwt.claim.sub" = '11111111-1111-1111-1111-111111111111';
    SET LOCAL "request.headers" = '{"x-profile-id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}';

    SELECT id, content FROM memories WHERE id = '40000000-0000-0000-0000-000000000001';
    """
    revoked_out = run_psql(check_revoked_sql)
    if "User loves jazz music" in revoked_out:
        raise AssertionError("REVOCATION FAILURE: Profile 1B can still read revoked memory share!")
    print("PASS: Revoked memory share immediately ceases visibility for Profile 1B.")

    # 8. TEST AUDIT LOGS APPEND-ONLY
    print("\n--- Test 8: Audit Logs Immutability ---")
    audit_test_sql = """
    SET ROLE authenticated;
    SET LOCAL "request.jwt.claim.sub" = '11111111-1111-1111-1111-111111111111';
    SET LOCAL "request.headers" = '{"x-profile-id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}';

    -- Try to delete audit logs
    DELETE FROM audit_logs WHERE user_id = '11111111-1111-1111-1111-111111111111';
    """
    run_psql(audit_test_sql)
    check_audit_count = run_psql("SELECT count(*) FROM audit_logs WHERE user_id = '11111111-1111-1111-1111-111111111111';")
    if "0" in check_audit_count.split():
        raise AssertionError("Audit logs were deleted by authenticated user!")
    print("PASS: Audit logs are strictly immutable and protected by default-deny RLS.")

    print("\n=================================================================")
    print("ALL 8 VERIFICATION TESTS PASSED WITH 100% SUCCESS!")
    print("=================================================================")

if __name__ == "__main__":
    main()
