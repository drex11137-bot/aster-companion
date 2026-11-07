#!/usr/bin/env python3
"""
test_query_router.py - Unit test suite for QueryRouter.
Tests query intent classification, scope routing, query expansion, and explicit abstention
per Instruction.md Sections 27, 30, 140, 141.
"""

import unittest
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from query_router import QueryRouter


class TestQueryRouter(unittest.TestCase):
    def setUp(self):
        self.router = QueryRouter(project_root="/workspaces/codespaces-blank", confidence_threshold=0.40)

    def test_intent_present_state(self):
        res = self.router.classify_intent("What is the active objective now?")
        self.assertEqual(res["intent"], "present-state")
        self.assertEqual(res["temporal"], "present")
        self.assertGreaterEqual(res["confidence"], 0.80)

        res2 = self.router.classify_intent("What is X now?")
        self.assertEqual(res2["intent"], "present-state")

    def test_intent_historical_as_of(self):
        res = self.router.classify_intent("What was the previous version of Antigravity CLI before 1.1.25?")
        self.assertEqual(res["intent"], "historical as-of")
        self.assertEqual(res["temporal"], "historical")
        self.assertGreaterEqual(res["confidence"], 0.80)

        res2 = self.router.classify_intent("What was X before?")
        self.assertEqual(res2["intent"], "historical as-of")

    def test_intent_procedural(self):
        res = self.router.classify_intent("How do we run tests?")
        self.assertEqual(res["intent"], "procedural")
        self.assertGreaterEqual(res["confidence"], 0.80)

        res2 = self.router.classify_intent("How do I do X?")
        self.assertEqual(res2["intent"], "procedural")

    def test_intent_debugging(self):
        res = self.router.classify_intent("Why did secret scanning fail?")
        self.assertEqual(res["intent"], "debugging")
        self.assertGreaterEqual(res["confidence"], 0.80)

        res2 = self.router.classify_intent("Why did X fail?")
        self.assertEqual(res2["intent"], "debugging")

    def test_intent_why_rationale(self):
        res = self.router.classify_intent("Why did we choose the 5-tier memory architecture?")
        self.assertEqual(res["intent"], "why/rationale")
        self.assertGreaterEqual(res["confidence"], 0.80)

        res2 = self.router.classify_intent("Why did we choose X?")
        self.assertEqual(res2["intent"], "why/rationale")

    def test_scope_determination_section_27(self):
        # Section 27: "How do we handle this repo's auth?" -> favors project memory
        s_auth = self.router.determine_scope("How do we handle this repo's auth?", intent="procedural")
        self.assertEqual(s_auth["primary"], "project")

        # Section 27: "What is our general Git merge convention?" -> may search global/tool memory
        s_git = self.router.determine_scope("What is our general Git merge convention?", intent="procedural")
        self.assertTrue(s_git["primary"] in ["tool", "global"])
        self.assertTrue("tool" in s_git["candidates"] or "global" in s_git["candidates"])

        # Domain query
        s_db = self.router.determine_scope("Postgres connection pooling guidelines", intent="procedural")
        self.assertEqual(s_db["primary"], "domain")

    def test_query_expansion_section_140(self):
        exp = self.router.expand_query("auth adr for k8s tests")
        self.assertIn("authentication", exp["abbreviations"].values())
        self.assertIn("architectural decision record", exp["abbreviations"].values())
        self.assertIn("kubernetes", exp["abbreviations"].values())
        self.assertTrue(len(exp["expanded_terms"]) <= 4)

    def test_abstention_section_30_on_run_tests(self):
        # "How do we run tests?" should abstain because memory does not contain test execution commands
        res = self.router.route_and_query("How do we run tests?")
        self.assertTrue(res["abstained"])
        self.assertEqual(res["message"], "No sufficiently trustworthy memory found")
        self.assertLess(res["max_confidence"], 0.40)

    def test_abstention_on_fabricated_query(self):
        res = self.router.route_and_query("What is the quantum teleportation frequency of this repository?")
        self.assertTrue(res["abstained"])
        self.assertEqual(res["message"], "No sufficiently trustworthy memory found")

    def test_successful_resolution_adr(self):
        res = self.router.route_and_query("Why did we choose the 5-tier memory architecture?")
        self.assertFalse(res["abstained"])
        self.assertGreaterEqual(res["max_confidence"], 0.40)
        self.assertIsNotNone(res["context_package"])
        self.assertIn("[MEMORY]", res["context_package"])


if __name__ == "__main__":
    unittest.main()
