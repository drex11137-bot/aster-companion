# Antigravity Workstation Operations & Runbook Guide

This document defines the operational procedures, daily commands, diagnostic suites, repair workflows, performance classifications, and long-horizon execution models for the Antigravity engineering workstation.

---

## 1. Daily Commands & Diagnostic Suite

The workstation provides both unified and specialized domain diagnostic tools. Use these commands to inspect environment health, diagnose regressions, and verify subsystem functionality.

### Command Reference

| Command / Script | Primary Domain | Purpose & When to Use | Execution Speed |
| :--- | :--- | :--- | :--- |
| `agy-env-doctor` | Unified Workstation | Run at session start or after config changes. Verifies all 64+ workstation invariants. | `FAST (~3s)` |
| `agy-agent-doctor` | Agent Platform | Run when diagnosing Antigravity agent configuration, subagents, skills, and memory state. | `FAST (~1s)` |
| `agy-mcp-doctor` | Model Context Protocol | Run when diagnosing MCP server definitions, JSON configuration, and socket connectivity. | `FAST (~1s)` |
| `agy-android-doctor` | Android & Mobile RE | Run when troubleshooting Android SDK, ADB, Gradle, and reverse engineering toolchains. | `FAST (~2s)` |
| `agy-web-doctor` | Web & Frontend | Run when troubleshooting Node.js, package managers (npm, yarn, pnpm), and Playwright. | `FAST (~2s)` |
| `agy-binary-doctor` | Binary Analysis & SRE | Run when diagnosing native compilers, debuggers, Ghidra, Radare2, Rizin, and Checksec. | `FAST (~2s)` |
| `agy-wasm-doctor` | WebAssembly Stack | Run when diagnosing WABT, Wasmtime, Wasmer, Wasm-opt, and Clang wasm32 toolchains. | `FAST (~1s)` |
| `agy-security-doctor` | Security & SAST | Run when verifying Semgrep, CodeQL, Gitleaks, Trivy, Bandit, and OSV-Scanner readiness. | `FAST (~2s)` |
| `agy-network-doctor` | Network & PCAP | Run when verifying TShark, Tcpdump, Capinfos, Editcap, Mergecap, Nmap, and Scapy. | `FAST (~1s)` |
| `bash .devcontainer/scripts/verify-toolchain.sh` | Core CLI & Languages | 37-point deterministic verification of core compilers, runtimes, and build tools. | `FAST (~2s)` |
| `bash .devcontainer/scripts/verify-android.sh` | Android Build & RE | Full build & RE verification across APK decompilation, signing, and unit testing. | `MEDIUM (~10s)` |
| `bash .devcontainer/scripts/verify-binary-stack.sh` | Binary SRE & WASM | Full Ghidra headless decompiler analysis and WASM pipeline execution. | `MEDIUM (~15s)` |
| `bash .devcontainer/scripts/verify-security-stack.sh` | Security Scanners | Executes live vulnerability and secret detection runs against test fixtures. | `MEDIUM (~12s)` |
| `bash .devcontainer/scripts/verify-network-stack.sh` | Network Forensics | Dissects sample PCAP fixture, asserts DNS/TCP extraction, tests Scapy generation. | `FAST (~2s)` |
| `bash .devcontainer/scripts/verify-mcp.sh` | Model Context Protocol | Validates all 6 configured MCP servers, env vars, and command executables. | `FAST (~1s)` |
| `bash .devcontainer/scripts/bootstrap.sh` | Workstation Init | Run upon provisioning a fresh container or restoring environment state. | `FAST (~5s)` |

---

## 2. Operation Performance Tiers

Operations in the Codespace are classified by resource intensity to guide agent execution and prevent memory or CPU exhaustion:

```text
+-----------------------------------------------------------------------------------------+
| FAST TIER (< 5 seconds, Minimal RAM)                                                    |
| - `agy-env-doctor`, `verify-toolchain.sh`, `verify-mcp.sh`, `verify-network-stack.sh`   |
| - Ripgrep code searches (`rg`), AST parsing with Semgrep, Gitleaks secret scans        |
| - Wasmtime executions, Radare2/Rizin disassembly, Capinfos PCAP summaries               |
+-----------------------------------------------------------------------------------------+
                                             │
                                             ▼
+-----------------------------------------------------------------------------------------+
| MEDIUM TIER (5 - 30 seconds, Moderate RAM)                                              |
| - Full C/C++ builds (`cmake -B build -G Ninja && ninja -C build`)                       |
| - Android APK decompilation (`apktool d`, `jadx -d`) and Smali assembly                 |
| - Playwright headless browser E2E test runs (`npx playwright test`)                     |
| - Ghidra Headless ELF analysis (`analyzeHeadless`) on moderate-sized binaries           |
| - Bandit and Pip-Audit Python package vulnerability scans                               |
+-----------------------------------------------------------------------------------------+
                                             │
                                             ▼
+-----------------------------------------------------------------------------------------+
| HEAVY TIER (> 30 seconds, High RAM / High CPU)                                          |
| - Complete CodeQL database creation and semantic query evaluation                       |
| - Full Android Gradle release builds (`./gradlew assembleRelease --no-daemon`)          |
| - Deep Trivy container filesystem and rootfs vulnerability scanning                     |
| - Multi-binary bulk Ghidra decompiler passes across extensive firmware images          |
| Note: Always run with `--no-daemon` and manage background tasks carefully.             |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Systematic Subsystem Repair Workflow

When a tool, script, or test fails, follow this deterministic 6-step recovery model:

```text
       Subsystem Failure Detected
                   │
                   ▼
  1. RUN DIAGNOSTIC DOCTOR
     Execute `agy-env-doctor` to pinpoint the failing component.
                   │
                   ▼
  2. ISOLATE DOMAIN RUNBOOK
     Run the targeted domain script (e.g. `verify-android.sh`, `verify-binary-stack.sh`).
                   │
                   ▼
  3. CONSULT COMPATIBILITY MATRIX
     Check `docs/compatibility-matrix.md` to verify whether the failure is a known
     platform boundary (e.g., KVM hardware limitation, headless X11 absence).
                   │
                   ▼
  4. EXECUTE REMEDIATION
     - Fix pathing, environment variables, or package dependencies.
     - Apply headless or offline mitigation if platform-constrained.
                   │
                   ▼
  5. RERUN VERIFICATION SUITE
     Verify the repair by rerunning the domain doctor and `agy-env-doctor`.
                   │
                   ▼
  6. UPDATE DURABLE STATE
     Record the failure, root cause, and fix in `.agent-state/decisions.md`
     and `.agents/memory/GOTCHAS.md`.
```

---

## 4. Long-Horizon Task Execution Protocol

For complex, multi-phase tasks spanning multiple subagents and invocations, agents MUST follow the structured lifecycle:

1. **PLAN**: Inspect repository, detect project type, select domain skillbook, and outline milestones.
2. **CHECKPOINT 1**: Record objectives and active priorities in `.agent-state/current-state.md`.
3. **IMPLEMENT**: Make small, controlled, modular modifications. Preserve existing documentation and comments.
4. **VERIFY**: Run domain unit tests, compilers, linters, and security scanners. Gather empirical evidence.
5. **CHECKPOINT 2**: Update `.agent-state/completed-work.md` with verified milestones and test outputs.
6. **REVIEW**: Perform adversarial review or delegate to `adversarial-reviewer` to probe edge cases.
7. **REPAIR**: Address any findings or regressions flagged by the review.
8. **FINALIZE**: Update memory indexes, compact `CURRENT.md`, and author the completion report.

---

## 5. Session Initialization & Handoff Runbook

### Starting a New Session
1. Execute `/start-session` or inspect `.agent-state/current-state.md` and `.agents/memory/CURRENT.md`.
2. Run `python3 tools/bin/agy-env-doctor` to confirm workstation readiness.
3. Review `.agent-state/blockers.md` and `.agent-state/decisions.md` to restore architectural context without re-reading entire transcripts.

### Ending / Suspending a Session
1. Verify no orphan background tasks remain active via `manage_task(Action='list')`.
2. Compact active working state into `.agent-state/current-state.md` (< 30 lines).
3. Write an episodic log in `.agents/memory/sessions/` detailing achievements and next steps.
4. Commit verified code changes with clean commit messages.
