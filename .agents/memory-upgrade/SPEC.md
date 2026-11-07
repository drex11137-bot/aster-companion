# ANTIGRAVITY MEMORY OS — MASTER ARCHITECTURAL SPECIFICATION
**Document ID:** AGY-SPEC-MEMOS-001  
**Version:** 2.0.0  
**Status:** Approved / Authoritative Architecture Specification  
**Author:** Agent 1 — Lead Memory Architect  
**Effective Date:** 2026-09-03  
**Governing Directives:** `Instruction.md` Sections 5–7, 15, 16, 26, 86, 110, 180, 216, 253; `AGENTS.md`; `~/.gemini/antigravity-cli/memory/POLICY.md`

---

## 1. Executive Summary & Architectural Vision

The Antigravity Memory Operating System (Memory OS) is an autonomous, local-first, semantic, and evidence-gated knowledge management infrastructure designed for pair-programming AI agents operating in the Antigravity CLI environment (`agy`).

Historically, agent memory systems operated on unstructured flat Markdown text, manual user-driven memory promotion, and naive regex/keyword queries. This naive model suffered from five fundamental system pathologies:
1. **Semantic Blindness**: Inability to discover conceptually related memories when keywords differ.
2. **Temporal Collapse**: Conflating current repository state with historical observations, causing stale assumptions to persist indefinitely.
3. **Hallucinatory Ingestion**: Unvalidated agent discoveries and speculative thoughts entering durable storage without verification.
4. **Contradiction Accumulation**: Silently accumulating conflicting facts instead of enforcing supersession and lineage tracking.
5. **Context Bloat & Contamination**: Inadvertent loading of entire memory trees, polluting LLM context windows and risking secret leakage.

The Memory OS upgrade transforms the architecture into an **8-tier evidence-gated operating system**. It marries **Canonical Markdown Authority** with a **derived, disposable hybrid retrieval substrate** (MemSearch dense embeddings + BM25 lexical search fused via Reciprocal Rank Fusion), strict **bitemporal semantics**, **5-gate admission filtering**, and **lineage-preserving supersession**.

```text
                                 AGENT EXPERIENCE
                                        │
                                        ▼
                                EXPERIENCE CAPTURE
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
                 Conversation Events             Tool & Evidence
                  (User / Agent)                 (CLI / Git / Tests)
                         │                             │
                         └──────────────┬──────────────┘
                                        ▼
                                 CANDIDATE BUS
                           (.agents/memory/inbox/)
                                        │
                                        ▼
                                 MEMORY COMPILER
                                        │
                  ┌─────────────────────┼─────────────────────┐
                  ▼                     ▼                     ▼
             Classify              Deduplicate            Conflict
          (15 Norm Types)        (Hash / Semantic)       (Lineage)
                  │                     │                     │
                  └─────────────────────┼─────────────────────┘
                                        ▼
                                 ADMISSION GATE
                    [Security -> Evidence -> Dedup -> Temporal -> Scope]
                                        │
                                ┌───────┴───────┐
                                ▼               ▼
                             REJECT          PROMOTE
                                                │
                                                ▼
                                    CANONICAL MARKDOWN (TIER 4)
                                    (Human-Readable Source of Truth)
                                                │
                                                ▼
                                           INDEX QUEUE
                                    (Async Single-Writer WAL)
                                                │
                                                ▼
                                    RETRIEVAL SUBSTRATE (TIER 6)
                                   (MemSearch: Dense + BM25 + RRF)
                                                │
                                ┌───────────────┼───────────────┐
                                ▼               ▼               ▼
                              Dense          Lexical        Metadata
                            Embeddings        BM25           Filters
                                └───────────────┼───────────────┘
                                                ▼
                                        RECIPROCAL RANK
                                         FUSION (RRF)
                                                │
                                                ▼
                                        EVIDENCE RERANKER
                                  (Freshness + Authority Bias)
                                                │
                                                ▼
                                        CONTEXT COMPILER
                                 (Scoped & Budgeted Ingestion)
                                                │
                                                ▼
                                            AGENT TURN
```

---

## 2. The Canonical Markdown Authority Invariant

### 2.1 The Invariant Definition
> **INVARIANT 1 & 2:** Canonical memory remains human-readable Markdown. All vector stores, embeddings, database files, BM25 tables, inverted indexes, and relationship graphs are strictly **derived state**, which must be completely disposable and deterministically rebuildable from canonical Markdown files.

```text
       ┌─────────────────────────────────────────────────────────┐
       │             CANONICAL MARKDOWN AUTHORITY                │
       │  - Project Memory: .agents/memory/*.md                  │
       │  - Global Memory: ~/.gemini/antigravity-cli/memory/*.md │
       │  - Governed by Git, atomic transactions, and file locks │
       └────────────────────────────┬────────────────────────────┘
                                    │ (Deterministic ETL & Embedding)
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │             DERIVED RETRIEVAL SUBSTRATE                 │
       │  - MemSearch Vector Stores (HNSW / FAISS / SQLite-VSS)  │
       │  - BM25 Inverted Lexical Indexes                        │
       │  - Derived Lineage & Contradiction Graphs               │
       │  - Ephemeral Query Caches                               │
       │  * DISPOSABLE AT ANY TIME * ZERO DATA LOSS ON DELETION  │
       └─────────────────────────────────────────────────────────┘
```

### 2.2 Operational Guarantees
1. **Single Source of Truth**: The definitive state of any memory record resides in its canonical Markdown file. If a conflict occurs between a vector database record and the Markdown document, the Markdown record is unconditionally authoritative.
2. **Disposability & Rebuildability**:
   - The entire retrieval substrate (directories such as `.agent-state/indexes/`, `.cache/memsearch/`, or temporary SQLite databases) can be purged via `rm -rf` without loss of knowledge.
   - The command `python3 scripts/memory_engine.py --rebuild-index` or `scripts/memsearch_backend.py --reindex` must completely reparse all canonical Markdown records, re-embed content, and regenerate indexes from scratch.
3. **Index Failure Isolation (Invariant 9 & 14)**:
   - Failure, crash, or corruption of the vector backend (e.g. missing embedding models, unavailable GPU/Cuda, out-of-memory errors) must **never corrupt** canonical Markdown memory.
   - In the event of retrieval substrate unavailability, the system must gracefully fall back to deterministic lexical grep/BM25 search without aborting agent operations.
4. **Transaction Safety**:
   - All mutations to canonical Markdown must execute through atomic filesystem transactions:
     $$\text{Read} \longrightarrow \text{Pre-Scan Secrets} \longrightarrow \text{Write Temporary File} \longrightarrow \text{Validate Temp File} \longrightarrow \text{Atomic Replace (`os.replace`)} \longrightarrow \text{Enqueue Index Update}$$
   - Writers acquire an advisory file lock (`<file>.lock`) to ensure single-writer serialized writes across concurrent subagents.

---

## 3. The 8-Tier Memory Architecture

The Memory OS organizes knowledge into 8 functional tiers (Tier 0 through Tier 7), orchestrated by a dedicated Tier 8 Control Plane.

```text
+-------------------------------------------------------------------------------+
| TIER 0: GOVERNANCE & POLICY                                                   |
| Rules, security constraints, instructions (GEMINI.md, AGENTS.md, POLICY.md)   |
+-------------------------------------------------------------------------------+
                                        │
+-------------------------------------------------------------------------------+
| TIER 1: ACTIVE WORKING STATE                                                  |
| Ephemeral task focus, immediate blockers, execution phase (CURRENT.md <30L)  |
+-------------------------------------------------------------------------------+
                                        │
+-------------------------------------------------------------------------------+
| TIER 2: EPISODIC MEMORY                                                       |
| Chronological experience, session summaries, execution traces (sessions/*.md) |
+-------------------------------------------------------------------------------+
                                        │
+-------------------------------------------------------------------------------+
| TIER 3: CANDIDATE MEMORY & STAGING                                            |
| Unverified candidate pool, quarantine, extraction staging (inbox/*.json)      |
+-------------------------------------------------------------------------------+
                                        │
+-------------------------------------------------------------------------------+
| TIER 4: CANONICAL SEMANTIC MEMORY                                             |
| Verified durable facts, decisions, gotchas, architecture (DECISIONS.md, etc.) |
+-------------------------------------------------------------------------------+
                                        │
+-------------------------------------------------------------------------------+
| TIER 5: PROCEDURAL MEMORY                                                     |
| Executable workflows, diagnostic runbooks, skill specs (procedural/*.md)      |
+-------------------------------------------------------------------------------+
                                        │
+-------------------------------------------------------------------------------+
| TIER 6: DERIVED RETRIEVAL SUBSTRATE                                           |
| MemSearch, dense embeddings, BM25 tables, RRF rankers, query caches           |
+-------------------------------------------------------------------------------+
                                        │
+-------------------------------------------------------------------------------+
| TIER 7: EVIDENCE & PROVENANCE                                                 |
| Git commit links, file line ranges, CLI execution logs, test artifacts        |
+-------------------------------------------------------------------------------+
                                        │
+-------------------------------------------------------------------------------+
| TIER 8: MEMORY CONTROL PLANE (ORCHESTRATION & MAINTENANCE)                    |
| Memory Compiler, Candidate Reconciler, Index WAL Queue, Memory Doctor         |
+-------------------------------------------------------------------------------+
```

### 3.1 Tier 0 — Governance & Policy
* **Contents**: `~/.gemini/GEMINI.md`, `/workspaces/codespaces-blank/AGENTS.md`, `.agents/rules/`, `~/.gemini/antigravity-cli/memory/POLICY.md`.
* **Semantics**: Absolute non-negotiable operational boundaries. Defines agent behavior, permission gates, zero-secrets rules, and memory durability scale.
* **Mutability**: Read-only during normal agent tasks; modified solely through explicit, deliberate user governance decisions.

### 3.2 Tier 1 — Active Working State
* **Contents**: `.agents/memory/CURRENT.md`.
* **Semantics**: High-velocity mutable state reflecting the active turn.
* **Constraints**:
  - Strictly budgeted to **< 30 lines**.
  - Must never accumulate historical logs, long code snippets, or session archives.
  - Contains only: Current Objective, Active Status/Phase, Blockers, Immediate Next Steps, and Active Subagents.

### 3.3 Tier 2 — Episodic Memory
* **Contents**: `.agents/memory/sessions/YYYY-MM-DD-HHMM.md` and `~/.gemini/antigravity-cli/memory/sessions/`.
* **Semantics**: Append-only narrative record of historical events, discoveries, tool invocations, and session outcomes. Answers: *"What happened during session X?"*
* **Preservation**: Historical logs are permanent and immutable. They are never overwritten; newer understanding supersedes but does not delete them.

### 3.4 Tier 3 — Candidate Memory & Staging
* **Contents**: `.agents/memory/inbox/*.json` and global inbox equivalent.
* **Semantics**: Quarantine zone for newly extracted learnings, observed tool patterns, and unverified agent hypotheses.
* **Safety Invariant (Invariant 3)**: Candidate objects are **inert**. They are invisible to regular retrieval until validated and promoted by the Memory Compiler.

### 3.5 Tier 4 — Canonical Semantic Memory
* **Contents**:
  - Project Scope: `.agents/memory/ARCHITECTURE.md`, `.agents/memory/DECISIONS.md`, `.agents/memory/GOTCHAS.md`.
  - Global Scope: `~/.gemini/antigravity-cli/memory/GENERAL.md`, `USER.md`, `ENVIRONMENT.md`.
  - Specialized Scopes: `domains/<domain>.md`, `tools/<tool>.md`.
* **Semantics**: The curated, durable knowledge repository of verified truths, architectural principles, user preferences, and platform gotchas.

### 3.6 Tier 5 — Procedural Memory
* **Contents**: `.agents/memory/procedural/*.md` and `.agents/skills/<skill-name>/SKILL.md`.
* **Semantics**: Step-by-step operational playbooks, test execution workflows, and toolchain runbooks.
* **Safety Invariant (Invariant 16)**: Procedural candidates remain inert until verified by end-to-end execution. Never automatically overwrite agent skills based solely on speculative LLM generation.

### 3.7 Tier 6 — Derived Retrieval Substrate
* **Contents**: Local embedding vectors, BM25 indices, Reciprocal Rank Fusion (RRF) pipelines, inverted token postings, and metadata filtering trees.
* **Semantics**: Accelerates search over Tier 4, Tier 5, and Tier 2 memory.
* **Disposability**: Fully disposable, derived state. Can be flushed and regenerated on demand.

### 3.8 Tier 7 — Evidence & Provenance
* **Contents**: Provenance metadata records linking memory entries to source artifacts: Git commit SHAs, file path + line ranges, CLI commands + exit codes, and test suite execution logs.
* **Semantics**: Explains *why* a memory is believed and *how* it was proven. Enables automatic staleness detection when underlying files change.

### 3.9 Tier 8 — Memory Control Plane
* **Contents**: Orchestration software in `scripts/`:
  - `memory_compiler.py`: Extraction, normalization, scoring, and candidate compilation.
  - `memory_reconciler.py`: Conflict detection, deduplication, and supersession.
  - `memory_index_queue.py`: Single-writer asynchronous WAL index update queue.
  - `memory_doctor.py`: Invariant verification, index synchronization, and health auditing.
  - `memory_feedback.py`: Telemetry & retrieval feedback logger.

---

## 4. Normalized Memory Record Model Schema

### 4.1 Schema Definition (v2.0.0)

Every durable memory record managed by the Memory OS conforms to the **Normalized Memory Record Model** (`schema_version: "2.0.0"`).

```yaml
schema_version: "2.0.0"
memory_id: "mem-20260903-171400-e4a1b2"
title: "Gradle Daemon Memory Exhaustion in Linux Codespaces"
type: "GOTCHA"
scope: "project"
status: "active"
content: "Running Gradle builds with default background daemons causes silent OOM kills in GitHub Codespaces due to the 8GB cgroup memory limit. Always append `--no-daemon` to `./gradlew` commands."
why: "GitHub Codespaces enforces strict container memory limits; multiple persistent Gradle daemon forks accumulate memory and trigger Linux kernel OOM killer."
evidence:
  source_type: "terminal_command"
  command: "./gradlew assembleDebug --no-daemon"
  exit_code: 0
  file_path: "/workspaces/codespaces-blank/AGENTS.md"
  line_start: 94
  line_end: 98
  commit_sha: "9f3b12c"
confidence: "HIGH"
confidence_score: 0.95
source: "file:///workspaces/codespaces-blank/AGENTS.md#L94-L98"
source_authority: "AUTHORITATIVE_REPO"
observed_at: "2026-09-03T12:00:00Z"
recorded_at: "2026-09-03T17:14:00Z"
valid_from: "2026-09-03T12:00:00Z"
valid_until: null
superseded_at: null
supersedes: "mem-20260815-091000-c8f2a1"
superseded_by: null
content_hash: "a8f5f167f44f4964e6c998dee827110c0160f4e1f86dc1a6f8812c332158866a"
author_agent: "Agent 1"
created_by: "lead-memory-architect"
tags: ["android", "gradle", "codespaces", "oom", "daemon"]
derived_from: ["sess-20260903-1200"]
related_to: ["mem-20260901-161600-b1c2d3"]
supports: ["mem-20260901-161600-b1c2d3"]
contradicts: []
```

### 4.2 Field Specifications

| Field Name | Type | Nullable | Required | Description / Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `schema_version` | String | No | Yes | Schema version identifier. Must be `"2.0.0"`. |
| `memory_id` | String | No | Yes | Globally unique ID format: `mem-<YYYYMMDD>-<HHMMSS>-<6-char-hash>`. |
| `title` | String | No | Yes | Concise, descriptive summary title (< 100 characters). |
| `type` | Enum | No | Yes | One of the 15 normalized memory types (Section 5). |
| `scope` | String | No | Yes | `project`, `global`, `domain:<name>`, `tool:<name>`, `session:<id>`. No null scope allowed. |
| `status` | Enum | No | Yes | `observed`, `candidate`, `validated`, `active`, `stale`, `superseded`, `deprecated`, `archived`, `rejected`. |
| `content` | String | No | Yes | Core factual claim, principle, or knowledge payload. |
| `why` | String | No | Yes | Operational rationale, context, root cause, or significance. |
| `evidence` | Object/String | No | Yes | Structured pointer to verifiable proof (command, file lines, test, commit). |
| `confidence` | Enum | No | Yes | Qualitative rating: `HIGH`, `MEDIUM`, `LOW`. |
| `confidence_score`| Float | No | Yes | Quantitative certainty metric: $[0.0, 1.0]$. |
| `source` | String | No | Yes | URI or locator string (e.g. `file:///path#L10-L20` or `git:commit_sha`). |
| `source_authority`| Enum | No | No | `AUTHORITATIVE_REPO`, `LIVE_TOOL`, `EXPLICIT_USER`, `INFERRED_AGENT`. |
| `observed_at` | ISO 8601 | No | Yes | Timestamp when the event/truth occurred in reality. |
| `recorded_at` | ISO 8601 | No | Yes | Timestamp when the record was created in the system. |
| `valid_from` | ISO 8601 | No | Yes | Start of temporal validity. |
| `valid_until` | ISO 8601 | Yes | Yes | End of validity. `null` indicates currently valid. |
| `superseded_at` | ISO 8601 | Yes | No | Timestamp when supersession occurred. |
| `supersedes` | String/List | Yes | Yes | `memory_id` of prior record(s) superseded by this record. |
| `superseded_by` | String | Yes | No | `memory_id` of newer record that replaced this one. |
| `content_hash` | String | No | Yes | SHA-256 hash of normalized `(title + content + scope)`. |
| `author_agent` | String | No | No | Identifier of agent who created candidate. |
| `created_by` | String | No | No | Role or workflow responsible for ingestion. |
| `tags` | List[String] | No | No | Normalized keyword tags for fast filtering. |
| `derived_from` | List[String] | Yes | No | Pointers to session IDs or transcript files. |
| `related_to` | List[String] | Yes | No | Pointers to associated memory IDs. |
| `supports` | List[String] | Yes | No | Memory IDs reinforced by this record. |
| `contradicts` | List[String] | Yes | No | Memory IDs conflicting with this record. |

### 4.3 Dual Markdown Serialization & Storage Formats

To guarantee human readability (Invariant 1) while supporting machine parsing, records are serialized in two standard formats:

#### Format A: Modular Frontmatter Document (for individual topic files)
Used for standalone skills, domain guides, and modular entries under `procedural/` or `inbox/`:
```markdown
---
schema_version: "2.0.0"
memory_id: "mem-20260903-171400-e4a1b2"
title: "Gradle Daemon Memory Exhaustion in Linux Codespaces"
type: "GOTCHA"
scope: "project"
status: "active"
confidence: "HIGH"
confidence_score: 0.95
observed_at: "2026-09-03T12:00:00Z"
valid_from: "2026-09-03T12:00:00Z"
valid_until: null
supersedes: "mem-20260815-091000-c8f2a1"
content_hash: "a8f5f167f44f4964e6c998dee827110c0160f4e1f86dc1a6f8812c332158866a"
---

# Gradle Daemon Memory Exhaustion in Linux Codespaces

### Content
Running Gradle builds with default background daemons causes silent OOM kills in GitHub Codespaces due to the 8GB cgroup memory limit. Always append `--no-daemon` to `./gradlew` commands.

### Why
GitHub Codespaces enforces strict container memory limits; multiple persistent Gradle daemon forks accumulate memory and trigger Linux kernel OOM killer.

### Evidence
- **Source:** [`AGENTS.md:L94-L98`](file:///workspaces/codespaces-blank/AGENTS.md#L94-L98)
- **Commit:** `9f3b12c`
- **Verification:** Live test execution passed.
```

#### Format B: Structured Bullet Block (for consolidated files)
Used in aggregated files such as `DECISIONS.md`, `GOTCHAS.md`, and `ARCHITECTURE.md`:
```markdown
- **[mem-20260903-171400-e4a1b2]** (2026-09-03) `[GOTCHA]` `{scope:project}` `{status:active}` **Gradle Daemon Memory Exhaustion in Linux Codespaces**
  - **Content:** Running Gradle builds with default background daemons causes silent OOM kills in GitHub Codespaces. Always append `--no-daemon`.
  - **Why:** Codespaces cgroup limit is 8GB; multiple daemons trigger kernel OOM.
  - **Evidence:** [`AGENTS.md:L94-L98`](file:///workspaces/codespaces-blank/AGENTS.md#L94-L98) | Commit: `9f3b12c`
  - **Validity:** `[2026-09-03 -> current]` | **Confidence:** HIGH (0.95)
  - **Lineage:** Supersedes `[mem-20260815-091000-c8f2a1]` | Hash: `a8f5f167`
```

### 4.4 Backward Compatibility Engine
The Memory OS maintains 100% backward compatibility with legacy v1.0 memory records:
```text
- [2026-09-01] [GOTCHA] (Durability 4): Never invoke Gradle daemon in Codespaces.
```
The parser in `scripts/memory_compiler.py` automatically migrates legacy entries into v2.0.0 model representations on read:
- `memory_id` = Generated deterministically from `mem-legacy-<date>-<hash(text[:32])>`
- `type` = Direct mapping (`GOTCHA` -> `GOTCHA`)
- `scope` = Inferred from file location (`.agents/memory/GOTCHAS.md` -> `project`)
- `status` = `"active"` (unless superseded tag detected)
- `confidence` = Derived from durability rating (Durability 4 -> `HIGH`, 0.80)
- `observed_at` = Date extracted from record (`2026-09-01T00:00:00Z`)
- `valid_from` = `2026-09-01T00:00:00Z`
- `valid_until` = `null`

---

## 5. Normalized Memory Types & Admission Rules

The Memory OS replaces informal category tags with **15 Normalized Semantic Memory Types**. Each type enforces strict admission criteria, durability ratings, storage locations, and validation rules.

```text
       CANDIDATE EXTRACTION
               │
               ▼
       5-GATE ADMISSION PIPELINE
       ┌─────────────────────────────────────────────────────────┐
       │ Gate 1: Security & Zero-Secrets Scan (Regex + Entropy)  │
       │ Gate 2: Evidence & Grounding Verification               │
       │ Gate 3: Deduplication & Near-Neighbor Analysis          │
       │ Gate 4: Contradiction & Temporal Lineage Check          │
       │ Gate 5: Authority & Multi-Scope Boundary Enforcement    │
       └────────────────────────────┬────────────────────────────┘
                                    │
                         ┌──────────┴──────────┐
                         ▼                     ▼
                      PASS                  FAIL
                         │                     │
                         ▼                     ▼
                Promote to Canonical      Reject / Quarantine
                Storage (Tiers 4-5)       in .agents/memory/inbox/
```

### 5.1 The 15 Normalized Memory Types

| Type Name | Durability Scale | Primary Storage Path | Admission Gate Criteria | Lifecycle & Revocation |
| :--- | :---: | :--- | :--- | :--- |
| **`EPHEMERAL`** | 0–1 | None (In-memory/turn context) | Discarded immediately. Routine tool outputs, acknowledgments, intermediate loops. | Expires at end of turn. Never persisted. |
| **`SESSION`** | 2 | `.agents/memory/sessions/` | Bound to active conversation. Records turn narrative, active work summary, handoffs. | Immutable historical record. Never promoted to persistent store unless distilled. |
| **`EVENT`** | 2–3 | `sessions/` or `PROJECT.md` | Significant system event (toolchain upgrade, benchmark run, outage, migration). Requires timestamp and log proof. | Retained as episodic milestone. |
| **`PROJECT`** | 3 | `.agents/memory/ARCHITECTURE.md` | Repo-specific conventions, build commands, directory structure. Requires live repo verification. | Overrides global scope. Superseded when repo structure shifts. |
| **`DOMAIN`** | 4 | `~/.gemini/antigravity-cli/memory/domains/` | Technology stack principles (e.g. WASM, Android NDK, Ghidra). Must generalize across projects. | Governed by domain toolchain verifications. |
| **`TOOL`** | 4 | `~/.gemini/antigravity-cli/memory/tools/` | CLI options, compiler quirks, tool flags. Must be verified via execution or official manual. | Superseded on tool major version upgrade. |
| **`FACT`** | 3–5 | Scoped target Markdown | Objective assertion about environment, library, or system. Strict proof required (log/file/hash). | Invalidated when underlying evidence file or config changes. |
| **`DECISION`** | 3–5 | `.agents/memory/DECISIONS.md` | Architectural choice, trade-off evaluation, ADR. Must include context, alternatives, and why. | Superseded only by deliberate new ADR or explicit decision entry. |
| **`GOTCHA`** | 3–4 | `.agents/memory/GOTCHAS.md` | Pitfall, silent failure, counter-intuitive behavior, edge case. Requires error logs + validated workaround. | Deprecated when upstream bug is patched and verified. |
| **`PROCEDURE`**| 3–4 | `.agents/memory/procedural/` | Multi-step operational playbook, runbook, or recovery script. Must execute successfully end-to-end. | Remains inert candidate until verified. |
| **`PREFERENCE`**| 5 | `~/.gemini/antigravity-cli/memory/USER.md` | Explicit user coding style, naming convention, or communication instruction. User prompt proof required. | Updated only upon explicit user command or instruction. |
| **`NEGATIVE_KNOWLEDGE`** | 3–5 | Target store (`GOTCHAS` / `DECISIONS`) | Documented failure mode, rejected library, or anti-pattern ("what NOT to do"). Requires failure proof. | Highly valued; prevents expensive cycles rediscovering dead ends. |
| **`CORRECTION`**| 3–5 | Scoped target store | Explicit remediation of agent error or inaccurate memory. Requires pointer to erroneous memory ID. | Immediately marks superseded record as `superseded`. |
| **`HANDOFF`** | 2–3 | `.agents/memory/sessions/` & `CURRENT.md` | Multi-agent delegation, pending blockers, and unfinished tasks. Requires target subagent/role. | Active until next session or receiving agent takes ownership. |
| **`GLOBAL`** | 5 | `~/.gemini/antigravity-cli/memory/GENERAL.md` | Universal cross-project standard, core organizational policy. Governed by `POLICY.md`. | Highest admission bar; requires cross-workspace durability. |

### 5.2 The 5-Gate Admission Pipeline

A candidate memory record $C$ extracted from agent experience must pass all 5 gates sequentially before admission into canonical Tier 4/5 storage:

#### Gate 1: Security & Zero-Secrets Filter (Non-negotiable Invariant 8)
- Candidate content, why, and evidence strings are scanned using deterministic high-entropy regex patterns and keyword matches:
  - Private keys (`BEGIN RSA PRIVATE KEY`, `ssh-ed25519`)
  - Tokens and API keys (`ghp_`, `gho_`, `AKIA`, `sk-`, `eyJ`)
  - Passwords, authorization headers, and bearer tokens
- **Action on Violation**: Immediate hard failure. Candidate is permanently rejected; zero-secrets alert is logged; candidate is erased from memory.

#### Gate 2: Evidence & Grounding Verification (Invariant 13 & 21)
- The candidate must possess concrete, non-empty `evidence` backed by an authoritative source:
  - File pointer (`file_path` + valid line bounds)
  - Live execution trace (CLI command with zero exit code or documented expected error)
  - Verifiable Git commit SHA
- Speculative agent assumptions ("I think library X might be faster") fail Gate 2 and are quarantined in `inbox/` as `status: "unverified"`.

#### Gate 3: Deduplication & Near-Neighbor Analysis
- **Exact Match**: If `content_hash(C) == content_hash(E)` for any existing active record $E$, operation is a `NOOP` (duplicate discarded).
- **Structural Match**: If `C.source == E.source` and claims identical facts, update `last_verified_at` of $E$ without creating redundant records.
- **Semantic Near-Neighbor**: If vector cosine similarity $\text{sim}(C, E) \ge 0.92$, the Memory Reconciler triggers merge analysis to synthesize refined knowledge rather than append clutter.

#### Gate 4: Contradiction & Temporal Lineage Gate (Invariant 6)
- The Reconciler evaluates whether $C$ contradicts an existing active record $E$:
  - If $C$ asserts a state incompatible with $E$, verify evidence timestamps and source authority.
  - If $C$ possesses newer `observed_at` and equal or higher `source_authority`, mark $E$ as `status: "superseded"`, set $E.\text{valid\_until} = C.\text{valid\_from}$, $E.\text{superseded\_by} = C.\text{memory\_id}$, and link $C.\text{supersedes} = E.\text{memory\_id}$.
  - Under no circumstances is historical record $E$ deleted. Lineage is permanently preserved.

#### Gate 5: Authority & Multi-Scope Boundary Gate (Invariant 7)
- Validates that $C$ is directed to its correct authoritative scope:
  - Project-specific code patterns are barred from global memory (`GENERAL.md`).
  - Global memory modifications require explicit governance compliance (`POLICY.md`).
  - Procedural skill proposals cannot modify `.agents/skills/` directly; they are routed to `.agents/memory/procedural/` until certified.

### 5.3 Candidate Scoring Formula
When ranking candidate entries for promotion, the Memory Compiler computes the deterministic candidate score:

$$\text{Score} = w_{nov} N + w_{dur} D + w_{ev} E + w_{rec} R + w_{ut} U + w_{sig} S + w_{rel} P - w_{red} \Omega - w_{unc} \Psi$$

Where:
- $N$ = Novelty score $[0, 1]$ (inverse vector proximity to existing cluster)
- $D$ = Durability rating $[0, 5]$ normalized to $[0, 1]$
- $E$ = Evidence strength $[0, 1]$ (CLI/Git test proof = 1.0; code inspection = 0.8; user assertion = 0.9; LLM inference = 0.2)
- $R$ = Recurrence frequency (occurrences across sessions)
- $U$ = Future utility estimation $[0, 1]$
- $S$ = Explicit user signal (1.0 if requested by user, else 0.0)
- $P$ = Project relevance $[0, 1]$
- $\Omega$ = Redundancy penalty $[0, 1]$
- $\Psi$ = Uncertainty / speculative phrasing penalty $[0, 1]$
- **Admission Threshold**: $\text{Score} \ge 0.70$ is required for automatic candidate promotion.

---

## 6. Bitemporal Validity Semantics & Multi-Scope Boundaries

### 6.1 Bitemporal Validity Semantics

To prevent temporal collapse, the Memory OS enforces two independent dimensions of time for every memory record:

```text
               REALITY / EVENT TIME (observed_at)
  ─────────────────────────────────────────────────────────────►
  Event Occurs in Reality                       Bug Workaround Verified
  (Commit 9f3b12c committed)                    (Test passes)
  t_obs1                                        t_obs2
        ▲                                             ▲
        │                                             │
  ──────┼─────────────────────────────────────────────┼────────►
        ▼                                             ▼
  t_rec1                                        t_rec2
  Recorded into Memory OS                       Superseding Record Recorded
               ASSERTION / SYSTEM TIME (valid_from -> valid_until)
```

1. **Reality Time (`observed_at`)**:
   - The timestamp when the phenomenon, bug, change, or fact actually occurred in the physical codebase or environment.
   - Grounded in Git commit timestamps, file modification times, or command execution timestamps.
2. **Assertion / System Time (`valid_from`, `valid_until`, `recorded_at`)**:
   - The timeframe during which the Memory OS considers this assertion to be valid and current.
   - `valid_from`: The moment the memory became authoritative.
   - `valid_until`: The moment the assertion was superseded, refuted, or deprecated. If the record is currently active, `valid_until = null`.
   - `recorded_at`: The physical system timestamp when the record was ingested into storage.

#### Query Capabilities Enabled by Bitemporality:
- **Current Truth Query**:
  $$\text{SELECT} * \text{WHERE } \text{status} = \text{'active'} \text{ AND } \text{valid\_until IS NULL}$$
  Answers: *"What is the true configuration right now?"*
- **Point-in-Time Historical Query (As-Of $T$)**:
  $$\text{SELECT} * \text{WHERE } \text{valid\_from} \le T \text{ AND } (T < \text{valid\_until} \text{ OR } \text{valid\_until IS NULL})$$
  Answers: *"What was our architectural belief on August 15th, 2026?"*
- **Belief Evolution Query**:
  $$\text{SELECT } \text{memory\_id, title, valid\_from, valid\_until, supersedes, why } \text{ORDER BY valid\_from ASC}$$
  Answers: *"How and why did our Android SDK build configuration change over time?"*

#### Code-Coupled Staleness Detection (Invariant 5 & 13)
When a memory record points to specific source code lines (`file_path: "src/auth.ts"`, `line_start: 45`, `line_end: 60`, `commit_sha: "a1b2c3d"`), the Memory OS evaluates Git freshness during retrieval:
1. If `git rev-parse HEAD` differs from `commit_sha`, inspect whether `git diff commit_sha..HEAD -- file_path` touched the referenced line range.
2. If lines were modified or deleted, the record's status is dynamically flagged as `status: "stale"`, and an evidence freshness alert is returned with the search hit.
3. Live repository state always overrides stale memory (Invariant 5).

### 6.2 Multi-Scope Retrieval Boundaries

Knowledge is partitioned into five strict hierarchical scopes. Scopes prevent context cross-contamination and guarantee security isolation.

```text
       ┌─────────────────────────────────────────────────────────┐
       │                      GLOBAL SCOPE                       │
       │   ~/.gemini/antigravity-cli/memory/                     │
       │   Universal standards, global preferences, environment  │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                   DOMAIN & TOOL SCOPES                  │
       │   domains/<domain>.md | tools/<tool>.md                 │
       │   Stack-specific patterns (Android, WASM, Ghidra, CMake)│
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                     PROJECT SCOPE                       │
       │   /workspaces/codespaces-blank/.agents/memory/          │
       │   Repo architecture, project decisions, local gotchas   │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                     SESSION SCOPE                       │
       │   .agents/memory/sessions/ & CURRENT.md                 │
       │   Active turn state, immediate blockers, episodic logs  │
       └─────────────────────────────────────────────────────────┘
```

#### Multi-Scope Boundary Rules:
1. **Explicit Scoping (Invariant 7)**: Every record must declare an explicit `scope` attribute (`project`, `global`, `domain:<name>`, `tool:<name>`, `session:<id>`). **"Null scope" is strictly prohibited.**
2. **Precedence Hierarchy**:
   $$\text{Active Session / CURRENT.md} \succ \text{Project Memory} \succ \text{Domain / Tool Memory} \succ \text{Global Memory}$$
   If a project decision in `.agents/memory/DECISIONS.md` conflicts with a global default in `~/.gemini/antigravity-cli/memory/GENERAL.md`, the **project-scoped decision unconditionally overrides the global default** for tasks within this repository.
3. **Query Route Scoping**:
   - Repository-specific questions (*"How do we run unit tests?"*) execute scoped queries: `scope IN ('project', 'session')`.
   - General tooling questions (*"What are Ghidra headless syntax options?"*) execute: `scope IN ('tool:ghidra', 'domain:reverse-engineering', 'global')`.
   - Query results always preserve and return their source `scope` tag.

---

## 7. Retrieval Substrate & Query Pipeline

### 7.1 MemSearch Hybrid Architecture
The Tier 6 retrieval engine utilizes **MemSearch** configured for local-first execution. It combines dense semantic retrieval with sparse BM25 lexical search, harmonized through Reciprocal Rank Fusion (RRF).

```text
                               QUERY: "Why did Gradle OOM kill the build?"
                                                │
                       ┌────────────────────────┴────────────────────────┐
                       ▼                                                 ▼
             DENSE SEMANTIC PATH                                SPARSE LEXICAL PATH
        (FastEmbed / Sentence-Transformers)                      (SQLite BM25 / RankBM25)
                       │                                                 │
                       ▼                                                 ▼
            Dense Vector Cosine Rank                                Lexical BM25 Rank
          [R_dense(1), R_dense(2), ...]                       [R_bm25(1), R_bm25(2), ...]
                       │                                                 │
                       └────────────────────────┬────────────────────────┘
                                                ▼
                                   RECIPROCAL RANK FUSION (RRF)
                                                │
                                                ▼
                                    EVIDENCE & FRESHNESS RERANKER
                                 Score * FreshnessBoost * AuthorityBoost
                                                │
                                                ▼
                                        METADATA FILTERING
                                   (Scope, Status != 'superseded')
                                                │
                                                ▼
                                     MAXIMAL MARGINAL RELEVANCE
                                      (Diversity Deduplication)
                                                │
                                                ▼
                                    COMPILED RETRIEVAL CONTEXT
                                   (Strict Token Budget < 1200 tokens)
```

### 7.2 Reciprocal Rank Fusion (RRF) Formulation
For any document $d \in D$, the hybrid score is calculated as:

$$\text{RRF}(d) = \sum_{m \in \{\text{dense}, \text{bm25}\}} \frac{w_m}{k + \text{rank}_m(d)}$$

Where:
- $k$ = Smoothing constant (default: 60)
- $w_{\text{dense}}$ = Weight assigned to dense semantic retrieval (default: 0.6)
- $w_{\text{bm25}}$ = Weight assigned to exact lexical retrieval (default: 0.4)
- $\text{rank}_m(d)$ = Ordinal rank of document $d$ in retrieval system $m$ ($1$-indexed)

### 7.3 Evidence-Aware Reranking
Following RRF score computation, candidates are adjusted by an evidence multiplier:

$$\text{FinalScore}(d) = \text{RRF}(d) \times M_{\text{auth}}(d) \times M_{\text{fresh}}(d) \times M_{\text{scope}}(d)$$

Where:
- $M_{\text{auth}}$ = Authority multiplier: $1.2$ for `AUTHORITATIVE_REPO` / verified test; $1.0$ for user assertion; $0.7$ for unverified.
- $M_{\text{fresh}}$ = Freshness multiplier: $1.0$ if Git commit unchanged; $0.5$ if code line range modified (`stale`).
- $M_{\text{scope}}$ = Scope relevance multiplier: $1.3$ for exact project match; $1.0$ for domain/tool; $0.8$ for global.

---

## 8. Compliance Matrix with Section 253 (22 Non-Negotiable Invariants)

The following matrix formally certifies how the Memory OS architecture complies with every invariant set forth in `Instruction.md` Section 253.

| Invariant # | Invariant Description | Architectural Enforcement Mechanism |
| :---: | :--- | :--- |
| **1** | Canonical memory remains human-readable. | All durable truth is stored in GitHub Flavored Markdown files (`.agents/memory/*.md`, `~/.gemini/.../*.md`). |
| **2** | Derived indexes are rebuildable. | Vector databases, BM25 indices, and caches are disposable; fully regenerable via `scripts/memory_engine.py --rebuild-index`. |
| **3** | A candidate is not automatically authoritative. | Candidates are isolated in Tier 3 (`inbox/`); inert until admitted by the 5-Gate Admission Pipeline. |
| **4** | A memory result is not automatically an instruction. | Memory context is presented as factual background data (`MEMORY_CONTEXT`); it cannot override prompt directives. |
| **5** | Current live evidence outranks stale memory. | Live Git state, filesystem checks, and test executions take unconditional priority over stored memory records. |
| **6** | History is preserved through supersession. | Records are never deleted on contradiction; older records are marked `superseded` and linked via `supersedes` lineage. |
| **7** | Scope boundaries are enforced. | Explicit scoping (`project`, `global`, `domain`, `tool`, `session`) is mandatory; cross-scope leakage is blocked by filters. |
| **8** | Secrets never enter durable memory or semantic indexes. | Deterministic high-entropy regex scanner (`scripts/secret_scanner.py`) filters all writes; hard failure on secrets. |
| **9** | Index failure cannot corrupt canonical memory. | Memory writes occur directly to Markdown via atomic rename before index updates are enqueued; index crashes do not corrupt files. |
| **10** | Automatic writes are idempotent. | Content hashing (`content_hash`) prevents duplicate record creation; reapplying the same write produces a `NOOP`. |
| **11** | Expensive work is deferred out of hot hooks. | Embedding generation and deep indexing are offloaded to an asynchronous background index queue (`scripts/memory_index_queue.py`). |
| **12** | Unknown is a valid answer. | When retrieval confidence falls below threshold ($< 0.40$), the search system outputs `No matching memory found` rather than hallucinating. |
| **13** | Evidence must be fresh enough for the claim being made. | Git tree comparison detects modified lines; code-coupled memories are invalidated or marked `stale` if underlying files changed. |
| **14** | The semantic layer can be disabled without destroying memory. | If MemSearch/embeddings are disabled, the system falls back seamlessly to deterministic lexical regex search over Markdown. |
| **15** | No learned ranking policy becomes authoritative without evaluation. | Search weights and scoring models remain fixed unless validated against the regression benchmark suite (`scripts/memory_benchmark.py`). |
| **16** | No generated procedural skill becomes active without admission path. | Skills generated by agents are staged in `.agents/memory/procedural/` and require live CLI test verification before becoming active. |
| **17** | Every major automatic mutation is auditable. | Every compiler admission, merge, and supersession writes a structured entry to `.agents/memory-upgrade/audit/mutations.jsonl`. |
| **18** | Tests must independently verify behavior. | Automated test suites in `tests/test_memory_os.py` execute independent end-to-end verification of all memory operations. |
| **19** | Passing tests do not excuse stale architecture documentation. | `SPEC.md`, `ADR-002`, and `docs/architecture.md` are updated and checked for drift during memory health audits. |
| **20** | Green health report must correspond to consistent evidence. | `scripts/memory_doctor.py` validates index checksums, missing file pointers, and unlinked supersessions before returning 0. |
| **21** | Agent may automate implementation, but may not fabricate proof. | Provenance pointers require verifiable filesystem paths, Git commit SHAs, or exit codes; synthesized evidence is rejected. |
| **22** | System must remain understandable to future agents. | Clean directory layout, standardized frontmatter schemas, explicit ADRs, and clear architectural boundaries ensure agent legibility. |

---

## 9. Live Repository Topology & Component Integration

### 9.1 Filesystem Mapping

The Memory OS is mapped to the current repository structure without creating redundant directories:

```text
/workspaces/codespaces-blank/
├── .agent-state/
│   ├── indexes/                # Derived MemSearch vector store & BM25 tables (disposable, .gitignored)
│   ├── queue/                  # Asynchronous index update WAL files (.gitignored)
│   └── telemetry/              # Retrieval feedback and latency logs
│
├── .agents/
│   ├── memory/
│   │   ├── INDEX.md            # Canonical Project Memory Routing Index
│   │   ├── CURRENT.md          # Tier 1 Active Working State (< 30 lines)
│   │   ├── ARCHITECTURE.md     # Tier 4 Canonical Project Architecture Facts
│   │   ├── DECISIONS.md        # Tier 4 Canonical Architectural Decisions
│   │   ├── GOTCHAS.md          # Tier 4 Canonical Project Gotchas & Pitfalls
│   │   ├── inbox/              # Tier 3 Candidate Memory Quarantine Staging
│   │   ├── procedural/         # Tier 5 Procedural Runbooks & Candidate Skills
│   │   └── sessions/           # Tier 2 Episodic Session Logs (YYYY-MM-DD-HHMM.md)
│   │
│   ├── memory-upgrade/
│   │   ├── SPEC.md             # This Master Architecture Specification
│   │   ├── PLAN.md             # Multi-Phase Upgrade Execution Plan
│   │   ├── ACCEPTANCE.md       # Acceptance Criteria & Verification Checklist
│   │   ├── audit/              # Forensic baseline audits and mutation logs
│   │   ├── benchmarks/         # Retrieval quality & latency benchmark results
│   │   ├── evidence/           # Test execution and verification artifacts
│   │   └── decisions/
│   │       └── ADR-002-memory-os.md # Architectural Decision Record for Memory OS
│   │
│   ├── hooks.json              # Deterministic Lifecycle Hooks (PreInvocation, PreToolUse, PostToolUse, Stop)
│   └── skills/                 # Agent Skills (memory-start, memory-end, memory-promote, memory-search, memory-audit)
│
├── scripts/
│   ├── memory_engine.py        # Master Memory Engine CLI (/start-session, /end-session, /promote-memory)
│   ├── memory_compiler.py      # Candidate extraction, normalization, and scoring
│   ├── memory_reconciler.py    # Deduplication, conflict analysis, and supersession
│   ├── memory_index_queue.py   # Asynchronous index update worker & queue
│   ├── memsearch_backend.py    # MemSearch hybrid retrieval adapter (Dense + BM25 + RRF)
│   ├── memory_doctor.py        # Health auditor & invariant verification engine
│   ├── memory_feedback.py      # Telemetry & retrieval feedback logger
│   ├── secret_scanner.py       # Zero-secrets regex & entropy scanner
│   ├── detect_contradictions.py# Contradiction detection engine
│   └── compact_memory.py       # CURRENT.md compaction utility
│
└── ~/.gemini/antigravity-cli/memory/  # Tier 4 Global Durable Memory (POLICY.md, GENERAL.md, USER.md, ENVIRONMENT.md)
```

### 9.2 Lifecycle Hook Integration
The Memory OS integrates into the deterministic hooks defined in `.agents/hooks.json`:
1. **`PreInvocation` (`scripts/hooks/pre_invocation.py`)**:
   - Reads `CURRENT.md` to establish active objective.
   - Evaluates memory index health (`memory_doctor.py --quick-check`).
   - Executes scoped retrieval compiler if query context requires background memory.
2. **`PreToolUse` (`scripts/hooks/pre_tool_use.py`)**:
   - Acts as security gatekeeper; intercepts `write_to_file`, `replace_file_content`, and memory mutation commands to block credential leakage.
3. **`PostToolUse` (`scripts/hooks/post_tool_use.py`)**:
   - Observes execution events (test passes/failures, build errors).
   - If an event matches a candidate extraction pattern (e.g. fatal bug resolved), emits candidate record to `.agents/memory/inbox/`.
4. **`Stop` (`scripts/hooks/stop_guard.py`)**:
   - Flushes pending index update queues.
   - Verifies that `CURRENT.md` is compacted and no background memory tasks are dangling.

---

## 10. Verification, Testing & Certification Plan

In compliance with Invariants 18, 20, and 21, the Memory OS specification mandates automated end-to-end verification:
1. **Schema Validation Test**: Validate that all existing and generated records strictly conform to the 16-field v2.0.0 JSON schema.
2. **5-Gate Admission Test**: Test synthetic candidates (secret payload, ungrounded speculation, exact duplicate, direct contradiction, out-of-scope assertion) to verify 100% rejection accuracy.
3. **Disposability & Rebuild Test**: Purge all derived vector indexes, trigger `rebuild_indexes()`, and verify that search results are bitwise identical.
4. **Bitemporal Lineage Test**: Create a superseding memory record; verify that the old record receives `valid_until` and `superseded_by`, and that as-of point-in-time queries return correct historical records.
5. **Secret Scanner Integrity Test**: Attempt to write 25 known test API tokens/keys; confirm 100% interception and zero leaked files.
6. **Doctor Invariant Audit**: Run `python3 scripts/memory_doctor.py --verify-all` to ensure all 22 invariants evaluate to `PASS`.

---
*Signed and Certified by:*  
**Lead Memory Architect (Agent 1)**  
*Antigravity Autonomous Engineering Systems*  
`2026-09-03T17:14:47Z`
