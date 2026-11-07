#!/usr/bin/env python3
"""
Performance & Compaction Auditor for Antigravity Persistent Memory.
Measures and enforces line budgets, byte budgets, token estimates,
chronological session ordering, and fact deduplication with pointer recommendations.
"""

import os
import sys
import re
import json
import argparse
import time
import math
import glob
from typing import Dict, List, Tuple, Any, Optional

# Standard Line and Byte Budgets
LINE_BUDGETS: Dict[str, int] = {
    "CURRENT.md": 30,
    "INDEX.md": 50,
    "POLICY.md": 150,
    "GEMINI.md": 100,
    "GOTCHAS.md": 100,
    "DECISIONS.md": 200,
    "ARCHITECTURE.md": 200,
    "sessions": 150,  # per session file
    "default": 150,
}

BYTE_BUDGETS: Dict[str, int] = {
    "CURRENT.md": 2048,      # 2 KB
    "INDEX.md": 4096,        # 4 KB
    "POLICY.md": 6144,       # 6 KB
    "GEMINI.md": 8192,       # 8 KB
    "GOTCHAS.md": 8192,      # 8 KB
    "DECISIONS.md": 16384,   # 16 KB
    "ARCHITECTURE.md": 16384,# 16 KB
    "sessions": 12288,       # 12 KB per session file
    "default": 12288,        # 12 KB
}

def estimate_tokens(text: str) -> int:
    """Estimates token count (~4 chars per token average)."""
    if not text:
        return 0
    return max(1, len(text) // 4)

def get_budget_for_file(filename: str, parent_dir: str = "") -> Tuple[int, int]:
    """Returns (max_lines, max_bytes) for a given filename."""
    if "sessions" in parent_dir or "sessions" in filename:
        return LINE_BUDGETS["sessions"], BYTE_BUDGETS["sessions"]
    
    max_lines = LINE_BUDGETS.get(filename, LINE_BUDGETS["default"])
    max_bytes = BYTE_BUDGETS.get(filename, BYTE_BUDGETS["default"])
    return max_lines, max_bytes

def audit_file_budgets(file_path: str) -> Dict[str, Any]:
    """Audits line count, byte size, and token estimate for a single file."""
    if not os.path.isfile(file_path):
        return {"error": f"File not found: {file_path}", "passed": False}
    
    filename = os.path.basename(file_path)
    parent_dir = os.path.dirname(file_path)
    max_lines, max_bytes = get_budget_for_file(filename, parent_dir)
    
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    lines = content.splitlines()
    line_count = len(lines)
    byte_count = os.path.getsize(file_path)
    token_est = estimate_tokens(content)
    
    line_passed = line_count <= max_lines
    byte_passed = byte_count <= max_bytes
    passed = line_passed and byte_passed
    
    violations = []
    if not line_passed:
        violations.append(f"Line budget exceeded ({line_count} > {max_lines} lines)")
    if not byte_passed:
        violations.append(f"Byte budget exceeded ({byte_count} > {max_bytes} bytes)")
        
    return {
        "path": file_path,
        "filename": filename,
        "line_count": line_count,
        "max_lines": max_lines,
        "byte_count": byte_count,
        "max_bytes": max_bytes,
        "token_estimate": token_est,
        "passed": passed,
        "violations": violations,
    }

def check_chronological_sessions(sessions_dir: str) -> Dict[str, Any]:
    """Validates that session files in sessions_dir are chronologically named and internally ordered."""
    if not os.path.isdir(sessions_dir):
        return {"passed": True, "files": [], "issues": []}
    
    session_files = [
        f for f in os.listdir(sessions_dir)
        if f.endswith(".md") and not f.startswith(".")
    ]
    
    if not session_files:
        return {"passed": True, "files": [], "issues": []}
    
    # Pattern for timestamp filenames YYYY-MM-DD or YYYY-MM-DD-HHMM
    date_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2}(?:-\d{2,4})?)")
    
    issues = []
    parsed_files = []
    
    for f in session_files:
        match = date_pattern.match(f)
        if not match:
            issues.append(f"Non-standard session filename format: {f} (expected YYYY-MM-DD or YYYY-MM-DD-HHMM)")
        else:
            parsed_files.append((match.group(1), f))
    
    # Sort files chronologically by extracted timestamp
    sorted_parsed = sorted(parsed_files, key=lambda x: x[0])
    sorted_files = [f for _, f in sorted_parsed]
    
    # Check internal timestamps in each file
    time_stamp_regex = re.compile(r"\b(\d{4}-\d{2}-\d{2}(?:T|\s+)\d{2}:\d{2}(?::\d{2})?(?:Z)?)\b")
    for _, fname in parsed_files:
        fpath = os.path.join(sessions_dir, fname)
        if not os.path.isfile(fpath):
            continue
        with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
            content = fp.read()
        timestamps = time_stamp_regex.findall(content)
        for i in range(len(timestamps) - 1):
            if timestamps[i] > timestamps[i+1]:
                issues.append(f"Internal timestamps out of order in {fname}: {timestamps[i]} > {timestamps[i+1]}")
            
    passed = len(issues) == 0
    return {
        "passed": passed,
        "files": sorted_files,
        "issues": issues,
    }

def detect_repeated_facts(memory_files: List[str]) -> Dict[str, Any]:
    """Detects repeated bullet points / statements across memory files to suggest pointers."""
    fact_map: Dict[str, List[Tuple[str, int]]] = {}
    recommendations = []
    
    for file_path in memory_files:
        if not os.path.isfile(file_path):
            continue
        # Skip session logs and candidate inbox as they are not durable facts
        if "sessions" in file_path or "/sessions/" in file_path or "inbox" in file_path or "/inbox/" in file_path:
            continue
        filename = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
        for line_no, line in enumerate(lines, 1):
            cleaned = line.strip()
            # Ignore headers, short lines, table borders, dividers
            if len(cleaned) < 25 or cleaned.startswith("#") or cleaned.startswith("|") or cleaned.startswith("---"):
                continue
            
            # Normalize bullet points and whitespace
            normalized = re.sub(r"^[-*+]\s+", "", cleaned).strip().lower()
            if len(normalized) < 20:
                continue
            
            if normalized in fact_map:
                fact_map[normalized].append((filename, line_no))
            else:
                fact_map[normalized] = [(filename, line_no)]
                
    for fact, occurrences in fact_map.items():
        if len(occurrences) > 1:
            files_involved = list({f for f, _ in occurrences})
            if len(files_involved) > 1:
                recommendations.append({
                    "fact_preview": fact[:60] + ("..." if len(fact) > 60 else ""),
                    "occurrences": [{"file": f, "line": l} for f, l in occurrences],
                    "recommendation": f"Fact repeated across {', '.join(files_involved)}. Prefer storing in a single canonical file (e.g. DECISIONS.md or GOTCHAS.md) and referencing via markdown pointer."
                })
                
    return {
        "duplicates_count": len(recommendations),
        "recommendations": recommendations,
    }

def compact_current_md(file_path: str) -> bool:
    """Compacts CURRENT.md to keep it strictly within the 30-line budget."""
    if not os.path.isfile(file_path):
        return False
    
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    lines = content.splitlines()
    if len(lines) <= LINE_BUDGETS["CURRENT.md"]:
        return False  # Already compact
    
    # Preserve core headers and compact notes
    core_sections: Dict[str, List[str]] = {
        "header": ["# Active Working State", "Last Updated: 2026-09-01T15:45:00Z", ""],
        "objective": ["## Current Objective"],
        "status": ["## Active Status"],
        "blockers": ["## Blockers"],
        "next_steps": ["## Next Steps"],
    }
    
    current_sec = "objective"
    for line in lines:
        stripped = line.strip()
        if "## Current Objective" in stripped:
            current_sec = "objective"
        elif "## Active Status" in stripped or "## Status" in stripped:
            current_sec = "status"
        elif "## Blockers" in stripped:
            current_sec = "blockers"
        elif "## Next Steps" in stripped:
            current_sec = "next_steps"
        elif stripped and not stripped.startswith("#"):
            if current_sec in core_sections and len(core_sections[current_sec]) < 6:
                core_sections[current_sec].append(line)
                
    # Fallback content if empty
    if len(core_sections["objective"]) == 1:
        core_sections["objective"].append("Implement and validate persistent memory architecture.")
    if len(core_sections["status"]) == 1:
        core_sections["status"].append("- Memory system operating within performance constraints.")
    if len(core_sections["blockers"]) == 1:
        core_sections["blockers"].append("- None.")
    if len(core_sections["next_steps"]) == 1:
        core_sections["next_steps"].append("- Maintain strict token and line budgets.")
        
    compacted_lines = (
        core_sections["header"] +
        core_sections["objective"] + [""] +
        core_sections["status"] + [""] +
        core_sections["blockers"] + [""] +
        core_sections["next_steps"]
    )
    
    compacted_content = "\n".join(compacted_lines) + "\n"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(compacted_content)
        
    return True

def compact_markdown_file(file_path: str) -> bool:
    """Trims duplicate blank lines and trailing whitespace in markdown files."""
    if not os.path.isfile(file_path):
        return False
    
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    # Strip trailing whitespace on each line
    lines = [line.rstrip() for line in content.splitlines()]
    
    # Collapse multiple consecutive empty lines to a single empty line
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty:
                cleaned_lines.append(line)
                prev_empty = True
        else:
            cleaned_lines.append(line)
            prev_empty = False
            
    new_content = "\n".join(cleaned_lines) + "\n"
    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False

import math
import glob
import time

def calculate_entropy(text: str) -> float:
    if not text: return 0.0
    freq = {}
    for c in text:
        freq[c] = freq.get(c, 0) + 1
    ent = 0.0
    for f in freq.values():
        p = f / len(text)
        ent -= p * math.log2(p)
    return ent

def gather_telemetry(target_dir: str, memory_files: List[str], file_audits: List[Dict[str, Any]]) -> Dict[str, Any]:
    file_count = len(memory_files)
    total_bytes = sum(f.get("byte_count", 0) for f in file_audits)
    
    entropies = []
    promotions = 0
    rejections = 0
    
    for fpath in memory_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
                entropies.append(calculate_entropy(content))
                promotions += content.lower().count("promoted") + content.lower().count("promotion")
        except:
            pass
            
    log_files = glob.glob(os.path.join(target_dir, "**", "*.log"), recursive=True) + glob.glob(os.path.join(target_dir, "..", "*.log"), recursive=True)
    for lf in log_files:
        try:
            with open(lf, "r", encoding="utf-8") as f:
                content = f.read()
                rejections += content.lower().count("rejected") + content.lower().count("rejection")
        except:
            pass
            
    avg_entropy = sum(entropies)/len(entropies) if entropies else 0.0
    
    return {
        "file_count": file_count,
        "memory_footprint_bytes": total_bytes,
        "entropy_distribution": {
            "average_shannon_entropy": round(avg_entropy, 3),
            "min": round(min(entropies), 3) if entropies else 0.0,
            "max": round(max(entropies), 3) if entropies else 0.0,
        },
        "promotion_stats": {
            "estimated_promotions": promotions
        },
        "rejection_logs": {
            "estimated_rejections": rejections
        },
        "last_audit_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "remote_calls_made": 0
    }

def run_compaction(target_dir: str, enforce: bool = False) -> Dict[str, Any]:
    """Runs a full audit/compaction pass on target_dir."""
    memory_files = []
    sessions_dir = None
    
    if os.path.isfile(target_dir):
        memory_files = [target_dir]
    elif os.path.isdir(target_dir):
        for root, dirs, files in os.walk(target_dir):
            if os.path.basename(root) == "sessions":
                sessions_dir = root
            for f in files:
                if f.endswith(".md"):
                    memory_files.append(os.path.join(root, f))
    else:
        return {"error": f"Target path does not exist: {target_dir}", "passed": False}
    
    # Auto-compaction if enforce flag is set
    actions_taken = []
    if enforce:
        for fpath in memory_files:
            if os.path.basename(fpath) == "CURRENT.md":
                if compact_current_md(fpath):
                    actions_taken.append(f"Compacted CURRENT.md to fit < 30 lines budget ({fpath})")
            if compact_markdown_file(fpath):
                actions_taken.append(f"Cleaned whitespace and blank lines in {fpath}")

    # Audit all files
    file_audits = [audit_file_budgets(f) for f in sorted(memory_files)]
    all_files_passed = all(fa.get("passed", False) for fa in file_audits)
    
    # Chronological session check
    chrono_result = {"passed": True, "files": [], "issues": []}
    if sessions_dir:
        chrono_result = check_chronological_sessions(sessions_dir)
    elif os.path.isdir(os.path.join(target_dir, "sessions")):
        chrono_result = check_chronological_sessions(os.path.join(target_dir, "sessions"))
        
    # Deduplication check
    dedup_result = detect_repeated_facts(memory_files)
    
    total_lines = sum(fa.get("line_count", 0) for fa in file_audits)
    total_bytes = sum(fa.get("byte_count", 0) for fa in file_audits)
    total_tokens = sum(fa.get("token_estimate", 0) for fa in file_audits)
    
    overall_passed = all_files_passed and chrono_result.get("passed", True)
    
    telemetry = gather_telemetry(target_dir, memory_files, file_audits)
    
    return {
        "status": "PASS" if overall_passed else "FAIL",
        "passed": overall_passed,
        "target": target_dir,
        "files_audited": len(file_audits),
        "total_lines": total_lines,
        "total_bytes": total_bytes,
        "total_est_tokens": total_tokens,
        "actions_taken": actions_taken,
        "file_details": file_audits,
        "chronological_check": chrono_result,
        "deduplication_check": dedup_result,
        "telemetry": telemetry,
    }

def print_human_report(report: Dict[str, Any], verbose: bool = False):
    """Formats and prints the human-readable audit report."""
    print("=" * 70)
    print(" ANTIGRAVITY MEMORY PERFORMANCE & TOKEN OPTIMIZATION REPORT")
    print("=" * 70)
    print(f"Target Directory : {report.get('target')}")
    print(f"Overall Status   : {report.get('status')}")
    print(f"Files Audited    : {report.get('files_audited')}")
    print(f"Total Lines      : {report.get('total_lines')}")
    print(f"Total Bytes      : {report.get('total_bytes')} bytes")
    print(f"Total Tokens Est : ~{report.get('total_est_tokens')} tokens")
    print("-" * 70)
    
    print("\n[FILE BUDGET COMPLIANCE]")
    fmt = "{:<25} | {:<12} | {:<14} | {:<10} | {:<6}"
    print(fmt.format("File", "Lines/Max", "Bytes/Max", "~Tokens", "Status"))
    print("-" * 70)
    
    for f in report.get("file_details", []):
        name = f.get("filename", "unknown")
        lines_str = f"{f.get('line_count')}/{f.get('max_lines')}"
        bytes_str = f"{f.get('byte_count')}/{f.get('max_bytes')}"
        tok_str = f"~{f.get('token_estimate')}"
        status_str = "OK" if f.get("passed") else "FAIL"
        print(fmt.format(name[:25], lines_str, bytes_str, tok_str, status_str))
        if not f.get("passed"):
            for v in f.get("violations", []):
                print(f"  └─ VIOLATION: {v}")
                
    # Chronological check
    chrono = report.get("chronological_check", {})
    print("\n[CHRONOLOGICAL SESSION ORDERING]")
    if chrono.get("passed"):
        print(f"Status: PASS ({len(chrono.get('files', []))} session logs strictly chronological)")
    else:
        print("Status: FAIL")
        for iss in chrono.get("issues", []):
            print(f"  └─ ISSUE: {iss}")
            
    # Deduplication check
    dedup = report.get("deduplication_check", {})
    print("\n[FACT DEDUPLICATION & POINTER CHECK]")
    if dedup.get("duplicates_count", 0) == 0:
        print("Status: PASS (No cross-file duplicate facts detected)")
    else:
        print(f"Status: WARN ({dedup.get('duplicates_count')} duplicate facts detected across files)")
        for r in dedup.get("recommendations", []):
            print(f"  └─ Fact: '{r['fact_preview']}'")
            print(f"     Advice: {r['recommendation']}")
            
    # Telemetry
    telemetry = report.get("telemetry", {})
    if telemetry:
        print("\n[LOCAL TELEMETRY]")
        print(f"File Count: {telemetry.get('file_count')}")
        print(f"Memory Footprint: {telemetry.get('memory_footprint_bytes')} bytes")
        print(f"Entropy Avg: {telemetry.get('entropy_distribution', {}).get('average_shannon_entropy')}")
        print(f"Promotions: {telemetry.get('promotion_stats', {}).get('estimated_promotions')}")
        print(f"Rejections: {telemetry.get('rejection_logs', {}).get('estimated_rejections')}")
        print(f"Last Audit: {telemetry.get('last_audit_date')}")
        print(f"Remote Calls: {telemetry.get('remote_calls_made')}")

    if report.get("actions_taken"):
        print("\n[ACTIONS PERFORMED]")
        for act in report.get("actions_taken", []):
            print(f"  - {act}")
            
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(
        description="Antigravity Memory Performance & Compaction Auditor"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="/workspaces/codespaces-blank/.agents/memory",
        help="Path to memory directory or file (default: .agents/memory)"
    )
    parser.add_argument(
        "--check",
        "--audit",
        action="store_true",
        help="Audit mode (exits with code 1 if budgets are exceeded)"
    )
    parser.add_argument(
        "--enforce",
        "--compact",
        action="store_true",
        help="Auto-compact oversized files (e.g. CURRENT.md) and clean whitespace"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report in JSON format"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    report = run_compaction(args.target, enforce=args.enforce)
    
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_human_report(report, verbose=args.verbose)
        
    sys.exit(0 if report.get("passed", False) else 1)

if __name__ == "__main__":
    main()
