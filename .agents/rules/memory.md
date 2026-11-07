# Antigravity Persistent Memory Governance Rule

You are operating under the Antigravity Persistent Memory System.
Follow these operational directives at all times:

## 1. Locating Memory
- **Global Index**: `~/.gemini/antigravity-cli/memory/INDEX.md`
- **Project Index**: `.agents/memory/INDEX.md`

## 2. Progressive Disclosure & Index-First Loading
- **ALWAYS** inspect the index first before loading any memory file.
- Load **ONLY** the memory files strictly required for the current prompt.
- **NEVER** inject the entire memory directory or historical session logs into the context window.

## 3. Authority Hierarchy
1. Active Repository State & Source Code (Authoritative)
2. Explicit User Instructions (Immediate Priority)
3. Project Memory (`.agents/memory/`)
4. Global Durable Memory (`~/.gemini/antigravity-cli/memory/`)

## 4. Knowledge Classification (9 Types & Durability 0–5)
- **Types**: `EPHEMERAL`, `SESSION`, `PROJECT`, `DOMAIN`, `TOOL`, `GLOBAL`, `DECISION`, `GOTCHA`, `PROCEDURE`
- **Durability Scale**:
  - `0–1`: Discard (temporary/noise)
  - `2`: Session only (`sessions/`)
  - `3`: Project memory (`.agents/memory/`)
  - `4`: Domain/Tool memory (`~/.gemini/antigravity-cli/memory/domains/` or `tools/`)
  - `5`: Global durable memory (`~/.gemini/antigravity-cli/memory/`)

## 5. Performance & Token Optimization (Phase 15 Constraints)
- **Index-First Protocol**: Always load `INDEX.md` first; load specific files selectively.
- **Line & Size Budgets**:
  - `CURRENT.md`: Strict limit **< 30 lines** (< 2 KB).
  - `INDEX.md`: Strict limit **< 50 lines** (< 4 KB).
  - Other memory files: Enforce token and line limits (see `.agents/rules/performance.md`).
- **Chronological Session Logs**: Session records in `sessions/` must be chronological (`YYYY-MM-DD-HHMM.md`).
- **Fact Deduplication & Pointers**:
  - Avoid repeated copies of the same fact across multiple files.
  - Prefer relative pointers and links over duplication (e.g. `See [DECISIONS.md](file:///workspaces/codespaces-blank/.agents/memory/DECISIONS.md)`).
- **Automated Compaction**: Audit memory budgets using `scripts/compact_memory.py --check`.

## 6. Memory Pollution Prevention
- Keep `CURRENT.md` concise (< 30 lines) with only active objective, status, blockers, and next steps.
- Session logs are strictly chronological and append-only.
- Never write duplicate facts across multiple memory files.

## 7. Security Invariant
- **NEVER** store API keys, passwords, tokens, cookies, auth headers, private keys, or certificates in any memory file.
- All candidate writes are audited by `secret_scanner.py`.
