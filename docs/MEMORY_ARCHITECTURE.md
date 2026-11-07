# Antigravity Persistent Memory System

## 1. Architecture Overview
The Antigravity Persistent Memory System is an AI-first, hierarchical memory engine engineered for the Antigravity CLI (`agy`). It preserves high-value durable knowledge, architectural decisions, and runtime gotchas across sessions while strictly preventing memory bloat, context pollution, cross-project contamination, and secret leakage.

### 5-Layer Decoupled Memory Hierarchy
1. **Instructions**: Global `~/.gemini/GEMINI.md` and project `.agents/rules/` directives.
2. **Global Durable Knowledge**: `~/.gemini/antigravity-cli/memory/` containing cross-project tool, domain, and environmental truths.
3. **Project Durable Knowledge**: `.agents/memory/` containing repository-specific architectural decisions and gotchas.
4. **Episodic Sessions**: Chronological logs mapping the agent's work timeline (`sessions/`).
5. **Working State**: Active session tracking (`.agents/memory/CURRENT.md`).

## 2. Actual Directory Tree
### Global Memory (User-Level)
```
~/.gemini/antigravity-cli/memory
├── ENVIRONMENT.md
├── GENERAL.md
├── INDEX.md
├── POLICY.md
├── README.md
├── USER.md
├── domains/
├── projects/
├── sessions/
└── tools/
```

### Project Memory (Workspace-Level)
```
/workspaces/codespaces-blank/.agents/memory
├── ARCHITECTURE.md
├── CURRENT.md
├── DECISIONS.md
├── GOTCHAS.md
├── INDEX.md
└── sessions/
    └── 2026-09-01-1546.md
```

## 3. Data Models (Classification & Scope)
Memory candidates are classified across 9 types and a 0–5 durability scale:
- **0–1 (Discard)**: `EPHEMERAL`. No durable value.
- **2 (Session)**: `SESSION`. Active working state, archived on session end.
- **3 (Project)**: `PROJECT`, `DECISION`, `GOTCHA`, `ARCHITECTURE`. Bound to repository.
- **4 (Tool/Domain)**: `TOOL`, `DOMAIN`. Valid across repositories for specific tech stacks.
- **5 (Global)**: `GLOBAL`, `PROCEDURE`. Universal preferences and environment parameters.

## 4. Memory Lifecycle & 5. Startup Flow
1. **Session Start**: `scripts/memory_engine.py start-session` locates workspace, reads `INDEX.md`, identifies interrupted work in `CURRENT.md`, and compiles a tailored working context without loading the entire memory tree.
2. **During Work**: Agent references current filesystem as source of truth. Discovered insights are queued for classification.
3. **Session End (6. Shutdown Flow)**: `scripts/memory_engine.py end-session` logs work to `sessions/<timestamp>.md`, validates promotion candidates, updates durable knowledge (if accepted), and cleans `CURRENT.md`.

## 7. Promotion Rules
- **No Secrets**: Candidates are rejected if they contain tokens/keys (scanned by `secret_scanner.py`).
- **No Contradictions**: Rejects entries that contradict authoritative live repository state.
- **Deduplication**: Semantically identical facts are merged rather than duplicated.
- **Supersession**: Outdated facts are not silently deleted; they are marked `SUPERSEDED` for historical auditability.

## 8. Security Rules (Zero-Secrets Policy)
- **Scanning**: Candidate memory is scanned via entropy and regex checks before any write operation.
- **Execution Hook**: `pre_tool_security_gate.py` intercepts potentially sensitive file writes and shell commands.
- **Result**: If a secret is detected, the promotion is immediately aborted.

## 9. Validation & Deterministic Checks
- Validated via `scripts/audit_memory.py`.
- Checks index integrity, broken references, oversized files, contradictory facts, and project-scope violations.
- Outputs strict `PASS`, `FAIL`, or `UNTESTED` verdicts.

## 10. Recovery & 11. Troubleshooting
- **Interrupted Session**: Relaunch via `start-session`. The system reads `CURRENT.md` to resume exactly where it left off.
- **Corrupted Memory**: Run `audit-memory` to identify discrepancies, followed by `reorganize-memory` to compact and sync indexes.
- **Stale Memory**: Always prefer repository state. If memory claims `Python 3.10` but `pyproject.toml` claims `3.12`, the file is authoritative.

## 12. Supported Antigravity Version & 13. Limitations
- **Supported Target**: Antigravity CLI.
- **Limitations**: Semantic vector search is not natively implemented; relies on lexical and deterministic path indexing. Hooks rely on CLI support for `hooks.json`.

## 14. Backup Strategy
- **Workspace Memory** (`.agents/memory/`): Commit directly to Git. Use standard `.gitignore` rules to exclude ephemeral files if necessary.
- **Global Memory** (`~/.gemini/antigravity-cli/memory/`): Sync via dotfiles or private vault.

## 15. Extension Points
- Implement custom `pre_tool_use` / `post_tool_use` hooks in `scripts/hooks/` to augment telemetry.
- Add advanced regex heuristics to `scripts/secret_scanner.py`.
- Define new reusable operations in `skills/`.
