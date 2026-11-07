#!/usr/bin/env python3
"""
Unit and integration tests for memory search engine (Phase 7 - Memory Search).
"""

import os
import sys
import unittest
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, "/workspaces/codespaces-blank/scripts")
from search_memory import (
    discover_memory_files,
    extract_section_snippets,
    run_memory_search,
    format_markdown_report,
    SCOPE_MAPPING
)

class TestMemorySearch(unittest.TestCase):

    def test_discover_memory_files_all(self):
        files = discover_memory_files(["all"])
        self.assertTrue(len(files) > 0)
        file_paths = [f[0] for f in files]
        # Should include global files and project files
        self.assertTrue(any("POLICY.md" in p for p in file_paths))
        self.assertTrue(any("ARCHITECTURE.md" in p for p in file_paths))

    def test_discover_memory_files_scoped(self):
        dec_files = discover_memory_files(["decisions"])
        self.assertTrue(any("DECISIONS.md" in f[0] for f in dec_files))
        self.assertFalse(any("ARCHITECTURE.md" in f[0] for f in dec_files))

        arch_files = discover_memory_files(["architecture"])
        self.assertTrue(any("ARCHITECTURE.md" in f[0] for f in arch_files))
        self.assertFalse(any("DECISIONS.md" in f[0] for f in arch_files))

    def test_keyword_search_ranking(self):
        res = run_memory_search(
            query="ADR-001",
            scopes=["decisions"],
            is_regex=False
        )
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["total_matches_count"] >= 1)
        top_match = res["results"][0]
        self.assertIn("ADR-001", top_match["snippet"])
        self.assertTrue(top_match["score"] >= 25)

    def test_regex_search(self):
        res = run_memory_search(
            query=r"ADR-\d+",
            scopes=["decisions"],
            is_regex=True
        )
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["total_matches_count"] >= 1)

    def test_invalid_regex_handling(self):
        res = run_memory_search(
            query=r"[unclosed-regex",
            scopes=["all"],
            is_regex=True
        )
        self.assertEqual(res["status"], "error")
        self.assertIn("Invalid regex pattern", res["message"])

    def test_multi_scope_search(self):
        res = run_memory_search(
            query="Antigravity",
            scopes=["architecture", "policy", "decisions"]
        )
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["total_matches_count"] >= 1)

    def test_markdown_report_generation(self):
        res = run_memory_search(query="Memory", scopes=["all"], max_results=3)
        report = format_markdown_report(res)
        self.assertIn("## Memory Search Results: `Memory`", report)
        self.assertIn("| Rank | Score | Scope | Source File | Heading / Context | Lines |", report)
        self.assertIn("### Extracted Relevant Snippets", report)

    def test_json_serializability(self):
        res = run_memory_search(query="Policy", scopes=["global"])
        dumped = json.dumps(res)
        loaded = json.loads(dumped)
        self.assertEqual(loaded["status"], "success")
        self.assertEqual(loaded["query"], "Policy")


if __name__ == "__main__":
    unittest.main()
