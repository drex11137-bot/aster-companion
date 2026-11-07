# Antigravity Engineering Workstation Master Architecture

This document defines the complete architectural design, structural layers, runtime interactions, security boundaries, and design rationales for the Antigravity multi-domain engineering workstation running in GitHub Codespaces.

---

## 1. Architectural Overview & Design Philosophy

The Antigravity workstation is designed as an **autonomous, reproducible, modular, security-conscious, and agent-operable development environment**. Rather than acting as a loose collection of disparate tools, the workstation provides a tightly integrated 10-layer architecture:

```text
+-------------------------------------------------------------------------+
|                        LAYER 1: USER & AGENT INTENT                     |
|            User Prompts, Antigravity CLI (`agy`), Slash Commands        |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                    LAYER 2: HIERARCHICAL MEMORY & STATE                 |
|   Global Instructions (`~/.gemini/`) ──► Project Memory (`.agents/`)    |
|   Durable Session Logs ──► Active Task State (`.agent-state/`)          |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                    LAYER 3: ORCHESTRATION & SUBAGENTS                   |
|   9 Specialized Subagents (`.agents/agents/`) with Least-Privilege Tools|
|   Dynamic Subagent Invocation & Inter-Agent Messaging                   |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                    LAYER 4: DOMAIN SKILLBOOKS & ROUTING                 |
|   16 Focused Domain Skills (`.agents/skills/`)                          |
|   Progressive Disclosure, Decision Trees, Tool Routing & Fallbacks     |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                    LAYER 5: SECURITY GATEKEEPERS & HOOKS                |
|   Deterministic Lifecycle Hooks (`.agents/hooks.json`)                  |
|   PreInvocation ──► PreToolUse (Secret Filter) ──► PostToolUse ──► Stop |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                    LAYER 6: MODEL CONTEXT PROTOCOL (MCP)                |
|   MCP Servers: context7, github, playwright, sqlite, postgres, hexana  |
|   Read-Only Policy Enforcers & Lazy-Loaded Semantic Tool Providers      |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                    LAYER 7: IDE EXTENSIONS & TASK ENGINE                |
|   VS Code Remote Containers, `.vscode/settings.json`, `tasks.json`      |
|   Launch Configurations, Remote LSP Servers (C++, Python, Java, Rust)   |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                    LAYER 8: CLI TOOLCHAINS & RUNTIMES                   |
|   Node.js 24, Python 3.12, Java 21/17, GCC 13/Clang 18, Go, Rust, Gradle|
|   Android SDK/ADB/JADX/Apktool, Ghidra, Rizin, WABT, TShark, Semgrep    |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                    LAYER 9: VERIFICATION & DOCTOR SUITE                 |
|   Unified `agy-env-doctor`, Domain Verifiers (`.devcontainer/scripts/`)  |
|   Cryptographic Evidence, Synthetic Test Fixtures (`fixtures/`)         |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                    LAYER 10: DEVCONTAINER & REPRODUCIBILITY             |
|   Debian/Ubuntu Multi-Stage Container (`.devcontainer/Dockerfile`)       |
|   Deterministic Package Pinning, Caching, and Non-Root Hardening        |
+-------------------------------------------------------------------------+
```

---

## 2. Detailed Layer Specifications

### Layer 1: User & Agent Intent Engine
- **Antigravity CLI (`agy`)**: The primary execution engine interfacing between the underlying AI model (e.g. Gemini 2.5 Pro / Flash) and the host operating system.
- **Slash Commands**: High-level behavioral macros (e.g., `/start-session`, `/promote-memory`, `/goal`, `/plan`, `/grill-me`) enabling structured workflows.
- **Pair Programming Interaction**: Balances autonomous task execution with interactive human alignment, asking clarifying questions only when critical decisions require disambiguation.

### Layer 2: Hierarchical Memory & State Engine
The workstation decouples memory into distinct lifecycles to prevent context bloat and hallucination:
1. **Global Instructions** (`~/.gemini/GEMINI.md`): Baseline agent identity, tool semantics, and zero-secrets security policies.
2. **Project Durable Knowledge** (`.agents/memory/`): Architectural choices, persistent domain gotchas, verified test findings.
3. **Active Working State** (`.agent-state/current-state.md`): Compact (< 30 lines) active phase state, preventing multi-turn memory degradation.
4. **Episodic Session Logs** (`.agents/memory/sessions/`): Timestamped records of past executions and intermediate findings.
5. **Authoritative Source Code**: Live repository state always supersedes stored memory; live tests override previous assumptions.

### Layer 3: Orchestration & Subagent Hierarchy
Antigravity defines 9 specialized subagents in `.agents/agents/`. Each subagent adheres to the principle of **least privilege**:
- `environment-auditor`: Read-only system inspection, dependency scanning, configuration verification.
- `android-engineer`: Gradle wrapper builds, Android SDK/NDK integration, and headless emulator workflows.
- `web-engineer`: Full-stack web architectures, Next.js/React, TypeScript bundling, and API routes.
- `backend-engineer`: Service architectures, database integrations, API contracts, ORMs.
- `binary-analyst`: Static binary disassembly, symbol extraction, ELF/PE/WASM/DEX triage.
- `security-auditor`: SAST analysis, CodeQL taint tracking, Semgrep rules, supply chain vulnerability scans.
- `network-analyst`: PCAP trace inspection, TShark filtering, protocol forensics, Scapy automation.
- `verification-engineer`: Multi-domain test execution, build validation, and compliance evidence gathering.
- `adversarial-reviewer`: Independent critique, edge-case probing, regression hunting, and break-testing.

### Layer 4: Focused Domain Skills
Sixteen modular skillbooks (`.agents/skills/*/SKILL.md`) provide step-by-step procedural playbooks with **progressive disclosure**:
- **Triggers & Prerequisites**: Precise activation conditions preventing false-positive triggering.
- **Decision Trees**: Clear visual branching (e.g., triage binary type -> route to ELF, WASM, DEX, or PE workflow).
- **Tool Selection Rationale**: Directs the agent on why a particular tool is chosen over alternatives.
- **Verification & Fallbacks**: Mandatory evidence checks and automated recovery steps if the primary approach fails.

### Layer 5: Security Gatekeepers & Deterministic Hooks
Hooks defined in `.agents/hooks.json` execute automatically on agent lifecycle events:
- **`PreInvocation` (`scripts/hooks/pre_invocation.py`)**: Validates environment invariants, memory coherence, and active workspace root.
- **`PreToolUse` (`scripts/hooks/pre_tool_use.py`)**: Intercepts `write_to_file`, `replace_file_content`, and `run_command` calls to evaluate regexes for API keys, private certificates, passwords, and tokens. Blocks execution if a secret leak is detected.
- **`PostToolUse` (`scripts/hooks/post_tool_use.py`)**: Captures tool return codes, formats linting errors, and tracks failed operations.
- **`Stop` (`scripts/hooks/stop_guard.py`)**: Verifies idle state, cleans up orphaned background tasks, and ensures durable state persistence.

### Layer 6: Model Context Protocol (MCP)
MCP servers provide structured, semantic APIs without polluting the shell command line:
- `context7`: Up-to-date documentation retrieval for external libraries and APIs.
- `github`: Repository exploration, issues, pull requests, and CI workflow tracking.
- `playwright`: Headless browser automation, DOM accessibility trees, and visual assertions.
- `sqlite-safe` & `postgres-safe`: Strictly read-only database exploration proxies (`DB_READONLY=true`, `PGREADONLY=true`).
- `hexana`: WebAssembly and native binary inspection, disassembly, and call graph analysis.

### Layer 7: IDE Extensions & Task Engine
Configured via `.vscode/extensions.json`, `settings.json`, and `tasks.json`:
- **Remote Container Compatibility**: Extensions selected specifically for Linux Codespaces headless operation.
- **Unified IDE Tasks**: Provides one-click commands for `agy-env-doctor`, `security:scan`, Android builds, and test verification.
- **Headless Debugging**: Launch configurations for Node.js, Python, GDB/LLDB, and Java tests.

### Layer 8: CLI Toolchains & Runtimes
Verified, multi-domain toolchain installed directly in the container:
- **Runtimes**: Node.js 24, Python 3.12, OpenJDK 21/17, GCC 13, Clang 18, Go, Rust 1.85+.
- **Mobile/Android**: Android SDK (API 34/35), `adb`, `apktool`, `jadx`, `apksigner`, `zipalign`, `smali`/`baksmali`.
- **Binary SRE**: Ghidra 11.2 Headless, Radare2 6.2, Rizin 0.9, GDB 15, LLDB 18, `checksec`, Binutils.
- **WebAssembly**: WABT (`wat2wasm`, `wasm2wat`), `wasm-tools`, Wasmtime 48.0.
- **Cybersecurity & SAST**: Semgrep 1.175, CodeQL 2.26, Trivy 0.74, Gitleaks 8.30, Bandit 1.9, OSV-Scanner.
- **Network Forensics**: TShark 4.2, Tcpdump 4.99, Capinfos, Scapy 2.7, Nmap 7.94.

### Layer 9: Verification & Doctor Suite
- **`agy-env-doctor`**: Unified diagnostic tool in `tools/bin/` checking 60+ workstation invariants across all domains.
- **Standalone Domain Doctors**: Modular verifiers in `.devcontainer/scripts/` returning strict non-zero exit codes on failure.
- **Multi-Domain Fixtures**: Synthetic test targets in `fixtures/` (Android APKs, C binaries, PCAP traces, WASM modules, Web apps) for deterministic validation.

### Layer 10: Devcontainer & Reproducibility
- **`Dockerfile` & `devcontainer.json`**: Declarative container definition ensuring any fresh Codespace or local Docker runner reproduces the exact workstation state.
- **Multi-Stage Build Optimization**: Pre-caches package dependencies, builds binary tools from source, and enforces non-root `codespace` user permissions.

---

## 3. Layer Interaction & Dataflow Matrix

| Trigger / Action | Ingress Layer | Processing Layers | Egress / Outcome |
| :--- | :--- | :--- | :--- |
| **User Prompts Agent** | Layer 1 (CLI) | Layer 2 (State) ──► Layer 5 (`PreInvocation`) ──► Layer 4 (Skill Selection) | Structured Execution Plan |
| **Agent Executes Tool** | Layer 3/4 (Subagent/Skill) | Layer 5 (`PreToolUse` Security Gate) ──► Layer 6/8 (MCP or CLI) | Safe Tool Execution |
| **Tool Completes** | Layer 6/8 (Tool Output) | Layer 5 (`PostToolUse` Lint/Error Track) ──► Layer 9 (Verification Check) | Validated Evidence Artifact |
| **Task Finishes** | Layer 1/3 (Agent Completion) | Layer 5 (`Stop` Hook) ──► Layer 2 (Durable State Update `.agent-state/`) | Synchronized Repository State |

---

## 4. Architectural Boundaries & Platform Mitigations

```text
+───────────────────────────+────────────────────────────+──────────────────────────────────────────────+
| Platform Boundary         | Root Cause                 | Workstation Mitigation / Fallback            |
+───────────────────────────+────────────────────────────+──────────────────────────────────────────────+
| Xcode / iOS Simulator     | macOS Darwin proprietary   | Linux Swift CLI + JSON Handoff Schema        |
| Android Hardware KVM      | Azure VM virtualization    | Headless Robolectric + JVM Mocking + ADB     |
| GUI Applications (Ghidra) | Headless Cloud Container   | Headless CLI Analyzer (`analyzeHeadless`)    |
| Promiscuous Sniffing      | Unprivileged container net | Offline PCAP dissection via TShark & Scapy   |
| Production Database Write | Safety Policy Enforced     | Read-only MCP proxies with strict auth gates |
+───────────────────────────+────────────────────────────+──────────────────────────────────────────────+
```

---

## 5. Summary Architecture Quality Checklist

- [x] **Modular**: Every layer is independently testable and decoupled.
- [x] **Reproducible**: Full environment declared in `.devcontainer/`.
- [x] **Verifiable**: 23 dedicated test reports and automated doctor suites.
- [x] **Security-Conscious**: Regex pre-tool filtering, zero secrets, read-only DB proxies.
- [x] **Agent-Operable**: Clear tool schemas, discoverable skills, and least-privilege subagents.
