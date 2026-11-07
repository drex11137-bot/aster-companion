# FORENSIC AUDIT REPORT
## Antigravity Memory OS — Phase 2 Ground Truth Forensic Audit
**Document Identifier:** `FORENSIC_AUDIT.md`  
**Location:** [`.agent/memory-audit/audit/FORENSIC_AUDIT.md`](file:///workspaces/codespaces-blank/.agent/memory-audit/audit/FORENSIC_AUDIT.md)  
**Audit Phase:** Stage 2 — Forensic Architecture Audit  
**Auditor:** Agent 2 (Forensic Baseline Auditor)  
**Directives Governed:** [`instruction.md`](file:///workspaces/codespaces-blank/instruction.md) (Sections 0, 1, 2, 7, 8, 9, 10–51)  
**Audit Date:** 2026-09-04  
**Working Directory:** `/workspaces/codespaces-blank`  
**Git HEAD:** `1a2b3c4` (Dirty working tree: modified & untracked audit artifacts)  

---

## 1. Executive Summary

Per **Section 0** and **Section 2** of [`instruction.md`](file:///workspaces/codespaces-blank/instruction.md), this forensic audit operates under the absolute rule: **The previous build, documentation, and pass messages are not the source of truth; only executable reality and verified file state govern.**

The previous agent claimed to have completed a 5-tier persistent memory operating system for the Antigravity platform. An exhaustive forensic inspection across [`scripts/`](file:///workspaces/codespaces-blank/scripts/), [`scripts/hooks/`](file:///workspaces/codespaces-blank/scripts/hooks/), [`.agents/hooks.json`](file:///workspaces/codespaces-blank/.agents/hooks.json), [`tools/bin/`](file:///workspaces/codespaces-blank/tools/bin/), and [`.agents/memory/`](file:///workspaces/codespaces-blank/.agents/memory/) reveals a dual reality:

1. **Substantial Algorithmic Implementation:** Significant, high-quality code was written across 29 Python modules (~12,500 lines of code) implementing specialized sub-engines: `secret_scanner.py` (Shannon entropy and regex patterns), `candidate_bus.py` (staged memory bus), `memory_compiler.py` (multi-criteria scoring and admission gate), `memory_reconciler.py` (transactional state machine with rollback), `procedural_engine.py` (step type classification and Invariant 16 isolation), `learning_loop.py` (retrieval decay curves and shadow linear reranker), and `memory_doctor.py` (6-dimension health check).
2. **Critical Integration & Runtime Severance:** Despite the volume of code, the system is **fragmented and disconnected**. Major architectural subsystems operate in silos or only execute inside unit tests. Specifically:
   - **Dense Semantic Retrieval Disconnected:** The primary search pipeline ([`scripts/search_memory.py`](file:///workspaces/codespaces-blank/scripts/search_memory.py) and [`scripts/query_router.py`](file:///workspaces/codespaces-blank/scripts/query_router.py)) does **not** call MemSearch or vector search at all; it relies entirely on lexical regex matching.
   - **MemSearch Backend Deficiencies:** [`scripts/memsearch_backend.py`](file:///workspaces/codespaces-blank/scripts/memsearch_backend.py) suffers from two severe bugs: device discovery warnings on stdout break `json.loads` (triggering silent keyword fallbacks), and its `delete()` method issues an invalid CLI command (`memsearch delete`), silently failing.
   - **Lifecycle Hooks Disconnected / Stubs:** [`scripts/hooks/post_tool_use.py`](file:///workspaces/codespaces-blank/scripts/hooks/post_tool_use.py) and [`scripts/hooks/stop_hook.py`](file:///workspaces/codespaces-blank/scripts/hooks/stop_hook.py) are non-functional stubs that record no telemetry and capture no experience. Global CLI configuration at `~/.gemini/antigravity-cli/hooks.json` explicitly has `"enabled": false`.
   - **Promotion Bypass:** [`scripts/memory_engine.py:promote_memory`](file:///workspaces/codespaces-blank/scripts/memory_engine.py#L215-L265) bypasses `memory_compiler.py` and `memory_reconciler.py`, blindly appending text to markdown files without verifying evidence or checking contradictions.
   - **Active Test Suite Failure:** Pytest execution identified an active failure in [`scripts/test_query_router.py:TestQueryRouter.test_successful_resolution_adr`](file:///workspaces/codespaces-blank/scripts/test_query_router.py#L98-L105) where `QueryRouter` filters out 3-letter abbreviations (`adr`), causing queries on architectural decisions to abstain.
   - **Fake Test Artifact:** [`scripts/verify_subagent_memory.py`](file:///workspaces/codespaces-blank/scripts/verify_subagent_memory.py) is a fake simulation script that tests nothing and prints synthetic passes.

---

## 2. Runtime Environment & Baseline Inspection

| Attribute | Forensic Baseline Value | Evaluation / Impact |
| :--- | :--- | :--- |
| **Operating System** | Linux 6.8.0-1052-azure (Ubuntu 22.04.1 LTS x86_64) | Standard GitHub Codespaces environment. |
| **System Python** | Python 3.12.1 (`/home/codespace/.python/current/bin/python3`) | Standard runner for scripts and tests. |
| **MemSearch Virtualenv** | Python 3.12.1 (`/workspaces/codespaces-blank/.venv-memsearch/bin/python3`) | Virtual environment housing `memsearch` Python package. |
| **MemSearch CLI** | `/home/codespace/.local/bin/memsearch` (v0.4.19) | Dedicated binary with ONNX embedding support. |
| **Vector DB Substrate** | Milvus Lite (`.agents/memory/.memsearch/milvus.db` & `~/.memsearch/milvus.db`) | Parquet partition files and Flat index files exist. |
| **Antigravity CLI** | Native app directory at `/home/codespace/.gemini/antigravity-cli` | Configuration and brain state present; binary not in system PATH. |
| **Global Hook Config** | `/home/codespace/.gemini/antigravity-cli/hooks.json` | **`"enabled": false`** (Platform hooks globally disabled). |
| **Workspace Hook Config** | [`.agents/hooks.json`](file:///workspaces/codespaces-blank/.agents/hooks.json) | `"enabled": true` for `antigravity-platform-hooks`. |
| **Test Suite Baseline** | 284 pytest cases collected | **283 Passed, 1 Failed** (`test_successful_resolution_adr`). |

---

## 3. Deep File-by-File Inspection

### 3.1 Inspection of `scripts/hooks/` & Lifecycle Configuration

#### [`.agents/hooks.json`](file:///workspaces/codespaces-blank/.agents/hooks.json)
- **Claim:** Declares platform hooks for `PreInvocation`, `PreToolUse`, `PostToolUse`, and `Stop`.
- **Reality:** Syntactically valid JSON. Configures 4 hook entry points targeting `/workspaces/codespaces-blank/scripts/hooks/*.py` with 15-second timeouts.
- **Defects / Gaps:** 
  1. `PreToolUse` matcher is restricted to `"write_to_file|replace_file_content|run_command"`. Tools like `manage_task` (which passes `Input` into interactive bash sessions) or MCP tool calls are unmonitored.
  2. The configuration is duplicated at `~/.gemini/antigravity-cli/hooks.json` under `"antigravity-memory-guards"`, where `"enabled": false` is set.

#### [`scripts/hooks/pre_invocation.py`](file:///workspaces/codespaces-blank/scripts/hooks/pre_invocation.py) (53 lines)
- **Claim:** Reads [`.agents/memory/CURRENT.md`](file:///workspaces/codespaces-blank/.agents/memory/CURRENT.md) and injects active context directives before agent invocation.
- **Reality:** Parses JSON from stdin, hashes `conversationId` into `/tmp/ag_preinv_<hash>` for idempotency, checks if `CURRENT.md` contains `"Current Objective"`, and returns:
  `{"injectSteps": [{"ephemeralMessage": "Antigravity Memory Directive: Memory is advisory. Inspect .agents/memory/INDEX.md and load only relevant context."}]}`.
- **Defects / Gaps:** It does not invoke [`scripts/context_compiler.py`](file:///workspaces/codespaces-blank/scripts/context_compiler.py). It injects a static advisory string rather than dynamic, layered context packages.

#### [`scripts/hooks/pre_tool_use.py`](file:///workspaces/codespaces-blank/scripts/hooks/pre_tool_use.py) (80 lines)
- **Claim:** Intercepts tool calls to prevent writing secrets, credentials, or private keys.
- **Reality:** Extracts `CodeContent`, `ReplacementContent`, and `CommandLine` from `toolCall.args`, hashes the payload to check `~/.cache/antigravity/security_cache/`, and invokes [`scripts/secret_scanner.py:scan_text`](file:///workspaces/codespaces-blank/scripts/secret_scanner.py#L461). If secrets are found, returns `{"decision": "deny", "reason": "..."}`.
- **Defects / Gaps:**
  1. **Fail-Open Behavior:** Lines 74-76 catch general exceptions and emit `{"decision": "allow", "reason": f"Hook exception handled gracefully: {str(e)}"}`. A crash in the scanner allows secrets through.
  2. **Parameter Blindness:** Does not scan `Input` in `manage_task`, `TargetContent` in `replace_file_content`, or arbitrary MCP tool arguments.

#### [`scripts/hooks/post_tool_use.py`](file:///workspaces/codespaces-blank/scripts/hooks/post_tool_use.py) (46 lines)
- **Claim:** "Performs syntax tracking, lint feedback recording, and execution health auditing. Enqueues candidate memory items."
- **Reality:** **FUNCTIONAL STUB.** Inspects if target file ends in `.json`, attempts `json.load(f)`, catches exceptions with `except Exception: pass`, and unconditionally emits `print(json.dumps({}))`.
- **Defects / Gaps:** Does not record syntax feedback, does not interface with `candidate_bus.py`, does not capture error traces, and does not record tool execution telemetry.

#### [`scripts/hooks/stop_hook.py`](file:///workspaces/codespaces-blank/scripts/hooks/stop_hook.py) (31 lines)
- **Claim:** "Session Guard: Verifies active working session state and ensures clean shutdown. Enqueues session summarization."
- **Reality:** **FUNCTIONAL STUB.** Extracts `fullyIdle` and `terminationReason` into local variables and unconditionally emits `{"decision": "stop"}`.
- **Defects / Gaps:** Never checks uncommitted git changes, never triggers session log generation (`session_manager.py:end_session`), never updates `CURRENT.md`, and never reconciles candidate memories.

---

### 3.2 Inspection of Core Scripts (`scripts/`)

#### [`scripts/search_memory.py`](file:///workspaces/codespaces-blank/scripts/search_memory.py) (448 lines)
- **Claim:** Scoped hybrid memory search engine.
- **Reality:** Functional, fast lexical search engine using regular expressions, heading weights, and keyword density over Markdown files.
- **Critical Finding:** **Zero vector search capability.** `search_memory.py` does not import, reference, or call `memsearch`, `Milvus`, or embeddings. The entire retrieval pipeline is purely lexical.

#### [`scripts/query_router.py`](file:///workspaces/codespaces-blank/scripts/query_router.py) (920 lines)
- **Claim:** Scope-aware intent classifier, layered recall router, query expander, and explicit abstention gate.
- **Reality:** Implements query intent classification (`present-state`, `historical as-of`, `why/rationale`, `procedural`, `debugging`), scope determination, and abstention logic (`"No sufficiently trustworthy memory found"`).
- **Critical Bug (Active Test Failure):**
  - In `scripts/query_router.py:702`:
    ```python
    for term in expansion["expanded_terms"][:2]:
        if term != expansion["original_query"].lower() and len(term) > 3:
            search_terms.append(term)
    ```
  - The condition `len(term) > 3` filters out valid 3-letter technical abbreviations such as `adr` (`len("adr") == 3`).
  - Consequently, queries like `"Why did we choose the 5-tier memory architecture?"` do not search `adr`, fail to retrieve `ADR-001` from `DECISIONS.md`, calculate a max confidence of 0.12, and erroneously abstain. This causes `TestQueryRouter.test_successful_resolution_adr` to fail.

#### [`scripts/memsearch_backend.py`](file:///workspaces/codespaces-blank/scripts/memsearch_backend.py) (271 lines)
- **Claim:** Adapter boundary isolating MemSearch/Milvus vector database operations.
- **Reality:**
  - Defines `SemanticRetrievalBackend` interface and `MemSearchBackend` implementation.
  - Interacts with `/home/codespace/.local/bin/memsearch` via `subprocess.run`.
- **Critical Defects:**
  1. **Python Import Failure:** `_check_python_pkg()` does `import memsearch`, which fails under system Python (`ModuleNotFoundError`) because `memsearch` is installed in `/workspaces/codespaces-blank/.venv-memsearch/`.
  2. **Non-Existent CLI Delete Command:** Line 149 executes `memsearch delete <path>`. The `memsearch` CLI (v0.4.19) has no `delete` subcommand (`Error: No such command 'delete'`). The call fails, leaving stale vector chunks in Milvus indefinitely.
  3. **Output Parsing Failure Swallowed:** Line 177 attempts `json.loads(res.stdout)`. Hardware warnings emitted by ONNX Runtime to stdout cause `JSONDecodeError`, which lines 178-179 swallow with `pass`, falling back to word count matching.

#### [`scripts/candidate_bus.py`](file:///workspaces/codespaces-blank/scripts/candidate_bus.py) (872 lines)
- **Claim:** Automatic experience and candidate memory capture from tool events.
- **Reality:** Excellent standalone logic. Implements `Candidate` dataclass, secret pre-screening, SHA-256 deduplication, file locking on `candidates.jsonl`, noise filtering, and provenance tracking.
- **Integration Gap:** Completely disconnected from the runtime lifecycle. No hooks (`post_tool_use.py` or `stop_hook.py`) invoke `CandidateBus`. Staged candidates accumulate without automated draining.

#### [`scripts/memory_compiler.py`](file:///workspaces/codespaces-blank/scripts/memory_compiler.py) (1040 lines)
- **Claim:** Candidate scoring, classification, and admission gatekeeper.
- **Reality:** Computes composite scores across novelty, durability, evidence, and redundancy, emitting structured `AdmissionDecision` records (ACCEPT, HOLD, REJECT) into `.agents/memory/inbox/admission_decisions.jsonl`.
- **Integration Gap:** `MemoryCompiler` only writes decisions to a JSONL log; it **does not write or promote accepted memories into canonical Markdown files**. That was left to `MemoryReconciler`, but the two are not connected.

#### [`scripts/memory_reconciler.py`](file:///workspaces/codespaces-blank/scripts/memory_reconciler.py) (1209 lines)
- **Claim:** Transactional memory reconciler with conflict detection and supersession lineage.
- **Reality:** Features `CanonicalRecord` parsing, `difflib` similarity, version/architecture contradiction detection, atomic file replacement, and journal logging (`reconciliation_journal.jsonl`).
- **Integration Gap:** Only invoked in `tests/test_memory_reconciler.py` and `scripts/memory_benchmark.py`. Never executed by runtime hooks, CLI commands, or `memory_engine.py`.

#### [`scripts/memory_index_queue.py`](file:///workspaces/codespaces-blank/scripts/memory_index_queue.py) (744 lines)
- **Claim:** Single-writer index queue and control plane for vector indexing.
- **Reality:** Implements `index_queue.jsonl` management, file lease locking (`index_writer.lease.lock`), update coalescing, and health transitions (`HEALTHY`, `STALE`, `DEGRADED`, etc.).
- **Integration Gap:** No automatic process enqueues files when Markdown changes occur, and no background daemon runs `drain()` to process the queue.

#### [`scripts/memory_engine.py`](file:///workspaces/codespaces-blank/scripts/memory_engine.py) (478 lines)
- **Claim:** Unified CLI for session lifecycle and memory operations.
- **Reality:** Naive, early-stage implementation.
- **Critical Non-Conformance:**
  - `promote_memory()` (lines 215-265) takes raw text, prepends `- [YYYY-MM-DD] [TYPE] (Durability N):`, and appends it directly to a file.
  - It bypasses `CandidateBus`, `MemoryCompiler`, `MemoryReconciler`, evidence verification, and contradiction checks entirely.

#### [`scripts/session_manager.py`](file:///workspaces/codespaces-blank/scripts/session_manager.py) (522 lines)
- **Claim:** Robust session start and end management with atomic file operations.
- **Reality:** Implements session log creation and `CURRENT.md` updates.
- **Defect:** Lines 448 and 474 use standard `open(filepath, "w")` without atomic tmpfiles or file locks, leaving files vulnerable to truncation on crashes.

#### [`scripts/procedural_engine.py`](file:///workspaces/codespaces-blank/scripts/procedural_engine.py) (991 lines)
- **Claim:** Distills multi-step procedures from episodic sessions into candidate workflows.
- **Reality:** Comprehensive implementation distinguishing `OBSERVED_COMMAND`, `VERIFIED_STEP`, `INFERRED_STEP`, and preserving tool provenance. Strictly enforces Invariant 16 (staging in `inbox/procedures/`).
- **Integration Gap:** Only runs in `tests/test_procedural_engine.py`. Disconnected from live session shutdowns.

#### [`scripts/learning_loop.py`](file:///workspaces/codespaces-blank/scripts/learning_loop.py) (1568 lines)
- **Claim:** Memory decay curves, access reinforcement, and shadow mode ranking.
- **Reality:** Implements decay models and shadow reranker with strict isolation (`shadow_ranker_v1.json`). Contains `ReciprocalRankFusion` class (lines 586-650).
- **Critical Finding:** `ReciprocalRankFusion` fuses only lexical score, authority, importance, and freshness. It does **not** fuse vector similarity scores with lexical scores.

#### [`scripts/secret_scanner.py`](file:///workspaces/codespaces-blank/scripts/secret_scanner.py) (703 lines)
- **Claim:** Gatekeeper scanning memory and code for leaked credentials.
- **Reality:** Highly capable implementation combining 20+ credential regexes, Shannon entropy evaluation, safe placeholder whitelisting, and snippet redaction.
- **Vulnerability:** Many other modules (`memory_feedback.py`, `memory_engine.py`, `procedural_engine.py`, `context_compiler.py`, `memory_reconciler.py`, `memory_compiler.py`) define a fallback `DummyScanner` that returns `is_clean = True` if `secret_scanner` fails to import.

#### [`scripts/verify_subagent_memory.py`](file:///workspaces/codespaces-blank/scripts/verify_subagent_memory.py) (37 lines)
- **Claim:** Verifies subagent memory context propagation and workspace isolation.
- **Reality:** **FALSE TEST / STUB.** Compares two hardcoded string variables (`current_cwd != os.path.dirname(...)`), prints `"PASS: Subagent isolation confirmed"`, prints `"PASS: Global rules inheritance check"`, and exits 0. It executes no real assertions or runtime isolation tests.

---

### 3.3 Inspection of Tools in `tools/bin/`

| Tool Binary | Underlying Target | Execution Verification | Real State & Capabilities |
| :--- | :--- | :--- | :--- |
| **`agy-memory-doctor`** | [`scripts/memory_doctor.py`](file:///workspaces/codespaces-blank/scripts/memory_doctor.py) | **PASS (Exit 0)** | Comprehensive 6-dimension diagnostic engine (Markdown integrity, secrets, coherence, vector health, inbox backlog, telemetry quality). |
| **`agy-agent-doctor`** | Bash script | **PASS (Exit 0)** | Checks `AGENTS.md`, `.agents/hooks.json` syntax, and hook executable paths. |
| **`agy-env-doctor`** | Python 3 script | **PASS (Exit 0)** | Comprehensive audit of environment, core CLI, toolchain, and permissions. |
| **`agy-security-doctor`** | Bash script | **PASS (Exit 0)** | Runs Semgrep, CodeQL, and Bandit SAST scanners. |
| **`agy-network-doctor`** | Python 3 script | **PASS (Exit 0)** | Audits PCAP analysis tools (tshark, tcpdump) against fixtures. |
| **`agy-web-doctor`** | Python 3 script | **PASS (Exit 0)** | Audits Node, Playwright, Chrome, ESLint, Prettier. |
| **`agy-wasm-doctor`** | Python 3 script | **PASS (Exit 0)** | Audits Wasm toolchains (wasmtime, emscripten, hexana). |
| **`agy-mcp-doctor`** | Python 3 script | **PASS (Exit 0)** | Audits MCP configuration and stdio server connectivity. |
| **`agy-binary-doctor`** | Bash script | **PASS (Exit 0)** | Audits binary analysis tools (gdb, lldb, radare2, rizin, ghidra). |
| **`agy-android-doctor`** | Bash script | **PASS (Exit 0)** | Audits Android SDK, adb, apktool, jadx. |

---

### 3.4 Inspection of Memory Layers (`.agents/memory/` & `~/.gemini/antigravity-cli/memory/`)

#### Tier 0: Governance Layer
- **Global:** `~/.gemini/antigravity-cli/memory/POLICY.md` (13 core immutable policy rules).
- **Workspace:** `.agents/rules/memory.md` (Operational loading rules).
- **Evaluation:** **REAL & AUTHORITATIVE.** Clear boundaries, date stamping rules, zero-secret mandates, and authority hierarchy.

#### Tier 1: Working State Layer
- **Workspace:** [`.agents/memory/CURRENT.md`](file:///workspaces/codespaces-blank/.agents/memory/CURRENT.md)
- **Evaluation:** **PARTIAL / STALE.** Contains `Objective 99` stamped on 2026-09-01. Not kept current across subsequent working sessions.

#### Tier 2: Episodic Memory Layer
- **Workspace:** [`.agents/memory/sessions/`](file:///workspaces/codespaces-blank/.agents/memory/sessions/)
- **Files Present:** `2026-09-01-1546.md`, `2026-09-01-1617.md`, `2026-09-02-1015.md`, `2026-09-02-1430.md`.
- **Evaluation:** **PARTIAL / INCOMPLETE.** Missing session records for September 3 and September 4, during which extensive development occurred.

#### Tier 3: Candidate Memory Layer
- **Workspace:** [`.agents/memory/inbox/candidates.jsonl`](file:///workspaces/codespaces-blank/.agents/memory/inbox/candidates.jsonl) (12 candidates staged).
- **Decisions Log:** [`.agents/memory/inbox/admission_decisions.jsonl`](file:///workspaces/codespaces-blank/.agents/memory/inbox/admission_decisions.jsonl) (5 decisions recorded).
- **Procedures Staged:** `inbox/procedures/proc-20260903-python3-01.md`, `proc-20260903-session-memory-audit.md`.
- **Evaluation:** **REAL STAGING / BLOCKED PROMOTION.** Candidates are properly isolated in the inbox per Invariant 16, but accumulate without automated promotion or reconciliation.

#### Tier 4: Canonical Memory Layer
- **Workspace Files:** `DECISIONS.md`, `GOTCHAS.md`, `ARCHITECTURE.md`, `INDEX.md`.
- **Global Files:** `GENERAL.md`, `USER.md`, `ENVIRONMENT.md`, `domains/`, `tools/`.
- **Evaluation:** **PARTIAL.** Core files are structured with date stamps and confidence markers. However:
  - `domains/database.md`, `domains/frontend.md`, `domains/medical.md` are 1-line stubs.
  - `inbox/admission_decisions.jsonl` accepted candidate `cand_proc_004` for promotion to `.agents/memory/PROCEDURES.md`, but `PROCEDURES.md` does not exist on disk.

---

## 4. Pattern Hunt for False Completion

An automated pattern scan was conducted across all files in `scripts/`, `tools/bin/`, and `.agents/`:

| Pattern | Occurrences | Forensic Context & Findings |
| :--- | :---: | :--- |
| **`TODO` / `FIXME`** | 4 | In `audit_memory.py:335` (detection rule for cleanup comments) and `.agents/skills/native-development/SKILL.md:72` (Mermaid chart labels). No operational TODO placeholders found. |
| **`NotImplementedError`** | 6 | All 6 in [`scripts/memsearch_backend.py:34-54`](file:///workspaces/codespaces-blank/scripts/memsearch_backend.py#L34-L54) defining the abstract interface `SemanticRetrievalBackend`. |
| **`except Exception: pass`** | 22 | Found across `scripts/audit_memory.py` (10), `scripts/memory_doctor.py` (9), `scripts/compact_memory.py` (2), `scripts/session_manager.py` (2), `scripts/hooks/post_tool_use.py` (1). In `post_tool_use.py`, JSON syntax errors are swallowed silently. |
| **`DummyScanner` / `MockResult`** | 7 | Fallback dummy classes returning `is_clean = True` found in `memory_feedback.py:51`, `memory_engine.py:37`, `procedural_engine.py:37`, `validate_memory.py:26`, `context_compiler.py:45`, `memory_reconciler.py:45`, `memory_compiler.py:56`. |
| **`simulate` / `fake`** | 12 | Used legitimately in test harnesses (`memory_benchmark.py`, `test_concurrency.py`, `context_compiler.py` adversarial fixtures). Found **illegitimately** in `scripts/verify_subagent_memory.py` (fake test). |

---

## 5. Architectural Gap Analysis: Live vs Intended

```
Intended (Instruction.md Section 10):
Experience -> CandidateBus -> Compiler -> Reconciler -> Canonical Markdown -> IndexQueue -> MemSearch (Dense) \
                                                                                                                ==> RRF Hybrid Fusion -> ContextCompiler -> Agent
                                                                                       Lexical (BM25/Regex)    /

Actual Repository Reality:
Experience -X-> [CandidateBus (Isolated)] -X-> [Compiler (Logs only)] -X-> [Reconciler (Isolated)]
                                                                               |
                                                                               v
Live Markdown Updates: memory_engine.py --(Direct Append, No Gate)----------> Canonical Markdown
                                                                               |
                                                                               +---> Lexical Search (Regex) ---> ContextCompiler -> Agent
                                                                               |
                                      IndexQueue (No Daemon)                   |
                                         |                                     |
                                         v                                     |
                                  MemSearch / Milvus Lite (DISCONNECTED FROM LIVE SEARCH)
```

1. **No Live Experience Capture:** Agent tool calls and completions in real sessions do not invoke `CandidateBus`.
2. **Disconnected Pipeline:** `CandidateBus` does not trigger `MemoryCompiler`. `MemoryCompiler` does not trigger `MemoryReconciler`. `MemoryReconciler` does not enqueue to `MemoryIndexQueue`.
3. **Disconnected Semantic Retrieval:** Live queries routed through `query_router.py` and `context_compiler.py` query `search_memory.py`, which is purely lexical. MemSearch vector embeddings in Milvus are never queried during normal agent operations.
4. **No True RRF Hybrid Retrieval:** The retrieval path does not perform Reciprocal Rank Fusion between dense embeddings and sparse/lexical hits.

---

## 6. Audit Verdict & Next Actions

The repository represents an advanced, near-complete implementation where **all required algorithms exist in code**, but several critical runtime connections, hooks, and adapters were left disconnected or stubbed.

### Primary Remediations Required in Stage 4:
1. **Fix `query_router.py`:** Update line 702 to `len(term) >= 3` so abbreviation expansions (`adr`) are queried, resolving the test failure.
2. **Connect MemSearch to Retrieval:** Wire `MemSearchBackend.search()` into `search_memory.py` and implement true hybrid RRF fusion with lexical search results.
3. **Fix `memsearch_backend.py`:** Sanitize device discovery warnings before `json.loads` and replace `memsearch delete` CLI call with Python-level `MilvusStore.delete_by_source()`.
4. **Upgrade Lifecycle Hooks:** Wire `candidate_bus.py` into `post_tool_use.py` and implement session checkpointing/reconciliation in `stop_hook.py`.
5. **Enforce Evidence Gate on Promotion:** Replace naive append in `memory_engine.py:promote_memory` with calls to `MemoryCompiler` and `MemoryReconciler`.
6. **Eliminate Fail-Open Security:** Remove `DummyScanner` fallbacks that default to `is_clean = True`.
