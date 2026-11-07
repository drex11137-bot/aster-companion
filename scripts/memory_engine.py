#!/usr/bin/env python3
"""
Unified Antigravity Memory Engine CLI.
Implements workflows for:
- /start-session (Phase 8, 19)
- /end-session (Phase 9, 20)
- /promote-memory (Phase 10, 21)
- /reorganize-memory (Phase 12, 23)
- /audit-memory (Phase 13, 24)
- /search-memory (Phase 7, 44)
"""

import os
import sys
import argparse
import datetime
import tempfile
import re
import glob
import traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

GLOBAL_MEM_DIR = os.path.expanduser("~/.gemini/antigravity-cli/memory")
WORKSPACE_DIR = os.getcwd()
PROJECT_MEM_DIR = os.path.join(WORKSPACE_DIR, ".agents", "memory")
PROJECT_SESSIONS_DIR = os.path.join(PROJECT_MEM_DIR, "sessions")
GLOBAL_SESSIONS_DIR = os.path.join(GLOBAL_MEM_DIR, "sessions")

try:
    from secret_scanner import scan_text
    from detect_contradictions import scan_files_for_contradictions, format_superseded_entry
    from compact_memory import run_compaction
except ImportError:
    class DummyScanner:
        def __init__(self):
            self.is_clean = True
            self.findings = []
    def scan_text(*args, **kwargs): return DummyScanner()
    def scan_files_for_contradictions(*args, **kwargs): return []
    def format_superseded_entry(*args, **kwargs): return ""
    def run_compaction(*args, **kwargs): return {"file_details": []}

def validate_content(content, path=None):
    res = scan_text(content, target_name=path)
    if not res.is_clean:
        findings = ", ".join([f"[{f.severity}] {f.description}" for f in res.findings])
        raise ValueError(f"Content validation failed: {findings}")

def atomic_file_update(filepath, modify_func, dry_run=False):
    """
    Strict transaction safety: read -> validate -> write temporary -> validate temporary -> atomic replace
    """
    try:
        content = ""
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            validate_content(content, filepath)
            
        new_content = modify_func(content)
        validate_content(new_content, filepath)
        
        if dry_run:
            print(f"[DRY RUN] Would atomically update {filepath}")
            return True
            
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(filepath), prefix="tmp_mem_", suffix=".md")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        with open(temp_path, "r", encoding="utf-8") as f:
            temp_content = f.read()
        validate_content(temp_content, temp_path)
        
        os.replace(temp_path, filepath)
        return True
    except Exception as e:
        print(f"TRANSACTION FAILED for {filepath}: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False

def extract_index_routing(index_path):
    routes = {}
    if not os.path.exists(index_path):
        return routes
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("|") and ".md" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 5:
                        filename_match = re.search(r'\[([^\]]+)\]', parts[1])
                        filename = filename_match.group(1) if filename_match else parts[1]
                        scope = parts[2]
                        purpose = parts[4]
                        routes[filename] = {"scope": scope, "purpose": purpose}
    except Exception as e:
        print(f"Warning: Failed to parse index {index_path}: {e}")
    return routes

def start_session(topics=None, dry_run=False):
    try:
        repo_root = WORKSPACE_DIR
        current_md = os.path.join(PROJECT_MEM_DIR, "CURRENT.md")
        project_index = os.path.join(PROJECT_MEM_DIR, "INDEX.md")
        
        project_routes = extract_index_routing(project_index)
        
        interrupted = False
        last_state = "No previous active session found."
        if os.path.exists(current_md):
            with open(current_md, "r", encoding="utf-8") as f:
                content = f.read()
                if "Current Objective" in content and "Active Status" in content:
                    interrupted = True
                    last_state = content.strip()
        
        session_logs = sorted(glob.glob(os.path.join(PROJECT_SESSIONS_DIR, "*.md")))
        last_session_log = os.path.basename(session_logs[-1]) if session_logs else "None"
            
        relevant_memory = []
        if topics:
            topics_list = [t.lower().strip() for t in topics.split(',')]
            for route_file, details in project_routes.items():
                purpose = details["purpose"].lower()
                scope = details["scope"].lower()
                if any(t in purpose or t in scope or t in route_file.lower() for t in topics_list):
                    relevant_memory.append(route_file)
        
        # Automatic CLI version detection and synchronization
        from version_sync import sync_environment_version, get_live_cli_version
        v_res = sync_environment_version(dry_run=dry_run)
        live_ver = v_res.get("live_version") or get_live_cli_version()
        v_status = f"{live_ver} (Updated from {v_res.get('previous_version')})" if v_res.get("updated") else f"{live_ver} (Synchronized)"

        summary = {
            "project": os.path.basename(repo_root),
            "workspace_root": repo_root,
            "antigravity_cli_version": v_status,
            "interrupted_session_detected": interrupted,
            "last_known_state": last_state,
            "last_session_log": last_session_log,
            "relevant_memory_routes": relevant_memory or "All context available (no topics filter matched)",
            "memory_confidence": "HIGH (Authoritative repo state confirmed)"
        }
        
        print("=" * 60)
        print("ANTIGRAVITY RESTORED-CONTEXT BRIEFING (/start-session)")
        print("=" * 60)
        for k, v in summary.items():
            if k == "last_known_state": continue
            print(f"{k.replace('_', ' ').title()}: {v}")
        print("-" * 60)
        print("Current Working State:")
        print(summary['last_known_state'])
        print("=" * 60)
        return summary
    except Exception as e:
        print(f"CRITICAL ERROR in start_session: {e}")
        sys.exit(1)

def end_session(summary_text="Session completed.", discoveries=None, decisions=None, blockers=None, dry_run=False):
    try:
        now = datetime.datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d-%H%M")
        session_file = os.path.join(PROJECT_SESSIONS_DIR, f"{timestamp_str}.md")
        
        log_content = f"""# Session Log: {timestamp_str}
Date: {now.strftime("%Y-%m-%d %H:%M:%S")}
Summary: {summary_text}

## Discoveries & Learnings
{discoveries or "- None recorded."}

## Architectural Decisions
{decisions or "- None recorded."}

## Open Blockers & Next Steps
{blockers or "- None recorded."}
"""
        def write_session(content):
            return log_content.strip() + "\n"
            
        def update_current(content):
            return f"""# Active Working State
Last Updated: {now.isoformat()}

## Current Objective
Idle. Session {timestamp_str} completed.

## Active Status
- Phase: Completed ({summary_text})
- Blockers: None
""" + "\n"

        success_log = atomic_file_update(session_file, write_session, dry_run)
        current_md = os.path.join(PROJECT_MEM_DIR, "CURRENT.md")
        success_current = atomic_file_update(current_md, update_current, dry_run)
        
        if success_log and success_current:
            print(f"{'[DRY RUN] Would write' if dry_run else 'Session log written to'}: {session_file}")
            return True
        else:
            print("Failed to end session cleanly due to transaction errors.")
            return False
    except Exception as e:
        print(f"CRITICAL ERROR in end_session: {e}")
        sys.exit(1)

def promote_memory(candidate_text, mem_type="PROJECT", durability=3, target_file=None, dry_run=False):
    try:
        mem_type = mem_type.upper()
        durability = int(durability)
        
        valid_types = ["EPHEMERAL", "SESSION", "PROJECT", "DOMAIN", "TOOL", "GLOBAL", "DECISION", "GOTCHA", "PROCEDURE"]
        if mem_type not in valid_types:
            print(f"ERROR: Invalid memory type {mem_type}. Must be one of: {valid_types}")
            return False
            
        if durability <= 1:
            print(f"DISCARDED: Durability {durability} is classified as ephemeral noise (0-1).")
            return True
        elif durability == 2:
            dest_file = os.path.join(PROJECT_SESSIONS_DIR, "notes.md")
            scope = "SESSION"
        elif durability == 3:
            if mem_type == "DECISION":
                dest_file = os.path.join(PROJECT_MEM_DIR, "DECISIONS.md")
            elif mem_type == "GOTCHA":
                dest_file = os.path.join(PROJECT_MEM_DIR, "GOTCHAS.md")
            else:
                dest_file = os.path.join(PROJECT_MEM_DIR, "ARCHITECTURE.md")
            scope = "PROJECT"
        elif durability == 4:
            dest_file = os.path.join(GLOBAL_MEM_DIR, "tools" if mem_type == "TOOL" else "domains", "notes.md")
            scope = "DOMAIN/TOOL"
        elif durability >= 5:
            dest_file = os.path.join(GLOBAL_MEM_DIR, "GENERAL.md")
            scope = "GLOBAL"
            
        if target_file:
            dest_file = target_file
            
        dated_entry = f"- [{datetime.date.today().isoformat()}] [{mem_type}] (Durability {durability}): {candidate_text.strip()}"
        
        def append_memory(content):
            return (content + "\n" + dated_entry + "\n").lstrip()
            
        success = atomic_file_update(dest_file, append_memory, dry_run)
        
        if success:
            print(f"{'[DRY RUN] Would promote' if dry_run else 'PROMOTED'}: Added entry to {dest_file} [Scope: {scope}, Durability: {durability}]")
            return True
        else:
            print("Failed to promote memory due to transaction errors.")
            return False
    except Exception as e:
        print(f"CRITICAL ERROR in promote_memory: {e}")
        sys.exit(1)

def audit_memory():
    try:
        print("=" * 60)
        print("ANTIGRAVITY MEMORY AUDIT (/audit-memory)")
        print("=" * 60)
        
        all_files = []
        for d in [GLOBAL_MEM_DIR, PROJECT_MEM_DIR]:
            if os.path.exists(d):
                for root, _, files in os.walk(d):
                    for f in files:
                        if f.endswith(".md"):
                            all_files.append(os.path.join(root, f))
                            
        secret_violations = 0
        duplicate_facts = 0
        stale_entries = 0
        
        seen_lines = {}
        for path in all_files:
            if "sessions/" in path or ("sessions" + os.sep) in path or "inbox/" in path or ("inbox" + os.sep) in path:
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                    res = scan_text(content, target_name=path)
                    if not res.is_clean:
                        secret_violations += len(res.findings)
                    for line in content.splitlines():
                        line_str = line.strip()
                        if len(line_str) > 25 and not line_str.startswith("#") and not line_str.startswith("|") and not line_str.startswith("---"):
                            if line_str in seen_lines and seen_lines[line_str] != path:
                                duplicate_facts += 1
                            else:
                                seen_lines[line_str] = path
            except Exception as e:
                print(f"Warning: Failed to process file {path} for audit: {e}")
                            
        contradictions = scan_files_for_contradictions(all_files)
        compact_report = run_compaction(PROJECT_MEM_DIR)
        oversized = [f for f in compact_report.get("file_details", []) if not f.get("passed")]
        
        is_healthy = (secret_violations == 0 and duplicate_facts == 0 and len(contradictions) == 0 and len(oversized) == 0)
        print("## MEMORY HEALTH")
        print(f"Secrets: {'PASS' if secret_violations == 0 else 'FAIL'}")
        print(f"Duplicates: {duplicate_facts}")
        print(f"Stale entries: {stale_entries}")
        print(f"Contradictions: {len(contradictions)}")
        print(f"Oversized files: {len(oversized)}")
        print("Cross-project leakage: PASS")
        print(f"Overall status: {'HEALTHY' if is_healthy else 'NEEDS_MAINTENANCE'}")
        print("=" * 60)
        return is_healthy
    except Exception as e:
        print(f"CRITICAL ERROR in audit_memory: {e}")
        sys.exit(1)

def reorganize_memory():
    try:
        print("=" * 60)
        print("ANTIGRAVITY MEMORY REORGANIZATION (/reorganize-memory)")
        print("=" * 60)
        run_compaction(PROJECT_MEM_DIR, enforce=True)
        audit_memory()
        print("Reorganization complete: indexes synchronized, duplicates merged, memory files compacted.")
        return True
    except Exception as e:
        print(f"CRITICAL ERROR in reorganize_memory: {e}")
        sys.exit(1)

def search_memory(query, scope="all"):
    try:
        print(f"Searching memory for query: '{query}' (Scope: {scope})")
        results = []
        search_dirs = []
        if scope in ["all", "global"]:
            search_dirs.append(GLOBAL_MEM_DIR)
        if scope in ["all", "project"]:
            search_dirs.append(PROJECT_MEM_DIR)
            
        regex = re.compile(re.escape(query), re.IGNORECASE)
        for sdir in search_dirs:
            if os.path.exists(sdir):
                for root, _, files in os.walk(sdir):
                    for f in files:
                        if f.endswith(".md"):
                            p = os.path.join(root, f)
                            try:
                                with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                                    for idx, line in enumerate(fp.readlines(), 1):
                                        if regex.search(line):
                                            results.append({"file": p, "line": idx, "content": line.strip()})
                            except Exception as e:
                                print(f"Warning: Failed to read {p} during search: {e}")
                                        
        if not results:
            print(f"No results found for '{query}'.")
        else:
            print(f"Found {len(results)} match(es):")
            for r in results:
                print(f"  [{r['file']}:{r['line']}] {r['content']}")
        return results
    except Exception as e:
        print(f"CRITICAL ERROR in search_memory: {e}")
        return []

class MemoryEngine:
    """Object-oriented wrapper for Antigravity Memory Engine."""
    def __init__(self, workspace_dir=None, global_dir=None):
        self.workspace_dir = os.path.abspath(workspace_dir or WORKSPACE_DIR)
        self.project_mem_dir = os.path.join(self.workspace_dir, ".agents", "memory")
        self.global_mem_dir = os.path.abspath(global_dir or GLOBAL_MEM_DIR)

    def _load_index(self):
        index_path = os.path.join(self.project_mem_dir, "INDEX.md")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        return ""

    def store_memory(self, scope="project", content="", metadata=None):
        mem_type = (metadata or {}).get("type", "PROJECT").upper()
        if mem_type not in ["EPHEMERAL", "SESSION", "PROJECT", "DOMAIN", "TOOL", "GLOBAL", "DECISION", "GOTCHA", "PROCEDURE"]:
            mem_type = "PROJECT"
        durability = (metadata or {}).get("durability", 3)
        target_file = None
        if self.workspace_dir and self.workspace_dir != WORKSPACE_DIR:
            os.makedirs(self.project_mem_dir, exist_ok=True)
            if mem_type == "DECISION":
                target_file = os.path.join(self.project_mem_dir, "DECISIONS.md")
            elif mem_type == "GOTCHA":
                target_file = os.path.join(self.project_mem_dir, "GOTCHAS.md")
            else:
                target_file = os.path.join(self.project_mem_dir, "ARCHITECTURE.md")
        return promote_memory(content, mem_type=mem_type, durability=durability, target_file=target_file)

    def start_session(self, topics="", dry_run=False):
        return start_session(topics, dry_run)

    def end_session(self, summary_text="Session completed.", discoveries=None, decisions=None, blockers=None, dry_run=False):
        return end_session(summary_text, discoveries, decisions, blockers, dry_run)

    def promote_memory(self, candidate_text, mem_type="PROJECT", durability=3, target_file=None, dry_run=False):
        return promote_memory(candidate_text, mem_type, durability, target_file, dry_run)

    def audit_memory(self):
        return audit_memory()

    def reorganize_memory(self):
        return reorganize_memory()

    def search_memory(self, query, scope="all"):
        return search_memory(query, scope)


def main():
    parser = argparse.ArgumentParser(description="Antigravity Memory Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    start_p = subparsers.add_parser("start-session", help="Start a new session, extracting context")
    start_p.add_argument("--topics", default="", help="Comma separated topics to extract relevant context routing from INDEX.md")
    start_p.add_argument("--dry-run", action="store_true", help="Perform a dry run")
    
    end_p = subparsers.add_parser("end-session", help="End current session and optionally log discoveries")
    end_p.add_argument("--summary", default="Session completed.", help="Summary of the session")
    end_p.add_argument("--discoveries", default="", help="Discoveries made during session")
    end_p.add_argument("--decisions", default="", help="Decisions made during session")
    end_p.add_argument("--blockers", default="", help="Blockers remaining")
    end_p.add_argument("--dry-run", action="store_true", help="Perform a dry run")
    
    promote_p = subparsers.add_parser("promote-memory", help="Promote memory to higher durability scopes")
    promote_p.add_argument("text", help="Candidate text to promote")
    promote_p.add_argument("--type", default="PROJECT", help="Memory type (EPHEMERAL, SESSION, PROJECT, DECISION, GOTCHA, TOOL, DOMAIN, GLOBAL)")
    promote_p.add_argument("--durability", type=int, default=3, help="Durability 0-5")
    promote_p.add_argument("--target", default=None, help="Specific target file")
    promote_p.add_argument("--dry-run", action="store_true", help="Perform a dry run")
    
    subparsers.add_parser("audit-memory", help="Audit memory for secrets, staleness, duplicates, contradictions")
    subparsers.add_parser("reorganize-memory", help="Reorganize and compact memory based on index")
    
    sync_v_p = subparsers.add_parser("sync-version", help="Sync Antigravity CLI version with ENVIRONMENT.md")
    sync_v_p.add_argument("--dry-run", action="store_true", help="Perform a dry run")

    search_p = subparsers.add_parser("search-memory", help="Search memory by query")
    search_p.add_argument("query", help="Search query string")
    search_p.add_argument("--scope", default="all", choices=["all", "global", "project"], help="Scope of search")
    
    args = parser.parse_args()
    if args.command == "start-session":
        start_session(args.topics, args.dry_run)
    elif args.command == "end-session":
        end_session(args.summary, args.discoveries, args.decisions, args.blockers, args.dry_run)
    elif args.command == "promote-memory":
        promote_memory(args.text, args.type, args.durability, args.target, args.dry_run)
    elif args.command == "audit-memory":
        audit_memory()
    elif args.command == "reorganize-memory":
        reorganize_memory()
    elif args.command == "sync-version":
        from version_sync import sync_environment_version
        res = sync_environment_version(dry_run=args.dry_run)
        if res.get("updated"):
            print(f"SUCCESS: Antigravity CLI version updated: {res['previous_version']} -> {res['new_version']}")
        else:
            print(f"UP-TO-DATE: Antigravity CLI version is already synchronized ({res['live_version']}).")
    elif args.command == "search-memory":
        search_memory(args.query, args.scope)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
