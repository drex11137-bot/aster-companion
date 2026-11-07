# COMPONENT MATRIX
## Antigravity Memory OS — Phase 2 Subsystem Conformance & Classification Matrix
**Document Identifier:** `COMPONENT_MATRIX.md`  
**Location:** [`.agent/memory-audit/audit/COMPONENT_MATRIX.md`](file:///workspaces/codespaces-blank/.agent/memory-audit/audit/COMPONENT_MATRIX.md)  
**Audit Phase:** Stage 2 — Forensic Architecture Audit  
**Auditor:** Agent 2 (Forensic Baseline Auditor)  
**Directives Governed:** [`instruction.md`](file:///workspaces/codespaces-blank/instruction.md) (Section 7 Component Inventory & Section 8 Classification Rules)  
**Audit Date:** 2026-09-04  

---

## 1. Classification Definitions (Instruction.md Section 8)

Every audited component is classified into exactly one of the following authoritative states:

| Classification | Strict Definition |
| :--- | :--- |
| **REAL** | The component has executable behavior and is demonstrably connected to the actual system path. |
| **PARTIAL** | Some required functionality works, but material behavior is missing or disconnected. |
| **STUB** | The interface exists but meaningful implementation is missing (`pass`, `return None`, `return {}`, `raise NotImplementedError`, or equivalent placeholders). |
| **MOCK_ONLY** | Works only against fake fixtures, mock services, fake data, or demo paths. |
| **DOCUMENTED_ONLY** | The architecture is described in markdown/documentation but not actually implemented in code. |
| **BROKEN** | Implementation exists but fails real execution or violates its contract under standard operation. |
| **MISSING** | No meaningful implementation or file exists on disk. |

> [!IMPORTANT]
> Per Section 8: Never count `STUB`, `MOCK_ONLY`, `DOCUMENTED_ONLY`, `BROKEN`, or `MISSING` as completed.

---

## 2. Master Component Classification Matrix

| # | Component | Subsystem / File | Expected Specification | Exists on Disk | Classification | Execution Status | Integration Status | Concrete Evidence / Defect Reference |
| :-: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | **Canonical Memory** | `.agents/memory/*.md`, `~/.gemini/antigravity-cli/memory/` | Section 11 | YES | **PARTIAL** | Operational | Partial | Core markdown files exist (`DECISIONS.md`, `GOTCHAS.md`, `ARCHITECTURE.md`, `INDEX.md`, `POLICY.md`, `USER.md`). However, global `domains/` files (`medical.md`, `database.md`, `frontend.md`) are 1-line stubs. `PROCEDURES.md` was admitted by the compiler but never created on disk. |
| 2 | **Current Working State** | [`.agents/memory/CURRENT.md`](file:///workspaces/codespaces-blank/.agents/memory/CURRENT.md) | Section 11 | YES | **PARTIAL** | Stale | Disconnected | File exists and follows schema (<30 lines). Stale timestamp (`2026-09-01T16:17:50Z`, Objective 99). Stop hooks do not update it; `session_manager.py` writes via un-atomic `open("w")`. |
| 3 | **Episodic Memory** | [`.agents/memory/sessions/`](file:///workspaces/codespaces-blank/.agents/memory/sessions/) | Section 11 | YES | **PARTIAL** | Incomplete | Disconnected | Contains 4 session logs from Sept 1–2. Zero logs recorded for Sept 3 or Sept 4 despite heavy activity. `stop_hook.py` fails to trigger session end logging. |
| 4 | **Candidate Bus** | [`scripts/candidate_bus.py`](file:///workspaces/codespaces-blank/scripts/candidate_bus.py) | Section 9, 90-93 | YES | **PARTIAL** | Verified | Disconnected | 872 lines. Idempotent hashing, secret screening, file locking, and staging in `candidates.jsonl` functional. Disconnected from hooks (`post_tool_use.py` does not call it). Accumulates 12 un-drained items (DEF-006). |
| 5 | **Memory Compiler** | [`scripts/memory_compiler.py`](file:///workspaces/codespaces-blank/scripts/memory_compiler.py) | Section 10, 11 | YES | **PARTIAL** | Verified | Disconnected | 1040 lines. Evaluates novelty, durability, evidence, redundancy, and outputs decisions (ACCEPT, HOLD, REJECT) to `admission_decisions.jsonl`. Does not mutate canonical files; bypassed by `memory_engine.py:promote_memory`. |
| 6 | **Semantic Deduplication** | [`scripts/memory_reconciler.py`](file:///workspaces/codespaces-blank/scripts/memory_reconciler.py) | Section 20 | YES | **PARTIAL** | Verified (Isolated) | Disconnected | SequenceMatcher ratio (>0.85) and topic overlap implemented in `memory_reconciler.py`. Bypassed in live CLI (`memory_engine.py` directly appends lines without dedup). |
| 7 | **Contradiction Engine** | [`scripts/detect_contradictions.py`](file:///workspaces/codespaces-blank/scripts/detect_contradictions.py), [`scripts/memory_reconciler.py`](file:///workspaces/codespaces-blank/scripts/memory_reconciler.py) | Section 19 | YES | **PARTIAL** | Operational | Partial | `detect_contradictions.py` only implements 3 rigid regexes (Python version, package manager, monolithic/microservices architecture). `memory_reconciler.py` has advanced negation pairs but is not called by runtime. |
| 8 | **Temporal Model** | [`scripts/memory_reconciler.py`](file:///workspaces/codespaces-blank/scripts/memory_reconciler.py), [`scripts/query_router.py`](file:///workspaces/codespaces-blank/scripts/query_router.py) | Section 18 | YES | **PARTIAL** | Operational | Partial | `CanonicalRecord` and `CandidateMemory` track `observed_at`, `recorded_at`, `valid_from`, `valid_until`, `supersedes`. Temporal query classification works, but bitemporal replay is unintegrated. |
| 9 | **Provenance Tracking** | [`scripts/candidate_bus.py`](file:///workspaces/codespaces-blank/scripts/candidate_bus.py), [`scripts/context_compiler.py`](file:///workspaces/codespaces-blank/scripts/context_compiler.py) | Section 21 | YES | **PARTIAL** | Verified | Partial | Full provenance dataclass exists in `candidate_bus.py` (`command`, `exit_code`, `source_type`, `output_hash`). Stripped or absent when memories are promoted via `memory_engine.py`. |
| 10 | **Evidence Gate** | [`scripts/memory_compiler.py`](file:///workspaces/codespaces-blank/scripts/memory_compiler.py) | Section 23 | YES | **PARTIAL** | Verified (Unit) | Disconnected | `CompilerThresholds` enforces `min_evidence_for_admission = 0.5` and verified provenance. Live CLI `memory_engine.py:promote_memory` bypasses this gate completely. |
| 11 | **Semantic Retrieval** | [`scripts/memsearch_backend.py`](file:///workspaces/codespaces-blank/scripts/memsearch_backend.py), Milvus Lite | Section 13, 25 | YES | **PARTIAL** | Verified (CLI) | **Disconnected** | Milvus Lite DB exists and `memsearch search "query" --provider onnx` succeeds via CLI. However, `search_memory.py` and `query_router.py` do NOT call vector search. Adapter `delete()` calls non-existent CLI command (DEF-001, DEF-002). |
| 12 | **Lexical Retrieval** | [`scripts/search_memory.py`](file:///workspaces/codespaces-blank/scripts/search_memory.py) | Section 26 | YES | **REAL** | Verified | Integrated | 448 lines. Robust multi-term keyword and regex scanning, heading boosts, line number extraction, and scope isolation. Used as sole engine by query router. |
| 13 | **RRF / Hybrid Retrieval Fusion** | [`scripts/learning_loop.py`](file:///workspaces/codespaces-blank/scripts/learning_loop.py) | Section 27 | YES | **PARTIAL** | Verified (Unit) | **Disconnected** | `ReciprocalRankFusion` class in `learning_loop.py` fuses lexical score, authority, importance, and freshness. It does NOT fuse dense vector search with sparse search (DEF-003). Uncalled by `search_memory.py`. |
| 14 | **Metadata Reranking** | [`scripts/query_router.py`](file:///workspaces/codespaces-blank/scripts/query_router.py), [`scripts/learning_loop.py`](file:///workspaces/codespaces-blank/scripts/learning_loop.py) | Section 28 | YES | **REAL** | Verified | Integrated | `calculate_match_confidence` reranks candidates based on intent alignment, active vs superseded status, canonical tier, and verification bonus. |
| 15 | **Scope Filtering** | [`scripts/search_memory.py`](file:///workspaces/codespaces-blank/scripts/search_memory.py) | Section 30 | YES | **REAL** | Verified | Integrated | `SCOPE_MAPPING` isolates project, global, decisions, gotchas, architecture, current, sessions, tools, domains, user, policy. Enforces workspace boundary containment. |
| 16 | **Progressive Recall** | [`scripts/context_compiler.py`](file:///workspaces/codespaces-blank/scripts/context_compiler.py) | Section 31 | YES | **REAL** | Verified | Integrated | Implements `DisclosureLevel` (L1 preview <200 chars, L2 full section, L3 deep provenance, AUTO budget packing). |
| 17 | **Context Compiler** | [`scripts/context_compiler.py`](file:///workspaces/codespaces-blank/scripts/context_compiler.py) | Section 32 | YES | **REAL** | Verified | Integrated | 1023 lines. Strict token budgeting, trust verdict assignment (CERTIFY, ADVISORY, WARN, BLOCK), and compact Markdown context packaging. |
| 18 | **Index Queue & Single-Writer Control** | [`scripts/memory_index_queue.py`](file:///workspaces/codespaces-blank/scripts/memory_index_queue.py) | Section 15, 33 | YES | **PARTIAL** | Verified (CLI) | Disconnected | 744 lines. Implements durable `index_queue.jsonl`, `index_writer.lease.lock`, update coalescing, and drain logic. Disconnected because writes do not enqueue items and no worker daemon drains it. |
| 19 | **Index Health Subsystem** | [`scripts/memory_index_queue.py`](file:///workspaces/codespaces-blank/scripts/memory_index_queue.py), [`scripts/memory_doctor.py`](file:///workspaces/codespaces-blank/scripts/memory_doctor.py) | Section 14 | YES | **REAL** | Verified | Integrated | Tracks `canonical_revision`, `indexed_revision`, `last_success`, `last_failure`, `failure_count`. Explicitly handles `HEALTHY`, `STALE`, `DEGRADED`, `REBUILDING`, `FAILED`, `MISSING`. |
| 20 | **Watcher Process** | Background Daemon | Section 34 | NO | **MISSING** | Non-existent | Disconnected | No background process or system daemon is running to watch markdown files and auto-enqueue updates. `memsearch watch` command exists in CLI but is not running. |
| 21 | **Feedback Ledger & Telemetry** | [`scripts/memory_feedback.py`](file:///workspaces/codespaces-blank/scripts/memory_feedback.py) | Section 33, 39 | YES | **REAL** | Verified | Integrated | 1043 lines. Logs to `retrieval_ledger.jsonl` with file locking. Accurately calculates MRR, NDCG@10, False Recall Rate, and emits `telemetry.json`. |
| 22 | **Memory Decay Subsystem** | [`scripts/learning_loop.py`](file:///workspaces/codespaces-blank/scripts/learning_loop.py) | Section 35 | YES | **REAL** | Verified | Integrated | Implements logarithmic and exponential decay curves with access reinforcement and governance fact immunity. |
| 23 | **Procedural Memory Engine** | [`scripts/procedural_engine.py`](file:///workspaces/codespaces-blank/scripts/procedural_engine.py) | Section 37, 38 | YES | **PARTIAL** | Verified (Isolated) | Disconnected | 991 lines. Distills procedures with step classification (`OBSERVED_COMMAND`, `VERIFIED_STEP`) and Invariant 16 isolation in `inbox/procedures/`. Not called during session termination. |
| 24 | **Crash Recovery & File Locking** | [`scripts/lock_manager.py`](file:///workspaces/codespaces-blank/scripts/lock_manager.py) | Section 42, 44 | YES | **PARTIAL** | Verified | Partial | `file_lock` with `fcntl.flock`, atomic writes via temporary file and rename, stale lock cleanup. Used in `memory_reconciler.py`, but bypassed in `session_manager.py`. |
| 25 | **Security Controls / Secret Scanner** | [`scripts/secret_scanner.py`](file:///workspaces/codespaces-blank/scripts/secret_scanner.py) | Section 39, 41 | YES | **PARTIAL** | Verified | Partial | 703 lines. Robust regex patterns, Shannon entropy checking, and placeholder whitelisting. Flawed by fail-open hook behavior and fallback `DummyScanner` classes. |
| 26 | **Benchmarks** | [`scripts/memory_benchmark.py`](file:///workspaces/codespaces-blank/scripts/memory_benchmark.py) | Section 72-79 | YES | **PARTIAL** | Verified | Partial | 1280 lines. Implements A001-A030 acceptance matrix and longitudinal stress testing. Flawed by using an in-memory TF-IDF mock instead of live MemSearch (DEF-004). |
| 27 | **Adversarial Tests** | `tests/test_memory_os_adversarial.py`, `test_adversarial_attacks.py` | Section 65 | YES | **REAL** | Verified | Integrated | Comprehensive suites testing path traversal, symlink escapes, secret injection, corrupted jsonl, and concurrency contention. |
| 28 | **Doctor / Health Command** | `tools/bin/agy-memory-doctor` -> [`scripts/memory_doctor.py`](file:///workspaces/codespaces-blank/scripts/memory_doctor.py) | Section 51, 105 | YES | **REAL** | Verified | Integrated | 1353 lines. Authoritative 6-dimension health diagnostic suite executable via symlinked CLI binary. Output verified cleanly. |
| 29 | **Audit & Reporting Subsystem** | [`scripts/audit_memory.py`](file:///workspaces/codespaces-blank/scripts/audit_memory.py) | Section 13 | YES | **REAL** | Verified | Integrated | 553 lines. Generates comprehensive audit reports across memory bounds, duplicate facts, stale dates, and policy non-conformance. |
| 30 | **Lifecycle Hooks Suite** | [`.agents/hooks.json`](file:///workspaces/codespaces-blank/.agents/hooks.json), [`scripts/hooks/`](file:///workspaces/codespaces-blank/scripts/hooks/) | Section 49, 50 | YES | **PARTIAL** | Operational | Partial | `pre_invocation.py` and `pre_tool_use.py` operate. However, `post_tool_use.py` and `stop_hook.py` are stubs (DEF-008, DEF-010). Global CLI hook configuration has `"enabled": false`. |
| 31 | **Query Intent Router** | [`scripts/query_router.py`](file:///workspaces/codespaces-blank/scripts/query_router.py) | Section 27, 30 | YES | **BROKEN** | **FAIL (1 test)** | Integrated | Implements intent classification, scope determination, and abstention. **Fails active unit test** `test_successful_resolution_adr` due to 3-letter abbreviation filtering bug on line 702. |
| 32 | **Semantic Backend Adapter** | [`scripts/memsearch_backend.py`](file:///workspaces/codespaces-blank/scripts/memsearch_backend.py) | Section 21 | YES | **BROKEN** | Partial | Partial | `delete()` invokes invalid CLI command (`memsearch delete`). Device discovery warning on stdout breaks `json.loads`, triggering silent fallback to keyword counts (DEF-002). |
| 33 | **Session Manager** | [`scripts/session_manager.py`](file:///workspaces/codespaces-blank/scripts/session_manager.py) | Section 11 | YES | **PARTIAL** | Verified | Partial | Generates session logs and updates `CURRENT.md`. Non-atomic writes on lines 448 and 474 violate crash-safety contract. |
| 34 | **Subagent Isolation Verifier** | [`scripts/verify_subagent_memory.py`](file:///workspaces/codespaces-blank/scripts/verify_subagent_memory.py) | Section 30 | YES | **MOCK_ONLY** | Fake Exit 0 | Disconnected | Contains static string equality check and hardcoded `print("PASS...")` calls without real assertions or execution isolation checks. |
| 35 | **Toolchain Version Synchronizer** | [`scripts/version_sync.py`](file:///workspaces/codespaces-blank/scripts/version_sync.py) | Section 4.2 | YES | **REAL** | Verified | Integrated | 384 lines. Probes live CLI tool versions (`agy`, `python3`, `node`, `git`) and synchronizes active specifications in `ENVIRONMENT.md`. |
| 36 | **Backup & Recovery Utility** | [`scripts/backup_memory.py`](file:///workspaces/codespaces-blank/scripts/backup_memory.py) | Section 44 | YES | **REAL** | Verified | Integrated | Implements tar.gz archiving, timestamped backup rotation, and full extraction restore. |

---

## 3. Subsystem Classification Summary Statistics

```text
Total Audited Components: 36

┌───────────────────┬───────┬────────────┐
│ Classification    │ Count │ Percentage │
├───────────────────┼───────┼────────────┤
│ REAL              │  13   │   36.1%    │
│ PARTIAL           │  18   │   50.0%    │
│ BROKEN            │   2   │    5.6%    │
│ MOCK_ONLY         │   1   │    2.8%    │
│ MISSING           │   1   │    2.8%    │
│ STUB              │   1   │    2.8%    │ (post_tool_use / stop_hook stubs grouped in hooks)
│ DOCUMENTED_ONLY   │   0   │    0.0%    │
└───────────────────┴───────┴────────────┘
```

### Critical Takeaways:
1. **Core Algorithms are NOT Documented-Only:** The previous build did not just write documentation; it implemented genuine, high-complexity algorithms (`secret_scanner.py`, `memory_compiler.py`, `memory_reconciler.py`, `learning_loop.py`, `context_compiler.py`, `memory_doctor.py`).
2. **The "Last Mile" Integration Severance:** 50% of components are classified as **PARTIAL** because they were implemented as isolated modules that are not invoked by the runtime hooks or primary query engine.
3. **Active Failures Must Be Repaired:** Two components are **BROKEN** (`query_router.py` due to abbreviation filtering causing pytest failure; `memsearch_backend.py` due to silent JSON parsing failure and non-existent CLI delete command).
4. **Zero Live Semantic Search:** Despite MemSearch and Milvus Lite existing on disk, the live query router and context compiler run 100% on lexical regex search.
