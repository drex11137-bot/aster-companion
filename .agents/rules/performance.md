# Performance & Token Optimization Governance Rule

This rule governs token conservation, context budget management, and progressive disclosure for the Antigravity Persistent Memory System.

## 1. Index-First Loading (Mandatory Progressive Disclosure)
- **Always load index first**: Before loading any specific memory document, inspect `.agents/memory/INDEX.md` (or global `~/.gemini/antigravity-cli/memory/INDEX.md`).
- **Load only relevant files**: Never inject the full memory directory or historical session archives into the prompt context.
- **Context Budget Guard**: Loaded memory must remain lean (target < 5% of model context window, never exceeding 10%).

## 2. Line & Byte Budgets
All memory files must adhere to strict size ceilings:

| File Type | Line Budget | Byte Budget | Token Target | Description |
| :--- | :--- | :--- | :--- | :--- |
| `CURRENT.md` | **< 30 lines** | < 2,048 bytes | ~500 tokens | Ephemeral working state; focus exclusively on current task |
| `INDEX.md` | **< 50 lines** | < 4,096 bytes | ~1,000 tokens | Table of pointers to memory artifacts |
| `POLICY.md` | **< 80 lines** | < 6,144 bytes | ~1,500 tokens | Core governance and rules |
| `GEMINI.md` | **< 100 lines** | < 8,192 bytes | ~2,000 tokens | Operating principles and identity |
| `GOTCHAS.md` | **< 100 lines** | < 8,192 bytes | ~2,000 tokens | Critical traps and environment quirks |
| `DECISIONS.md` | **< 200 lines** | < 16,384 bytes | ~4,000 tokens | Architectural Decision Records (ADRs) |
| `ARCHITECTURE.md` | **< 200 lines** | < 16,384 bytes | ~4,000 tokens | Structural topology and patterns |
| `sessions/*.md` | **< 150 lines** | < 12,288 bytes | ~3,000 tokens | Session logs (archival, chronological) |

## 3. Strict Deduplication & Pointer Strategy
- **Single Source of Truth**: A fact or decision must be recorded in exactly one durable file.
- **Prefer Pointers over Duplication**: When referencing knowledge from another memory file, use relative markdown links or anchor pointers rather than duplicating content:
  - *Do*: `See [DECISIONS.md#adr-002](file:///workspaces/codespaces-blank/.agents/memory/DECISIONS.md#adr-002) for vector indexing rationale.`
  - *Don't*: Re-paste the entire rationale or architecture diagram in `CURRENT.md` or `GOTCHAS.md`.

## 4. Chronological Session Management
- Session log files must be named chronologically: `sessions/YYYY-MM-DD-HHMM.md`.
- Session entries within files must be ordered in strict chronological sequence.
- Completed session notes must never remain in `CURRENT.md`; they must be flushed to the active session file.

## 5. Automated Compaction & Auditing
- Memory compaction and budget enforcement are audited via `scripts/compact_memory.py`.
- Run audit: `python3 scripts/compact_memory.py --check`
- Run auto-compaction: `python3 scripts/compact_memory.py --enforce`
