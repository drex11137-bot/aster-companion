#!/usr/bin/env python3
"""
search_memory.py - Hybrid Semantic, Keyword, and Regex Scoped Memory Search Engine.
Part of the Antigravity Persistent Memory System (Phase 7 & Phase 2 P1-1).

Features:
- Dense semantic retrieval using MemSearchBackend (local ONNX/BGE-M3 vector substrate)
- True Reciprocal Rank Fusion (RRF) combining dense semantic matches and lexical BM25/keyword matches:
  RRF_score = (w_dense / (60 + rank_dense)) + (w_lexical / (60 + rank_lexical))
- Deep scope filtering (--scope=all, global, project, decisions, gotchas, architecture, sessions, tools, domains, user, general, policy)
- Multi-signal evidence reranking integration (freshness, source tier authority, epistemic confidence)
- Markdown section-aware snippet extraction with line numbers and file link formatting
- Code-fence breakout prevention (SEC-005) wrapping snippet code blocks in quad backticks (````markdown)
- Configurable --hybrid flag (default: true; --no-hybrid for lexical-only mode)
- JSON and human-readable Markdown report output modes
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import uuid

try:
    from memory_feedback import FeedbackLedger, FeedbackOutcome
except ImportError:
    FeedbackLedger = None
    FeedbackOutcome = None

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

try:
    from memsearch_backend import MemSearchBackend
except ImportError:
    MemSearchBackend = None

try:
    from evidence_reranker import EvidenceReranker, SourceTier, TrustVerdict
except ImportError:
    EvidenceReranker = None
    SourceTier = None
    TrustVerdict = None

DEFAULT_GLOBAL_MEM_DIR = os.path.expanduser("~/.gemini/antigravity-cli/memory")
DEFAULT_PROJECT_MEM_DIR = "/workspaces/codespaces-blank/.agents/memory"
DEFAULT_RULES_DIR = "/workspaces/codespaces-blank/.agents/rules"

SCOPE_MAPPING = {
    "all": ["*"],
    "global": [
        os.path.join(DEFAULT_GLOBAL_MEM_DIR, "**/*"),
        DEFAULT_GLOBAL_MEM_DIR
    ],
    "project": [
        os.path.join(DEFAULT_PROJECT_MEM_DIR, "**/*"),
        DEFAULT_PROJECT_MEM_DIR
    ],
    "decisions": [
        os.path.join(DEFAULT_PROJECT_MEM_DIR, "DECISIONS.md"),
        os.path.join(DEFAULT_GLOBAL_MEM_DIR, "projects", "**/*")
    ],
    "gotchas": [
        os.path.join(DEFAULT_PROJECT_MEM_DIR, "GOTCHAS.md"),
        os.path.join(DEFAULT_GLOBAL_MEM_DIR, "tools", "**/*")
    ],
    "architecture": [
        os.path.join(DEFAULT_PROJECT_MEM_DIR, "ARCHITECTURE.md")
    ],
    "current": [
        os.path.join(DEFAULT_PROJECT_MEM_DIR, "CURRENT.md")
    ],
    "sessions": [
        os.path.join(DEFAULT_PROJECT_MEM_DIR, "sessions", "**/*"),
        os.path.join(DEFAULT_GLOBAL_MEM_DIR, "sessions", "**/*")
    ],
    "tools": [
        os.path.join(DEFAULT_GLOBAL_MEM_DIR, "tools", "**/*")
    ],
    "domains": [
        os.path.join(DEFAULT_GLOBAL_MEM_DIR, "domains", "**/*")
    ],
    "user": [
        os.path.join(DEFAULT_GLOBAL_MEM_DIR, "USER.md")
    ],
    "general": [
        os.path.join(DEFAULT_GLOBAL_MEM_DIR, "GENERAL.md")
    ],
    "environment": [
        os.path.join(DEFAULT_GLOBAL_MEM_DIR, "ENVIRONMENT.md")
    ],
    "policy": [
        os.path.join(DEFAULT_GLOBAL_MEM_DIR, "POLICY.md"),
        os.path.join(DEFAULT_RULES_DIR, "memory.md")
    ]
}

STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "without",
    "is", "are", "was", "were", "does", "do", "how", "what", "where", "when",
    "why", "from", "and", "or", "so", "it", "by", "as", "this", "that"
}


def str2bool(v: Any) -> bool:
    """Parses boolean strings from CLI flags."""
    if isinstance(v, bool):
        return v
    if str(v).lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif str(v).lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected (true/false).")


def discover_memory_files(scopes: List[str], project_root: str = "/workspaces/codespaces-blank") -> List[Tuple[str, str]]:
    """
    Discovers all candidate memory files matching the requested scopes.
    Returns list of tuples (file_path, identified_scope).
    """
    global_dir = os.path.expanduser("~/.gemini/antigravity-cli/memory")
    project_mem_dir = os.path.join(project_root, ".agents", "memory")
    rules_dir = os.path.join(project_root, ".agents", "rules")

    candidate_files = set()
    normalized_scopes = [s.strip().lower() for s in scopes if s.strip()]
    if not normalized_scopes or "all" in normalized_scopes:
        search_all = True
    else:
        search_all = False

    def scan_dir(dir_path: str, default_scope: str):
        if not os.path.exists(dir_path):
            return
        for root, _, files in os.walk(dir_path):
            for file in sorted(files):
                if file.endswith(".md") or file.endswith(".txt"):
                    full_path = os.path.abspath(os.path.join(root, file))
                    candidate_files.add((full_path, default_scope))

    if search_all:
        scan_dir(global_dir, "global")
        scan_dir(project_mem_dir, "project")
        scan_dir(rules_dir, "policy")
    else:
        for scope in normalized_scopes:
            if scope == "global":
                scan_dir(global_dir, "global")
            elif scope == "project":
                scan_dir(project_mem_dir, "project")
            elif scope == "decisions":
                f = os.path.join(project_mem_dir, "DECISIONS.md")
                if os.path.exists(f):
                    candidate_files.add((f, "decisions"))
            elif scope == "gotchas":
                f = os.path.join(project_mem_dir, "GOTCHAS.md")
                if os.path.exists(f):
                    candidate_files.add((f, "gotchas"))
                scan_dir(os.path.join(global_dir, "tools"), "gotchas")
            elif scope == "architecture":
                f = os.path.join(project_mem_dir, "ARCHITECTURE.md")
                if os.path.exists(f):
                    candidate_files.add((f, "architecture"))
            elif scope == "current":
                f = os.path.join(project_mem_dir, "CURRENT.md")
                if os.path.exists(f):
                    candidate_files.add((f, "current"))
            elif scope == "sessions":
                scan_dir(os.path.join(project_mem_dir, "sessions"), "sessions")
                scan_dir(os.path.join(global_dir, "sessions"), "sessions")
            elif scope == "tools":
                scan_dir(os.path.join(global_dir, "tools"), "tools")
            elif scope == "domains":
                scan_dir(os.path.join(global_dir, "domains"), "domains")
            elif scope == "user":
                f = os.path.join(global_dir, "USER.md")
                if os.path.exists(f):
                    candidate_files.add((f, "user"))
            elif scope == "general":
                f = os.path.join(global_dir, "GENERAL.md")
                if os.path.exists(f):
                    candidate_files.add((f, "general"))
            elif scope == "environment":
                f = os.path.join(global_dir, "ENVIRONMENT.md")
                if os.path.exists(f):
                    candidate_files.add((f, "environment"))
            elif scope == "policy":
                f1 = os.path.join(global_dir, "POLICY.md")
                f2 = os.path.join(rules_dir, "memory.md")
                if os.path.exists(f1):
                    candidate_files.add((f1, "policy"))
                if os.path.exists(f2):
                    candidate_files.add((f2, "policy"))

    return sorted(list(candidate_files))


def get_file_sections(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses a markdown file into discrete sections based on headings (# or ##).
    Returns list of section dicts with heading, start_line, end_line, and content.
    """
    if not os.path.isfile(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return []

    if not lines:
        return []

    headings = []
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            headings.append((idx, stripped, level))

    if not headings:
        return [{
            "heading": os.path.basename(file_path),
            "start_line": 1,
            "end_line": len(lines),
            "content": "".join(lines).strip()
        }]

    has_h2 = any(h[2] == 2 for h in headings)
    has_h1 = any(h[2] == 1 for h in headings)

    if has_h2:
        target_headings = [h for h in headings if h[2] <= 2]
    elif has_h1:
        target_headings = [h for h in headings if h[2] == 1]
    else:
        target_headings = headings

    sections = []
    if target_headings[0][0] > 1:
        preamble_lines = lines[:target_headings[0][0] - 1]
        preamble_text = "".join(preamble_lines).strip()
        if preamble_text:
            sections.append({
                "heading": f"{os.path.basename(file_path)} Preamble",
                "start_line": 1,
                "end_line": target_headings[0][0] - 1,
                "content": preamble_text
            })

    for i, (ln, heading_text, _) in enumerate(target_headings):
        start_ln = ln
        if i + 1 < len(target_headings):
            end_ln = target_headings[i + 1][0] - 1
        else:
            end_ln = len(lines)

        sec_lines = lines[start_ln - 1 : end_ln]
        sections.append({
            "heading": heading_text,
            "start_line": start_ln,
            "end_line": end_ln,
            "content": "".join(sec_lines).strip()
        })

    return sections


def find_enclosing_section(
    file_path: str,
    line_num: int,
    sections_cache: Optional[Dict[str, List[Dict[str, Any]]]] = None
) -> Dict[str, Any]:
    """
    Finds the markdown section containing line_num in file_path.
    """
    if sections_cache is not None and file_path in sections_cache:
        sections = sections_cache[file_path]
    else:
        sections = get_file_sections(file_path)
        if sections_cache is not None:
            sections_cache[file_path] = sections

    for sec in sections:
        if sec["start_line"] <= line_num <= sec["end_line"]:
            return sec

    if sections:
        return min(sections, key=lambda s: abs(s["start_line"] - line_num))

    return {
        "heading": os.path.basename(file_path),
        "start_line": max(1, line_num - 2),
        "end_line": line_num + 2,
        "content": ""
    }


def extract_section_snippets(
    file_path: str,
    query: str,
    is_regex: bool = False,
    case_sensitive: bool = False,
    scope: str = "general"
) -> List[Dict[str, Any]]:
    """
    Reads a markdown file, searches for lexical matches with word boundary enforcement
    and stop word filtering, calculates relevance score, and extracts context snippets.
    """
    if not os.path.isfile(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return []

    if not lines:
        return []

    flags = 0 if case_sensitive else re.IGNORECASE

    # Prepare regex pattern or token list
    if is_regex:
        try:
            pattern = re.compile(query, flags)
            tokens = [query]
        except re.error as err:
            return [{"error": f"Invalid regex pattern: {err}"}]
    else:
        clean_q = query.strip()
        raw_tokens = [t for t in re.split(r"\s+", clean_q) if t]
        if not raw_tokens:
            return []

        # Filter punctuation from tokens
        cleaned_tokens = [re.sub(r"^[^\w]+|[^\w]+$", "", t) for t in raw_tokens]
        cleaned_tokens = [t for t in cleaned_tokens if t]
        if not cleaned_tokens:
            cleaned_tokens = raw_tokens

        # Stop word filtering: keep non-stop words if available
        non_stop_tokens = [t for t in cleaned_tokens if t.lower() not in STOP_WORDS]
        tokens = non_stop_tokens if non_stop_tokens else cleaned_tokens

        # Pattern for exact phrase
        phrase_regex = re.compile(re.escape(clean_q), flags)

        # Word boundary token regexes
        token_regexes = []
        for t in tokens:
            if re.match(r"^\w+$", t):
                token_regexes.append(re.compile(r"\b" + re.escape(t) + r"\b", flags))
            else:
                token_regexes.append(re.compile(re.escape(t), flags))

    current_heading = "Top-level"
    current_meta_lines = []

    # Map line numbers to headings and match lines
    line_matches = []
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            current_heading = stripped
            current_meta_lines = []
            for probe_idx in range(idx, min(len(lines), idx + 6)):
                probe_line = lines[probe_idx].strip()
                if probe_line.startswith("#"):
                    break
                if any(k in probe_line for k in ("**Type:**", "**Status:**", "**Source:**", "**Confidence:**", "<!-- bitemporal", "[SUPERSEDED", "Status:", "Confidence:", "Source:")):
                    current_meta_lines.append(probe_line)

        line_score = 0
        has_match = False

        if is_regex:
            m = pattern.search(line)
            if m:
                has_match = True
                line_score += 10
        else:
            if phrase_regex.search(line):
                has_match = True
                line_score += 25  # Exact full phrase match bonus
            else:
                hit_count = 0
                for t_re in token_regexes:
                    if t_re.search(line):
                        hit_count += 1
                if hit_count > 0:
                    has_match = True
                    line_score += (hit_count * 10)
                    if hit_count == len(tokens) and len(tokens) > 1:
                        line_score += 15  # All tokens present bonus

        # Check if heading itself matched
        if has_match and stripped.startswith("#"):
            line_score += 20

        if has_match:
            line_matches.append({
                "line_num": idx,
                "line_content": line.rstrip("\r\n"),
                "heading": current_heading,
                "section_meta": list(current_meta_lines),
                "score": line_score
            })

    if not line_matches:
        return []

    # Group close lines into coherent snippets
    grouped_snippets = []
    curr_group = [line_matches[0]]

    for lm in line_matches[1:]:
        prev = curr_group[-1]
        if lm["line_num"] - prev["line_num"] <= 3:
            curr_group.append(lm)
        else:
            grouped_snippets.append(curr_group)
            curr_group = [lm]
    if curr_group:
        grouped_snippets.append(curr_group)

    results = []
    for grp in grouped_snippets:
        start_ln = max(1, grp[0]["line_num"] - 1)
        end_ln = min(len(lines), grp[-1]["line_num"] + 1)
        snippet_lines = lines[start_ln - 1 : end_ln]
        total_score = sum(item["score"] for item in grp)
        formatted_snippet = "".join(snippet_lines).strip()

        results.append({
            "file": file_path,
            "filename": os.path.basename(file_path),
            "scope": scope,
            "heading": grp[0]["heading"],
            "section_meta": grp[0].get("section_meta", []),
            "start_line": start_ln,
            "end_line": end_ln,
            "match_lines": [item["line_num"] for item in grp],
            "score": total_score,
            "snippet": formatted_snippet
        })

    return results


def run_dense_search(
    query: str,
    files_with_scopes: List[Tuple[str, str]],
    top_k: int = 20,
    sections_cache: Optional[Dict[str, List[Dict[str, Any]]]] = None
) -> List[Dict[str, Any]]:
    """
    Executes dense semantic retrieval via MemSearchBackend and resolves matches
    to bounded section items within the candidate scopes.
    """
    if MemSearchBackend is None:
        return []

    try:
        backend = MemSearchBackend()
        # Fast path optimization: verify that at least one requested candidate file is actually indexed
        indexed_files = backend.manifest.get("indexed_files", {})
        if files_with_scopes and indexed_files:
            target_paths = set()
            for p, _ in files_with_scopes:
                target_paths.add(p)
                try:
                    target_paths.add(os.path.realpath(p))
                except Exception:
                    pass
            indexed_set = set(indexed_files.keys())
            try:
                indexed_real_set = {os.path.realpath(k) for k in indexed_files.keys() if os.path.exists(k)}
            except Exception:
                indexed_real_set = set()
            if not (target_paths & indexed_set or target_paths & indexed_real_set):
                return []

        chunks = backend.search(query=query, top_k=max(20, top_k * 3))
    except Exception:
        return []

    if not chunks:
        return []

    # Build scope lookup for path resolution
    scope_lookup = {}
    for p, sc in files_with_scopes:
        scope_lookup[p] = sc
        try:
            scope_lookup[os.path.realpath(p)] = sc
        except Exception:
            pass

    items_by_id: Dict[str, Dict[str, Any]] = {}

    for chunk in chunks:
        source_path = chunk.get("source") or chunk.get("file_path")
        if not source_path:
            continue

        real_source = os.path.realpath(source_path) if os.path.exists(source_path) else source_path
        assigned_scope = scope_lookup.get(source_path) or scope_lookup.get(real_source)
        if not assigned_scope:
            # Out of requested scope boundaries
            continue

        chunk_start = chunk.get("start_line", 1)
        sec = find_enclosing_section(source_path, chunk_start, sections_cache)
        item_id = f"{source_path}::{sec['start_line']}"
        raw_dense_score = float(chunk.get("score", 0.0))

        # Extract metadata from section content
        section_meta = []
        for line in sec["content"].splitlines()[:6]:
            stripped = line.strip()
            if any(k in stripped for k in ("**Type:**", "**Status:**", "**Source:**", "**Confidence:**", "[SUPERSEDED", "Status:", "Confidence:", "Source:")):
                section_meta.append(stripped)

        if item_id not in items_by_id or raw_dense_score > items_by_id[item_id]["score"]:
            items_by_id[item_id] = {
                "id": item_id,
                "file": source_path,
                "filename": os.path.basename(source_path),
                "scope": assigned_scope,
                "heading": sec["heading"],
                "section_meta": section_meta,
                "start_line": sec["start_line"],
                "end_line": sec["end_line"],
                "score": raw_dense_score,
                "snippet": sec["content"] if len(sec["content"].splitlines()) <= 50 else chunk.get("content", sec["content"][:800])
            }

    sorted_dense = sorted(items_by_id.values(), key=lambda x: x["score"], reverse=True)
    return sorted_dense


def reciprocal_rank_fusion(
    dense_items: List[Dict[str, Any]],
    lexical_items: List[Dict[str, Any]],
    w_dense: float = 0.6,
    w_lexical: float = 0.4,
    rrf_k: int = 60
) -> List[Dict[str, Any]]:
    """
    Combines dense semantic matches and lexical keyword matches via Reciprocal Rank Fusion (RRF):
    RRF_score = (w_dense / (60 + rank_dense)) + (w_lexical / (60 + rank_lexical))
    """
    dense_ranks: Dict[str, int] = {}
    dense_map: Dict[str, Dict[str, Any]] = {}
    for idx, item in enumerate(dense_items, 1):
        i_id = item["id"]
        dense_ranks[i_id] = idx
        dense_map[i_id] = item

    lexical_ranks: Dict[str, int] = {}
    lexical_map: Dict[str, Dict[str, Any]] = {}
    for idx, item in enumerate(lexical_items, 1):
        i_id = item["id"]
        lexical_ranks[i_id] = idx
        lexical_map[i_id] = item

    # Union candidate IDs preserving dense and lexical order
    all_candidate_ids = list(dict.fromkeys(list(dense_ranks.keys()) + list(lexical_ranks.keys())))

    fused_results = []
    for item_id in all_candidate_ids:
        d_rank = dense_ranks.get(item_id)
        l_rank = lexical_ranks.get(item_id)

        term_dense = (w_dense / (rrf_k + d_rank)) if d_rank is not None else 0.0
        term_lexical = (w_lexical / (rrf_k + l_rank)) if l_rank is not None else 0.0
        rrf_score = term_dense + term_lexical

        base_item = dense_map.get(item_id) or lexical_map.get(item_id)
        res = dict(base_item)
        res["score"] = round(rrf_score, 6)
        res["rrf_score"] = round(rrf_score, 6)
        res["dense_rank"] = d_rank
        res["lexical_rank"] = l_rank
        res["dense_score"] = dense_map[item_id]["score"] if item_id in dense_map else None
        res["lexical_score"] = lexical_map[item_id]["score"] if item_id in lexical_map else None

        fused_results.append(res)

    fused_results.sort(
        key=lambda x: (x["rrf_score"], x.get("dense_score") or 0.0, x.get("lexical_score") or 0.0),
        reverse=True
    )
    return fused_results


def run_memory_search(
    query: str,
    scopes: Optional[List[str]] = None,
    is_regex: bool = False,
    case_sensitive: bool = False,
    max_results: int = 10,
    project_root: str = "/workspaces/codespaces-blank",
    apply_reranker: bool = True,
    hybrid: bool = True,
    w_dense: float = 0.6,
    w_lexical: float = 0.4,
    rrf_k: int = 60
) -> Dict[str, Any]:
    """
    Executes ranked memory search across designated scopes.
    When hybrid=True, fuses dense semantic retrieval from MemSearchBackend with lexical
    keyword matches using Reciprocal Rank Fusion (RRF).
    When hybrid=False or is_regex=True, executes lexical/regex search.
    """
    if not scopes:
        scopes = ["all"]

    files_with_scopes = discover_memory_files(scopes, project_root)
    total_files_scanned = len(files_with_scopes)
    sections_cache: Dict[str, List[Dict[str, Any]]] = {}

    # 1. Lexical search across discovered files
    raw_lexical_snippets = []
    for file_path, file_scope in files_with_scopes:
        snippets = extract_section_snippets(
            file_path=file_path,
            query=query,
            is_regex=is_regex,
            case_sensitive=case_sensitive,
            scope=file_scope
        )
        for s in snippets:
            if "error" in s:
                return {"status": "error", "message": s["error"]}
            raw_lexical_snippets.append(s)

    # 2. Check if hybrid mode is active
    enable_hybrid = hybrid and (not is_regex) and (MemSearchBackend is not None)

    if enable_hybrid:
        # Resolve lexical snippets to discrete section items
        lexical_items_map: Dict[str, Dict[str, Any]] = {}
        for s in raw_lexical_snippets:
            sec = find_enclosing_section(s["file"], s["start_line"], sections_cache)
            item_id = f"{s['file']}::{sec['start_line']}"
            if item_id not in lexical_items_map or s["score"] > lexical_items_map[item_id]["score"]:
                lexical_items_map[item_id] = {
                    "id": item_id,
                    "file": s["file"],
                    "filename": s["filename"],
                    "scope": s["scope"],
                    "heading": sec["heading"],
                    "section_meta": s.get("section_meta", []),
                    "start_line": sec["start_line"],
                    "end_line": sec["end_line"],
                    "score": s["score"],
                    "snippet": sec["content"] if len(sec["content"].splitlines()) <= 50 else s["snippet"]
                }
        sorted_lexical_items = sorted(lexical_items_map.values(), key=lambda x: x["score"], reverse=True)

        # Run dense semantic search via MemSearchBackend
        dense_items = run_dense_search(
            query=query,
            files_with_scopes=files_with_scopes,
            top_k=max_results,
            sections_cache=sections_cache
        )

        if dense_items:
            # Fused results via Reciprocal Rank Fusion
            fused_candidates = reciprocal_rank_fusion(
                dense_items=dense_items,
                lexical_items=sorted_lexical_items,
                w_dense=w_dense,
                w_lexical=w_lexical,
                rrf_k=rrf_k
            )

            # Apply multi-signal evidence reranking if enabled
            if EvidenceReranker is not None and apply_reranker:
                reranker = EvidenceReranker(project_root=project_root)
                final_results = reranker.rerank_results(fused_candidates, apply_reranker=True)
            else:
                final_results = fused_candidates
        else:
            # Fallback to lexical results if dense backend yielded zero items
            if EvidenceReranker is not None and apply_reranker:
                reranker = EvidenceReranker(project_root=project_root)
                final_results = reranker.rerank_results(raw_lexical_snippets, apply_reranker=True)
            else:
                raw_lexical_snippets.sort(key=lambda x: x["score"], reverse=True)
                final_results = raw_lexical_snippets
    else:
        # Lexical-only mode
        if EvidenceReranker is not None and apply_reranker:
            reranker = EvidenceReranker(project_root=project_root)
            final_results = reranker.rerank_results(raw_lexical_snippets, apply_reranker=True)
        else:
            raw_lexical_snippets.sort(key=lambda x: x["score"], reverse=True)
            final_results = raw_lexical_snippets

    trimmed_results = final_results[:max_results]

    return {
        "status": "success",
        "query": query,
        "is_regex": is_regex,
        "case_sensitive": case_sensitive,
        "scopes": scopes,
        "hybrid": enable_hybrid,
        "files_scanned_count": total_files_scanned,
        "total_matches_count": len(final_results),
        "reranker_applied": apply_reranker and (EvidenceReranker is not None),
        "results": trimmed_results
    }


def format_markdown_report(search_data: Dict[str, Any]) -> str:
    """
    Formats the search results into a clean, GitHub-flavored Markdown report.
    Wraps snippets in quad backticks (````markdown) to prevent code-fence breakout (SEC-005).
    """
    if search_data.get("status") == "error":
        return f"### Memory Search Error\n> [!CAUTION]\n> {search_data.get('message')}"

    query = search_data["query"]
    scopes_str = ", ".join(search_data["scopes"])
    total_matches = search_data["total_matches_count"]
    files_scanned = search_data["files_scanned_count"]
    is_hybrid = search_data.get("hybrid", False)
    results = search_data["results"]

    output = []
    output.append(f"## Memory Search Results: `{query}`")
    mode_str = "Hybrid (RRF Dense + Lexical)" if is_hybrid else "Lexical Only"
    output.append(f"- **Mode**: `{mode_str}` | **Scope(s)**: `{scopes_str}` | **Scanned Files**: {files_scanned} | **Total Matches**: {total_matches}")
    output.append("")

    if not results:
        output.append("> [!NOTE]")
        output.append(f"> No memory entries found matching query `{query}` in scope `{scopes_str}`.")
        output.append("")
        return "\n".join(output)

    output.append("| Rank | Score | Scope | Source File | Heading / Context | Lines |")
    output.append("| :---: | :---: | :---: | :--- | :--- | :---: |")

    for idx, r in enumerate(results, 1):
        file_link = f"[{r['filename']}](file://{r['file']}#L{r['start_line']}-L{r['end_line']})"
        heading_clean = r['heading'].replace("|", "\\|")
        output.append(f"| {idx} | **{r['score']}** | `{r['scope']}` | {file_link} | {heading_clean} | L{r['start_line']}-{r['end_line']} |")

    output.append("")
    output.append("### Extracted Relevant Snippets")
    output.append("")

    for idx, r in enumerate(results, 1):
        file_link = f"[{r['filename']}:L{r['start_line']}-{r['end_line']}](file://{r['file']}#L{r['start_line']}-{r['end_line']})"
        output.append(f"#### Match #{idx} — `{r['scope'].upper()}`: {file_link}")
        output.append(f"> **Section**: {r['heading']}")
        if "trust_verdict" in r:
            output.append(
                f"> **Evidence Signals**: Verdict: **{r['trust_verdict']}** | "
                f"Authority: `{r.get('source_tier', 'UNKNOWN')}` ({r.get('source_authority', 0.0)}) | "
                f"Confidence: {r.get('epistemic_confidence', 0.0)} | "
                f"Status: `{r.get('temporal_status', 'ACTIVE')}` | "
                f"Score: **{r.get('score', 0.0)}**"
            )
        if "rrf_score" in r:
            output.append(
                f"> **Fusion (RRF)**: Score: `{r['rrf_score']}` | "
                f"Dense Rank: `#{r.get('dense_rank', 'N/A')}` | "
                f"Lexical Rank: `#{r.get('lexical_rank', 'N/A')}`"
            )
        output.append("````markdown")
        output.append(r["snippet"])
        output.append("````")
        output.append("")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Antigravity Scoped Memory Search Engine")
    parser.add_argument("query", help="Keyword(s) or regular expression to search for")
    parser.add_argument("--scope", "-s", default="all", help="Comma-separated scopes to search (e.g. decisions,gotchas,global,project,all)")
    parser.add_argument("--regex", "-r", action="store_true", help="Treat search query as a regular expression")
    parser.add_argument("--case-sensitive", "-c", action="store_true", help="Enable case-sensitive searching")
    parser.add_argument("--max-results", "-n", type=int, default=10, help="Maximum number of ranked results to return (default: 10)")
    parser.add_argument("--json", "-j", action="store_true", help="Output results as structured JSON")
    parser.add_argument("--project-root", default="/workspaces/codespaces-blank", help="Project repository root directory")
    parser.add_argument(
        "--hybrid",
        nargs="?",
        const=True,
        default=True,
        type=str2bool,
        help="Enable hybrid search fusing dense semantic and lexical matches (default: True). Use --no-hybrid for lexical-only."
    )
    parser.add_argument(
        "--no-hybrid",
        dest="hybrid",
        action="store_false",
        help="Run lexical-only search without semantic vector fusion."
    )
    parser.add_argument(
        "--rerank",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable multi-signal evidence reranking (default: True, use --no-rerank for raw scoring)"
    )
    parser.add_argument("--log-telemetry", action="store_true", help="Record search results to retrieval_ledger.jsonl")

    args = parser.parse_args()

    scopes = [s.strip() for s in args.scope.split(",") if s.strip()]
    res = run_memory_search(
        query=args.query,
        scopes=scopes,
        is_regex=args.regex,
        case_sensitive=args.case_sensitive,
        max_results=args.max_results,
        project_root=args.project_root,
        apply_reranker=args.rerank,
        hybrid=args.hybrid
    )

    if args.log_telemetry and FeedbackLedger is not None:
        try:
            ledger = FeedbackLedger()
            q_id = f"search_{uuid.uuid4().hex[:8]}"
            batch = []
            for idx, r in enumerate(res.get("results", []), 1):
                mem_id = f"{os.path.basename(r.get('file', 'unknown'))}#{r.get('heading', 'root')}"
                batch.append({
                    "query_id": q_id,
                    "memory_id": mem_id,
                    "was_visible": True,
                    "rank": idx,
                    "used_in_action": False,
                    "outcome": FeedbackOutcome.INFERRED_NONUSE.value,
                    "metadata": {
                        "query": args.query,
                        "scope": r.get("scope"),
                        "search_score": r.get("score"),
                        "rrf_score": r.get("rrf_score"),
                        "source_tier": r.get("source_tier"),
                        "source_authority": r.get("source_authority"),
                        "trust_verdict": r.get("trust_verdict")
                    }
                })
            if batch:
                ledger.record_batch(batch)
                res["telemetry_query_id"] = q_id
        except Exception:
            pass

    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print(format_markdown_report(res))


if __name__ == "__main__":
    main()
