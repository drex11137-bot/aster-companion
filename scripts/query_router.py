#!/usr/bin/env python3
"""
query_router.py - Scope-Aware Query Intent Router with Explicit Abstention.
Part of the Antigravity Persistent Memory Architecture (Agent 10: Query Routing Specialist).

Conforms strictly to Instruction.md:
- Section 27: Scope-Aware Querying (inferred project vs global vs tool vs domain, multi-scope fanout, scope retention)
- Section 28: Layered Recall (L0 Route, L1 Retrieve, L2 Expand, L3 Verify, L4 Reconcile)
- Section 29: Context Compiler (compact memory context packages)
- Section 30: Abstention ("No sufficiently trustworthy memory found" and "Relevant historical memories found...")
- Section 140: Query Expansion (synonyms, technical terms, abbreviations, component hints, cost-controlled)
- Section 141: Temporal Query Routing (present vs historical vs timeless detection)
"""

import os
import sys
import re
import json
import argparse
from typing import List, Dict, Any, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from search_memory import discover_memory_files, extract_section_snippets, run_memory_search
except ImportError:
    discover_memory_files = None
    extract_section_snippets = None
    run_memory_search = None


# Technical abbreviations for query expansion (Section 140)
ABBREVIATIONS: Dict[str, str] = {
    "auth": "authentication",
    "repo": "repository",
    "adr": "architectural decision record",
    "k8s": "kubernetes",
    "db": "database",
    "ci": "continuous integration",
    "cd": "continuous deployment",
    "cli": "command line interface",
    "mem": "memory",
    "env": "environment",
    "config": "configuration",
    "doc": "documentation",
    "docs": "documentation",
    "spec": "specification",
    "pcap": "packet capture",
    "sast": "static application security testing",
    "wasm": "webassembly"
}

# Domain & tool technical expansions (capped to avoid query explosion)
TECHNICAL_EXPANSIONS: Dict[str, List[str]] = {
    "tests": ["run tests", "pytest", "unit tests", "testing", "ctest", "npm test"],
    "test": ["testing", "unit tests", "pytest", "ctest"],
    "auth": ["authentication", "token", "credentials", "oauth"],
    "git": ["git merge", "branching", "git rebase", "commit"],
    "docker": ["container", "dockerfile", "docker compose", "image"],
    "database": ["postgresql", "sqlite", "connection pool", "database"],
    "frontend": ["react", "ui", "components", "client"],
    "secret": ["api key", "token", "secret scanner", "credentials"],
    "fail": ["error", "crash", "gotcha", "exception", "failure"],
    "choose": ["decision", "adr", "rationale", "architecture"],
    "gradle": ["gradle daemon", "--no-daemon", "memory exhaustion", "gotcha"],
    "branch": ["branch merge workflow", "branching", "git rebase", "git"]
}

# Canonical component routing hints
COMPONENT_HINTS: Dict[str, List[str]] = {
    "decision": ["DECISIONS.md"],
    "adr": ["DECISIONS.md"],
    "why": ["DECISIONS.md"],
    "rationale": ["DECISIONS.md"],
    "gotcha": ["GOTCHAS.md"],
    "quirk": ["GOTCHAS.md"],
    "pitfall": ["GOTCHAS.md"],
    "bug": ["GOTCHAS.md"],
    "fail": ["GOTCHAS.md"],
    "error": ["GOTCHAS.md"],
    "exhaustion": ["GOTCHAS.md"],
    "gradle": ["GOTCHAS.md"],
    "architecture": ["ARCHITECTURE.md"],
    "topology": ["ARCHITECTURE.md"],
    "active": ["CURRENT.md"],
    "objective": ["CURRENT.md"],
    "current state": ["CURRENT.md"],
    "policy": ["POLICY.md"],
    "rule": ["POLICY.md"],
    "governance": ["POLICY.md"],
    "user": ["USER.md"],
    "preference": ["USER.md"],
    "environment": ["ENVIRONMENT.md"],
    "specs": ["ENVIRONMENT.md"],
    "version": ["ENVIRONMENT.md"]
}


class QueryRouter:
    """
    Intelligent Query Intent and Scope Router with Explicit Abstention.
    """

    def __init__(
        self,
        project_root: str = "/workspaces/codespaces-blank",
        confidence_threshold: float = 0.40
    ):
        self.project_root = os.path.abspath(project_root)
        self.confidence_threshold = confidence_threshold
        self.global_mem_dir = os.path.expanduser("~/.gemini/antigravity-cli/memory")
        self.project_mem_dir = os.path.join(self.project_root, ".agents", "memory")

    def classify_intent(self, query: str) -> Dict[str, Any]:
        """
        Classifies query intent into one of 5 distinct categories:
        - present-state ("What is X now?")
        - historical as-of ("What was X before?")
        - procedural ("How do I do X?")
        - debugging ("Why did X fail?")
        - why/rationale ("Why did we choose X?")
        Also resolves temporal orientation per Section 141.
        """
        clean_q = query.strip()
        lower_q = clean_q.lower()

        scores = {
            "present-state": 0.0,
            "historical as-of": 0.0,
            "procedural": 0.0,
            "debugging": 0.0,
            "why/rationale": 0.0
        }
        matched_indicators = []
        temporal = "timeless"

        # 1. Temporal Detection (Section 141)
        present_temporal_patterns = [
            r"\b(currently|right now|now|today|latest|present|active|at present)\b",
            r"^what is .* (now|currently|today|latest)",
            r"^what (is|are) the (current|latest|present|active)",
            r"^what's .* now"
        ]
        historical_temporal_patterns = [
            r"\b(before|previously|prior|formerly|earlier|used to be|was|were|in the past)\b",
            r"\b(at the time|when we changed|last month|last week|superseded)\b",
            r"^what was .* (before|previously|prior|formerly)",
            r"^what was the (previous|former|old|prior|historical)",
            r"^how did we .* (before|previously)"
        ]

        for p in present_temporal_patterns:
            if re.search(p, lower_q):
                temporal = "present"
                scores["present-state"] += 3.5
                matched_indicators.append(f"present-temporal: {p}")
                break

        for p in historical_temporal_patterns:
            if re.search(p, lower_q):
                temporal = "historical"
                scores["historical as-of"] += 4.0
                matched_indicators.append(f"historical-temporal: {p}")
                break

        # 2. Procedural Patterns ("How do I do X?", "How do we run tests?", "What is our convention?")
        procedural_patterns = [
            (r"\b(how do (i|we|you)|how can (i|we|you)|how should (i|we)|how to)\b", 4.0),
            (r"\b(steps to|step-by-step|procedure for|workflow for|guide to|guide for|instructions for)\b", 3.5),
            (r"\b(how do we run|commands to|commands for|how to execute|how to build|how to deploy|how to test)\b", 4.5),
            (r"\b(run tests|test execution|execute tests|build workflow|run ctest|run pytest)\b", 2.5),
            (r"\b(convention(s)?|workflow(s)?|guideline(s)?|best practice(s)?|git merge convention)\b", 4.0)
        ]
        for pat, weight in procedural_patterns:
            if re.search(pat, lower_q):
                scores["procedural"] += weight
                matched_indicators.append(f"procedural: {pat}")

        # 3. Debugging Patterns ("Why did X fail?", "Error handling", "Crash")
        debugging_patterns = [
            (r"\b(why did .* fail|why is .* failing|why does .* fail)\b", 5.0),
            (r"\b(why did .* crash|why is .* broken|why didn't .* work)\b", 5.0),
            (r"\b(fail|failed|failure|failing)\b", 2.5),
            (r"\b(error|exception|traceback|crash|crashed|bug|broken|troubleshoot|gotcha)\b", 2.5),
            (r"\b(fix for|resolve issue|debugging)\b", 2.5)
        ]
        for pat, weight in debugging_patterns:
            if re.search(pat, lower_q):
                scores["debugging"] += weight
                matched_indicators.append(f"debugging: {pat}")

        # 4. Why/Rationale Patterns ("Why did we choose X?", "ADR", "Decision")
        why_patterns = [
            (r"\b(why did we choose|why was .* chosen|why did we pick|why did we use)\b", 5.0),
            (r"\b(why prefer|why choose|why pick|why not)\b", 4.0),
            (r"\b(rationale (for|behind)|reason (for|behind)|justification for)\b", 4.0),
            (r"\b(architectural decision|decision on|decision behind|adr-?\d*)\b", 3.5),
            (r"\b(trade-?off|tradeoffs)\b", 3.0)
        ]
        for pat, weight in why_patterns:
            if re.search(pat, lower_q):
                scores["why/rationale"] += weight
                matched_indicators.append(f"why/rationale: {pat}")

        # 5. Present-State Specific Question Patterns ("What is X now?")
        present_patterns = [
            (r"^what is [^?]+ now\??$", 4.0),
            (r"^what is the current\b", 4.0),
            (r"\b(current objective|active status|active working state)\b", 3.5),
            (r"^who is the (current|active)\b", 3.0),
            (r"\b(what are we working on now|active phase)\b", 4.0)
        ]
        for pat, weight in present_patterns:
            if re.search(pat, lower_q):
                scores["present-state"] += weight
                matched_indicators.append(f"present-state: {pat}")

        # Tie-breaking and disambiguation:
        # "Why did X fail?" is debugging, NOT why/rationale
        if scores["debugging"] > 0 and scores["why/rationale"] > 0:
            if re.search(r"\b(fail|error|crash|broken|exception)\b", lower_q):
                scores["why/rationale"] *= 0.3

        # Select top scoring intent
        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_intent, top_score = sorted_intents[0]

        # Calculate confidence of classification
        total_score = sum(scores.values())
        if total_score > 0:
            classification_confidence = round(min(0.98, top_score / (total_score + 0.1)), 2)
            if top_score >= 3.5:
                classification_confidence = max(0.85, classification_confidence)
        else:
            # Fallback based on question opening
            if lower_q.startswith("how"):
                top_intent = "procedural"
                classification_confidence = 0.70
            elif lower_q.startswith("why"):
                top_intent = "why/rationale"
                classification_confidence = 0.70
            elif lower_q.startswith("what was") or lower_q.startswith("when"):
                top_intent = "historical as-of"
                classification_confidence = 0.70
            else:
                top_intent = "present-state"
                classification_confidence = 0.60

        return {
            "intent": top_intent,
            "confidence": classification_confidence,
            "temporal": temporal,
            "scores": {k: round(v, 2) for k, v in scores.items()},
            "indicators": matched_indicators
        }

    def determine_scope(self, query: str, intent: Optional[str] = None) -> Dict[str, Any]:
        """
        Determines target scope automatically per Section 27:
        - project vs global vs tool vs domain
        - supports multi-scope candidate fan-out with scope provenance
        """
        lower_q = query.lower()
        
        # Scope score accumulator
        scope_scores = {
            "project": 0.0,
            "global": 0.0,
            "tool": 0.0,
            "domain": 0.0
        }
        reasoning = []

        # Project indicators (Section 27: "How do we handle this repo's auth?")
        project_signals = [
            (r"\b(this repo('s)?|our repo|this project|our project|this codebase|our app)\b", 4.0, "explicit repo reference"),
            (r"\b(in this repo|in our codebase|here|locally|current objective)\b", 3.0, "local context indicator"),
            (r"\b(adr|adr-\d+|architecture|decisions?|gotchas?)\b", 3.0, "project memory file reference"),
            (r"\b(run tests|unit tests|test suite|how do we test|ctest|pytest)\b", 3.0, "project test execution"),
            (r"\b(secret scanner|lock manager|session manager)\b", 3.0, "project script reference"),
            (r"\b(auth)\b", 2.0, "repo auth reference (Instruction.md Section 27)")
        ]
        for pat, wt, rsn in project_signals:
            if re.search(pat, lower_q):
                scope_scores["project"] += wt
                reasoning.append(f"project: {rsn}")

        # Tool indicators (Section 27: "What is our general Git merge convention?")
        tool_signals = [
            (r"\b(git|github|rebase|merge convention|branching|pull request)\b", 4.0, "Git tool reference"),
            (r"\b(docker|dockerfile|compose|container)\b", 3.5, "Docker tool reference"),
            (r"\b(npm|pnpm|yarn|node|package\.json)\b", 3.0, "JS package manager tool"),
            (r"\b(gradle|gradlew|cmake|ninja|ctest)\b", 3.0, "Build system tool"),
            (r"\b(playwright|headless browser)\b", 3.0, "Browser automation tool"),
            (r"\b(tshark|capinfos|tcpdump|nmap)\b", 3.0, "Network CLI tool"),
            (r"\b(ghidra|radare2|r2|rizin|checksec|gdb|lldb)\b", 3.5, "Reverse engineering tool"),
            (r"\b(semgrep|gitleaks|codeql|bandit)\b", 3.0, "Security analysis tool")
        ]
        for pat, wt, rsn in tool_signals:
            if re.search(pat, lower_q):
                scope_scores["tool"] += wt
                reasoning.append(f"tool: {rsn}")

        # Domain indicators
        domain_signals = [
            (r"\b(frontend|react|vue|ui components|tailwind|css|dom)\b", 3.5, "Frontend domain"),
            (r"\b(database|postgres|postgresql|sqlite|pooling|query optimization)\b", 3.5, "Database domain"),
            (r"\b(android|apk|dex|smali|jadx|apktool|aab)\b", 3.5, "Android domain"),
            (r"\b(wasm|webassembly|wat|wasm2wat|wat2wasm|wasmtime)\b", 3.5, "WASM domain"),
            (r"\b(cybersecurity|sast|reverse engineering|forensics)\b", 3.0, "Security/Forensics domain"),
            (r"\b(medical|healthcare|hipaa)\b", 3.5, "Medical domain")
        ]
        for pat, wt, rsn in domain_signals:
            if re.search(pat, lower_q):
                scope_scores["domain"] += wt
                reasoning.append(f"domain: {rsn}")

        # Global indicators
        global_signals = [
            (r"\b(general|across projects|all projects|globally|global memory)\b", 4.0, "explicit global reference"),
            (r"\b(user preferences?|user directives?|communication style)\b", 4.0, "USER.md preferences"),
            (r"\b(policy|memory policy|governance|immutable rules?|durability scale)\b", 4.0, "POLICY.md memory governance"),
            (r"\b(environment|cli version|agy version|specs|system specs)\b", 3.5, "ENVIRONMENT.md system specs"),
            (r"\b(engineering practices?|modular units|clean architecture)\b", 3.0, "GENERAL.md engineering practices")
        ]
        for pat, wt, rsn in global_signals:
            if re.search(pat, lower_q):
                scope_scores["global"] += wt
                reasoning.append(f"global: {rsn}")

        # Default fallback logic per Instruction.md Section 27
        if scope_scores["tool"] > 0 and "general" in lower_q:
            scope_scores["global"] += 2.0

        # Sort scopes
        ranked = sorted(scope_scores.items(), key=lambda x: x[1], reverse=True)
        primary_scope, primary_score = ranked[0]

        # If zero signal, default based on intent
        if primary_score == 0:
            if intent in ("why/rationale", "debugging", "present-state"):
                primary_scope = "project"
                reasoning.append("defaulted to project for intent contextualization")
            elif intent == "procedural":
                primary_scope = "project"
                reasoning.append("procedural repository default")
            else:
                primary_scope = "global"
                reasoning.append("broad query defaulted to global")

        # Candidate fan-out list (Section 27: multi-scope fanout)
        candidate_scopes = [primary_scope]
        for sc, sc_val in ranked[1:]:
            if sc_val >= 1.5 or (primary_score < 3.0 and sc not in candidate_scopes):
                candidate_scopes.append(sc)

        # Always include project & global in candidates if tool or domain is chosen
        if primary_scope in ("tool", "domain"):
            if "global" not in candidate_scopes:
                candidate_scopes.append("global")
            if intent in ("debugging", "why/rationale") or any(t in lower_q for t in ["gradle", "exhaustion", "gotcha", "crash", "bug", "daemon"]):
                if "project" not in candidate_scopes:
                    candidate_scopes.append("project")
        if primary_scope == "project" and "tool" not in candidate_scopes and any(t in lower_q for t in ["test", "git", "run"]):
            candidate_scopes.append("tool")

        return {
            "primary": primary_scope,
            "candidates": candidate_scopes,
            "scores": {k: round(v, 2) for k, v in scope_scores.items()},
            "reasoning": "; ".join(reasoning) if reasoning else "default scope assignment"
        }

    def expand_query(self, query: str, intent: Optional[str] = None) -> Dict[str, Any]:
        """
        Controlled Query Expansion per Section 140.
        Expands abbreviations, technical synonyms, and component hints without cost explosion.
        """
        clean_q = query.strip()
        tokens = re.findall(r"[A-Za-z0-9_-]+", clean_q.lower())
        
        expanded_terms = set()
        matched_abbreviations = {}
        hints = set()

        # 1. Expand abbreviations
        for tok in tokens:
            if tok in ABBREVIATIONS:
                expanded = ABBREVIATIONS[tok]
                matched_abbreviations[tok] = expanded
                expanded_terms.add(expanded)

        # 2. Add high-value technical synonyms
        for tok in tokens:
            if tok in TECHNICAL_EXPANSIONS:
                for exp in TECHNICAL_EXPANSIONS[tok][:3]:  # Top 3 to avoid explosion
                    expanded_terms.add(exp)

        # 3. Component mapping
        for key, files in COMPONENT_HINTS.items():
            if key in clean_q.lower():
                hints.update(files)

        # Add the original query terms
        expanded_terms.add(clean_q.lower())

        # Benchmark/cost cap: max 4 expanded terms
        capped_expansions = sorted(list(expanded_terms))[:4]

        return {
            "original_query": clean_q,
            "expanded_terms": capped_expansions,
            "abbreviations": matched_abbreviations,
            "component_hints": sorted(list(hints))
        }

    def calculate_match_confidence(
        self,
        snippet_data: Dict[str, Any],
        intent_data: Dict[str, Any],
        target_scope: str,
        query: str = ""
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculates normalized confidence (0.0 - 1.0) based on:
        - raw lexical/semantic score from search_memory
        - query content term coverage (penalizes incidental single-word hits)
        - intent alignment (procedural steps vs rationale vs debugging vs active/superseded)
        - trustworthiness signals (Confidence: VERIFIED, canonical source citations)
        """
        raw_score = float(snippet_data.get("score", 0))
        heading = snippet_data.get("heading", "")
        content = snippet_data.get("snippet", "")
        file_path = snippet_data.get("file", "")
        scope = snippet_data.get("scope", "")

        intent = intent_data.get("intent", "present-state")
        temporal = intent_data.get("temporal", "timeless")

        # Content token coverage check
        stopwords = {
            "what", "is", "the", "of", "this", "that", "in", "on", "for", "to", "a", "an",
            "and", "or", "how", "do", "we", "i", "can", "why", "did", "was", "our", "are",
            "about", "with", "by", "at", "from", "now", "before"
        }
        query_content_tokens = [
            t for t in re.findall(r"[a-z0-9_-]+", query.lower())
            if t not in stopwords and len(t) > 2
        ]
        match_text = (heading + " " + content).lower()
        if query_content_tokens:
            matched_tokens = [t for t in query_content_tokens if t in match_text]
            term_coverage = len(matched_tokens) / len(query_content_tokens)
        else:
            term_coverage = 1.0

        # Term coverage penalty
        if term_coverage < 0.4:
            coverage_multiplier = term_coverage * 0.5
        elif term_coverage < 0.7:
            coverage_multiplier = term_coverage
        else:
            coverage_multiplier = 1.0

        # Metadata extraction
        is_quarantined_candidate = bool(
            "inbox/" in file_path or
            "inbox" in os.path.dirname(file_path).split(os.sep) or
            re.search(r"status:\s*\"?CANDIDATE_STAGED\"?", content, re.IGNORECASE) or
            re.search(r"admitted:\s*false\b", content, re.IGNORECASE)
        )
        is_active = bool(
            (re.search(r"\bStatus:\s*ACTIVE\b", content, re.IGNORECASE) or
             "CURRENT.md" in file_path or
             "## Antigravity CLI Version History" in content) and
            not is_quarantined_candidate
        )
        is_superseded = bool(
            re.search(r"\bStatus:\s*SUPERSEDED\b", content, re.IGNORECASE) or
            "superseded" in heading.lower() or
            "## Superseded" in content
        )
        is_verified = bool(
            re.search(r"\bConfidence:\s*VERIFIED\b", content, re.IGNORECASE) and
            not is_quarantined_candidate
        )
        has_canonical_source = bool(
            re.search(r"\bSource:\s*[^\*\n]+", content, re.IGNORECASE)
        )

        # Base confidence calculation from search_memory score
        base_confidence = min(0.60, raw_score / 65.0)

        # Intent alignment factor
        alignment = 1.0
        details = []

        if intent == "procedural":
            # Procedural queries MUST have actionable steps or commands
            has_commands = bool(
                re.search(r"\b(npm test|pytest|ctest|cargo test|make|bash|gradlew|step\s*\d|instructions|workflow)\b|\brun\s+[a-z0-9_\-\./]+", content, re.IGNORECASE)
            )
            has_proc_heading = bool(
                re.search(r"\b(procedure|workflow|guide|how to|runbook)\b", heading, re.IGNORECASE)
            )
            if has_commands and has_proc_heading:
                alignment = 1.4
                details.append("strong procedural structure matched")
            elif has_proc_heading:
                alignment = 0.8
                details.append("procedural heading matched")
            else:
                # Passing mention of a term (e.g. "runtime" in changelog)
                # is NOT procedural execution guidance
                alignment = 0.20
                details.append("lacks procedural instructions or commands")

        elif intent == "why/rationale":
            has_rationale_sec = bool(
                re.search(r"(### Why|Rationale|Decision|trade-?off|justification|ADR-\d+)", content + heading, re.IGNORECASE)
            )
            if has_rationale_sec:
                alignment = 1.4
                details.append("decision rationale structure matched")
            else:
                alignment = 0.35
                details.append("lacks architectural rationale")

        elif intent == "debugging":
            has_debugging_sec = bool(
                re.search(r"(gotcha|quirk|pitfall|error|fail|troubleshoot|fix|problem|issue)", content + heading, re.IGNORECASE)
            )
            if has_debugging_sec:
                alignment = 1.4
                details.append("debugging/gotcha structure matched")
            else:
                alignment = 0.35
                details.append("lacks troubleshooting or gotcha context")

        elif intent == "present-state":
            if is_active and not is_superseded:
                alignment = 1.3
                details.append("active present state verified")
            elif is_superseded:
                alignment = 0.15
                details.append("superseded record cannot represent present state")
            else:
                alignment = 0.9

        elif intent == "historical as-of":
            if is_superseded or "sessions/" in file_path or "Superseded" in heading:
                alignment = 1.4
                details.append("historical / superseded record verified")
            elif is_active:
                alignment = 0.5
                details.append("active record demoted for historical query")
            else:
                alignment = 0.9

        # Trustworthiness weighting
        trust_multiplier = 1.0
        if is_verified:
            trust_multiplier += 0.15
            details.append("verified memory entry")
        if has_canonical_source:
            trust_multiplier += 0.10
            details.append("canonical source citation present")

        # Canonical file bonus
        canonical_files = ["DECISIONS.md", "GOTCHAS.md", "ARCHITECTURE.md", "POLICY.md", "ENVIRONMENT.md", "GENERAL.md", "USER.md"]
        if any(cf in file_path for cf in canonical_files):
            trust_multiplier += 0.10
            details.append("canonical memory file tier")

        if is_quarantined_candidate:
            trust_multiplier = 0.20
            details.append("quarantined unadmitted candidate (Invariant 16)")

        final_confidence = round(min(0.98, max(0.05, base_confidence * alignment * trust_multiplier * coverage_multiplier)), 2)
        if is_quarantined_candidate:
            final_confidence = min(final_confidence, 0.25)

        meta = {
            "is_active": is_active,
            "is_superseded": is_superseded,
            "is_verified": is_verified,
            "has_canonical_source": has_canonical_source,
            "alignment": alignment,
            "alignment_details": details
        }
        return final_confidence, meta

    def compile_context_package(self, match: Dict[str, Any]) -> str:
        """
        Builds a compact memory context package per Instruction.md Section 29.
        """
        content = match.get("content", "")
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        topic = match.get("topic", "General Memory")
        topic = re.sub(r"^#+\s*", "", topic)

        status = match.get("status", "ACTIVE")
        confidence = match.get("confidence", 0.85)
        scope = match.get("scope", "PROJECT").upper()
        source = match.get("source", match.get("filename", "memory"))
        date_str = match.get("date", "2026-09-01")
        evidence = match.get("evidence", "verified memory file")

        # L2 Expansion (Instruction.md Section 28): Retrieve canonical section body
        expanded_body_lines = []
        file_path = match.get("file")
        start_line = match.get("start_line", 1)
        if file_path and os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    all_lines = f.readlines()
                curr_idx = max(0, start_line - 1)
                if curr_idx < len(all_lines) and all_lines[curr_idx].strip().startswith("## "):
                    curr_idx += 1
                while curr_idx < len(all_lines):
                    line_str = all_lines[curr_idx].strip()
                    if line_str.startswith("## ") and curr_idx > start_line:
                        break
                    if not (line_str.startswith("**Type:**") or line_str.startswith("**Confidence:**") or line_str.startswith("## ")):
                        if line_str:
                            expanded_body_lines.append(line_str)
                    curr_idx += 1
                    if len(expanded_body_lines) >= 8:
                        break
            except Exception:
                pass

        if expanded_body_lines:
            cleaned_body = "\n".join(expanded_body_lines)
        else:
            # Fallback to snippet content
            cleaned_body_lines = []
            for line in lines:
                if line.startswith("**Type:**") or line.startswith("**Confidence:**") or line.startswith("## "):
                    continue
                cleaned_body_lines.append(line)
            cleaned_body = "\n".join(cleaned_body_lines[:8])

        package = (
            f"[MEMORY]\n"
            f"Topic: {topic}\n"
            f"Status: {status}\n"
            f"Confidence: {confidence:.2f}\n"
            f"Scope: {scope}\n"
            f"Source: {source}\n"
            f"Evidence: {evidence}\n"
            f"Date: {date_str}\n"
            f"Line Range: L{match.get('start_line', 1)}-L{match.get('end_line', 1)}\n\n"
            f"{cleaned_body}"
        )
        return package

    def route(self, query: str, **kwargs) -> Dict[str, Any]:
        """Convenience alias for route_and_query."""
        return self.route_and_query(query, **kwargs)

    def route_and_query(
        self,
        query: str,
        scope_override: Optional[str] = None,
        threshold_override: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Full end-to-end routing pipeline:
        1. Classifies intent & temporal orientation
        2. Determines automatic target scope
        3. Executes controlled query expansion
        4. Performs scoped retrieval
        5. Ranks matches by intent alignment & verification trust
        6. Enforces explicit abstention per Section 30
        7. Compiles compact context package per Section 29
        """
        threshold = threshold_override if threshold_override is not None else self.confidence_threshold

        # Step 1: Intent & Temporal Classification
        intent_info = self.classify_intent(query)
        
        # Step 2: Scope Determination
        scope_info = self.determine_scope(query, intent=intent_info["intent"])
        if scope_override and scope_override.lower() != "auto":
            target_scopes = [scope_override.lower()]
            scope_info["primary"] = scope_override.lower()
            scope_info["candidates"] = [scope_override.lower()]
        else:
            target_scopes = scope_info["candidates"]

        # Step 3: Controlled Query Expansion
        expansion = self.expand_query(query, intent=intent_info["intent"])

        # Step 4: Scoped Retrieval
        search_scopes = []
        for sc in target_scopes:
            if sc == "project":
                search_scopes.extend(["project", "decisions", "gotchas", "architecture", "current"])
            elif sc == "global":
                search_scopes.extend(["global", "general", "user", "environment", "policy"])
            elif sc == "tool":
                search_scopes.append("tools")
            elif sc == "domain":
                search_scopes.append("domains")
            elif sc == "all":
                search_scopes.append("all")
        search_scopes = list(dict.fromkeys(search_scopes))

        raw_candidates = []
        if run_memory_search:
            search_terms = [expansion["original_query"]]
            for term in expansion["expanded_terms"][:2]:
                if term != expansion["original_query"].lower() and len(term) >= 3:
                    search_terms.append(term)

            for term in search_terms:
                res = run_memory_search(
                    query=term,
                    scopes=search_scopes,
                    project_root=self.project_root,
                    max_results=15
                )
                if res.get("status") == "success":
                    raw_candidates.extend(res.get("results", []))

        # Deduplicate candidates by file and line range
        seen_keys = set()
        deduped_candidates = []
        for c in raw_candidates:
            key = (c.get("file"), c.get("start_line"), c.get("end_line"))
            if key not in seen_keys:
                seen_keys.add(key)
                deduped_candidates.append(c)

        # Step 5: Rank Matches by Intent Alignment and Trust
        evaluated_matches = []
        has_active_match = False
        has_historical_match = False

        for cand in deduped_candidates:
            conf, meta = self.calculate_match_confidence(cand, intent_info, scope_info["primary"], query=query)
            if meta["is_superseded"]:
                has_historical_match = True
            if meta["is_active"]:
                has_active_match = True

            heading = cand.get("heading", "Memory")
            content = cand.get("snippet", "")
            
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", heading + " " + content)
            date_str = date_match.group(1) if date_match else "2026-09-01"

            source_match = re.search(r"\*\*Source:\*\*\s*([^\*\n]+)", content)
            source_val = source_match.group(1).strip() if source_match else cand.get("filename", "memory")

            status_val = "SUPERSEDED" if meta["is_superseded"] else "ACTIVE"

            match_entry = {
                "topic": heading,
                "status": status_val,
                "confidence": conf,
                "scope": cand.get("scope", scope_info["primary"]),
                "source": source_val,
                "evidence": f"File: {cand.get('filename')} (lines {cand.get('start_line')}-{cand.get('end_line')})",
                "date": date_str,
                "file": cand.get("file"),
                "filename": cand.get("filename"),
                "start_line": cand.get("start_line"),
                "end_line": cand.get("end_line"),
                "content": content,
                "alignment_details": meta["alignment_details"]
            }
            evaluated_matches.append(match_entry)

        evaluated_matches.sort(key=lambda x: x["confidence"], reverse=True)

        # Step 6: Enforce Explicit Abstention (Instruction.md Section 30)
        abstained = False
        abstention_message = ""
        abstention_reason = ""
        best_match = evaluated_matches[0] if evaluated_matches else None
        max_confidence = best_match["confidence"] if best_match else 0.0

        if not evaluated_matches or max_confidence < threshold:
            abstained = True
            abstention_message = "No sufficiently trustworthy memory found"
            abstention_reason = (
                f"Confidence below threshold (max confidence: {max_confidence:.2f} < threshold: {threshold:.2f})"
                if evaluated_matches else "Zero candidate matches discovered in requested scopes"
            )
        elif intent_info["intent"] == "present-state" and best_match["status"] == "SUPERSEDED" and not has_active_match:
            abstained = True
            abstention_message = "Relevant historical memories found, but current-state verification is required."
            abstention_reason = "Historical/superseded record matched, but present-state query mandates live verification."

        # Step 7: Compile Output Package if not abstaining
        compiled_package = None
        if not abstained and best_match:
            compiled_package = self.compile_context_package(best_match)

        return {
            "query": query,
            "intent": intent_info,
            "scope": scope_info,
            "expansion": expansion,
            "max_confidence": max_confidence,
            "threshold": threshold,
            "abstained": abstained,
            "abstention_reason": abstention_reason if abstained else None,
            "message": abstention_message if abstained else "Trustworthy memory matched",
            "matches": evaluated_matches[:3] if not abstained else evaluated_matches[:1],
            "context_package": compiled_package
        }


def format_markdown_report(res: Dict[str, Any]) -> str:
    """
    Renders human-readable GitHub-flavored Markdown output.
    """
    query = res["query"]
    intent = res["intent"]
    scope = res["scope"]
    expansion = res["expansion"]
    max_conf = res["max_confidence"]
    threshold = res["threshold"]
    abstained = res["abstained"]
    message = res["message"]

    lines = []
    lines.append("# Antigravity Query Intent & Scope Router")
    lines.append(f"- **Query**: `{query}`")
    lines.append(f"- **Classified Intent**: `{intent['intent']}` (confidence: `{intent['confidence']}`, temporal: `{intent['temporal']}`)")
    lines.append(f"- **Target Scope**: `{scope['primary']}` (candidates: `{', '.join(scope['candidates'])}`)")
    lines.append(f"- **Scope Reasoning**: {scope['reasoning']}")
    lines.append(f"- **Query Expansion**: {', '.join([f'`{t}`' for t in expansion['expanded_terms']])}")
    lines.append(f"- **Confidence Score**: `{max_conf:.2f}` (Threshold: `{threshold:.2f}`)")
    status_tag = "ABSTAINED" if abstained else "RESOLVED"
    lines.append(f"- **Status**: `{status_tag}`")
    lines.append("")

    if abstained:
        lines.append("### Abstention Outcome")
        lines.append("> [!WARNING]")
        lines.append(f"> **{message}**")
        lines.append(">")
        lines.append(f"> *Reasoning:* {res['abstention_reason']}")
        lines.append("")
    else:
        lines.append("### Compiled Context Package (Instruction.md Section 29)")
        lines.append("```text")
        lines.append(res["context_package"])
        lines.append("```")
        lines.append("")
        lines.append("### Matched Candidates")
        for idx, m in enumerate(res["matches"], 1):
            file_link = f"[{m['filename']}](file://{m['file']}#L{m['start_line']}-L{m['end_line']})"
            lines.append(f"{idx}. **{m['topic']}** | Status: `{m['status']}` | Score: `{m['confidence']}` | File: {file_link}")
        lines.append("")

    return "\n".join(lines)


def run_benchmarks():
    """
    Runs self-verification benchmarks for intent classification, scope routing, and abstention.
    """
    router = QueryRouter()
    test_cases = [
        ("What is the active objective now?", "present-state", "project"),
        ("What was the previous version of Antigravity CLI before 1.1.25?", "historical as-of", "global"),
        ("How do we run tests?", "procedural", "project"),
        ("Why did secret scanning fail?", "debugging", "project"),
        ("Why did we choose the 5-tier memory architecture?", "why/rationale", "project"),
        ("What is our general Git merge convention?", "procedural", "tool"),
        ("How do we handle this repo's auth?", "procedural", "project")
    ]
    print("=" * 70)
    print("RUNNING QUERY ROUTER BENCHMARKS")
    print("=" * 70)
    all_passed = True
    for q, expected_intent, expected_scope in test_cases:
        intent_res = router.classify_intent(q)
        scope_res = router.determine_scope(q, intent=intent_res["intent"])
        intent_match = (intent_res["intent"] == expected_intent)
        scope_match = (scope_res["primary"] == expected_scope or expected_scope in scope_res["candidates"])
        passed = intent_match and scope_match
        if not passed:
            all_passed = False
        status_sym = "PASS" if passed else "FAIL"
        print(f"[{status_sym}] Query: '{q}'")
        print(f"       Intent: {intent_res['intent']} (expected: {expected_intent})")
        print(f"       Scope: {scope_res['primary']} (expected: {expected_scope}, candidates: {scope_res['candidates']})")
    print("=" * 70)
    print(f"OVERALL BENCHMARK: {'PASSED' if all_passed else 'FAILED'}")
    print("=" * 70)
    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Antigravity Scope-Aware Query Intent Router with Explicit Abstention")
    parser.add_argument("--query", "-q", help="The query string to route and evaluate")
    parser.add_argument("pos_query", nargs="?", help="Positional query string fallback")
    parser.add_argument("--scope", "-s", default="auto", help="Scope override (project, global, tool, domain, all, auto)")
    parser.add_argument("--threshold", "-t", type=float, default=0.40, help="Confidence threshold for abstention (default: 0.40)")
    parser.add_argument("--json", "-j", action="store_true", help="Output results in JSON format")
    parser.add_argument("--benchmark", action="store_true", help="Run routing and expansion benchmarks")
    parser.add_argument("--project-root", default="/workspaces/codespaces-blank", help="Workspace project root path")

    args = parser.parse_args()

    if args.benchmark:
        success = run_benchmarks()
        sys.exit(0 if success else 1)

    query_str = args.query or args.pos_query
    if not query_str:
        parser.print_help()
        sys.exit(1)

    router = QueryRouter(project_root=args.project_root, confidence_threshold=args.threshold)
    result = router.route_and_query(query=query_str, scope_override=args.scope, threshold_override=args.threshold)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_markdown_report(result))


if __name__ == "__main__":
    main()
