# INTEGRATION AUDIT REPORT
## Antigravity Memory OS — Phase 2 Subsystem Boundary Audit
**Audit Authority:** Core Repair Engineer (Agent 3)  
**Specification Reference:** [`instruction.md`](file:///workspaces/codespaces-blank/instruction.md) (Sections 10-35, 78-81, 90-95, 122)  
**Audit Date:** 2026-09-04  
**Audit Location:** `/workspaces/codespaces-blank/.agent/memory-audit/audit/INTEGRATION_AUDIT.md`  
**Overall Integration Status:** DEGRADED / PARTIALLY SEVERED  

---

## 1. Executive Summary & Integration Map

This audit evaluates the 10 structural integration boundaries connecting the subsystems of Antigravity Memory OS. Each boundary was inspected for interface conformance, inter-process protocol execution, data contract adherence, error handling, and silent degradation.

### Integration Topology Diagram
```mermaid
graph TB
    subgraph Antigravity Platform Boundary
        HOOKS[".agents/hooks.json"]
        PRE_INV["scripts/hooks/pre_invocation.py"]
        PRE_TOOL["scripts/hooks/pre_tool_use.py"]
        POST_TOOL["scripts/hooks/post_tool_use.py"]
        STOP["scripts/hooks/stop_hook.py"]
    end

    subgraph Candidate Ingestion Boundary
        CBUS["scripts/candidate_bus.py"]
        INBOX[".agents/memory/inbox/candidates.jsonl"]
        SCANNER["scripts/secret_scanner.py"]
    end

    subgraph Compilation & Reconciliation Boundary
        MCOMP["scripts/memory_compiler.py"]
        MRECON["scripts/memory_reconciler.py"]
        DECISIONS[".agents/memory/inbox/admission_decisions.jsonl"]
    end

    subgraph Canonical Storage Plane
        LOCKM["scripts/lock_manager.py"]
        MENG["scripts/memory_engine.py"]
        CANONICAL[".agents/memory/*.md"]
    end

    subgraph Index Control Plane
        IQUEUE["scripts/memory_index_queue.py"]
        QFILE[".agents/memory/index_queue.jsonl"]
        LEASE[".agents/memory/index_writer.lease"]
        QHEALTH[".agents/memory/index_health.json"]
    end

    subgraph Semantic Vector Substrate
        MBACK["scripts/memsearch_backend.py"]
        MCLI["memsearch CLI"]
        MILVUS[".memsearch/milvus.db"]
    end

    subgraph Retrieval & Routing Plane
        QROUTER["scripts/query_router.py"]
        SEARCH["scripts/search_memory.py"]
        CCOMP["scripts/context_compiler.py"]
    end

    subgraph Verification & Maintenance
        BENCH["scripts/memory_benchmark.py"]
        COMPACT["scripts/compact_memory.py"]
        CONTRA["scripts/detect_contradictions.py"]
        LEARN["scripts/learning_loop.py"]
    end

    %% Expected connections with audit status markings
    HOOKS -.->|B1: Configured| PRE_INV & PRE_TOOL & POST_TOOL & STOP
    POST_TOOL x-.-x|B1: DISCONNECTED| CBUS
    STOP x-.-x|B1: DISCONNECTED (DEF-005)| MRECON
    PRE_TOOL -->|B1: WIRED| SCANNER
    CBUS -->|B2: WIRED| SCANNER
    CBUS -->|B2: WIRED| INBOX
    INBOX -->|B2: PARTIAL| MCOMP
    MCOMP -->|B2: WIRED| DECISIONS
    MCOMP x-.-x|B2: DISCONNECTED| MRECON
    MRECON -->|B3: WIRED| LOCKM --> CANONICAL
    MRECON x-.-x|B3: DISCONNECTED| IQUEUE
    IQUEUE -->|B4: WIRED| QFILE & LEASE & QHEALTH
    IQUEUE -->|B4: WIRED| MBACK
    MBACK x-.-x|B5: BROKEN (DEF-001, DEF-002)| MCLI --> MILVUS
    QROUTER -->|B6: WIRED| SEARCH
    SEARCH x-.-x|B6: DISCONNECTED (DEF-003)| MBACK
    SEARCH -->|B7: PARTIAL| CCOMP
    CCOMP x-.-x|B7: DISCONNECTED| PRE_INV
    BENCH x-.-x|B10: MOCKED (DEF-004)| MBACK
```

---

## 2. Boundary-by-Boundary Audit & Conformance Analysis

### Boundary 1: Platform Lifecycle Hooks $\leftrightarrow$ Memory Subsystem
- **Upstream Component:** Antigravity CLI Platform Hook Runner
- **Downstream Component:** [`scripts/hooks/`](file:///workspaces/codespaces-blank/scripts/hooks/) (`pre_invocation.py`, `pre_tool_use.py`, `post_tool_use.py`, `stop_hook.py`)
- **Protocol:** JSON over `stdin`/`stdout`, process execution timeout = 15s.
- **Contract Defined In:** [`.agents/hooks.json`](file:///workspaces/codespaces-blank/.agents/hooks.json) & [`AGENTS.md`](file:///workspaces/codespaces-blank/AGENTS.md)
- **Status:** **DEGRADED / INCONSISTENT**
- **Findings:**
  1. **Hook Name Inconsistency (DEF-005)**: [`.agents/hooks.json:38`](file:///workspaces/codespaces-blank/.agents/hooks.json#L38) points to `scripts/hooks/stop_hook.py`. In contrast, [`AGENTS.md:150`](file:///workspaces/codespaces-blank/AGENTS.md#L150) explicitly specifies `scripts/hooks/stop_guard.py`. While both files existed in `scripts/hooks/`, running different filenames creates configuration divergence and verification ambiguities.
  2. **Missing PostToolUse Capture Wiring (DEF-008)**: [`scripts/hooks/post_tool_use.py`](file:///workspaces/codespaces-blank/scripts/hooks/post_tool_use.py) implements quick JSON syntax checks on edited files, but **never imports or executes [`CandidateBus.capture_tool_event()`](file:///workspaces/codespaces-blank/scripts/candidate_bus.py#L477)**. Runtime experience and error events are never automatically captured into the candidate stream.
  3. **Pass-through Stop Hook (DEF-010)**: [`scripts/hooks/stop_hook.py`](file:///workspaces/codespaces-blank/scripts/hooks/stop_hook.py) always emits `{"decision": "stop"}` without evaluating un-reconciled candidate backlog or triggering background maintenance.
  4. **PreToolUse Security Gate is Active**: [`scripts/hooks/pre_tool_use.py`](file:///workspaces/codespaces-blank/scripts/hooks/pre_tool_use.py) is properly wired to [`secret_scanner.py`](file:///workspaces/codespaces-blank/scripts/secret_scanner.py) and intercepts write operations containing credential patterns with exit code 0 and `{"decision": "deny"}`.

### Boundary 2: Candidate Bus $\leftrightarrow$ Memory Compiler & Reconciler
- **Upstream Component:** [`scripts/candidate_bus.py`](file:///workspaces/codespaces-blank/scripts/candidate_bus.py) & [`.agents/memory/inbox/candidates.jsonl`](file:///workspaces/codespaces-blank/.agents/memory/inbox/candidates.jsonl)
- **Downstream Component:** [`scripts/memory_compiler.py`](file:///workspaces/codespaces-blank/scripts/memory_compiler.py) & [`scripts/memory_reconciler.py`](file:///workspaces/codespaces-blank/scripts/memory_reconciler.py)
- **Protocol:** Durable JSONL file append under file lock (`fcntl.flock`).
- **Status:** **PARTIALLY SEVERED / STALLED (DEF-006)**
- **Findings:**
  1. **Candidate Staging Accumulation**: Candidate Bus properly writes clean records to `.agents/memory/inbox/candidates.jsonl`. However, **12 candidate items have accumulated in the inbox** without ever being processed or promoted.
  2. **Compiler Batch Disconnect**: [`MemoryCompiler.compile_inbox()`](file:///workspaces/codespaces-blank/scripts/memory_compiler.py#L894) reads candidates and writes `admission_decisions.jsonl`, but defaults to `dry_run=True` and does not delete processed candidates from `candidates.jsonl`.
  3. **Compiler $\leftrightarrow$ Reconciler Missing Link**: No automated glue connects the output of `MemoryCompiler` to `MemoryReconciler.reconcile()`. The reconciler only runs when manually invoked with synthetic test inputs.

### Boundary 3: Canonical Memory $\leftrightarrow$ Index Queue Control Plane
- **Upstream Component:** [`scripts/memory_reconciler.py`](file:///workspaces/codespaces-blank/scripts/memory_reconciler.py) & [`scripts/memory_engine.py`](file:///workspaces/codespaces-blank/scripts/memory_engine.py)
- **Downstream Component:** [`scripts/memory_index_queue.py`](file:///workspaces/codespaces-blank/scripts/memory_index_queue.py)
- **Protocol:** IPC / Python Method Call (`IndexQueueManager.enqueue()`)
- **Status:** **DISCONNECTED (DEF-009)**
- **Findings:**
  1. [`scripts/memory_reconciler.py`](file:///workspaces/codespaces-blank/scripts/memory_reconciler.py) performs atomic writes and supersession updates to `.agents/memory/*.md`, but contains **zero imports or calls to `IndexQueueManager`**.
  2. [`scripts/memory_engine.py`](file:///workspaces/codespaces-blank/scripts/memory_engine.py) contains zero calls to `IndexQueueManager`.
  3. The index queue [`.agents/memory/index_queue.jsonl`](file:///workspaces/codespaces-blank/.agents/memory/index_queue.jsonl) is never notified when canonical Markdown files change. Index updates can only occur if an external process enqueues them manually.

### Boundary 4: Index Queue Control Plane $\leftrightarrow$ MemSearch Backend Adapter
- **Upstream Component:** [`scripts/memory_index_queue.py`](file:///workspaces/codespaces-blank/scripts/memory_index_queue.py)
- **Downstream Component:** [`scripts/memsearch_backend.py`](file:///workspaces/codespaces-blank/scripts/memsearch_backend.py)
- **Protocol:** Python interface: `SemanticRetrievalBackend.index()`, `delete()`, `health()`, `rebuild()`.
- **Status:** **OPERATIONAL**
- **Findings:**
  1. `IndexQueueManager.drain()` acquires a single-writer lease lock on `.agents/memory/index_writer.lease`.
  2. Rapid consecutive file changes are coalesced into a single final job per file.
  3. Method calls `self.backend.index(source_path)` pass through to `MemSearchBackend.index()`.
  4. Health check properly inspects canonical vs indexed revision hashes.

### Boundary 5: MemSearch Backend Adapter $\leftrightarrow$ Native MemSearch CLI & Milvus Lite
- **Upstream Component:** [`scripts/memsearch_backend.py`](file:///workspaces/codespaces-blank/scripts/memsearch_backend.py)
- **Downstream Component:** `memsearch` CLI (`/home/codespace/.local/bin/memsearch`) & Milvus Lite (`~/.memsearch/milvus.db`)
- **Protocol:** CLI Subprocess execution (`subprocess.run(["memsearch", ...])`).
- **Status:** **CRITICALLY BROKEN (DEF-001, DEF-002)**
- **Findings:**
  1. **CLI Default Provider Crash (DEF-001)**: `memsearch config get embedding.provider` returns `openai`. In the absence of an `OPENAI_API_KEY`, invoking `memsearch search "query" --json-output` raises `openai.OpenAIError: Missing credentials` and aborts.
  2. **ONNX Output Corrupts JSON Decoding (DEF-002)**: When `--provider onnx` is passed, ONNX Runtime outputs a diagnostic warning to `stdout` before the JSON array:
     ```text
     2026-09-04 07:16:42.972426979 [W:onnxruntime:Default, device_discovery.cc:146 GetPciBusId] Skipping pci_bus_id for PCI path ...
     [
       { "chunk_hash": "...", ... }
     ]
     ```
     In [`scripts/memsearch_backend.py:177`](file:///workspaces/codespaces-blank/scripts/memsearch_backend.py#L177), `json.loads(res.stdout)` raises `json.JSONDecodeError` because of the non-JSON text on line 1.
     Lines 178-179 swallow the exception (`except json.JSONDecodeError: pass`) and fall through to a naive keyword counter over local files, **silently neutralizing all semantic vector search capabilities**.

### Boundary 6: Query Router $\leftrightarrow$ Search Subsystems (Lexical + Dense)
- **Upstream Component:** [`scripts/query_router.py`](file:///workspaces/codespaces-blank/scripts/query_router.py)
- **Downstream Component:** [`scripts/search_memory.py`](file:///workspaces/codespaces-blank/scripts/search_memory.py) & [`scripts/memsearch_backend.py`](file:///workspaces/codespaces-blank/scripts/memsearch_backend.py)
- **Protocol:** Python function call (`run_memory_search()`)
- **Status:** **PARTIALLY SEVERED (DEF-003)**
- **Findings:**
  1. `QueryRouter.route_query()` calls `search_memory.run_memory_search()`.
  2. [`scripts/search_memory.py`](file:///workspaces/codespaces-blank/scripts/search_memory.py) contains only lexical regex and keyword token matching (`extract_section_snippets()`).
  3. `search_memory.py` **never calls `MemSearchBackend` and implements no Reciprocal Rank Fusion (RRF)**. Queries requiring semantic expansion fail completely unless exact keywords are present.

### Boundary 7: Search Engine $\leftrightarrow$ Context Compiler & Agent Delivery
- **Upstream Component:** [`scripts/search_memory.py`](file:///workspaces/codespaces-blank/scripts/search_memory.py)
- **Downstream Component:** [`scripts/context_compiler.py`](file:///workspaces/codespaces-blank/scripts/context_compiler.py) & [`scripts/hooks/pre_invocation.py`](file:///workspaces/codespaces-blank/scripts/hooks/pre_invocation.py)
- **Protocol:** In-memory dataclass translation / CLI execution.
- **Status:** **DISCONNECTED (DEF-007)**
- **Findings:**
  1. [`scripts/context_compiler.py`](file:///workspaces/codespaces-blank/scripts/context_compiler.py) is well implemented: supports L1/L2/L3 progressive disclosure, enforces token budgets, and computes trust verdicts (`CERTIFY`, `ADVISORY`, `WARN`, `BLOCK`).
  2. However, [`scripts/hooks/pre_invocation.py`](file:///workspaces/codespaces-blank/scripts/hooks/pre_invocation.py) **never calls `context_compiler.py`**. The agent context injection is static: it merely reads up to 1KB of `CURRENT.md` and outputs an advisory reminder without any dynamic recall.

### Boundary 8: Compaction & Contradiction Tools $\leftrightarrow$ Canonical Storage
- **Upstream Component:** [`scripts/compact_memory.py`](file:///workspaces/codespaces-blank/scripts/compact_memory.py) & [`scripts/detect_contradictions.py`](file:///workspaces/codespaces-blank/scripts/detect_contradictions.py)
- **Downstream Component:** Canonical Markdown files in `.agents/memory/` and `~/.gemini/antigravity-cli/memory/`
- **Protocol:** Direct file read and atomic rewrite via `lock_manager.py`.
- **Status:** **OPERATIONAL (STANDALONE)**
- **Findings:**
  1. Both tools inspect canonical files safely and compute accurate line/byte budgets, token counts, and contradiction markers.
  2. Both respect file locks and transactional boundaries.
  3. Gaps exist only in automation: neither tool is wired into a recurring lifecycle cron or stop hook.

### Boundary 9: Learning Loop Shadow Mode $\leftrightarrow$ Live Production Path
- **Upstream Component:** [`scripts/learning_loop.py`](file:///workspaces/codespaces-blank/scripts/learning_loop.py)
- **Downstream Component:** Production Retrieval Path ([`scripts/search_memory.py`](file:///workspaces/codespaces-blank/scripts/search_memory.py))
- **Protocol:** Isolated shadow evaluation files (`.agents/memory/shadow_eval/`).
- **Status:** **OPERATIONAL & PROPERLY ISOLATED**
- **Findings:**
  1. Conforms strictly to Instruction.md Section 221 & 222: the learned ranker operates exclusively in SHADOW mode.
  2. Model weights, feature schema (`FEATURE_SCHEMA_VERSION = "1.0.0"`), and decay ledger operate in isolation and do not mutate the live search path.
  3. Tier 0 governance facts are immune to decay (half-life = 3650 days).

### Boundary 10: Benchmark Suite $\leftrightarrow$ Production Subsystems
- **Upstream Component:** [`scripts/memory_benchmark.py`](file:///workspaces/codespaces-blank/scripts/memory_benchmark.py)
- **Downstream Component:** Live MemSearch / Milvus Vector Database
- **Protocol:** Synthetic Evaluation vs Live Backend Query.
- **Status:** **MOCKED / ARTIFICIAL CONFORMANCE (DEF-004)**
- **Findings:**
  1. In [`scripts/memory_benchmark.py:111-330`](file:///workspaces/codespaces-blank/scripts/memory_benchmark.py#L111-L330), the class `BenchmarkRetriever` implements an in-memory toy TF-IDF character 3-gram cosine similarity model with a static synonym map.
  2. Lines 675, 802, and 824 execute all 30 acceptance matrix assertions (A001-A030) and retrieval metrics against `BenchmarkRetriever`.
  3. The real `MemSearchBackend` and native Milvus vector database were **never executed during benchmark certification**, masking DEF-001 and DEF-002 from detection.

---

## 3. Integration Conformance Matrix

| Boundary ID | Source Subsystem | Target Subsystem | Interface Mechanism | Expected State | Actual State | Severity | Verdict |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **B1.1** | Antigravity CLI | `stop_guard.py` / `stop_hook.py` | JSON over stdio | Execute stop guard per `AGENTS.md` | `hooks.json` points to `stop_hook.py` (DEF-005) | Medium | **INCONSISTENT** |
| **B1.2** | Antigravity CLI | `post_tool_use.py` $\rightarrow$ `candidate_bus.py` | Python import / IPC | Capture mutations & errors into inbox | `post_tool_use.py` does not call `CandidateBus` (DEF-008) | High | **DISCONNECTED** |
| **B1.3** | Antigravity CLI | `pre_invocation.py` $\rightarrow$ `context_compiler.py` | Python import / IPC | Dynamic layered context injection | Injects static 1-line text; no recall (DEF-007) | High | **DISCONNECTED** |
| **B2.1** | `candidate_bus.py` | `candidates.jsonl` | File append with lock | Atomic candidate staging | 12 candidates trapped; un-reconciled (DEF-006) | Medium | **STALLED** |
| **B2.2** | `candidates.jsonl` | `memory_compiler.py` $\rightarrow$ `memory_reconciler.py` | JSONL read $\rightarrow$ reconcile | Automated pipeline | `compile_inbox` has `dry_run=True`, does not call reconciler | High | **DISCONNECTED** |
| **B3.1** | `memory_reconciler.py` | `memory_index_queue.py` | Method call `enqueue()` | Enqueue changed canonical files | Zero references to `index_queue` in reconciler (DEF-009) | High | **DISCONNECTED** |
| **B4.1** | `memory_index_queue.py` | `memsearch_backend.py` | Interface `index()`, `delete()` | Coalesced batch dispatch | Properly implemented with lease lock | Low | **OPERATIONAL** |
| **B5.1** | `memsearch_backend.py` | `memsearch` CLI binary | Subprocess CLI | Search / index vector collections | Defaults to `openai`, crashes without key (DEF-001) | Critical | **BROKEN** |
| **B5.2** | `memsearch` CLI | `memsearch_backend.py:search()` | JSON stdout parse | Structured chunk list | ONNX warning corrupts `json.loads`, silent swallow (DEF-002) | High | **BROKEN** |
| **B6.1** | `query_router.py` | `search_memory.py` | Method call `run_memory_search` | Scope and intent resolution | Successfully routes scopes and classifications | Low | **OPERATIONAL** |
| **B6.2** | `search_memory.py` | `memsearch_backend.py` | Method call `search()` | Dense vector search & RRF fusion | No dense search or RRF in `search_memory.py` (DEF-003) | High | **DISCONNECTED** |
| **B7.1** | `search_memory.py` | `context_compiler.py` | Dataclass translation | Progressive disclosure packaging | Context compiler works, but not wired to live search | Medium | **PARTIAL** |
| **B8.1** | Compaction / Contradiction | Canonical Markdown | File I/O + File Locks | Line budgets & conflict resolution | Operational when run manually | Low | **OPERATIONAL** |
| **B9.1** | `learning_loop.py` | Live Retrieval Path | Shadow file outputs | Isolate shadow weights from live | Strictly isolated; Tier 0 facts immune | Low | **OPERATIONAL** |
| **B10.1** | `memory_benchmark.py` | Production MemSearch / Milvus | Live retrieval assertions | Validate live vector substrate | Uses mock `BenchmarkRetriever` TF-IDF (DEF-004) | High | **MOCKED** |

---

## 4. Root Cause Synthesis of Integration Gaps

The primary root cause of integration failures in the repository is **Component Siloing and Mock Substitution**:
1. Subsystems were developed as self-contained units with internal unit tests.
2. Cross-subsystem glue (hooks $\rightarrow$ candidate bus, reconciler $\rightarrow$ index queue, search engine $\rightarrow$ vector adapter) was left un-wired.
3. Verification suites masked these disconnections by implementing mock replacements (e.g. `BenchmarkRetriever` simulating semantic search) rather than asserting end-to-end execution against the live runtime.
4. Error handling in integration adapters favored silent fallbacks (e.g. falling back to naive word counter on JSON decode error) rather than explicit diagnostic logging, creating an illusion of functionality while the core semantic engine sat completely idle.
