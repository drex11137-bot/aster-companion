# FORENSIC STATE EXTRACTION: RETRIEVAL, FUSION & CONTEXT COMPILER
**System:** Antigravity Memory Operating System (Phase 1–16)  
**Agent:** Agent 5 — Retrieval, Fusion & Context Compiler Specialist  
**Execution Timestamp:** 2026-09-04T19:14:00Z  
**Target Repository:** `/workspaces/codespaces-blank`  
**Status:** Canonical Read-Only Forensic Extraction Complete  
**Governing Specifications:** `instruction.md` (Sections 24, 27, 28, 29, 51, 54, 55) & `AGENTS.md` (Squad 3)

---

## 1. EXECUTIVE CONTRACT & SCOPE OWNERSHIP

This document constitutes the authoritative forensic architecture and runtime extraction for the **Retrieval, Fusion, and Context Compilation subsystems** of the Antigravity Memory Operating System. 

In strict adherence to **Section 1 (Executive Contract)** and **Section 3 (No-Change Policy)** of `instruction.md`, this snapshot documents exclusively **what exists, executes, and has been empirically verified** across live source code, configuration files, test suites, and executed runtime commands.

### Owned Specification Sections
- **Section 24**: Confidence / Trust Model
- **Section 27**: Evidence Model
- **Section 28**: Retrieval Architecture
- **Section 29**: Retrieval Mechanics
- **Section 51**: Trust Boundaries
- **Section 54**: Feedback & Telemetry
- **Section 55**: Learning / Adaptation

### Forensic Absolute Evidence Priority
```text
1. EXECUTED RUNTIME OBSERVATION (Live command execution, CLI probes, test suite runs)
2. ACTUAL SOURCE CODE (scripts/query_router.py, search_memory.py, context_compiler.py, etc.)
3. ACTUAL EFFECTIVE CONFIGURATION (.agents/mcp_config.json, hooks.json, models/*.json)
4. GENERATED / DERIVED ARTIFACTS (.agents/memory/retrieval_ledger.jsonl, .memsearch/manifest.json)
5. EXECUTED TEST RESULTS (context_compiler.py --test: 9/9 PASS, learning_loop.py benchmark: 6/6 PASS)
6. REPOSITORY DOCUMENTATION (docs/architecture.md, AGENTS.md)
7. COMMENTS / AGENT CLAIMS (treated as advisory hypotheses until verified)
```

---

## 2. SECTION 28: RETRIEVAL ARCHITECTURE

### 2.1 Architectural Topology & Entry Points
The read path is structured as a multi-tier pipeline designed to minimize token usage, eliminate prompt injection vulnerabilities, ensure evidence-based truth over lexical similarity, and provide explicit abstention when no trustworthy memory exists.

```text
[User / Agent Query]
         │
         ▼
[scripts/query_router.py] ──────────► L0: Intent Classification & Automatic Scope Routing
         │                                (Controlled Query Expansion capped at 4 terms)
         ▼
[scripts/search_memory.py] ─────────► L1: Multi-Scope File Discovery & Dual Substrate Execution
    ┌────┴────────────────────────┐
    ▼                             ▼
[MemSearchBackend]         [extract_section_snippets]
Dense Semantic Path        Lexical / Regex Path
(bge-m3 ONNX / Milvus)     (Token boundary, headings, phrase match)
    └────┬────────────────────────┘
         ▼
[Reciprocal Rank Fusion (RRF)] ────► L2: Rank Fusion (k=60, w_dense=0.6, w_lexical=0.4)
         │
         ▼
[scripts/evidence_reranker.py] ─────► L3: Multi-Signal Evidence Reranker (Disjoint Tiers 0–4)
         │                                (Separates Truth from Retrieval Relevance)
         ▼
[scripts/context_compiler.py] ──────► L4: Trust Verdicts (CERTIFY, ADVISORY, WARN, BLOCK)
         │                                SEC-004 Injection Gate + Abstention Engine
         │                                Progressive Disclosure Token Packing (L1/L2/L3/Auto)
         ▼
[Safe Compiled Context Package] ───► L5: Injected into Agent Active Context
         │
         ▼
[scripts/memory_feedback.py] ───────► L6: Telemetry Ledger Recording (retrieval_ledger.jsonl)
```

### 2.2 Primary Script Interfaces & Roles
| Source File | Primary Class / Function | Operational Responsibility |
| :--- | :--- | :--- |
| [`scripts/query_router.py`](file:///workspaces/codespaces-blank/scripts/query_router.py) | `QueryRouter`, `classify_intent()`, `determine_scope()`, `expand_query()` | Analyzes query intent across 5 categories, resolves temporal orientation, calculates target scopes, expands abbreviations, and routes to search. |
| [`scripts/search_memory.py`](file:///workspaces/codespaces-blank/scripts/search_memory.py) | `run_memory_search()`, `discover_memory_files()`, `reciprocal_rank_fusion()` | Discovers files matching scopes, triggers dense vector retrieval and lexical search, applies RRF rank fusion, and integrates evidence reranker. |
| [`scripts/memsearch_backend.py`](file:///workspaces/codespaces-blank/scripts/memsearch_backend.py) | `MemSearchBackend`, `search()`, `_purge_entities()` | Adapter boundary encapsulating native `memsearch` CLI and local Milvus Lite vector database running ONNX `bge-m3` CPU embeddings. |
| [`scripts/evidence_reranker.py`](file:///workspaces/codespaces-blank/scripts/evidence_reranker.py) | `EvidenceReranker`, `extract_signals()`, `calculate_rerank_score()` | Enforces "Relevance != Truth". Evaluates source tier authority, epistemic confidence, and temporal penalties across disjoint authority score bands. |
| [`scripts/context_compiler.py`](file:///workspaces/codespaces-blank/scripts/context_compiler.py) | `ContextCompiler`, `evaluate_trust()`, `compile_chunks()` | Assigns structured trust verdicts (`CERTIFY`, `ADVISORY`, `WARN`, `BLOCK`), enforces token budgets, filters prompt injection attacks, and packages L1/L2/L3 context. |
| [`scripts/memory_feedback.py`](file:///workspaces/codespaces-blank/scripts/memory_feedback.py) | `FeedbackLedger`, `compute_metrics()` | Records retrieval feedback events under concurrency file locks, tracking visibility, utilization, correctness, and computing MRR/NDCG metrics. |
| [`scripts/learning_loop.py`](file:///workspaces/codespaces-blank/scripts/learning_loop.py) | `ShadowRanker`, `MemoryDecayModel`, `AccessReinforcementModel`, `BenchmarkGate` | Computes Ebbinghaus memory decay curves, access reinforcement saturation, and shadow linear ranking without mutating live baseline retrieval. |

### 2.3 Query Intent Classification & Temporal Orientation
In [`scripts/query_router.py`](file:///workspaces/codespaces-blank/scripts/query_router.py#L116-L257), queries are classified into 5 distinct intents:
1. **`present-state`**: ("What is the active objective now?") — Targets `CURRENT.md` and active project status.
2. **`historical as-of`**: ("What was the Antigravity CLI version before 1.1.25?") — Targets session journals and superseded records.
3. **`procedural`**: ("How do we run tests?", "What is our Git merge convention?") — Targets `PROCEDURES.md`, runbooks, and tool workflows.
4. **`debugging`**: ("Why did secret scanning fail?", "Why does Gradle exhaust memory?") — Targets `GOTCHAS.md` and troubleshooting guides.
5. **`why/rationale`**: ("Why did we choose Ninja over Make?", "ADR rationale") — Targets `DECISIONS.md`.

**Temporal Detection (Section 141)** distinguishes between:
- `present`: Queries matching `\b(currently|right now|now|today|latest|present|active)\b`.
- `historical`: Queries matching `\b(before|previously|prior|formerly|earlier|used to be|was|were|superseded)\b`.
- `timeless`: Invariant queries (e.g., architectural conventions, tool syntax).

### 2.4 Controlled Query Expansion (Section 140)
To avoid query explosion and prohibitive search latency, `query_router.py` enforces controlled query expansion:
- **Abbreviations**: 16 static expansions (e.g., `auth` -> `authentication`, `adr` -> `architectural decision record`, `k8s` -> `kubernetes`, `pcap` -> `packet capture`, `wasm` -> `webassembly`).
- **Domain Synonyms**: Capped to top 3 expansions per token (e.g., `tests` -> `run tests`, `pytest`, `unit tests`).
- **Component Hints**: Maps keywords directly to canonical files (e.g., `decision` -> `DECISIONS.md`, `gotcha` -> `GOTCHAS.md`, `objective` -> `CURRENT.md`).
- **Cost Cap**: Total expanded terms are hard-capped at **4 terms maximum** (`query_router.py:L410`).

---

## 3. SECTION 29: RETRIEVAL MECHANICS & DUAL PATHS

### 3.1 Dual Retrieval Substrates
The Antigravity persistent memory system implements two independent retrieval substrates that operate concurrently before rank fusion:

#### Path A: Dense Semantic Retrieval Substrate
- **Implementation**: [`scripts/memsearch_backend.py`](file:///workspaces/codespaces-blank/scripts/memsearch_backend.py) wrapping `memsearch` CLI and `MilvusStore`.
- **Embedding Model**: `BAAI/bge-m3` executed via local CPU ONNX runtime (`--provider onnx`).
- **Embedding Dimension**: 1024 dimensions.
- **Vector Storage**: Milvus Lite embedded database persisted at `~/.memsearch/milvus.db` (or `.agents/memory/.memsearch/`).
- **Resolution Boundary**: Dense chunks returned by Milvus are mapped back to enclosing markdown section boundaries via `find_enclosing_section()` in [`scripts/search_memory.py:L274-L302`](file:///workspaces/codespaces-blank/scripts/search_memory.py#L274-L302). This prevents fragmented sentence injection and ensures coherent semantic units.
- **Fast-Path Optimization**: `run_dense_search()` verifies against the indexed file manifest before calling ONNX inference; if no requested candidate files are in the manifest, the dense path exits in 0ms (`search_memory.py:L473-L489`).

#### Path B: Lexical Retrieval Substrate
- **Implementation**: [`scripts/search_memory.py:extract_section_snippets()`](file:///workspaces/codespaces-blank/scripts/search_memory.py#L304-L454).
- **Matching Mechanics**:
  - Word boundary enforcement (`\b<token>\b`).
  - Stop-word filtering removing 23 low-information words (`a`, `the`, `in`, `to`, `for`, etc.).
  - Exact full-phrase matching bonus: **+25 points**.
  - Individual token hit score: **+10 points** per matching token.
  - Multi-token bonus (all query tokens present in the same line): **+15 points**.
  - Markdown heading match bonus: **+20 points** if `#` or `##` heading contains query terms.
- **Section Proximity Grouping**: Lines matching within **3 lines of each other** are clustered into a single cohesive snippet (`search_memory.py:L420-L432`), capturing contextual lines above and below.

### 3.2 Reciprocal Rank Fusion (RRF) Algorithm
Dense and lexical candidate lists are fused in [`scripts/search_memory.py:reciprocal_rank_fusion()`](file:///workspaces/codespaces-blank/scripts/search_memory.py#L549-L601) using Reciprocal Rank Fusion:

$$\text{RRF\_Score}(d) = \frac{w_{\text{dense}}}{k + \text{rank}_{\text{dense}}(d)} + \frac{w_{\text{lexical}}}{k + \text{rank}_{\text{lexical}}(d)}$$

#### Verified Parameter Constants:
- **Smoothing Constant ($k$)**: `60` (standard Cormack et al. constant, prevents top ranks from overwhelmingly dominating scores).
- **Dense Weight ($w_{\text{dense}}$)**: `0.60` (prioritizes semantic paraphrase and conceptual alignment).
- **Lexical Weight ($w_{\text{lexical}}$)**: `0.40` (ensures exact symbol, function name, and keyword hits are retained).
- **Candidate ID Keying**: Bitemporal section ID `file_path::start_line`.
- **Tie-Breaking**: If RRF scores match, items are ordered by `dense_score`, then `lexical_score`, then line number.

### 3.3 Deduplication & Maximal Marginal Relevance (MMR)
- **Section-Level Unioning**: Multiple raw lexical or vector hits within the same markdown section are collapsed to the containing section boundary via `find_enclosing_section()`.
- **Candidate Deduplication**: `scripts/query_router.py:L730-L737` dedupes multi-query candidates across expanded search terms using the tuple `(file_path, start_line, end_line)`.
- **Diversification**: Evidence reranking groups results across disparate files and sources rather than allowing a single multi-chunk file to flood the top-k window.

### 3.4 Explicit Abstention Mechanics (Section 30 & 78)
The retrieval system strictly rejects the temptation to return low-confidence or misleading information. Explicit abstention is triggered under three conditions in [`scripts/query_router.py:L780-L798`](file:///workspaces/codespaces-blank/scripts/query_router.py#L780-L798):

```python
# Condition 1: Low Confidence / No Matches
if not evaluated_matches or max_confidence < threshold:  # threshold default = 0.40
    abstained = True
    abstention_message = "No sufficiently trustworthy memory found"

# Condition 2: Historical Memory Matched for Present Query
elif intent_info["intent"] == "present-state" and best_match["status"] == "SUPERSEDED" and not has_active_match:
    abstained = True
    abstention_message = "Relevant historical memories found, but current-state verification is required."

# Condition 3: Security / Policy Quarantine
elif len(chunks) == blocked_count and blocked_count > 0:
    abstention_message = "All candidate memories were blocked by security or policy gatekeepers."
```

---

## 4. SECTION 24: CONFIDENCE / TRUST MODEL

### 4.1 Separation of Truth from Retrieval Relevance
The Antigravity Persistent Memory OS enforces an unbreachable axiom:

> **"Retrieval similarity is not proof of truth."**  
> *(Instruction.md Section 17, 22, 24)*

A query for *"Antigravity CLI version"* might match an obsolete note stating *"Antigravity is version 1.0.0"* with near-perfect lexical and semantic similarity (0.98 relevance). Under a single-scalar retrieval model, this incorrect fact would win. In Antigravity, **epistemic truth, source authority, freshness, importance, and retrieval relevance are strictly separated**.

### 4.2 The Five Orthogonal Dimensions
| Dimension | Field Name | Representation | Scale / Values | Governance Meaning |
| :--- | :--- | :--- | :--- | :--- |
| **1. Epistemic Confidence** | `epistemic_confidence` | Normalized float | `0.00 – 1.00` (`VERIFIED`: 1.0, `HIGH`: 0.9, `MEDIUM`: 0.6, `LOW`: 0.4, `UNVERIFIED`: 0.2) | How certain is the fact based on validation evidence? |
| **2. Source Authority** | `source_authority` | Disjoint tier float | `0.20 – 1.00` (`USER_EXPLICIT`: 1.0, `TEST`: 0.95, `REPO`: 0.9, `OBSERVATION`: 0.7, `INFERENCE`: 0.4) | What is the inherent reliability of the origin? |
| **3. Temporal Freshness** | `temporal_status`, `temporal_penalty` | Status enum & float penalty | `ACTIVE` (0.0), `STALE` (-0.20), `SUPERSEDED` (-0.50) | Is the record current, decaying, or explicitly invalidated? |
| **4. Durability / Importance** | `importance` | Integer scale | `0 – 5` (0=Ephemeral, 3=Project, 5=Immutable Policy) | How durable is the knowledge intended to be? |
| **5. Retrieval Relevance** | `normalized_relevance` | Float from RRF | `0.00 – 1.00` | How closely does text match query terms? (Pure retrieval signal) |

### 4.3 Composite Truth Score Formula
Implemented in [`scripts/evidence_reranker.py:L253`](file:///workspaces/codespaces-blank/scripts/evidence_reranker.py#L253):

$$\text{Truth\_Score} = \left(0.60 \times \text{Source\_Authority} + 0.40 \times \text{Epistemic\_Confidence}\right) + \text{Temporal\_Penalty}$$

### 4.4 Disjoint Authority Tiers (Guaranteed Ranking Separation)
To ensure that an unverified claim or superseded note can **never** outrank an authoritative fact, [`scripts/evidence_reranker.py:calculate_rerank_score()`](file:///workspaces/codespaces-blank/scripts/evidence_reranker.py#L283-L345) divides candidate scores into **strictly disjoint bands**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 4: AUTHORITATIVE CURRENT FACT (70.0 - 100.0) -> [CERTIFY]         │
│ Source: USER_EXPLICIT (1.0), EXECUTED_TEST (0.95), REPO_SOURCE (0.90) │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 3: AGENT OBSERVATION (50.0 - 68.0)          -> [ADVISORY]         │
│ Source: Sessions, runtime command observations, unverified logs        │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 2: AGENT INFERENCE (35.0 - 48.0)            -> [ADVISORY]         │
│ Source: "I think X is true" - deductions without execution evidence    │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 1: UNVERIFIED CLAIM (15.0 - 28.0)           -> [UNVERIFIED]       │
│ Source: Candidate notes, unadmitted claims, low epistemic confidence   │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 0: SUPERSEDED / INVALIDATED (0.0 - 15.0)    -> [SUPERSEDED]       │
│ Source: Historical superseded records, contradicted memory             │
└────────────────────────────────────────────────────────────────────────┘
```

**Mathematical Guarantee:**  
Because Tier 0 max score is $15.0$, Tier 1 max score is $28.0$, and Tier 4 min score is $70.0$, **no amount of lexical or vector similarity can push an unverified or superseded record above an authoritative current fact**.

---

## 5. SECTION 27: EVIDENCE MODEL

### 5.1 The Five Epistemic Granularities
The Antigravity memory OS distinguishes five discrete evidence stages:

```text
[Raw Observation] ──► [Source Evidence] ──► [Agent Inference] ──► [Derived Summary] ──► [Canonical Fact]
```

1. **Raw Observation** (`SourceTier.AGENT_OBSERVATION`, Authority = 0.70):
   - Ephemeral session traces, tool stdout/stderr, unparsed command output.
   - Stored in `.agents/memory/sessions/YYYY-MM-DD-HHMM.md`.
2. **Source Evidence** (`SourceTier.REPOSITORY_SOURCE` / `EXECUTED_TEST`, Authority = 0.90–0.95):
   - Direct citations to repository code, configuration lines (`file:///path#L10-L20`), Git commit SHAs, or passing test assertions.
3. **Agent Inference** (`SourceTier.AGENT_INFERENCE`, Authority = 0.40):
   - Inductive hypotheses generated by LLMs during planning ("The bug might be caused by memory limits"). Never admitted to Tier 3/4 memory without verification.
4. **Derived Summary** (`SourceTier.DERIVED_SUMMARY`, Authority = 0.50):
   - Compaction indexes, session summaries, and synthesized previews.
5. **Canonical Fact** (`SourceTier.USER_EXPLICIT` / `POLICY`, Authority = 1.00):
   - Accepted Architectural Decision Records in `DECISIONS.md`, immutable governance rules in `POLICY.md`, and verified system specifications in `ENVIRONMENT.md`.

### 5.2 Evidence Grading & Attachment
Evidence is explicitly declared in memory metadata headers:
- `Confidence: VERIFIED` — Backed by passing test execution or live configuration check.
- `Confidence: INFERRED` — Agent inference or heuristic; requires human or test confirmation.
- `Confidence: CONTRADICTED` — Live repository scan discovered divergence between memory and code.
- `Confidence: UNVERIFIED` — Candidate memory staged in inbox awaiting admission gating.

### 5.3 Weak and Invalid Evidence Handling
- **Quarantined Candidates (Invariant 16)**: Memory files staged in `.agents/memory/inbox/` are penalized with `trust_multiplier = 0.20` and hard-capped at `confidence <= 0.25` in `query_router.py:L577-L584`.
- **Contradicted Evidence**: Chunks whose evidence contradicts the live repository are assigned `TrustVerdict.WARN` and a negative temporal penalty.

---

## 6. SECTION 51: TRUST BOUNDARIES & CONTEXT COMPILER

### 6.1 Trust Boundary Classification Matrix
Per Section 51, the system enforces a strict boundary between trusted canonical surfaces and untrusted external/staged inputs:

| Domain | Boundary Classification | Components / Storage | Gatekeeper Mechanism |
| :--- | :---: | :--- | :--- |
| **Governance & Policy** | **TRUSTED** | `~/.gemini/antigravity-cli/memory/POLICY.md`, `.agents/rules/` | Immutable, read-only, zero decay |
| **Canonical Project Memory** | **TRUSTED** | `DECISIONS.md`, `ARCHITECTURE.md`, `GOTCHAS.md` | Single-writer lease lock, git commit SHA |
| **Authoritative Repository** | **TRUSTED** | Source tree (`scripts/`, `src/`, `tests/`), toolchain configs | Live file inspection overrides memory |
| **Derived Vector Substrate** | **DERIVED** | `.agents/memory/.memsearch/`, `milvus.db` | Non-canonical, disposable, rebuildable |
| **Staged Ingestion Inbox** | **UNTRUSTED** | `.agents/memory/inbox/candidates.jsonl` | Quarantined, durability admission gate |
| **Raw Episodic Sessions** | **UNTRUSTED** | `.agents/memory/sessions/*.md`, transcripts | Ephemeral, rapid half-life decay |
| **Retrieved Memory Text** | **UNTRUSTED** | Content retrieved via search queries | SEC-004 prompt injection gatekeeper |

### 6.2 Progressive Disclosure Levels (Section 28 & 29)
Implemented in [`scripts/context_compiler.py`](file:///workspaces/codespaces-blank/scripts/context_compiler.py#L320-L436):

#### Level 1: Compact Summary (L1)
- **Target Constraint**: Strictly under **200 characters** (`len(l1_output) < 200` enforced by truncation guard).
- **Format**: `[MEM:<hash>] <Topic> | <STATUS> | Conf:<val> | <VERDICT> | <Snippet>`
- **Use Case**: Index listings, large candidate fan-outs, and extreme token budget pressure.

#### Level 2: Canonical Context Pack (L2)
- **Target Constraint**: Markdown block with structured front-matter.
- **Format**:
```text
[MEMORY]
Topic: <Heading>
Status: <ACTIVE|SUPERSEDED>
Confidence: <0.00-1.00>
Trust: <CERTIFY|ADVISORY|WARN>
Scope: <PROJECT|GLOBAL|TOOL|DOMAIN>
Evidence: <description> (<VERIFIED|INFERRED>)
Date: <YYYY-MM-DD>
State: <CURRENT|HISTORICAL>
Source: [<filename>#L<start>-L<end>](file://<path>#L<start>-L<end>)

<Canonical markdown body>
```

#### Level 3: Deep Provenance Pointer (L3)
- **Target Constraint**: Cryptographic and temporal audit trail.
- **Format**: Complete metadata including Git commit SHA, exact file URI, line numbers, execution turn, SHA-256 content hash, and repository reconciliation status.

#### Adaptive Mode (AUTO)
- Optimally packs top-ranking matches at Level 2.
- Automatically degrades lower-ranked matches to Level 1 when token budget is pressured.
- Strictly adheres to token budget ceilings (verified live against 250t, 300t, 500t budgets).

### 6.3 Trust Verdict Assignment Engine
Implemented in [`scripts/context_compiler.py:evaluate_trust()`](file:///workspaces/codespaces-blank/scripts/context_compiler.py#L257-L316):
- **`CERTIFY`**: Confidence $\ge 0.85$, evidence verified/tested, status `ACTIVE`, state `CURRENT`.
- **`ADVISORY`**: Confidence $0.60 – 0.84$, inferred/unverified evidence, heuristic guidance.
- **`WARN`**: Confidence $< 0.60$, status `SUPERSEDED`, `STALE`, or `CONTRADICTED`, or containing policy override patterns.
- **`BLOCK`**: Sensitive secret detected, status `FORBIDDEN` or `REVOKED`, or critical prompt injection attack detected.

### 6.4 Hardened Defenses Against Adversarial Memory
Retrieved memories can act as a vector for indirect prompt injection. The system provides two defensive layers:

#### Defense 1: SEC-004 Prompt Injection Detection
Inspected in [`scripts/context_compiler.py:L175-L236`](file:///workspaces/codespaces-blank/scripts/context_compiler.py#L175-L236):
- **Critical Exploit Payloads -> Hard `BLOCK` (Excluded from Context)**:
  - `ignore previous instructions`
  - `system override` / `override system prompt`
  - Persona escalation: `you are now unrestricted / root / admin / dan`
  - Secret exfiltration: `reveal all secrets / passwords / keys / tokens`
  - Destructive command directives: `rm -rf`, `sudo`, `chmod 777`, `curl ... | bash`
- **Instructional Overrides -> Mandatory `WARN` (NEVER CERTIFY)**:
  - `disregard policy / rules / safety`
  - `privileged command execution directives`
  - `run this command`

#### Defense 2: SEC-005 Code-Fence Breakout Defense
In [`scripts/search_memory.py:L783`](file:///workspaces/codespaces-blank/scripts/search_memory.py#L783) and `context_compiler.py`, memory snippets containing triple backticks (```` ``` ````) are enclosed in **quad backticks** (```` ````markdown ````). This prevents adversarial code snippets inside memory files from breaking out into active prompt instructions.

---

## 7. SECTION 54: FEEDBACK & TELEMETRY

### 7.1 Telemetry Storage & Schema
- **File Path**: [`/workspaces/codespaces-blank/.agents/memory/retrieval_ledger.jsonl`](file:///workspaces/codespaces-blank/.agents/memory/retrieval_ledger.jsonl)
- **Concurrency**: Governed by atomic file locking (`lock_manager.file_lock`) and `fsync`.
- **Zero Secrets Enforcement**: Every telemetry entry is scanned with `secret_scanner.scan_text()` before disk write (`memory_feedback.py:L161`). Any credential causes a fatal exception.

### 7.2 Tracked Signals
The telemetry engine tracks fine-grained signals distinguishing visibility from action:
- `was_visible`: Boolean. `True` if injected into model prompt; `False` if retrieved by search but omitted due to token budget or low rank.
- `used_in_action`: Boolean. `True` if the agent's generated code, command, or decision explicitly utilized the memory.
- `outcome`: Categorical classification:
  - `EXPLICIT_FEEDBACK`: Human user explicitly commended or corrected the memory.
  - `VERIFIED_OUTCOME`: Machine-verified task success (e.g., test passed, build succeeded).
  - `INFERRED_USAGE`: Behavioral inference of memory application.
  - `INFERRED_NONUSE`: Memory was visible in context but not acted upon.
- `helpful`: Explicit boolean evaluation of utility.
- `wrong`: Memory asserted a factually incorrect state.
- `stale`: Memory asserted an obsolete, superseded state.
- `prevented_error`: Memory directly warned against a known pitfall or gotcha.
- `blocked_action`: Memory contained bad advice that aborted execution.

### 7.3 Executed Runtime Observation: Live Ledger Metrics
A live probe of `python3 scripts/memory_feedback.py --metrics` executed against the live ledger yielded:

```text
## Retrieval Feedback & Telemetry Metrics Report
- Ledger Target: retrieval_ledger.jsonl (24 lines, 8,501 bytes)
- Queries Evaluated: 12
- Telemetry Events: 23

Core Retrieval Performance Metrics:
┌──────────────────────────────────────┬─────────┬──────────────┬────────┐
│ Metric                               │ Value   │ Target       │ Status │
├──────────────────────────────────────┼─────────┼──────────────┼────────┤
│ MRR (Mean Reciprocal Rank)           │ 0.6458  │ >= 0.7000    │ WARN   │
│ NDCG@10 (All Queries)                │ 0.7551  │ >= 0.7000    │ PASS   │
│ NDCG@10 (Relevant-Only Queries)      │ 0.8957  │ >= 0.7000    │ PASS   │
│ False Recall Rate (Item Level)       │ 0.5714  │ <= 0.4000    │ WARN   │
│ Strict False Recall Rate             │ 0.0952  │ <= 0.1500    │ PASS   │
│ Query False Recall Rate              │ 0.6364  │ <= 0.3500    │ INFO   │
│ Abstention False Recall Rate         │ 0.5000  │ <= 0.5000    │ INFO   │
└──────────────────────────────────────┴─────────┴──────────────┴────────┘

Telemetry Visibility Breakdown:
- Visible Recalls: 21 (91.3%)
- Not Shown Recalls: 2 (8.7%)
- Used in Action: 10 (47.6%)
- Shown But Unused: 11 (52.4%)
- Verified Positive Outcomes: 6
- Explicit Human Feedback: 2
- Wrong Memory Flags: 2
- Stale Memory Flags: 1
- Prevented Errors: 3
- Blocked Actions: 1
```

---

## 8. SECTION 55: LEARNING & ADAPTATION

### 8.1 Memory Decay Curves (Ebbinghaus Adaptation)
Implemented in [`scripts/learning_loop.py:MemoryDecayModel`](file:///workspaces/codespaces-blank/scripts/learning_loop.py#L419-L532):

#### Base Scope Half-Lives:
- `policy` / `governance` / `rules`: **3,650 days** (10 years — effectively immortal).
- `global`: **1,825 days** (5 years).
- `architecture`: **730 days** (2 years).
- `decisions`: **365 days** (1 year).
- `gotchas` / `tools` / `domains`: **180 days** (6 months).
- `project`: **90 days** (3 months).
- `sessions`: **14 days** (2 weeks).
- `candidate`: **7 days** (1 week).

#### Dynamic Decay Adjustments:
1. **Importance Scaling**:
   $$T_{1/2,\text{eff}} = T_{1/2,\text{base}} \times \left(1.0 + \left(\frac{\text{importance}}{2.0}\right)^{1.5}\right)$$
2. **Spaced Retrieval / Verification Reinforcement**:
   $$M_{\text{access}} = 1.0 + 0.25 \ln(1 + \text{access\_count}) + 0.75 \ln(1 + \text{verified\_count})$$
3. **Exponential Decay**:
   $$\text{Decay\_Factor}(t) = \exp\left(-\frac{\ln 2}{T_{1/2,\text{eff}}} \times t\right)$$
4. **Authority Retention Floor**:
   $$\text{Retention\_Floor} = \min(0.85, \text{authority} \times 0.55)$$
5. **Governance Immunity**: If scope is `policy`, file is `POLICY.md`, or authority $\ge 0.95$, `decay_factor` is hardcoded to **$1.0$ indefinitely** (`learning_loop.py:L472-L484`).

### 8.2 Access Reinforcement Mechanics
In [`scripts/learning_loop.py:AccessReinforcementModel`](file:///workspaces/codespaces-blank/scripts/learning_loop.py#L537-L581):
- **Raw Access Signal**: $\tanh(0.12 \ln(1 + \text{access\_count}))$
- **Verified Signal**: $\tanh(0.35 \ln(1 + \text{verified\_count}))$
- **Refutation Penalty**: $\tanh(0.50 \times \text{refuted\_count})$
- **Combined Reinforcement**:
  $$\text{Reinforcement} = 0.25 \times \text{Raw\_Access} + 0.75 \times \text{Verified} - 0.60 \times \text{Refuted}$$
- **Anti-Echo-Chamber Invariant**: The $\tanh$ function provides sub-linear saturation, preventing popularity loops from elevating unverified memories.

### 8.3 Shadow Linear Ranker (Section 41 & 221)
The learned ranking layer operates **strictly in SHADOW mode in ISOLATION**. It does not alter live search results. Live retrieval remains deterministic baseline RRF.

#### Active Model Metadata (Inspected live via `learning_loop.py model-info`):
- **Schema Version**: `1.0.0`
- **Model Version**: `1.0.0`
- **Training Corpus Version**: `2026.09.03`
- **Weights (Named Schema Mapping)**:
  - `baseline_rrf_score`: `+0.40`
  - `decay_factor`: `+0.15`
  - `access_reinforcement`: `+0.15`
  - `importance`: `+0.10`
  - `authority`: `+0.15`
  - `freshness`: `+0.05`
  - `stale_penalty`: `-0.25`
  - `superseded_penalty`: `-0.35`
- **Named Mapping Guarantee**: Weights are resolved by feature name, never by positional index, preventing silent misalignment when features evolve (`learning_loop.py:L685-L695`).

### 8.4 Benchmark Gate (Section 41 & 222)
A learned model cannot be promoted without passing 6 automated criteria in [`scripts/learning_loop.py:BenchmarkGate`](file:///workspaces/codespaces-blank/scripts/learning_loop.py#L1036-L1150).

#### Executed Runtime Benchmark Run:
```text
============================================================
ANTIGRAVITY BENCHMARK GATE (Instruction.md Section 41, 222)
============================================================
Status: PASS (100.0%)
Checks Passed: 6 / 6
Model Version: 1.0.0 (Schema: 1.0.0)
------------------------------------------------------------
[PASS] governance_fact_decay_immunity: 2-year-old governance policy decay factor: 1.0000 (Required >= 0.98)
[PASS] verified_access_reinforcement_boost: Verified (0.436) > Unverified (0.021)
[PASS] superseded_demotion_invariant: Active ADR score (0.780) > Superseded ADR score (0.334)
[PASS] candidate_ttl_expiration: 20-day-old candidate with 14d TTL: factor=0.0, expired=True
[PASS] stale_episodic_deprioritization: Durable Architecture (0.853) > Stale Session (0.278)
[PASS] schema_and_feature_completeness: Schema version 1.0.0, 8 verified features.
============================================================
```

---

## 9. FORENSIC DISCREPANCIES, DEFECTS & RUNTIME OBSERVATIONS

In accordance with Section 1 of `instruction.md` ("Do not silently repair discrepancies in the report. Expose them."), we document the following empirical findings:

### 1. MemSearch CPU Subprocess Timeout
- **Observation**: During live probe of `query_router.py` executing `search_memory.py`, calls to `/home/codespace/.local/bin/memsearch search ... --provider onnx` timed out after **15 seconds**.
- **Root Cause**: Loading the `BAAI/bge-m3` ONNX model and running 1024-dim embedding inference on CPU within a devcontainer environment exceeds 15 seconds during initial execution.
- **Handling**: `memsearch_backend.py:L292-L296` caught the timeout, logged `CLI search failed: Command ... timed out after 15 seconds`, flagged the backend state as degraded, and cleanly fell back to the lexical retrieval path.
- **Impact**: Zero system crashes; search results were successfully served via lexical retrieval and correctly routed to `DECISIONS.md#L26-L32`. However, dense retrieval is unavailable on slow CPU cycles unless timeout is extended.

### 2. MMR Terminology vs Implementation
- **Observation**: While architectural guidelines reference MMR (Maximal Marginal Relevance) diversity filtering, the codebase implements diversification via:
  1. Section-level deduplication (`find_enclosing_section`).
  2. Multi-scope fanout deduplication (`seen_keys = (file, start_line, end_line)`).
  3. Disjoint authority banding.
- **Finding**: A standalone cosine-distance MMR penalty matrix does not exist in `evidence_reranker.py`; diversity is achieved structurally by markdown section grouping.

### 3. Telemetry Logging Opt-In
- **Observation**: `search_memory.py` requires an explicit `--log-telemetry` flag to append search events to `retrieval_ledger.jsonl`.
- **Finding**: Routine background searches do not automatically mutate `retrieval_ledger.jsonl` to avoid ledger pollution from test probes.

---

## 10. COMPANION ARTIFACTS INVENTORY

| Artifact Path | Format | Status | Description |
| :--- | :---: | :---: | :--- |
| [`/workspaces/codespaces-blank/.agent/memory-state/diagrams/read-flow.mmd`](file:///workspaces/codespaces-blank/.agent/memory-state/diagrams/read-flow.mmd) | Mermaid | **CREATED** | Comprehensive visual flowchart detailing the read path from query to context compilation. |
| [`/workspaces/codespaces-blank/.agent/memory-state/staging/05_retrieval_compiler.md`](file:///workspaces/codespaces-blank/.agent/memory-state/staging/05_retrieval_compiler.md) | Markdown | **CREATED** | Authoritative staging report for Sections 24, 27, 28, 29, 51, 54, 55. |

---

## 11. VERIFICATION CHECKLIST & DEFINITION OF DONE

- [x] Read-only inspection adhered to; no production code modified.
- [x] Inspected `scripts/query_router.py`, `search_memory.py`, `context_compiler.py`, `evidence_reranker.py`, `memsearch_backend.py`, `memory_feedback.py`, `learning_loop.py`.
- [x] Dual retrieval paths documented (Dense ONNX `bge-m3` + Lexical heading/phrase matcher).
- [x] Reciprocal Rank Fusion (RRF) algorithm and parameters documented ($k=60, w_{\text{dense}}=0.6, w_{\text{lexical}}=0.4$).
- [x] Confidence / Trust Model documented with 5 orthogonal dimensions and disjoint score tiers.
- [x] Evidence Model documented with 5 granularities, freshness, and weak evidence handling.
- [x] Trust boundaries and progressive disclosure (L1, L2, L3, Auto) documented with live test evidence.
- [x] Defenses against prompt injection (SEC-004) and code fence breakout (SEC-005) documented.
- [x] Feedback telemetry documented with live metric extraction from `retrieval_ledger.jsonl`.
- [x] Learning loop documented with Ebbinghaus decay formulas, access reinforcement, and shadow ranker.
- [x] Generated Mermaid diagram at `.agent/memory-state/diagrams/read-flow.mmd`.
- [x] Generated staging report at `.agent/memory-state/staging/05_retrieval_compiler.md`.
- [x] Ready for transfer to Master Consolidation Agent.
