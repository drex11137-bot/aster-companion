# ADR-002: Semantic + Evidence-Gated Memory OS Upgrade

* **Status:** Accepted / Approved  
* **Date:** 2026-09-03  
* **Author:** Agent 1 — Lead Memory Architect  
* **Deciders:** Lead Memory Architect (Agent 1), Antigravity Autonomous Engineering Systems  
* **Consulted:** `Instruction.md` Sections 5–7, 15, 16, 26, 86, 110, 180, 216, 253; `AGENTS.md`; `~/.gemini/antigravity-cli/memory/POLICY.md`  
* **Supersedes:** ADR-001 (Legacy Flat Markdown Keyword-Grep Memory Architecture)

---

## 1. Context & Problem Statement

Autonomous pair-programming agents require long-term memory across sessions, projects, and toolchain configurations. The legacy memory system in this repository was built on flat Markdown documents (`.agents/memory/*.md`, `~/.gemini/antigravity-cli/memory/*.md`) accessed via keyword regex grep (`ripgrep`) and manual memory promotion.

While flat Markdown files have the virtue of being human-readable and Git-friendly, forensic analysis identified five critical architectural deficiencies:

1. **Semantic Recall Failure**: Keyword queries fail whenever the agent uses synonyms or searches for conceptual abstractions (e.g. querying *"daemon memory crash"* fails to match a note documenting *"Gradle background process killed by cgroups limit"*).
2. **Temporal Collapse & Stale Contamination**: Memory records lacked temporal grounding. Stale discoveries (such as an obsolete SDK version or a temporary workaround) persisted indefinitely alongside current truths, causing agents to reproduce resolved issues.
3. **Hallucinatory Ingestion & Lack of Evidence Gating**: Agent observations and speculative reasoning were frequently promoted directly into canonical memory without objective verification, polluting persistent state with inaccurate assumptions.
4. **Contradiction Accumulation Without Lineage**: Conflicting records accumulated silently across files without explicit supersession links (`supersedes`, `valid_until`), leaving the agent unable to determine which statement is current.
5. **Context Bloat & Vulnerability**: Loading large unindexed memory files bloated context windows, degraded reasoning performance, and increased the attack surface for accidental credential leakage.

We require a modernized **Memory Operating System** that introduces dense semantic search and automated candidate ingestion while preserving absolute human readability, git-native auditing, and zero-secrets security.

---

## 2. Decision Drivers & Invariants

The architectural decision must strictly comply with all **22 Non-Negotiable Invariants** specified in `Instruction.md` Section 253, specifically:

* **Canonical Markdown Authority (Invariants 1 & 2)**: Canonical memory must remain human-readable Markdown. Derived vector databases, BM25 tables, and caches must be 100% disposable and deterministically rebuildable.
* **Evidence-Gated Admission (Invariants 3, 13 & 21)**: Speculation is not memory. Every durable record must be grounded in verified live evidence (Git commit, test run, CLI exit code, or explicit user command).
* **Bitemporal Validity & History Preservation (Invariants 5 & 6)**: The system must track both reality time (`observed_at`) and assertion time (`valid_from` to `valid_until`). History is never deleted; contradiction resolves into explicit supersession.
* **Multi-Scope Isolation (Invariant 7)**: Strict scope boundaries (`project`, `global`, `domain`, `tool`, `session`) must prevent context leakage and guarantee project precedence.
* **Zero-Secrets Security (Invariant 8)**: No credentials, tokens, or private keys may ever enter durable memory or semantic indexes.
* **Fault-Tolerant Read/Write Paths (Invariants 9 & 14)**: Index corruption or vector engine failure must never corrupt canonical memory or block agent execution.

---

## 3. Considered Architectural Alternatives

### Alternative 1: Status Quo (Flat Markdown + ripgrep)
* **Description**: Continue relying solely on flat `.md` files queried via `rg` keyword search.
* **Advantages**: Minimal complexity; zero external dependencies; human-readable; native Git versioning.
* **Disadvantages**: Zero semantic discovery; prone to duplicate notes; manual promotion burden; no temporal invalidation; high hallucination risk.
* **Verdict**: **Rejected.** Unviable for autonomous, multi-session software engineering.

### Alternative 2: External / Managed Cloud Vector Database (e.g. Pinecone, Weaviate Cloud, Qdrant Cloud)
* **Description**: Store memory embeddings and metadata in an external cloud vector database.
* **Advantages**: High scalability; managed vector search infrastructure.
* **Disadvantages**:
  - Requires cloud API credentials and network egress, violating the Codespaces local-first constraint and increasing security attack surface.
  - Inverts the authority model: the cloud database becomes the source of truth, breaking Git traceability and offline reproducibility.
* **Verdict**: **Rejected.** Incompatible with local-first, zero-secrets security requirements.

### Alternative 3: Monolithic Vector Store as Primary Source of Truth with Markdown Export
* **Description**: Ingest memory directly into a local embedded vector database (e.g. SQLite-VSS, ChromaDB), generating Markdown files merely as export views.
* **Advantages**: High write speed; tightly coupled embeddings.
* **Disadvantages**:
  - Directly violates Invariant 1 and Invariant 2.
  - Vector database files are opaque binary blobs that produce unreadable Git diffs and merge conflicts.
  - Index corruption destroys the primary knowledge base.
* **Verdict**: **Rejected.** Opaque state destroys system inspectability.

### Alternative 4: Hybrid Semantic + Evidence-Gated Memory OS with Canonical Markdown Authority (Chosen)
* **Description**:
  - Canonical Markdown remains the sole, human-readable, Git-versioned source of truth.
  - A derived, disposable retrieval substrate (**MemSearch**) provides hybrid dense vector + BM25 lexical search combined via Reciprocal Rank Fusion (RRF).
  - A 5-gate admission pipeline isolates unverified candidates in `.agents/memory/inbox/` until verified.
  - A normalized 16-field bitemporal schema models validity, lineage, and provenance.
* **Advantages**: Fulfills all 22 non-negotiable invariants; total disaster recovery (indexes rebuildable from Markdown in seconds); zero-secrets filter; explainable, evidence-backed memories.
* **Disadvantages**: Requires local embedding runtime and asynchronous index synchronization.
* **Verdict**: **Accepted.** Optimal balance of semantic power, rigorous safety, and architectural durability.

---

## 4. Decision Outcome & Key Architectural Decisions

We adopt **Alternative 4: The Antigravity Memory OS**. The system comprises eight distinct architectural decisions:

### Decision 4.1: The 8-Tier Memory Hierarchy
We establish the 8-tier functional architecture defined in `SPEC.md`:
* **Tier 0 — Governance**: Rules, policies, security boundaries (`GEMINI.md`, `AGENTS.md`, `POLICY.md`).
* **Tier 1 — Active Working State**: High-velocity mutable task state (`CURRENT.md` < 30 lines).
* **Tier 2 — Episodic Memory**: Chronological session logs (`sessions/`).
* **Tier 3 — Candidate Memory**: Isolated quarantine staging for unverified discoveries (`inbox/`).
* **Tier 4 — Canonical Semantic Memory**: Verified truths, decisions, gotchas, architecture (`DECISIONS.md`, `GOTCHAS.md`).
* **Tier 5 — Procedural Memory**: Validated operational runbooks and skills (`procedural/`).
* **Tier 6 — Derived Retrieval Substrate**: MemSearch dense embeddings + BM25 indices (disposable).
* **Tier 7 — Evidence & Provenance**: Grounded pointers to Git commits, line ranges, and execution traces.
* **Tier 8 — Memory Control Plane**: Orchestration engine (`scripts/memory_compiler.py`, `scripts/memory_reconciler.py`, `scripts/memory_index_queue.py`, `scripts/memory_doctor.py`).

### Decision 4.2: Canonical Markdown Authority & Disposable Substrate
Canonical Markdown files are the single source of truth. All vector stores, BM25 indices, and caches located under `.agent-state/indexes/` are strictly derived and disposable. A full rebuild can be triggered at any time via:
```bash
python3 scripts/memory_engine.py --rebuild-index
```
Vector index corruption or absence will never crash or halt agent operations; the retrieval engine falls back gracefully to deterministic lexical search.

### Decision 4.3: Normalized 16-Field Memory Record Model (v2.0.0)
Every memory record implements the normalized schema:
`schema_version`, `memory_id`, `title`, `type`, `scope`, `status`, `content`, `why`, `evidence`, `confidence`, `confidence_score`, `source`, `observed_at`, `valid_from`, `valid_until`, `supersedes`, `content_hash`.
Existing legacy records (`- [YYYY-MM-DD] [TYPE] (Durability N): text`) are parsed and upgraded dynamically on read via the backward compatibility engine.

### Decision 4.4: 15 Normalized Types & 5-Gate Admission Pipeline
We normalize memory into 15 semantic types: `EPHEMERAL`, `SESSION`, `EVENT`, `PROJECT`, `DOMAIN`, `TOOL`, `FACT`, `DECISION`, `GOTCHA`, `PROCEDURE`, `PREFERENCE`, `NEGATIVE_KNOWLEDGE`, `CORRECTION`, `HANDOFF`, `GLOBAL`.
Candidates extracted from agent experience are staged in `.agents/memory/inbox/` and must pass all five admission gates:
1. **Security & Zero-Secrets Gate** (deterministic entropy and regex scanning).
2. **Evidence & Grounding Gate** (verifiable CLI, Git, or file pointer).
3. **Deduplication Gate** (exact content hash and cosine distance analysis).
4. **Contradiction & Temporal Gate** (supersession lineage resolution).
5. **Authority & Scope Gate** (scope boundaries and `POLICY.md` compliance).

### Decision 4.5: Bitemporal Validity Semantics
We decouple Reality/Event Time (`observed_at`) from Assertion/System Time (`valid_from`, `valid_until`, `recorded_at`).
* When code changes in Git, memories referencing affected lines are dynamically flagged as `stale`.
* When a fact changes, the existing record is updated with `valid_until = now` and `superseded_by = new_id`, while the new record links `supersedes = old_id`. Historical knowledge is permanently preserved.

### Decision 4.6: Multi-Scope Boundary Isolation
We enforce five explicit scopes: `project`, `global`, `domain`, `tool`, `session`.
* "Null scope" is disallowed.
* Query resolution strictly prioritizes: $\text{Session} \succ \text{Project} \succ \text{Domain/Tool} \succ \text{Global}$.
* Project memory overrides global memory on repository-specific decisions.

### Decision 4.7: Local MemSearch Hybrid Retrieval & RRF Fusion
The read path combines dense semantic retrieval with BM25 sparse lexical search using Reciprocal Rank Fusion (RRF):
$$\text{RRF}(d) = \frac{0.6}{60 + \text{rank}_{\text{dense}}(d)} + \frac{0.4}{60 + \text{rank}_{\text{bm25}}(d)}$$
Results are reranked by evidence freshness and authority before injection into the agent's context under a strict token budget (< 1200 tokens).

### Decision 4.8: Single-Writer Asynchronous Index Update Queue
To keep lifecycle hooks fast and prevent concurrency lockouts during multi-agent workflows, file mutations are written atomically to Markdown first, followed by appending an index mutation task to a Write-Ahead Log queue (`.agent-state/queue/index_wal.jsonl`). A single-writer worker processes embedding updates asynchronously.

---

## 5. Consequences & Invariant Compliance

### Positive Consequences
* **Accurate Semantic Discovery**: Agents can retrieve relevant knowledge across phrasing variations and architectural abstractions.
* **Elimination of Stale Hallucinations**: Evidence gating and bitemporal invalidation prevent outdated facts from misguiding the agent.
* **Total Disaster Recovery**: Complete recovery from vector corruption in seconds by rebuilding from canonical Markdown files.
* **Full Auditability**: Lineage tracking (`supersedes`, `derived_from`) and mutation logging (`mutations.jsonl`) explain *why* any piece of knowledge was admitted or modified.
* **Zero Secrets Guaranteed**: Multi-stage pre-write scanning guarantees credentials never enter files or vector databases.

### Negative Consequences & Trade-offs
* **Local Compute Overhead**: Local dense embedding generation consumes CPU cycles.  
  * *Mitigation*: Embedding operations are offloaded to an asynchronous background queue, deferred out of hot execution hooks.
* **Schema Rigidity**: Requiring 16 fields could break older workflows.  
  * *Mitigation*: The compiler provides a transparent backward compatibility layer that reads legacy single-line Markdown entries without error.

---

## 6. Non-Negotiable Invariants Verification

| Invariant | Requirement Summary | Architectural Compliance |
| :---: | :--- | :--- |
| **1 & 2** | Human-readable canonical truth; rebuildable indexes. | Markdown files are authoritative; MemSearch indexes are fully rebuildable. |
| **3** | Candidate is not automatically authoritative. | Staging quarantine in `.agents/memory/inbox/`; admission gated by 5 gates. |
| **4** | Memory result is not an instruction. | Memory injected as background data block; prompt instructions retain authority. |
| **5** | Live repository state outranks stale memory. | Live Git state, files, and tests take unconditional precedence. |
| **6** | History preserved through supersession. | Records are never deleted; lineage tracked via `supersedes` / `superseded_by`. |
| **7** | Scope boundaries enforced. | Five explicit scopes; no null scope; project overrides global. |
| **8** | Secrets never enter durable memory. | High-entropy regex scanner rejects candidate writes containing credentials. |
| **9** | Index failure cannot corrupt memory. | Canonical writes complete before index queue ingestion; index failures isolate safely. |
| **10** | Automatic writes are idempotent. | Exact SHA-256 content hashing deduplicates repeated write operations. |
| **11** | Expensive work deferred out of hot hooks. | Indexing queued to asynchronous worker; hooks remain lightweight. |
| **12** | Unknown is a valid answer. | Low-confidence searches return empty match rather than speculative hallucinations. |
| **13** | Evidence must be fresh enough. | Code-coupled memories verify Git commit freshness against current HEAD. |
| **14** | Semantic layer can be disabled. | System falls back gracefully to lexical regex search if embeddings are absent. |
| **15** | No unverified learned ranking policy. | Retrieval weights remain fixed unless validated against regression benchmark suite. |
| **16** | No active procedural skill without admission. | Procedural skills staged in `procedural/`; require live CLI verification. |
| **17** | Major mutations are auditable. | Ingestion, reconciliation, and supersession write to audit logs. |
| **18** | Tests independently verify behavior. | Complete test suite validates schema, admission, rebuild, and search. |
| **19** | Documentation kept current. | Architecture docs and ADRs updated concurrently with implementation. |
| **20** | Green health report requires consistent evidence. | `memory_doctor.py` validates index integrity and links before reporting green. |
| **21** | No fabricated proof. | Provenance pointers require verifiable filesystem paths, Git SHAs, or exit codes. |
| **22** | Understandable to future agents. | Clean layout, standardized schemas, explicit ADRs ensure agent legibility. |

---

## 7. Implementation & Rollout Schedule

In accordance with `Instruction.md` Section 110, rollout proceeds in six strictly gated phases:
* **Phase 0: Forensic Baseline & Architecture**: Establish `SPEC.md`, `ADR-002`, baseline audits, and acceptance criteria. *(Current Phase)*
* **Phase 1: Foundation Repair**: Resolve index routing inconsistencies, legacy references, and file lock handling.
* **Phase 2: MemSearch Read Path**: Implement local MemSearch adapter, hybrid dense+BM25 retrieval, and RRF fusion.
* **Phase 3: Retrieval Compiler & Context Budgeting**: Implement scope-aware query routing and evidence reranking.
* **Phase 4: Candidate Memory & Ingestion Pipeline**: Deploy `.agents/memory/inbox/`, extraction parser, and 5-gate admission engine.
* **Phase 5: Reconciliation, Supersession & Index Queue**: Deploy `memory_reconciler.py` and `memory_index_queue.py`.
* **Phase 6: Verification, Benchmark & Memory Doctor**: Execute regression benchmarks, invariant audits, and certification.

---
*Architectural Decision Approved by:*  
**Lead Memory Architect (Agent 1)**  
*Antigravity Autonomous Engineering Systems*  
`2026-09-03T17:14:47Z`
