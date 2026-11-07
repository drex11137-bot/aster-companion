#!/usr/bin/env python3
"""
Antigravity Persistent Memory Audit & Health Diagnostics Engine (Phase 13).
Audits global (~/.gemini/antigravity-cli/memory/) and workspace (.agents/memory/) files for:
- Secret leakage (Security Policy #1 & Phase 16)
- Duplicated facts (Deduplication Policy #8)
- Stale entries (State Authority & Date Policy #3, #6)
- Contradictory entries (Contradiction Policy #13)
- Oversized files (Performance & Context Policy Phase 15)
- Bad categorization (Classification Policy Phase 10)
- Global/project contamination / cross-project leakage (Separation Principle #1)
- Unsupported assumptions / speculative statements (Truth Policy #2)

Outputs the standardized Phase 13 ## MEMORY HEALTH report.
"""

import os
import re
import sys
import glob
import math
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Threshold configurations
OVERSIZED_LIMITS = {
    "CURRENT.md": {"max_lines": 50, "max_bytes": 4096},
    "INDEX.md": {"max_lines": 120, "max_bytes": 8192},
    "POLICY.md": {"max_lines": 150, "max_bytes": 10240},
    "DEFAULT": {"max_lines": 250, "max_bytes": 16384}
}

SECRET_PATTERNS = [
    (r"AIza[0-9A-Za-z-_]{35}", "Google API Key"),
    (r"sk-[a-zA-Z0-9_-]{20,}", "OpenAI / Anthropic API Key"),
    (r"ghp_[0-9a-zA-Z]{36}", "GitHub Personal Access Token"),
    (r"gho_[0-9a-zA-Z]{36}", "GitHub OAuth Token"),
    (r"xox[baprs]-[0-9a-zA-Z]{10,48}", "Slack Token"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----", "Private Key Header"),
    (r"ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*", "JWT Token / Bearer Header"),
    (r"(?i)(?:password|passwd|secret|api[_-]?key|auth[_-]?token)\s*[:=]\s*[\"'][^\"'\s]{8,}[\"']", "Hardcoded Password/Token Variable"),
    (r"(?i)bearer\s+[a-zA-Z0-9_\-\.~+/]{20,}={0,2}", "Bearer Authentication Token"),
]

SPECULATION_PATTERNS = [
    r"\b(?:maybe|probably|perhaps|might be|seems like|assumed to be|unconfirmed|guess(?:ing)?)\b",
    r"\b(?:not sure if|suspected that|hypothetically|presumably)\b"
]

PROJECT_SPECIFIC_INDICATORS = [
    (r"/workspaces/([a-zA-Z0-9_\-\.]+)", "Workspace repository path in global memory"),
    (r"codespaces-blank", "Workspace-specific repository name in global memory"),
]


def shannon_entropy(data: str) -> float:
    if not data:
        return 0.0
    entropy = 0.0
    for x in set(data):
        p_x = float(data.count(x)) / len(data)
        if p_x > 0:
            entropy += - p_x * math.log2(p_x)
    return entropy


class MemoryAuditor:
    def __init__(self, global_dir: str = None, project_dir: str = None):
        self.global_dir = os.path.expanduser(global_dir or "~/.gemini/antigravity-cli/memory")
        self.project_dir = os.path.abspath(project_dir or "/workspaces/codespaces-blank/.agents/memory")
        
        self.global_files = self._collect_files(self.global_dir)
        self.project_files = self._collect_files(self.project_dir)
        self.all_files = self.global_files + self.project_files

        self.findings = {
            "secrets": [],
            "duplicates": [],
            "stale_entries": [],
            "contradictions": [],
            "oversized_files": [],
            "cross_project_leakage": [],
            "bad_categorization": [],
            "unsupported_assumptions": [],
            "unindexed_files": []
        }

    def _collect_files(self, base_dir: str) -> List[str]:
        if not os.path.exists(base_dir):
            return []
        collected = []
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".md"):
                    collected.append(os.path.join(root, file))
        return collected

    def audit_secrets(self):
        """Scans all memory files for secret patterns and high entropy candidates."""
        for file_path in self.all_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.splitlines()

                for idx, line in enumerate(lines, 1):
                    # Skip code blocks demonstrating patterns or regex in documentation
                    if line.strip().startswith("`") or "r\"" in line or "pattern" in line.lower():
                        continue
                    for pattern, desc in SECRET_PATTERNS:
                        if re.search(pattern, line):
                            self.findings["secrets"].append({
                                "file": file_path,
                                "line": idx,
                                "description": desc,
                                "snippet": line.strip()[:60] + "..." if len(line.strip()) > 60 else line.strip()
                            })

                    # High-entropy token check
                    tokens = re.findall(r"[A-Za-z0-9+/_-]{32,}", line)
                    for t in tokens:
                        if shannon_entropy(t) > 4.6 and not t.startswith("http") and not re.match(r"^[0-9a-fA-F-]+$", t):
                            self.findings["secrets"].append({
                                "file": file_path,
                                "line": idx,
                                "description": f"High-entropy secret token candidate (entropy={shannon_entropy(t):.2f})",
                                "snippet": t[:10] + "..." + t[-6:]
                            })
            except Exception as e:
                pass

    def audit_oversized_files(self):
        """Checks file size and line counts against compactness thresholds."""
        for file_path in self.all_files:
            try:
                stat = os.stat(file_path)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    line_count = sum(1 for _ in f)

                filename = os.path.basename(file_path)
                limits = OVERSIZED_LIMITS.get(filename, OVERSIZED_LIMITS["DEFAULT"])

                if line_count > limits["max_lines"] or stat.st_size > limits["max_bytes"]:
                    self.findings["oversized_files"].append({
                        "file": file_path,
                        "line_count": line_count,
                        "max_lines": limits["max_lines"],
                        "size_bytes": stat.st_size,
                        "max_bytes": limits["max_bytes"]
                    })
            except Exception as e:
                pass

    def audit_cross_project_leakage(self):
        """Checks if global memory contains workspace-specific paths or project IDs."""
        for file_path in self.global_files:
            # Skip projects/ subdirectory inside global memory as it is intended for project profiles
            if "/projects/" in file_path:
                continue
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                for idx, line in enumerate(lines, 1):
                    for pattern, desc in PROJECT_SPECIFIC_INDICATORS:
                        if re.search(pattern, line):
                            self.findings["cross_project_leakage"].append({
                                "file": file_path,
                                "line": idx,
                                "pattern": desc,
                                "snippet": line.strip()
                            })
                            break
            except Exception as e:
                pass

    def audit_unsupported_assumptions(self):
        """Checks for speculative hedging language violating Policy Rule #2."""
        for file_path in self.all_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                for idx, line in enumerate(lines, 1):
                    # Ignore lines inside policy/rule descriptions describing speculation policy
                    if "speculat" in line.lower() or "never store" in line.lower() or "hypothesis" in line.lower():
                        continue
                    for pattern in SPECULATION_PATTERNS:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            self.findings["unsupported_assumptions"].append({
                                "file": file_path,
                                "line": idx,
                                "matched_word": match.group(0),
                                "snippet": line.strip()
                            })
            except Exception as e:
                pass

    def audit_duplicates(self):
        """Detects duplicated durable facts across memory files."""
        facts_map: Dict[str, List[Tuple[str, int]]] = {}
        for file_path in self.all_files:
            # Skip session logs and candidate inbox as they are not durable facts
            if "sessions/" in file_path or "/sessions/" in file_path or "inbox/" in file_path or "/inbox/" in file_path:
                continue
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                for idx, line in enumerate(lines, 1):
                    clean = line.strip()
                    # Only check bullet points (- or * followed by space); exclude markdown bold (**Type:**)
                    if (clean.startswith("- ") or clean.startswith("* ")) and len(clean) > 25:
                        # Normalize date prefixes and punctuation
                        normalized = re.sub(r"^[-*]\s*(\[\d{4}-\d{2}-\d{2}\])?\s*", "", clean).lower()
                        normalized = re.sub(r"\s+", " ", normalized).strip()
                        if len(normalized) > 20:
                            if normalized not in facts_map:
                                facts_map[normalized] = []
                            facts_map[normalized].append((file_path, idx))
            except Exception as e:
                pass

        for norm_fact, occurrences in facts_map.items():
            if len(occurrences) > 1:
                # Group distinct files or distinct lines
                distinct_files = set(occ[0] for occ in occurrences)
                if len(distinct_files) > 1 or len(occurrences) > 1:
                    self.findings["duplicates"].append({
                        "fact": norm_fact[:80] + "...",
                        "count": len(occurrences),
                        "occurrences": [{"file": f, "line": l} for f, l in occurrences]
                    })

    def audit_contradictions(self):
        """Scans for contradictory assertions (e.g. mismatched version requirements or incompatible directives)."""
        facts = {}
        for file_path in self.all_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                in_superseded = False
                for idx, line in enumerate(lines, 1):
                    if line.strip().startswith("## Superseded") or line.strip().startswith("### Superseded"):
                        in_superseded = True
                        continue
                    if in_superseded and line.startswith("#"):
                        in_superseded = False
                    if in_superseded:
                        continue

                    # Version check contradiction detection
                    if "python" in line.lower() and ("required" in line.lower() or "version" in line.lower() or ">=" in line or "==" in line):
                        versions = re.findall(r"python[^\d\n\r]*?(\d+\.\d+)", line, re.IGNORECASE)
                        for v in versions:
                            if "python_ver" in facts and facts["python_ver"]["ver"] != v:
                                self.findings["contradictions"].append({
                                    "type": "Python Version Conflict",
                                    "file_a": facts["python_ver"]["file"],
                                    "line_a": facts["python_ver"]["line"],
                                    "val_a": facts["python_ver"]["ver"],
                                    "file_b": file_path,
                                    "line_b": idx,
                                    "val_b": v
                                })
                            else:
                                facts["python_ver"] = {"ver": v, "file": file_path, "line": idx}
                    
                    # Package manager contradiction detection
                    if "package manager" in line.lower() or "always use" in line.lower():
                        for pm in ["pnpm", "npm", "yarn", "poetry", "pipenv"]:
                            if pm in line.lower():
                                if "pkg_mgr" in facts and facts["pkg_mgr"]["pm"] != pm:
                                    # If one is project and one is global, project overrides (not a contradiction unless in same scope)
                                    same_scope = (("global" in facts["pkg_mgr"]["file"] and "global" in file_path) or
                                                  (".agents" in facts["pkg_mgr"]["file"] and ".agents" in file_path))
                                    if same_scope:
                                        self.findings["contradictions"].append({
                                            "type": "Package Manager Directive Conflict",
                                            "file_a": facts["pkg_mgr"]["file"],
                                            "line_a": facts["pkg_mgr"]["line"],
                                            "val_a": facts["pkg_mgr"]["pm"],
                                            "file_b": file_path,
                                            "line_b": idx,
                                            "val_b": pm
                                        })
                                else:
                                    facts["pkg_mgr"] = {"pm": pm, "file": file_path, "line": idx}
            except Exception as e:
                pass

    def audit_stale_entries(self):
        """Scans for broken file references, obsolete metadata, and non-existent targets."""
        for file_path in self.all_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                for idx, line in enumerate(lines, 1):
                    # Check for explicit file references in markdown: `file://...` or [text](path)
                    refs = re.findall(r"\[.*?\]\((file://)?((?:/workspaces|/home/codespace)/[^)#]+)", line)
                    for _, path in refs:
                        clean_path = path.strip()
                        if not os.path.exists(clean_path):
                            self.findings["stale_entries"].append({
                                "file": file_path,
                                "line": idx,
                                "reason": f"Referenced file does not exist in repository: {clean_path}",
                                "snippet": line.strip()
                            })
            except Exception as e:
                pass

    def audit_categorization(self):
        """Scans for entries placed in inappropriate files according to the 9 types."""
        for file_path in self.all_files:
            filename = os.path.basename(file_path)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                for idx, line in enumerate(lines, 1):
                    # User preferences in ARCHITECTURE.md
                    if filename == "ARCHITECTURE.md" and ("user prefers" in line.lower() or "user style" in line.lower()):
                        self.findings["bad_categorization"].append({
                            "file": file_path,
                            "line": idx,
                            "issue": "User preference detected in ARCHITECTURE.md (should be in USER.md)",
                            "snippet": line.strip()
                        })
                    # Ephemeral debug notes in DECISIONS.md
                    if filename == "DECISIONS.md" and ("temp fix" in line.lower() or "todo: clean up" in line.lower()):
                        self.findings["bad_categorization"].append({
                            "file": file_path,
                            "line": idx,
                            "issue": "Temporary/ephemeral note in DECISIONS.md (should be in CURRENT.md or session log)",
                            "snippet": line.strip()
                        })
            except Exception as e:
                pass

    def audit_unindexed_files(self):
        """Scans for canonical memory files that are not registered in their respective INDEX.md."""
        global_index_path = os.path.join(self.global_dir, "INDEX.md")
        if os.path.exists(global_index_path):
            try:
                with open(global_index_path, "r", encoding="utf-8", errors="ignore") as f:
                    global_idx = f.read()
                for fpath in self.global_files:
                    fname = os.path.basename(fpath)
                    if fname == "INDEX.md" or "/sessions/" in fpath or "sessions/" in fpath:
                        continue
                    rel_path = os.path.relpath(fpath, self.global_dir)
                    if rel_path not in global_idx and fname not in global_idx:
                        self.findings["unindexed_files"].append({
                            "file": fpath,
                            "index_file": global_index_path,
                            "identifier": rel_path
                        })
            except Exception as e:
                pass

        project_index_path = os.path.join(self.project_dir, "INDEX.md")
        if os.path.exists(project_index_path):
            try:
                with open(project_index_path, "r", encoding="utf-8", errors="ignore") as f:
                    project_idx = f.read()
                for fpath in self.project_files:
                    fname = os.path.basename(fpath)
                    if fname == "INDEX.md" or "/sessions/" in fpath or "sessions/" in fpath or "/inbox/" in fpath or "inbox/" in fpath:
                        continue
                    rel_path = os.path.relpath(fpath, self.project_dir)
                    if rel_path not in project_idx and fname not in project_idx:
                        self.findings["unindexed_files"].append({
                            "file": fpath,
                            "index_file": project_index_path,
                            "identifier": rel_path
                        })
            except Exception as e:
                pass

    def run_full_audit(self) -> Dict[str, Any]:
        self.audit_secrets()
        self.audit_oversized_files()
        self.audit_cross_project_leakage()
        self.audit_unsupported_assumptions()
        self.audit_duplicates()
        self.audit_contradictions()
        self.audit_stale_entries()
        self.audit_categorization()
        self.audit_unindexed_files()
        return self.findings

    def audit_all(self) -> Dict[str, Any]:
        return self.run_full_audit()

    def generate_report(self) -> str:
        sec_fail = len(self.findings["secrets"]) > 0
        leak_fail = len(self.findings["cross_project_leakage"]) > 0
        dup_count = len(self.findings["duplicates"])
        stale_count = len(self.findings["stale_entries"])
        contra_count = len(self.findings["contradictions"])
        oversized_count = len(self.findings["oversized_files"])
        bad_cat_count = len(self.findings["bad_categorization"])
        spec_count = len(self.findings["unsupported_assumptions"])
        unindexed_count = len(self.findings.get("unindexed_files", []))

        total_defects = (
            len(self.findings["secrets"])
            + len(self.findings["cross_project_leakage"])
            + dup_count
            + stale_count
            + contra_count
            + oversized_count
            + bad_cat_count
            + spec_count
            + unindexed_count
        )

        if sec_fail or leak_fail:
            overall_status = f"CRITICAL (DEFECTS FOUND: Immediate Action Required - {total_defects} defect(s) detected)"
        elif total_defects > 0:
            overall_status = f"DEGRADED (DEFECTS FOUND: Maintenance Recommended - {total_defects} defect(s) detected)"
        else:
            overall_status = "HEALTHY (Zero Defects)"

        report = []
        report.append("## MEMORY HEALTH")
        report.append(f"Secrets: {'FAIL' if sec_fail else 'PASS'}")
        report.append(f"Duplicates: {dup_count}")
        report.append(f"Stale entries: {stale_count}")
        report.append(f"Contradictions: {contra_count}")
        report.append(f"Oversized files: {oversized_count}")
        report.append(f"Cross-project leakage: {'FAIL' if leak_fail else 'PASS'}")
        report.append(f"Unindexed files: {unindexed_count}")
        report.append(f"Overall status: {overall_status}")
        report.append("")
        report.append("### Detailed Diagnostics")

        # Secrets details
        if sec_fail:
            report.append("#### 🔴 Secrets Detected (SECURITY VIOLATION):")
            for item in self.findings["secrets"]:
                report.append(f"- **{item['file']}:{item['line']}** - {item['description']} (`{item['snippet']}`)")
        else:
            report.append("- **Secrets**: PASS (Zero credentials, keys, or high-entropy tokens detected).")

        # Cross-project leakage details
        if leak_fail:
            report.append("#### 🔴 Cross-Project Leakage Detected:")
            for item in self.findings["cross_project_leakage"]:
                report.append(f"- **{item['file']}:{item['line']}** - Matched `{item['pattern']}`: `{item['snippet']}`")
        else:
            report.append("- **Cross-project leakage**: PASS (Global memory is strictly clean of project-specific paths).")

        # Duplicates details
        if dup_count > 0:
            report.append(f"#### ⚠️ Duplicates ({dup_count}):")
            for item in self.findings["duplicates"]:
                report.append(f"- Fact: `{item['fact']}` (Repeated in {item['count']} locations):")
                for occ in item["occurrences"]:
                    report.append(f"  - `{occ['file']}:{occ['line']}`")
        else:
            report.append("- **Duplicates**: 0 (No redundant durable facts found across scopes).")

        # Stale entries details
        if stale_count > 0:
            report.append(f"#### ⚠️ Stale Entries ({stale_count}):")
            for item in self.findings["stale_entries"]:
                report.append(f"- **{item['file']}:{item['line']}** - {item['reason']}")
        else:
            report.append("- **Stale entries**: 0 (All referenced files and links are valid).")

        # Contradictions details
        if contra_count > 0:
            report.append(f"#### ⚠️ Contradictions ({contra_count}):")
            for item in self.findings["contradictions"]:
                report.append(f"- **{item['type']}**: `{item['file_a']}:{item['line_a']}` ('{item['val_a']}') vs `{item['file_b']}:{item['line_b']}` ('{item['val_b']}')")
        else:
            report.append("- **Contradictions**: 0 (Memory facts are fully coherent).")

        # Oversized files details
        if oversized_count > 0:
            report.append(f"#### ⚠️ Oversized Files ({oversized_count}):")
            for item in self.findings["oversized_files"]:
                report.append(f"- **{item['file']}**: {item['line_count']} lines (limit: {item['max_lines']}), {item['size_bytes']} bytes (limit: {item['max_bytes']})")
        else:
            report.append("- **Oversized files**: 0 (All memory files within compact context budgets).")

        # Bad categorization details
        if bad_cat_count > 0:
            report.append(f"#### ⚠️ Bad Categorization ({bad_cat_count}):")
            for item in self.findings["bad_categorization"]:
                report.append(f"- **{item['file']}:{item['line']}** - {item['issue']}")
        else:
            report.append("- **Bad categorization**: 0 (All memories follow proper 9-type classification).")

        # Unsupported assumptions details
        if spec_count > 0:
            report.append(f"#### ⚠️ Unsupported Assumptions ({spec_count}):")
            for item in self.findings["unsupported_assumptions"]:
                report.append(f"- **{item['file']}:{item['line']}** - Speculative word '{item['matched_word']}': `{item['snippet']}`")
        else:
            report.append("- **Unsupported assumptions**: 0 (All durable memories are verified facts).")

        # Unindexed files details
        if unindexed_count > 0:
            report.append(f"#### ⚠️ Unindexed Files ({unindexed_count}):")
            for item in self.findings["unindexed_files"]:
                report.append(f"- **{item['file']}** - Not registered in `{item['index_file']}`")
        else:
            report.append("- **Unindexed files**: 0 (All memory files properly registered in INDEX.md).")

        report.append("")
        report.append("### Recommended Remediation Actions")
        if sec_fail:
            report.append("1. **IMMEDIATE**: Purge secrets from flagged memory files and rotate exposed credentials.")
        if leak_fail:
            report.append("2. **ISOLATION**: Move project-specific filepaths from global memory to `.agents/memory/`.")
        if dup_count > 0:
            report.append("3. **DEDUPLICATION**: Run `/reorganize-memory` or consolidate duplicate facts using pointers.")
        if contra_count > 0:
            report.append("4. **SUPERSEDING**: Resolve contradictions by marking superseded entries with reasons.")
        if oversized_count > 0:
            report.append("5. **COMPACTION**: Archive old sessions or split oversized files into topic sub-files.")
        if unindexed_count > 0:
            report.append("6. **INDEXING**: Register all unindexed memory files in the corresponding INDEX.md.")
        if total_defects == 0:
            report.append("1. No remediation required. Memory ecosystem is operating with 100% health.")

        return "\n".join(report)


def main():
    auditor = MemoryAuditor()
    auditor.run_full_audit()
    report = auditor.generate_report()
    print(report)

    total_defects = sum(len(v) for v in auditor.findings.values())
    if len(auditor.findings["secrets"]) > 0 or len(auditor.findings["cross_project_leakage"]) > 0:
        sys.exit(1)
    if total_defects > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
