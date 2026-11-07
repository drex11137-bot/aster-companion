# ENVIRONMENT REPORT — Hardware, OS & Toolchain Inventory
## Antigravity Engineering Workstation & Memory OS
**Specification Authority:** `instruction.md` Section 5, Section 109, Section 122  
**Date:** 2026-09-04  
**Evaluator:** Agent 21 (Workstation Release Master) & Forensic Baseline Team  
**Evaluation Standard:** Deterministic CLI Inspection & Zero Assumptions  

---

## 1. Executive Hardware & Platform Topology

| Parameter | Observed Host Value | Target Specification | Compliance |
| :--- | :--- | :--- | :---: |
| **Operating System** | Linux 6.8.0-1052-azure (Ubuntu 24.04.1 LTS noble) | Linux x86_64 (Container/VM) | **COMPLIANT** |
| **Architecture** | `x86_64` (AMD64) | `x86_64` | **COMPLIANT** |
| **CPU Topology** | 4 vCPUs (Intel Xeon / AMD EPYC Hyperthreaded) | $\ge 2$ Cores | **COMPLIANT** |
| **System Memory** | 16 GB RAM | $\ge 8$ GB RAM | **COMPLIANT** |
| **Primary Filesystem** | ext4 on overlayfs (`/workspaces/codespaces-blank`) | POSIX Compliant with `fcntl` lock support | **COMPLIANT** |
| **C Library** | GNU C Library (glibc) 2.39 | glibc $\ge 2.35$ | **COMPLIANT** |

---

## 2. Memory Subsystem Runtime Inventory (Section 109)

In accordance with Section 109 of `instruction.md`, the runtime configuration of the memory subsystem is explicitly recorded:

| Component | Current Version / Identifier | Path / Location | Provider / Engine |
| :--- | :--- | :--- | :--- |
| **Antigravity CLI** | `agy` CLI 2.0 (Google Antigravity Workstation) | Host Environment | Core Agent Runtime |
| **MemSearch CLI** | `memsearch` 0.4.19 | `/home/codespace/.local/bin/memsearch` | Local CLI Substrate |
| **MemSearch Venv** | Python 3.12.1 Isolated Virtual Environment | `/workspaces/codespaces-blank/.venv-memsearch` | Isolated Substrate Venv |
| **Milvus Lite** | `milvus-lite` 3.2.1 (`pymilvus` 3.0.1) | `~/.memsearch/milvus.db` | Embedded SQLite/Milvus |
| **Embedding Engine**| `onnxruntime` 1.29.0 | Local CPU ONNX Runtime | CPU Quantized Engine |
| **Embedding Model** | `bge-m3` (`gpahal/bge-m3-onnx-int8`) | Embedded in MemSearch Runtime | 1024-Dimension Dense Vectors |
| **Embedding Provider**| `onnx` (explicit in `~/.memsearch/config.toml`) | `~/.memsearch/config.toml` | 100% Offline / Local CPU |
| **Locking Mechanism**| POSIX `fcntl` Advisory File Locking | `.agents/memory/index_writer.lease.lock` | Single-Writer Lease Lock |
| **Index Manifest**  | JSON v2.0 Schema | `.agents/memory/.memsearch/manifest.json` | Atomic Revision Tracking |

---

## 3. Workstation Core Toolchain Inventory

### Languages, Compilers & Runtimes
- **Python**: `Python 3.12.1` (`/usr/local/python/current/bin/python3`)
- **Node.js**: `v24.14.0` (`/usr/local/share/nvm/versions/node/v24.14.0/bin/node`)
- **OpenJDK**: `openjdk version "21.0.10" 2026-01-20 LTS` (Default), Java 17 available
- **GCC**: `gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`
- **Clang / LLVM**: `Ubuntu clang version 18.1.3 (1ubuntu1)`
- **Go**: `go version go1.26.1 linux/amd64`
- **Make / Build Tools**: `GNU Make 4.4.1`, `cmake version 3.28.3`, `ninja 1.11.1`
- **Git**: `git version 2.53.0`

### Security & Static Analysis Toolchains
- **Gitleaks**: `v8.30.1` (Zero secrets validation)
- **Semgrep**: `1.175.0` (AST security analysis)
- **Bandit**: `1.7.9` (Python AST vulnerability scanner)
- **Secret Scanner**: Native custom high-entropy Shannon + 25-regex engine (`scripts/secret_scanner.py`)

### Binary Analysis & Reverse Engineering
- **radare2 (r2)**: `6.2.0 +1 abi:132 @ linux-x86_64`
- **rizin**: `0.9.1 @ linux-x86-64`
- **apktool**: `3.0.3`
- **jadx**: `1.5.6`
- **checksec**: Installed and operational
- **binutils**: `readelf`, `objdump`, `nm`, `strings`, `file`

### Network Forensics
- **TShark (Wireshark)**: `4.2.2` (Git v4.2.2 packaged as 4.2.2-1.1build3)
- **capinfos**: Operational
- **tcpdump**: Operational

---

## 4. Operational Boundaries & Platform Constraints

1. **Local Codespaces Isolation**: All network operations for memory indexing and semantic embeddings are bound to `localhost` and local disk (`~/.memsearch/milvus.db`). No cloud API keys (e.g. OpenAI) are required or used.
2. **CPU ONNX Throughput**: Multi-core CPU ONNX inference executes at ~45s per multi-paragraph file. Background batch queuing via `IndexQueueManager` prevents blocking interactive turns.
3. **Lease Locking**: Embedded Milvus Lite requires serialized writer access; POSIX advisory locking ensures zero file corruption across subagents.

---

## 5. Environment Certification
The operational environment is fully configured, validated, and verified. All compilers, runtimes, and local vector substrates are operational with zero external blockers.
