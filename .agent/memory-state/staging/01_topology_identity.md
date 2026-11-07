# ANTIGRAVITY MEMORY OS — FORENSIC TOPOLOGY & PLATFORM AUDIT
## Master Snapshot Identity, Complete File Manifest, Repository Tree, Dependency Matrix, Data Store Inventory, Runtime Process Graph & Resource Profile

**Document Identifier:** `01_topology_identity.md`  
**Staging Location:** [`.agent/memory-state/staging/01_topology_identity.md`](file:///workspaces/codespaces-blank/.agent/memory-state/staging/01_topology_identity.md)  
**Author:** Agent 1: Forensic Topology & Platform Auditor  
**Directives Governed:** [`instruction.md`](file:///workspaces/codespaces-blank/instruction.md) (Sections 6, 7, 8, 44, 45, 64, 65; Section 2 Absolute Evidence Hierarchy; Section 3 No-Change Policy)  
**Execution Timestamp:** 2026-09-04T19:15:00Z  
**Target Repository:** `/workspaces/codespaces-blank`  
**Companion Artifacts:**
- Machine File Manifest: [`.agent/memory-state/machine/file-manifest.json`](file:///workspaces/codespaces-blank/.agent/memory-state/machine/file-manifest.json)
- Machine Dependency Manifest: [`.agent/memory-state/machine/dependency-manifest.json`](file:///workspaces/codespaces-blank/.agent/memory-state/machine/dependency-manifest.json)
- Full Repository Tree: [`.agent/memory-state/evidence/tree.txt`](file:///workspaces/codespaces-blank/.agent/memory-state/evidence/tree.txt)
- Master System State: [`.agent/memory-state/MEMORY_SYSTEM_STATE.md`](file:///workspaces/codespaces-blank/.agent/memory-state/MEMORY_SYSTEM_STATE.md)

---

## 1. Executive Summary & Evidence Hierarchy

This forensic report establishes the empirical, concrete baseline of the Antigravity Engineering Workstation and the 8-tier Antigravity Persistent Memory Operating System. Conducted in strict adherence to Section 3 (No-Change Policy) of [`instruction.md`](file:///workspaces/codespaces-blank/instruction.md), every finding in this report is derived from live runtime execution, process tree sampling, cryptographic hashing, and live configuration inspection without altering any canonical memory or system state.

### 1.1 Evidence Taxonomy
In accordance with Section 2, all findings are stamped with their evidentiary classification:
- `[OBSERVED_EXECUTION]`: Empirically verified through shell execution, system inspection (`lscpu`, `free`, `ps`, `lsof`, `milvus-lite`), and real-time process monitoring.
- `[SOURCE_CODE]`: Verified by direct inspection of Python scripts, shell hooks, and build manifests.
- `[CONFIGURATION]`: Extracted from static configuration files (`mcp_config.json`, `config.toml`, `manifest.json`, `pyvenv.cfg`).
- `[TEST_EVIDENCE]`: Generated from executed test suites, diagnostic benchmarks, or tool runs.
- `[DOCUMENTED]`: Architectural statements from specifications ([`instruction.md`](file:///workspaces/codespaces-blank/instruction.md), [`AGENTS.md`](file:///workspaces/codespaces-blank/AGENTS.md)).
- `[CONTRADICTED]`: Discrepancies between documented claims and observed runtime reality.
- `[UNKNOWN]`: Unverifiable parameters or uninstantiated processes.

### 1.2 Core Audit Discoveries
1. **Operating Environment Drift Exposed:** While earlier audit documentation claimed an Ubuntu 22.04 LTS baseline, live kernel and release inspection proves the container runs **Ubuntu 24.04.4 LTS (Noble Numbat)** on Linux kernel `6.8.0-1052-azure` with Python 3.12.1 and Node.js v24.14.0 `[CONTRADICTED / OBSERVED_EXECUTION]`.
2. **Dual-Layer Milvus Architecture:** Two distinct Milvus Lite instances coexist: a global user instance at `~/.memsearch/milvus.db` (5.4 MB) and a workspace instance at `.agents/memory/.memsearch/milvus.db` (204 KB, 16 indexed chunks).
3. **Flock Singleton Gating:** Live inspection captured concurrent lock contention on `~/.memsearch/milvus.db/LOCK`. Milvus Lite enforces single-writer execution via `fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)`, throwing `DataDirLockedError` when secondary processes attempt simultaneous access `[OBSERVED_EXECUTION]`.
4. **Vector Model Topology:** Embeddings are produced locally using CPU-optimized ONNX runtime with `BAAI/bge-m3` (1024-dimensional dense vectors), completely avoiding external API key dependencies `[OBSERVED_EXECUTION]`.
5. **Disk Capacity Alert:** The overlay root filesystem `/` is at **98% capacity** (31 GB used of 32 GB, 730 MB available), driven heavily by build artifacts, container packages, and the `.venv-memsearch` environment (489 MB) `[OBSERVED_EXECUTION]`.

---

## 2. Section 6: Master Snapshot Identity

| Parameter | Recorded Value | Evidence Source |
| :--- | :--- | :--- |
| **Snapshot Schema Version** | `1.0.0` | [`instruction.md`](file:///workspaces/codespaces-blank/instruction.md) Section 6 |
| **Snapshot Identifier** | `SNAP-20260904-01-TOPOLOGY` | Generated forensic identifier |
| **Generated Timestamp** | `2026-09-04T19:15:00Z` | System UTC clock |
| **Timezone** | `UTC (+00:00)` | System environment |
| **Repository Path** | `/workspaces/codespaces-blank` | Working directory root |
| **Repository Name** | `codespaces-blank` | Workspace basename |
| **Git Remote(s)** | `None configured` (local repository only) | `[OBSERVED_EXECUTION: git remote -v]` |
| **Current Branch** | `main` | `[OBSERVED_EXECUTION: git branch --show-current]` |
| **HEAD Commit SHA** | `b9a56487e1ad925c041c7a8225a71a738fa561d8` | `[OBSERVED_EXECUTION: git rev-parse HEAD]` |
| **Working-Tree Status** | Dirty: 74 modified/deleted tracked files, 68 untracked items | `[OBSERVED_EXECUTION: git status --porcelain]` |
| **Antigravity CLI Version** | `agy 1.1.26` (`/home/codespace/.local/bin/agy`) | `[OBSERVED_EXECUTION: agy --version]` |
| **MemSearch CLI Version** | `memsearch 0.4.19` (`/home/codespace/.local/bin/memsearch`) | `[OBSERVED_EXECUTION: memsearch --version]` |
| **Operating System** | `Ubuntu 24.04.4 LTS (Noble Numbat)` | `[OBSERVED_EXECUTION: /etc/os-release]` |
| **Linux Kernel** | `6.8.0-1052-azure #58~22.04.1-Ubuntu SMP x86_64` | `[OBSERVED_EXECUTION: uname -a]` |
| **CPU Architecture** | `x86_64` (AMD EPYC 9V74 80-Core, 4 vCPUs allocated) | `[OBSERVED_EXECUTION: lscpu]` |
| **Base Python Runtime** | `3.12.1` (`/home/codespace/.python/current/bin/python3`) | `[OBSERVED_EXECUTION: python3 --version]` |
| **Isolated MemSearch Python** | `3.12.1` (`/workspaces/codespaces-blank/.venv-memsearch/bin/python3`) | `[OBSERVED_EXECUTION: .venv-memsearch python3]` |
| **Node Runtime** | `v24.14.0` (`/home/codespace/nvm/current/bin/node`) | `[OBSERVED_EXECUTION: node --version]` |
| **Package Managers** | `uv 0.12.8`, `npm 11.9.0`, `pip 26.2.1`, `apt/dpkg 1.22.6` | `[OBSERVED_EXECUTION]` |
| **Vector Database Substrate** | `Milvus Lite 3.2.1` / `pymilvus 3.0.1` | `[OBSERVED_EXECUTION: uv pip list]` |
| **Embedding Provider** | `onnx` (CPU ONNX Runtime 1.29.0) | `[CONFIGURATION: ~/.memsearch/config.toml]` |
| **Embedding Model** | `BAAI/bge-m3` (ONNX INT8 quantized) | `[OBSERVED_EXECUTION / CONFIGURATION]` |
| **Embedding Dimension** | `1024` dimensions | `[OBSERVED_EXECUTION: index_health.json]` |

---

## 3. Section 7: Complete File Manifest

A complete traversal of `/workspaces/codespaces-blank` was conducted, excluding transient directories (`.git`, `node_modules`, `__pycache__`, `.venv-memsearch`, and `.agent/memory-state` during generation). Every file was hashed with SHA-256 and categorized into canonical, runtime, configuration, test, audit, and generated classes.

The full machine-readable manifest is stored at [`.agent/memory-state/machine/file-manifest.json`](file:///workspaces/codespaces-blank/.agent/memory-state/machine/file-manifest.json).

### 3.1 Classification Breakdown (470 Files Cataloged)

```text
┌─────────────────────────────────────────────────────────────┐
│              FILE CLASSIFICATION DISTRIBUTION               │
├─────────────────────┬──────────────┬────────────────────────┤
│ Classification      │ Count        │ Primary Subsystems     │
├─────────────────────┼──────────────┼────────────────────────┤
│ TEST                │ 120 files    │ tests/, fixtures/      │
│ RUNTIME             │ 90 files     │ scripts/, tools/bin/   │
│ AUDIT               │ 78 files     │ .agent/memory-audit/   │
│ DOCUMENTATION       │ 52 files     │ docs/, skills/, *.md   │
│ OTHER               │ 43 files     │ cyber-runner/, PDFs    │
│ CONFIG              │ 35 files     │ .agents/, .vscode/     │
│ DERIVED             │ 28 files     │ ledgers, queues, eval  │
│ GENERATED           │ 13 files     │ locks, logs, temp sess │
│ CANONICAL           │ 11 files     │ .agents/memory/*.md    │
├─────────────────────┼──────────────┼────────────────────────┤
│ TOTAL               │ 470 files    │ Workspace Scanned      │
└─────────────────────┴──────────────┴────────────────────────┘
```

### 3.2 Memory Relevance Distribution
- **HIGH Relevance (184 files):** Direct Memory OS engines, canonical markdown files, candidate inbox queues, lifecycle hooks, memory doctor diagnostics, and acceptance test suites.
- **MEDIUM Relevance (151 files):** Devcontainer scripts, platform baseline audit logs, general documentation, and subagent definitions.
- **LOW Relevance (129 files):** Test fixtures, mock binaries, sample network traces, VS Code workspace settings.
- **NONE (6 files):** Unrelated medical/curriculum PDFs stored in workspace root (`Medicine and Dentistry-CCMAS 2023-FINAL.pdf`, etc.).

---

## 4. Section 8: Complete Actual Repository Tree

The complete physical repository layout was captured using `tree -a -I ".git|node_modules|__pycache__|.venv-memsearch|build" /workspaces/codespaces-blank` and is preserved in [`.agent/memory-state/evidence/tree.txt`](file:///workspaces/codespaces-blank/.agent/memory-state/evidence/tree.txt).

The scan cataloged **181 directories and 484 physical files**.

### 4.1 Structural Topography & Directory Roles

```text
/workspaces/codespaces-blank/
├── .agent/                             # Comprehensive audit, diagnostic, and state reports
│   ├── memory-audit/                   # 19 forensic audit logs, baseline traces, defect ledgers
│   └── memory-state/                   # Post-build state extraction package (this audit)
│       ├── evidence/                   # Raw verification outputs (tree.txt)
│       ├── machine/                    # Machine-readable manifests (file, dependency, etc.)
│       └── staging/                    # Modular audit findings (01 through 11)
├── .agent-state/                       # Ephemeral multi-phase execution state
│   ├── current-state.md                # Phase mirror
│   └── decisions.md                    # In-flight decisions
├── .agents/                            # Antigravity customization and memory core
│   ├── agents/                         # 9 domain subagent definitions
│   ├── hooks.json                      # Deterministic lifecycle hook registry
│   ├── mcp_config.json                 # MCP server declarations (8 servers)
│   ├── memory/                         # Project Persistent Memory (8-Tier OS)
│   │   ├── .memsearch/                 # Local Milvus Lite DB and indexing manifest
│   │   ├── inbox/                      # Staged candidate bus and procedural staging
│   │   ├── models/                     # Shadow ranker configuration
│   │   ├── sessions/                   # 4 episodic session markdown journals
│   │   ├── shadow_eval/                # Offline retrieval evaluation records
│   │   ├── ARCHITECTURE.md             # Canonical layer & component definitions
│   │   ├── CURRENT.md                  # Active working memory (< 30 lines)
│   │   ├── DECISIONS.md                # Architectural decision records (ADRs)
│   │   ├── GOTCHAS.md                  # Operational traps & mitigations
│   │   ├── INDEX.md                    # Project memory index
│   │   ├── PROCEDURES.md               # Distilled executable workflows
│   │   ├── admission_decisions.jsonl   # Gatekeeper audit log
│   │   ├── index_health.json           # Vector index status & telemetry
│   │   ├── index_queue.jsonl           # Durable index mutation log
│   │   ├── learning_ledger.json        # Access counts & decay reinforcement
│   │   ├── retrieval_ledger.jsonl      # Query telemetry & relevance judgments
│   │   └── telemetry.json              # Retrieval quality benchmarks (MRR, NDCG)
│   ├── rules/                          # Workstation governance guidelines
│   └── skills/                         # 16 domain skillbooks
├── .devcontainer/                      # Devcontainer specification and verification suite
├── .environment-audit/                 # Pre-build environment audit records
├── .environment-baseline/              # Workstation toolchain baseline measurements
├── cyber-runner/                       # Cyberpunk game demo application
├── docs/                               # Master workstation architectural documentation
│   ├── architecture.md                 # 10-layer master architecture
│   ├── operations.md                   # Daily commands & diagnostic runbooks
│   ├── toolchain-matrix.md             # Component & toolchain inventory
│   ├── compatibility-matrix.md         # Platform constraints & boundaries
│   └── test_reports/                   # 23 verification test reports
├── fixtures/                           # Multi-domain test fixtures (Android, C, Web, WASM)
├── scripts/                            # Memory OS engine & utility implementations
│   ├── hooks/                          # PreInvocation, PreToolUse, PostToolUse, Stop
│   ├── candidate_bus.py                # Candidate experience bus & SHA-256 deduplication
│   ├── context_compiler.py             # Progressive disclosure & trust gating
│   ├── evidence_reranker.py            # RRF reciprocal rank fusion & MMR diversity
│   ├── learning_loop.py                # Decay calculation & shadow ranker
│   ├── memory_compiler.py              # Admission gating & normalization
│   ├── memory_doctor.py                # 6-dimension health diagnostic engine
│   ├── memory_feedback.py              # Retrieval telemetry & NDCG calculation
│   ├── memory_index_queue.py           # Single-writer index queue & lease manager
│   ├── memory_reconciler.py            # Bitemporal reconciliation & supersession
│   ├── memsearch_backend.py            # Decoupled Milvus/ONNX adapter facade
│   ├── procedural_engine.py            # Workflow sequence mining & synthesis
│   ├── query_router.py                 # 5-intent classifier & explicit abstention
│   └── search_memory.py                # Hybrid lexical + semantic retrieval CLI
├── tests/                              # Memory OS test suite (unit, e2e, adversarial)
└── tools/                              # Diagnostic CLI wrappers (agy-*-doctor)
```

### 4.2 Excluded Directories Rationale
1. `.git/` (21 MB): Git internal object database, commit history, and packfiles; excluded to avoid bloating file manifests with VCS metadata.
2. `node_modules/` & `fixtures/web/node_modules/` (124 MB): Deep third-party JavaScript dependencies; excluded from source tree inspection.
3. `__pycache__/`: Ephemeral Python bytecode cache (`*.pyc`); excluded per Section 3 standards.
4. `.venv-memsearch/` (489 MB): Isolated virtual environment created by `uv` for Milvus Lite, ONNX Runtime, and PyMilvus; inspected separately in Section 44.
5. `fixtures/c_native/build/`: Compiled CMake and Ninja build artifacts; excluded to prevent binary noise.

---

## 5. Section 44: Dependency Inventory

The workstation integrates dependencies across the host system, the workstation base Python environment, the isolated MemSearch virtualenv, Node.js packages, and system native compilers.

The complete machine-readable manifest is stored at [`.agent/memory-state/machine/dependency-manifest.json`](file:///workspaces/codespaces-blank/.agent/memory-state/machine/dependency-manifest.json).

### 5.1 Memory Substrate & Semantic Search Dependencies

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        MEMORY OS RUNTIME DEPENDENCY MATRIX                             │
├────────────────────┬───────────┬───────────────────┬─────────┬─────────────────────────┤
│ Package            │ Version   │ Environment       │ Scope   │ Primary Usage           │
├────────────────────┼───────────┼───────────────────┼─────────┼─────────────────────────┤
│ memsearch          │ 0.4.19    │ .venv-memsearch   │ runtime │ Core vector search CLI  │
│ milvus-lite        │ 3.2.1     │ .venv-memsearch   │ runtime │ Local vector DB engine  │
│ pymilvus           │ 3.0.1     │ .venv-memsearch   │ runtime │ Milvus SDK client       │
│ onnxruntime        │ 1.29.0    │ .venv-memsearch   │ runtime │ CPU ONNX model runner   │
│ faiss-cpu          │ 1.15.0    │ .venv-memsearch   │ runtime │ In-memory fallback DB   │
│ tokenizers         │ 0.23.2    │ .venv-memsearch   │ runtime │ bge-m3 token encoder    │
│ huggingface-hub    │ 1.30.0    │ .venv-memsearch   │ runtime │ Model weight cache      │
│ pydantic           │ 2.13.5    │ .venv-memsearch   │ runtime │ Schema validation       │
│ watchdog           │ 6.0.0     │ .venv-memsearch   │ optional│ FS change notification  │
│ bge-m3 (ONNX)      │ BAAI INT8 │ Model Substrate   │ runtime │ 1024-dim dense vectors  │
│ agy (Antigravity)  │ 1.1.26    │ System CLI        │ runtime │ Master AI CLI & runtime │
│ uv                 │ 0.12.8    │ System CLI        │ dev/run │ Venv & package resolver │
│ pytest             │ 9.1.1     │ Base Python       │ test    │ Verification runner     │
│ gitleaks           │ 8.18.4    │ System CLI        │ gate    │ Secret leak prevention  │
│ semgrep            │ 1.98.0+   │ System CLI        │ test    │ AST code scanner        │
│ git                │ 2.53.0    │ System CLI        │ runtime │ Source code management  │
│ ripgrep (rg)       │ 14.1.0    │ System CLI        │ runtime │ Lexical BM25 search     │
└────────────────────┴───────────┴───────────────────┴─────────┴─────────────────────────┘
```

### 5.2 Model Context Protocol (MCP) Infrastructure
The platform declares 8 MCP servers in [`.agents/mcp_config.json`](file:///workspaces/codespaces-blank/.agents/mcp_config.json) executed via Node.js, Python, or native Go:
1. **`sqlite-safe`**: Executes `@modelcontextprotocol/server-sqlite` via Node.js with `DB_READONLY: true`. Blocks mutations.
2. **`postgres-safe`**: Executes `@modelcontextprotocol/server-postgres` via Node.js with `PGREADONLY: true`. Read-only schema exploration.
3. **`playwright`**: Executes `@executeautomation/playwright-mcp-server` via Node.js. Isolated headless browser automation.
4. **`context7`**: Executes `@upsonic/context7` via Node.js. Live documentation lookup for evolving APIs.
5. **`chrome-devtools`**: Executes `chrome-devtools-mcp` via Node.js. Inspects DOM, console, network traces.
6. **`github`**: Executes native Go binary `/home/codespace/.local/share/mise/installs/go/1.24.0/bin/github-mcp-server`.
7. **`hexana`**: Executes `hexana-mcp stdio`. WebAssembly analysis, disassembly, and function call graphs.
8. **`tavily`**: Executes `tavily` via Node.js. Real-time web crawling and search API.

---

## 6. Section 45: Data Store Inventory

The Antigravity Memory OS distributes durable and derived state across 9 distinct storage media encompassing 22 specific data stores.

### 6.1 Comprehensive Data Store Catalog

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   COMPLETE DATA STORE INVENTORY MATRIX                                      │
├────────────────────────────────┬───────────────┬────────────────────────────┬─────────────┬─────────────────┤
│ Store Location                 │ Format        │ Role                       │ Authority   │ Process Owner   │
├────────────────────────────────┼───────────────┼────────────────────────────┼─────────────┼─────────────────┤
│ .agents/memory/CURRENT.md      │ Markdown      │ Active working state       │ AUTHORITATIVE│ Pre/Post Hooks  │
│ .agents/memory/DECISIONS.md    │ Markdown      │ Architectural decisions    │ AUTHORITATIVE│ Memory Compiler │
│ .agents/memory/GOTCHAS.md      │ Markdown      │ Operational pitfalls       │ AUTHORITATIVE│ Memory Compiler │
│ .agents/memory/ARCHITECTURE.md │ Markdown      │ Persistent architecture    │ AUTHORITATIVE│ Reconciler      │
│ .agents/memory/PROCEDURES.md   │ Markdown      │ Promoted workflows         │ AUTHORITATIVE│ Procedural Eng. │
│ .agents/memory/INDEX.md        │ Markdown      │ Project memory index       │ AUTHORITATIVE│ Session Manager │
│ .agents/memory/sessions/*.md   │ Markdown (4)  │ Episodic session logs      │ AUTHORITATIVE│ Session Manager │
│ ~/.gemini/.../memory/*.md      │ Markdown (11) │ Global user/env memory     │ AUTHORITATIVE│ Global CLI      │
│ .agents/memory/inbox/cand...   │ JSONL (207)   │ Candidate experience bus   │ DERIVED/STAGE PostToolUse Hook │
│ .agents/memory/admiss...jsonl  │ JSONL (133)   │ Gatekeeper audit ledger    │ DERIVED     │ Memory Compiler │
│ .agents/memory/index_q...jsonl │ JSONL (295)   │ Index mutation queue       │ DERIVED     │ Index Queue Eng │
│ .agents/memory/retrie...jsonl  │ JSONL (23)    │ Query telemetry ledger     │ DERIVED     │ Feedback Eng.   │
│ .agents/memory/telemetry.json  │ JSON          │ Retrieval benchmark scores │ DERIVED     │ Doctor / Bench  │
│ .agents/memory/index_he...json │ JSON          │ Vector index health report │ DERIVED     │ Doctor / Queue  │
│ .agents/memory/learning...json │ JSON          │ Access & decay ledger      │ DERIVED     │ Learning Loop   │
│ .agents/memory/models/*.json   │ JSON          │ Shadow ranker parameters   │ CONFIG      │ Learning Loop   │
│ ~/.memsearch/milvus.db         │ Milvus Lite   │ Global vector database     │ DERIVED     │ MemSearch CLI   │
│ .agents/memory/.memsearch/mil..│ Milvus Lite   │ Project vector database    │ DERIVED     │ MemSearch CLI   │
│ .agents/memory/.memse...man... │ JSON          │ Vector manifest (17 files) │ DERIVED     │ MemSearch CLI   │
│ .agents/memory/inbox/proc...   │ MD/JSON (8)   │ Staged procedure workflows │ DERIVED/STAGE Procedural Eng. │
│ .agents/memory/*.lock          │ Zero-byte     │ Single-writer file locks   │ EPHEMERAL   │ Reconciler/Queue│
│ ~/.memsearch/milvus.db/LOCK    │ OS Lockfile   │ Milvus Lite flock lock     │ EPHEMERAL   │ milvus-lite     │
└────────────────────────────────┴───────────────┴────────────────────────────┴─────────────┴─────────────────┘
```

### 6.2 Data Store Details & Schemas

#### 1. Canonical Markdown Stores (Tier 1, 3, 4, 7)
- **Authority:** Authoritative. Primary source of truth.
- **Recovery:** Git version control. If derived vector stores are corrupted or deleted, all knowledge is reconstructed by re-indexing canonical Markdown files.
- **Locking:** Protected by advisory file locks (`.lock`) using `fcntl.flock` during write operations.

#### 2. Candidate Experience Bus (`inbox/candidates.jsonl`) (Tier 6)
- **Authority:** Derived / Staging buffer.
- **Schema:**
  ```json
  {
    "id": "cand-20260904-123456-abc123",
    "timestamp": "2026-09-04T19:13:00Z",
    "session_id": "sess-20260904-01",
    "trigger_event": "PostToolUse",
    "source_tool": "run_command",
    "candidate_type": "GOTCHA",
    "scope": "PROJECT",
    "confidence": 0.85,
    "content": "Description of discovered trap...",
    "raw_evidence": "Command exit code 1...",
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  }
  ```
- **Record Count:** 207 records `[OBSERVED_EXECUTION]`.

#### 3. Index Queue (`index_queue.jsonl`) (Tier 5 Management)
- **Authority:** Derived operational queue.
- **Schema:**
  ```json
  {
    "job_id": "job-idx-20260904-001",
    "action": "UPSERT",
    "source_path": "/workspaces/codespaces-blank/.agents/memory/GOTCHAS.md",
    "content_hash": "a1b2c3...",
    "enqueued_at": "2026-09-04T12:30:00Z",
    "status": "COMPLETED",
    "attempts": 1,
    "completed_at": "2026-09-04T12:30:02Z"
  }
  ```
- **Record Count:** 295 records `[OBSERVED_EXECUTION]`.

#### 4. Retrieval Feedback Ledger (`retrieval_ledger.jsonl`) (Tier 8)
- **Authority:** Derived telemetry ledger.
- **Schema:**
  ```json
  {
    "query_id": "qry-20260904-001",
    "timestamp": "2026-09-04T06:42:54Z",
    "query": "how to build android debug apk",
    "intent": "TASK_DIRECTED",
    "retrieved_chunks": ["chunk-123", "chunk-456"],
    "mrr": 1.0,
    "ndcg_10": 1.0,
    "latency_ms": 5.4,
    "explicit_feedback": null
  }
  ```
- **Record Count:** 23 records `[OBSERVED_EXECUTION]`.

#### 5. Milvus Lite Vector Databases (`~/.memsearch/milvus.db` & `.agents/memory/.memsearch/milvus.db`)
- **Authority:** Derived, non-authoritative vector index.
- **Engine:** Milvus Lite embedded C++ engine via gRPC local thread manager.
- **Collections:** `memsearch_chunks`
- **Fields:** `id` (int64 primary key), `vector` (float32 array, dim=1024), `text` (varchar), `source` (varchar), `chunk_index` (int32).
- **Entities:** Global: 5.4 MB; Local Workspace: 204 KB (16 chunks) `[OBSERVED_EXECUTION]`.
- **Locking:** Single-process exclusion enforced via OS `LOCK` file and `fcntl.flock`.

---

## 7. Section 64: Runtime Process Graph

A forensic snapshot of the active process hierarchy was captured via `ps -eo pid,ppid,user,%cpu,%mem,vsz,rss,stat,start,time,cmd`.

### 7.1 Process Hierarchy Graph

```text
PID 1: /sbin/docker-init [root]
├── PID 7: /bin/sh (entrypoint watchdog)
├── PID 35: sshd: /usr/sbin/sshd [root]
├── PID 64: dockerd --dns 127.0.0.1 [root]
│   └── PID 97: containerd [root]
├── PID 747: sh /home/codespace/.vscode-server/... [codespace]
│   └── PID 756: /vscode/bin/linux-x64/.../node (VS Code Host)
│       ├── PID 799: node (Extension Host)
│       │   ├── PID 1460 -> 1475: /usr/local/codespaces/... (Remote Agent)
│       │   ├── PID 1663 -> 7028: /home/codespace/.local/bin/mise
│       │   └── PID 2110: GitHub Copilot Language Server
│       ├── PID 817 -> 2064: node (File Watcher Daemon)
│       └── PID 2455 -> 2470: /usr/bin/bash (Interactive Shell pts/0)
│           └── PID 3277: agy [Antigravity CLI Orchestrator]
│               ├── PID 3390 -> 3493 -> 3494: node tavily-mcp
│               ├── PID 5965 -> 6090 -> 6095: chrome-devtools-mcp
│               ├── PID 5966 -> 6168 -> 6170: node @upsonic/context7
│               ├── PID 5967 -> 6114 -> 6123: node @modelcontextprotocol/server-postgres
│               ├── PID 5968: hexana-mcp stdio
│               ├── PID 5986 -> 6266 -> 6267: node @executeautomation/playwright-mcp-server
│               ├── PID 5987 -> 6106 -> 6107: node @modelcontextprotocol/server-sqlite
│               ├── PID 5988: github-mcp-server (Native Go binary)
│               ├── PID 16342 -> 16343: pytest tests/ (Background Verification Worker)
│               └── PID 17288: python3 scripts/run_section128_demo.py
│                   └── PID 23156: python3 memsearch index ... (Active Index Worker)
└── PID 2231: adb -L tcp:5037 fork-server server [codespace]
```

### 7.2 Process Attributes & Lifecycle Mechanics

| Process Subsystem | PID(s) | Startup Mechanism | Shutdown / Termination | Singleton / Locking | Log Destination | Health Mechanism |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Antigravity CLI (`agy`)** | `3277` | Interactive terminal invocation (`agy`) | User exit / SIGINT / SIGTERM | Terminal TTY bound (`pts/0`) | `~/.gemini/antigravity-cli/logs/` | Active turn heartbeat |
| **MCP Server Pool** | `3390`-`5988` | Spawned as child subprocesses of `agy` | SIGTERM on `agy` exit | Supervised by `agy` stdio pipes | Stdio pipe to parent | Ping/ListTools handshake |
| **Milvus Lite Engine** | Subproc of `memsearch` | Spawned via Python `MilvusStore` in thread | Thread exit / Python cleanup | `fcntl.flock` on `milvus.db/LOCK` | Embedded log stream | Connection probe on start |
| **Index Worker** | `17288`, `23156` | Sequential script execution | Process completion (Code 0) | `index_writer.lease.lock` | Console stdout / stderr | Exit code assertion |
| **Test Worker (`pytest`)** | `16343` | Diagnostic task launch | Test suite finish | None (read-only tests) | Pipe to `tee` and logfile | Exit code assertion |
| **Android ADB Server** | `2231` | Auto-fork on `adb` CLI call | `adb kill-server` | TCP port `5037` bind | Internal daemon socket | `adb get-state` |

---

## 8. Section 65: Resource Profile

Resource utilization was measured on the live container environment during multi-agent indexing and test operations.

### 8.1 Memory (RAM) Allocation & Usage

```text
┌─────────────────────────────────────────────────────────────┐
│                 SYSTEM RAM PROFILE (MB)                     │
├─────────────────────┬──────────────┬────────────────────────┤
│ Metric              │ Value (MB)   │ Percentage of Total    │
├─────────────────────┼──────────────┼────────────────────────┤
│ Total Physical RAM  │ 15,995 MB    │ 100.0%                 │
│ Used RAM            │ 8,348 MB     │ 52.2%                  │
│ Buffer / OS Cache   │ 6,026 MB     │ 37.7%                  │
│ Available RAM       │ 7,647 MB     │ 47.8%                  │
│ Free RAM (Strict)   │ 2,031 MB     │ 12.7%                  │
│ Shared Memory (shm) │ 64 MB        │ 0.4%                   │
│ Swap Space          │ 0 MB         │ None configured        │
└─────────────────────┴──────────────┴────────────────────────┘
```
*Observation:* With zero swap configured, available memory (~7.6 GB) is sufficient for concurrent ONNX inference and Node MCP servers.

### 8.2 CPU Hardware Profile
- **Processor:** AMD EPYC 9V74 80-Core Processor
- **Allocated vCPUs:** 4 vCPUs (cores 0-3 on NUMA node 0)
- **Core Geometry:** 1 socket, 2 physical cores, 2 threads per core
- **Clock Speed / BogoMIPS:** 5192.25 BogoMIPS
- **Caches:**
  - L1d: 64 KiB (2 instances)
  - L1i: 64 KiB (2 instances)
  - L2: 2 MiB (2 instances)
  - L3: 32 MiB (1 shared instance)
- **Vector Acceleration Extensions:** AVX, AVX2, FMA, BMI1, BMI2, VAES, VPCLMULQDQ, SHA_NI (utilized by ONNX Runtime for INT8 matrix multiplication).

### 8.3 Storage & Filesystem Footprint

```text
┌─────────────────────────────────────────────────────────────┐
│               FILESYSTEM & DISK FOOTPRINT                   │
├─────────────────────┬──────────────┬────────────────────────┤
│ Target Mount / Path │ Footprint    │ Capacity / Context     │
├─────────────────────┼──────────────┼────────────────────────┤
│ Root Filesystem (/) │ 31 GB / 32 GB│ 98% FULL (730 MB avail)│
│ /tmp (/dev/sda1)    │ 5.6 GB / 118G│ 5% Used (106 GB avail) │
│ /vscode (/dev/root) │ 16 GB / 29 GB│ 56% Used               │
├─────────────────────┼──────────────┼────────────────────────┤
│ WORKSPACE ROOT      │ 536 MB total │ /workspaces/...        │
│ ├── .venv-memsearch │ 489 MB       │ Python virtualenv      │
│ ├── fixtures/       │ 124 MB       │ Multi-domain fixtures  │
│ ├── cyber-runner/   │ 22 MB        │ Demo game code         │
│ ├── .git/           │ 21 MB        │ Git repository history │
│ ├── .agents/        │ 7.3 MB       │ Agent OS & Memory Core │
│ ├── .agents/mem-upg │ 5.7 MB       │ Memory OS upgrade pack │
│ ├── scripts/        │ 2.0 MB       │ Execution scripts      │
│ ├── tests/          │ 1.8 MB       │ Test suite scripts     │
│ ├── .agent/         │ 1.3 MB       │ State & Audit reports  │
│ ├── docs/           │ 428 KB       │ Workstation docs       │
│ └── tools/          │ 336 KB       │ Diagnostic tool scripts│
├─────────────────────┼──────────────┼────────────────────────┤
│ MEMORY SUBSYSTEMS   │              │                        │
│ ├── ~/.memsearch/   │ 5.4 MB       │ Global Milvus vector DB│
│ ├── .agents/memory/ │ 1.2 MB       │ Workspace memory core  │
│ └── ~/.gemini/mem/  │ 68 KB        │ Global user memory     │
└─────────────────────┴──────────────┴────────────────────────┘
```
> [!WARNING]
> **Filesystem Capacity Risk:** The primary container overlay filesystem `/` has only **730 MB free space remaining (98% full)**. Build artifacts or large cache downloads could trigger write errors (`ENOSPC`). Temporary large files must use `/tmp` (106 GB available).

### 8.4 Memory OS Entity Metrics

| Metric Entity | Verified Count | Storage Location |
| :--- | :--- | :--- |
| **Staged Experience Candidates** | `207` records | [`.agents/memory/inbox/candidates.jsonl`](file:///workspaces/codespaces-blank/.agents/memory/inbox/candidates.jsonl) |
| **Admission Decisions Logged** | `133` records | [`.agents/memory/admission_decisions.jsonl`](file:///workspaces/codespaces-blank/.agents/memory/admission_decisions.jsonl) |
| **Index Queue Operations** | `295` records | [`.agents/memory/index_queue.jsonl`](file:///workspaces/codespaces-blank/.agents/memory/index_queue.jsonl) |
| **Retrieval Ledger Entries** | `23` records | [`.agents/memory/retrieval_ledger.jsonl`](file:///workspaces/codespaces-blank/.agents/memory/retrieval_ledger.jsonl) |
| **Project Episodic Sessions** | `4` journals | [`.agents/memory/sessions/`](file:///workspaces/codespaces-blank/.agents/memory/sessions/) |
| **Global Episodic Sessions** | `0` journals | `~/.gemini/antigravity-cli/memory/sessions/` |
| **Indexed Vector Chunks (Local)**| `16` chunks | [`.agents/memory/.memsearch/milvus.db`](file:///workspaces/codespaces-blank/.agents/memory/.memsearch/milvus.db) |
| **Indexed Source Files** | `17` files | [`.agents/memory/.memsearch/manifest.json`](file:///workspaces/codespaces-blank/.agents/memory/.memsearch/manifest.json) |
| **Staged Procedures** | `8` workflows | [`.agents/memory/inbox/procedures/`](file:///workspaces/codespaces-blank/.agents/memory/inbox/procedures/) |
| **Offline Shadow Evaluations** | `3` runs | [`.agents/memory/shadow_eval/`](file:///workspaces/codespaces-blank/.agents/memory/shadow_eval/) |
| **Canonical Markdown Files** | `17` files | Workspace (6) and Global User (11) |
| **Active Working State Budget** | `13` lines (504 B) | [`.agents/memory/CURRENT.md`](file:///workspaces/codespaces-blank/.agents/memory/CURRENT.md) (Passes `< 30 lines` budget) |
| **Mean Retrieval Latency** | `6.13 ms` | [`.agents/memory/telemetry.json`](file:///workspaces/codespaces-blank/.agents/memory/telemetry.json) |
| **Mean Reciprocal Rank (MRR)** | `0.95` | [`.agents/memory/telemetry.json`](file:///workspaces/codespaces-blank/.agents/memory/telemetry.json) |
| **NDCG@10 Retrieval Quality** | `0.9631` | [`.agents/memory/telemetry.json`](file:///workspaces/codespaces-blank/.agents/memory/telemetry.json) |

---

## 9. Discrepancies & Contradictions Exposed

In accordance with Section 1 and Section 2 of [`instruction.md`](file:///workspaces/codespaces-blank/instruction.md), discrepancies between documentation, configuration, and observed reality are explicitly highlighted:

1. **OS Distribution Drift:**
   - *Documented Claim:* Various prior audit files listed Ubuntu 22.04 LTS (`jammy`).
   - *Observed Reality:* Host OS is **Ubuntu 24.04.4 LTS (Noble Numbat)** on kernel `6.8.0-1052-azure`.
   - *Resolution:* Marked as `[CONTRADICTED]`. Updated in all machine manifests.

2. **Embedding Model Configuration Claims:**
   - *Documented Claim:* Earlier notes conjectured `sentence-transformers/all-MiniLM-L6-v2`.
   - *Observed Reality:* Active model is `BAAI/bge-m3` executed via local ONNX runtime with 1024-dimensional dense vectors.
   - *Resolution:* Marked as `[OBSERVED_EXECUTION]`. Verified in `~/.memsearch/config.toml` and `index_health.json`.

3. **Index Synchronization Status:**
   - *Documented Claim:* Vector database claimed to be synchronized with canonical files.
   - *Observed Reality:* `index_health.json` reports status `STALE` (`canonical_revision: 6512fc8ee7af43cb`, `indexed_revision: 1387a86172d2dcfb`), with 1 pending job in queue. Background re-indexing worker (`scripts/run_section128_demo.py`) was actively reconciling this state during the audit.
   - *Resolution:* Accurately recorded as `STALE` in accordance with Section 1's anti-whitewashing directive.

---

## 10. Audit Certification & Sign-Off

This forensic topology and platform audit is complete, fully reproducible, and verified by live execution.

- **Primary Staging Output:** [`.agent/memory-state/staging/01_topology_identity.md`](file:///workspaces/codespaces-blank/.agent/memory-state/staging/01_topology_identity.md)
- **Machine Manifest 1:** [`.agent/memory-state/machine/file-manifest.json`](file:///workspaces/codespaces-blank/.agent/memory-state/machine/file-manifest.json) (470 files hashed)
- **Machine Manifest 2:** [`.agent/memory-state/machine/dependency-manifest.json`](file:///workspaces/codespaces-blank/.agent/memory-state/machine/dependency-manifest.json) (Categorized inventory)
- **Evidence Tree:** [`.agent/memory-state/evidence/tree.txt`](file:///workspaces/codespaces-blank/.agent/memory-state/evidence/tree.txt) (181 dirs, 484 files)
- **Zero Secrets Verification:** Scanned and certified clean of API keys, private credentials, and tokens.
- **No-Change Policy Compliance:** 100% compliant. Read-only inspection; zero canonical files modified.
