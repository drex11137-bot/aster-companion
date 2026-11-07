# ADR-003: Memory OS Phase 2 Governance, Canonical Markdown Supremacy & Disposable Vector Index Invariants

* **Document ID:** AGY-ADR-003  
* **Status:** Accepted / Authoritative Architecture Directive  
* **Date:** 2026-09-04  
* **Author:** Lead Memory Architect (Agent 1)  
* **Deciders:** Lead Memory Architect (Agent 1), Antigravity Autonomous Engineering Systems Phase 2  
* **Consulted:** `instruction.md` Sections 10–24, 138 (25 Non-Negotiable Invariants); `SPEC.md` v2.0.0; `ADR-002-memory-os.md`; `~/.gemini/antigravity-cli/memory/POLICY.md`  
* **Extends:** ADR-002 (Semantic + Evidence-Gated Memory OS Upgrade)  
* **Supersedes:** Any informal or ungrounded memory ingestion practices; legacy single-scalar confidence ratings; synchronous hook-blocking index writes.

---

## 1. Context & Problem Statement

In Phase 1 of the Antigravity Memory OS upgrade, the repository transitioned from flat, unstructured text documents queried via `ripgrep` to an 8-tier evidence-gated memory system with a local hybrid retrieval substrate (MemSearch: dense semantic embeddings + sparse BM25 lexical search).

However, forensic audits of real-world multi-agent memory systems have exposed three critical architectural failure modes:

1. **The Vector Store Authority Inversion Trap**: Over time, agent implementations begin treating the vector database (Milvus Lite / FAISS / SQLite-VSS) as the primary store of truth. When vector databases corrupt, drop indexes, or run out of memory, agents suffer catastrophic amnesia or begin hallucinating because the vector database was not strictly disposable.
2. **Synchronous Hook Blocking & Hidden Indexing Failures**: Previous agents attempted to embed memories synchronously inside hot execution hooks (`PreToolUse`, `PostToolUse`), leading to high latency spikes and unhandled race conditions. To mask these failures, authors frequently appended `|| true` or silent `except: pass` blocks, creating a facade of health while the index silently drifted from reality.
3. **Speculative Candidate Infiltration & Confidence Collapse**: Without rigid admission gating, speculative agent thoughts ("I believe library X might work") were promoted directly into permanent memory. Furthermore, collapsing confidence into a single floating-point number conflated relevance with truth, allowing highly similar but demonstrably false memories to outrank verified codebase facts.

Phase 2 requires a binding, uncompromising architectural decision that establishes **Canonical Markdown Supremacy**, guarantees the **complete disposability and rebuildability of the derived retrieval substrate**, and enforces all **25 Non-Negotiable Invariants** from `instruction.md`.

---

## 2. Decision Drivers & Invariants

This decision is governed unconditionally by the **25 Non-Negotiable Invariants** set forth in `instruction.md` Section 138 and the foundational principles of `SPEC.md` v2.0.0:

* **Invariant 1 & 2 (Canonical Markdown Supremacy & Failure Isolation)**: Canonical memory must remain human-readable Markdown. Index failure, vector DB corruption, or model unavailability cannot corrupt or destroy canonical memory.
* **Invariant 3, 13 & 21 (Evidence-Gated Admission & Provenance)**: Candidates are inert until validated by a 5-gate pipeline. Memory writes must be idempotent based on content hashing. Every durable claim must possess auditable provenance.
* **Invariant 5, 6 & 7 (History Preservation & Contradiction Resolution)**: Historical state is never deleted; facts evolve through explicit supersession lineages (`valid_until`, `supersedes`). Contradictions are resolved through temporal precedence or explicitly marked `CONTESTED`.
* **Invariant 8 & 9 (Hybrid Retrieval & Explicit Abstention)**: Retrieval combines dense embeddings and BM25 lexical search via Reciprocal Rank Fusion (RRF). When retrieval confidence falls below threshold (< 0.40), the system must explicitly abstain rather than hallucinate.
* **Invariant 10 (Explicit Scope Boundaries)**: Scopes (`project`, `global`, `domain`, `tool`, `session`) are mandatory; null scope is banned. Project memory unconditionally overrides global defaults on repository-specific decisions.
* **Invariant 11, 12 & 15 (Observable Health, Rebuildability & No Masked Errors)**: Index health must be explicitly reported across 6 states (`HEALTHY`, `STALE`, `DEGRADED`, `FAILED`, `MISSING`, `REBUILDING`). The entire index must be rebuildable via a single command. Hooks must never swallow persistence or indexing failures.
* **Invariant 14 (Concurrency Safety)**: Advisory file lease locks and atomic file replacements (`os.replace` via temporary files) prevent multi-agent race conditions.
* **Invariant 16 & 18 (Security, Inertness & Negative Knowledge)**: Zero secrets in durable memory. Retrieved context is inert data (`[MEMORY]`), preventing instruction injection. Known bugs and anti-patterns are preserved as negative knowledge.

---

## 3. Considered Architectural Alternatives

### Alternative 1: Vector Database as Single Source of Truth with Markdown Export
* **Description**: Write all candidate and durable memories directly into Milvus / Chroma / SQLite-VSS; periodically dump markdown files for human inspection.
* **Critique**: Violates Invariants 1, 2, and 12. Vector databases are opaque binary files that create Git merge conflicts, cannot be diffed cleanly, and cause irreversible data loss upon file lock or corruption.
* **Verdict**: **Strictly Prohibited & Permanently Rejected.**

### Alternative 2: Synchronous Dual-Write (Simultaneous Markdown & Vector Ingestion)
* **Description**: In every hook or tool call, write simultaneously to Markdown and immediately execute embedding generation into Milvus.
* **Critique**: Violates Invariant 11 and 15. Generating local embeddings (ONNX `bge-m3`) takes 200–800ms per text block. Doing this in hot hooks severely degrades agent responsiveness and creates high lock contention when concurrent subagents execute.
* **Verdict**: **Rejected.**

### Alternative 3: Asynchronous Single-Writer WAL Architecture with Canonical Markdown Supremacy (Selected)
* **Description**:
  1. All mutations execute directly against canonical Markdown files using POSIX atomic rename (`os.replace`) protected by advisory file locks.
  2. Memory writes immediately append an indexing task to a persistent Write-Ahead Log (WAL) queue (`.agents/memory/index_queue.jsonl`).
  3. A single-writer background worker acquires an exclusive lease (`index_writer.lease.lock`) to drain the queue into the derived MemSearch Milvus Lite backend.
  4. If Milvus fails, crashes, or is purged via `rm -rf`, canonical memory is completely unaffected. A single command (`python3 scripts/memory_engine.py --rebuild-index`) rebuilds all embeddings and indexes from scratch.
* **Verdict**: **Accepted as the Authoritative Standard for Phase 2.**

---

## 4. Architectural Directives & Governance Rules

### Directive 4.1: The Canonical Markdown Supremacy Principle
1. **Source of Truth**: The human-readable Markdown documents located in `.agents/memory/*.md` (project scope) and `~/.gemini/antigravity-cli/memory/*.md` (global scope) constitute the sole, authoritative representation of durable agent knowledge.
2. **Secondary Status of Vector Stores**: Vector embeddings, Milvus database collections, HNSW graphs, inverted token postings, and SQLite search tables are classified strictly as **ephemeral, derived retrieval caches**.
3. **Disaster Recovery Contract**:
   - Deleting `.agents/memory/.memsearch/` or `.agent-state/indexes/` must result in **zero loss of knowledge**.
   - Running:
     ```bash
     python3 scripts/memory_engine.py --rebuild-index
     ```
     must deterministically reparse all canonical Markdown documents, re-extract chunks, compute embeddings, and restore the search index to full operational health.

### Directive 4.2: Derived Vector Index Isolation & Error Handling
1. **Failure Isolation**: A crash, corrupted lock, missing ONNX model, or cgroup OOM termination in the vector backend must never halt agent tool execution, nor corrupt canonical files.
2. **Graceful Fallback**: If the semantic retrieval substrate is unavailable or marked `DEGRADED`, the search layer must automatically fall back to deterministic lexical regex search (`search_memory.py`) over Markdown files without failing the user prompt.
3. **No Error Suppression**: Under no circumstances may hook scripts or indexing workers execute shell idioms like `memsearch index ... || true` or catch exceptions without logging. Indexing failures must be recorded in `.agents/memory/index_health.json` with an incremented `failure_count` and state set to `DEGRADED` or `FAILED`.

### Directive 4.3: Strict 8-Tier Memory Model Governance
The system enforces strict operational boundaries across the 8 memory tiers defined in `SPEC.md`:
* **Tier 0 (Governance)**: `AGENTS.md`, `POLICY.md`, `GEMINI.md`. Authoritative behavioral boundaries; read-only during normal tasks.
* **Tier 1 (Working State)**: `.agents/memory/CURRENT.md`. High-velocity state strictly capped at **< 30 lines**. Historical logs in `CURRENT.md` are prohibited; `scripts/compact_memory.py` enforces compaction.
* **Tier 2 (Episodic Memory)**: `.agents/memory/sessions/YYYY-MM-DD-HHMM.md`. Immutable, append-only narrative logs of sessions and handoffs.
* **Tier 3 (Candidate Memory)**: `.agents/memory/inbox/candidates.jsonl`. Staging quarantine. Candidate objects are **inert**; they are invisible to standard retrieval until admitted by the 5-Gate Pipeline.
* **Tier 4 (Canonical Semantic Memory)**: `ARCHITECTURE.md`, `DECISIONS.md`, `GOTCHAS.md`, `INDEX.md`. Curated durable repository knowledge conforming to Normalized Model v2.0.0.
* **Tier 5 (Procedural Memory)**: `.agents/memory/procedural/` and `.agents/skills/`. Reusable runbooks and diagnostic workflows. Candidate procedures must remain inert in `inbox/procedures/` until certified by live execution.
* **Tier 6 (Derived Retrieval Substrate)**: MemSearch dense embeddings + BM25 indices. Fully disposable and regenerable.
* **Tier 7 (Evidence & Provenance)**: Verifiable links to Git commits, line ranges, and CLI execution logs.
* **Tier 8 (Memory Control Plane)**: The orchestration engine (`scripts/memory_compiler.py`, `scripts/memory_reconciler.py`, `scripts/memory_index_queue.py`, `scripts/memory_doctor.py`, `scripts/learning_loop.py`).

### Directive 4.4: 5-Gate Evidence-Gated Admission Pipeline
Every candidate record $C$ extracted by the Candidate Bus must pass all 5 gates sequentially before being written to Tier 4 or Tier 5 storage:
1. **Gate 1 — Security & Zero-Secrets Scan**: Scanned via `scripts/secret_scanner.py` using high-entropy regex patterns (API keys, private keys, authorization tokens). Any finding causes immediate hard rejection and quarantine in `rejected_secrets.jsonl`.
2. **Gate 2 — Evidence & Grounding Verification**: Requires non-empty, verifiable proof (Git commit SHA, file line range, terminal command exit code). Speculative agent musings fail Gate 2 and remain unpromoted.
3. **Gate 3 — Deduplication Analysis**: Exact content hash collisions (`content_hash`) trigger a `NOOP` (updating `last_verified_at`). Semantic similarity $\ge 0.92$ triggers non-destructive merge synthesis.
4. **Gate 4 — Contradiction & Temporal Lineage**: Evaluates whether $C$ contradicts active fact $E$. If $C$ is newer and has equal or higher source authority, $E$ is marked `superseded` (`valid_until = now`), and $C$ links `supersedes = E.memory_id`. Historical records are never deleted.
5. **Gate 5 — Authority & Multi-Scope Boundary**: Enforces explicit scoping (`project`, `global`, `domain:<name>`, `tool:<name>`). Project memory overrides global memory.

### Directive 4.5: Decoupled Multi-Dimensional Trust & Explicit Abstention
1. **Decoupled Trust Dimensions**: Scalar confidence is forbidden. The system tracks 6 orthogonal dimensions: `epistemic_confidence`, `source_authority`, `freshness`, `retrieval_relevance`, `importance`, `durability`.
2. **Relevance $\ne$ Truth**: A highly similar vector match from an unverified agent thought must never outrank a less similar but strongly evidenced repository test.
3. **Explicit Abstention (Invariant 9)**: When search results yield a maximum confidence below the threshold ($0.40$), the Query Router must return an explicit abstention (`abstained: True`, message: `"No sufficiently trustworthy memory found"`) instead of synthesizing speculative facts.

### Directive 4.6: Single-Writer Asynchronous WAL Index Queue
1. **Atomic Write First**: All Markdown writes occur via `lock_manager.atomic_write()` (write to temporary file on the same filesystem, followed by POSIX atomic `os.replace`).
2. **WAL Queue Enqueue**: Upon successful file write, an indexing task is appended to `.agents/memory/index_queue.jsonl`.
3. **Leased Worker**: A background worker acquires the exclusive advisory lease `.agents/memory/index_writer.lease.lock` (with a 30-second stale lease timeout) to drain queued files into Milvus. Rapid sequential writes to the same file are coalesced into a single reindex pass.

---

## 5. System Consequences & Trade-Offs

### Positive Consequences
* **Total Disaster Recovery**: The entire retrieval substrate can be purged or corrupted without risking permanent loss of agent learnings.
* **Deterministic Auditability**: Every durable fact traces back to a specific session, commit, command, and author agent. Git diffs clearly display memory evolution.
* **Elimination of Silent Failures**: Explicit index health states (`HEALTHY`, `STALE`, `DEGRADED`, `FAILED`, `MISSING`, `REBUILDING`) and observable telemetry ensure drift is detected immediately.
* **Zero Credential Leakage**: Multi-layer pre-write scanning ensures tokens and credentials never enter durable Markdown files or vector embeddings.

### Negative Consequences & Trade-Offs
* **Asynchronous Indexing Latency**: Memories written to Markdown are not instantaneously present in the dense vector index until the WAL queue drains (typical latency: 50–500ms).  
  * *Mitigation*: The lexical search engine (`search_memory.py`) queries live Markdown files directly, guaranteeing zero latency for exact keyword retrieval.
* **Local Compute Consumption**: Local ONNX embeddings (`bge-m3`) utilize container CPU cores.  
  * *Mitigation*: Indexing is deferred out of hot execution hooks and processed in batches by the single-writer queue.

---

## 6. Verification, Testing & Certification Contract

To certify compliance with ADR-003, the repository mandates continuous automated verification:

1. **Memory Doctor Invariant Diagnostics**:
   ```bash
   python3 scripts/memory_doctor.py --json
   ```
   Must verify that all 6 health predicates evaluate to `PASS`:
   - `canonical_valid`: All canonical files adhere to schema and line bounds.
   - `no_blocking_security`: Zero secrets detected by Gitleaks and regex scanner.
   - `no_index_corruption`: Milvus Lite collections and manifest files are coherent.
   - `no_schema_corruption`: Metadata conforms to schema v2.0.0.
   - `no_contradiction`: Zero unmanaged conflicting facts.
   - `required_indexes_current`: Canonical Git revisions match indexed revisions.
2. **Adversarial & Chaos Testing Suite**:
   ```bash
   python3 -m unittest tests/test_memory_os_adversarial.py
   python3 -m unittest tests/test_chaos_recovery.py
   ```
   Validates index recovery following simulated worker kill, vector database lock corruption, and adversarial prompt-injection payloads.
3. **Disposability & Rebuild Certification**:
   Purging `.agents/memory/.memsearch/` and executing `scripts/memory_index_queue.py --rebuild` must restore 100% of canonical chunks to `HEALTHY` state.

---

*Certified and Approved by:*  
**Lead Memory Architect (Agent 1)**  
*Antigravity Autonomous Engineering Systems — Phase 2*  
`2026-09-04T07:20:00Z`
