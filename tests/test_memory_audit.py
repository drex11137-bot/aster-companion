#!/usr/bin/env python3
"""
Unit and Integration tests for Memory Audit & Health Diagnostics Specialist (Agent 12, Phase 7/13).
Verifies detection of:
- Secret leakage
- Duplicated facts
- Stale entries
- Contradictory entries
- Oversized files
- Cross-project leakage
- Bad categorization
- Unsupported assumptions
- Output standardized report structure
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
from audit_memory import MemoryAuditor, SECRET_PATTERNS, shannon_entropy


class TestMemoryAudit(unittest.TestCase):
    def setUp(self):
        self.temp_global = tempfile.TemporaryDirectory()
        self.temp_project = tempfile.TemporaryDirectory()
        self.global_dir = self.temp_global.name
        self.project_dir = self.temp_project.name

    def tearDown(self):
        self.temp_global.cleanup()
        self.temp_project.cleanup()

    def test_clean_memory_health(self):
        # Create minimal valid memory files
        with open(os.path.join(self.global_dir, "INDEX.md"), "w") as f:
            f.write("# Global Memory Index\n- [GENERAL.md](GENERAL.md)\n")
        with open(os.path.join(self.global_dir, "GENERAL.md"), "w") as f:
            f.write("# General Facts\n- [2026-09-01] TypeScript strict mode is enabled across all microservices.\n")
        with open(os.path.join(self.project_dir, "ARCHITECTURE.md"), "w") as f:
            f.write("# Architecture\n- [2026-09-01] React 19 is used for front-end interface components.\n")

        auditor = MemoryAuditor(global_dir=self.global_dir, project_dir=self.project_dir)
        findings = auditor.run_full_audit()

        self.assertEqual(len(findings["secrets"]), 0)
        self.assertEqual(len(findings["cross_project_leakage"]), 0)
        self.assertEqual(len(findings["duplicates"]), 0)
        self.assertEqual(len(findings["contradictions"]), 0)
        self.assertEqual(len(findings["stale_entries"]), 0)

        report = auditor.generate_report()
        self.assertIn("## MEMORY HEALTH", report)
        self.assertIn("Secrets: PASS", report)
        self.assertIn("Cross-project leakage: PASS", report)
        self.assertIn("Overall status: HEALTHY", report)

    def test_secret_detection(self):
        with open(os.path.join(self.global_dir, "LEAK.md"), "w") as f:
            f.write("API Key: AIzaSyD9x8w7v6u5t4s3r2q1p0o9n8m7l6k5j4i\n")
            f.write("OpenAI: sk-proj-1234567890123456789012345678901234567890\n")

        auditor = MemoryAuditor(global_dir=self.global_dir, project_dir=self.project_dir)
        findings = auditor.run_full_audit()

        self.assertTrue(len(findings["secrets"]) >= 2)
        report = auditor.generate_report()
        self.assertIn("Secrets: FAIL", report)
        self.assertIn("Overall status: CRITICAL", report)

    def test_cross_project_leakage_detection(self):
        with open(os.path.join(self.global_dir, "GENERAL.md"), "w") as f:
            f.write("- [2026-09-01] Internal app config resides in /workspaces/codespaces-blank/config.json\n")

        auditor = MemoryAuditor(global_dir=self.global_dir, project_dir=self.project_dir)
        findings = auditor.run_full_audit()

        self.assertEqual(len(findings["cross_project_leakage"]), 1)
        report = auditor.generate_report()
        self.assertIn("Cross-project leakage: FAIL", report)
        self.assertIn("Overall status: CRITICAL", report)

    def test_duplicate_facts_detection(self):
        fact = "- [2026-09-01] Python >= 3.12 is enforced for all async queue services."
        with open(os.path.join(self.global_dir, "GENERAL.md"), "w") as f:
            f.write(f"# General\n{fact}\n")
        with open(os.path.join(self.project_dir, "ARCHITECTURE.md"), "w") as f:
            f.write(f"# Architecture\n{fact}\n")

        auditor = MemoryAuditor(global_dir=self.global_dir, project_dir=self.project_dir)
        findings = auditor.run_full_audit()

        self.assertTrue(len(findings["duplicates"]) >= 1)
        report = auditor.generate_report()
        self.assertIn("Duplicates: 1", report)

    def test_contradiction_detection(self):
        with open(os.path.join(self.global_dir, "GENERAL.md"), "w") as f:
            f.write("- [2026-09-01] Python version required: 3.11 for all runtime tasks.\n")
        with open(os.path.join(self.project_dir, "ARCHITECTURE.md"), "w") as f:
            f.write("- [2026-09-01] Python version required: 3.13 for all runtime tasks.\n")

        auditor = MemoryAuditor(global_dir=self.global_dir, project_dir=self.project_dir)
        findings = auditor.run_full_audit()

        self.assertTrue(len(findings["contradictions"]) >= 1)
        report = auditor.generate_report()
        self.assertIn("Contradictions: 1", report)

    def test_unsupported_assumptions_detection(self):
        with open(os.path.join(self.project_dir, "DECISIONS.md"), "w") as f:
            f.write("- [2026-09-01] The cache server probably crashed due to memory leaks.\n")

        auditor = MemoryAuditor(global_dir=self.global_dir, project_dir=self.project_dir)
        findings = auditor.run_full_audit()

        self.assertTrue(len(findings["unsupported_assumptions"]) >= 1)
        report = auditor.generate_report()
        self.assertIn("Unsupported Assumptions", report)

    def test_oversized_file_detection(self):
        with open(os.path.join(self.project_dir, "CURRENT.md"), "w") as f:
            for i in range(60):
                f.write(f"Line {i} content exceeding line budget\n")

        auditor = MemoryAuditor(global_dir=self.global_dir, project_dir=self.project_dir)
        findings = auditor.run_full_audit()

        self.assertEqual(len(findings["oversized_files"]), 1)
        report = auditor.generate_report()
        self.assertIn("Oversized files: 1", report)


if __name__ == "__main__":
    unittest.main()
