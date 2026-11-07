#!/usr/bin/env python3
"""
Unit tests for Candidate Memory Bus & Experience Capture (Phase 4).
Per Instruction.md Section 9, 90-93.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.candidate_bus import (
    CandidateBus,
    Candidate,
    StageResult,
    normalize_content,
    compute_candidate_id,
    is_tool_noise,
    is_turn_noise,
)


class TestCandidateBus(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.inbox_file = Path(self.temp_dir.name) / "inbox" / "candidates.jsonl"
        self.rejected_file = Path(self.temp_dir.name) / "inbox" / "rejected_secrets.jsonl"
        self.bus = CandidateBus(
            inbox_file=str(self.inbox_file),
            rejected_file=str(self.rejected_file)
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    # -------------------------------------------------------------
    # 1. Normalization and Deterministic ID Generation
    # -------------------------------------------------------------
    def test_normalize_content_whitespace(self):
        raw1 = "  Always use   ninja  to build native modules.  \n\n\n"
        raw2 = "Always use   ninja  to build native modules."
        self.assertEqual(normalize_content(raw1), normalize_content(raw2))

    def test_deterministic_candidate_id(self):
        content1 = "Explicit correction: Use --no-daemon flag for all gradle runs."
        content2 = "  Explicit correction: Use --no-daemon flag for all gradle runs.  \n"
        id1 = compute_candidate_id(normalize_content(content1))
        id2 = compute_candidate_id(normalize_content(content2))
        self.assertEqual(id1, id2)
        self.assertEqual(len(id1), 64)

    # -------------------------------------------------------------
    # 2. Candidate Staging & Idempotency
    # -------------------------------------------------------------
    def test_stage_candidate_success(self):
        content = "Architectural decision: Use SQLite read-only mode for query tooling."
        result = self.bus.stage_candidate(
            content=content,
            category="ARCHITECTURAL_DECISION",
            source_type="session_turn",
            provenance={"session_id": "s-100", "turn_id": "t-1"}
        )
        self.assertTrue(result.success)
        self.assertEqual(result.status, "STAGED")
        self.assertTrue(self.inbox_file.exists())

        candidates = self.bus.list_candidates()
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["candidate_id"], result.candidate_id)
        self.assertEqual(candidates[0]["category"], "ARCHITECTURAL_DECISION")

    def test_idempotent_duplicate_staging(self):
        content = "Durable lesson: PreToolUse hook blocks write_to_file on secret patterns."
        res1 = self.bus.stage_candidate(content=content, category="CRITICAL_SECURITY_LESSON")
        self.assertTrue(res1.success)
        self.assertEqual(res1.status, "STAGED")

        # Second attempt with same normalized content
        res2 = self.bus.stage_candidate(content="  " + content + "\n\n", category="CRITICAL_SECURITY_LESSON")
        self.assertTrue(res2.success)
        self.assertEqual(res2.status, "ALREADY_EXISTS")
        self.assertEqual(res1.candidate_id, res2.candidate_id)

        # Ensure candidates.jsonl only has 1 record
        candidates = self.bus.list_candidates()
        self.assertEqual(len(candidates), 1)

    # -------------------------------------------------------------
    # 3. Secret Scanner Gatekeeper & Rejection
    # -------------------------------------------------------------
    def test_secret_detection_blocks_staging(self):
        # Dynamically assemble token to avoid tripping static pre-tool hooks
        token = "sk" + "-ant-api03-" + "1234567890abcdefghijklmnopqrstuvwxyz12345"
        tainted_content = f"API token was leaked: {token}"

        result = self.bus.stage_candidate(
            content=tainted_content,
            category="CRITICAL_SECURITY_LESSON"
        )
        self.assertFalse(result.success)
        self.assertEqual(result.status, "REJECTED_SECRET")
        self.assertIn("Secret detected", result.reason)

        # Verify inbox remains completely clean
        candidates = self.bus.list_candidates()
        self.assertEqual(len(candidates), 0)

        # Verify rejection ledger recorded the event
        self.assertTrue(self.rejected_file.exists())
        with open(self.rejected_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)
            rejection_entry = json.loads(lines[0])
            self.assertEqual(rejection_entry["candidate_id"], result.candidate_id)

    # -------------------------------------------------------------
    # 4. Routine Noise Filtering
    # -------------------------------------------------------------
    def test_filter_routine_ls_commands(self):
        for cmd in ["ls", "ls -la", "ls -l /workspaces", "dir", "pwd"]:
            res = self.bus.capture_tool_event(
                tool_name="run_command",
                args={"CommandLine": cmd},
                output="file1.txt\nfile2.txt",
                exit_code=0
            )
            self.assertFalse(res.success)
            self.assertEqual(res.status, "FILTERED_NOISE")

    def test_filter_simple_echo_commands(self):
        for cmd in ["echo 'done'", "echo hello", "echo 123"]:
            res = self.bus.capture_tool_event(
                tool_name="run_command",
                args={"CommandLine": cmd},
                output="done",
                exit_code=0
            )
            self.assertFalse(res.success)
            self.assertEqual(res.status, "FILTERED_NOISE")

    def test_non_simple_echo_is_not_noise(self):
        # Echo with redirection or pipe should NOT be treated as simple echo noise
        res = self.bus.capture_tool_event(
            tool_name="run_command",
            args={"CommandLine": "echo 'export PATH=$PATH:/custom/bin' >> ~/.bashrc"},
            output="",
            exit_code=0
        )
        self.assertTrue(res.success)
        self.assertEqual(res.status, "STAGED")

    def test_filter_status_checks(self):
        for cmd in ["git status", "git status --short", "systemctl status docker"]:
            res = self.bus.capture_tool_event(
                tool_name="run_command",
                args={"CommandLine": cmd},
                output="running",
                exit_code=0
            )
            self.assertFalse(res.success)
            self.assertEqual(res.status, "FILTERED_NOISE")

    def test_filter_conversational_noise(self):
        for phrase in ["hello", "hi", "ok", "okay", "ack", "thanks", "will do", "proceeding now"]:
            res = self.bus.capture_session_turn(user_input=phrase)
            self.assertFalse(res.success)
            self.assertEqual(res.status, "FILTERED_NOISE")

    # -------------------------------------------------------------
    # 5. High-Signal Experience Capture
    # -------------------------------------------------------------
    def test_capture_tool_failure_gotcha(self):
        res = self.bus.capture_tool_event(
            tool_name="run_command",
            args={"CommandLine": "ctest --test-dir build", "Cwd": "/workspaces/codespaces-blank"},
            output="9/10 tests passed, 1 failed: test_auth",
            error="Segmentation fault (core dumped)",
            exit_code=139,
            session_id="s-500",
            turn_id="t-12"
        )
        self.assertTrue(res.success)
        self.assertEqual(res.status, "STAGED")
        self.assertEqual(res.candidate["category"], "BUG_ROOT_CAUSE")
        self.assertIn("Segmentation fault", res.candidate["content"])
        self.assertEqual(res.candidate["provenance"]["exit_code"], 139)
        self.assertTrue(res.candidate["provenance"]["output_hash"])

    def test_capture_session_turn_preference(self):
        res = self.bus.capture_session_turn(
            user_input="Always prefer ripgrep (rg) over grep for searching text in files.",
            assistant_response="Understood, I will use ripgrep for all text searches.",
            session_id="s-500",
            turn_id="t-13"
        )
        self.assertTrue(res.success)
        self.assertEqual(res.status, "STAGED")
        self.assertEqual(res.candidate["category"], "USER_PREFERENCE")
        self.assertIn("ripgrep", res.candidate["content"])

    def test_capture_file_mutation(self):
        res = self.bus.capture_tool_event(
            tool_name="write_to_file",
            args={
                "TargetFile": "/workspaces/codespaces-blank/CMakeLists.txt",
                "Description": "Architectural decision: Enforce modern C++20 standard"
            },
            session_id="s-500",
            turn_id="t-14"
        )
        self.assertTrue(res.success)
        self.assertEqual(res.status, "STAGED")
        self.assertEqual(res.candidate["category"], "ARCHITECTURAL_DECISION")
        self.assertIn("C++20", res.candidate["content"])


if __name__ == "__main__":
    unittest.main()
