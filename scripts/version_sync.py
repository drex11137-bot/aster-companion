#!/usr/bin/env python3
"""
Antigravity CLI & Toolchain Version Synchronization & Incremental History Manager (Section 4.2).

Automatically detects live CLI toolchain updates across core tools (agy, python3, node, git),
reconciles the active specifications in `ENVIRONMENT.md`, maintains an incremental
version history audit table, and logs formal `## Superseded` records conforming to
Axioms 3, 6, 7, and 13 of `POLICY.md`, ensuring historical records are never wiped.
"""

import os
import re
import sys
import shutil
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional, List

DEFAULT_ENV_FILE = os.path.expanduser("~/.gemini/antigravity-cli/memory/ENVIRONMENT.md")
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

try:
    from lock_manager import safe_update_memory
except ImportError:
    safe_update_memory = None


CLI_TOOLS = {
    "agy": {
        "name": "Antigravity CLI",
        "cmd": ["agy", "--version"],
        "regex": r"([0-9\.]+)",
        "source": "agy --version",
        "default_binary": "/home/codespace/.local/bin/agy",
        "spec_pattern": r"-\s*\[\d{4}-\d{2}-\d{2}\]\s*Antigravity CLI Version:\s*([0-9\.]+)(?:\s*\(([^)]*)\))?",
        "spec_template": "- [{date}] Antigravity CLI Version: {version} (`{path}`)."
    },
    "python3": {
        "name": "Python",
        "cmd": ["python3", "--version"],
        "regex": r"Python\s+([0-9\.]+)",
        "source": "python3 --version",
        "default_binary": "/home/codespace/.python/current/bin/python3",
        "spec_pattern": r"-\s*\[\d{4}-\d{2}-\d{2}\]\s*Python Version:\s*([0-9\.]+)(?:\s*\(([^)]*)\))?",
        "spec_template": "- [{date}] Python Version: {version} (`{path}`)."
    },
    "node": {
        "name": "Node.js",
        "cmd": ["node", "--version"],
        "regex": r"v?([0-9\.]+)",
        "source": "node --version",
        "default_binary": "/home/codespace/nvm/current/bin/node",
        "spec_pattern": r"-\s*\[\d{4}-\d{2}-\d{2}\]\s*Node\.js Version:\s*([0-9\.]+)(?:\s*\(([^)]*)\))?",
        "spec_template": "- [{date}] Node.js Version: {version} (`{path}`)."
    },
    "git": {
        "name": "Git",
        "cmd": ["git", "--version"],
        "regex": r"git version\s+([0-9\.]+)",
        "source": "git --version",
        "default_binary": "/usr/local/bin/git",
        "spec_pattern": r"-\s*\[\d{4}-\d{2}-\d{2}\]\s*Git Version:\s*([0-9\.]+)(?:\s*\(([^)]*)\))?",
        "spec_template": "- [{date}] Git Version: {version} (`{path}`)."
    }
}


def get_live_cli_version() -> str:
    """Query live Antigravity CLI binary for its version string (backwards-compatible helper)."""
    tool_info = get_live_tool_version("agy")
    return tool_info.get("version", "unknown")


def get_live_tool_version(tool_key: str) -> Dict[str, Any]:
    """Query live system binary for a specific tool's version and location."""
    conf = CLI_TOOLS.get(tool_key)
    if not conf:
        return {"version": "unknown", "path": "unknown", "source": "unknown"}

    cmd = conf["cmd"]
    source = conf["source"]
    regex = conf["regex"]
    resolved_path = shutil.which(cmd[0]) or conf.get("default_binary", "unknown")

    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        output = (res.stdout + " " + res.stderr).strip()
        match = re.search(regex, output)
        if match:
            return {
                "name": conf["name"],
                "version": match.group(1).strip(),
                "path": resolved_path,
                "source": source
            }
    except Exception:
        pass

    return {
        "name": conf["name"],
        "version": "unknown",
        "path": resolved_path,
        "source": source
    }


def get_all_live_tool_versions() -> Dict[str, Dict[str, Any]]:
    """Query all configured CLI tools for their live versions."""
    return {k: get_live_tool_version(k) for k in CLI_TOOLS}


def extract_current_recorded_version(content: str) -> Optional[str]:
    """Extract current recorded Antigravity CLI version from ENVIRONMENT.md (backwards-compatible helper)."""
    match = re.search(r"Antigravity CLI Version:\s*([0-9\.]+)", content)
    if match:
        return match.group(1).strip()
    return None


def extract_recorded_tool_versions(content: str) -> Dict[str, Optional[str]]:
    """Extract all recorded CLI tool versions from ENVIRONMENT.md."""
    recorded = {}
    
    # 1. Antigravity CLI
    agy_match = re.search(r"Antigravity CLI Version:\s*([0-9\.]+)", content)
    recorded["agy"] = agy_match.group(1).strip() if agy_match else None

    # 2. Python
    py_match = re.search(r"Python Version:\s*([0-9\.]+)", content)
    if not py_match:
        py_match = re.search(r"Python\s+([0-9\.]+)", content)
    recorded["python3"] = py_match.group(1).strip() if py_match else None

    # 3. Node.js
    node_match = re.search(r"Node\.js Version:\s*([0-9\.]+)", content)
    if not node_match:
        node_match = re.search(r"Node\.js\s+v?([0-9\.]+)", content)
    recorded["node"] = node_match.group(1).strip() if node_match else None

    # 4. Git
    git_match = re.search(r"Git Version:\s*([0-9\.]+)", content)
    if not git_match:
        git_match = re.search(r"git version\s+([0-9\.]+)", content)
    recorded["git"] = git_match.group(1).strip() if git_match else None

    # Also check active rows in version history tables
    table_matches = re.findall(r"\|\s*`?([a-zA-Z0-9_\-\.\s]+?)`?\s*\|\s*`?([0-9\.]+)`?\s*\|\s*[^|]+\|\s*[^|]+\|\s*[^|]+\|\s*ACTIVE\s*\|", content)
    for tool_raw, ver in table_matches:
        t_clean = tool_raw.strip().lower()
        if "agy" in t_clean or "antigravity" in t_clean:
            recorded["agy"] = ver
        elif "python" in t_clean:
            recorded["python3"] = ver
        elif "node" in t_clean:
            recorded["node"] = ver
        elif "git" in t_clean:
            recorded["git"] = ver

    return recorded


def sync_environment_version(
    env_file_path: str = DEFAULT_ENV_FILE,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Detects CLI toolchain version drift and updates ENVIRONMENT.md with:
    - Current observed versions and paths in specifications
    - Incremental history rows marking superseded previous versions
    - Formal ## Superseded records without wiping historical entries.
    """
    live_tools = get_all_live_tool_versions()
    agy_live = live_tools.get("agy", {}).get("version", "unknown")

    result = {
        "live_version": agy_live,
        "recorded_version": None,
        "previous_version": None,
        "new_version": agy_live,
        "updated": False,
        "tools": {},
        "error": None
    }

    if not os.path.exists(env_file_path):
        result["error"] = f"Environment file not found at {env_file_path}"
        return result

    try:
        with open(env_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        recorded_versions = extract_recorded_tool_versions(content)
        result["recorded_version"] = recorded_versions.get("agy")
        result["previous_version"] = recorded_versions.get("agy")

        today_str = datetime.now().strftime("%Y-%m-%d")
        new_content = content
        any_updated = False
        superseded_blocks_to_add = []

        # Update Last Updated line if anything changed
        for tool_key, tool_info in live_tools.items():
            conf = CLI_TOOLS[tool_key]
            live_ver = tool_info.get("version", "unknown")
            rec_ver = recorded_versions.get(tool_key)
            tool_path = tool_info.get("path", conf.get("default_binary", "unknown"))
            tool_source = tool_info.get("source", conf.get("source", "unknown"))
            tool_name = conf["name"]

            result["tools"][tool_key] = {
                "name": tool_name,
                "live_version": live_ver,
                "recorded_version": rec_ver,
                "path": tool_path,
                "source": tool_source,
                "updated": False
            }

            if live_ver == "unknown":
                continue

            if rec_ver != live_ver:
                any_updated = True
                result["tools"][tool_key]["updated"] = True
                result["tools"][tool_key]["previous_version"] = rec_ver

                # 1. Update specification line in ## Environment Specifications
                if tool_key == "agy":
                    new_content = re.sub(
                        r"-\s*\[\d{4}-\d{2}-\d{2}\]\s*Antigravity CLI Version:\s*[0-9\.]+(\s*\([^)]*\))?",
                        f"- [{today_str}] Antigravity CLI Version: {live_ver} (`{tool_path}`).",
                        new_content
                    )
                else:
                    spec_pat = conf["spec_pattern"]
                    if re.search(spec_pat, new_content):
                        new_content = re.sub(
                            spec_pat,
                            f"- [{today_str}] {tool_name} Version: {live_ver} (`{tool_path}`).",
                            new_content
                        )

                # 2. Add formal superseded record block (do not wipe old ones)
                if rec_ver:
                    block = f"""
## Superseded ({today_str})
**Type:** ENVIRONMENT **Scope:** GLOBAL **Confidence:** VERIFIED **Source:** {tool_source} **Status:** SUPERSEDED
- **Previous**: {tool_name} Version: {rec_ver} (`{tool_path}`)
- **Current**: {tool_name} Version: {live_ver} (`{tool_path}`)
- **Reason**: Live {tool_name} toolchain update detected on workstation
- **Date**: {today_str}
"""
                    superseded_blocks_to_add.append(block.strip())

        # 3. Synchronize Antigravity CLI Version History Table
        if "agy" in result["tools"] and (result["tools"]["agy"]["updated"] or "## Antigravity CLI Version History" not in new_content):
            new_row = f"| `{agy_live}` | {today_str} | `{result['recorded_version'] or 'unknown'}` | `agy --version` | ACTIVE |"
            if "## Antigravity CLI Version History" in new_content:
                lines = new_content.splitlines()
                updated_lines = []
                inserted = False
                for line in lines:
                    if line.strip().startswith("| `") and "ACTIVE" in line:
                        line = line.replace("ACTIVE", "SUPERSEDED")
                    updated_lines.append(line)
                    if line.strip().startswith("| :--- | :--- | :--- | :--- | :--- |") and not inserted:
                        updated_lines.append(new_row)
                        inserted = True
                new_content = "\n".join(updated_lines)
            else:
                initial_table = f"""## Antigravity CLI Version History
| Version | First Observed | Previous Version | Detection Source | Status |
| :--- | :--- | :--- | :--- | :--- |
| `{result['recorded_version'] or '1.1.23'}` | 2026-09-01 | Baseline | Workstation Bootstrap | SUPERSEDED |
{new_row}
"""
                if "## Superseded" in new_content:
                    parts = new_content.split("## Superseded", 1)
                    new_content = parts[0].rstrip() + "\n\n" + initial_table + "\n## Superseded" + parts[1]
                else:
                    new_content = new_content.rstrip() + "\n\n" + initial_table

        # 4. Synchronize Comprehensive CLI Tool Version History Table
        tool_history_header = "## CLI Tool Version History\n| Tool | Version | First Observed | Previous Version | Detection Source | Status |\n| :--- | :--- | :--- | :--- | :--- | :--- |"
        if "## CLI Tool Version History" in new_content:
            lines = new_content.splitlines()
            updated_lines = []
            for line in lines:
                for tool_k, tinfo in result["tools"].items():
                    if tinfo.get("updated") and f"| `{tool_k}` |" in line and "ACTIVE" in line:
                        line = line.replace("ACTIVE", "SUPERSEDED")
                updated_lines.append(line)
            # Add new rows for updated tools
            inserted_table_lines = []
            for line in updated_lines:
                inserted_table_lines.append(line)
                if line.strip().startswith("| :--- | :--- | :--- | :--- | :--- | :--- |"):
                    for tool_k, tinfo in result["tools"].items():
                        if tinfo.get("updated"):
                            t_row = f"| `{tool_k}` | `{tinfo['live_version']}` | {today_str} | `{tinfo.get('previous_version') or 'Baseline'}` | `{tinfo['source']}` | ACTIVE |"
                            inserted_table_lines.append(t_row)
            new_content = "\n".join(inserted_table_lines)
        else:
            # Build initial CLI tool version table
            tool_rows = []
            for tool_k, tinfo in result["tools"].items():
                prev = tinfo.get("previous_version") or "Baseline"
                tool_rows.append(f"| `{tool_k}` | `{tinfo['live_version']}` | {today_str} | `{prev}` | `{tinfo['source']}` | ACTIVE |")
            full_tool_table = tool_history_header + "\n" + "\n".join(tool_rows) + "\n"
            
            if "## Superseded" in new_content:
                parts = new_content.split("## Superseded", 1)
                new_content = parts[0].rstrip() + "\n\n" + full_tool_table + "\n## Superseded" + parts[1]
            else:
                new_content = new_content.rstrip() + "\n\n" + full_tool_table
            any_updated = True

        # 5. Append new formal ## Superseded blocks while maintaining all existing ones
        if superseded_blocks_to_add:
            blocks_text = "\n\n".join(superseded_blocks_to_add)
            new_content = new_content.rstrip() + "\n\n" + blocks_text + "\n"

        # 6. Update Last Updated header line if any updates occurred
        if any_updated:
            new_content = re.sub(r"Last Updated:\s*\d{4}-\d{2}-\d{2}", f"Last Updated: {today_str}", new_content)

            if not dry_run:
                if safe_update_memory:
                    safe_update_memory(env_file_path, lambda _: new_content)
                else:
                    with open(env_file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)

            result["updated"] = True
            result["new_version"] = agy_live

    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Antigravity CLI & Toolchain Version Sync (Section 4.2)")
    parser.add_argument("--env-file", default=DEFAULT_ENV_FILE, help="Path to ENVIRONMENT.md")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without modifying files")
    parser.add_argument("--check", action="store_true", help="Only check if tools are synchronized")
    args = parser.parse_args()

    res = sync_environment_version(args.env_file, dry_run=args.dry_run or args.check)
    if res.get("error"):
        print(f"Error: {res['error']}")
        sys.exit(1)

    print("=" * 60)
    print("ANTIGRAVITY TOOLCHAIN VERSION SYNCHRONIZATION")
    print("=" * 60)
    for tool_k, tinfo in res.get("tools", {}).items():
        status = "UPDATED" if tinfo.get("updated") else "SYNCHRONIZED"
        print(f"- {tinfo['name']} ({tool_k}): {tinfo['live_version']} [{status}] (Source: {tinfo['source']})")
    print("=" * 60)

    if res.get("updated"):
        if args.check:
            print("DRIFT DETECTED: Live CLI tool versions differ from recorded state.")
            sys.exit(1)
        print(f"SUCCESS: Synchronized toolchain versions to {args.env_file}.")
    else:
        print("UP-TO-DATE: All CLI toolchain versions are already synchronized.")
    sys.exit(0)


if __name__ == "__main__":
    main()
