# SUBAGENT MEMORY HANDOFF PROTOCOL

## Overview
This document specifies the rules and architecture for how subagents handle memory in the Antigravity CLI environment. Subagents must inherit global rules, safely read project memory without cross-workspace contamination, and perform atomic handoffs.

## Context Propagation
When a main agent spawns a subagent, it MUST pass specific context pointers rather than copying all memory contents into the subagent prompt:
1. **Workspace Root**: The subagent must be explicitly given its `Cwd` (Current Working Directory).
2. **Relevant Context**: The main agent must select only the relevant subset of memory file paths from the `INDEX.md` and explicitly tell the subagent to load them if needed.

## Isolation Rules
1. **No Cross-Workspace Access**: A subagent spawned in `/workspaces/project-a` MUST NOT read from `/workspaces/project-b/.agents/memory/`. Any attempt to read outside the designated workspace memory root should be blocked or considered an isolation failure.
2. **Global Rules Inheritance**: Subagents can read from global memory `~/.gemini/antigravity-cli/memory/` and MUST apply global policies (like secret avoidance and atomic writing).

## Atomic Handoff and Writes
Subagents may discover new durable facts. To prevent concurrent write issues and corruption:
1. **Advisory Writes**: Subagents should prefer reporting findings back to the main agent via explicit messages, leaving the promotion to the main agent.
2. **Atomic Writes**: If a subagent must write memory directly, it MUST use atomic write patterns (write to `.tmp` file and rename).
3. **Locking**: Concurrent operations to `INDEX.md` or session files must avoid overwriting each other.

## Verification
A verification script `scripts/verify_subagent_memory.py` tests:
- Context propagation (ability to read right memory).
- Isolation (inability/refusal to read cross-workspace memory).
- Safe reporting / atomic handoff.
