#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

def run_cmd(cmd, timeout=5):
    try:
        p = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            timeout=timeout
        )
        return {
            'command': cmd,
            'exit_code': p.returncode,
            'stdout': p.stdout.strip(),
            'stderr': p.stderr.strip()
        }
    except subprocess.TimeoutExpired:
        return {'command': cmd, 'exit_code': -1, 'stdout': '', 'stderr': 'TimeoutExpired'}
    except Exception as e:
        return {'command': cmd, 'exit_code': -1, 'stdout': '', 'stderr': str(e)}

def probe_tool(name, check_cmd, path_override=None):
    binary_path = path_override or shutil.which(name)
    if not binary_path:
        # Check if check_cmd works even if which fails
        res = run_cmd(check_cmd)
        if res['exit_code'] == 0:
            first_line = (res['stdout'] or res['stderr']).split('\n')[0]
            return {
                'name': name,
                'available': True,
                'path': 'shell command / alias',
                'version_raw': first_line,
                'full_output': (res['stdout'] + ('\n' + res['stderr'] if res['stderr'] else '')).strip()
            }
        return {
            'name': name,
            'available': False,
            'path': None,
            'version_raw': None,
            'full_output': None
        }
    
    res = run_cmd(check_cmd)
    raw_output = res['stdout'] if res['stdout'] else res['stderr']
    first_line = raw_output.split('\n')[0] if raw_output else ''
    
    return {
        'name': name,
        'available': (res['exit_code'] == 0),
        'path': binary_path,
        'version_raw': first_line if res['exit_code'] == 0 else (first_line or f"Failed with exit code {res['exit_code']}"),
        'full_output': raw_output.strip()
    }

def sanitize_env(env):
    sanitized = {}
    secret_patterns = [
        r'KEY', r'SECRET', r'TOKEN', r'PASS', r'AUTH', r'CREDENTIAL', r'PRIVATE',
        r'SIGNATURE', r'BEARER', r'COOKIE', r'CERT'
    ]
    for k, v in sorted(env.items()):
        is_secret = any(re.search(pat, k, re.IGNORECASE) for pat in secret_patterns)
        if is_secret:
            sanitized[k] = '[REDACTED_SECRET]'
        else:
            sanitized[k] = v
    return sanitized

def main():
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # 1. System Info
    uname_a = run_cmd("uname -a")
    uname_m = run_cmd("uname -m")
    os_release = run_cmd("cat /etc/os-release")
    user_id = run_cmd("id")
    nproc = run_cmd("nproc")
    free_h = run_cmd("free -h")
    df_h = run_cmd("df -h")
    git_status = run_cmd("git status --short")
    git_branch = run_cmd("git branch --show-current")
    agy_version = run_cmd("agy --version")
    code_extensions = run_cmd("code --list-extensions")
    
    system_info = {
        'timestamp': timestamp,
        'uname_a': uname_a['stdout'],
        'architecture': uname_m['stdout'],
        'os_release': os_release['stdout'],
        'id': user_id['stdout'],
        'nproc': nproc['stdout'],
        'free_h': free_h['stdout'],
        'df_h': df_h['stdout'],
        'git_status': git_status['stdout'],
        'git_branch': git_branch['stdout'],
        'agy_version': agy_version['stdout'] if agy_version['exit_code'] == 0 else agy_version['stderr'],
        'code_available': shutil.which("code") is not None,
        'code_extensions': code_extensions['stdout'].splitlines() if code_extensions['exit_code'] == 0 else [],
        'path': os.environ.get('PATH', '').split(':'),
        'environment': sanitize_env(dict(os.environ))
    }
    
    # Tool categories
    android_home = os.environ.get('ANDROID_HOME', '/opt/android-sdk')
    ghidra_home = os.environ.get('GHIDRA_HOME', '/opt/ghidra')
    
    tool_definitions = {
        "core_cli": [
            ("git", "git --version"),
            ("gh", "gh --version"),
            ("curl", "curl --version"),
            ("jq", "jq --version"),
            ("yq", "yq --version"),
            ("rg", "rg --version"),
            ("fd", "fd --version" if shutil.which("fd") else "fdfind --version"),
            ("tree", "tree --version"),
            ("make", "make --version"),
            ("cmake", "cmake --version"),
            ("ninja", "ninja --version"),
            ("gcc", "gcc --version"),
            ("g++", "g++ --version"),
            ("clang", "clang --version"),
            ("clang++", "clang++ --version"),
            ("python3", "python3 --version"),
            ("pip3", "pip3 --version"),
            ("node", "node --version"),
            ("npm", "npm --version"),
            ("pnpm", "pnpm --version"),
            ("yarn", "yarn --version"),
            ("java", "java -version"),
            ("javac", "javac -version"),
            ("go", "go version"),
            ("rustc", "rustc --version"),
            ("cargo", "cargo --version"),
        ],
        "android_tools": [
            ("sdkmanager", f"{android_home}/cmdline-tools/latest/bin/sdkmanager --version" if os.path.exists(f"{android_home}/cmdline-tools/latest/bin/sdkmanager") else "sdkmanager --version"),
            ("adb", "adb --version"),
            ("avdmanager", f"{android_home}/cmdline-tools/latest/bin/avdmanager list avd" if os.path.exists(f"{android_home}/cmdline-tools/latest/bin/avdmanager") else "avdmanager list avd"),
            ("apkanalyzer", f"{android_home}/cmdline-tools/latest/bin/apkanalyzer --version" if os.path.exists(f"{android_home}/cmdline-tools/latest/bin/apkanalyzer") else "apkanalyzer --version"),
            ("apktool", "apktool -version"),
            ("jadx", "jadx --version"),
            ("apksigner", "apksigner --version"),
            ("zipalign", "zipalign -c -v 4 /dev/null 2>&1 || true"),
            ("smali", "smali --version"),
            ("baksmali", "baksmali --version"),
            ("frida", "frida --version"),
            ("gradle", "gradle --version"),
        ],
        "binary_tools": [
            ("file", "file --version"),
            ("readelf", "readelf -v"),
            ("objdump", "objdump -v"),
            ("nm", "nm -V"),
            ("strings", "strings -v"),
            ("checksec", "checksec --version"),
            ("ghidra_headless", f"{ghidra_home}/support/analyzeHeadless -help" if os.path.exists(f"{ghidra_home}/support/analyzeHeadless") else "analyzeHeadless -help"),
            ("radare2", "radare2 -v"),
            ("rizin", "rizin -v"),
            ("gdb", "gdb --version"),
            ("lldb", "lldb --version"),
            ("strace", "strace -V"),
            ("ltrace", "ltrace -V"),
            ("ropgadget", "ROPgadget --version"),
            ("one_gadget", "one_gadget --version"),
            ("patchelf", "patchelf --version"),
        ],
        "wasm_tools": [
            ("wat2wasm", "wat2wasm --version"),
            ("wasm2wat", "wasm2wat --version"),
            ("wasm-validate", "wasm-validate --version"),
            ("wasm-objdump", "wasm-objdump --version"),
            ("wasm-opt", "wasm-opt --version"),
            ("wasmtime", "wasmtime --version"),
            ("wasmer", "wasmer --version"),
            ("wasm-decompile", "wasm-decompile --version"),
            ("wasm2c", "wasm2c --version"),
        ],
        "security_tools": [
            ("semgrep", "semgrep --version"),
            ("codeql", "codeql version"),
            ("gitleaks", "gitleaks version"),
            ("bandit", "bandit --version"),
            ("trivy", "trivy --version"),
            ("osv-scanner", "osv-scanner --version"),
            ("checkov", "checkov --version"),
            ("snyk", "snyk --version"),
            ("grype", "grype version"),
            ("syft", "syft version"),
        ],
        "network_tools": [
            ("tshark", "tshark -v"),
            ("tcpdump", "tcpdump --version"),
            ("capinfos", "capinfos -v"),
            ("editcap", "editcap -v"),
            ("mergecap", "mergecap -v"),
            ("nmap", "nmap --version"),
            ("scapy", 'python3 -c "import scapy; print(scapy.__version__)"'),
            ("masscan", "masscan --version"),
            ("termshark", "termshark --version"),
        ],
        "container_tools": [
            ("docker", "docker --version"),
            ("docker-compose", "docker compose version"),
            ("kubectl", "kubectl version --client"),
            ("helm", "helm version"),
            ("kustomize", "kustomize version"),
            ("kubeconform", "kubeconform -v"),
            ("hadolint", "hadolint --version"),
            ("podman", "podman --version"),
            ("nerdctl", "nerdctl --version"),
        ],
        "browser_tools": [
            ("playwright", "playwright --version || npx --no-install playwright --version || python3 -m playwright --version"),
            ("puppeteer", "npx --no-install puppeteer --version"),
            ("chromium", "chromium --version || chromium-browser --version || google-chrome --version"),
            ("firefox", "firefox --version"),
        ]
    }
    
    inventory_results = {}
    for category, tools in tool_definitions.items():
        inventory_results[category] = []
        for name, cmd in tools:
            res = probe_tool(name, cmd)
            inventory_results[category].append(res)
            
    full_inventory = {
        'system': system_info,
        'tools': inventory_results
    }
    
    # Save JSON snapshot
    os.makedirs('.environment-audit/baseline', exist_ok=True)
    json_path = '.environment-audit/baseline/system-inventory.json'
    with open(json_path, 'w') as f:
        json.dump(full_inventory, f, indent=2)
    print(f"Saved JSON inventory to {json_path}")
    
    # Generate Markdown Report
    md_path = '.environment-audit/baseline/inventory-report.md'
    with open(md_path, 'w') as f:
        f.write("# Baseline System & Toolchain Inventory Report\n\n")
        f.write(f"- **Audit Timestamp**: `{timestamp}`\n")
        f.write(f"- **Auditor**: Subagent 01 (Inventory Auditor - Phase A)\n")
        f.write(f"- **Host Uname**: `{system_info['uname_a']}`\n")
        f.write(f"- **Architecture**: `{system_info['architecture']}`\n")
        f.write(f"- **CPU Cores (`nproc`)**: `{system_info['nproc']}`\n")
        f.write(f"- **User Identity**: `{system_info['id']}`\n")
        f.write(f"- **Git Branch**: `{system_info['git_branch']}`\n")
        f.write(f"- **Git Cleanliness**: `{'Clean' if not system_info['git_status'] else 'Modified files present'}`\n")
        f.write(f"- **AGY CLI**: `{system_info['agy_version']}`\n\n")
        
        f.write("## 1. System Hardware & Storage\n\n")
        f.write("### Memory (`free -h`)\n```text\n")
        f.write(system_info['free_h'] + "\n```\n\n")
        f.write("### Filesystem (`df -h`)\n```text\n")
        f.write(system_info['df_h'] + "\n```\n\n")
        f.write("### OS Release (`/etc/os-release`)\n```text\n")
        f.write(system_info['os_release'] + "\n```\n\n")
        
        f.write("## 2. Environment & PATH\n\n")
        f.write("### Executable Search PATH\n")
        for p in system_info['path']:
            f.write(f"- `{p}`\n")
        f.write("\n")
        
        f.write("### Key Environment Variables (Sanitized)\n\n")
        f.write("| Variable | Value |\n")
        f.write("| :--- | :--- |\n")
        key_vars = [
            'SHELL', 'USER', 'HOME', 'WORKSPACE', 'ANDROID_HOME', 'ANDROID_SDK_ROOT',
            'GHIDRA_HOME', 'JAVA_HOME', 'GOPATH', 'GOROOT', 'CARGO_HOME', 'RUSTUP_HOME',
            'NODE_PATH', 'LANG', 'LC_ALL', 'PLAYWRIGHT_BROWSERS_PATH'
        ]
        for kv in key_vars:
            val = system_info['environment'].get(kv, '_Not set_')
            f.write(f"| `{kv}` | `{val}` |\n")
        f.write("\n")
        
        f.write("## 3. Toolchain Verification Matrix\n\n")
        
        cat_titles = {
            "core_cli": "Core CLI & Language Runtimes",
            "android_tools": "Android SDK & Mobile Reverse Engineering",
            "binary_tools": "Binary Inspection & Disassembly Tools",
            "wasm_tools": "WebAssembly (WASM) Toolchains",
            "security_tools": "Security, SAST & Vulnerability Scanners",
            "network_tools": "Network Forensics & Packet Analysis",
            "container_tools": "Container & Cloud-Native Tools",
            "browser_tools": "Browser & Playwright Automation"
        }
        
        for cat, items in inventory_results.items():
            f.write(f"### {cat_titles.get(cat, cat.title())}\n\n")
            f.write("| Tool | Status | Path | Observed Version Line |\n")
            f.write("| :--- | :---: | :--- | :--- |\n")
            for item in items:
                status = "✅ Present" if item['available'] else "❌ Missing"
                path = f"`{item['path']}`" if item['path'] else "—"
                ver = f"`{item['version_raw']}`" if item['version_raw'] else "—"
                f.write(f"| **{item['name']}** | {status} | {path} | {ver} |\n")
            f.write("\n")
            
        f.write("## 4. Summary Statistics\n\n")
        total_tools = sum(len(items) for items in inventory_results.values())
        present_tools = sum(sum(1 for i in items if i['available']) for items in inventory_results.values())
        missing_tools = total_tools - present_tools
        f.write(f"- **Total Tools Probed**: {total_tools}\n")
        f.write(f"- **Tools Present / Operational**: {present_tools}\n")
        f.write(f"- **Tools Missing / Offline**: {missing_tools}\n")
        f.write(f"- **Coverage Percentage**: `{present_tools / total_tools * 100:.1f}%`\n\n")
        
    print(f"Saved Markdown report to {md_path}")

if __name__ == '__main__':
    main()
