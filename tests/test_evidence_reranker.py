#!/usr/bin/env python3
"""
test_evidence_reranker.py - Verification of Multi-Signal Evidence Reranking.
Enforces Instruction.md Section 17 & 22: Relevance != Truth.
"""

import os
import sys
import tempfile
import unittest
import shutil

# Ensure scripts directory is in path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(WORKSPACE_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from evidence_reranker import (
    EvidenceReranker,
    SourceTier,
    TrustVerdict,
    SOURCE_TIER_WEIGHTS,
    CONFIDENCE_TIER_WEIGHTS,
    SUPERSEDED_PENALTY,
    STALE_PENALTY,
)
from search_memory import run_memory_search


class TestEvidenceReranker(unittest.TestCase):
    """
    Test suite verifying multi-signal evidence scoring, authority tiers,
    temporal penalties, and the core invariant: Relevance != Truth.
    """

    def setUp(self):
        self.reranker = EvidenceReranker(project_root=WORKSPACE_ROOT)
        self.temp_dir = tempfile.mkdtemp(prefix="test_reranker_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_source_tier_weights(self):
        """Verify explicit source tier authority hierarchy per Section 22."""
        self.assertEqual(SOURCE_TIER_WEIGHTS["USER_EXPLICIT"], 1.0)
        self.assertEqual(SOURCE_TIER_WEIGHTS["EXECUTED_TEST"], 0.95)
        self.assertEqual(SOURCE_TIER_WEIGHTS["REPOSITORY_SOURCE"], 0.9)
        self.assertEqual(SOURCE_TIER_WEIGHTS["AGENT_OBSERVATION"], 0.7)
        self.assertEqual(SOURCE_TIER_WEIGHTS["AGENT_INFERENCE"], 0.4)
        self.assertEqual(SOURCE_TIER_WEIGHTS["UNVERIFIED"], 0.2)

        # Invariant: USER_EXPLICIT > EXECUTED_TEST > REPOSITORY_SOURCE > AGENT_OBSERVATION > AGENT_INFERENCE > UNVERIFIED
        self.assertGreater(SOURCE_TIER_WEIGHTS["USER_EXPLICIT"], SOURCE_TIER_WEIGHTS["EXECUTED_TEST"])
        self.assertGreater(SOURCE_TIER_WEIGHTS["EXECUTED_TEST"], SOURCE_TIER_WEIGHTS["REPOSITORY_SOURCE"])
        self.assertGreater(SOURCE_TIER_WEIGHTS["REPOSITORY_SOURCE"], SOURCE_TIER_WEIGHTS["AGENT_OBSERVATION"])
        self.assertGreater(SOURCE_TIER_WEIGHTS["AGENT_OBSERVATION"], SOURCE_TIER_WEIGHTS["AGENT_INFERENCE"])
        self.assertGreater(SOURCE_TIER_WEIGHTS["AGENT_INFERENCE"], SOURCE_TIER_WEIGHTS["UNVERIFIED"])

    def test_superseded_penalty(self):
        """Verify -0.5 temporal validity penalty for superseded records."""
        self.assertEqual(SUPERSEDED_PENALTY, -0.5)

        # Snippet marked with status=SUPERSEDED
        item_status = {
            "snippet": "**Status:** SUPERSEDED\nWe previously configured port 8080.",
            "heading": "## Old Port Decision",
            "file": "/workspaces/codespaces-blank/.agents/memory/DECISIONS.md",
            "score": 50.0
        }
        signals_status = self.reranker.extract_signals(item_status)
        self.assertTrue(signals_status.is_superseded)
        self.assertEqual(signals_status.temporal_status, "SUPERSEDED")
        self.assertEqual(signals_status.temporal_penalty, -0.5)
        self.assertEqual(signals_status.trust_verdict, TrustVerdict.SUPERSEDED.value)

        # Snippet marked with [SUPERSEDED] tag in heading
        item_tag = {
            "snippet": "**Confidence:** VERIFIED\nWe use port 8080.",
            "heading": "## ADR-005: [SUPERSEDED] Old Port Decision",
            "file": "/workspaces/codespaces-blank/.agents/memory/DECISIONS.md",
            "score": 50.0
        }
        signals_tag = self.reranker.extract_signals(item_tag)
        self.assertTrue(signals_tag.is_superseded)
        self.assertEqual(signals_tag.temporal_penalty, -0.5)
        self.assertEqual(signals_tag.trust_verdict, TrustVerdict.SUPERSEDED.value)

        # Snippet with explicit [SUPERSEDED on 2026-09-02 by id:cand-001]
        item_full_tag = {
            "snippet": "**Status:** SUPERSEDED [SUPERSEDED on 2026-09-02 by id:cand-001]\nLegacy setting.",
            "heading": "## Port Config",
            "file": "/workspaces/codespaces-blank/.agents/memory/DECISIONS.md",
            "score": 50.0
        }
        signals_full = self.reranker.extract_signals(item_full_tag)
        self.assertTrue(signals_full.is_superseded)
        self.assertEqual(signals_full.superseded_by, "cand-001")
        self.assertEqual(signals_full.temporal_penalty, -0.5)

    def test_relevance_not_equal_truth_unverified_vs_authoritative(self):
        """
        CORE INVARIANT (Instruction.md Section 17 & 22):
        An unverified record with 10x higher lexical relevance MUST NEVER outrank
        an authoritative current fact with low lexical relevance.
        """
        # Unverified claim with massive keyword stuffing (lexical score = 120.0)
        unverified_snippet = {
            "id": "unverified_item",
            "file": "/workspaces/codespaces-blank/.agents/memory/inbox/notes.md",
            "scope": "project",
            "heading": "## Unverified Agent Speculation",
            "snippet": (
                "**Type:** NOTE **Confidence:** UNVERIFIED **Source:** UNVERIFIED **Status:** ACTIVE\n"
                "database database database database postgresql postgresql migration\n"
                "I guess we might use SQLite for production database database."
            ),
            "score": 120.0,
            "start_line": 10,
            "end_line": 15
        }

        # Authoritative repository fact with minimal lexical match (lexical score = 10.0)
        authoritative_snippet = {
            "id": "authoritative_item",
            "file": "/workspaces/codespaces-blank/.agents/memory/DECISIONS.md",
            "scope": "decisions",
            "heading": "## ADR-042: Production Database Engine",
            "snippet": (
                "**Type:** DECISION **Scope:** PROJECT **Confidence:** VERIFIED **Source:** REPOSITORY_SOURCE **Status:** ACTIVE\n"
                "The canonical production database is PostgreSQL 16."
            ),
            "score": 10.0,
            "start_line": 20,
            "end_line": 25
        }

        # 1. Without reranking (pure lexical): unverified outranks authoritative (THE DEFECT)
        candidates_raw = [dict(unverified_snippet), dict(authoritative_snippet)]
        candidates_raw.sort(key=lambda x: x["score"], reverse=True)
        self.assertEqual(candidates_raw[0]["id"], "unverified_item", "Baseline lexical search would rank unverified first")

        # 2. With evidence reranking: authoritative MUST strictly outrank unverified
        candidates_reranked = [dict(unverified_snippet), dict(authoritative_snippet)]
        reranked = self.reranker.rerank_results(candidates_reranked, apply_reranker=True)

        self.assertEqual(reranked[0]["id"], "authoritative_item")
        self.assertEqual(reranked[1]["id"], "unverified_item")
        self.assertGreater(reranked[0]["score"], reranked[1]["score"])
        self.assertEqual(reranked[0]["trust_verdict"], TrustVerdict.CERTIFY.value)
        self.assertEqual(reranked[1]["trust_verdict"], TrustVerdict.UNVERIFIED.value)
        # Verify authoritative score is in Tier 4 [70.0, 100.0] while unverified is in Tier 1 [15.0, 28.0]
        self.assertGreaterEqual(reranked[0]["score"], 70.0)
        self.assertLessEqual(reranked[1]["score"], 28.0)

    def test_relevance_not_equal_truth_superseded_vs_authoritative(self):
        """
        CORE INVARIANT:
        A superseded record with massive keyword relevance MUST NEVER outrank
        an active authoritative fact with minimal relevance.
        """
        superseded_snippet = {
            "id": "superseded_item",
            "file": "/workspaces/codespaces-blank/.agents/memory/DECISIONS.md",
            "scope": "decisions",
            "heading": "## ADR-010: [SUPERSEDED] Authentication Provider",
            "snippet": (
                "**Type:** DECISION **Confidence:** VERIFIED **Source:** REPOSITORY_SOURCE **Status:** SUPERSEDED\n"
                "auth authentication auth auth auth jwt token session auth auth auth\n"
                "We use local session cookies."
            ),
            "score": 150.0,
            "start_line": 1,
            "end_line": 6
        }

        active_snippet = {
            "id": "active_item",
            "file": "/workspaces/codespaces-blank/.agents/memory/DECISIONS.md",
            "scope": "decisions",
            "heading": "## ADR-020: Authentication Upgrade",
            "snippet": (
                "**Type:** DECISION **Confidence:** VERIFIED **Source:** REPOSITORY_SOURCE **Status:** ACTIVE\n"
                "We use OAuth2 and OIDC authentication tokens."
            ),
            "score": 20.0,
            "start_line": 10,
            "end_line": 15
        }

        # Rerank
        results = [dict(superseded_snippet), dict(active_snippet)]
        reranked = self.reranker.rerank_results(results, apply_reranker=True)

        self.assertEqual(reranked[0]["id"], "active_item")
        self.assertEqual(reranked[1]["id"], "superseded_item")
        self.assertGreater(reranked[0]["score"], reranked[1]["score"])
        self.assertEqual(reranked[0]["trust_verdict"], TrustVerdict.CERTIFY.value)
        self.assertEqual(reranked[1]["trust_verdict"], TrustVerdict.SUPERSEDED.value)
        # Active authoritative is in Tier 4 (>= 70.0), superseded is in Tier 0 (<= 15.0)
        self.assertGreaterEqual(reranked[0]["score"], 70.0)
        self.assertLessEqual(reranked[1]["score"], 15.0)

    def test_agent_inference_never_outranks_executed_test(self):
        """
        Section 22: 'An agent saying I think this is probably true must never outrank
        an executed repository test proving otherwise.'
        """
        inference_snippet = {
            "id": "agent_inference_item",
            "file": "/workspaces/codespaces-blank/.agents/memory/sessions/2026-09-02-1430.md",
            "scope": "sessions",
            "heading": "## Agent Speculation",
            "snippet": (
                "**Confidence:** HIGH **Source:** AGENT_INFERENCE **Status:** ACTIVE\n"
                "memory memory memory memory leak leak leak leak leak\n"
                "I think the memory leak is probably caused by Gradle daemon."
            ),
            "score": 100.0,
            "start_line": 1,
            "end_line": 5
        }

        executed_test_snippet = {
            "id": "executed_test_item",
            "file": "/workspaces/codespaces-blank/tests/test_memory_compiler.py",
            "scope": "project",
            "heading": "## Memory Leak Execution Test",
            "snippet": (
                "**Confidence:** VERIFIED **Source:** EXECUTED_TEST **Status:** ACTIVE\n"
                "test_memory_leak passed without leak; verified container limits."
            ),
            "score": 15.0,
            "start_line": 100,
            "end_line": 105
        }

        results = [dict(inference_snippet), dict(executed_test_snippet)]
        reranked = self.reranker.rerank_results(results, apply_reranker=True)

        self.assertEqual(reranked[0]["id"], "executed_test_item")
        self.assertEqual(reranked[1]["id"], "agent_inference_item")
        self.assertGreater(reranked[0]["score"], reranked[1]["score"])
        self.assertGreaterEqual(reranked[0]["score"], 70.0)
        self.assertLessEqual(reranked[1]["score"], 48.0)

    def test_epistemic_confidence_separation_from_source(self):
        """Section 17: Audit that epistemic_confidence and source_authority are separated."""
        item = {
            "snippet": "**Confidence:** 0.85 **Source:** EXECUTED_TEST **Status:** ACTIVE\nTest fact.",
            "heading": "## Test Run",
            "file": "/workspaces/codespaces-blank/tests/test_foo.py",
            "score": 30.0
        }
        signals = self.reranker.extract_signals(item)
        self.assertEqual(signals.source_tier, "EXECUTED_TEST")
        self.assertEqual(signals.source_authority, 0.95)
        self.assertEqual(signals.epistemic_confidence, 0.85)
        self.assertEqual(signals.temporal_penalty, 0.0)

    def test_end_to_end_search_memory_with_reranking(self):
        """End-to-end integration test with run_memory_search on temporary files."""
        # Create temp project structure
        mem_dir = os.path.join(self.temp_dir, ".agents", "memory")
        os.makedirs(mem_dir, exist_ok=True)

        # Write authoritative DECISIONS.md
        dec_file = os.path.join(mem_dir, "DECISIONS.md")
        with open(dec_file, "w", encoding="utf-8") as f:
            f.write(
                "# Project Architectural Decisions\n\n"
                "## 2026-09-01 — ADR-099: Web Framework Choice\n"
                "**Type:** DECISION **Scope:** PROJECT **Confidence:** VERIFIED **Source:** REPOSITORY_SOURCE **Status:** ACTIVE\n"
                "### What\n"
                "We use FastAPI for backend APIs.\n"
            )

        # Write superseded GOTCHAS.md with high keyword stuffing
        gotchas_file = os.path.join(mem_dir, "GOTCHAS.md")
        with open(gotchas_file, "w", encoding="utf-8") as f:
            f.write(
                "# Gotchas\n\n"
                "## 2026-09-01 — Old Framework [SUPERSEDED]\n"
                "**Type:** GOTCHA **Scope:** PROJECT **Confidence:** VERIFIED **Source:** REPOSITORY_SOURCE **Status:** SUPERSEDED\n"
                "### What\n"
                "FastAPI FastAPI FastAPI FastAPI framework choice backend backend backend.\n"
                "Flask was previously used.\n"
            )

        # Query with reranker enabled (default)
        res_reranked = run_memory_search(
            query="FastAPI framework backend",
            scopes=["project"],
            project_root=self.temp_dir,
            apply_reranker=True
        )
        self.assertEqual(res_reranked["status"], "success")
        self.assertGreaterEqual(res_reranked["total_matches_count"], 2)
        # ADR-099 (ACTIVE, REPOSITORY_SOURCE) must rank #1
        top_reranked = res_reranked["results"][0]
        self.assertIn("ADR-099", top_reranked["heading"])
        self.assertEqual(top_reranked["temporal_status"], "ACTIVE")
        self.assertEqual(top_reranked["trust_verdict"], "CERTIFY")

        # Second match is the superseded entry
        second_reranked = res_reranked["results"][1]
        self.assertEqual(second_reranked["temporal_status"], "SUPERSEDED")
        self.assertEqual(second_reranked["trust_verdict"], "SUPERSEDED")
        self.assertGreater(top_reranked["score"], second_reranked["score"])

        # Query with reranker disabled (--no-rerank)
        res_no_rerank = run_memory_search(
            query="FastAPI framework backend",
            scopes=["project"],
            project_root=self.temp_dir,
            apply_reranker=False
        )
        # Without reranker, the superseded entry with repeated keywords outranks the active decision
        top_no_rerank = res_no_rerank["results"][0]
        self.assertIn("Old Framework", top_no_rerank["heading"], "Without reranker, raw lexical match outranks truth")


if __name__ == "__main__":
    unittest.main()
