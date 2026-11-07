# MEMORY OPERATIONS GUIDE — Antigravity Memory OS Architecture & Runbook
**Authority:** `instruction.md` Section 121  
**Target Audience:** Autonomous Agents, Pair Programmers, Operations Engineers  
**System Version:** Phase 2 Production (8-Tier Decoupled Architecture)  

---

## 1. Architectural Overview

The Antigravity Memory Operating System is structured into eight decoupled tiers, separating transient conversational context from immutable governance and derived search indices.

```text
[ Agent Turn / Tool Executions ]
             │
             ▼ (PostToolUse Hook: scripts/hooks/post_tool_use.py)
┌────────────────────────────────────────────────────────┐
│ Tier 6: Candidate Experience Bus                       │
│ (.agents/memory/inbox/candidates.jsonl)                │
└────────────────────────────┬───────────────────────────┘
                             │
                             ▼ (MemoryCompiler: scripts/memory_compiler.py)
┌────────────────────────────────────────────────────────┐
│ 5-Gate Admission Compiler Pipeline                     │
│ (Gate 1: Secrets | Gate 2: Durability | Gate 3: Schema │
│  Gate 4: Source Authority | Gate 5: Deduplication)     │
└────────────────────────────┬───────────────────────────┘
                             │
                             ▼ (MemoryReconciler: scripts/memory_reconciler.py)
┌────────────────────────────────────────────────────────┐
│ Tier 3 & Tier 4: Canonical Markdown Storage            │
│ (.agents/memory/{DECISIONS,GOTCHAS,ARCHITECTURE}.md)   │
└────────────────────────────┬───────────────────────────┘
                             │
                             ▼ (IndexQueueManager: scripts/memory_index_queue.py)
┌────────────────────────────────────────────────────────┐
│ Tier 5: Derived Semantic Substrate                     │
│ (~/.memsearch/milvus.db & CPU ONNX bge-m3 embeddings)  │
└────────────────────────────┬───────────────────────────┘
                             │
                             ▼ (Hybrid Search & RRF: scripts/search_memory.py)
┌────────────────────────────────────────────────────────┐
│ Tier 1: Context Compiler & Working Memory              │
│ (.agents/memory/CURRENT.md & L1/L2/L3 Context Packets) │
└────────────────────────────────────────────────────────┘
```

---

## 2. Core Operational Workflows

### 2.1 How Memory is Captured
- **Hook Integration**: The deterministic lifecycle hook `scripts/hooks/post_tool_use.py` intercepts all completed tool executions.
- **Trigger Conditions**:
  - Command failures (exit code $\neq 0$ or error patterns in stderr).
  - High-impact file modifications (`write_to_file` or `replace_file_content` targeting project configuration or canonical documentation).
- **Execution Performance**: Capture logic is strictly guarded to execute in $< 30\text{ms}$ (averages $0.03\text{ms} - 2.5\text{ms}$), ensuring zero latency impact on user interactions.

### 2.2 How Candidates are Created
- **Experience Staging**: Candidate events are written to `.agents/memory/inbox/candidates.jsonl`.
- **Idempotent Hashing**: Every candidate is assigned a deterministic 16-character SHA-256 ID:
  $$\text{ID} = \text{SHA256}(\text{source} : \text{timestamp} : \text{canonical\_content})[:16]$$
- **Noise Filtering**: Routine tool operations (`ls`, `git status`, `echo`, successful `cd`) are filtered out automatically before staging.

### 2.3 How Candidates are Promoted
- **Admission Pipeline (`scripts/memory_compiler.py`)**:
  Candidates pass sequentially through five strict evaluation gates:
  1. **Gate 1 — Secret Hygiene**: Scans for API keys, tokens, and high Shannon entropy ($H > 4.5$).
  2. **Gate 2 — Durability Threshold**: Must score durability $\ge 3.0$ for Tier 3 project storage.
  3. **Gate 3 — Schema Validation**: Enforces Schema v2.0 fields (`source`, `source_authority`, `evidence`, RFC3339 timestamps).
  4. **Gate 4 — Epistemic Confidence**: Evaluates source reliability (`USER_EXPLICIT`: 1.0, `EXECUTED_TEST`: 0.95, `INFERENCE`: 0.4).
  5. **Gate 5 — Deduplication**: Merges exact or near-neighbor semantic duplicates ($\text{cosine similarity} \ge 0.85$).
- **Promotion Command**:
  ```bash
  python3 scripts/memory_compiler.py --drain
  ```
  Evaluated decisions are permanently logged in `.agents/memory/admission_decisions.jsonl`.

### 2.4 How Contradictions are Handled
- **Detection Engine (`scripts/detect_contradictions.py`)**:
  When a new candidate makes an assertion regarding a topic already present in canonical memory, the engine measures semantic divergence and polarity inversion.
- **Supersession Resolution**:
  - If the new claim is backed by higher source authority (e.g. live test evidence superseding old inference) or later verified occurrence time, the old entry is marked:
    `[SUPERSEDED on YYYY-MM-DD by id:XYZ]`
  - If conflicting evidence is ambiguous, the record is flagged `status: "CONTESTED"` rather than silently overwritten.

### 2.5 How Corrections Work
- **Non-Destructive Supersession**: Historical records are never deleted from Markdown files.
- **Temporal Validity Tracking**:
  Old records have their `valid_until` timestamp set to the moment of supersession. 
- **Retrieval Demotion**:
  Active queries filter out records where `valid_until < now`, while historical point-in-time queries (`as_of="YYYY-MM-DD"`) retrieve pre-supersession facts.

### 2.6 How Retrieval Works
- **Dual-Branch Search (`scripts/search_memory.py`)**:
  1. **Dense Vector Branch**: Invokes `MemSearchBackend.search()`, computing embeddings via CPU ONNX `bge-m3` over Milvus Lite.
  2. **Lexical Branch**: Performs exact keyword and BM25 regex matching.
- **Reciprocal Rank Fusion (RRF)**:
  Fuses ranked lists using $k=60$:
  $$RRF(d) = \frac{0.6}{60 + r_{\text{dense}}(d)} + \frac{0.4}{60 + r_{\text{lexical}}(d)}$$
- **Multi-Signal Reranker**: Applies epistemic weights and freshness demotions.
- **Explicit Abstention (`scripts/query_router.py`)**: If top match confidence is $< 0.40$, the system returns `abstained: true` instead of hallucinating.

### 2.7 How Index Health Works
- **Health State Machine**: Tracked in `.agents/memory/index_health.json`.
- **States**: `HEALTHY`, `STALE`, `DEGRADED`, `FAILED`, `REBUILDING`.
- **Diagnostics**: Monitored continuously by `tools/bin/agy-memory-doctor`. Any SQLite lock error or unhandled ONNX crash transitions the status to `DEGRADED` with failure timestamps and tracebacks recorded.

### 2.8 How Rebuild Works
- **Disposability Invariant**: Derived index files can be deleted without risk.
- **Rebuild Command**:
  ```bash
  python3 scripts/memsearch_backend.py --rebuild
  ```
- **Rebuild Sequence**:
  1. Purges existing Milvus Lite collection `memsearch_chunks` in `~/.memsearch/milvus.db`.
  2. Parses all 15 canonical Markdown files across project and global memory tiers.
  3. Re-chunks documents into 500-token paragraphs with sliding overlap.
  4. Generates CPU ONNX `bge-m3` vectors and inserts them into Milvus Lite.
  5. Updates `.agents/memory/.memsearch/manifest.json` and resets index health to `HEALTHY`.

### 2.9 How Recovery Works
- **Write-Ahead Log Queue (`scripts/memory_index_queue.py`)**:
  Indexing jobs are logged to `.agents/memory/index_queue.jsonl` with statuses: `PENDING` $\rightarrow$ `PROCESSING` $\rightarrow$ `DONE` / `FAILED`.
- **Crash Recovery**:
  Jobs acquire a 30-second lease lock (`index_writer.lease.lock`). If an indexing process is abruptly terminated (SIGKILL or power loss), the lease expires. The subsequent invocation reclaims abandoned `PROCESSING` jobs without data corruption.

### 2.10 How to Inspect Provenance
- **Context Envelopes**:
  Every memory packet generated by `scripts/context_compiler.py` includes a structured provenance header:
  ```text
  [MEMORY id="DEC-002" source="AGENTS.md:L94-L98" commit="2a3f81e" confidence="0.95"]
  ```
- **Live Inspection Command**:
  ```bash
  python3 scripts/context_compiler.py --file .agents/memory/DECISIONS.md --level L2
  ```

### 2.11 How to Diagnose Failures
- **Unified Diagnostic CLI**:
  ```bash
  tools/bin/agy-memory-doctor
  ```
- **Diagnostic Dimensions Evaluated**:
  1. *Canonical Integrity*: Unindexed files, line bounds violations ($>30$ lines in `CURRENT.md`), broken markdown links.
  2. *Secret Hygiene*: High-entropy credentials or API keys across all files.
  3. *Coherence*: Unresolved contradictions and duplicate assertions.
  4. *Vector Substrate*: Milvus Lite connection status, ONNX model weights, chunk count synchronization.
  5. *Ingestion Backlog*: Staged candidates count in `inbox/candidates.jsonl`.
  6. *Telemetry Quality*: Rolling NDCG@10 and MRR scores in `retrieval_ledger.jsonl`.
- **Automated Repair Command**:
  ```bash
  tools/bin/agy-memory-doctor --fix
  ```
