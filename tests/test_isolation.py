#!/usr/bin/env python3
"""
Multi-Repo Workspace Isolation Test (Section 31).
Verifies that project memory in Repository A does NOT leak into Repository B.
"""

import os
import sys
import unittest
import tempfile
import shutil
import subprocess

SCRIPT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
MEMORY_ENGINE_BIN = os.path.join(SCRIPT_DIR, "memory_engine.py")

class TestMultiRepoIsolation(unittest.TestCase):
    def setUp(self):
        # Create base temporary directory
        self.base_dir = tempfile.mkdtemp(prefix="antigravity_isolation_")
        
        self.project_a_dir = os.path.join(self.base_dir, "project-A")
        self.project_b_dir = os.path.join(self.base_dir, "project-B")
        
        os.makedirs(os.path.join(self.project_a_dir, ".agents", "memory"), exist_ok=True)
        os.makedirs(os.path.join(self.project_b_dir, ".agents", "memory"), exist_ok=True)
        
        # Populate project-A memory
        with open(os.path.join(self.project_a_dir, ".agents", "memory", "DECISIONS.md"), "w") as f:
            f.write("# Architectural Decisions\n- This project uses Postgres.\n")
            
        # Populate project-B memory
        with open(os.path.join(self.project_b_dir, ".agents", "memory", "DECISIONS.md"), "w") as f:
            f.write("# Architectural Decisions\n- This project uses MongoDB.\n")

    def tearDown(self):
        shutil.rmtree(self.base_dir, ignore_errors=True)

    def _run_search(self, cwd, query):
        env = os.environ.copy()
        result = subprocess.run(
            [sys.executable, MEMORY_ENGINE_BIN, "search-memory", query, "--scope", "project"],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True
        )
        return result.stdout

    def test_isolation_boundary(self):
        # In Project A, we should see Postgres but NOT MongoDB
        out_a_postgres = self._run_search(self.project_a_dir, "Postgres")
        out_a_mongodb = self._run_search(self.project_a_dir, "MongoDB")
        
        self.assertIn("Found 1 match", out_a_postgres, "Project A should find its own memory (Postgres)")
        self.assertIn("No results found", out_a_mongodb, "Project A should NOT find Project B's memory (MongoDB)")

        # In Project B, we should see MongoDB but NOT Postgres
        out_b_mongodb = self._run_search(self.project_b_dir, "MongoDB")
        out_b_postgres = self._run_search(self.project_b_dir, "Postgres")
        
        self.assertIn("Found 1 match", out_b_mongodb, "Project B should find its own memory (MongoDB)")
        self.assertIn("No results found", out_b_postgres, "Project B should NOT find Project A's memory (Postgres)")

if __name__ == "__main__":
    unittest.main()
