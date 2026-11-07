# DEFECT LEDGER
## Antigravity Memory OS — Phase 2 Defect & Non-Conformance Register
**Specification Reference:** [`instruction.md`](file:///workspaces/codespaces-blank/instruction.md) (Section 124)  
**Audit Date:** 2026-09-04  
**Ledger Location:** `/workspaces/codespaces-blank/.agent/memory-audit/audit/DEFECT_LEDGER.md`  
**Total Defects Recorded:** 10 (Critical: 1, High: 4, Medium: 4, Low: 1)  

---

## 1. Defect Summary Register

| Defect ID | Severity | Subsystem / Component | Summary Description | Status |
| :---: | :---: | :--- | :--- | :---: |
| **DEF-001** | **CRITICAL** | MemSearch CLI Substrate (`~/.memsearch/`) | MemSearch CLI defaults to `openai`, causing immediate crash on missing API key. | **IDENTIFIED** |
| **DEF-002** | **HIGH** | Semantic Backend Adapter ([`scripts/memsearch_backend.py`](file:///workspaces/codespaces-blank/scripts/memsearch_backend.py)) | ONNX Runtime warning on `stdout` breaks `json.loads`; silently swallowed with fallback to naive word counter. | **IDENTIFIED** |
| **DEF-003** | **HIGH** | Scoped Search Engine ([`scripts/search_memory.py`](file:///workspaces/codespaces-blank/scripts/search_memory.py)) | Lacks dense semantic retrieval and Reciprocal Rank Fusion (RRF); purely lexical regex. | **IDENTIFIED** |
| **DEF-004** | **HIGH** | Memory Benchmark Suite ([`scripts/memory_benchmark.py`](file:///workspaces/codespaces-blank/scripts/memory_benchmark.py)) | Used in-memory TF-IDF mock `BenchmarkRetriever` instead of live MemSearch / Milvus substrate. | **IDENTIFIED** |
| **DEF-005** | **MEDIUM** | Hook Configuration / Governance ([`.agents/hooks.json`](file:///workspaces/codespaces-blank/.agents/hooks.json)) | `hooks.json` references `stop_hook.py` while `AGENTS.md` references `stop_guard.py`. | **IDENTIFIED** |
| **DEF-006** | **MEDIUM** | Candidate Ingestion Pipeline ([`.agents/memory/inbox/`](file:///workspaces/codespaces-blank/.agents/memory/inbox/)) | Candidate inbox accumulating 12 un-reconciled items with no automated drain mechanism. | **IDENTIFIED** |
| **DEF-007** | **HIGH** | PreInvocation Hook ([`scripts/hooks/pre_invocation.py`](file:///workspaces/codespaces-blank/scripts/hooks/pre_invocation.py)) | Injects static 1-line prompt reminder; fails to invoke `context_compiler.py` or layered recall. | **IDENTIFIED** |
| **DEF-008** | **MEDIUM** | PostToolUse Hook ([`scripts/hooks/post_tool_use.py`](file:///workspaces/codespaces-blank/scripts/hooks/post_tool_use.py)) | Does not invoke `candidate_bus.py` for automated experience capture on mutations/errors. | **IDENTIFIED** |
| **DEF-009** | **MEDIUM** | Memory Reconciler ([`scripts/memory_reconciler.py`](file:///workspaces/codespaces-blank/scripts/memory_reconciler.py)) | Modifies canonical files but fails to enqueue file changes into `memory_index_queue.py`. | **IDENTIFIED** |
| **DEF-010** | **LOW** | Stop Hook Lifecycle Guard ([`scripts/hooks/stop_hook.py`](file:///workspaces/codespaces-blank/scripts/hooks/stop_hook.py)) | Empty pass-through returns `{"decision": "stop"}` without running reconciliation or compaction. | **IDENTIFIED** |

---

## 2. Detailed Defect Records

```yaml
id: DEF-001
severity: CRITICAL
component: MemSearch CLI Configuration (~/.memsearch/)
symptom: |
  Invoking `memsearch search` or `memsearch index` without an explicit `--provider onnx` flag
  crashes immediately with `openai.OpenAIError: Missing credentials`.
root_cause: |
  MemSearch CLI resolves its embedding provider configuration to `openai` by default when no
  `~/.memsearch/config.toml` exists or when `embedding.provider` is not explicitly set.
  Because no OpenAI credentials exist in the environment, `openai.AsyncOpenAI()` raises
  an unhandled `OpenAIError`, halting process execution with exit code 1.
evidence: |
  Command executed:
    $ memsearch config get embedding.provider
  Output:
    openai

  Command executed:
    $ memsearch search "test" --json-output
  Traceback:
    File ".../site-packages/memsearch/cli.py", line 366, in search
      ms = MemSearch(**_cfg_to_memsearch_kwargs(cfg))
    File ".../site-packages/memsearch/embeddings/openai.py", line 41, in __init__
      self._client = openai.AsyncOpenAI(**kwargs)
    File ".../site-packages/openai/_client.py", line 1011, in __init__
      raise OpenAIError("Missing credentials. Please pass an `api_key`...")
    openai.OpenAIError: Missing credentials.
repair: |
  1. Execute `memsearch config set embedding.provider onnx` to permanently write `provider = "onnx"`
     to `~/.memsearch/config.toml`.
  2. Ensure `scripts/memsearch_backend.py` explicitly injects `--provider onnx` on all CLI invocations
     as a defense-in-depth guarantee.
regression_test: |
  $ memsearch search "test" --json-output
  Verify exit code is 0 and output contains valid JSON chunks without requiring OPENAI_API_KEY.
status: IDENTIFIED
```

```yaml
id: DEF-002
severity: HIGH
component: MemSearch Backend Adapter (scripts/memsearch_backend.py)
symptom: |
  Semantic search through `MemSearchBackend.search()` silently fails to execute vector retrieval
  and falls back to a naive word count search (`matches = sum(text.count(t) for t in query_terms)`),
  rendering dense semantic retrieval non-functional across the entire system.
root_cause: |
  When the `memsearch` CLI executes using the local ONNX provider, the underlying `onnxruntime`
  library prints a hardware device discovery warning to `stdout` before emitting the JSON array:
    2026-09-04 07:16:42.972426979 [W:onnxruntime:Default, device_discovery.cc:146 GetPciBusId] Skipping pci_bus_id for PCI path ...
    [
      { "chunk_hash": "...", ... }
    ]
  In `scripts/memsearch_backend.py:177`, `json.loads(res.stdout)` attempts to parse the complete
  stdout string. This raises `json.JSONDecodeError` due to the warning prefix.
  Lines 178-179 swallow the exception with `except json.JSONDecodeError: pass`, causing execution
  to fall through to line 184 ("Fallback keyword match against indexed files in manifest").
evidence: |
  Direct invocation of CLI command shows stdout pollution:
    $ memsearch search "test" --provider onnx --json-output
    2026-09-04 07:16:42.972426979 [W:onnxruntime:Default, device_discovery.cc:146 GetPciBusId] Skipping pci_bus_id for PCI path at "/sys/devices/LNXSYSTM:00/LNXSYBUS:00/PNP0A03:00/device:07/VMBUS:01/5620e0c7-8062-4dce-aeb7-520c7ef76171" because filename "5620e0c7-8062-4dce-aeb7-520c7ef76171" did not match expected pattern of [0-9a-f]+:[0-9a-f]+:[0-9a-f]+[.][0-9a-f]+
    [
      {
        "chunk_hash": "4c7a8cd165bbb9cc",
        "content": "Testing locking",
        ...
      }
    ]

  Code inspection of scripts/memsearch_backend.py lines 175-184:
    if res.returncode == 0 and res.stdout.strip():
        try:
            return json.loads(res.stdout)
        except json.JSONDecodeError:
            pass
    # Fallback keyword match against indexed files in manifest
    query_terms = query.lower().split()
repair: |
  In `scripts/memsearch_backend.py:search()`:
  1. Extract the JSON substring by slicing from the first `[` to the last `]` in `res.stdout`.
  2. Set environment variable `ORT_LOGGING_LEVEL=3` during subprocess execution to suppress ONNX warnings.
  3. Log an explicit error instead of silently passing when parsing truly invalid JSON.
regression_test: |
  python3 -c "from scripts.memsearch_backend import MemSearchBackend; b = MemSearchBackend(); res = b.search('test'); assert len(res) > 0 and 'chunk_hash' in res[0]"
status: IDENTIFIED
```

```yaml
id: DEF-003
severity: HIGH
component: Scoped Search Engine (scripts/search_memory.py)
symptom: |
  The production search entrypoint `scripts/search_memory.py` is unable to perform dense semantic
  search or hybrid Reciprocal Rank Fusion (RRF). Paraphrased queries without verbatim keywords
  return zero matching results.
root_cause: |
  `scripts/search_memory.py` was implemented solely as a lexical scanner (`extract_section_snippets()`)
  using regular expressions and string splitting. It does not import `memsearch_backend.py`, does not
  query the vector substrate, and does not implement the hybrid RRF formula (`score = 1 / (60 + rank)`)
  mandated by Instruction.md Sections 10, 23, and 79.
evidence: |
  Grep search for semantic / vector / rrf references in `scripts/search_memory.py` returns 0 hits:
    $ grep -i "memsearch" scripts/search_memory.py -> (0 matches)
    $ grep -i "rrf" scripts/search_memory.py -> (0 matches)
    $ grep -i "embedding" scripts/search_memory.py -> (0 matches)
  Paraphrased query test:
    $ python3 scripts/search_memory.py "how do we stop accidental credential leaks and token exposure in files?"
    Output: No memory entries found matching query.
repair: |
  Refactor `scripts/search_memory.py` to:
  1. Import `MemSearchBackend` from `scripts.memsearch_backend`.
  2. Execute parallel/sequential dense vector search and lexical regex search.
  3. Combine ranks using Reciprocal Rank Fusion ($w_{dense} \cdot \frac{1}{60 + r_{dense}} + w_{lex} \cdot \frac{1}{60 + r_{lex}}$).
  4. Apply metadata reranking multipliers (`m_auth`, `m_fresh`, `m_scope`) and filter superseded entries.
regression_test: |
  python3 scripts/search_memory.py "how do we stop accidental credential leaks and token exposure in files?" --json
  Verify that `mem-002` (Zero Secrets Policy) is returned as Rank 1 with valid RRF score.
status: IDENTIFIED
```

```yaml
id: DEF-004
severity: HIGH
component: Memory Benchmark Suite (scripts/memory_benchmark.py)
symptom: |
  The benchmark test matrix (A001-A030) and retrieval metrics report 100% pass rates, but the tests
  were never run against the live MemSearch / Milvus substrate, masking critical vector failures (DEF-001, DEF-002).
root_cause: |
  In `scripts/memory_benchmark.py`, lines 111-330 define an in-memory class `BenchmarkRetriever`
  which approximates semantic retrieval via a hardcoded Python dictionary of synonyms and character
  3-gram cosine overlap.
  In lines 675, 802-803, and 823-824, the acceptance test runner binds:
    self.retriever = BenchmarkRetriever(self.corpus)
  This mock retriever was used for all assertions, leaving the real `MemSearchBackend` unverified.
evidence: |
  Inspection of `scripts/memory_benchmark.py`:
    Line 674: self.corpus = get_canonical_benchmark_corpus()
    Line 675: self.retriever = BenchmarkRetriever(self.corpus)
    Line 802: lex_results = [d.get("memory_id") for d, s in self.retriever.search_lexical(query, top_k=3)]
    Line 803: sem_results = [d.get("memory_id") for d, s in self.retriever.search_semantic(query, top_k=3)]
    Line 824: hyb_metrics = compute_retrieval_metrics(self.retriever, queries, mode="hybrid_reranked")
repair: |
  1. Modify `scripts/memory_benchmark.py` to index the canonical benchmark corpus into live MemSearch / Milvus.
  2. Instantiate `MemSearchBackend` and query the real substrate for semantic lane assertions.
  3. Keep `BenchmarkRetriever` strictly as a fallback baseline reference for comparative metric tests.
regression_test: |
  python3 scripts/memory_benchmark.py --live-substrate
  Verify all 30 assertions pass against live Milvus Lite index at `~/.memsearch/milvus.db`.
status: IDENTIFIED
```

```yaml
id: DEF-005
severity: MEDIUM
component: Hook Configuration & Governance (.agents/hooks.json vs AGENTS.md)
symptom: |
  Configuration divergence between governance documentation and runtime hook definitions:
  `AGENTS.md` mandates `scripts/hooks/stop_guard.py` for the Stop event, but `.agents/hooks.json`
  configures `scripts/hooks/stop_hook.py`.
root_cause: |
  During an earlier refactoring of hook handlers, `stop_hook.py` was created without updating
  the authoritative policy document `AGENTS.md`, leaving redundant files with duplicate logic.
evidence: |
  `.agents/hooks.json:38`:
    "command": "python3 /workspaces/codespaces-blank/scripts/hooks/stop_hook.py"

  `AGENTS.md:150`:
    4. **`Stop` (`scripts/hooks/stop_guard.py`)**: Session guard verifying idle state and background tasks.
repair: |
  Standardize on a single canonical filename (`scripts/hooks/stop_hook.py`), update `AGENTS.md` to reference
  `scripts/hooks/stop_hook.py`, and remove or redirect the duplicate `scripts/hooks/stop_guard.py`.
regression_test: |
  python3 scripts/validate_memory.py
  Verify exit code is 0 and hook paths match documentation.
status: IDENTIFIED
```

```yaml
id: DEF-006
severity: MEDIUM
component: Candidate Ingestion Pipeline (.agents/memory/inbox/candidates.jsonl)
symptom: |
  12 candidate memory records have accumulated in `.agents/memory/inbox/candidates.jsonl`
  without being processed, evaluated, or reconciled into canonical memory files.
root_cause: |
  Candidates are staged into `candidates.jsonl` by `CandidateBus`, but no automated lifecycle trigger
  (such as a stop hook, maintenance cron, or session close event) invokes `MemoryCompiler.compile_inbox()`
  and `MemoryReconciler.reconcile()`. Staged items sit in the inbox indefinitely.
evidence: |
  Inspection of `/workspaces/codespaces-blank/.agents/memory/inbox/candidates.jsonl`:
    Line 1:  cand_dec_001 (ninja-build and CMake adoption)
    Line 2:  cand_gotcha_002 (Gradle daemon OOM gotcha)
    Line 3:  cand_proj_003 (persistence layer)
    Line 4:  cand_proc_004 (multi-phase test execution order)
    Line 5:  cand_tool_005 (TShark offline inspection)
    Line 6:  cand_global_unverified_006 (speculative Python 3.14 assertion)
    Line 7:  cand_proj_missing_prov_007 (Bazel migration)
    Line 8:  cand_session_008 (active task session log)
    Line 9:  cand_ephemeral_009 (routine terminal output)
    Line 10: cand_redundant_010 (redundant persistence layer fact)
    Line 11: c1a08f1f... (pytest execution tool event)
    Line 12: 145497a0... (ls execution tool event)
repair: |
  1. Author a dedicated drain command `scripts/drain_candidates.py` (or integrate into `memory_compiler.py`).
  2. Execute compiler admission gating (`decide_admission()`), write decisions to `admission_decisions.jsonl`.
  3. Reconcile accepted candidates into canonical Markdown files (`DECISIONS.md`, `GOTCHAS.md`, etc.).
  4. Truncate or archive processed records from `candidates.jsonl`.
regression_test: |
  python3 scripts/memory_compiler.py --drain
  Verify that `candidates.jsonl` contains 0 pending items and canonical files receive accepted entries.
status: IDENTIFIED
```

```yaml
id: DEF-007
severity: HIGH
component: PreInvocation Hook (scripts/hooks/pre_invocation.py)
symptom: |
  The PreInvocation hook provides zero dynamic memory recall during agent conversation turns.
  It injects only a static hardcoded string ("Antigravity Memory Directive: Memory is advisory...").
root_cause: |
  `scripts/hooks/pre_invocation.py` checks for the substring "Current Objective" in `CURRENT.md`
  and emits a single static prompt message. It does not inspect the current turn prompt, does not
  call `query_router.py`, and does not invoke `context_compiler.py` to compile relevant memories.
evidence: |
  Inspection of `scripts/hooks/pre_invocation.py` lines 34-40:
    if "Current Objective" in content:
        inject_steps.append({
            "ephemeralMessage": "Antigravity Memory Directive: Memory is advisory. Inspect .agents/memory/INDEX.md and load only relevant context."
        })
repair: |
  Update `scripts/hooks/pre_invocation.py` to:
  1. Extract incoming prompt or turn objective from hook payload.
  2. Call `QueryRouter` to resolve target scopes and determine if recall is required.
  3. Invoke `ContextCompiler` under a strict token budget (<300 tokens, <50ms execution timeout)
     to inject compact progressive disclosure context (L1 preview).
regression_test: |
  echo '{"user_prompt": "What was the Gradle memory issue?"}' | python3 scripts/hooks/pre_invocation.py
  Verify returned `injectSteps` contains dynamic compiled context for Gradle daemon OOM.
status: IDENTIFIED
```

```yaml
id: DEF-008
severity: MEDIUM
component: PostToolUse Hook (scripts/hooks/post_tool_use.py)
symptom: |
  The PostToolUse hook never captures runtime execution experience into the candidate inbox.
  Command failures, compiler errors, and architectural edits drop without observation.
root_cause: |
  `scripts/hooks/post_tool_use.py` only implements JSON syntax checks on modified `.json` files.
  It never imports `CandidateBus` or calls `capture_tool_event()`.
evidence: |
  Inspection of `scripts/hooks/post_tool_use.py`:
    Line 28: if tool_name in ["write_to_file", "replace_file_content"]:
    Line 32:     if target_file.endswith(".json"): ...
    Line 39: print(json.dumps({}))
  Zero calls to `candidate_bus`.
repair: |
  In `scripts/hooks/post_tool_use.py`:
  1. Import `CandidateBus`.
  2. For `run_command` failures (exit_code != 0) or significant file writes, invoke
     `CandidateBus.capture_tool_event()`.
  3. Ensure execution completes in under 30ms so as not to degrade CLI latency.
regression_test: |
  echo '{"toolCall": {"name": "run_command", "args": {"CommandLine": "ninja -C build"}}, "error": "build failed", "exitCode": 1}' | python3 scripts/hooks/post_tool_use.py
  Verify a new candidate appears in `.agents/memory/inbox/candidates.jsonl`.
status: IDENTIFIED
```

```yaml
id: DEF-009
severity: MEDIUM
component: Memory Reconciler (scripts/memory_reconciler.py)
symptom: |
  When the reconciler modifies canonical memory files (`DECISIONS.md`, `GOTCHAS.md`), it fails
  to notify the index control plane. The semantic index becomes stale relative to canonical Markdown.
root_cause: |
  `scripts/memory_reconciler.py` uses `lock_manager.atomic_write()` to persist changes to disk,
  but does not import `IndexQueueManager` or call `IndexQueueManager.enqueue()`.
evidence: |
  Grep for `IndexQueueManager` or `enqueue` in `scripts/memory_reconciler.py` yields 0 matches.
repair: |
  In `scripts/memory_reconciler.py`:
  1. Import `IndexQueueManager` from `scripts.memory_index_queue`.
  2. In `_apply_add()`, `_apply_supersede()`, and `_apply_update()`, call `IndexQueueManager().enqueue(target_file)`.
regression_test: |
  Reconcile a test candidate and verify that an `upsert` job appears in `.agents/memory/index_queue.jsonl`.
status: IDENTIFIED
```

```yaml
id: DEF-010
severity: LOW
component: Stop Hook Lifecycle Guard (scripts/hooks/stop_hook.py)
symptom: |
  Session termination never triggers memory compaction, candidate reconciliation, or index synchronization.
root_cause: |
  `scripts/hooks/stop_hook.py` is an empty pass-through that returns `{"decision": "stop"}` regardless
  of pending un-reconciled candidate items or dirty memory files.
evidence: |
  Inspection of `scripts/hooks/stop_hook.py` lines 21-27:
    fully_idle = payload.get("fullyIdle", True) ...
    print(json.dumps({"decision": "stop"}))
repair: |
  Enhance `scripts/hooks/stop_hook.py` to:
  1. Trigger lightweight candidate drain and index queue flush when `fullyIdle` is True.
  2. Return `{"decision": "stop"}` after triggering background maintenance.
regression_test: |
  echo '{"fullyIdle": true}' | python3 scripts/hooks/stop_hook.py
  Verify maintenance triggers cleanly without blocking shutdown.
status: IDENTIFIED
```

---

## 3. Prioritized Remediation Plan (Stage 3 Roadmap)

```
Priority 1 (Critical Substrate Repairs):
  - DEF-001: Set MemSearch CLI provider to ONNX (`memsearch config set embedding.provider onnx`).
  - DEF-002: Patch `scripts/memsearch_backend.py` to extract JSON from ONNX warning stdout.

Priority 2 (Core Read Path Repairs):
  - DEF-003: Wire dense semantic search and Reciprocal Rank Fusion into `scripts/search_memory.py`.
  - DEF-004: Rewire `scripts/memory_benchmark.py` to assert against live MemSearch substrate.
  - DEF-007: Wire `scripts/hooks/pre_invocation.py` to dynamic layered context compilation.

Priority 3 (Write & Lifecycle Pipeline Repairs):
  - DEF-006: Drain 12 accumulated candidates from `.agents/memory/inbox/candidates.jsonl`.
  - DEF-008: Wire `scripts/hooks/post_tool_use.py` to `CandidateBus.capture_tool_event()`.
  - DEF-009: Wire `scripts/memory_reconciler.py` to `IndexQueueManager.enqueue()`.
  - DEF-005: Align `hooks.json` and `AGENTS.md` on canonical hook filename (`stop_hook.py`).
  - DEF-010: Wire session close in `scripts/hooks/stop_hook.py` to trigger background maintenance.
```
