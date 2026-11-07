#!/usr/bin/env python3
"""
Unit and integration tests for retrieval feedback ledger and telemetry engine.
Verifies compliance with Instruction.md Section 39, Section 40, and Section 78.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to sys.path
SCRIPT_DIR = "/workspaces/codespaces-blank/scripts"
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from memory_feedback import (
    FeedbackLedger,
    FeedbackOutcome,
    VALID_OUTCOMES,
    generate_synthetic_telemetry,
    format_markdown_metrics,
)


class TestFeedbackLedger(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.ledger_path = os.path.join(self.temp_dir.name, "test_retrieval_ledger.jsonl")
        self.ledger = FeedbackLedger(self.ledger_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_record_single_event_success(self):
        rec = self.ledger.record_event(
            query_id="q_test_1",
            memory_id="DECISIONS.md#ADR-001",
            was_visible=True,
            rank=1,
            used_in_action=True,
            outcome=FeedbackOutcome.VERIFIED_OUTCOME.value,
            helpful=True,
            prevented_error=True,
            latency_ms=12.5,
            context_tokens=100,
        )
        self.assertEqual(rec["query_id"], "q_test_1")
        self.assertEqual(rec["memory_id"], "DECISIONS.md#ADR-001")
        self.assertTrue(rec["was_visible"])
        self.assertEqual(rec["rank"], 1)
        self.assertTrue(rec["used_in_action"])
        self.assertEqual(rec["outcome"], FeedbackOutcome.VERIFIED_OUTCOME.value)
        self.assertTrue(rec["helpful"])
        self.assertTrue(rec["prevented_error"])

        # Read back from ledger file
        records = self.ledger.read_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["query_id"], "q_test_1")

    def test_outcome_validation(self):
        # Valid outcomes should pass
        for outcome in VALID_OUTCOMES:
            self.ledger.record_event(
                query_id="q_val",
                memory_id="doc.md",
                was_visible=True,
                rank=1,
                used_in_action=False,
                outcome=outcome,
            )

        # Invalid outcome should raise ValueError
        with self.assertRaises(ValueError) as ctx:
            self.ledger.record_event(
                query_id="q_val_fail",
                memory_id="doc.md",
                was_visible=True,
                rank=1,
                used_in_action=False,
                outcome="INVALID_OUTCOME_LABEL",
            )
        self.assertIn("Invalid outcome", str(ctx.exception))

    def test_secret_scanner_blocks_leaks(self):
        # Dynamically constructed token to test Zero-Secrets enforcement at runtime
        fake_token = "".join(["sk", "-proj-", "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567890123456789"])
        with self.assertRaises(ValueError) as ctx:
            self.ledger.record_event(
                query_id="q_leak",
                memory_id="config.env",
                was_visible=True,
                rank=1,
                used_in_action=True,
                outcome=FeedbackOutcome.INFERRED_USAGE.value,
                metadata={"secret": fake_token},
            )
        self.assertIn("Zero-Secrets Policy violation", str(ctx.exception))

    def test_visibility_vs_usage_distinction_section_39(self):
        """
        Verify Section 39:
        Distinguish 'not shown' (was_visible=False) from 'shown but unused' (was_visible=True, used=False).
        """
        self.ledger.record_batch([
            {
                "query_id": "q_vis_test",
                "memory_id": "item_shown_used.md",
                "was_visible": True,
                "rank": 1,
                "used_in_action": True,
                "outcome": FeedbackOutcome.VERIFIED_OUTCOME.value,
            },
            {
                "query_id": "q_vis_test",
                "memory_id": "item_shown_unused.md",
                "was_visible": True,
                "rank": 2,
                "used_in_action": False,
                "outcome": FeedbackOutcome.INFERRED_NONUSE.value,
            },
            {
                "query_id": "q_vis_test",
                "memory_id": "item_not_shown.md",
                "was_visible": False,
                "rank": 3,
                "used_in_action": False,
                "outcome": FeedbackOutcome.INFERRED_NONUSE.value,
            },
        ])

        metrics = self.ledger.compute_metrics()
        self.assertEqual(metrics["counts"]["visible"], 2)
        self.assertEqual(metrics["counts"]["not_visible"], 1)
        self.assertEqual(metrics["counts"]["used"], 1)
        self.assertEqual(metrics["counts"]["shown_unused"], 1)

    def test_mrr_calculation_exact(self):
        """
        Query 1: First relevant hit at rank 1 -> RR = 1.0
        Query 2: First relevant hit at rank 2 -> RR = 0.5
        Query 3: First relevant hit at rank 4 -> RR = 0.25
        Query 4: No relevant hit -> RR = 0.0
        Expected MRR = (1.0 + 0.5 + 0.25 + 0.0) / 4 = 1.75 / 4 = 0.4375
        """
        records = [
            # Q1
            {"query_id": "q1", "memory_id": "m1", "was_visible": True, "rank": 1, "used_in_action": True, "outcome": "VERIFIED_OUTCOME"},
            # Q2
            {"query_id": "q2", "memory_id": "m2_bad", "was_visible": True, "rank": 1, "used_in_action": False, "outcome": "INFERRED_NONUSE"},
            {"query_id": "q2", "memory_id": "m2_good", "was_visible": True, "rank": 2, "used_in_action": True, "outcome": "VERIFIED_OUTCOME"},
            # Q3
            {"query_id": "q3", "memory_id": "m3_1", "was_visible": True, "rank": 1, "used_in_action": False, "outcome": "INFERRED_NONUSE"},
            {"query_id": "q3", "memory_id": "m3_2", "was_visible": True, "rank": 2, "used_in_action": False, "outcome": "INFERRED_NONUSE"},
            {"query_id": "q3", "memory_id": "m3_3", "was_visible": True, "rank": 3, "used_in_action": False, "outcome": "INFERRED_NONUSE"},
            {"query_id": "q3", "memory_id": "m3_4", "was_visible": True, "rank": 4, "used_in_action": True, "outcome": "INFERRED_USAGE"},
            # Q4 (stale memory, not relevant)
            {"query_id": "q4", "memory_id": "m4", "was_visible": True, "rank": 1, "used_in_action": True, "wrong": True, "outcome": "EXPLICIT_FEEDBACK"},
        ]
        self.ledger.record_batch(records)
        metrics = self.ledger.compute_metrics()
        self.assertAlmostEqual(metrics["mrr"], 0.4375, places=4)

    def test_ndcg10_calculation_exact(self):
        """
        Query A:
        Rank 1: rel = 3.0 (VERIFIED_OUTCOME, used)
        DCG = (2^3 - 1)/log2(2) = 7.0 / 1.0 = 7.0
        IDCG = 7.0 -> NDCG = 1.0
        """
        self.ledger.record_event(
            query_id="qA",
            memory_id="mA",
            was_visible=True,
            rank=1,
            used_in_action=True,
            outcome="VERIFIED_OUTCOME",
        )
        metrics = self.ledger.compute_metrics()
        self.assertAlmostEqual(metrics["ndcg_at_10"], 1.0, places=4)

    def test_false_recall_rate_and_abstention(self):
        """
        Test False Recall Rate and Section 78 Abstention:
        - 1 regular query with 1 relevant item and 1 irrelevant visible item.
        - 1 abstention query with 0 items returned (abstention success).
        - 1 abstention query with 1 irrelevant item returned (false recall on absent memory).
        """
        records = [
            {"query_id": "q_reg", "memory_id": "good.md", "was_visible": True, "rank": 1, "used_in_action": True, "outcome": "VERIFIED_OUTCOME"},
            {"query_id": "q_reg", "memory_id": "noise.md", "was_visible": True, "rank": 2, "used_in_action": False, "outcome": "INFERRED_NONUSE"},
            # Abstention 1: perfect
            {"query_id": "q_abs_good", "memory_id": "none", "was_visible": False, "rank": None, "used_in_action": False, "outcome": "INFERRED_NONUSE", "metadata": {"is_abstention": True}},
            # Abstention 2: false recall
            {"query_id": "q_abs_bad", "memory_id": "unwanted.md", "was_visible": True, "rank": 1, "used_in_action": False, "wrong": True, "outcome": "INFERRED_NONUSE", "metadata": {"is_abstention": True}},
        ]
        self.ledger.record_batch(records)
        metrics = self.ledger.compute_metrics()

        # Visible items: 3 total (good.md, noise.md, unwanted.md)
        # False recalls among visible items: noise.md (irrelevant/nonuse) and unwanted.md (wrong) -> 2 false recalls
        self.assertEqual(metrics["counts"]["visible"], 3)
        self.assertAlmostEqual(metrics["false_recall_rate"], 2 / 3, places=3)
        # Strict false recall: only unwanted.md (wrong=True) -> 1 / 3
        self.assertAlmostEqual(metrics["strict_false_recall_rate"], 1 / 3, places=3)
        # Abstention false recall: 1 failure out of 2 abstention queries -> 0.5
        self.assertAlmostEqual(metrics["abstention_false_recall_rate"], 0.5, places=3)

    def test_empty_ledger_handles_gracefully(self):
        metrics = self.ledger.compute_metrics()
        self.assertEqual(metrics["status"], "empty")
        self.assertEqual(metrics["mrr"], 0.0)
        self.assertEqual(metrics["ndcg_at_10"], 0.0)
        self.assertEqual(metrics["false_recall_rate"], 0.0)
        self.assertEqual(metrics["total_records"], 0)

    def test_synthetic_telemetry_batch(self):
        events = generate_synthetic_telemetry()
        self.assertTrue(len(events) >= 10)
        self.ledger.record_batch(events)
        metrics = self.ledger.compute_metrics()
        self.assertEqual(metrics["status"], "success")
        self.assertEqual(metrics["total_queries"], 10)
        self.assertTrue(metrics["mrr"] > 0.5)
        self.assertTrue(metrics["ndcg_at_10"] > 0.6)

        # Markdown report generation
        md = format_markdown_metrics(metrics, self.ledger.ledger_path)
        self.assertIn("## Retrieval Feedback & Telemetry Metrics Report", md)
        self.assertIn("MRR (Mean Reciprocal Rank)", md)
        self.assertIn("NDCG@10", md)
        self.assertIn("False Recall Rate", md)


if __name__ == "__main__":
    unittest.main()
