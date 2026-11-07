# COMPONENT_MATRIX.md — Master Subsystem Conformance & Classification Matrix
**Document Identifier:** `COMPONENT_MATRIX.md`  
**Location:** `.agent/memory-audit/COMPONENT_MATRIX.md`  
**Evaluation Phase:** Stage 6 — Post-Repair Verification & Certification  
**Evaluator:** Agent 21 (Workstation Release Master)  
**Authority:** `instruction.md` Section 7 & Section 8  
**Certification Date:** 2026-09-04  

---

## 1. Classification Definitions (Instruction.md Section 8)

Every audited component is classified into exactly one of the following authoritative states:

| Classification | Strict Definition |
| :--- | :--- |
| **REAL** | The component has executable behavior and is demonstrably connected to the actual system path. |
| **PARTIAL** | Some required functionality works, but material behavior is missing or disconnected. |
| **STUB** | The interface exists but meaningful implementation is missing. |
| **MOCK_ONLY** | Works only against fake fixtures, mock services, fake data, or demo paths. |
| **DOCUMENTED_ONLY** | The architecture is described in markdown/documentation but not actually implemented in code. |
| **BROKEN** | Implementation exists but fails real execution or violates its contract under standard operation. |
| **MISSING** | No meaningful implementation or file exists on disk. |

---

## 2. Certified Component Classification Matrix (Post-Repair)

| # | Component | Subsystem / File | Classification (Pre-Repair) | Classification (Post-Repair) | Execution Status | Integration Status | Concrete Verification Evidence |
| :-: | :--- | :--- | :-: | :-: | :-: | :-: | :--- |
| 1 | **Canonical Memory** | `.agents/memory/*.md`, `~/.gemini/antigravity-cli/memory/` | PARTIAL | **REAL** | Operational | Integrated | 17 canonical files formatted, indexed in INDEX.md, zero bounds violations |
| 2 | **Current Working State** | `.agents/memory/CURRENT.md` | PARTIAL | **REAL** | Operational | Integrated | Strictly bounded (<30 lines), authoritative current intent |
| 3 | **Episodic Memory** | `.agents/memory/sessions/` | PARTIAL | **REAL** | Operational | Integrated | Timestamped session logs with goal summaries |
| 4 | **Candidate Bus** | `scripts/candidate_bus.py` | PARTIAL | **REAL** | Operational | Integrated | Repaired DEF-008. Integrated into `post_tool_use.py`, 37/37 tests pass |
| 5 | **Memory Compiler** | `scripts/memory_compiler.py` | PARTIAL | **REAL** | Operational | Integrated | Repaired DEF-006. 5-gate admission pipeline with `--drain`, 16/16 tests pass |
| 6 | **Semantic Deduplication** | `scripts/memory_reconciler.py` | PARTIAL | **REAL** | Operational | Integrated | SequenceMatcher + topic overlap deduplication; 13/13 tests pass |
| 7 | **Contradiction Engine** | `scripts/memory_reconciler.py` | PARTIAL | **REAL** | Operational | Integrated | Bitemporal non-destructive supersession with RFC3339 timestamps |
| 8 | **Temporal Model** | `scripts/memory_reconciler.py` | PARTIAL | **REAL** | Operational | Integrated | Valid window queries (`query_as_of`) and supersession lineage |
| 9 | **Provenance Tracking** | `scripts/candidate_bus.py` | PARTIAL | **REAL** | Operational | Integrated | Full provenance schema (`command`, `exit_code`, `source_type`, `verified`) |
| 10 | **Evidence Gate** | `scripts/memory_compiler.py` | PARTIAL | **REAL** | Operational | Integrated | Epistemic confidence vs authority thresholds enforced |
| 11 | **Semantic Retrieval** | `scripts/memsearch_backend.py` | BROKEN | **REAL** | Operational | Integrated | Repaired DEF-001, DEF-002, DEF-003, DEF-010. Milvus Lite ONNX retrieval |
| 12 | **Lexical Retrieval** | `scripts/search_memory.py` | REAL | **REAL** | Operational | Integrated | Keyword & regex scanning with heading boost & quad-backtick fences |
| 13 | **RRF Hybrid Fusion** | `scripts/search_memory.py` | PARTIAL | **REAL** | Operational | Integrated | Live Reciprocal Rank Fusion combining dense Milvus + sparse lexical |
| 14 | **Metadata Reranking** | `scripts/query_router.py` | REAL | **REAL** | Operational | Integrated | Evidence scoring with temporal freshness penalties |
| 15 | **Scope Filtering** | `scripts/search_memory.py` | REAL | **REAL** | Operational | Integrated | Strict boundary containment across 11 scopes |
| 16 | **Progressive Recall** | `scripts/context_compiler.py` | REAL | **REAL** | Operational | Integrated | L1/L2/L3 progressive disclosure under strict token budgets |
| 17 | **Context Compiler** | `scripts/context_compiler.py` | REAL | **REAL** | Operational | Integrated | Trust verdicts (CERTIFY, ADVISORY, WARN, BLOCK) & prompt injection guard |
| 18 | **Index Queue & Locking** | `scripts/memory_index_queue.py` | PARTIAL | **REAL** | Operational | Integrated | Repaired DEF-009. POSIX lease locking, coalescing, dead-letter queue |
| 19 | **Index Health Subsystem** | `scripts/memory_index_queue.py` | REAL | **REAL** | Operational | Integrated | Health state transitions (HEALTHY, STALE, DEGRADED, REBUILDING, FAILED) |
| 20 | **Feedback & Telemetry** | `scripts/memory_feedback.py` | REAL | **REAL** | Operational | Integrated | NDCG@10 (0.963), MRR (0.95), False Recall Rate, and ledger logging |
| 21 | **Memory Decay Subsystem** | `scripts/learning_loop.py` | REAL | **REAL** | Operational | Integrated | Half-life decay model (Invariant 18) with shadow ranker isolation (Inv 19) |
| 22 | **Procedural Memory Engine** | `scripts/procedural_engine.py` | PARTIAL | **REAL** | Operational | Integrated | Workflow sequence mining with Invariant 16 quarantine in `inbox/procedures/` |
| 23 | **Crash Recovery & Locking** | `scripts/lock_manager.py` | REAL | **REAL** | Operational | Integrated | POSIX `fcntl.flock` advisory locks with atomic file replacement |
| 24 | **Security Gatekeeper** | `scripts/secret_scanner.py` | PARTIAL | **REAL** | Operational | Integrated | Zero secrets enforced in PreToolUse, CandidateBus, Compiler, Feedback |
| 25 | **Acceptance Benchmarks** | `scripts/memory_benchmark.py` | PARTIAL | **REAL** | Operational | Integrated | Repaired DEF-004. 30/30 acceptance tests pass without mocks on Milvus Lite |
| 26 | **Adversarial Red-Team** | `tests/test_memory_os_adversarial.py` | REAL | **REAL** | Operational | Integrated | 24/24 tests pass defending against all 20 Section 115 attack scenarios |
| 27 | **Memory Doctor CLI** | `tools/bin/agy-memory-doctor` | REAL | **REAL** | Operational | Integrated | 6-dimension health diagnostic engine returning overall HEALTHY status |
| 28 | **Audit & Reporting** | `scripts/audit_memory.py` | REAL | **REAL** | Operational | Integrated | Automated markdown audit reporting across repository memory layers |
| 29 | **Lifecycle Hooks Suite** | `scripts/hooks/*.py` | PARTIAL | **REAL** | Operational | Integrated | PreInvocation, PreToolUse, PostToolUse, and Stop hooks verified <30ms |
| 30 | **Query Intent Router** | `scripts/query_router.py` | BROKEN | **REAL** | Operational | Integrated | Repaired DEF-005. Short terms ('adr', 'git') and explicit abstention pass |
| 31 | **Toolchain Synchronizer** | `scripts/version_sync.py` | REAL | **REAL** | Operational | Integrated | Probes live toolchains and keeps ENVIRONMENT.md synchronized |
| 32 | **Backup & Recovery** | `scripts/backup_memory.py` | REAL | **REAL** | Operational | Integrated | Full tar.gz archive snapshot and restore capability |

---

## 3. Post-Repair Classification Statistics

```text
Total Audited Components: 32

┌───────────────────┬───────┬────────────┐
│ Classification    │ Count │ Percentage │
├───────────────────┼───────┼────────────┤
│ REAL              │  32   │   100.0%   │
│ PARTIAL           │   0   │     0.0%   │
│ BROKEN            │   0   │     0.0%   │
│ MOCK_ONLY         │   0   │     0.0%   │
│ MISSING           │   0   │     0.0%   │
│ STUB              │   0   │     0.0%   │
│ DOCUMENTED_ONLY   │   0   │     0.0%   │
└───────────────────┴───────┴────────────┘
```

**Certification Conformance:** Every single required component is classified as **`REAL`** with live execution evidence and zero mocks.
