#!/usr/bin/env python3
"""
Unit and Integration Test Suite for Memory Compiler & Admission Gatekeeper.
Phase 10 & 11 - Candidate Normalization, Scoring, and Admission Gating.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add project root and scripts directory to sys.path
WORKSPACE_DIR = "/workspaces/codespaces-blank"
SCRIPTS_DIR = os.path.join(WORKSPACE_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from memory_compiler import (
    MemoryCompiler,
    MemoryCategory,
    AdmissionDecisionType,
    ProvenanceStatus,
    CompilerThresholds,
    CandidateScore,
    AdmissionDecision,
)


class TestMemoryCompiler(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.compiler = MemoryCompiler(
            workspace_dir=self.temp_dir.name,
            global_dir=os.path.join(self.temp_dir.name, "global")
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    # -------------------------------------------------------------
    # 1. 9 Memory Categories Normalization & Classification
    # -------------------------------------------------------------
    def test_normalize_all_nine_categories(self):
        expected_categories = [
            "EPHEMERAL", "SESSION", "PROJECT", "DOMAIN",
            "TOOL", "GLOBAL", "DECISION", "GOTCHA", "PROCEDURE"
        ]
        for cat in expected_categories:
            raw = {"content": f"Test memory content for {cat}", "category": cat.lower()}
            normalized = self.compiler.normalize(raw)
            self.assertEqual(normalized["category"], cat)
            self.assertIn(normalized["durability"], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0])

    def test_heuristic_classification(self):
        test_cases = [
            ("Routine progress update for step 2", "EPHEMERAL"),
            ("Current task: running compiler tests", "SESSION"),
            ("Architecture decision: We decided to use Ninja build", "DECISION"),
            ("Gotcha: Gradle daemon crashes in container due to memory", "GOTCHA"),
            ("Procedure: Steps to clean and rebuild native workspace", "PROCEDURE"),
            ("Run tshark with -r flag for offline PCAP reading", "TOOL"),
            ("User preference: always format with 4 spaces", "GLOBAL"),
            ("Standard project layout in repo workspace", "PROJECT"),
        ]
        for content, expected_cat in test_cases:
            cat = self.compiler.classify({"content": content})
            self.assertEqual(cat, expected_cat, f"Failed heuristic for: {content}")

    # -------------------------------------------------------------
    # 2. Candidate Scoring (Novelty + Durability + Evidence - Redundancy)
    # -------------------------------------------------------------
    def test_candidate_score_formula(self):
        candidate = {
            "novelty": 1.0,
            "durability": 3.0,
            "evidence": 1.0,
            "redundancy": 0.2
        }
        score_obj = self.compiler.calculate_score(candidate)
        # 1.0 + 3.0 + 1.0 - 0.2 = 4.8
        self.assertAlmostEqual(score_obj.score, 4.8, places=2)
        self.assertEqual(score_obj.novelty, 1.0)
        self.assertEqual(score_obj.durability, 3.0)
        self.assertEqual(score_obj.evidence, 1.0)
        self.assertEqual(score_obj.redundancy, 0.2)

    def test_candidate_score_with_high_redundancy(self):
        candidate = {
            "novelty": 0.2,
            "durability": 3.0,
            "evidence": 0.5,
            "redundancy": 0.9
        }
        score_obj = self.compiler.calculate_score(candidate)
        # 0.2 + 3.0 + 0.5 - 0.9 = 2.8
        self.assertAlmostEqual(score_obj.score, 2.8, places=2)

    # -------------------------------------------------------------
    # 3. Provenance Verification
    # -------------------------------------------------------------
    def test_verified_provenance_fresh_git_file(self):
        candidate = {
            "content": "Valid git commit fact",
            "provenance": {
                "source_type": "git_file",
                "path": "docs/architecture.md",
                "commit": "abc1234",
                "status": "VERIFIED",
                "verified": True
            }
        }
        normalized = self.compiler.normalize(candidate)
        is_verified, msg = self.compiler.verify_provenance(normalized)
        self.assertTrue(is_verified)
        self.assertIn("Verified provenance", msg)

    def test_unverified_provenance_marked_status(self):
        candidate = {
            "content": "Speculative assertion",
            "provenance": {
                "source_type": "web_search",
                "url": "https://example.com",
                "status": "UNVERIFIED"
            }
        }
        normalized = self.compiler.normalize(candidate)
        is_verified, msg = self.compiler.verify_provenance(normalized)
        self.assertFalse(is_verified)
        self.assertIn("unverified", msg)

    def test_missing_provenance(self):
        candidate = {"content": "Candidate with zero provenance"}
        normalized = self.compiler.normalize(candidate)
        is_verified, msg = self.compiler.verify_provenance(normalized)
        self.assertFalse(is_verified)

    # -------------------------------------------------------------
    # 4. Admission Gating: Durability >= 3 & Provenance Threshold
    # -------------------------------------------------------------
    def test_admission_gate_accept(self):
        candidate = {
            "category": "DECISION",
            "content": "Adopt ninja-build for native builds",
            "durability": 3.0,
            "novelty": 1.0,
            "evidence": 1.0,
            "redundancy": 0.0,
            "provenance": {
                "source_type": "git_file",
                "path": "docs/architecture.md",
                "status": "VERIFIED",
                "verified": True
            }
        }
        decision = self.compiler.decide_admission(candidate)
        self.assertEqual(decision.decision, AdmissionDecisionType.ACCEPT.value)
        self.assertTrue(decision.provenance_verified)
        self.assertGreaterEqual(decision.score, 3.0)
        self.assertIn("DECISIONS.md", decision.target_path)

    def test_admission_gate_hold_when_unverified_provenance(self):
        # Durability 5.0 (>= 3.0) but provenance is UNVERIFIED -> MUST HOLD
        candidate = {
            "category": "GLOBAL",
            "content": "Global developer guideline without proof",
            "durability": 5.0,
            "novelty": 1.0,
            "evidence": 0.2,
            "redundancy": 0.0,
            "provenance": {
                "source_type": "web",
                "status": "UNVERIFIED",
                "verified": False
            }
        }
        decision = self.compiler.decide_admission(candidate)
        self.assertEqual(decision.decision, AdmissionDecisionType.HOLD.value)
        self.assertFalse(decision.provenance_verified)
        self.assertIn("qualifies for canonical promotion, but provenance is unverified", decision.reason)

    def test_admission_gate_hold_session_scope(self):
        # Durability 2.0 (SESSION) -> MUST HOLD for session logs
        candidate = {
            "category": "SESSION",
            "content": "Currently debugging memory compiler tests",
            "durability": 2.0,
            "novelty": 0.8,
            "evidence": 0.9,
            "redundancy": 0.0,
            "provenance": {
                "source_type": "session_log",
                "session_id": "sess_101",
                "status": "FRESH",
                "verified": True
            }
        }
        decision = self.compiler.decide_admission(candidate)
        self.assertEqual(decision.decision, AdmissionDecisionType.HOLD.value)
        self.assertIn("Session-scoped context", decision.reason)

    def test_admission_gate_reject_ephemeral(self):
        # Durability 1.0 -> MUST REJECT (ephemeral noise)
        candidate = {
            "category": "EPHEMERAL",
            "content": "Routine terminal output: total 42 files listed",
            "durability": 1.0,
            "novelty": 0.1,
            "evidence": 0.1,
            "redundancy": 0.5
        }
        decision = self.compiler.decide_admission(candidate)
        self.assertEqual(decision.decision, AdmissionDecisionType.REJECT.value)
        self.assertIn("Ephemeral noise", decision.reason)

    def test_admission_gate_reject_high_redundancy(self):
        # Redundancy >= 0.75 -> MUST REJECT
        candidate = {
            "category": "PROJECT",
            "content": "Exact duplicated project fact",
            "durability": 3.0,
            "novelty": 0.1,
            "evidence": 0.9,
            "redundancy": 0.85,
            "provenance": {
                "source_type": "git_file",
                "path": "AGENTS.md",
                "status": "VERIFIED",
                "verified": True
            }
        }
        decision = self.compiler.decide_admission(candidate)
        self.assertEqual(decision.decision, AdmissionDecisionType.REJECT.value)
        self.assertIn("Excessive redundancy", decision.reason)

    def test_admission_gate_reject_secrets(self):
        # Construct secret dynamically to verify SecretScanner integration
        prefix = "sk-" + "proj-"
        fake_secret = prefix + "abc1234567890123456789012345678901234567890"
        candidate = {
            "category": "PROJECT",
            "content": f"Database credentials leaked: export API_KEY={fake_secret}",
            "durability": 3.0,
            "provenance": {
                "source_type": "git_file",
                "path": "test.txt",
                "status": "VERIFIED",
                "verified": True
            }
        }
        decision = self.compiler.decide_admission(candidate)
        self.assertEqual(decision.decision, AdmissionDecisionType.REJECT.value)
        self.assertIn("Security violation", decision.reason)

    # -------------------------------------------------------------
    # 5. Section 11 Methods
    # -------------------------------------------------------------
    def test_prepare_write_accepted_decision(self):
        candidate = {
            "category": "DECISION",
            "content": "Use SQLite for local test runs",
            "context": "Need fast local database without docker dependency",
            "rationale": "SQLite is built-in and zero-config",
            "consequences": "Tests run cleanly in CI"
        }
        decision = AdmissionDecision(
            decision="ACCEPT",
            candidate_id="cand_test_01",
            category="DECISION",
            score=5.0,
            score_breakdown={"score": 5.0, "durability": 3.0},
            provenance_verified=True,
            reason="Passed admission gate",
            target_scope="PROJECT",
            target_path="/workspaces/codespaces-blank/.agents/memory/DECISIONS.md"
        )
        write_payload = self.compiler.prepare_write(candidate, decision)
        self.assertTrue(write_payload["commit_ready"])
        self.assertEqual(write_payload["action"], "APPEND")
        self.assertIn("## [", write_payload["formatted_entry"])
        self.assertIn("- **Decision**: Use SQLite for local test runs", write_payload["formatted_entry"])

    def test_prepare_write_held_does_not_commit(self):
        decision = AdmissionDecision(
            decision="HOLD",
            candidate_id="cand_held_01",
            category="GLOBAL",
            score=4.0,
            score_breakdown={"score": 4.0, "durability": 5.0},
            provenance_verified=False,
            reason="Unverified provenance",
            target_scope="GLOBAL"
        )
        write_payload = self.compiler.prepare_write({}, decision)
        self.assertFalse(write_payload["commit_ready"])
        self.assertEqual(write_payload["action"], "NONE")

    def test_find_exact_duplicates(self):
        pool = [
            {"content": "Always pass --no-daemon to gradle wrapper", "file": "GOTCHAS.md"},
            {"content": "Use ninja for native compilation", "file": "ARCHITECTURE.md"}
        ]
        cand = {"content": "Always pass --no-daemon to gradle wrapper"}
        matches = self.compiler.find_exact_duplicates(cand, existing_memories=pool)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["file"], "GOTCHAS.md")

    def test_find_semantic_neighbors(self):
        pool = [
            {"content": "Gradle daemon crashes due to memory limits in container", "file": "GOTCHAS.md"},
            {"content": "Frontend bundler uses Vite with Tailwind CSS", "file": "ARCHITECTURE.md"}
        ]
        cand = {"content": "Gradle daemon execution leads to memory exhaustion"}
        neighbors = self.compiler.find_semantic_neighbors(cand, existing_memories=pool, threshold=0.25)
        self.assertGreaterEqual(len(neighbors), 1)
        self.assertEqual(neighbors[0]["file"], "GOTCHAS.md")

    def test_detect_conflict(self):
        pool = [
            {"content": "Always use PostgreSQL for database storage", "file": "ARCHITECTURE.md"}
        ]
        cand = {"content": "Do not use PostgreSQL for database storage, avoid it"}
        conflicts = self.compiler.detect_conflict(cand, existing_memories=pool)
        self.assertGreaterEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["conflict_type"], "POLARITY_CONTRADICTION")

    # -------------------------------------------------------------
    # 6. Inbox Compilation
    # -------------------------------------------------------------
    def test_compile_inbox_lifecycle(self):
        inbox_file = os.path.join(self.temp_dir.name, "test_candidates.jsonl")
        decisions_file = os.path.join(self.temp_dir.name, "test_decisions.jsonl")

        sample_records = [
            {
                "id": "c1",
                "category": "DECISION",
                "content": "Record 1 with verified provenance",
                "durability": 3.0,
                "provenance": {"source_type": "git_file", "path": "docs/arch.md", "status": "VERIFIED", "verified": True}
            },
            {
                "id": "c2",
                "category": "PROJECT",
                "content": "Record 2 with unverified provenance",
                "durability": 3.0,
                "provenance": {"status": "UNVERIFIED"}
            },
            {
                "id": "c3",
                "category": "EPHEMERAL",
                "content": "Record 3 trivial terminal print",
                "durability": 1.0
            }
        ]

        with open(inbox_file, "w", encoding="utf-8") as f:
            for r in sample_records:
                f.write(json.dumps(r) + "\n")

        summary = self.compiler.compile_inbox(inbox_path=inbox_file, output_path=decisions_file)
        self.assertEqual(summary["total_candidates"], 3)
        self.assertEqual(summary["counts"]["ACCEPT"], 1)
        self.assertEqual(summary["counts"]["HOLD"], 1)
        self.assertEqual(summary["counts"]["REJECT"], 1)
        self.assertTrue(os.path.exists(decisions_file))


if __name__ == "__main__":
    unittest.main()
