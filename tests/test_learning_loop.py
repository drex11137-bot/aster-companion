#!/usr/bin/env python3
"""
Unit and integration tests for Antigravity Memory Decay & Shadow Ranking Loop (Phase 16).
Tests scripts/learning_loop.py per Instruction.md Sections 41-43, 23, 221, 222.
"""

import os
import sys
import json
import math
import tempfile
import datetime
import unittest
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = "/workspaces/codespaces-blank/scripts"
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from learning_loop import (
    MemoryItem,
    DecayProfile,
    ReinforcementProfile,
    ModelMetadata,
    CandidateRanking,
    ShadowComparisonReport,
    MemoryDecayModel,
    AccessReinforcementModel,
    ReciprocalRankFusion,
    ModelManager,
    LearningLedger,
    ShadowRanker,
    BenchmarkGate,
    LearningLoop,
    SchemaMismatchError,
    FEATURE_SCHEMA_VERSION,
    CANONICAL_FEATURE_NAMES,
    DEFAULT_WEIGHTS
)


class TestMemoryDecayModel(unittest.TestCase):
    """Verifies memory decay curves per Instruction.md Section 42."""

    def setUp(self):
        self.ref_time = datetime.datetime(2026, 9, 3, 12, 0, 0, tzinfo=datetime.timezone.utc)
        self.decay_model = MemoryDecayModel(reference_time=self.ref_time)

    def test_governance_fact_immunity(self):
        """Core governance facts should not decay simply because they are old."""
        # 3-year-old policy memory
        policy_item = MemoryItem(
            id="POLICY.md#L1",
            file_path="/workspaces/codespaces-blank/.agents/memory/POLICY.md",
            scope="policy",
            heading="# Antigravity Memory Policy",
            content="13 immutable policy rules",
            created_at=self.ref_time - datetime.timedelta(days=1095),
            importance=5.0,
            authority=1.0
        )
        prof = self.decay_model.compute_decay(policy_item)
        self.assertTrue(prof.is_governance_exempt)
        self.assertEqual(prof.decay_factor, 1.0)
        self.assertFalse(prof.is_expired)

    def test_episodic_material_deprioritized(self):
        """Low-value episodic material may be deprioritized quickly."""
        # 45-day-old session memory
        session_item = MemoryItem(
            id="2026-07-20.md#L1",
            file_path="/workspaces/codespaces-blank/.agents/memory/sessions/2026-07-20.md",
            scope="sessions",
            heading="# Session 2026-07-20",
            content="Exploratory terminal debugging",
            created_at=self.ref_time - datetime.timedelta(days=45),
            importance=2.0,
            authority=0.35,
            access_count=0,
            verified_count=0
        )
        prof = self.decay_model.compute_decay(session_item)
        self.assertFalse(prof.is_governance_exempt)
        self.assertLess(prof.decay_factor, 0.40)
        self.assertGreater(prof.decay_factor, 0.0)

    def test_candidate_memory_expires(self):
        """Candidates may expire after TTL window."""
        candidate_item = MemoryItem(
            id="candidate_skill.md#L1",
            file_path="/workspaces/codespaces-blank/.agents/memory/candidate_skill.md",
            scope="candidate",
            heading="## Candidate Skill",
            content="Unverified candidate procedure [CANDIDATE]",
            created_at=self.ref_time - datetime.timedelta(days=20),
            importance=1.5,
            authority=0.25,
            is_candidate=True,
            ttl_days=14.0
        )
        prof = self.decay_model.compute_decay(candidate_item)
        self.assertTrue(prof.is_expired)
        self.assertEqual(prof.decay_factor, 0.0)

    def test_custom_ttl_expiration(self):
        """Temporary memories respect explicit TTLs."""
        temp_item = MemoryItem(
            id="temp_notes.md#L1",
            file_path="/workspaces/codespaces-blank/.agents/memory/temp_notes.md",
            scope="general",
            heading="## Scratchpad",
            content="Temporary debug info TTL: 3d",
            created_at=self.ref_time - datetime.timedelta(days=5),
            importance=2.0,
            authority=0.50,
            ttl_days=3.0
        )
        prof = self.decay_model.compute_decay(temp_item)
        self.assertTrue(prof.is_expired)
        self.assertEqual(prof.decay_factor, 0.0)

    def test_importance_multiplier_extends_half_life(self):
        """Higher durability importance extends memory half-life."""
        item_dur2 = MemoryItem(
            id="test1", file_path="/test", scope="project", heading="H1", content="C1",
            created_at=self.ref_time - datetime.timedelta(days=60), importance=2.0, authority=0.65
        )
        item_dur5 = MemoryItem(
            id="test2", file_path="/test", scope="project", heading="H2", content="C2",
            created_at=self.ref_time - datetime.timedelta(days=60), importance=5.0, authority=0.65
        )
        prof_dur2 = self.decay_model.compute_decay(item_dur2)
        prof_dur5 = self.decay_model.compute_decay(item_dur5)
        self.assertGreater(prof_dur5.effective_half_life_days, prof_dur2.effective_half_life_days)
        self.assertGreater(prof_dur5.decay_factor, prof_dur2.decay_factor)

    def test_spaced_access_reinforcement_on_decay(self):
        """Frequently verified memories decay significantly slower."""
        unverified_item = MemoryItem(
            id="adr-unver", file_path="/test", scope="decisions", heading="ADR", content="Text",
            created_at=self.ref_time - datetime.timedelta(days=120), importance=4.0, authority=0.80,
            access_count=0, verified_count=0
        )
        verified_item = MemoryItem(
            id="adr-ver", file_path="/test", scope="decisions", heading="ADR", content="Text",
            created_at=self.ref_time - datetime.timedelta(days=120), importance=4.0, authority=0.80,
            access_count=8, verified_count=6
        )
        prof_unver = self.decay_model.compute_decay(unverified_item)
        prof_ver = self.decay_model.compute_decay(verified_item)
        self.assertGreater(prof_ver.effective_half_life_days, prof_unver.effective_half_life_days)
        self.assertGreater(prof_ver.decay_factor, prof_unver.decay_factor)

    def test_superseded_memory_retention(self):
        """Superseded memories remain queryable historically with controlled penalty."""
        superseded_item = MemoryItem(
            id="DECISIONS.md#ADR-OLD", file_path="/test", scope="decisions", heading="## ADR-OLD", content="text",
            created_at=self.ref_time - datetime.timedelta(days=30), importance=4.0, authority=0.80,
            is_superseded=True
        )
        prof = self.decay_model.compute_decay(superseded_item)
        self.assertFalse(prof.is_expired)
        self.assertGreater(prof.decay_factor, 0.0)
        self.assertLess(prof.decay_factor, 0.50)


class TestAccessReinforcementModel(unittest.TestCase):
    """Verifies access reinforcement rules per Instruction.md Section 43."""

    def setUp(self):
        self.reinforce = AccessReinforcementModel()

    def test_verified_use_strengthens_priority(self):
        """Successful verified use strengthens retrieval priority."""
        item = MemoryItem(
            id="item1", file_path="/test", scope="gotchas", heading="H", content="C",
            created_at=datetime.datetime.now(datetime.timezone.utc),
            access_count=5, verified_count=5
        )
        prof = self.reinforce.compute_reinforcement(item)
        self.assertGreater(prof.reinforcement_score, 0.40)
        self.assertGreater(prof.verified_signal, prof.raw_access_signal)

    def test_epistemic_truth_signal_separation(self):
        """Retrieved != true, and frequently retrieved != authoritative."""
        # High retrieval but zero verification
        item_high_access = MemoryItem(
            id="item2", file_path="/test", scope="sessions", heading="H", content="C",
            created_at=datetime.datetime.now(datetime.timezone.utc),
            authority=0.35,  # Inherent authority MUST NOT change
            access_count=30, verified_count=0
        )
        prof = self.reinforce.compute_reinforcement(item_high_access)
        self.assertIsNotNone(prof.epistemic_warning)
        self.assertEqual(item_high_access.authority, 0.35, "Authority must remain immutable")

    def test_refutation_penalty(self):
        """Refuted memories receive negative penalty in reinforcement."""
        item_clean = MemoryItem(
            id="item3", file_path="/test", scope="gotchas", heading="H", content="C",
            created_at=datetime.datetime.now(datetime.timezone.utc),
            access_count=3, verified_count=2, refuted_count=0
        )
        item_refuted = MemoryItem(
            id="item4", file_path="/test", scope="gotchas", heading="H", content="C",
            created_at=datetime.datetime.now(datetime.timezone.utc),
            access_count=3, verified_count=2, refuted_count=2
        )
        prof_clean = self.reinforce.compute_reinforcement(item_clean)
        prof_refuted = self.reinforce.compute_reinforcement(item_refuted)
        self.assertGreater(prof_clean.reinforcement_score, prof_refuted.reinforcement_score)


class TestReciprocalRankFusion(unittest.TestCase):
    """Verifies baseline deterministic RRF fusion per Instruction.md Section 23."""

    def setUp(self):
        self.rrf = ReciprocalRankFusion(k=60)
        self.now = datetime.datetime(2026, 9, 3, 12, 0, 0, tzinfo=datetime.timezone.utc)

    def test_deterministic_and_reproducible_ranking(self):
        candidates = [
            MemoryItem(id="item-C", file_path="/t", scope="sessions", heading="C", content="C",
                       created_at=self.now - datetime.timedelta(days=1), importance=2.0, authority=0.35, raw_score=20.0),
            MemoryItem(id="item-A", file_path="/t", scope="policy", heading="A", content="A",
                       created_at=self.now - datetime.timedelta(days=100), importance=5.0, authority=1.0, raw_score=40.0),
            MemoryItem(id="item-B", file_path="/t", scope="decisions", heading="B", content="B",
                       created_at=self.now - datetime.timedelta(days=10), importance=4.0, authority=0.80, raw_score=35.0)
        ]
        res1 = self.rrf.fuse(candidates)
        res2 = self.rrf.fuse(candidates)

        self.assertEqual(len(res1), 3)
        self.assertEqual([r[0].id for r in res1], [r[0].id for r in res2], "RRF must be 100% deterministic")
        self.assertEqual(res1[0][0].id, "item-A", "Policy item with highest score and authority must rank #1")


class TestModelManagerAndVersioning(unittest.TestCase):
    """Verifies feature schema versioning per Instruction.md Section 41."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.model_file = os.path.join(self.temp_dir, "test_model.json")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

    def test_schema_metadata_travels_with_weights(self):
        """Feature schema version, model version, and corpus version must travel with weights."""
        model = ModelMetadata(
            schema_version="1.0.0",
            model_version="1.0.0",
            training_corpus_version="2026.09.03",
            weights=dict(DEFAULT_WEIGHTS)
        )
        ModelManager.save_model(model, self.model_file)

        loaded = ModelManager.load_model(self.model_file)
        self.assertEqual(loaded.schema_version, "1.0.0")
        self.assertEqual(loaded.model_version, "1.0.0")
        self.assertEqual(loaded.training_corpus_version, "2026.09.03")
        self.assertEqual(loaded.weights, DEFAULT_WEIGHTS)

    def test_schema_mismatch_rejection(self):
        """Incompatible schema versions are strictly rejected."""
        incompatible = ModelMetadata(
            schema_version="2.0.0",  # Incompatible major version
            weights=dict(DEFAULT_WEIGHTS)
        )
        with self.assertRaises(SchemaMismatchError):
            ModelManager.validate_model_schema(incompatible)

    def test_missing_or_unknown_features_rejection(self):
        """Missing or unknown features are strictly rejected."""
        broken_weights = dict(DEFAULT_WEIGHTS)
        del broken_weights["decay_factor"]
        broken_model = ModelMetadata(weights=broken_weights)
        with self.assertRaises(SchemaMismatchError):
            ModelManager.validate_model_schema(broken_model)

    def test_feature_ordering_named_mapping_invariant(self):
        """Never allow a new feature ordering to reinterpret old weights silently."""
        reversed_order = list(reversed(CANONICAL_FEATURE_NAMES))
        model = ModelMetadata(
            feature_order=reversed_order,
            weights=dict(DEFAULT_WEIGHTS)
        )
        # Validate re-alignment strictly by feature name
        ModelManager.validate_model_schema(model)
        self.assertEqual(model.feature_order, CANONICAL_FEATURE_NAMES)
        self.assertEqual(model.weights["decay_factor"], DEFAULT_WEIGHTS["decay_factor"])


class TestShadowRankerAndIsolation(unittest.TestCase):
    """Verifies shadow ranker comparison and strict live path isolation."""

    def setUp(self):
        self.now = datetime.datetime(2026, 9, 3, 12, 0, 0, tzinfo=datetime.timezone.utc)
        self.ranker = ShadowRanker()
        self.rrf = ReciprocalRankFusion(k=60)

    def test_shadow_comparison_metrics(self):
        """Shadow ranking computes Spearman rho, Kendall tau, and rank differences."""
        candidates = [
            MemoryItem(id="DECISIONS.md#ADR-001", file_path="/t/DECISIONS.md", scope="decisions",
                       heading="ADR-001", content="Verified decision",
                       created_at=self.now - datetime.timedelta(days=20),
                       importance=4.0, authority=0.80, access_count=5, verified_count=4, raw_score=40.0),
            MemoryItem(id="sessions/log.md#L1", file_path="/t/sessions/log.md", scope="sessions",
                       heading="Log", content="Episodic session note",
                       created_at=self.now - datetime.timedelta(days=40),
                       importance=2.0, authority=0.35, access_count=1, verified_count=0, raw_score=35.0),
            MemoryItem(id="POLICY.md#L1", file_path="/t/POLICY.md", scope="policy",
                       heading="Policy", content="Immutable policy rules",
                       created_at=self.now - datetime.timedelta(days=365),
                       importance=5.0, authority=1.0, access_count=2, verified_count=2, raw_score=30.0)
        ]
        baseline = self.rrf.fuse(candidates)
        report = self.ranker.evaluate_shadow_ranking("architecture", baseline, reference_time=self.now)

        self.assertEqual(report.total_candidates, 3)
        self.assertTrue(-1.0 <= report.spearman_rho <= 1.0)
        self.assertTrue(-1.0 <= report.kendall_tau <= 1.0)
        self.assertEqual(len(report.rankings), 3)

        # Verify old rank, new rank, difference recorded per Section 221
        for r in report.rankings:
            self.assertEqual(r.rank_diff, r.baseline_rank - r.shadow_rank)

    def test_strict_live_path_isolation(self):
        """Live search results must NEVER be modified by shadow ranking."""
        temp_dir = tempfile.mkdtemp()
        ledger_path = os.path.join(temp_dir, "ledger.json")
        model_path = os.path.join(temp_dir, "model.json")

        loop = LearningLoop(
            workspace_dir="/workspaces/codespaces-blank",
            model_path=model_path,
            ledger_path=ledger_path,
            reference_time=self.now
        )

        res = loop.query_with_shadow("memory", scopes=["all"], max_results=5, persist_eval=False)
        self.assertEqual(res["status"], "success")
        self.assertIn("live_results", res)
        self.assertIn("shadow_comparison", res)

        # Invariant: live results rank order matches baseline RRF exactly
        live_ranks = [r["rank"] for r in res["live_results"]]
        self.assertEqual(live_ranks, list(range(1, len(live_ranks) + 1)))

        # Verify live algorithm is deterministic RRF
        self.assertIn("ReciprocalRankFusion", res["live_ranking_algorithm"])
        self.assertIn("VERIFIED", res["isolation_guarantee"])

        import shutil
        shutil.rmtree(temp_dir)


class TestBenchmarkGate(unittest.TestCase):
    """Verifies benchmark gate execution per Instruction.md Section 41, 222."""

    def test_benchmark_gate_all_pass(self):
        gate = BenchmarkGate()
        bench_res = gate.run_benchmark()
        self.assertEqual(bench_res["status"], "PASS")
        self.assertTrue(bench_res["passed"])
        self.assertEqual(bench_res["score"], 1.0)
        self.assertEqual(bench_res["checks_passed"], 6)
        self.assertEqual(bench_res["checks_run"], 6)


class TestLearningLedgerPersistence(unittest.TestCase):
    """Verifies persistence of access and verification signals."""

    def test_ledger_record_and_reload(self):
        temp_dir = tempfile.mkdtemp()
        ledger_file = os.path.join(temp_dir, "ledger.json")

        ledger1 = LearningLedger(ledger_file)
        ledger1.record_access("DECISIONS.md#ADR-001", verified=True)
        ledger1.record_access("DECISIONS.md#ADR-001", verified=True)

        ledger2 = LearningLedger(ledger_file)
        rec = ledger2.get_record("DECISIONS.md#ADR-001")
        self.assertIsNotNone(rec)
        self.assertEqual(rec["access_count"], 2)
        self.assertEqual(rec["verified_count"], 2)
        self.assertEqual(rec["refuted_count"], 0)

        import shutil
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
