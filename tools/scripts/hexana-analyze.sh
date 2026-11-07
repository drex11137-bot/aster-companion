#!/usr/bin/env bash
# ==============================================================================
# hexana-analyze.sh — JetBrains Hexana CLI & Fallback Binary Analysis Suite
# ==============================================================================
# Discovers hexana-mcp standalone binary or provides seamless fallback to native
# Linux WASM/ELF tools (wasm-tools, wabt, readelf, objdump, rizin, radare2).
# ==============================================================================
set -euo pipefail

HEXANA_BIN="$(which hexana-mcp 2>/dev/null || echo "/home/codespace/.hexana-storage/mcp/server/bin/hexana-mcp")"

function usage() {
    cat << 'EOF'
Usage: hexana-analyze.sh <command> [arguments...]

Commands:
  summary <file>           Display binary/module header, format, and section summary
  exports <file>           List exported functions and symbols
  imports <file>           List imported functions and dynamic dependencies
  disasm <file> [funcidx]  Disassemble WASM function or native entry
  doctor                   Run environment health check for Hexana and fallback tools
  mcp-stdio                Launch Hexana MCP server over stdio
  mcp-http [port]          Launch Hexana MCP server over HTTP (default port 8999)

EOF
    exit 1
}

function call_hexana_stdio() {
    local method="$1"
    local tool_name="$2"
    local args_json="$3"
    
    python3 -c "
import subprocess, json, sys

p = subprocess.Popen(
    ['$HEXANA_BIN', 'stdio', '--tool-profile=advanced', '--log-level=quiet'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

def send_req(req):
    p.stdin.write(json.dumps(req) + '\n')
    p.stdin.flush()
    line = p.stdout.readline()
    return json.loads(line) if line else {}

def send_notif(notif):
    p.stdin.write(json.dumps(notif) + '\n')
    p.stdin.flush()

send_req({
    'jsonrpc': '2.0',
    'id': 1,
    'method': 'initialize',
    'params': {
        'protocolVersion': '2024-11-05',
        'capabilities': {},
        'clientInfo': {'name': 'hexana-cli-wrapper', 'version': '1.0'}
    }
})
send_notif({'jsonrpc': '2.0', 'method': 'notifications/initialized'})

res = send_req({
    'jsonrpc': '2.0',
    'id': 2,
    'method': '$method',
    'params': {
        'name': '$tool_name',
        'arguments': json.loads('''$args_json''')
    }
})

p.stdin.close()
p.terminate()
p.wait()

if 'result' in res:
    structured = res['result'].get('structuredContent')
    if structured:
        print(json.dumps(structured, indent=2))
    elif 'content' in res['result']:
        for item in res['result']['content']:
            print(item.get('text', ''))
    else:
        print(json.dumps(res['result'], indent=2))
elif 'error' in res:
    print('ERROR:', json.dumps(res['error'], indent=2), file=sys.stderr)
    sys.exit(1)
"
}

function cmd_summary() {
    local target="$1"
    if [ ! -f "$target" ]; then
        echo "Error: File not found: $target" >&2
        exit 1
    fi

    local abs_target
    abs_target="$(realpath "$target")"

    if [ -x "$HEXANA_BIN" ]; then
        echo "=== Hexana MCP Binary Summary ($abs_target) ==="
        if [[ "$abs_target" =~ \.wasm$ ]]; then
            call_hexana_stdio "tools/call" "summarize_module" "{\"path\":\"$abs_target\"}"
        else
            call_hexana_stdio "tools/call" "summarize_binary" "{\"path\":\"$abs_target\"}"
        fi
    else
        echo "=== Fallback CLI Binary Summary ($abs_target) ==="
        file "$abs_target"
        if [[ "$abs_target" =~ \.wasm$ ]]; then
            if command -v wasm-tools >/dev/null 2>&1; then
                wasm-tools dump "$abs_target"
            fi
        else
            if command -v readelf >/dev/null 2>&1; then
                readelf -h "$abs_target"
            fi
        fi
    fi
}

function cmd_exports() {
    local target="$1"
    if [ ! -f "$target" ]; then
        echo "Error: File not found: $target" >&2
        exit 1
    fi

    local abs_target
    abs_target="$(realpath "$target")"

    if [ -x "$HEXANA_BIN" ]; then
        echo "=== Hexana MCP Exports Listing ($abs_target) ==="
        if [[ "$abs_target" =~ \.wasm$ ]]; then
            call_hexana_stdio "tools/call" "list_exports" "{\"path\":\"$abs_target\"}"
        else
            call_hexana_stdio "tools/call" "list_binary_functions" "{\"path\":\"$abs_target\"}"
        fi
    else
        echo "=== Fallback CLI Exports Listing ($abs_target) ==="
        if [[ "$abs_target" =~ \.wasm$ ]]; then
            if command -v wasm-tools >/dev/null 2>&1; then
                wasm-tools dump "$abs_target" | grep -A 5 "export section"
            elif command -v wasm2wat >/dev/null 2>&1; then
                wasm2wat "$abs_target" | grep 'export'
            fi
        else
            if command -v nm >/dev/null 2>&1; then
                nm -D --defined-only "$abs_target" 2>/dev/null || readelf --dyn-syms "$abs_target"
            fi
        fi
    fi
}

function cmd_imports() {
    local target="$1"
    if [ ! -f "$target" ]; then
        echo "Error: File not found: $target" >&2
        exit 1
    fi

    local abs_target
    abs_target="$(realpath "$target")"

    if [ -x "$HEXANA_BIN" ]; then
        echo "=== Hexana MCP Imports Listing ($abs_target) ==="
        if [[ "$abs_target" =~ \.wasm$ ]]; then
            call_hexana_stdio "tools/call" "list_imports" "{\"path\":\"$abs_target\"}"
        else
            call_hexana_stdio "tools/call" "list_binary_functions" "{\"path\":\"$abs_target\"}"
        fi
    else
        echo "=== Fallback CLI Imports Listing ($abs_target) ==="
        if [[ "$abs_target" =~ \.wasm$ ]]; then
            if command -v wasm-tools >/dev/null 2>&1; then
                wasm-tools dump "$abs_target" | grep -A 5 "import section"
            elif command -v wasm2wat >/dev/null 2>&1; then
                wasm2wat "$abs_target" | grep 'import'
            fi
        else
            if command -v readelf >/dev/null 2>&1; then
                readelf -d "$abs_target"
            fi
        fi
    fi
}

function cmd_disasm() {
    local target="$1"
    local funcidx="${2:-0}"
    if [ ! -f "$target" ]; then
        echo "Error: File not found: $target" >&2
        exit 1
    fi

    local abs_target
    abs_target="$(realpath "$target")"

    if [ -x "$HEXANA_BIN" ] && [[ "$abs_target" =~ \.wasm$ ]]; then
        echo "=== Hexana MCP Function Disassembly ($abs_target, funcidx=$funcidx) ==="
        call_hexana_stdio "tools/call" "disassemble_function" "{\"path\":\"$abs_target\",\"funcidx\":$funcidx}"
    else
        echo "=== Fallback CLI Disassembly ($abs_target) ==="
        if [[ "$abs_target" =~ \.wasm$ ]]; then
            if command -v wasm2wat >/dev/null 2>&1; then
                wasm2wat "$abs_target"
            elif command -v wasm-tools >/dev/null 2>&1; then
                wasm-tools print "$abs_target"
            fi
        else
            if command -v objdump >/dev/null 2>&1; then
                objdump -d "$abs_target" | head -n 50
            fi
        fi
    fi
}

function cmd_doctor() {
    echo "================================================================="
    echo " Hexana & Binary Analysis Health Doctor"
    echo "================================================================="
    
    echo -n "[1/6] Hexana MCP Binary: "
    if [ -x "$HEXANA_BIN" ]; then
        echo "AVAILABLE ($HEXANA_BIN)"
        "$HEXANA_BIN" doctor 2>&1 | sed 's/^/      /'
    else
        echo "NOT FOUND / NOT EXECUTABLE ($HEXANA_BIN)"
    fi

    echo -n "[2/6] VS Code Extension: "
    if [ -d "/home/codespace/.vscode-remote/extensions/jetbrains.hexana-wasm-0.10.0" ]; then
        echo "INSTALLED (jetbrains.hexana-wasm v0.10.0)"
    else
        echo "NOT INSTALLED"
    fi

    echo -n "[3/6] WebAssembly Tools: "
    local wasm_status="PASS ("
    command -v wasm-tools >/dev/null 2>&1 && wasm_status+="wasm-tools "
    command -v wasm2wat >/dev/null 2>&1 && wasm_status+="wabt "
    command -v wasmtime >/dev/null 2>&1 && wasm_status+="wasmtime "
    echo "${wasm_status% })"

    echo -n "[4/6] Native Binary Tools: "
    local bin_status="PASS ("
    command -v readelf >/dev/null 2>&1 && bin_status+="readelf "
    command -v objdump >/dev/null 2>&1 && bin_status+="objdump "
    command -v nm >/dev/null 2>&1 && bin_status+="nm "
    command -v checksec >/dev/null 2>&1 && bin_status+="checksec "
    echo "${bin_status% })"

    echo -n "[5/6] Reverse Engineering Frameworks: "
    local re_status="PASS ("
    command -v rz-bin >/dev/null 2>&1 && re_status+="rizin "
    command -v radare2 >/dev/null 2>&1 && re_status+="radare2 "
    [ -n "${GHIDRA_HOME:-}" ] && re_status+="ghidra "
    echo "${re_status% })"

    echo -n "[6/6] Antigravity MCP Integration: "
    if grep -q "hexana" /workspaces/codespaces-blank/.agents/mcp_config.json 2>/dev/null; then
        echo "CONFIGURED (.agents/mcp_config.json)"
    else
        echo "NOT CONFIGURED"
    fi
    echo "================================================================="
}

case "${1:-}" in
    summary)
        [ $# -ge 2 ] || usage
        cmd_summary "$2"
        ;;
    exports)
        [ $# -ge 2 ] || usage
        cmd_exports "$2"
        ;;
    imports)
        [ $# -ge 2 ] || usage
        cmd_imports "$2"
        ;;
    disasm)
        [ $# -ge 2 ] || usage
        cmd_disasm "$2" "${3:-0}"
        ;;
    doctor)
        cmd_doctor
        ;;
    mcp-stdio)
        exec "$HEXANA_BIN" stdio --tool-profile=production --log-level=quiet
        ;;
    mcp-http)
        local port="${2:-8999}"
        exec "$HEXANA_BIN" http --port="$port" --log-level=quiet
        ;;
    *)
        if [ -n "${1:-}" ] && [ -f "$1" ]; then
            cmd_summary "$1"
        else
            usage
        fi
        ;;
esac
