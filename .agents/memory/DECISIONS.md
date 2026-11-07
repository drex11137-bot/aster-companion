# Project Architectural Decisions
Last Updated: 2026-09-01

## 2026-09-01 — ADR-001: 5-Tier Memory Architecture
**Type:** DECISION **Scope:** PROJECT **Confidence:** VERIFIED **Source:** docs/instruction.md **Status:** ACTIVE
### What
Decouple into Instructions, Durable Knowledge, Project Knowledge, Episodic Sessions, and Working State.
### Why
Needed a scalable memory system that prevents instruction bloat, cross-project contamination, and secret leakage.
### Evidence
Keeps prompt context minimal while preserving critical learnings.
### Notes
N/A

## 2026-09-01 — ADR-002: Dual Skill Entrypoints
**Type:** DECISION **Scope:** PROJECT **Confidence:** VERIFIED **Source:** docs/instruction.md **Status:** ACTIVE
### What
Create modular skill directories with YAML frontmatter in `.agents/skills/` and maintain flat definitions in `~/.gemini/antigravity-cli/skills/`.
### Why
Support both native Antigravity skill directories and flat markdown skill files.
### Evidence
N/A
### Notes
`.agents/skills/<name>/SKILL.md` is the canonical native skill format discovered by Antigravity CLI. Flat definitions in `~/.gemini/antigravity-cli/skills/` serve as early compatibility references.

## [2026-09-04] Adopt ninja-build and CMake for all native C/C++ builds to e
- **Context**: Identified during active development.
- **Decision**: Adopt ninja-build and CMake for all native C/C++ builds to enforce fast parallel incremental compilation.
- **Rationale**: Verified empirically via live execution.
- **Consequences**: Maintains system stability and governance.
- **Status**: Accepted

## 2026-09-05 — ADR-003: 3D Asset, Environment & Character Pipeline
**Type:** DECISION **Scope:** PROJECT **Confidence:** VERIFIED **Source:** Phase 4 Implementation **Status:** ACTIVE
### What
Implement decoupled `AssetManager`, procedural `TextureGenerator` (`THREE.DataTexture` Uint8Array), modular environment kit `ModularKit`, endless 5-chunk streaming `EnvironmentChunkManager`, and humanoid character pipeline `KiraVanceRig` with 9-state `AnimationStateMachine`.
### Why
Guarantees anti-slop visual fidelity, zero-allocation runtime performance, universal headless test execution across Node.js/Vitest, and network-resilient fallbacks for external 3D assets.
### Evidence
All 21 Vitest test suites (99/99 tests) pass; 13/13 Playwright E2E steps pass with 0 browser console errors.

