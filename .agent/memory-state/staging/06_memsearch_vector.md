# FORENSIC STATE EXTRACTION: MEMSEARCH & VECTOR SUBSTRATE
**System:** Antigravity Memory Operating System (Phase 1–16)  
**Agent:** Agent 6 — MemSearch & Vector Substrate Engineer  
**Execution Timestamp:** 2026-09-04T19:20:00Z  
**Target Repository:** `/workspaces/codespaces-blank`  
**Status:** Canonical Read-Only Forensic Extraction Complete  
**Governing Specifications:** `instruction.md` (Sections 30, 31, 32, 33, 34, 35) & `AGENTS.md` (Squad 2 & Squad 4)

---

## 1. EXECUTIVE CONTRACT & SCOPE OWNERSHIP

This document constitutes the authoritative forensic architecture and runtime extraction for the **MemSearch Semantic Retrieval Substrate, Vector Database, Index Architecture, Health State Machine, and Single-Writer Queue Mechanics** of the Antigravity Memory Operating System.

In strict compliance with **Section 1 (Executive Contract)** and **Section 3 (No-Change Policy)** of `instruction.md`:
1. This snapshot reflects **empirically observed runtime state** and live code reality, not speculative designs or unverified claims.
2. Under the **No-Change Policy**, existing indexes, queues, canonical memory, and health records were **NOT repaired, re-indexed, or mutated** during extraction (`--fix` was strictly withheld). Discrepancies and stale states are fully exposed as live evidence.
3. Every claim is supported by executed commands, file system inspection, configuration resolution, or raw evidence logs.

### Owned Specification Sections
- **Section 30**: MemSearch Complete Integration Record
- **Section 31**: MemSearch Live Probes
- **Section 32**: Index Architecture
- **Section 33**: Index Health
- **Section 34**: Index Consistency Probe
- **Section 35**: Indexing / Queue Mechanics

### Forensic Evidence Hierarchy
```text
1. EXECUTED RUNTIME OBSERVATION (Live CLI commands, probe logs, process locks)
2. ACTUAL SOURCE CODE (scripts/memsearch_backend.py, scripts/memory_index_queue.py)
3. ACTUAL EFFECTIVE CONFIGURATION (~/.memsearch/config.toml, schema.json)
4. GENERATED / DERIVED ARTIFACTS (.agents/memory/.memsearch/manifest.json, index_health.json)
5. EXECUTED TEST RESULTS (Live stats and search evidence files)
6. REPOSITORY DOCUMENTATION (docs/architecture.md, AGENTS.md)
7. COMMENTS / AGENT CLAIMS (Treated as advisory hypotheses until verified)
```

---

## 2. SECTION 30: MEMSEARCH COMPLETE INTEGRATION RECORD

### 2.1 Runtime Environment & Package Provenance
- **MemSearch Version**: `0.4.19` (Verified via `/home/codespace/.local/bin/memsearch --version`).
- **Installation Method**: Python virtual environment isolation (`.venv-memsearch`) with user-local symlink.
- **Package Manager**: Wheel / pip within virtualenv.
- **Binary Path**: `/home/codespace/.local/bin/memsearch` (symlink pointing to `/workspaces/codespaces-blank/.venv-memsearch/bin/memsearch`).
- **Dedicated Python Runtime**: `/workspaces/codespaces-blank/.venv-memsearch/bin/python3` -> `/home/codespace/.python/current/bin/python` (Python 3.12.1).
- **Core Dependencies (Site-Packages Inventory)**:
  - `memsearch`: 0.4.19 (`memsearch-0.4.19.dist-info`)
  - `milvus_lite`: 3.2.1 (`milvus_lite-3.2.1.dist-info`)
  - `pymilvus`: 3.0.1 (`pymilvus-3.0.1.dist-info`)
  - `onnxruntime`: 1.29.0 (`onnxruntime-1.29.0.dist-info`)
  - `tokenizers`: 0.23.2 (`tokenizers-0.23.2.dist-info`)
  - `huggingface_hub`: 1.30.0 (`huggingface_hub-1.30.0.dist-info`)
  - `numpy`: 2.5.2 (`numpy-2.5.2.dist-info`)
  - `pydantic`: 2.13.5 (`pydantic-2.13.5.dist-info`)
  - `click`: 8.5.0 (`click-8.5.0.dist-info`)
  - `tomli_w`: 1.2.0 (`tomli_w-1.2.0.dist-info`)

### 2.2 Effective Configuration & Defaults
The primary configuration file is located at `~/.memsearch/config.toml`. Inspection via `memsearch.config.resolve_config()` confirms the following resolved runtime settings:

```toml
[milvus]
uri = "~/.memsearch/milvus.db"
token = ""
collection = "memsearch_chunks"

[embedding]
provider = "onnx"
model = "bge-m3"
batch_size = 0
base_url = ""
api_key = ""

[chunking]
max_chunk_size = 1500
overlap_lines = 2

[indexing]
ignore_files = []
exclude = []

[watch]
debounce_ms = 1500
```

- **Embedding Provider**: `onnx` (CPU local ONNX Runtime inference, no external API keys required).
- **Embedding Model**: `bge-m3` (BAAI BGE-M3 multilingual foundation embedding).
- **Embedding Dimension**: `1024` dimensions (dense float vector).
- **Chunk Size**: `1500` characters maximum.
- **Chunk Overlap**: `2` overlapping lines between adjacent chunks.
- **Ignore Rules**: Queue-level exclusion for `.memsearch/`, `inbox/`, `sessions/`, and hidden files.
- **Vector Backend**: `Milvus Lite` (embedded SQLite/file-backed gRPC storage engine).
- **Connection URI**: `~/.memsearch/milvus.db` (zero secrets, local disk storage).
- **Target Collection**: `memsearch_chunks`.

### 2.3 CLI Command Surface
Verified via `memsearch --help`:
- `memsearch index <PATHS>`: Indexes markdown files from target paths.
- `memsearch search <QUERY>`: Performs hybrid dense + sparse BM25 retrieval for query.
- `memsearch stats`: Reports collection entity statistics and chunk counts.
- `memsearch expand <CHUNK_ID>`: Expands chunk hash to display enclosing context.
- `memsearch reset`: Wipes collection and resets vector database.
- `memsearch watch <PATHS>`: Auto-indexes on markdown file modifications (1500ms debounce).
- `memsearch compact`: Compresses stored memories into summaries.
- `memsearch transcript <SESSION_ID>`: Displays original conversation turns and tool calls.
- `memsearch skills`: Distills and inspects candidate skills.

### 2.4 Integration Boundaries & Layer Responsibilities
1. **Integration Boundary (`scripts/memsearch_backend.py`)**:
   - Implements the `SemanticRetrievalBackend` abstract interface per Section 21 & 35.
   - Decouples all repository retrieval code from Milvus Lite / ONNX library details.
   - Provides methods: `index()`, `delete()`, `search()`, `expand()`, `health()`, `rebuild()`.
   - Before re-indexing any file, executes `_purge_entities(abs_path)` calling `store.delete_by_source(abs_path)` to prevent orphaned chunk duplication.
   - Manages derived manifest tracking in `.agents/memory/.memsearch/manifest.json`.

2. **Source-of-Truth Boundary**:
   - **Canonical Memory (Authoritative)**: All human and agent durable knowledge resides exclusively in canonical Markdown files (`.agents/memory/{DECISIONS,GOTCHAS,ARCHITECTURE,PROCEDURES,INDEX,CURRENT}.md` and global `~/.gemini/antigravity-cli/memory/*.md`).
   - **Vector Database (100% Derived / Ephemeral)**: Milvus Lite (`~/.memsearch/milvus.db`) and `.agents/memory/.memsearch/manifest.json` are strictly ephemeral caches. If deleted, destroyed, or corrupted, zero knowledge is lost. The entire vector database is recreatable on demand from markdown files.

3. **Failure Boundary & Graceful Degradation**:
   - Milvus Lite uses an exclusive OS file flock (`~/.memsearch/milvus.db/LOCK`).
   - If Milvus Lite is locked by another process, missing, or fails with a runtime exception, `scripts/memsearch_backend.py` intercepts the error, flags backend health as `DEGRADED`, and executes a graceful fallback:
     - Executes local keyword / regex substring scoring over all canonical markdown files tracked in manifest.
     - Upper-level pipelines (`scripts/search_memory.py`, `scripts/context_compiler.py`) continue operating seamlessly without raising unhandled crashes.

4. **Version / Migration Boundary**:
   - Recorded in `.agents/memory/index_health.json` under `embedding_model`, `embedding_provider`, `embedding_dimension`, and `migration_state`.
   - If the embedding model or dimension changes (e.g., from `bge-m3` 1024-dim to an alternative model), `verify_index_integrity()` detects the mismatch and flags `migration_state: "MIGRATION_REQUIRED"`.
   - Existing vectors cannot be cross-matched across embedding spaces; a complete vector rebuild is enforced.

---

## 3. SECTION 31: MEMSEARCH LIVE PROBES

Live probes were executed against the installed CLI and underlying Milvus Lite vector database. Raw outputs were captured into durable evidence files under `.agent/memory-state/evidence/`.

### 3.1 Live Probe 1: Collection Statistics (`memsearch stats`)
- **Command**: `/home/codespace/.local/bin/memsearch stats`
- **Exit Code**: `0`
- **Raw Output Location**: `/workspaces/codespaces-blank/.agent/memory-state/evidence/memsearch-stats.txt`
- **Output Content**:
  ```text
  Total indexed chunks: 264
  ```
- **Forensic Finding**: The Milvus Lite collection `memsearch_chunks` contains exactly **264 indexed chunks** across project and global memory tiers.

### 3.2 Live Probe 2: Semantic Retrieval (`memsearch search "architecture"`)
- **Command**: `/home/codespace/.local/bin/memsearch search "architecture"`
- **Exit Code**: `0`
- **Raw Output Location**: `/workspaces/codespaces-blank/.agent/memory-state/evidence/memsearch-search.txt`
- **Execution Output**:
  ```text
  --- Result 1 (score: 0.9919) ---
  Source: /workspaces/codespaces-blank/.agents/memory/ARCHITECTURE.md
  Heading: Project System Architecture
  # Project System Architecture
  Last Updated: 2026-09-01

  --- Result 2 (score: 0.9692) ---
  Source: /home/codespace/.gemini/antigravity-cli/memory/README.md
  Heading: 1. Architecture Overview
  ## 1. Architecture Overview
  The Antigravity Persistent Memory System is an AI-first, hierarchical memory engine engineered for the Antigravity CLI (`agy`). It preserves high-value durable knowledge, architectural decisions, and runtime gotchas across sessions while strictly preventing memory bloat, context pollution, cross-project contamination, and secret leakage.

  --- Result 3 (score: 0.9685) ---
  Source: /workspaces/codespaces-blank/.agents/memory/DECISIONS.md
  Heading: 2026-09-01 — ADR-001: 5-Tier Memory Architecture
  ## 2026-09-01 — ADR-001: 5-Tier Memory Architecture
  **Type:** DECISION **Scope:** PROJECT **Confidence:** VERIFIED **Source:** docs/instruction.md **Status:** ACTIVE

  --- Result 4 (score: 0.4841) ---
  Source: /workspaces/codespaces-blank/.agents/memory/sessions/2026-09-02-1430.md
  Heading: 3. Architectural Decisions
  ## 3. Architectural Decisions
  - Verified toolchain parity across sessions.

  --- Result 5 (score: 0.4841) ---
  Source: /home/codespace/.gemini/antigravity-cli/memory/README.md
  Heading: Project Memory (Workspace-Level)
  ### Project Memory (Workspace-Level)
  ```
  <project-root>/.agents/memory
  ├── ARCHITECTURE.md
  ├── CURRENT.md
  ├── DECISIONS.md
  ├── GOTCHAS.md
  ├── INDEX.md
  └── sessions/
      └── 2026-09-01-1546.md
  ```
  ```
- **Forensic Finding**: Semantic search returns highly relevant, ranked results with exact confidence scores. `ARCHITECTURE.md` is scored highest (`0.9919`), followed closely by global `README.md` (`0.9692`) and project `DECISIONS.md` (`0.9685`).

### 3.3 Live Probe 3: Milvus Lite Locking & Concurrency Boundary Probe
During live probing, concurrent test execution by background processes exposed the underlying concurrency contract of Milvus Lite:
- **Observed Exception**:
  ```text
  milvus_lite.exceptions.DataDirLockedError: another process holds the lock on '/home/codespace/.memsearch/milvus.db': [Errno 11] Resource temporarily unavailable
  RuntimeError: Could not open the local Milvus database at /home/codespace/.memsearch/milvus.db: <ConnectionConfigException: (code=1, message=Open local milvus failed)>.
  ```
- **Forensic Verification**: Milvus Lite is strictly single-process and cannot support concurrent writers or overlapping reader-writer sessions on the same database directory. This empirical evidence proves why the Antigravity Memory OS requires a **single-writer lease lock** (`scripts/lock_manager.py` on `index_writer.lease.lock`) and queue coalescing before invoking MemSearch commands.

---

## 4. SECTION 32: INDEX ARCHITECTURE

### 4.1 Canonical Revision vs. Indexed Revision
To detect drift between markdown truth and vector index state without scanning all vector embeddings, the system maintains dual revisions:
- **Canonical Revision (`canonical_revision`)**:
  - Computed dynamically by `IndexQueueManager.compute_canonical_revision()`.
  - Calculates a composite SHA-256 hash over relative paths, modification timestamps (`mtime`), and file sizes (`size_bytes`) of all `.md` files in `.agents/memory/` (excluding `.memsearch/` and `inbox/`).
  - Formatted as a 16-character hexadecimal digest (e.g., `6512fc8ee7af43cb`).
- **Indexed Revision (`indexed_revision`)**:
  - Stored in `.agents/memory/index_health.json`.
  - Updated to match `canonical_revision` ONLY when an index rebuild or queue drain completes with zero errors and zero remaining pending jobs.
  - When `canonical_revision != indexed_revision`, the index is deterministically diagnosed as `STALE`.

### 4.2 Chunk Identity Hashing
- **Chunk Hash Formula**: Each chunk in Milvus Lite is uniquely identified by `chunk_hash`, a 64-character hexadecimal SHA-256 hash calculated over the chunk content combined with its structural path and line boundaries.
- **Manifest Tracking**: `.agents/memory/.memsearch/manifest.json` tracks source file integrity via full-file SHA-256 hashes (`content_hash`), file size, and indexing timestamp (`indexed_at`).

### 4.3 Milvus Lite Storage Schema
Verified directly from `/home/codespace/.memsearch/milvus.db/collections/memsearch_chunks/schema.json`:
```json
{
  "collection_name": "memsearch_chunks",
  "enable_dynamic_field": true,
  "fields": [
    {
      "name": "chunk_hash",
      "dtype": "varchar",
      "max_length": 64,
      "is_primary": true,
      "auto_id": false,
      "nullable": false
    },
    {
      "name": "embedding",
      "dtype": "float_vector",
      "dim": 1024,
      "is_primary": false,
      "nullable": false
    },
    {
      "name": "content",
      "dtype": "varchar",
      "max_length": 65535,
      "enable_analyzer": true,
      "is_primary": false,
      "nullable": false
    },
    {
      "name": "sparse_vector",
      "dtype": "sparse_float_vector",
      "is_function_output": true,
      "is_primary": false,
      "nullable": false
    },
    {
      "name": "source",
      "dtype": "varchar",
      "max_length": 1024,
      "is_primary": false,
      "nullable": false
    },
    {
      "name": "heading",
      "dtype": "varchar",
      "max_length": 1024,
      "is_primary": false,
      "nullable": false
    },
    {
      "name": "heading_level",
      "dtype": "int64",
      "is_primary": false,
      "nullable": false
    },
    {
      "name": "start_line",
      "dtype": "int64",
      "is_primary": false,
      "nullable": false
    },
    {
      "name": "end_line",
      "dtype": "int64",
      "is_primary": false,
      "nullable": false
    }
  ],
  "functions": [
    {
      "name": "bm25_fn",
      "function_type": 1,
      "input_field_names": ["content"],
      "output_field_names": ["sparse_vector"],
      "params": {}
    }
  ],
  "schema_format_version": 2,
  "version": 1
}
```

### 4.4 Authoritative Classification
- **Classification**: **`derived/rebuildable`**.
- The vector database is strictly a derived acceleration structure.
- Full index rebuild is non-destructive to source memory.

---

## 5. SECTION 33: INDEX HEALTH STATE MACHINE

The system health model is defined in `scripts/memory_index_queue.py` under `IndexHealthState`:

```text
┌─────────────────────────────────────────────────────────────┐
│                    INDEX HEALTH STATES                      │
├──────────────┬──────────────────────────────────────────────┤
│ HEALTHY      │ All canonical memory indexed; hashes match   │
│ STALE        │ Canonical files edited; queue jobs pending   │
│ DEGRADED     │ Indexing errors occurred / DLQ active        │
│ REBUILDING   │ Complete index regeneration in progress      │
│ FAILED       │ Manifest corrupt / database unrecoverable    │
│ MISSING      │ No health record or collections found        │
└──────────────┴──────────────────────────────────────────────┘
```

### 5.1 State Specifications
| Health State | Trigger | Detection Mechanism | User-Visible Behavior | Recovery Procedure |
| :--- | :--- | :--- | :--- | :--- |
| **`HEALTHY`** | Canonical revision equals indexed revision; 0 pending jobs; 0 failed jobs. | `check_and_refresh_health()` | Fast hybrid semantic retrieval with full confidence. | Normal operation. |
| **`STALE`** | Markdown files modified on disk without re-index; new jobs enqueued; `canonical_revision != indexed_revision`. | `compute_canonical_revision() != indexed_revision` or `detect_dirty_canonical_files()`. | Retrieval functions normally but warning emitted; recent edits may only appear via lexical search. | Run `memory_index_queue.py --drain` or allow hook auto-drain. |
| **`DEGRADED`** | Job failure after 3 retries; entries in Dead-Letter Queue; MemSearch CLI / Milvus runtime failure. | `failed_sources > 0` or `backend.health()["status"] == "DEGRADED"`. | Advisory warning displayed; system falls back to regex/lexical search for failed sources. | Inspect DLQ via `--list-dlq`, fix malformed file, run `--requeue-dlq` and `--drain`. |
| **`REBUILDING`** | Full or targeted rebuild initiated. | Active lease lock during `rebuild()`; health state explicitly set to `REBUILDING`. | Retrieval temporarily falls back to lexical regex scanner. | Completes automatically; transitions to `HEALTHY` or `DEGRADED`. |
| **`FAILED`** | Corrupted `manifest.json` (JSONDecodeError); irrecoverable Milvus database corruption. | `verify_index_integrity()["is_corrupt"] == True`. | Critical health alert; vector retrieval blocked; full fallback to lexical mode. | Remove corrupted `.memsearch/` files and invoke `memory_index_queue.py --rebuild`. |
| **`MISSING`** | Fresh workspace deployment; no `index_health.json` or collections exist. | Absence of `index_health.json` and 0 completed jobs. | Context compiler prompts for initial index bootstrap. | Run `memory_index_queue.py --rebuild`. |

---

## 6. SECTION 34: INDEX CONSISTENCY PROBE

A forensic inspection was conducted on `.agents/memory/index_health.json` and compared against live disk files and manifest tracking.

### 6.1 Current Live Health State Record
Inspection of `/workspaces/codespaces-blank/.agents/memory/index_health.json`:
```json
{
  "status": "STALE",
  "canonical_revision": "6512fc8ee7af43cb",
  "indexed_revision": "1387a86172d2dcfb",
  "pending_jobs_count": 1,
  "total_processed_jobs": 43,
  "failed_jobs_count": 0,
  "dead_letter_jobs_count": 0,
  "last_success": "2026-09-03T17:22:31.446745+00:00",
  "last_failure": null,
  "failed_sources": [],
  "embedding_provider": "onnx",
  "embedding_model": "bge-m3",
  "embedding_dimension": 1024,
  "migration_state": "CURRENT",
  "diagnostics": [],
  "schema_version": "1.0.0",
  "last_updated": "2026-09-04T12:25:32.883974+00:00"
}
```

### 6.2 Empirical Drift Analysis (Manifest Hash vs. Live Disk Hash)
Comparing `/workspaces/codespaces-blank/.agents/memory/.memsearch/manifest.json` against current live files on disk reveals hash discrepancies across active workspace memory files:

| File Path | Indexed Manifest Hash (SHA-256) | Live Disk Hash (SHA-256) | Status |
| :--- | :--- | :--- | :--- |
| `.agents/memory/CURRENT.md` | `45088dad04a3b84045fd6a8b040b791417d28613d0e5055406b181f87217fc34` | `a1fbd7ef6243dd54732be767a247b333f1dc4ea293106850879bc343736b8454` | **MODIFIED** |
| `.agents/memory/DECISIONS.md` | `547c3fbca023c80a00c3fdd3448f7984b4fae117f8bdcd682d1bb6d3ff9da55f` | `db8ddb5aa1b7f02184d632cc96165cf1af0aebb0486a112f0d685b750027af55` | **MODIFIED** |
| `.agents/memory/GOTCHAS.md` | `d0bc8c2068253766cbac4bf59918005cda71227150277256e2f84acd37f034c0` | `ba07e40e0c9f3f56a68d364e442fcbdb87be506f46f8d3120e43709d813019f7` | **MODIFIED** |
| `.agents/memory/PROCEDURES.md` | `53299cd42349940bb95bdd43ccdc3d2a73d350330caa298c8cf36ab8e0b05ae6` | `da8bd4b3b4bd2c272fe7300d164fcef10d672a12e09e0074f26b3c22186ea5d5` | **MODIFIED** |
| `.agents/memory/ARCHITECTURE.md`| `589488be897c30198211f6c1ce4a341f962f1ec180b9c9c6f70f3229264e294c` | `82654bfc667f370dc83bb88065d6609f8a88cbf857a9b0e8e384e0db6271c61d` | **MODIFIED** |

### 6.3 Forensic Root Cause & No-Change Enforcement
- **Why the index is STALE**: Source markdown files were updated during active development and multi-agent coordination without executing a synchronous queue drain.
- **Queue State**: Inspection of `index_queue.jsonl` confirms 5 pending queue jobs waiting for drain (`notes.md`, `DECISIONS.md`, `GOTCHAS.md`, `ARCHITECTURE.md`, `PROCEDURES.md`).
- **Strict Compliance with Section 3**: In strict compliance with the No-Change Policy, the index was **NOT mutated or drained** to force a clean status. The STALE state is documented as an authentic snapshot of runtime operations.

---

## 7. SECTION 35: INDEXING & QUEUE MECHANICS

### 7.1 Queue Architecture & Control Plane
- **Queue Implementation**: `scripts/memory_index_queue.py`.
- **Durable Queue Log**: `.agents/memory/index_queue.jsonl` (JSONL append-only log).
- **Execution Model**: **Queued, asynchronous, batch drainable, single-writer lease locked**.

### 7.2 Single-Writer Lease Locking
- **Lease Lock File**: `/workspaces/codespaces-blank/.agents/memory/index_writer.lease.lock`.
- **Locking Implementation**: Uses `scripts/lock_manager.py` with `file_lock` context manager implementing `fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)`.
- **Lease Timeout**: Configurable default of 10.0 seconds for drains; 30.0 seconds for full rebuilds.
- **Concurrency Protection**: If another process holds the lease lock, `SingleWriterConflictError` / `LockTimeout` is caught, logging a warning and safely aborting without corrupting Milvus Lite.

### 7.3 Queue Coalescing & Idempotency Keys
- **Idempotency Key**: Each job has a deterministic unique ID: `job_{timestamp_ms}_{uuid_hex8}` (e.g., `job_1788549093883_84a98e90`).
- **Enqueue Deduplication**: If an existing pending job in `index_queue.jsonl` shares the identical `source_path`, `content_hash`, and `event_type`, `enqueue()` immediately returns the existing job without creating a duplicate.
- **Coalescing Execution (`_coalesce_pending_jobs`)**:
  - When `drain()` runs, pending jobs are grouped by `source_path`.
  - For files edited multiple times in rapid succession, only the **latest** job is retained for indexing.
  - All preceding pending jobs for that file are marked `status = "coalesced"` with note `"Coalesced into newer sequential update"`.
  - This prevents wasteful multi-minute ONNX embedding runs on intermediate file drafts.

### 7.4 Retry Policy & Dead-Letter Queue (DLQ)
- **Retry Threshold**: `max_attempts = 3`.
- **Retry Mechanism**: When an indexing attempt fails (e.g. temporary process lock), the job's `attempts` counter increments, `error` is recorded, and status remains `pending` for the next drain cycle.
- **Dead-Letter Transition**: If `attempts >= max_attempts`, the job transitions to `status = "failed"`, `dead_letter = True`, and is appended to `.agents/memory/index_dead_letter.jsonl`.
- **DLQ Recovery**: `IndexQueueManager.requeue_dead_letter(job_id=None)` moves dead-letter jobs back to active pending state with attempts reset to 0.

---

## 8. COMPANION ARTIFACTS & EVIDENCE SUMMARY

1. **Mermaid Flow Diagram**:
   - Location: `/workspaces/codespaces-blank/.agent/memory-state/diagrams/index-flow.mmd`
   - Covers: Canonical file mutation -> hook trigger -> queue enqueue -> lease lock -> coalescing -> MemSearch backend adapter -> ONNX bge-m3 dense + BM25 sparse indexing -> Milvus Lite upsert -> manifest update -> health refresh & graceful fallback.
2. **Raw Evidence Artifacts**:
   - `/workspaces/codespaces-blank/.agent/memory-state/evidence/memsearch-stats.txt`: Verified output of `memsearch stats` showing 264 indexed chunks.
   - `/workspaces/codespaces-blank/.agent/memory-state/evidence/memsearch-search.txt`: Verified output of `memsearch search "architecture"` showing top 5 semantic matches and similarity scores.

