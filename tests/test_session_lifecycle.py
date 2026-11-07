#!/usr/bin/env python3
"""
Test Suite for Antigravity Session Lifecycle Skills (Phase 7, 8, 9, 10, 16)
Tests:
- Global skill definitions (~/.gemini/antigravity-cli/skills/memory-start.md & memory-end.md)
- Project skill definitions (.agents/skills/memory-start/SKILL.md & memory-end/SKILL.md)
- /start-session restoration, interruption detection, staleness & contradiction checks
- /end-session session logging (YYYY-MM-DD-HHMM.md), memory classification, and compaction
- Zero-secret security gatekeeper enforcement
"""

import os
import sys
import tempfile
import shutil
import unittest
from datetime import datetime, timezone

# Add scripts directory to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from session_manager import (
    start_session,
    end_session,
    detect_interruption,
    detect_stale_and_contradictions,
    parse_current_md,
    scan_secrets,
    VALID_TYPES,
    DURABILITY_TIERS
)


class TestSessionLifecycle(unittest.TestCase):

    def test_global_skills_exist_and_valid(self):
        """Phase 7: Verify global skills exist and contain valid triggers/frontmatter."""
        global_start = os.path.expanduser("~/.gemini/antigravity-cli/skills/memory-start.md")
        global_end = os.path.expanduser("~/.gemini/antigravity-cli/skills/memory-end.md")

        self.assertTrue(os.path.isfile(global_start), f"Missing {global_start}")
        self.assertTrue(os.path.isfile(global_end), f"Missing {global_end}")

        with open(global_start, "r", encoding="utf-8") as f:
            start_content = f.read()
        self.assertIn("name: memory-start", start_content)
        self.assertIn("trigger: /start-session", start_content)
        self.assertIn("Restored Context", start_content)

        with open(global_end, "r", encoding="utf-8") as f:
            end_content = f.read()
        self.assertIn("name: memory-end", end_content)
        self.assertIn("trigger: /end-session", end_content)
        self.assertIn("Candidate Durable Memories", end_content)

    def test_project_skills_exist_and_valid(self):
        """Phase 7: Verify project skills exist and contain proper triggers."""
        proj_start = os.path.join(REPO_ROOT, ".agents", "skills", "memory-start", "SKILL.md")
        proj_end = os.path.join(REPO_ROOT, ".agents", "skills", "memory-end", "SKILL.md")

        self.assertTrue(os.path.isfile(proj_start), f"Missing {proj_start}")
        self.assertTrue(os.path.isfile(proj_end), f"Missing {proj_end}")

        with open(proj_start, "r", encoding="utf-8") as f:
            start_content = f.read()
        self.assertIn("trigger: /start-session", start_content)

        with open(proj_end, "r", encoding="utf-8") as f:
            end_content = f.read()
        self.assertIn("trigger: /end-session", end_content)

    def test_start_session_workflow(self):
        """Phase 8: Test /start-session returns all required context fields."""
        res = start_session(REPO_ROOT)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("summary", res)
        summary = res["summary"]

        self.assertIn("## Restored Context", summary)
        self.assertIn("- **Project**:", summary)
        self.assertIn("- **Current Objective**:", summary)
        self.assertIn("- **Last Known State**:", summary)
        self.assertIn("- **Relevant Decisions**:", summary)
        self.assertIn("- **Known Blockers**:", summary)
        self.assertIn("- **Relevant Gotchas**:", summary)
        self.assertIn("- **Open Tasks**:", summary)
        self.assertIn("- **Memory Confidence**:", summary)

    def test_interruption_detection(self):
        """Phase 8: Test detecting interrupted sessions."""
        # Uncommitted / unfinalized state
        current_data = {
            "objective": "Halfway through migrating database schemas",
            "phase": "Mid-migration",
            "blockers": "None",
            "next_steps": ["Run migration step 2"]
        }
        git_info_dirty = {
            "is_git": True,
            "repo_root": "/tmp/test",
            "branch": "feature/db",
            "commit": "abc1234",
            "is_clean": False,
            "uncommitted_files": ["M db/schema.sql"]
        }
        is_interrupted, reason = detect_interruption(current_data, None, git_info_dirty)
        self.assertTrue(is_interrupted)
        self.assertIn("uncommitted changes", reason)

    def test_end_session_workflow(self):
        """Phase 9 & 10: Test /end-session log generation and memory classification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup mock workspace
            mem_dir = os.path.join(tmpdir, ".agents", "memory")
            os.makedirs(os.path.join(mem_dir, "sessions"), exist_ok=True)
            
            with open(os.path.join(mem_dir, "INDEX.md"), "w") as f:
                f.write("# Index\n")
            with open(os.path.join(mem_dir, "CURRENT.md"), "w") as f:
                f.write("# Active State\n## Current Objective\nTesting end-session\n")

            candidates = [
                {"type": "PROJECT", "durability": 3, "description": "ADR: Used modular skills"},
                {"type": "GOTCHA", "durability": 3, "description": "Token limits must be watched"},
                {"type": "GLOBAL", "durability": 5, "description": "Always run tests before committing"},
                {"type": "EPHEMERAL", "durability": 1, "description": "Temp test output"}
            ]

            res = end_session(
                workspace_path=tmpdir,
                completed_items=["Completed memory-start and memory-end skills", "Ran test suite"],
                unresolved_items=["None"],
                decisions_made=["ADR-005: Adopted 9-type memory classification taxonomy"],
                discoveries=["CURRENT.md is strictly bounded to < 30 lines"],
                next_steps=["Implement next phase skills"],
                candidate_memories=candidates,
                new_objective="Proceed to Phase 11"
            )

            self.assertEqual(res["status"], "SUCCESS")
            log_path = res["log_path"]
            self.assertTrue(os.path.isfile(log_path))

            # Inspect log contents
            with open(log_path, "r", encoding="utf-8") as f:
                log_content = f.read()

            self.assertIn("## 1. Completed Work", log_content)
            self.assertIn("## 2. Unresolved Issues & Blockers", log_content)
            self.assertIn("## 3. Architectural Decisions", log_content)
            self.assertIn("## 4. Discoveries & Gotchas", log_content)
            self.assertIn("## 5. Next Steps", log_content)
            self.assertIn("## 6. Candidate Durable Memories", log_content)
            self.assertIn("GLOBAL", log_content)
            self.assertIn("GOTCHA", log_content)

            # Inspect CURRENT.md compaction
            current_path = res["current_path"]
            with open(current_path, "r", encoding="utf-8") as f:
                current_lines = f.readlines()

            self.assertLess(len(current_lines), 30, "CURRENT.md must not exceed 30 lines budget")
            self.assertIn("Proceed to Phase 11", "".join(current_lines))

    def test_security_rejection_in_end_session(self):
        """Phase 16: Verify that attempting to persist API keys or tokens raises a security error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem_dir = os.path.join(tmpdir, ".agents", "memory")
            os.makedirs(os.path.join(mem_dir, "sessions"), exist_ok=True)

            with self.assertRaises(ValueError) as ctx:
                end_session(
                    workspace_path=tmpdir,
                    completed_items=["Leaking secret sk-proj-12345678901234567890123456789012345678901234"],
                    unresolved_items=["None"],
                    decisions_made=["None"],
                    discoveries=["None"],
                    next_steps=["None"]
                )
            self.assertIn("SECURITY VIOLATION", str(ctx.exception))

    def test_session_recovery_integration(self):
        """Phase 16 (Section 32): Verify full session recovery from an interrupted state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem_dir = os.path.join(tmpdir, ".agents", "memory")
            os.makedirs(mem_dir, exist_ok=True)
            
            # Simulate interrupted session state with partial work and unresolved blockers
            interrupted_current_md = (
                "# Active Working State\n"
                "## Current Objective\n"
                "Implement distributed locking mechanism\n\n"
                "## Active Status\n"
                "- Phase: Mid-implementation (partial work on redis adapter)\n"
                "- Blockers: Connection timeout when testing with high concurrency\n"
                "- Next Steps: Debug redis connection pool settings\n"
            )
            with open(os.path.join(mem_dir, "CURRENT.md"), "w", encoding="utf-8") as f:
                f.write(interrupted_current_md)
                
            # Note: No sessions directory or last log implies interruption if dirty,
            # or we can mock git_info to be dirty. `start_session` will call `get_git_info(tmpdir)`
            # Since tmpdir isn't a git repo, `is_clean` will be True by default.
            # But we can override get_git_info by patching or let it be.
            # Actually, `detect_interruption` says:
            # if not git_info["is_clean"]: return True ...
            # Wait, if `last_log is None` and `is_clean` is True, it returns `False, "Initial workspace session."`
            # Let's mock `get_git_info` just for this test, or create a mock function.
            # Instead of mocking, let's create a dummy last log that doesn't say "Session Concluded".
            sessions_dir = os.path.join(mem_dir, "sessions")
            os.makedirs(sessions_dir, exist_ok=True)
            with open(os.path.join(sessions_dir, "2026-09-01-1200.md"), "w", encoding="utf-8") as f:
                f.write("# Session Log\n\nSome previous work, abruptly stopped.")
            
            res = start_session(workspace_path=tmpdir)
            
            self.assertEqual(res["status"], "SUCCESS")
            self.assertTrue(res["is_interrupted"])
            
            summary = res["summary"]
            # Verify recovery of project, objective, state, problem, next action
            self.assertIn("Implement distributed locking mechanism", summary)
            self.assertIn("Connection timeout when testing with high concurrency", summary)
            self.assertIn("Debug redis connection pool settings", summary)
            self.assertIn("INTERRUPTED", summary)

if __name__ == "__main__":
    unittest.main()
