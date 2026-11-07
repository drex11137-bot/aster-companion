# Antigravity Memory OS — Future AI Architectural & Operational Handoff

**Target Audience:** Any autonomous or pair-programming AI coding assistant (e.g. Antigravity, Gemini, Claude, OpenAI Codex) operating within this repository.  
**Version:** 2.0.0 (Semantic + Evidence-Gated 8-Tier Architecture)  
**Date:** 2026-09-04  
**Author:** Agent 21 (Workstation Release Master)

---

## 1. Core Architecture: The 8 Memory Tiers

The repository organizes memory into 8 strictly decoupled tiers to ensure zero prompt bloat, zero secret leakage, and complete provenance tracking:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                          8-TIER MEMORY SYSTEM                           │
├────────────────────────────────┬────────────────────────────────────────┤
│ Tier 1: Working Memory         │ .agents/memory/CURRENT.md (<30 lines)  │
│ Tier 2: Episodic Memory        │ .agents/memory/sessions/YYYY-MM-DD.md  │
│ Tier 3: Project Knowledge      │ .agents/memory/{DECISIONS,GOTCHAS}.md  │
│ Tier 4: Global Durable         │ ~/.gemini/antigravity-cli/memory/      │
│ Tier 5: Semantic Retrieval     │ .agents/memory/.memsearch/ & Milvus    │
│ Tier 6: Candidate Bus          │ .agents/memory/inbox/candidates.jsonl  │
│ Tier 7: Procedural Memory      │ .agents/memory/inbox/procedures/       │
│ Tier 8: Memory Telemetry       │ .agents/memory/retrieval_ledger.jsonl  │
└────────────────────────────────┴────────────────────────────────────────┘
```

---

## 2. Invariant Hierarchy: Authority and Truth

When conflicting information is encountered, resolve authority using this **strict linear precedence hierarchy**:

$$\text{Live Repository Reality} > \text{Explicit User Directive} > \text{Policy Rules} > \text{Canonical Markdown Memory} > \text{Vector Retrieval}$$

1. **Live Code Reality Wins**: Live files, compilers, and test outcomes always outrank memory. Memory is advisory.
2. **Canonical Markdown Is the True Storage Substrate**: The vector database (`.memsearch/` or Milvus Lite) is strictly an optional derived index. If the vector DB is deleted, corrupt, or missing, the entire system operates seamlessly on native lexical search (`scripts/search_memory.py`).
3. **Zero Secrets Policy**: NEVER commit, write, or stage credentials, private keys, API keys, or auth headers in any memory file. The `scripts/hooks/pre_tool_use.py` security gate unconditionally blocks credentials.

---

## 3. Daily Operations: CLI Tooling & Commands

### 3.1 Inspecting Memory Health
Run the unified 6-dimension memory diagnostic:
```bash
tools/bin/agy-memory-doctor
```
- Inspects Canonical Markdown Integrity, Secret Hygiene, Coherence, Vector Index Health, Ingestion Backlog, and Telemetry Quality.
- To automatically repair stale index chunks: `tools/bin/agy-memory-doctor --fix`.

### 3.2 Searching Memory (Hybrid Search)
```bash
python3 scripts/search_memory.py --query "Gradle daemon" --scope project
python3 scripts/search_memory.py --query "Architecture" --json
```
- Automatically fuses Lexical (exact code/tokens) and Semantic (conceptual) search using Reciprocal Rank Fusion (RRF).

### 3.3 Routing Queries with Explicit Abstention
```bash
python3 scripts/query_router.py --query "How do we run tests?"
```
- Classifies intent (`present-state`, `historical as-of`, `procedural`, `debugging`, `why/rationale`).
- If no memory is sufficiently confident, it emits explicit abstention (*"No sufficiently trustworthy memory found"*) instead of hallucinating.

### 3.4 Context Compilation with Progressive Disclosure
```bash
python3 scripts/context_compiler.py --file .agents/memory/DECISIONS.md --level auto --budget 500
```
- **L1**: Compact single-line summary (`< 200` characters).
- **L2**: Full Markdown block with source citation and Trust Verdict (`CERTIFY`, `ADVISORY`, `WARN`, `BLOCK`).
- **L3**: Deep provenance pointer (Git commit SHA, line ranges, execution turn).

### 3.5 Experience Capture via Candidate Bus
```bash
python3 scripts/candidate_bus.py --list
```
- High-signal events (build failures, tool errors, architectural decisions) are captured in `.agents/memory/inbox/candidates.jsonl`.
- Routine noise (`ls`, `pwd`, simple echo, status checks) is automatically filtered out.
- SHA-256 content hashing guarantees idempotency.

### 3.6 Memory Reconciliation & Bitemporality
```bash
python3 scripts/memory_reconciler.py --reconcile-inbox
```
- Compares staged candidates against canonical memory.
- Distinguishes exact duplicates, semantic refinements, scope complements, and true contradictions.
- Applies bitemporal timestamps (`observed_at`, `recorded_at`, `valid_from`, `valid_until`) and non-destructive supersession (`[SUPERSEDED on YYYY-MM-DD by id:XYZ]`).

---

## 4. Running the Acceptance & Benchmark Suite

Verify complete workstation memory health and acceptance criteria:
```bash
# Run 30/30 Acceptance Criteria Test Matrix
python3 scripts/memory_benchmark.py --acceptance-matrix

# Run 18/18 Adversarial Security & Poisoning Red-Team Suite
python3 -m unittest tests/test_memory_os_adversarial.py -v

# Run Master Workstation Discovery Suite (254+ tests)
bash tests/run_all_tests.sh

# Run Workstation Diagnostic Doctor
python3 tools/bin/agy-env-doctor --summary
```

---

## 5. Non-Negotiable Rules for Future Agents

1. **NEVER bypass the PreToolUse security hook**: Do not write credentials into memory.
2. **NEVER write directly to active skills from session mining**: Invariant 16 mandates that all mined procedures stage to `.agents/memory/inbox/procedures/` for human or senior agent review.
3. **NEVER store massive virtual environments or cache files in `/workspaces`**: `/workspaces` is constrained (96% utilized). Always allocate large models and virtual environments on `/tmp` (105 GB free).
4. **ALWAYS keep `CURRENT.md` compact**: Active working state must remain under 30 lines.
