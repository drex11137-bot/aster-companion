#!/usr/bin/env python3
"""
Comprehensive test suite for MemoryReconciler.
Tests reconciliation, conflict resolution, bitemporal semantics, supersession,
transaction logging, and full rollback per Instruction.md Sections 12, 14, 15, and 84.
"""

import os
import sys
import json
import shutil
import tempfile
import pytest
from datetime import date, datetime, timezone

# Add scripts directory to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from memory_reconciler import (
    MemoryReconciler,
    CandidateMemory,
    CanonicalRecord,
    ReconciliationAction,
    ConflictClassification,
    ReconciliationResult,
)


@pytest.fixture
def temp_memory_env(tmp_path):
    """Sets up an isolated temporary memory environment mirroring .agents/memory/."""
    mem_dir = tmp_path / ".agents" / "memory"
    mem_dir.mkdir(parents=True)
    decisions_dir = tmp_path / ".agents" / "memory-upgrade" / "decisions"
    decisions_dir.mkdir(parents=True)
    log_file = decisions_dir / "reconciliation_log.jsonl"

    # Seed with initial canonical records
    decisions_file = mem_dir / "DECISIONS.md"
    decisions_file.write_text("""# Project Architectural Decisions
Last Updated: 2026-09-01

## 2026-09-01 — ADR-001: 5-Tier Memory Architecture
**Type:** DECISION **Scope:** PROJECT **Confidence:** VERIFIED **Source:** docs/instruction.md **Status:** ACTIVE
### What
Decouple into Instructions, Durable Knowledge, Project Knowledge, Episodic Sessions, and Working State.
### Why
Needed a scalable memory system that prevents instruction bloat, cross-project contamination, and secret leakage.
### Evidence
Keeps prompt context minimal while preserving critical learnings.
### Notes
N/A

## 2026-09-01 — ADR-002: Dual Skill Entrypoints
**Type:** DECISION **Scope:** PROJECT **Confidence:** VERIFIED **Source:** docs/instruction.md **Status:** ACTIVE
### What
Create modular skill directories with YAML frontmatter in `.agents/skills/` and maintain flat definitions in `~/.gemini/antigravity-cli/skills/`.
### Why
Support both native Antigravity skill directories and flat markdown skill files.
### Evidence
N/A
### Notes
Canonical format.
""", encoding="utf-8")

    gotchas_file = mem_dir / "GOTCHAS.md"
    gotchas_file.write_text("""# Project Gotchas & Quirks
Last Updated: 2026-09-01

## 2026-09-01 — Secret Scanning Mechanism
**Type:** GOTCHA **Scope:** PROJECT **Confidence:** VERIFIED **Source:** secret_scanner.py **Status:** ACTIVE
### What
Any text containing credential patterns is rejected at write time by secret_scanner.py.
### Why
Prevent secrets from leaking into durable memory.
### Evidence
Unit tests pass.
### Notes
N/A
""", encoding="utf-8")

    arch_file = mem_dir / "ARCHITECTURE.md"
    arch_file.write_text("""# Project System Architecture
Last Updated: 2026-09-01

## 2026-09-01 — Database Infrastructure: Local Development
**Type:** PROJECT **Scope:** PROJECT **Confidence:** VERIFIED **Source:** config **Status:** ACTIVE
### What
SQLite is used for local development environments.
### Why
Lightweight and file-based with zero configuration overhead.
### Evidence
Verified with pytest fixtures.
""", encoding="utf-8")

    reconciler = MemoryReconciler(
        memory_dir=str(mem_dir),
        log_file=str(log_file),
        workspace_dir=str(tmp_path),
    )
    return reconciler, str(mem_dir), str(log_file)


class TestMemoryReconciler:
    """Tests core MemoryReconciler functionalities."""

    def test_canonical_records_scanning(self, temp_memory_env):
        reconciler, mem_dir, _ = temp_memory_env
        records = reconciler.scan_canonical_records()
        assert len(records) == 4
        ids = [r.id for r in records]
        assert "ADR-001" in ids
        assert "ADR-002" in ids
        for r in records:
            assert r.is_active() is True
            assert r.status == "ACTIVE"

    def test_duplicate_detection_noop(self, temp_memory_env):
        """Verify duplicate facts result in NOOP without mutating storage."""
        reconciler, mem_dir, log_file = temp_memory_env
        candidate = CandidateMemory(
            id="cand-dup-01",
            type="DECISION",
            title="ADR-001: 5-Tier Memory Architecture",
            content="Decouple into Instructions, Durable Knowledge, Project Knowledge, Episodic Sessions, and Working State.",
            durability=3,
        )
        result = reconciler.reconcile_candidate(candidate)
        assert result.action == ReconciliationAction.NOOP
        assert result.classification == ConflictClassification.DUPLICATE
        assert result.success is True

        # Ensure no mutations occurred in file
        decisions_content = open(os.path.join(mem_dir, "DECISIONS.md")).read()
        assert "cand-dup-01" not in decisions_content

    def test_complement_detection_scope_difference(self, temp_memory_env):
        """
        Verify complementary facts with scope/environment difference (Instruction.md Section 14)
        are both preserved as ACTIVE without superseding.
        """
        reconciler, mem_dir, log_file = temp_memory_env
        # Existing in ARCHITECTURE.md is: "SQLite is used for local development environments."
        # Candidate is: "PostgreSQL is used in production environments."
        candidate = CandidateMemory(
            id="cand-comp-01",
            type="PROJECT",
            title="Database Infrastructure: Production",
            content="PostgreSQL is used in production environments for clustering and high availability.",
            context="production",
            evidence="Kubernetes statefulset manifests",
            durability=3,
        )
        result = reconciler.reconcile_candidate(candidate)
        assert result.action == ReconciliationAction.ADD
        assert result.classification == ConflictClassification.COMPLEMENT
        assert result.success is True

        # Verify ARCHITECTURE.md now contains BOTH records active
        records = reconciler.scan_canonical_records(os.path.join(mem_dir, "ARCHITECTURE.md"))
        active_records = [r for r in records if r.is_active()]
        assert len(active_records) == 2
        titles = [r.title for r in active_records]
        assert any("Local Development" in t for t in titles)
        assert any("Production" in t for t in titles)

    def test_refinement_detection_and_enrichment(self, temp_memory_env):
        """Verify refinement enriches existing record while preserving lineage."""
        reconciler, mem_dir, log_file = temp_memory_env
        candidate = CandidateMemory(
            id="cand-ref-01",
            type="GOTCHA",
            title="Secret Scanning Mechanism",
            content="Any text containing credential patterns is rejected at write time by secret_scanner.py, and pre-commit hooks validate entropy thresholds above 4.5.",
            evidence="Verified with test_secret_scanner.py",
            durability=3,
        )
        result = reconciler.reconcile_candidate(candidate)
        assert result.action == ReconciliationAction.UPDATE
        assert result.classification == ConflictClassification.REFINEMENT
        assert result.success is True

        gotchas_content = open(os.path.join(mem_dir, "GOTCHAS.md")).read()
        assert "Refinement" in gotchas_content
        assert "pre-commit hooks validate entropy" in gotchas_content

    def test_true_contradiction_and_supersession(self, temp_memory_env):
        """
        Verify true contradiction marks superseded record with [SUPERSEDED on YYYY-MM-DD by id:XYZ],
        preserves history, records bitemporal fields, and appends new active record.
        """
        reconciler, mem_dir, log_file = temp_memory_env
        today_str = date.today().isoformat()

        # Overturn ADR-001 with ADR-003
        candidate = CandidateMemory(
            id="cand-adr-003",
            type="DECISION",
            title="ADR-003: 6-Tier Memory Architecture with Transaction Logging",
            content="Replace 5-Tier Memory Architecture with 6-Tier Architecture incorporating an explicit bitemporal reconciliation engine.",
            supersedes=["ADR-001"],
            evidence="Instruction.md Sections 12-15 benchmark tests",
            metadata={"why": "Enables robust time-travel queries and zero-loss audit trails."},
            durability=3,
        )
        result = reconciler.reconcile_candidate(candidate)
        assert result.action == ReconciliationAction.SUPERSEDE
        assert result.classification == ConflictClassification.CONTRADICTION
        assert "ADR-001" in result.superseded_records
        assert result.success is True

        # Inspect DECISIONS.md file content
        decisions_content = open(os.path.join(mem_dir, "DECISIONS.md")).read()

        # 1. Verify exact superseded marker: [SUPERSEDED on YYYY-MM-DD by id:XYZ]
        expected_tag = f"[SUPERSEDED on {today_str} by id:cand-adr-003]"
        assert expected_tag in decisions_content

        # 2. Verify status line contains SUPERSEDED and the tag
        assert f"**Status:** SUPERSEDED {expected_tag}" in decisions_content

        # 3. Verify historical text of ADR-001 was NOT destroyed
        assert "Decouple into Instructions, Durable Knowledge" in decisions_content
        assert "Needed a scalable memory system that prevents instruction bloat" in decisions_content

        # 4. Verify new record appended and ACTIVE
        assert "ADR-003: 6-Tier Memory Architecture" in decisions_content
        assert "cand-adr-003" in decisions_content

        # 5. Verify records parsed by scanner
        records = reconciler.scan_canonical_records(os.path.join(mem_dir, "DECISIONS.md"))
        adr1 = next(r for r in records if r.id == "ADR-001")
        adr3 = next(r for r in records if "cand-adr-003" in r.id or "adr-003" in r.id)

        assert adr1.status == "SUPERSEDED"
        assert adr1.is_active() is False
        assert adr1.superseded_by == "cand-adr-003"
        assert adr1.valid_until == today_str

        assert adr3.status == "ACTIVE"
        assert adr3.is_active() is True
        assert "ADR-001" in adr3.supersedes

    def test_version_contradiction_supersession(self, temp_memory_env):
        """Verify version update on tools triggers automatic supersession."""
        reconciler, mem_dir, log_file = temp_memory_env
        today_str = date.today().isoformat()

        # Add initial version fact to ARCHITECTURE.md
        initial_cand = CandidateMemory(
            id="cand-ver-old",
            type="PROJECT",
            title="Antigravity CLI Runtime",
            content="Antigravity CLI version 1.1.23 is the required runtime environment.",
            durability=3,
        )
        r1 = reconciler.reconcile_candidate(initial_cand)
        assert r1.action == ReconciliationAction.ADD

        # Now submit updated version fact
        update_cand = CandidateMemory(
            id="cand-ver-new",
            type="PROJECT",
            title="Antigravity CLI Runtime",
            content="Antigravity CLI version 1.1.25 is the required runtime environment.",
            evidence="Live CLI check agy --version",
            durability=3,
        )
        r2 = reconciler.reconcile_candidate(update_cand)
        assert r2.action == ReconciliationAction.SUPERSEDE
        assert r2.classification == ConflictClassification.CONTRADICTION

        arch_content = open(os.path.join(mem_dir, "ARCHITECTURE.md")).read()
        assert f"[SUPERSEDED on {today_str} by id:cand-ver-new]" in arch_content
        assert "Antigravity CLI version 1.1.23" in arch_content
        assert "Antigravity CLI version 1.1.25" in arch_content

    def test_transaction_logging_and_atomic_rollback(self, temp_memory_env):
        """Verify transaction log records full snapshots and rollback restores exact state."""
        reconciler, mem_dir, log_file = temp_memory_env
        original_content = open(os.path.join(mem_dir, "DECISIONS.md")).read()

        # Perform superseding mutation
        candidate = CandidateMemory(
            id="cand-rb-test",
            type="DECISION",
            title="ADR-001: 5-Tier Memory Architecture",
            content="Overturned completely: Single monolithic memory file.",
            supersedes=["ADR-001"],
            durability=3,
        )
        res = reconciler.reconcile_candidate(candidate)
        assert res.action == ReconciliationAction.SUPERSEDE
        tx_id = res.transaction_id
        assert tx_id is not None

        # Verify transaction logged
        history = reconciler.get_transaction_history()
        assert len(history) >= 1
        last_tx = history[-1]
        assert last_tx["transaction_id"] == tx_id
        assert last_tx["action"] == "SUPERSEDE"
        assert last_tx["reverted"] is False

        # File was modified
        mutated_content = open(os.path.join(mem_dir, "DECISIONS.md")).read()
        assert "Single monolithic memory file" in mutated_content

        # Rollback transaction
        success = reconciler.rollback(tx_id)
        assert success is True

        # Verify exact pre-transaction content restored
        restored_content = open(os.path.join(mem_dir, "DECISIONS.md")).read()
        assert restored_content == original_content

        # Verify rollback recorded in history
        updated_history = reconciler.get_transaction_history()
        assert updated_history[0]["reverted"] is True
        assert updated_history[-1]["action"] == "ROLLBACK"
        assert updated_history[-1]["target_transaction_id"] == tx_id

    def test_secret_scanner_rejection(self, temp_memory_env):
        """Verify secret tokens in candidate memory are rejected immediately."""
        reconciler, mem_dir, log_file = temp_memory_env
        # Dynamically construct synthetic credential to test scanner
        prefix = "g" + "hp_"
        secret_token = prefix + ("A" * 36)
        candidate = CandidateMemory(
            id="cand-secret-01",
            type="PROJECT",
            title="Deploy Credentials",
            content=f"Use access token {secret_token} for automated sync.",
            durability=3,
        )
        result = reconciler.reconcile_candidate(candidate)
        assert result.action == ReconciliationAction.REJECT
        assert result.classification == ConflictClassification.SECURITY_VIOLATION
        assert result.success is False

    def test_ephemeral_durability_discard(self, temp_memory_env):
        """Verify candidates with durability <= 1 are discarded as ephemeral."""
        reconciler, mem_dir, log_file = temp_memory_env
        candidate = CandidateMemory(
            id="cand-ephemeral",
            type="EPHEMERAL",
            title="Transient test debug calculation",
            content="Calculation value was 42 at step 3.",
            durability=1,
        )
        result = reconciler.reconcile_candidate(candidate)
        assert result.action == ReconciliationAction.REJECT
        assert result.classification == ConflictClassification.EPHEMERAL_DISCARD

    def test_bitemporal_time_travel_query(self, temp_memory_env):
        """Verify bitemporal query retrieves historically active facts based on valid window."""
        reconciler, mem_dir, log_file = temp_memory_env

        # Supersede ADR-001 with cand-adr-003 today
        candidate = CandidateMemory(
            id="cand-adr-003",
            type="DECISION",
            title="ADR-003: 6-Tier Architecture",
            content="6-Tier Architecture description.",
            supersedes=["ADR-001"],
            valid_from="2026-09-03",
            durability=3,
        )
        reconciler.reconcile_candidate(candidate)

        # Query as of 2026-09-01 (before supersession): ADR-001 should be valid
        records_past = reconciler.query_as_of(valid_at="2026-09-01", target_file=os.path.join(mem_dir, "DECISIONS.md"))
        past_ids = [r.id for r in records_past]
        assert "ADR-001" in past_ids

        # Query as of 2026-09-04 (after supersession): ADR-003 should be valid, ADR-001 not in valid set
        records_future = reconciler.query_as_of(valid_at="2026-09-04", target_file=os.path.join(mem_dir, "DECISIONS.md"))
        future_ids = [r.id for r in records_future]
        assert "ADR-001" not in future_ids
        assert any("adr-003" in i.lower() for i in future_ids)

    def test_index_queue_notification_on_mutation(self, temp_memory_env):
        """
        DEF-009: Verify IndexQueueManager.enqueue(target_path, operation=op)
        is called whenever canonical markdown files are modified (_apply_add, _apply_supersede, _apply_update).
        """
        reconciler, mem_dir, log_file = temp_memory_env
        enqueued_calls = []

        class MockQueueManager:
            def enqueue(self, source_path=None, event_type="upsert", operation=None, target_path=None, **kwargs):
                target = source_path or target_path
                op = operation or event_type
                enqueued_calls.append((target, op))
                return {"status": "pending", "source_path": target, "operation": op}

        mock_mgr = MockQueueManager()
        reconciler.index_queue_manager = mock_mgr

        # 1. Test _apply_add / reconcile new fact
        new_cand = CandidateMemory(
            id="cand-new-fact-01",
            type="DECISION",
            title="ADR-004: New Architecture Policy",
            content="Use modern schema validation.",
            durability=3,
        )
        res_add = reconciler.reconcile_candidate(new_cand)
        assert res_add.action == ReconciliationAction.ADD
        assert len(enqueued_calls) == 1
        assert enqueued_calls[-1][0] == os.path.join(mem_dir, "DECISIONS.md")
        assert enqueued_calls[-1][1] == "add"

        # 2. Test _apply_update / refinement
        ref_cand = CandidateMemory(
            id="cand-refine-02",
            type="DECISION",
            title="ADR-004: New Architecture Policy",
            content="Use modern schema validation with strict Pydantic models.",
            durability=3,
        )
        res_update = reconciler.reconcile_candidate(ref_cand)
        assert res_update.action == ReconciliationAction.UPDATE
        assert len(enqueued_calls) == 2
        assert enqueued_calls[-1][0] == os.path.join(mem_dir, "DECISIONS.md")
        assert enqueued_calls[-1][1] == "update"

        # 3. Test _apply_supersede / contradiction
        sup_cand = CandidateMemory(
            id="cand-supersede-03",
            type="DECISION",
            title="ADR-004: New Architecture Policy",
            content="Replace schema validation: Discontinue Pydantic in favor of Rust Serde bindings.",
            supersedes=[new_cand.id],
            durability=3,
        )
        res_sup = reconciler.reconcile_candidate(sup_cand)
        assert res_sup.action == ReconciliationAction.SUPERSEDE
        assert len(enqueued_calls) == 3
        assert enqueued_calls[-1][0] == os.path.join(mem_dir, "DECISIONS.md")
        assert enqueued_calls[-1][1] == "supersede"

    def test_drain_pending_accepted_candidates(self, temp_memory_env):
        """
        DEF-006: Verify drain_candidates processes pending accepted items from candidates.jsonl
        into canonical files (DECISIONS.md, GOTCHAS.md), marks them PROMOTED, and triggers enqueue.
        """
        reconciler, mem_dir, log_file = temp_memory_env
        inbox_dir = os.path.join(mem_dir, "inbox")
        os.makedirs(inbox_dir, exist_ok=True)
        inbox_file = os.path.join(inbox_dir, "candidates.jsonl")

        # Seed candidates into inbox
        candidates_data = [
            {
                "id": "cand_dec_drain_01",
                "category": "DECISION",
                "content": "Adopt ninja-build and CMake for all native C/C++ builds to enforce fast parallel incremental compilation.",
                "durability": 3.0,
                "novelty": 1.0,
                "evidence": 1.0,
                "redundancy": 0.0,
                "provenance": {"source_type": "git_file", "path": "docs/architecture.md", "status": "VERIFIED", "verified": True},
                "status": "STAGED",
            },
            {
                "id": "cand_gotcha_drain_02",
                "category": "GOTCHA",
                "content": "Running Gradle daemon inside Codespaces leads to OOM memory exhaustion; always pass --no-daemon flag.",
                "durability": 3.0,
                "novelty": 1.0,
                "evidence": 1.0,
                "redundancy": 0.0,
                "provenance": {"source_type": "tool_execution", "command": "./gradlew assembleDebug --no-daemon", "status": "FRESH", "verified": True},
                "status": "STAGED",
            },
            {
                "id": "cand_noise_drain_03",
                "category": "EPHEMERAL",
                "content": "Routine terminal output: total 42 files listed in /tmp",
                "durability": 1.0,
                "provenance": {"source_type": "terminal", "status": "FRESH", "verified": True},
                "status": "STAGED",
            }
        ]

        with open(inbox_file, "w", encoding="utf-8") as f:
            for item in candidates_data:
                f.write(json.dumps(item) + "\n")

        # Execute candidate drain
        drain_result = reconciler.drain_candidates(inbox_file=inbox_file)
        assert drain_result["total_candidates"] == 3
        assert drain_result["promoted_count"] == 2
        assert drain_result["rejected_count"] == 1

        # Verify DECISIONS.md contains new decision entry
        decisions_content = open(os.path.join(mem_dir, "DECISIONS.md")).read()
        assert "cand_dec_drain_01" in decisions_content
        assert "ninja-build and CMake" in decisions_content

        # Verify GOTCHAS.md received the new gotcha entry
        gotchas_content = open(os.path.join(mem_dir, "GOTCHAS.md")).read()
        assert "cand_gotcha_drain_02" in gotchas_content
        assert "Running Gradle daemon" in gotchas_content

        # Verify candidates.jsonl statuses updated
        updated_lines = open(inbox_file).readlines()
        records = [json.loads(line) for line in updated_lines]
        statuses = {r["id"]: r["status"] for r in records}
        assert statuses["cand_dec_drain_01"] == "PROMOTED"
        assert statuses["cand_gotcha_drain_02"] == "PROMOTED"
        assert statuses["cand_noise_drain_03"] == "REJECTED"

    def test_bitemporal_rfc3339_supersession(self, temp_memory_env):
        """
        Verify bitemporal non-destructive supersession records exact RFC3339 timestamps
        and supersedes pointer while keeping historical content intact.
        """
        reconciler, mem_dir, log_file = temp_memory_env
        decisions_file = os.path.join(mem_dir, "DECISIONS.md")

        candidate = CandidateMemory(
            id="cand-bitemp-sup-01",
            type="DECISION",
            title="ADR-002: Dual Skill Entrypoints",
            content="Supersede dual entrypoints with unified declarative skill registry.",
            supersedes=["ADR-002"],
            durability=3,
        )

        res = reconciler.reconcile_candidate(candidate)
        assert res.action == ReconciliationAction.SUPERSEDE

        content = open(decisions_file).read()
        # Verify non-destructive supersession marker
        assert "[SUPERSEDED on " in content
        assert f"by id:{candidate.id}]" in content

        # Verify RFC3339 timestamps in bitemporal comment
        assert "superseded_at=" in content
        assert "T" in content
        assert "Z" in content

        # Verify old record text still intact
        assert "Create modular skill directories with YAML frontmatter" in content

        # Verify record parser extracts superseded_at
        records = reconciler.scan_canonical_records(decisions_file)
        adr2 = next(r for r in records if r.id == "ADR-002")
        assert adr2.status == "SUPERSEDED"
        assert adr2.superseded_by == "cand-bitemp-sup-01"
        assert adr2.superseded_at is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
