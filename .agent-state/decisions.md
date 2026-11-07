# Architectural & Implementation Decisions

## Decision 1: Subagent Tool Schema Normalization
- **Context**: Phase 1 defined subagent tool lists in `.agents/agents/*/agent.json` containing `read_file`, which is an invalid/hallucinated tool in Antigravity CLI.
- **Decision**: Purge `read_file` and replace with valid native tool `view_file` across all 9 agent definitions and skill references.
- **Rationale**: Prevents tool invocation failures and subagent runtime errors.

## Decision 2: Durable State Store Separation
- **Context**: Instruction.md Section 15 requires long tasks not to rely exclusively on chat context.
- **Decision**: Maintain `.agent-state/` for persistent phase tracking, separate from `.agents/memory/` and `.environment-audit/`.
- **Rationale**: Prevents context bloat and ensures reproducible resumption.

## Decision 3: Deterministic CLI Doctor Suite
- **Context**: Instruction.md Section 40 and 41 requires unified `agy-env-doctor` and 7 standalone domain doctor CLIs.
- **Decision**: Author Python/Bash CLI executables in `tools/bin/` with ASCII box formatting and explicit non-zero exit codes.
- **Rationale**: Deterministic diagnostic testing replaces model guesswork.
