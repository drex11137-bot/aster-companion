#!/usr/bin/env python3
"""
Unit and Integration Tests for Performance & Compaction Auditor (compact_memory.py).
"""

import os
import sys
import json
import tempfile
import subprocess
import unittest
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import compact_memory

class TestCompactionAuditor(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_estimate_tokens(self):
        self.assertEqual(compact_memory.estimate_tokens(""), 0)
        self.assertEqual(compact_memory.estimate_tokens("abc"), 1)
        self.assertEqual(compact_memory.estimate_tokens("a" * 400), 100)

    def test_audit_file_budgets_within_budget(self):
        current_md = os.path.join(self.test_dir, "CURRENT.md")
        with open(current_md, "w", encoding="utf-8") as f:
            f.write("# Active Working State\n## Objective\nTask 1\n## Status\nOngoing\n")
        
        res = compact_memory.audit_file_budgets(current_md)
        self.assertTrue(res["passed"])
        self.assertEqual(res["line_count"], 5)
        self.assertEqual(res["max_lines"], 30)
        self.assertEqual(len(res["violations"]), 0)

    def test_audit_file_budgets_line_exceeded(self):
        current_md = os.path.join(self.test_dir, "CURRENT.md")
        with open(current_md, "w", encoding="utf-8") as f:
            f.write("\n".join([f"Line {i}" for i in range(35)]) + "\n")
        
        res = compact_memory.audit_file_budgets(current_md)
        self.assertFalse(res["passed"])
        self.assertEqual(res["line_count"], 35)
        self.assertTrue(any("Line budget exceeded" in v for v in res["violations"]))

    def test_audit_index_md_line_exceeded(self):
        index_md = os.path.join(self.test_dir, "INDEX.md")
        with open(index_md, "w", encoding="utf-8") as f:
            f.write("\n".join([f"| row {i} | info |" for i in range(55)]) + "\n")
            
        res = compact_memory.audit_file_budgets(index_md)
        self.assertFalse(res["passed"])
        self.assertEqual(res["line_count"], 55)
        self.assertEqual(res["max_lines"], 50)
        self.assertTrue(any("Line budget exceeded" in v for v in res["violations"]))

    def test_audit_file_budgets_byte_exceeded(self):
        index_md = os.path.join(self.test_dir, "INDEX.md")
        huge_line = "x" * 5000
        with open(index_md, "w", encoding="utf-8") as f:
            f.write(f"# Header\n{huge_line}\n")
            
        res = compact_memory.audit_file_budgets(index_md)
        self.assertFalse(res["passed"])
        self.assertTrue(any("Byte budget exceeded" in v for v in res["violations"]))

    def test_chronological_sessions_valid(self):
        sess_dir = os.path.join(self.test_dir, "sessions")
        os.makedirs(sess_dir, exist_ok=True)
        
        f1 = os.path.join(sess_dir, "2026-09-01-0900.md")
        f2 = os.path.join(sess_dir, "2026-09-01-1400.md")
        f3 = os.path.join(sess_dir, "2026-09-02-1000.md")
        
        for f in (f1, f2, f3):
            with open(f, "w", encoding="utf-8") as fp:
                fp.write("# Session Log\n")
                
        res = compact_memory.check_chronological_sessions(sess_dir)
        self.assertTrue(res["passed"])
        self.assertEqual(len(res["issues"]), 0)
        self.assertEqual(len(res["files"]), 3)

    def test_chronological_sessions_invalid_order(self):
        sess_dir = os.path.join(self.test_dir, "sessions")
        os.makedirs(sess_dir, exist_ok=True)
        
        f1 = os.path.join(sess_dir, "invalid-filename.md")
        with open(f1, "w", encoding="utf-8") as fp:
            fp.write("# Session\n")
            
        res = compact_memory.check_chronological_sessions(sess_dir)
        self.assertFalse(res["passed"])
        self.assertTrue(any("Non-standard session filename format" in iss for iss in res["issues"]))

    def test_chronological_internal_timestamps_out_of_order(self):
        sess_dir = os.path.join(self.test_dir, "sessions")
        os.makedirs(sess_dir, exist_ok=True)
        
        f1 = os.path.join(sess_dir, "2026-09-01.md")
        with open(f1, "w", encoding="utf-8") as fp:
            fp.write("2026-09-01T14:00:00Z - Started\n2026-09-01T10:00:00Z - Earlier\n")
            
        res = compact_memory.check_chronological_sessions(sess_dir)
        self.assertFalse(res["passed"])
        self.assertTrue(any("Internal timestamps out of order" in iss for iss in res["issues"]))

    def test_detect_repeated_facts_and_pointers(self):
        f1 = os.path.join(self.test_dir, "CURRENT.md")
        f2 = os.path.join(self.test_dir, "GOTCHAS.md")
        
        duplicate_fact = "- SQLite database requires WAL mode enabled for concurrent access."
        with open(f1, "w", encoding="utf-8") as fp:
            fp.write(f"# Working State\n{duplicate_fact}\n")
        with open(f2, "w", encoding="utf-8") as fp:
            fp.write(f"# Gotchas\n{duplicate_fact}\n")
            
        res = compact_memory.detect_repeated_facts([f1, f2])
        self.assertEqual(res["duplicates_count"], 1)
        self.assertIn("Prefer storing in a single canonical file", res["recommendations"][0]["recommendation"])

    def test_compact_current_md(self):
        current_md = os.path.join(self.test_dir, "CURRENT.md")
        lines = [
            "# Active Working State",
            "Last Updated: 2026-09-01",
            "## Current Objective",
            "Build robust memory system",
            "## Active Status",
        ] + [f"- Finished step {i}" for i in range(25)] + [
            "## Blockers",
            "- None",
            "## Next Steps",
            "- Validate test coverage",
        ]
        with open(current_md, "w", encoding="utf-8") as fp:
            fp.write("\n".join(lines) + "\n")
            
        self.assertTrue(len(lines) > 30)
        compacted = compact_memory.compact_current_md(current_md)
        self.assertTrue(compacted)
        
        with open(current_md, "r", encoding="utf-8") as fp:
            new_lines = fp.readlines()
        self.assertTrue(len(new_lines) <= 30)

    def test_compact_markdown_file_whitespace(self):
        test_file = os.path.join(self.test_dir, "test.md")
        with open(test_file, "w", encoding="utf-8") as fp:
            fp.write("Line 1   \n\n\n\nLine 2  \n\n\n")
            
        compacted = compact_memory.compact_markdown_file(test_file)
        self.assertTrue(compacted)
        with open(test_file, "r", encoding="utf-8") as fp:
            cleaned = fp.read()
        self.assertEqual(cleaned, "Line 1\n\nLine 2\n\n")

    def test_run_compaction_full_pass(self):
        f1 = os.path.join(self.test_dir, "CURRENT.md")
        f2 = os.path.join(self.test_dir, "INDEX.md")
        with open(f1, "w", encoding="utf-8") as fp:
            fp.write("# Active Working State\n## Objective\nComplete phase 15\n")
        with open(f2, "w", encoding="utf-8") as fp:
            fp.write("# Memory Index\n| File | Purpose |\n| --- | --- |\n")
            
        report = compact_memory.run_compaction(self.test_dir)
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["passed"])
        self.assertEqual(report["files_audited"], 2)
        self.assertTrue(report["total_lines"] > 0)
        self.assertTrue(report["total_bytes"] > 0)

    def test_run_compaction_single_file(self):
        f1 = os.path.join(self.test_dir, "CURRENT.md")
        with open(f1, "w", encoding="utf-8") as fp:
            fp.write("# Active Working State\n## Current Objective\nTest single file\n")
            
        report = compact_memory.run_compaction(f1)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["files_audited"], 1)

    def test_cli_execution_audit_pass(self):
        cmd = [sys.executable, "/workspaces/codespaces-blank/scripts/compact_memory.py", "/workspaces/codespaces-blank/.agents/memory", "--check"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("ANTIGRAVITY MEMORY PERFORMANCE", result.stdout)

    def test_cli_execution_audit_fail(self):
        oversized_file = os.path.join(self.test_dir, "CURRENT.md")
        with open(oversized_file, "w", encoding="utf-8") as fp:
            fp.write("\n".join([f"Line {i}" for i in range(40)]) + "\n")
            
        cmd = [sys.executable, "/workspaces/codespaces-blank/scripts/compact_memory.py", self.test_dir, "--check"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL", result.stdout)

    def test_cli_execution_enforce_compaction(self):
        oversized_file = os.path.join(self.test_dir, "CURRENT.md")
        lines = [
            "# Active Working State",
            "Last Updated: 2026-09-01",
            "## Current Objective",
            "Build memory system",
            "## Active Status",
        ] + [f"- Extra line {i}" for i in range(35)] + [
            "## Blockers",
            "- None",
            "## Next Steps",
            "- Next item",
        ]
        with open(oversized_file, "w", encoding="utf-8") as fp:
            fp.write("\n".join(lines) + "\n")
            
        # Run enforce mode
        cmd = [sys.executable, "/workspaces/codespaces-blank/scripts/compact_memory.py", self.test_dir, "--enforce"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("PASS", result.stdout)
        
        # Verify file is now < 30 lines
        with open(oversized_file, "r", encoding="utf-8") as fp:
            new_lines = fp.readlines()
        self.assertTrue(len(new_lines) <= 30)

    def test_cli_execution_json_flag(self):
        cmd = [sys.executable, "/workspaces/codespaces-blank/scripts/compact_memory.py", "/workspaces/codespaces-blank/.agents/memory", "--json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["status"], "PASS")
        self.assertIn("file_details", parsed)

if __name__ == "__main__":
    unittest.main()
