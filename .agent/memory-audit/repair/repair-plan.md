# Antigravity Memory OS Phase 2: Master Repair Plan
**Document ID:** `repair-plan.md`  
**Location:** [`.agent/memory-audit/repair/repair-plan.md`](file:///workspaces/codespaces-blank/.agent/memory-audit/repair/repair-plan.md)  
**Governing Directives:** `instruction.md` Section 71–74  
**Date:** 2026-09-04  

---

## 1. Prioritized Defect & Repair Register

### Priority 0 (P0) — Correctness, Security & Data-Integrity Blockers
- **P0-1 (DEF-001 / SEC-001)**: **PreToolUse Fail-Closed Security Fix** `[COMPLETED - 2026-09-04]`
  - *Location*: `scripts/hooks/pre_tool_use.py:74-77`
  - *Fix*: Replace `except Exception: return {"decision": "allow"}` with fail-closed `{"decision": "deny", "reason": "PreToolUse security gate exception (fail-closed)"}`. Added cache size > 0 and recent mtime validation. Verified with unit tests.
- **P0-2 (DEF-001 / SUB-001)**: **MemSearch CLI ONNX Configuration**
  - *Location*: `~/.memsearch/config.toml`
  - *Fix*: Ensure global MemSearch config sets `embedding.provider = "onnx"` and `embedding.model = "bge-m3"` so no OpenAI API keys are required.
- **P0-3 (DEF-002 / SUB-002)**: **MemSearchBackend Stdout Warning Strip & Parse**
  - *Location*: `scripts/memsearch_backend.py:165-182`
  - *Fix*: Strip non-JSON prefix (device warning banners) before `json.loads`. Log error if decode fails, set degraded status, do not silently swallow.
- **P0-4 (DEF-002 / SUB-003)**: **Fix Invalid `memsearch delete` Command**
  - *Location*: `scripts/memsearch_backend.py:144-156`
  - *Fix*: MemSearch CLI 0.4.19 does not have a `delete` subcommand; implement chunk cleanup via manifest update and SQLite/Milvus entity drop or index rebuild.

### Priority 1 (P1) — Major Missing Functionality & Broken Tests
- **P1-1 (DEF-003 / RET-001)**: **Implement True Hybrid RRF Search**
  - *Location*: `scripts/search_memory.py`
  - *Fix*: Call `MemSearchBackend.search()`, fuse dense semantic results with lexical BM25 results using Reciprocal Rank Fusion ($1 / (k + \text{rank})$), and add multi-signal reranking with freshness and source authority.
- **P1-2 (DEF-001 / ROUTE-001)**: **Fix Query Router Abbreviation Filter & Thresholds**
  - *Location*: `scripts/query_router.py:702, 710`
  - *Fix*: Change `len(term) > 3` to `len(term) >= 3` so terms like `adr` match. Increase candidate retrieval budget from 5 to 15. Fix `test_successful_resolution_adr` test failure.
- **P1-3 (DEF-004 / BENCH-001)**: **Rewire Benchmark Suite to Live Backend**
  - *Location*: `scripts/memory_benchmark.py`
  - *Fix*: Eliminate `BenchmarkRetriever` in-memory TF-IDF mock in A001–A030 acceptance criteria; test directly against `search_memory.py` and live `MemSearchBackend`.

### Priority 2 (P2) — Integration Wiring, Lifecycle & Quality Gaps
- **P2-1 (DEF-008 / HOOK-001)**: **Wire PostToolUse Hook to CandidateBus**
  - *Location*: `scripts/hooks/post_tool_use.py`
  - *Fix*: Wire tool errors, build failures, and file changes into `CandidateBus.record_event()` for automatic staging.
- **P2-2 (DEF-009 / RECON-001)**: **Wire MemoryReconciler to IndexQueue**
  - *Location*: `scripts/memory_reconciler.py`
  - *Fix*: Upon atomic Markdown commit, call `IndexQueueManager.enqueue(target_path, "UPDATE")`.
- **P2-3 (DEF-006 / INBOX-001)**: **Reconcile and Drain Candidate Inbox**
  - *Location*: `.agents/memory/inbox/candidates.jsonl`
  - *Fix*: Run candidate compilation and reconciliation to promote verified items and clear backlog.
- **P2-4 (SEC-005 / SEC-002)**: **Code-Fence Escape & Tool Interception** `[P2-4 Tool Interception COMPLETED - 2026-09-04]`
  - *Location*: `scripts/search_memory.py`, `scripts/hooks/pre_tool_use.py`, `.agents/hooks.json`
  - *Fix*: Intercepted `manage_task` (`Input`) and `notebook_edit` (`Content`) in `pre_tool_use.py` and `.agents/hooks.json`. Markdown fence breakout defense addressed.

### Priority 3 (P3) — Cleanup, Polish & Documentation Synchronization
- **P3-1 (MOCK-001)**: **Deprecate / Remove Mock Script**
  - *Location*: `scripts/verify_subagent_memory.py`
  - *Fix*: Remove or rewrite to perform real memory verification instead of comparing static strings.
- **P3-2 (DOC-001)**: **Synchronize AGENTS.md & hooks.json**
  - *Location*: `.agents/hooks.json` vs `AGENTS.md`
  - *Fix*: Ensure stop hook paths and definitions are consistent.

---

## 2. Squad Execution Waves (Stage 4)

- **Wave 2: Storage Substrate & Security (Squad 1 & 2)**:
  - Agent 4 (`security_gatekeeper`): P0-1, P2-4
  - Agent 5 (`memsearch_runtime_engineer`): P0-2
  - Agent 6 (`storage-backend-adapter-engineer`): P0-3, P0-4

- **Wave 3: Search, Reranking & Routing (Squad 3)**:
  - Agent 7 (`hybrid_search_specialist`): P1-1
  - Agent 8 (`evidence_reranker_engineer`): Reranking
  - Agent 9 (`context_compiler_engineer`): Context compiler
  - Agent 10 (`query_routing_specialist`): P1-2

- **Wave 4: Ingestion, Reconciliation & Queue (Squad 4)**:
  - Agent 11 (`candidate_bus_engineer`): P2-1
  - Agent 12 (`memory_compiler_gatekeeper`): Admission
  - Agent 13 (`memory_reconciler_specialist`): P2-2, P2-3
  - Agent 14 (`index_queue_engineer`): Queue drain

- **Wave 5: Feedback & Procedures (Squad 5)**:
  - Agent 15 (`feedback_telemetry_engineer`): Telemetry
  - Agent 16 (`learning_loop_specialist`): Shadow ranker
  - Agent 17 (`procedural_skill_engineer`): Quarantine procedures

- **Wave 6: Diagnostics, Matrix & Adversarial Red-Team (Squad 6)**:
  - Agent 18 (`memory_doctor_engineer`): Doctor
  - Agent 19 (`benchmark_test_architect`): P1-3
  - Agent 20 (`adversarial_red_team_reviewer`): 20 Attacks

- **Wave 7: Master Verification & Certification (Squad 6)**:
  - Agent 21 (`workstation_release_master`): Verification, Demo & Certification
