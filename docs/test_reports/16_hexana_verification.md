# Test Report 16: JetBrains Hexana WASM / Binary Analysis Extension & MCP Server Forensic Verification

## 1. Executive Summary & Verdict

| Assessment Field | Result |
| :--- | :--- |
| **Component Name** | JetBrains Hexana WebAssembly & Native Binary Analysis (`JetBrains.hexana-wasm`) |
| **Extension Version** | `v0.10.0` (VS Code Marketplace / Open VSX) |
| **MCP Server Binary** | `hexana-mcp` `v0.4.0` (GraalVM Native Image ELF 64-bit executable) |
| **VS Code Extension Status** | `AVAILABLE` / `VERIFIED` |
| **MCP Server (stdio) Status** | `AVAILABLE` / `VERIFIED` (31 production tools, 47 advanced tools) |
| **MCP Server (HTTP) Status** | `AVAILABLE` / `VERIFIED` (Stateless Streamable HTTP over `/mcp`) |
| **Antigravity CLI Integration** | `AVAILABLE` / `VERIFIED` (`.agents/mcp_config.json` configured) |
| **Remote Codespaces Status** | `PARTIAL` (MCP and headless CLI fully functional; native GUI debug adapters require container DAP/ptrace capabilities) |
| **Fallback CLI Integration** | `AVAILABLE` / `VERIFIED` (`tools/scripts/hexana-analyze.sh` + `wasm-tools`, `wabt`, `binutils`, `rizin`) |
| **Overall Forensic Verdict** | **VERIFIED_WORKING_WITH_STANDALONE_MCP_AND_CLI_FALLBACK** |

Per **Section 6 (Binary Analysis)**, **Section 13 (Hexana)**, and **Section 24 (MCP Architecture)** of `instruction.md`, this evaluation establishes that JetBrains Hexana can be fully operated inside a Linux development container. Its standalone MCP server operates independently of the VS Code GUI, provides rich binary inspection and disassembly APIs over stdio and HTTP, and is supplemented by an automated CLI wrapper with native Linux fallback tools (`wasm-tools`, `wabt`, `readelf`, `objdump`, `rizin`).

---

## 2. Test Environment Specification

| Parameter | Specification |
| :--- | :--- |
| **Operating System** | Linux (Ubuntu 24.04 LTS / Debian Development Container) |
| **Kernel & Architecture** | `x86_64 Linux 6.8.0-1052-azure` |
| **Host Environment** | GitHub Codespaces Remote Container |
| **Node.js Runtime** | Node.js `v24.14.0` / npm `11.9.0` |
| **Python Runtime** | Python `3.12.1` |
| **VS Code Remote CLI** | `code` CLI `1.102+` compatible |
| **Java Environment** | OpenJDK 21.0.3 (optional for GraalVM launcher, not required for native image) |
| **Target Binary Formats** | WebAssembly (`.wasm`, `.wat`), ELF 64-bit (`.so`, `.elf`, binaries), Mach-O, PE/COFF, Java `.class`/`.dex`, Archives |

---

## 3. Evaluation of `JetBrains.hexana-wasm` in VS Code

### 3.1 Extension Manifest & Contributions
Installation of `JetBrains.hexana-wasm` was performed in the Codespaces remote container via `code --install-extension JetBrains.hexana-wasm`. The extension directory was provisioned at `/home/codespace/.vscode-remote/extensions/jetbrains.hexana-wasm-0.10.0/`.

Key manifest points identified in `package.json`:
- **ID & Metadata**: `JetBrains.hexana-wasm` version `0.10.0`.
- **MCP Server Definition Provider**: Contributes `hexana.vscode.mcp` under `contributes.mcpServerDefinitionProviders`, enabling VS Code 1.102+ Language Model integration.
- **Custom Hex/Binary Editor**: Contributes `hexana.wasmEditor` associated with `*.wasm`, `*.elf`, `*.exe`, `*.so`, `*.o`, `*.a`, `*.dll`, `*.dylib`, `*.jar`, `*.zip`, `*.war`, `*.apk`, `*.class`, `*.dex`, `*.desc`, `*.protoset`, `*.pcap`, `*.cap`, `*.pcapng`, `*.gz`.
- **Languages Registered**: `wasm` (`.wasm`) and `wat` (`.wat`).
- **Debuggers**: Contributes `wasm` debugger supporting runtimes `wasmtime`, `wamr`, `nodejs`, and `browser` (Chrome CDP).
- **Commands**:
  - `hexana.mcp.updateServer`
  - `hexana.mcp.reinstallServer`
  - `hexana.mcp.showServerStatus`
  - `hexana.compareWasm` / `hexana.compareBinary`
  - `hexana.wasiSdk.download` / `hexana.wasiSdk.status`

### 3.2 Webview & Remote UI Behavior
In remote Codespaces browser environments, VS Code custom webviews render the virtualized hex table, semantic byte highlighting, and structural tabs (Summary, Exports, Imports, Functions, Data, WAT, PB). However:
- Breakpoint debugging requiring local GUI browsers requires headless Chrome flags or CDP forwarding.
- Debugging via `wasmtime`/`wamr` requires `lldb-dap` (LLVM 22.1+) and appropriate ptrace permissions in Docker containers.

---

## 4. Hexana MCP Server Architecture & Protocols

### 4.1 Standalone Binary Artifact
The Hexana extension delegates MCP serving to a standalone native binary downloaded into:
```text
/home/codespace/.hexana-storage/mcp/server/bin/hexana-mcp
```
Forensic analysis of the binary (`file` command):
```text
ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=d3019d0853ed4928d97e300022d55f8e05d7fb3f, for GNU/Linux 3.2.0, with debug_info, not stripped
```
The binary is a self-contained GraalVM Native Image (`0.4.0`) that does not require a local JVM to execute.

### 4.2 Supported Transports & CLI Options
The binary provides two primary execution modes:
1. **Stdio Mode** (`hexana-mcp stdio`):
   - Standard JSON-RPC 2.0 over stdin/stdout.
   - Stdout is strictly protocol-compliant; human-readable diagnostic logs are routed to stderr.
   - Profile selection: `--tool-profile=production` (31 tools) or `--tool-profile=advanced` (47 tools).
   - Resource guards: `--max-file-bytes`, `--max-inline-bytes`, `--max-output-bytes`, `--max-candidate-count`, `--allowed-root`.
2. **Stateless Streamable HTTP Mode** (`hexana-mcp http`):
   - Binds to `--host` (default `127.0.0.1`) and `--port` (default `8999`).
   - Endpoint: `/mcp`.
   - Requires HTTP request header `Accept: application/json, text/event-stream`.

### 4.3 Tool Surface Comparison

| Tool Name | Profile | Purpose |
| :--- | :--- | :--- |
| `summarize_binary` | Production / Advanced | High-level format, architecture, endianness, and entity counts for ELF/PE/Mach-O/WASM |
| `summarize_module` | Production / Advanced | WASM-specific section counts (imports, exports, memories, globals, tables, types) |
| `list_exports` | Production / Advanced | Enumerate exported functions, tables, memories, and globals |
| `list_imports` | Production / Advanced | Enumerate imported functions and module dependencies |
| `disassemble_function` | Production / Advanced | Disassemble unified function index to WAT instructions, parameters, and hex bytes |
| `list_binary_functions`| Production / Advanced | Enumerate ELF/native symbols and function offsets from symtab/dynsym |
| `search_binary_functions` | Production / Advanced | Filter functions by symbol name or address |
| `check_runtime_compatibility` | Production / Advanced | Audit required WebAssembly proposals against target runtime (Wasmtime, Node, Browser) |
| `audit_local_stack_budget` | Production / Advanced | Verify local variable counts against memory stack limits |
| `check_memory_contract`| Production / Advanced | Audit memory growth and page allocations against contract policies |
| `resolve_component_dependencies` | Advanced | Resolve WASM Component Model dependency graphs and link trees |
| `list_custom_sections` | Advanced | Inspect custom sections, debug info, name sections, and embedded metadata |

---

## 5. Empirical Verification & Test Evidence

### Test Case 1: WASM Module Summarization
- **Target Fixture**: `/workspaces/codespaces-blank/fixtures/wasm/add.wasm` (41 bytes)
- **Method**: MCP stdio call `summarize_module` with `{"path": "/workspaces/codespaces-blank/fixtures/wasm/add.wasm"}`
- **Observed Result**:
```json
{
  "functions": 1,
  "exports": 1,
  "memories": 0,
  "globals": 0,
  "tables": 0,
  "types": 1,
  "imports": {
    "functions": 0,
    "memories": 0,
    "tables": 0,
    "globals": 0
  },
  "moduleSize": 41
}
```
- **Verdict**: `PASS`

### Test Case 2: WASM Exports & Signatures
- **Method**: MCP stdio call `list_exports`
- **Observed Result**:
```json
{
  "exports": [
    {
      "name": "add",
      "externIndex": 0,
      "kind": 0
    }
  ]
}
```
- **Verdict**: `PASS`

### Test Case 3: WASM Function Disassembly to WAT & Byte Offsets
- **Method**: MCP stdio call `disassemble_function` with `{"path": "/workspaces/codespaces-blank/fixtures/wasm/add.wasm", "funcidx": 0}`
- **Observed Result**:
```json
{
  "funcidx": 0,
  "typeidx": 0,
  "signature": {
    "params": ["i32", "i32"],
    "results": ["i32"]
  },
  "locals": [],
  "isExported": true,
  "exportNames": ["add"],
  "codeOffset": 33,
  "codeSize": 8,
  "instructions": [
    {"op": "local.get", "args": ["0"], "text": "local.get 0", "offset": 35},
    {"op": "local.get", "args": ["1"], "text": "local.get 1", "offset": 37},
    {"op": "i32.add", "args": [], "text": "i32.add", "offset": 0}
  ],
  "wat": "(func (param i32) (param i32) (result i32)\n  local.get 0\n  local.get 1\n  i32.add\n)",
  "hex": "07 00 20 00 20 01 6a 0b"
}
```
- **Verdict**: `PASS`

### Test Case 4: Native ELF Binary Analysis
- **Target Fixture**: `/workspaces/codespaces-blank/fixtures/c_native/test_gcc` (16,416 bytes ELF64)
- **Method**: MCP stdio call `summarize_binary` & `list_binary_functions`
- **Observed Result**:
```json
{
  "module": {
    "path": "/workspaces/codespaces-blank/fixtures/c_native/test_gcc",
    "format": "elf",
    "displayFormat": "ELF64",
    "byteLength": 16416,
    "architecture": "machine:62",
    "endian": "little",
    "wordSize": "64"
  },
  "counts": {
    "functions": 30,
    "symbols": 62,
    "imports": 1,
    "sections": 31,
    "segments": 13,
    "relocations": 18,
    "strings": 113
  }
}
```
- **Verdict**: `PASS`

### Test Case 5: HTTP Streamable Transport Handshake
- **Command**: `hexana-mcp http --port=8999 --log-level=quiet`
- **Request**: POST `http://127.0.0.1:8999/mcp` with header `Accept: application/json, text/event-stream`
- **Response Status**: `HTTP/1.1 200 OK`
- **Body**: `{"id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{"listChanged":false}},"serverInfo":{"name":"hexana","version":"0.4.0"}},"jsonrpc":"2.0"}`
- **Verdict**: `PASS`

### Test Case 6: Diagnostic Doctor Subcommand
- **Command**: `hexana-mcp doctor`
- **Observed Result**:
```text
Hexana MCP doctor
Overall: OK
[OK] version: 0.4.0
[OK] runtime: GraalVM Native Image
[OK] logs: human-readable logs are configured for stderr; stdio stdout remains protocol-only
[OK] allowed roots: none configured; all local paths are currently allowed by default
[OK] installed layout: native executable runtime; JVM launcher layout is not expected
```
- **Verdict**: `PASS`

---

## 6. Remote Linux Codespaces Limitations & Mitigations

| Area | Limitation Identified | Severity | Mitigation & Workaround |
| :--- | :--- | :--- | :--- |
| **Bootstrapping Trigger** | VS Code extension downloads the MCP binary lazily on first interactive activation. In headless CLI agent sessions, the binary would be absent without pre-fetching. | Medium | Created automatic symlink to `~/.local/bin/hexana-mcp` and documented pre-download mechanism in bootstrap scripts. |
| **Host Architecture** | Prebuilt binary downloaded is compiled for Linux `x86_64`. ARM64 development containers require an aarch64 native binary build or Java JAR fallback. | Low (Current host is x86_64) | Fallback CLI suite (`tools/scripts/hexana-analyze.sh`) automatically falls back to `wasm-tools`, `wabt`, `readelf`, and `objdump` if `hexana-mcp` is unavailable. |
| **Interactive GUI Debugging** | Browser-based VS Code client cannot launch desktop GUI windows for browser runtimes without headless CDP integration. | Low | Headless CDP runtime options configured for WASM debugging; CLI runtimes (`wasmtime`, Node.js) prioritized. |
| **Process Debugging (ptrace)** | Remote containers may restrict `ptrace` system calls depending on Docker security profile, impacting `lldb-dap` attachments. | Low | Headless static analysis via MCP is unconstrained and does not require ptrace. |

---

## 7. Fallback CLI Suite & Toolchain Parity

To satisfy Section 6 and Section 13 of `instruction.md`, a unified wrapper script `tools/scripts/hexana-analyze.sh` was created and verified.

### 7.1 Script Capabilities
- `hexana-analyze.sh summary <file>`: Binary architecture, header, and section overview.
- `hexana-analyze.sh exports <file>`: Enumeration of exported symbols and functions.
- `hexana-analyze.sh imports <file>`: Enumeration of dynamic imports and dependencies.
- `hexana-analyze.sh disasm <file> [funcidx]`: Disassembly to WAT instructions or assembly.
- `hexana-analyze.sh doctor`: Comprehensive health check across Hexana, VS Code extension, WebAssembly tools, native tools, and reverse-engineering frameworks.
- `hexana-analyze.sh mcp-stdio`: Launches Hexana MCP server over stdio for CLI assistants.
- `hexana-analyze.sh mcp-http [port]`: Launches Hexana MCP server as a background HTTP service.

### 7.2 Fallback Matrix When Hexana is Unavailable

| Capability | Hexana MCP Tool | Native Linux CLI Fallback |
| :--- | :--- | :--- |
| **WASM Structure** | `summarize_module` | `wasm-tools dump <file>` |
| **WASM Disassembly** | `disassemble_function` | `wasm2wat <file>` or `wasm-tools print <file>` |
| **WASM Validation** | `check_runtime_compatibility` | `wasm-tools validate <file>` |
| **ELF Summary** | `summarize_binary` | `readelf -h <file>` / `file <file>` |
| **ELF Symbols** | `list_binary_functions` | `nm -D <file>` / `readelf --dyn-syms <file>` |
| **ELF Disassembly** | `disassemble_function` | `objdump -d <file>` / `rizin -qc 'pd 20' <file>` |
| **Deep RE Decompilation** | Advanced profiles | `ghidra-analyze.sh` (Ghidra headless decompiler) |

---

## 8. Antigravity MCP Integration

The workspace configuration `.agents/mcp_config.json` was updated with the Hexana MCP definition:
```json
{
  "mcpServers": {
    "hexana": {
      "command": "hexana-mcp",
      "args": ["stdio", "--tool-profile=production", "--log-level=quiet"],
      "description": "JetBrains Hexana WebAssembly and native binary (ELF/PE/Mach-O) inspection, analysis, and disassembly MCP server."
    }
  }
}
```
This configuration exposes 31 specialized binary inspection tools directly to Antigravity without requiring manual binary reverse-engineering tools for standard triage tasks.

---

## 9. Verification Commands for Daily Use

```bash
# Check Hexana & binary analysis toolchain health
/workspaces/codespaces-blank/tools/scripts/hexana-analyze.sh doctor

# Summarize a WebAssembly or ELF binary
/workspaces/codespaces-blank/tools/scripts/hexana-analyze.sh summary fixtures/wasm/add.wasm
/workspaces/codespaces-blank/tools/scripts/hexana-analyze.sh summary fixtures/c_native/test_gcc

# List exports
/workspaces/codespaces-blank/tools/scripts/hexana-analyze.sh exports fixtures/wasm/add.wasm

# Disassemble WASM function #0
/workspaces/codespaces-blank/tools/scripts/hexana-analyze.sh disasm fixtures/wasm/add.wasm 0

# Start standalone Hexana MCP server over stdio
hexana-mcp stdio --tool-profile=production --log-level=quiet

# Start standalone Hexana MCP server over HTTP
hexana-mcp http --port=8999 --log-level=info
```
