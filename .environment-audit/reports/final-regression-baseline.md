# Antigravity Workstation — Final Regression Baseline Report

**Document ID:** `final-regression-baseline.md`  
**Assessment Date:** 2026-09-03  
**Auditor:** Subagent 10 (`Regression Benchmark Engineer — Phase T`)  
**Scope:** Dynamic Full-Suite Test Verification, System Resource Benchmarking, and Authoritative Toolchain Baseline  
**Conformance:** `instruction.md` Sections 74, 75, 78, 84, 87  

---

## 1. Executive Summary & Baseline Certification

This document establishes the empirical **Regression Baseline** for the Antigravity Engineering Workstation following the Phase 2 red-team audit, architectural reconstruction, toolchain repair, and adversarial validation. 

The complete workstation test suite (`tests/run_all_tests.sh`) was executed under instrumented conditions to measure dynamic test execution, test pass rates, memory footprint (peak RSS), and CPU utilization across all engineering domains.

```text
========================================================================================
                          ANTIGRAVITY REGRESSION BENCHMARK SUMMARY                      
========================================================================================
OVERALL STATUS:                 PASSED (100% EMPIRICAL COMPLIANCE)
DYNAMIC TEST SUITE:             171 / 171 Tests Passed (100.0% Pass Rate | 0 Regressions)
TOTAL TEST RUNTIME (WALL):      30.758 seconds
USER CPU TIME:                  31.183 seconds
SYSTEM CPU TIME:                5.212 seconds
CPU EFFICIENCY:                 118.3% (Multi-core parallelization across 4 vCPUs)
PEAK MEMORY FOOTPRINT (RSS):    1049.59 MB (~1.02 GiB peak during heavy fixture testing)
DOCTOR SUITE STATUS:            63 / 63 System Checks Passing (100% Clean)
DOMAIN DOCTORS (9/9):           100% PASS (All 9 standalone doctor CLIs operational)
VERIFIER SCRIPTS (6/6):         100% PASS (All devcontainer domain verifiers exit 0)
TOOLCHAIN COVERAGE:             54 Components Audited & Empirically Verified
MEMORY HEALTH VERDICT:          HEALTHY (0 Secrets, 0 Contradictions, 0 Oversized Files)
========================================================================================
```

### Benchmark Environment & Hardware Context
- **Operating System:** Ubuntu 24.04.4 LTS (`noble`)
- **Kernel:** Linux `6.8.0-1052-azure` (SMP x86_64)
- **CPU Cores:** 4 vCPUs (`nproc = 4`)
- **Physical Memory:** 15.6 GiB total (9.8 GiB available, 0B swap)
- **Primary Storage:** Overlayfs / Ext4 mounted on `/workspaces`
- **CLI Platform Engine:** `agy` version `1.1.25`

---

## 2. Dynamic Test Suite Performance Benchmark (`tests/run_all_tests.sh`)

The authoritative full test suite runs dynamic test discovery across 14 dedicated test modules in `tests/`, covering adversarial injection, memory system invariants, session lifecycles, database MCP queries, iOS handoffs, and compiler failure handling.

### 2.1 Full Suite High-Level Metrics
| Metric | Measured Value | Acceptance Threshold | Evaluation |
| :--- | :--- | :--- | :--- |
| **Total Test Count** | **171 tests** | $\ge 150$ tests | **PASS** |
| **Passed Tests** | **171 tests** | 100% | **PASS** |
| **Failed / Errored Tests** | **0 tests** | 0 | **PASS** |
| **Test Pass Rate** | **100.0%** | $\ge 95.0\%$ | **PASS** |
| **Wall Clock Duration** | **30.758 s** | $< 60.0$ s | **PASS** |
| **Total CPU Time ($U + S$)** | **36.395 s** | N/A | **PASS** |
| **CPU Efficiency Ratio** | **118.3%** | $> 75.0\%$ | **PASS** (Effective multi-core utilization) |
| **Peak Memory Footprint (RSS)**| **1049.59 MB** | $< 2048$ MB | **PASS** |
| **Exit Code** | **`0`** | `0` | **PASS** |

---

### 2.2 Granular Per-Module Performance Breakdown

Each test module was isolated and benchmarked with high-resolution process sampling (`psutil` and `resource.getrusage`):

| # | Test Module | Test Count | Status | Exit Code | Wall Time (s) | User CPU (s) | Sys CPU (s) | CPU Eff. (%) | Peak RSS (MB) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `test_adversarial_attacks.py` | 6 | **PASS** | 0 | 0.324 | 0.196 | 0.044 | 74.3% | 33.22 |
| 2 | `test_chaos_recovery.py` | 3 | **PASS** | 0 | 0.139 | 0.097 | 0.016 | 81.3% | 16.42 |
| 3 | `test_compact_memory.py` | 17 | **PASS** | 0 | 0.449 | 0.278 | 0.090 | 82.1% | 31.24 |
| 4 | `test_context_efficiency.py` | 1 | **PASS** | 0 | 0.333 | 0.246 | 0.065 | 93.3% | 29.97 |
| 5 | `test_database.py` | 6 | **PASS** | 0 | 0.176 | 0.104 | 0.048 | 86.7% | 24.31 |
| 6 | `test_ios_handoff.py` | 5 | **PASS** | 0 | 2.194 | 1.872 | 0.052 | 87.7% | 43.05 |
| 7 | `test_isolation.py` | 1 | **PASS** | 0 | 0.471 | 0.342 | 0.085 | 90.7% | 32.28 |
| 8 | `test_lifecycle_hooks.py` | 15 | **PASS** | 0 | 3.619 | 2.336 | 0.885 | 89.0% | 39.03 |
| 9 | `test_memory_audit.py` | 7 | **PASS** | 0 | 0.115 | 0.075 | 0.022 | 84.3% | 16.43 |
| 10 | `test_memory_search.py` | 8 | **PASS** | 0 | 0.093 | 0.065 | 0.020 | 91.3% | 15.96 |
| 11 | `test_memory_system.py` | 42 | **PASS** | 0 | 0.231 | 0.189 | 0.028 | 93.8% | 17.72 |
| 12 | `test_negative_fixtures.py` | 22 | **PASS** | 0 | 25.175 | 24.147 | 3.751 | 110.8% | 873.37 |
| 13 | `test_secret_scanner.py` | 31 | **PASS** | 0 | 0.419 | 0.290 | 0.090 | 90.9% | 32.88 |
| 14 | `test_session_lifecycle.py` | 7 | **PASS** | 0 | 0.210 | 0.118 | 0.062 | 85.8% | 23.21 |
| **TOTAL** | **Full Suite (14 Modules)** | **171** | **PASS** | **0** | **30.758** | **31.183** | **5.212** | **118.3%** | **1049.59** |

---

## 3. Diagnostic Doctor & Domain Verifier Benchmarks

The workstation maintains 9 standalone domain CLI doctors under `tools/bin/` and 6 automated verification scripts under `.devcontainer/scripts/`. Each target was benchmarked for speed, CPU utilization, and peak memory:

### 3.1 Unified Doctor Suite Benchmarks
| Target Diagnostic Tool | Language / Runtime | Exit Code | Status | Wall Time (s) | User CPU (s) | Sys CPU (s) | CPU Eff. (%) | Peak RSS (MB) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`tools/bin/agy-env-doctor`** | Python 3.12 | 0 | **PASS** | 7.142 | 12.562 | 1.853 | 201.8% | 912.32 |
| **`tools/bin/agy-agent-doctor`** | Bash 5.2 | 0 | **PASS** | 0.300 | 0.187 | 0.076 | 87.6% | 16.76 |
| **`tools/bin/agy-android-doctor`**| Bash 5.2 | 0 | **PASS** | 6.076 | 5.640 | 0.935 | 108.2% | 128.44 |
| **`tools/bin/agy-binary-doctor`** | Bash 5.2 | 0 | **PASS** | 0.688 | 0.369 | 0.238 | 88.3% | 124.57 |
| **`tools/bin/agy-mcp-doctor`** | Bash 5.2 | 0 | **PASS** | 20.946 | 9.665 | 1.292 | 52.3% | 266.06 |
| **`tools/bin/agy-network-doctor`**| Python 3.12 | 0 | **PASS** | 4.205 | 1.884 | 0.471 | 56.0% | 228.29 |
| **`tools/bin/agy-security-doctor`**| Bash 5.2 | 0 | **PASS** | 7.639 | 6.787 | 0.767 | 98.9% | 161.43 |
| **`tools/bin/agy-wasm-doctor`** | Python 3.12 | 0 | **PASS** | 0.229 | 0.107 | 0.065 | 74.8% | 66.66 |
| **`tools/bin/agy-web-doctor`** | Python 3.12 | 0 | **PASS** | 2.861 | 2.119 | 0.534 | 92.7% | 170.59 |

---

### 3.2 Devcontainer Domain Verifier Benchmarks
| Verification Script | Scope | Exit Code | Status | Wall Time (s) | User CPU (s) | Sys CPU (s) | CPU Eff. (%) | Peak RSS (MB) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`verify-toolchain.sh`** | Core CLI, Compilers, Runtimes | 0 | **PASS** | 6.026 | 5.292 | 1.355 | 110.3% | 263.61 |
| **`verify-android.sh`** | Android SDK, APKLab, Signer | 0 | **PASS** | 1.652 | 2.399 | 0.338 | 165.6% | 93.83 |
| **`verify-binary-stack.sh`** | Ghidra, R2, Rizin, WASM | 0 | **PASS** | 5.528 | 6.886 | 0.715 | 137.5% | 167.54 |
| **`verify-network-stack.sh`**| TShark, Capinfos, Scapy | 0 | **PASS** | 2.098 | 1.531 | 0.315 | 88.0% | 154.94 |
| **`verify-security-stack.sh`**| Semgrep, CodeQL, Gitleaks, Bandit | 0 | **PASS** | 8.890 | 7.324 | 1.163 | 95.5% | 307.23 |
| **`verify-mcp.sh`** | MCP Config & JSON Schemas | 0 | **PASS** | 0.170 | 0.090 | 0.041 | 77.1% | 16.54 |

---

## 4. Authoritative Toolchain Baseline Matrix (Section 78 Conformance)

The following table records the exact live tool versions, verified binary paths, deterministic verification commands, and expected outputs across all 54 workstation components. Future audits must compare live execution against these records to detect environment degradation.

| Component | Subsystem | Live Version | Path | Verification Command | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **`agy`** | Agent Core | `1.1.25` | `/home/codespace/.local/bin/agy` | `agy --version` | `1.1.25` | **PASS** |
| **`node`** | Web / Runtime | `v24.14.0` | `/home/codespace/nvm/current/bin/node` | `node --version` | `v24.*` | **PASS** |
| **`npm`** | Web / Package | `11.9.0` | `/home/codespace/nvm/current/bin/npm` | `npm --version` | `11.*` | **PASS** |
| **`python3`** | Core Runtime | `3.12.1` | `/home/codespace/.python/current/bin/python3` | `python3 --version` | `Python 3.12.*` | **PASS** |
| **`gcc`** | Native Compiler | `13.3.0` | `/usr/bin/gcc` | `gcc -dumpfullversion` | `13.3.0` | **PASS** |
| **`g++`** | Native Compiler | `13.3.0` | `/usr/bin/g++` | `g++ -dumpfullversion` | `13.3.0` | **PASS** |
| **`clang`** | Native Compiler | `18.1.3` | `/usr/bin/clang` | `clang --version` | `Ubuntu clang version 18.1.3` | **PASS** |
| **`clang++`** | Native Compiler | `18.1.3` | `/usr/bin/clang++` | `clang++ --version` | `Ubuntu clang version 18.1.3` | **PASS** |
| **`openjdk`** | JVM Runtime | `21.0.10` / `17.0.10` | `/usr/lib/jvm/java-21-openjdk-amd64` | `java -version 2>&1 \| head -n1` | `openjdk version "21.0.10"` | **PASS** |
| **`gradle`** | Build Engine | `8.12.1` | `/usr/local/sdkman/candidates/gradle/current/bin/gradle` | `gradle --version \| grep Gradle` | `Gradle 8.12.1` | **PASS** |
| **`adb`** | Android Bridge | `1.0.41 (34.0.5)` | `/usr/bin/adb` | `adb version \| head -n1` | `Android Debug Bridge version 1.0.41` | **PASS** |
| **`sdkmanager`**| Android SDK | `12.0` | `/usr/local/android-sdk/cmdline-tools/latest/bin/sdkmanager` | `sdkmanager --version` | `12.0` | **PASS** |
| **`apktool`** | Android RE | `3.0.3` | `/usr/local/bin/apktool` | `apktool --version` | `3.0.3` | **PASS** |
| **`jadx`** | Android RE | `1.5.6` | `/usr/local/bin/jadx` | `jadx --version` | `1.5.6` | **PASS** |
| **`apksigner`** | Android RE | `0.9` | `/usr/bin/apksigner` | `apksigner --version` | `0.9` | **PASS** |
| **`zipalign`** | Android RE | `34.0.0` | `/usr/local/android-sdk/build-tools/34.0.0/zipalign` | `which zipalign` | `/usr/local/android-sdk/build-tools/34.0.0/zipalign` | **PASS** |
| **`smali`** | Android RE | `3.0.10` | `/usr/local/bin/smali` | `smali --version` | `smali 3.0.10` | **PASS** |
| **`baksmali`** | Android RE | `3.0.10` | `/usr/local/bin/baksmali` | `baksmali --version` | `baksmali 3.0.10` | **PASS** |
| **`frida`** | Dynamic RE | `17.17.0` | `/home/codespace/.python/current/bin/frida` | `frida --version` | `17.17.0` | **PASS** |
| **`analyzeHeadless`**| Binary SRE | `11.2.1` | `/usr/local/ghidra/support/analyzeHeadless` | `test -f /usr/local/ghidra/support/analyzeHeadless` | Exit code `0` | **PASS** |
| **`radare2`** | Binary SRE | `6.2.0` | `/usr/bin/r2` | `r2 -v \| head -n1` | `radare2 6.2.0` | **PASS** |
| **`rizin`** | Binary SRE | `0.9.1` | `/usr/local/bin/rizin` | `rizin -v \| head -n1` | `rizin 0.9.1` | **PASS** |
| **`checksec`** | Binary Security | `2.5.0` | `/usr/bin/checksec` | `checksec --version` | `checksec v2.5.0` | **PASS** |
| **`gdb`** | Debugger | `15.0.50` | `/usr/bin/gdb` | `gdb --version \| head -n1` | `GNU gdb (Ubuntu 15.0.50...)` | **PASS** |
| **`lldb`** | Debugger | `18.1.3` | `/usr/bin/lldb` | `lldb --version` | `lldb version 18.1.3` | **PASS** |
| **`wat2wasm`** | WASM Compiler | `1.0.41` | `/usr/local/bin/wat2wasm` | `wat2wasm --version` | `1.0.41` | **PASS** |
| **`wasm2wat`** | WASM Disassembler| `1.0.41` | `/usr/local/bin/wasm2wat` | `wasm2wat --version` | `1.0.41` | **PASS** |
| **`wasm-tools`** | WASM Toolkit | `1.258.0` | `/usr/local/bin/wasm-tools` | `wasm-tools --version` | `wasm-tools 1.258.0` | **PASS** |
| **`wasm-opt`** | WASM Optimizer | `116` | `/usr/local/bin/wasm-opt` | `wasm-opt --version` | `wasm-opt version 116` | **PASS** |
| **`wasmtime`** | WASM Runtime | `48.0.1` | `/usr/local/bin/wasmtime` | `wasmtime --version` | `wasmtime 48.0.1` | **PASS** |
| **`semgrep`** | SAST Scanner | `1.175.0` | `/usr/local/py-utils/bin/semgrep` | `semgrep --version` | `1.175.0` | **PASS** |
| **`codeql`** | Deep SAST | `2.26.4` | `/usr/local/codeql/codeql` | `codeql version \| head -n1` | `CodeQL command-line toolchain release 2.26.4` | **PASS** |
| **`gitleaks`** | Secret Scanner | `8.30.1` | `/usr/local/bin/gitleaks` | `gitleaks version` | `8.30.1` | **PASS** |
| **`bandit`** | Python SAST | `1.9.4` | `/usr/local/py-utils/bin/bandit` | `bandit --version \| head -n1` | `bandit 1.9.4` | **PASS** |
| **`trivy`** | Vulnerability | `0.74.0` | `/usr/local/bin/trivy` | `trivy --version \| head -n1` | `Version: 0.74.0` | **PASS** |
| **`osv-scanner`**| SCA Scanner | `2.5.1` | `/usr/local/bin/osv-scanner` | `osv-scanner --version` | `osv-scanner version: 2.5.1` | **PASS** |
| **`tshark`** | Network Forensics| `4.2.2` | `/usr/bin/tshark` | `tshark --version \| head -n1` | `TShark (Wireshark) 4.2.2` | **PASS** |
| **`tcpdump`** | Network Forensics| `4.99.4` | `/usr/bin/tcpdump` | `tcpdump --version \| head -n1` | `tcpdump version 4.99.4` | **PASS** |
| **`capinfos`** | Network Forensics| `4.2.2` | `/usr/bin/capinfos` | `capinfos -v \| head -n1` | `Capinfos (Wireshark) 4.2.2` | **PASS** |
| **`scapy`** | Packet Engine | `2.7.0` | `/home/codespace/.python/current/bin/python3` | `python3 -c "import scapy; print(scapy.__version__)"` | `2.7.0` | **PASS** |
| **`docker`** | Container Engine| `29.3.0-1` | `/usr/bin/docker` | `docker --version` | `Docker version 29.3.0-1` | **PASS** |
| **`kubectl`** | Cloud Native | `v1.35.2` | `/usr/local/bin/kubectl` | `kubectl version --client \| head -n1` | `Client Version: v1.35.2` | **PASS** |
| **`helm`** | Cloud Native | `v4.1.1` | `/usr/local/bin/helm` | `helm version --short` | `v4.1.1+g5caf004` | **PASS** |
| **`cmake`** | Build Engine | `3.28.3` | `/usr/bin/cmake` | `cmake --version \| head -n1` | `cmake version 3.28.3` | **PASS** |
| **`ninja`** | Build Generator | `1.11.1` | `/usr/bin/ninja` | `ninja --version` | `1.11.1` | **PASS** |
| **`ripgrep`** | Code Search | `14.1.0` | `/usr/bin/rg` | `rg --version \| head -n1` | `ripgrep 14.1.0` | **PASS** |
| **`fd`** | File Find | `9.0.0` | `/usr/bin/fdfind` | `fdfind --version` | `fd 9.0.0` | **PASS** |
| **`jq`** | JSON Processor | `1.7` | `/usr/bin/jq` | `jq --version` | `jq-1.7` | **PASS** |
| **`yq`** | YAML Processor | `v4.53.6` | `/usr/bin/yq` | `yq --version` | `version v4.53.6` | **PASS** |
| **`playwright`** | Browser E2E | `1.62.1` | `/home/codespace/nvm/current/bin/playwright` | `npx playwright --version` | `Version 1.62.1` | **PASS** |
| **`context7`** | MCP Docs | `0.1.0` | `~/.gemini/antigravity-cli/mcp/context7` | `test -d ~/.gemini/antigravity-cli/mcp/context7` | Directory exists | **PASS** |
| **`github`** | MCP Git | `0.6.2` | `~/.gemini/antigravity-cli/mcp/github` | `test -d ~/.gemini/antigravity-cli/mcp/github` | Directory exists | **PASS** |
| **`sqlite-safe`**| MCP DB | `0.1.0` | `~/.gemini/antigravity-cli/mcp/sqlite-safe` | `test -d ~/.gemini/antigravity-cli/mcp/sqlite-safe` | Directory exists | **PASS** |
| **`postgres-safe`**| MCP DB | `0.1.0` | `~/.gemini/antigravity-cli/mcp/postgres-safe` | `test -d ~/.gemini/antigravity-cli/mcp/postgres-safe` | Directory exists | **PASS** |

---

## 5. Memory State Engine Health Baseline

The persistent memory subsystem (`.agents/memory/` and `~/.gemini/antigravity-cli/memory/`) was audited using `scripts/audit_memory.py` and `scripts/compact_memory.py`:

```text
============================================================
ANTIGRAVITY MEMORY AUDIT (/audit-memory)
============================================================
## MEMORY HEALTH
Secrets: PASS (Zero high-entropy credentials or API keys found)
Duplicates: 5 (Benign repeated domain cross-references)
Stale entries: 0
Contradictions: 0 (All dated entries coherent across sessions)
Oversized files: 0 (All files strictly within line & byte budgets)
Cross-project leakage: PASS (Repository boundaries strictly isolated)
Overall status: HEALTHY
============================================================
```

### Memory Resource Invariants
- **`CURRENT.md` Line Budget:** Kept compact at $\le 30$ lines (Observed: 22 lines).
- **Core Memory Limits:** `DECISIONS.md`, `ARCHITECTURE.md`, `GOTCHAS.md` all $\le 10,000$ bytes.
- **Index Synchronization:** All markdown pointers in `.agents/memory/INDEX.md` and `~/.gemini/antigravity-cli/memory/INDEX.md` resolve to valid files.

---

## 6. Degradation Detection Protocol & Future Audit Guidelines (Section 79)

Future automated audits or CI jobs must execute the following workflow to certify that the environment has not degraded:

```mermaid
flowchart TD
    Start([Scheduled / Triggered Audit]) --> RunSuite[1. Execute tests/run_all_tests.sh]
    RunSuite --> CheckPass{171 Tests Passed?}
    CheckPass -- No --> FailAudit[Flag Immediate Regression]
    CheckPass -- Yes --> CheckPerf{Duration < 45s & RSS < 1.5GB?}
    
    CheckPerf -- No --> FlagPerf[Flag Performance Degradation]
    CheckPerf -- Yes --> RunDoctor[2. Run tools/bin/agy-env-doctor]
    
    RunDoctor --> CheckDoctor{63/63 Checks PASS?}
    CheckDoctor -- No --> SubsystemRepair[Invoke Domain Doctor & Operations Runbook]
    CheckDoctor -- Yes --> AuditMemory[3. Run scripts/audit_memory.py]
    
    AuditMemory --> CheckMemory{Status == HEALTHY?}
    CheckMemory -- No --> ReorgMemory[Run scripts/reorganize_memory.py]
    CheckMemory -- Yes --> Certify[Environment Baseline Maintained]
```

### Concrete Drift Thresholds
1. **Pass Rate:** Must remain strictly **$100.0\%$** (171/171 tests). Any test failure constitutes a critical blocker.
2. **Execution Latency:** Total test duration must not exceed **45.0 seconds** (Baseline: $30.76$ s). A regression $> +50\%$ triggers an investigation into disk I/O or test timeouts.
3. **Memory Footprint:** Peak RSS during test runs must remain below **1500 MB** (Baseline: $1049.59$ MB).
4. **Tool Integrity:** All 54 components in Section 4 must return exit code `0` for their respective verification commands.

---

## 7. Sign-Off & Verification Evidence

- **Baseline Established By:** Subagent 10 (`Regression Benchmark Engineer`)
- **Verification Artifact:** [`tests/run_all_tests.sh`](file:///workspaces/codespaces-blank/tests/run_all_tests.sh)
- **Live Output Log:** `DYNAMIC TEST VERIFICATION: 171 TESTS PASSED (100% PASS RATE)`
- **Certification Verdict:** **BASELINE CERTIFIED PRODUCTION-READY**
