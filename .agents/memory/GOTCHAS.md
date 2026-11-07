# Project Gotchas & Quirks
Last Updated: 2026-09-04

## 2026-09-01 — Secret Scanning Mechanism
**Type:** GOTCHA **Scope:** PROJECT **Confidence:** VERIFIED **Source:** secret_scanner.py **Status:** ACTIVE
### What
Any text containing API key patterns (e.g. `sk-`, `ghp_`, `AIza`) is rejected at write time by `secret_scanner.py`.
### Why
Prevent secrets from leaking into durable memory.
### Evidence
N/A
### Notes
N/A

## 2026-09-01 — Advisory Memory
**Type:** GOTCHA **Scope:** PROJECT **Confidence:** VERIFIED **Source:** POLICY.md **Status:** ACTIVE
### What
Repository state is authoritative. If code contradicts memory, code wins and memory must be updated with `Status: SUPERSEDED`.
### Why
Ensures we don't hallucinate.
### Evidence
N/A
### Notes
N/A

## 2026-09-01 — Context Window Conservation
**Type:** GOTCHA **Scope:** PROJECT **Confidence:** VERIFIED **Source:** instruction.md **Status:** ACTIVE
### What
Never cat or load all session files at once; load only the previous session summary during `/start-session`.
### Why
Save context window length.
### Evidence
N/A
### Notes
N/A

## 2026-09-01 — Gradle Daemon Memory Exhaustion
**Type:** GOTCHA **Scope:** PROJECT **Confidence:** VERIFIED **Source:** AGENTS.md **Status:** ACTIVE
### What
Gradle daemon crashes due to memory limits in container; always pass `--no-daemon` to gradle wrapper (`./gradlew`) to prevent daemon memory exhaustion.
### Why
Prevent container out-of-memory crashes during builds.
### Evidence
Documented in AGENTS.md Section 4 and test_memory_compiler.py.
### Notes
Verified in devcontainer builds.

## 2026-09-01 — Local ONNX Embedding Model
**Type:** GOTCHA **Scope:** PROJECT **Confidence:** VERIFIED **Source:** instruction.md **Status:** ACTIVE
### What
The application uses a local ONNX embedding model to avoid requiring an external embedding API.
### Why
Avoid requiring an external embedding API or cloud key, enabling local semantic vector retrieval with zero network transmission.
### Evidence
Documented in instruction.md Section 16; verified with local MemSearch ONNX provider.
### Notes
Uses local bge-m3 ONNX model for embeddings without third-party API dependencies.

