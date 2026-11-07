# AGENTS.md — Antigravity Engineering Workstation Master Guide

This document defines the architecture, toolchains, execution workflows, security boundaries, and operational standards for autonomous and pair-programming AI agents operating in this repository.

---

## 1. Repository Structure

```text
.
├── .agent-state/               # Active multi-phase durable state (current-state, blockers, decisions)
├── .agents/                    # Agent customizations, MCP configuration, and memory
│   ├── agents/                 # Specialized subagent definitions (9 domain agents)
│   ├── hooks.json              # Deterministic lifecycle hooks (PreInvocation, PreToolUse, PostToolUse, Stop)
│   ├── mcp_config.json         # Model Context Protocol server configuration
│   ├── memory/                 # Project persistent memory, session logs, CURRENT.md
│   ├── rules/                  # Hierarchical agent rules and guidelines
│   └── skills/                 # Focused domain skills (16 domain skillbooks)
├── .devcontainer/              # Devcontainer definitions and verification scripts
│   ├── devcontainer.json       # Devcontainer specification
│   ├── Dockerfile              # Reproducible multi-toolchain container build
│   └── scripts/                # Automated verification scripts
├── docs/                       # Architectural documentation and test reports
│   ├── architecture.md         # 10-layer master architecture documentation
│   ├── operations.md           # Daily commands, diagnostic runbooks, repair workflows
│   ├── toolchain-matrix.md     # Authoritative component & toolchain inventory matrix
│   ├── compatibility-matrix.md # Platform constraints, fallbacks & boundaries
│   ├── engineering-environment.md
│   ├── ios-macos-handoff.md    # Cross-platform iOS/macOS handoff specification
│   └── test_reports/           # 23 verification test reports and compliance logs
├── fixtures/                   # Multi-domain test fixtures (Android, C, Network, Security, WASM, Web)
├── scripts/                    # Platform scripts, memory engine, security scanner, hooks
│   └── hooks/                  # Hook handler implementations
└── tools/
    ├── bin/                    # Platform diagnostic CLI tools (agy-env-doctor)
    └── scripts/                # Helper utilities and analysis scripts
```

---

## 2. Toolchain Overview

The workstation integrates multi-domain toolchains verified for Linux/Codespaces:
- **Core CLI**: `git`, `gh`, `curl`, `jq`, `yq`, `ripgrep` (`rg`), `fd`, `tree`, `make`, `cmake`, `ninja`.
- **Languages & Runtimes**: Node.js 24, Python 3.12, OpenJDK 21/17, GCC 13, Clang 18, Go, Rust/Cargo.
- **Web & Browser**: Playwright, Vite, ESLint, Prettier, Tailwind CSS.
- **Android & Mobile**: Android SDK (`cmdline-tools`, `platform-tools`, `platforms`), ADB, Gradle wrapper.
- **Android Reverse Engineering**: `apktool`, `jadx`, `apksigner`, `zipalign`, `smali`, `baksmali`, `frida`.
- **Binary Analysis**: `file`, `readelf`, `objdump`, `nm`, `strings`, `checksec`, `ghidra-headless`, `radare2` (`r2`), `rizin`, `gdb`, `lldb`, `strace`, `ltrace`.
- **WebAssembly**: `wat2wasm`, `wasm2wat`, `wasm-validate`, `wasm-tools`, `wasmtime`.
- **Security & SAST**: `semgrep`, `codeql`, `gitleaks`, `bandit`, `trivy`, `osv-scanner`.
- **Network & Forensics**: `tshark`, `tcpdump`, `capinfos`, `editcap`, `mergecap`, `nmap`, `scapy`.
- **Containers & Cloud-Native**: `docker`, `docker compose`, `kubectl`, `helm`.

---

## 3. Build & Test Commands

### Web & Frontend
- Install: `npm ci` / `pnpm install` / `yarn install`
- Dev server: `npm run dev`
- Production build: `npm run build`
- Unit tests: `npm test`
- End-to-End browser tests: `npx playwright test`

### Native C/C++
- Configure: `cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug`
- Compile: `ninja -C build`
- Unit tests: `ctest --test-dir build --output-on-failure`

### Android Application
- Build Debug APK: `./gradlew assembleDebug --no-daemon`
- Unit tests: `./gradlew testDebugUnitTest --no-daemon`
- Android Lint: `./gradlew lintDebug --no-daemon`

### Python & Security
- Unit tests: `pytest tests/ -v`
- SAST Scan: `semgrep scan --config=auto`
- Secret Scan: `gitleaks detect --source . --no-git`
- Python Security: `bandit -r .`

### Unified Workstation Diagnostic
- Run doctor: `python3 tools/bin/agy-env-doctor`
- Run toolchain verifier: `bash .devcontainer/scripts/verify-toolchain.sh`
- Run domain verifiers: `bash .devcontainer/scripts/verify-*.sh`

---

## 4. Specialized Domain Workflows

### Android Workflow
1. Verify SDK configuration: `echo $ANDROID_HOME`, `adb version`.
2. Inspect `build.gradle` for `compileSdk` and `targetSdk`.
3. Use Gradle wrapper `./gradlew` with `--no-daemon` to prevent daemon memory exhaustion.
4. Run unit and lint checks before creating APK artifacts.

### Reverse Engineering & Binary Analysis Workflow
1. File identification: `file <target>`, `readelf -h <target>`.
2. Security mitigations audit: `checksec --file=<target>`.
3. Symbol and string extraction: `nm -D <target>`, `strings -a <target>`.
4. Headless decompilation: `${GHIDRA_HOME}/support/analyzeHeadless` or `r2 -q -c "aaa; afl; pdf @main" <target>`.
5. For Android APKs: `apktool d <target.apk> -o <out_dir>` and `jadx -d <src_dir> <target.apk>`.

### Network Forensics Workflow
1. Summary & packet metadata: `capinfos <capture.pcap>`.
2. Protocol hierarchy analysis: `tshark -r <capture.pcap> -q -z io,phs`.
3. Target filtering: `tshark -r <capture.pcap> -Y "<filter>" -T fields -e ...`.
4. Perform packet inspection offline without requiring root packet capture privileges.

---

## 5. Model Context Protocol (MCP) Rules & Permissions

MCP servers are configured in `.agents/mcp_config.json`:
- **`context7`**: Access live framework, library, and API documentation. Always consult Context7 when referencing changing APIs.
- **`github`**: Repository search, pull request audits, issue inspection, and CI workflow tracking.
- **`playwright`**: Headless browser automation, DOM assertions, UI accessibility testing, and screenshot verification.
- **`sqlite-safe` / `postgres-safe`**: Safe read-only database exploration (`DB_READONLY: true`, `PGREADONLY: true`). No destructive mutations permitted via MCP.
- **`hexana`**: WebAssembly and native binary inspection, disassembly, and call graph analysis.

### Permission Boundaries
- **Zero Secrets Policy**: Never write or persist API keys, OAuth tokens, SSH keys, passwords, or credentials.
- **Read-Only Database Access**: Database inspection is strictly read-only by default.
- **Isolated Browser Sessions**: Playwright runs in isolated profiles; personal profiles/cookies are never accessed.

---

## 6. Tool Selection Policy & Hierarchy

When selecting tools, follow the efficiency hierarchy—**never use the heaviest tool by default**:
- **Need current library documentation?** → `Context7` MCP (`query-docs`)
- **Need browser interaction?** → `playwright` MCP / CLI
- **Need GitHub repository data?** → `github` MCP / `gh` CLI
- **Need source code security review?** → `semgrep` (AST matching) → `codeql` (deep taint tracking)
- **Need dependency/container security?** → `gitleaks` (secrets) → `trivy` / `osv-scanner` / `pip-audit`
- **Need Android APK analysis?** → `apktool` (resources/manifest) + `jadx` (Java source) + `apksigner`
- **Need binary triage?** → `file` + `checksec` + binutils (`readelf`, `nm`, `strings`)
- **Need deep binary analysis?** → `r2` / `rizin` (fast CLI) → `Ghidra Headless` (`analyzeHeadless`) / `hexana`
- **Need PCAP analysis?** → `capinfos` (metadata) → `tshark` (filter/extract) → `scapy` (synthesis)
- **Need Android build?** → Gradle wrapper (`./gradlew`) + Android SDK + `adb`

---

## 7. Antigravity Lifecycle Hooks

Hooks are declared in `.agents/hooks.json` and executed deterministically:
1. **`PreInvocation` (`scripts/hooks/pre_invocation.py`)**: Context reminder and memory state validation.
2. **`PreToolUse` (`scripts/hooks/pre_tool_use.py`)**: Security gatekeeper intercepting `write_to_file`, `replace_file_content`, and `run_command` to block secret leaks.
3. **`PostToolUse` (`scripts/hooks/post_tool_use.py`)**: Syntax tracking, lint feedback recording, and tool execution error tracking.
4. **`Stop` (`scripts/hooks/stop_guard.py`)**: Session guard verifying idle state and background tasks.

---

## 8. Subagent Orchestration & 21-Agent Memory OS Roster

Antigravity operates a 21-agent specialized roster across 7 squads implementing and governing the 8-tier Memory Operating System:
- **Squad 0: Architecture & Forensics**:
  - `lead-memory-architect`: Master schema, 8 tiers, 22 invariants, ADR documentation.
  - `forensic-baseline-auditor`: Environment topology, defect discovery, baseline audits.
- **Squad 1: Core Repairs & Gatekeeper**:
  - `core-repair-engineer`: Unified audit diagnostics, version sync, bidirectional indexing.
  - `security-gatekeeper`: PreToolUse fail-closed enforcement, zero-secrets gatekeeper.
- **Squad 2: Storage Substrate & Adapters**:
  - `memsearch-runtime-engineer`: Isolated `.venv-memsearch`, Milvus Lite, CPU ONNX embeddings.
  - `storage-backend-adapter-engineer`: Decoupled `memsearch_backend.py` facade, fallback mechanisms.
- **Squad 3: Search, Gating & Compilation**:
  - `hybrid-search-specialist`: RRF reciprocal rank fusion, lexical + semantic retrieval.
  - `evidence-reranker-engineer`: Multi-signal evidence scoring, MMR diversity filtering.
  - `context-compiler-engineer`: Progressive disclosure (L1/L2/L3), trust verdicts (`CERTIFY`, `ADVISORY`, `WARN`, `BLOCK`).
  - `query-routing-specialist`: 5 intent classifications, scope routing, explicit abstention.
- **Squad 4: Ingestion, Normalization & Lifecycle**:
  - `candidate-bus-engineer`: Experience capture, routine noise filtering, deterministic SHA-256 IDs.
  - `memory-compiler-gatekeeper`: 9 memory types normalization, durability admission gating.
  - `memory-reconciler-specialist`: Bitemporality, non-destructive supersession, rollback logging.
  - `index-queue-engineer`: Single-writer lease locking, update coalescing, health state machine.
- **Squad 5: Feedback, Evolution & Procedures**:
  - `feedback-telemetry-engineer`: Retrieval feedback ledger, MRR, NDCG@10, false recall rates.
  - `learning-loop-specialist`: Half-life memory decay, access reinforcement, shadow ranker.
  - `procedural-skill-engineer`: Workflow sequence mining, safe `inbox/procedures/` staging (Invariant 16).
- **Squad 6: Quality, Diagnostics & Release**:
  - `memory-doctor-engineer`: 6-dimension health diagnostic engine (`agy-memory-doctor`).
  - `benchmark-test-architect`: 30-point Acceptance Test Matrix (A001–A030), deterministic scoring.
  - `adversarial-red-team-reviewer`: Secret injection, prompt injection, noise stress, corruption recovery.
  - `workstation-release-master`: Master verification, compliance certification, and future-AI handoff.

---

## 9. Antigravity 8-Tier Memory Operating System

The workstation enforces an 8-tier decoupled Memory OS governed by [`Instruction.md`](file:///workspaces/codespaces-blank/Instruction.md) and [`SPEC.md`](file:///workspaces/codespaces-blank/.agents/memory-upgrade/SPEC.md):
1. **Tier 1 (Working Memory)**: `.agents/memory/CURRENT.md` (bounded $< 30$ lines).
2. **Tier 2 (Episodic Memory)**: `.agents/memory/sessions/YYYY-MM-DD-HHMM.md` (chronological session journals).
3. **Tier 3 (Project Knowledge)**: `.agents/memory/{DECISIONS,GOTCHAS,ARCHITECTURE}.md`.
4. **Tier 4 (Global Durable)**: `~/.gemini/antigravity-cli/memory/` (`GENERAL.md`, `USER.md`, `POLICY.md`, `tools/`, `domains/`).
5. **Tier 5 (Semantic Retrieval Substrate)**: Derived vector index in `.agents/memory/.memsearch/` & Milvus Lite (`~/.memsearch/milvus.db`).
6. **Tier 6 (Candidate Experience Bus)**: Staged inbox at `.agents/memory/inbox/candidates.jsonl`.
7. **Tier 7 (Procedural Memory)**: Distilled workflows staged at `.agents/memory/inbox/procedures/`.
8. **Tier 8 (Feedback & Telemetry Ledger)**: Retrieval metrics at `.agents/memory/retrieval_ledger.jsonl`.

### Diagnostic & Health Tooling
- **Run Memory Doctor**: `tools/bin/agy-memory-doctor` (evaluates Canonical Integrity, Secret Hygiene, Coherence, Vector Health, Inbox Backlog, and Telemetry Quality).
- **Auto-repair & Index Sync**: `tools/bin/agy-memory-doctor --fix`.
- **Hybrid Search**: `python3 scripts/search_memory.py --query "<query>" --scope <scope>`.
- **Query Routing & Abstention**: `python3 scripts/query_router.py --query "<query>"`.
- **Acceptance Matrix Verification**: `python3 scripts/memory_benchmark.py --acceptance-matrix`.

---

## 10. Master Documentation References

- **Architecture Guide**: [`docs/architecture.md`](file:///workspaces/codespaces-blank/docs/architecture.md)
- **Operations & Runbooks**: [`docs/operations.md`](file:///workspaces/codespaces-blank/docs/operations.md)
- **Toolchain Matrix**: [`docs/toolchain-matrix.md`](file:///workspaces/codespaces-blank/docs/toolchain-matrix.md)
- **Compatibility Matrix**: [`docs/compatibility-matrix.md`](file:///workspaces/codespaces-blank/docs/compatibility-matrix.md)
- **iOS/macOS Handoff**: [`docs/ios-macos-handoff.md`](file:///workspaces/codespaces-blank/docs/ios-macos-handoff.md)
- **Test Reports**: [`docs/test_reports/`](file:///workspaces/codespaces-blank/docs/test_reports/)

---

## 11. Definition of Done (DoD)

A task or workstation component is complete ONLY when:
1. Code compiles/builds without warnings or errors.
2. Unit and integration tests pass with zero regressions.
3. SAST and secret scanners report zero Critical/High vulnerabilities.
4. Changes are verified with live command execution and concrete evidence.
5. All relevant documentation and test reports under `docs/test_reports/` are updated.
