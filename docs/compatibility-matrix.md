# Antigravity Workstation Platform Compatibility Matrix

**Authoritative Multi-Domain Compatibility, Constraints & Fallbacks**  
**Assessment Date:** 2026-10-07  
**Verified By:** Subagent 21 (`Documentation & Acceptance Officer`)  
**Conformance:** `instruction.md` Section 52  

---

## 1. Executive Platform Compatibility Matrix

This matrix documents operational status, host runtime constraints, and fallback mechanisms across all supported runtime modalities:
- **Linux Codespace** (Ubuntu 24.04 LTS x86_64)
- **VS Code Remote** (Codespaces web and desktop client)
- **Antigravity CLI** (`agy` execution interface)
- **CLI** (Standard shell terminal invocation)
- **MCP** (Model Context Protocol programmatic access)
- **GUI** (Interactive display requirements and headless fallbacks)
- **Android** (SDK, tools, and execution models)
- **iOS / macOS** (Host boundaries and handoff workflows)
- **Container** (Docker / Devcontainer environment isolation)

| Component / Subsystem | Linux Codespace | VS Code Remote | Antigravity CLI | CLI | MCP | GUI | Android | iOS/macOS | Container | Compatibility Notes & Fallback Strategies |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Antigravity Core (`agy`)** | YES | YES | YES | YES | NO | N/A | N/A | N/A | YES | Primary agent runtime; executes natively in Linux container. |
| **Documentation MCP (`context7`)** | YES | YES | YES | NO | YES | N/A | N/A | N/A | YES | Real-time external API/library docs retrieval via MCP. |
| **GitHub Integration (`github` MCP / `gh`)** | YES | YES | YES | YES | YES | N/A | N/A | N/A | YES | Dual access: CLI `gh` tool + MCP programmatic server. |
| **Headless Browser (`playwright`)** | YES | YES | YES | YES | YES | HEADLESS | N/A | N/A | YES | Headless Chromium automation with sandbox flags enabled. |
| **Safe DB Proxies (`sqlite-safe`, `postgres-safe`)** | YES | YES | YES | NO | YES | N/A | N/A | N/A | YES | Strictly read-only policy proxies preventing data mutation. |
| **Core Languages (Node, Python, Java, C/C++)** | YES | YES | YES | YES | NO | N/A | N/A | N/A | YES | Full compiler, interpreter, and build system suites. |
| **Android SDK / CLI (`sdkmanager`, `adb`)** | YES | YES | YES | YES | NO | N/A | YES | N/A | YES | Fully functional headless platform-tools (API 34/35). |
| **Android Emulation (`qemu-system`)** | NO | NO | NO | NO | NO | NO | LIMITED | NO | LIMITED | `/dev/kvm` disabled on Azure VM host. Fallback: JVM Robolectric tests & ADB network bridge. |
| **Android RE (`apktool`, `jadx`, `smali`)** | YES | YES | YES | YES | NO | N/A | YES | N/A | YES | Complete decompilation, disassembly, Smali editing & repacking. |
| **Ghidra SRE (`analyzeHeadless`)** | YES | YES | YES | YES | NO | HEADLESS | YES | N/A | YES | NSA Ghidra headless automated C decompiler & analysis scripts. |
| **Ghidra GUI Interactive Client** | NO | NO | NO | NO | NO | NO | N/A | N/A | NO | No native X11/Wayland display server in cloud web browser. Fallback: `analyzeHeadless` + Radare2/Rizin CLI. |
| **Binary SRE CLI (`r2`, `rizin`, `checksec`)** | YES | YES | YES | YES | NO | N/A | N/A | N/A | YES | High-speed terminal disassembly and ELF security checks. |
| **Native Debuggers (`gdb`, `lldb`)** | YES | YES | YES | YES | NO | N/A | N/A | N/A | YES | Native Linux core dump analysis, breakpoint debugging & ASan. |
| **WebAssembly (`wabt`, `wasm-opt`, `wasmtime`, `hexana`)** | YES | YES | YES | YES | YES | N/A | N/A | N/A | YES | WAT assembly, Binaryen optimization, Wasmtime runtime, and Hexana MCP analysis. |
| **SAST & Security (`semgrep`, `codeql`, `gitleaks`)** | YES | YES | YES | YES | NO | N/A | N/A | N/A | YES | AST search, semantic dataflow taint tracking, and secret scans. |
| **Network Forensics (`tshark`, `capinfos`, `scapy`)** | YES | YES | YES | YES | NO | N/A | N/A | N/A | YES | Deep offline packet dissection & synthetic PCAP generation. |
| **Live Raw Packet Capture (`tcpdump -i`)** | LIMITED | LIMITED | LIMITED | LIMITED | NO | N/A | N/A | N/A | LIMITED | Non-root container restricts raw interface promiscuous capture. Fallback: Offline PCAP analysis (`-r`). |
| **Cloud Native (`docker`, `kubectl`, `helm`)** | YES | YES | YES | YES | NO | N/A | N/A | N/A | YES | Docker-in-Docker socket support & Kubernetes toolchains. |
| **Apple Xcode & iOS Simulator** | NO | NO | NO | NO | NO | NO | NO | NO | NO | Proprietary to macOS Darwin. Fallback: Swift CLI + `docs/ios-macos-handoff.md` JSON schema. |

---

## 2. Platform Constraint Remediation & Fallback Strategies

### 2.1 Hardware Virtualization (KVM) Constraint
- **Constraint**: Cloud-hosted Azure VMs do not expose `/dev/kvm` to nested Docker containers.
- **Impact**: Full Android QEMU system emulators cannot run with hardware acceleration.
- **Engineered Fallback**:
  1. Headless JVM unit tests running via Robolectric mock SDK environments.
  2. Gradle automated test harness executing in headless CI mode (`./gradlew testDebugUnitTest --no-daemon`).
  3. ADB over TCP/IP bridging allowing connection to remote physical devices or external cloud device farms.

### 2.2 Cloud Headless Environment (GUI) Constraint
- **Constraint**: The Codespaces environment is accessed via browser/remote terminal without an active X11/Wayland display server.
- **Impact**: Desktop GUI applications (e.g. interactive Ghidra GUI window, desktop browser windows) cannot render visually.
- **Engineered Fallback**:
  1. **Ghidra**: Fully scripted via `$GHIDRA_HOME/support/analyzeHeadless` and `tools/scripts/ghidra-analyze.sh`.
  2. **Playwright**: Configured with `--headless=new`, `--no-sandbox`, and `--disable-dev-shm-usage`. Full visual verification via automated PNG screenshot generation and DOM accessibility snapshots.
  3. **Disassembly**: Interactive terminal workflows handled via Radare2 (`r2 -q`) and Rizin (`rizin`).

### 2.3 Operating System Boundary (macOS / iOS) Constraint
- **Constraint**: Apple Xcode, iOS SDKs, and CoreSimulator require macOS Darwin kernels and cannot be installed on Linux.
- **Impact**: Direct local compilation of `.ipa` packages and iOS simulator execution is unsupported on Linux.
- **Engineered Fallback**:
  1. Linux Swift runtime and SourceKit-LSP configured for Swift code authoring and syntax validation.
  2. Formal cross-platform handoff architecture documented in `docs/ios-macos-handoff.md`.
  3. Validated JSON schema in `docs/schemas/ios-handoff.schema.json` and sample payload in `docs/schemas/sample-handoff.json` for deterministic CI/CD job dispatch to macOS runners.

### 2.4 Container Privilege & Network Sniffing Constraint
- **Constraint**: Non-root container users cannot put network interfaces into promiscuous capture mode without `CAP_NET_RAW` privileges.
- **Impact**: Running `tcpdump -i eth0` generates permission errors.
- **Engineered Fallback**:
  1. Dissection workflows decoupled from live packet capture.
  2. Full offline PCAP dissection via `tshark -r`, `capinfos`, `editcap`, and `mergecap`.
  3. Python `scapy` library configured for deterministic synthetic traffic creation and protocol fuzzing (`fixtures/network/generate_sample_pcap.py`).
