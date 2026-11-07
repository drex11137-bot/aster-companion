# Project Procedures
Last Updated: 2026-10-07

## [2026-09-04] Memory Audit Diagnostic Procedure
- **Objective**: Execute memory doctor health evaluation before release or session termination.
- **Steps**:
  1. Verify working directory root (`/workspaces/codespaces-blank`).
  2. Execute diagnostic evaluation: `python3 scripts/memory_doctor.py`.
  3. Confirm zero secret leaks and verify predicate evaluations pass.
- **Verification**: Verified with exit code 0.

## [2026-10-07] Workstation Environment & Toolchain Synchronization
- **Objective**: Synchronize Antigravity CLI and system tool versions with recorded memory state.
- **Steps**:
  1. Check CLI version drift: `python3 scripts/version_sync.py --check`.
  2. Execute synchronization: `python3 scripts/version_sync.py` or `python3 scripts/memory_engine.py sync-version`.
  3. Validate updated versions in `~/.gemini/antigravity-cli/memory/ENVIRONMENT.md`.
- **Verification**: Live version (1.3.1) matches recorded state.

## [2026-10-07] Vector Index & Semantic Substrate Rebuild
- **Objective**: Rebuild and synchronize derived Milvus Lite vector store chunks with canonical Markdown memory.
- **Steps**:
  1. Run memory doctor with repair flag: `python3 scripts/memory_doctor.py --fix`.
  2. Rebuild index directly: `python3 scripts/memsearch_backend.py --rebuild`.
  3. Refresh retrieval benchmark telemetry: `python3 scripts/memory_benchmark.py --run`.
- **Verification**: Manifest reports all canonical files synchronized.

## [2026-10-07] Multi-Domain Workstation Verification
- **Objective**: Verify full workstation health across all 10 domain toolchains.
- **Steps**:
  1. Run environment doctor: `tools/bin/agy-env-doctor`.
  2. Run toolchain test script: `bash .devcontainer/scripts/verify-toolchain.sh`.
  3. Review status in `docs/test_reports/`.
- **Verification**: All 37 DoD criteria pass.
