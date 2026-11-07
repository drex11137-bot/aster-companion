#!/usr/bin/env python3
"""
Contradiction Detection & Superseding Logic for Antigravity Persistent Memory.
Hardened against Sections 15, 16, 22, 43 of instruction.md.
"""

import os
import re
import sys
import glob
from datetime import datetime

def find_superseded_blocks(content: str) -> list[dict]:
    results = []
    # Pattern 1: Section 42/43 style
    p1 = r"##\s*Superseded[^\n]*\n(?:[^\n]*\n)?- \*\*Previous\*\*:\s*([^\n]+)\n- \*\*Current\*\*:\s*([^\n]+)\n- \*\*Reason\*\*:\s*([^\n]+)\n- \*\*Date\*\*:\s*(\d{4}-\d{2}-\d{2})"
    for m in re.finditer(p1, content):
        results.append({
            "previous": m.group(1).strip(),
            "current": m.group(2).strip(),
            "reason": m.group(3).strip(),
            "date": m.group(4).strip(),
            "status": "SUPERSEDED"
        })
    # Pattern 2: Header style
    p2 = r"##\s*(\d{4}-\d{2}-\d{2})\s*—\s*([^\n]+)\n\*\*Type:\*\*\s*([^\n*]+)\s*\*\*Scope:\*\*\s*([^\n*]+)\s*\*\*Confidence:\*\*\s*([^\n*]+)\s*\*\*Source:\*\*\s*([^\n*]+)\s*\*\*Status:\*\*\s*(ACTIVE|SUPERSEDED|DEPRECATED|REVIEW)\n###\s*Previous:\s*([^\n]+)\n###\s*Current:\s*([^\n]+)\n###\s*Reason:\s*([^\n]+)"
    for m in re.finditer(p2, content):
        results.append({
            "date": m.group(1).strip(),
            "title": m.group(2).strip(),
            "type": m.group(3).strip(),
            "scope": m.group(4).strip(),
            "confidence": m.group(5).strip(),
            "source": m.group(6).strip(),
            "status": m.group(7).strip(),
            "previous": m.group(8).strip(),
            "current": m.group(9).strip(),
            "reason": m.group(10).strip()
        })
    return results

def format_superseded_entry(previous: str, current: str, reason: str, date_str: str, status: str = "SUPERSEDED", canonical_source: str = "unknown") -> str:
    """Formats an entry according to Section 43 (ACTIVE, SUPERSEDED, DEPRECATED, REVIEW) and Section 42."""
    if status not in ("ACTIVE", "SUPERSEDED", "DEPRECATED", "REVIEW"):
        status = "SUPERSEDED"
    
    return f"""## {date_str} — Memory Update
## Superseded ({date_str})
**Type:** DECISION **Scope:** PROJECT **Confidence:** VERIFIED **Source:** {canonical_source} **Status:** {status}
- **Previous**: {previous}
- **Current**: {current}
- **Reason**: {reason}
- **Date**: {date_str}
Previous: {previous}
Current: {current}
Reason: {reason}
Date: {date_str}
"""

def detect_version_contradiction(facts: dict, line: str, path: str, idx: int) -> list[str]:
    findings = []
    if "python" in line.lower() and any(w in line.lower() for w in ("require", "version", "runtime", ">=", "==", "<=")):
        versions = re.findall(r"Python\b.*?(?:>=|==|<=|>|<|:|version|required)?\s*(\d+\.\d+)", line, re.IGNORECASE)
        for v in versions:
            if "python_ver" in facts and facts["python_ver"]["ver"] != v:
                findings.append(f"Contradiction: Python version mismatch in {path}:{idx} (Python {v}) vs {facts['python_ver']['path']}:{facts['python_ver']['line']} (Python {facts['python_ver']['ver']})")
            else:
                facts["python_ver"] = {"ver": v, "path": path, "line": idx}
    return findings

def detect_tool_contradiction(facts: dict, line: str, path: str, idx: int) -> list[str]:
    findings = []
    npm_match = re.search(r'\b(npm|pnpm|yarn)\b', line, re.IGNORECASE)
    if npm_match and "package manage" in line.lower():
        tool = npm_match.group(1).lower()
        if "package_manager" in facts and facts["package_manager"]["tool"] != tool:
             findings.append(f"Contradiction (Package manager) in {path}:{idx} ({tool}) vs {facts['package_manager']['path']}:{facts['package_manager']['line']} ({facts['package_manager']['tool']})")
        else:
             facts["package_manager"] = {"tool": tool, "path": path, "line": idx}
    return findings

def detect_arch_contradiction(facts: dict, line: str, path: str, idx: int) -> list[str]:
    findings = []
    arch_match = re.search(r'Architecture:\s*(microservices|monolithic|serverless)', line, re.IGNORECASE)
    if arch_match:
        arch = arch_match.group(1).lower()
        if "architecture" in facts and facts["architecture"]["type"] != arch:
             findings.append(f"Contradiction (Architecture) in {path}:{idx} ({arch}) vs {facts['architecture']['path']}:{facts['architecture']['line']} ({facts['architecture']['type']})")
        else:
             facts["architecture"] = {"type": arch, "path": path, "line": idx}
    return findings

def scan_files_for_contradictions(file_paths: list[str], return_facts: bool = False):
    findings = []
    facts = {}
    for path in file_paths:
        if not os.path.exists(path) or os.path.isdir(path):
            continue
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
        in_superseded = False
        in_code_block = False
        for idx, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            
            # Skip checking within superseded entries to avoid false positives
            if "**Status:** SUPERSEDED" in line or "**Status:** DEPRECATED" in line:
                in_superseded = True
                continue
                
            if in_code_block or in_superseded:
                # Need some way to exit superseded block, simplistic for now
                if line.strip().startswith("## "):
                    in_superseded = False
                else:
                    continue

            findings.extend(detect_version_contradiction(facts, line, path, idx))
            findings.extend(detect_tool_contradiction(facts, line, path, idx))
            findings.extend(detect_arch_contradiction(facts, line, path, idx))
            
    if return_facts:
        return findings, facts
    return findings

def scan_files(file_paths: list[str]) -> list[str]:
    return scan_files_for_contradictions(file_paths)

def main():
    paths = sys.argv[1:] if len(sys.argv) > 1 else [
        os.path.expanduser("~/.gemini/antigravity-cli/memory/GENERAL.md"),
        "/workspaces/codespaces-blank/.agents/memory/ARCHITECTURE.md",
        "/workspaces/codespaces-blank/.agents/memory/GOTCHAS.md"
    ]
    contradictions = scan_files_for_contradictions(paths)
    if contradictions:
        print("CONTRADICTIONS_DETECTED:")
        for c in contradictions:
            print(f"  - {c}")
        sys.exit(1)
    else:
        print("NO_CONTRADICTIONS_FOUND: Memory is coherent.")
        sys.exit(0)

if __name__ == "__main__":
    main()
