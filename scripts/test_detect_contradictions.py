import unittest
import os
import tempfile
from detect_contradictions import scan_files_for_contradictions, format_superseded_entry, find_superseded_blocks

class TestContradictions(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        
    def tearDown(self):
        self.test_dir.cleanup()

    def test_version_contradiction(self):
        f1 = os.path.join(self.test_dir.name, "f1.md")
        f2 = os.path.join(self.test_dir.name, "f2.md")
        with open(f1, "w") as f: f.write("Requires Python 3.11\n")
        with open(f2, "w") as f: f.write("Python >= 3.13 is needed\n")
        
        findings = scan_files_for_contradictions([f1, f2])
        if isinstance(findings, tuple): findings = findings[0]
        self.assertTrue(any("Python" in f for f in findings))

    def test_tool_contradiction(self):
        f1 = os.path.join(self.test_dir.name, "f1.md")
        f2 = os.path.join(self.test_dir.name, "f2.md")
        with open(f1, "w") as f: f.write("Use npm for package management\n")
        with open(f2, "w") as f: f.write("Use pnpm for package management\n")
        
        findings = scan_files_for_contradictions([f1, f2])
        if isinstance(findings, tuple): findings = findings[0]
        self.assertTrue(any("Package manager" in f for f in findings))
        
    def test_arch_contradiction(self):
        f1 = os.path.join(self.test_dir.name, "f1.md")
        f2 = os.path.join(self.test_dir.name, "f2.md")
        with open(f1, "w") as f: f.write("Architecture: monolithic\n")
        with open(f2, "w") as f: f.write("Architecture: microservices\n")
        
        findings = scan_files_for_contradictions([f1, f2])
        if isinstance(findings, tuple): findings = findings[0]
        self.assertTrue(any("Architecture" in f for f in findings))
        
    def test_superseded_entry(self):
        entry = format_superseded_entry(
            previous="Python 3.11",
            current="Python 3.13",
            reason="Security updates",
            date_str="2026-09-01",
            status="SUPERSEDED",
            canonical_source="config/main.yaml"
        )
        self.assertIn("## 2026-09-01 — Memory Update", entry)
        self.assertIn("**Status:** SUPERSEDED", entry)
        self.assertIn("**Source:** config/main.yaml", entry)

if __name__ == '__main__':
    unittest.main()
