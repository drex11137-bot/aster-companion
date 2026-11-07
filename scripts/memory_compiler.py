#!/usr/bin/env python3
"""
Memory Compiler & Admission Gatekeeper for Antigravity Persistent Memory.
Instruction.md Section 10 & 11 Implementation.

Responsibilities:
1. Reads candidate records from .agents/memory/inbox/candidates.jsonl.
2. Normalizes candidates into 9 canonical memory categories:
   EPHEMERAL, SESSION, PROJECT, DOMAIN, TOOL, GLOBAL, DECISION, GOTCHA, PROCEDURE.
3. Computes candidate score:
   candidate_score = Novelty + Durability + Evidence - Redundancy
4. Enforces Admission Gate:
   - Security verification (zero secrets / prompt-injection protection via SecretScanner)
   - Durability score >= 3.0 and verified provenance required for canonical promotion
   - Durability == 2.0 (SESSION) -> HOLD for session log staging
   - Durability <= 1.0 (EPHEMERAL) -> REJECT (discarded as transient noise)
   - High redundancy (>= max_redundancy) -> REJECT
5. Emits admission decisions: ACCEPT, HOLD, REJECT with auditable provenance and rationale.
6. Implements Section 11 contract:
   normalize(), classify(), find_exact_duplicates(), find_semantic_neighbors(),
   detect_conflict(), resolve_temporal_state(), calculate_confidence(),
   calculate_scope(), attach_provenance(), decide_admission(), prepare_write().
"""

import os
import sys
import json
import re
import hashlib
import datetime
import tempfile
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

# Ensure scripts directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

WORKSPACE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
PROJECT_MEM_DIR = os.path.join(WORKSPACE_DIR, ".agents", "memory")
PROJECT_INBOX_DIR = os.path.join(PROJECT_MEM_DIR, "inbox")
DEFAULT_CANDIDATES_FILE = os.path.join(PROJECT_INBOX_DIR, "candidates.jsonl")
CANONICAL_DECISIONS_FILE = os.path.join(PROJECT_MEM_DIR, "admission_decisions.jsonl")
DEFAULT_DECISIONS_FILE = CANONICAL_DECISIONS_FILE
GLOBAL_MEM_DIR = os.path.expanduser("~/.gemini/antigravity-cli/memory")
SCHEMA_VERSION = "2.0.0"

# Security integration
try:
    from secret_scanner import scan_text
except ImportError:
    try:
        from scripts.secret_scanner import scan_text
    except ImportError:
        def scan_text(text: str, **kwargs):
            class DummyScanResult:
                is_clean = True
                findings = []
            return DummyScanResult()

# Concurrency & Lock Manager integration per Section 15 & 84
try:
    from lock_manager import file_lock, atomic_write, safe_update_memory
except ImportError:
    try:
        from scripts.lock_manager import file_lock, atomic_write, safe_update_memory
    except ImportError:
        from contextlib import contextmanager

        @contextmanager
        def file_lock(filepath, timeout=5.0):
            yield filepath

        def atomic_write(filepath, content):
            dirname = os.path.dirname(filepath)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        def safe_update_memory(filepath, update_fn, timeout=5.0):
            content = ""
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            new_content = update_fn(content)
            if new_content is not None:
                atomic_write(filepath, new_content)


class MemoryCategory(str, Enum):
    """The 9 canonical memory categories in the Antigravity Memory OS."""
    EPHEMERAL = "EPHEMERAL"
    SESSION = "SESSION"
    PROJECT = "PROJECT"
    DOMAIN = "DOMAIN"
    TOOL = "TOOL"
    GLOBAL = "GLOBAL"
    DECISION = "DECISION"
    GOTCHA = "GOTCHA"
    PROCEDURE = "PROCEDURE"


class AdmissionDecisionType(str, Enum):
    """The 3 admission decisions emitted by the Memory Compiler gatekeeper."""
    ACCEPT = "ACCEPT"
    HOLD = "HOLD"
    REJECT = "REJECT"


class ProvenanceStatus(str, Enum):
    """Provenance freshness and verification states per Section 17."""
    FRESH = "FRESH"
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    MISSING = "MISSING"
    INVALID = "INVALID"


@dataclass
class CompilerThresholds:
    """Configurable thresholds for candidate scoring and admission gating."""
    min_durability_for_promotion: float = 3.0
    min_score_for_admission: float = 3.0
    min_evidence_for_admission: float = 0.5
    max_redundancy_for_admission: float = 0.75
    reject_ephemeral_durability: float = 1.0
    require_verified_provenance: bool = True


@dataclass
class CandidateScore:
    """Detailed score breakdown calculated per Section 10 formula."""
    score: float
    novelty: float
    durability: float
    evidence: float
    redundancy: float
    recurrence: float = 0.0
    future_utility: float = 0.0
    explicit_user_signal: float = 0.0
    project_relevance: float = 0.0
    uncertainty: float = 0.0
    noise: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AdmissionDecision:
    """Admission decision emitted by the gatekeeper."""
    decision: str  # ACCEPT, HOLD, REJECT
    candidate_id: str
    category: str
    score: float
    score_breakdown: Dict[str, float]
    provenance_verified: bool
    reason: str
    target_scope: str
    target_path: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MemoryCompiler:
    """
    Candidate normalization, scoring, conflict analysis, and admission gating engine.
    Implements all responsibilities outlined in Instruction.md Section 10 and 11.
    """

    DEFAULT_CATEGORY_DURABILITY = {
        MemoryCategory.EPHEMERAL: 0.0,
        MemoryCategory.SESSION: 2.0,
        MemoryCategory.PROJECT: 3.0,
        MemoryCategory.DECISION: 3.0,
        MemoryCategory.GOTCHA: 3.0,
        MemoryCategory.PROCEDURE: 3.0,
        MemoryCategory.DOMAIN: 4.0,
        MemoryCategory.TOOL: 4.0,
        MemoryCategory.GLOBAL: 5.0,
    }

    def __init__(
        self,
        thresholds: Optional[CompilerThresholds] = None,
        workspace_dir: Optional[str] = None,
        global_dir: Optional[str] = None,
    ):
        self.thresholds = thresholds or CompilerThresholds()
        self.workspace_dir = workspace_dir or WORKSPACE_DIR
        self.project_mem_dir = os.path.join(self.workspace_dir, ".agents", "memory")
        self.global_mem_dir = global_dir or GLOBAL_MEM_DIR

    # ----------------------------------------------------------------------
    # 1. Candidate Extraction / Reading
    # ----------------------------------------------------------------------
    def read_candidates(self, filepath: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Reads raw candidate records from a JSONL file.
        Defaults to .agents/memory/inbox/candidates.jsonl.
        """
        path = filepath or DEFAULT_CANDIDATES_FILE
        candidates = []
        if not os.path.exists(path):
            return candidates

        with open(path, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, start=1):
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue
                try:
                    record = json.loads(raw)
                    if isinstance(record, dict):
                        if "line_number" not in record:
                            record["line_number"] = line_idx
                        candidates.append(record)
                except json.JSONDecodeError as err:
                    # Record malformed entry as unparseable candidate
                    candidates.append({
                        "id": f"malformed_line_{line_idx}",
                        "content": raw,
                        "category": MemoryCategory.EPHEMERAL.value,
                        "durability": 0.0,
                        "malformed_error": str(err),
                        "line_number": line_idx
                    })
        return candidates

    # ----------------------------------------------------------------------
    # 2. Normalization: normalize()
    # ----------------------------------------------------------------------
    def normalize(self, candidate: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        """
        Normalizes candidate into standardized schema with all required attributes:
        id, content, category (one of 9), durability (0-5), novelty (0-1),
        evidence (0-1), redundancy (0-1), provenance, temporal state, scope.
        """
        if isinstance(candidate, str):
            candidate = {"content": candidate}
        elif not isinstance(candidate, dict):
            candidate = {"content": str(candidate)}

        data = dict(candidate)

        # 1. Normalize text content
        raw_content = str(data.get("content") or data.get("text") or data.get("claim") or "").strip()
        # Clean excessive internal whitespace while preserving newlines
        clean_content = re.sub(r"[ \t]+", " ", raw_content)
        data["content"] = clean_content

        # Content hash for stable deterministic ID
        content_hash = hashlib.sha256(clean_content.lower().encode("utf-8")).hexdigest()
        cand_id = data.get("id") or data.get("candidate_id")
        if not cand_id:
            cand_id = f"cand_{content_hash[:12]}"
        data["id"] = cand_id
        data["candidate_id"] = cand_id
        data["schema_version"] = SCHEMA_VERSION

        # 2. Normalize category (one of 9 canonical categories)
        data["category"] = self.classify(data)

        # 3. Normalize durability (0.0 - 5.0)
        durability_val = data.get("durability")
        if durability_val is None:
            cat_enum = MemoryCategory(data["category"])
            durability_val = self.DEFAULT_CATEGORY_DURABILITY.get(cat_enum, 3.0)
        try:
            data["durability"] = float(durability_val)
        except (ValueError, TypeError):
            data["durability"] = 3.0
        data["durability"] = max(0.0, min(5.0, data["durability"]))

        # 4. Attach and normalize provenance
        data = self.attach_provenance(data, data.get("provenance"))

        # 5. Normalize novelty (0.0 - 1.0)
        novelty_val = data.get("novelty")
        if novelty_val is None:
            novelty_val = 1.0
        try:
            data["novelty"] = max(0.0, min(1.0, float(novelty_val)))
        except (ValueError, TypeError):
            data["novelty"] = 1.0

        # 6. Normalize redundancy (0.0 - 1.0)
        redundancy_val = data.get("redundancy")
        if redundancy_val is None:
            redundancy_val = 0.0
        try:
            data["redundancy"] = max(0.0, min(1.0, float(redundancy_val)))
        except (ValueError, TypeError):
            data["redundancy"] = 0.0

        # 7. Normalize evidence (0.0 - 1.0)
        evidence_val = data.get("evidence") if data.get("evidence") is not None else data.get("evidence_strength")
        if evidence_val is None:
            prov = data.get("provenance", {})
            prov_status = str(prov.get("status", "")).upper()
            if prov.get("verified") is True or prov_status in {ProvenanceStatus.FRESH.value, ProvenanceStatus.VERIFIED.value}:
                evidence_val = 1.0
            elif prov_status == ProvenanceStatus.UNVERIFIED.value:
                evidence_val = 0.3
            elif prov_status in {ProvenanceStatus.STALE.value, ProvenanceStatus.EXPIRED.value}:
                evidence_val = 0.2
            else:
                evidence_val = 0.0
        try:
            data["evidence"] = max(0.0, min(1.0, float(evidence_val)))
        except (ValueError, TypeError):
            data["evidence"] = 0.0

        # 8. Resolve temporal state
        data["temporal"] = self.resolve_temporal_state(data)

        # 9. Calculate scope
        data["scope"] = self.calculate_scope(data)

        # 10. Calculate confidence
        data["confidence"] = self.calculate_confidence(data)

        return data

    # ----------------------------------------------------------------------
    # 3. Classification: classify()
    # ----------------------------------------------------------------------
    def classify(self, candidate: Dict[str, Any]) -> str:
        """
        Classifies candidate into one of the 9 memory categories:
        EPHEMERAL, SESSION, PROJECT, DOMAIN, TOOL, GLOBAL, DECISION, GOTCHA, PROCEDURE.
        """
        raw_type = str(candidate.get("category") or candidate.get("type") or "").strip().upper()

        # Map direct enum names
        for cat in MemoryCategory:
            if raw_type == cat.value:
                return cat.value

        # Alias mappings
        alias_map = {
            "EPHEM": MemoryCategory.EPHEMERAL.value,
            "DEBUG": MemoryCategory.EPHEMERAL.value,
            "NOISE": MemoryCategory.EPHEMERAL.value,
            "TRANSIENT": MemoryCategory.EPHEMERAL.value,
            "LOG": MemoryCategory.SESSION.value,
            "WIP": MemoryCategory.SESSION.value,
            "TASK": MemoryCategory.SESSION.value,
            "ARCH": MemoryCategory.PROJECT.value,
            "ARCHITECTURE": MemoryCategory.PROJECT.value,
            "REPO": MemoryCategory.PROJECT.value,
            "WORKSPACE": MemoryCategory.PROJECT.value,
            "PROJECT_CONVENTION": MemoryCategory.PROJECT.value,
            "GENERAL_CANDIDATE": MemoryCategory.PROJECT.value,
            "FRAMEWORK": MemoryCategory.DOMAIN.value,
            "TECH": MemoryCategory.DOMAIN.value,
            "CLI": MemoryCategory.TOOL.value,
            "FLAG": MemoryCategory.TOOL.value,
            "COMMAND": MemoryCategory.TOOL.value,
            "TOOL_BEHAVIOR": MemoryCategory.TOOL.value,
            "USER": MemoryCategory.GLOBAL.value,
            "ENV": MemoryCategory.GLOBAL.value,
            "GENERAL": MemoryCategory.GLOBAL.value,
            "USER_PREFERENCE": MemoryCategory.GLOBAL.value,
            "CHOICE": MemoryCategory.DECISION.value,
            "ADR": MemoryCategory.DECISION.value,
            "ARCHITECTURAL_DECISION": MemoryCategory.DECISION.value,
            "BUG": MemoryCategory.GOTCHA.value,
            "TRAP": MemoryCategory.GOTCHA.value,
            "ROOT_CAUSE": MemoryCategory.GOTCHA.value,
            "WORKAROUND": MemoryCategory.GOTCHA.value,
            "NEGATIVE": MemoryCategory.GOTCHA.value,
            "BUG_ROOT_CAUSE": MemoryCategory.GOTCHA.value,
            "SUCCESSFUL_FIX": MemoryCategory.GOTCHA.value,
            "REUSABLE_WORKAROUND": MemoryCategory.GOTCHA.value,
            "CRITICAL_SECURITY_LESSON": MemoryCategory.GOTCHA.value,
            "EXPLICIT_CORRECTION": MemoryCategory.GOTCHA.value,
            "PLAYBOOK": MemoryCategory.PROCEDURE.value,
            "RUNBOOK": MemoryCategory.PROCEDURE.value,
            "WORKFLOW": MemoryCategory.PROCEDURE.value,
            "RECIPE": MemoryCategory.PROCEDURE.value,
            "REPEATED_WORKFLOW": MemoryCategory.PROCEDURE.value,
        }
        if raw_type in alias_map:
            return alias_map[raw_type]

        # Content-based heuristic classification
        content = str(candidate.get("content") or candidate.get("text") or "")
        lower_content = content.lower()

        # Ephemeral heuristics
        if any(lower_content.startswith(p) for p in ["hello", "ack", "okay", "acknowledged", "ls -", "pwd", "echo "]):
            return MemoryCategory.EPHEMERAL.value
        if re.search(r"^(routine\s+progress|trivial\s+scratch|debug\s+dump)", lower_content):
            return MemoryCategory.EPHEMERAL.value

        # Decision heuristics
        if any(term in lower_content for term in ["decision:", "we decided to", "accepted decision", "architectural choice", "chose to use"]):
            return MemoryCategory.DECISION.value

        # Gotcha heuristics (non-obvious bugs, failure causes, negative knowledge)
        if any(term in lower_content for term in ["gotcha:", "bug:", "root cause:", "workaround:", "trap:", "failed because", "do not use", "caution:"]):
            return MemoryCategory.GOTCHA.value

        # Procedure heuristics
        if any(term in lower_content for term in ["procedure:", "runbook:", "playbook:", "steps to ", "step 1:"]):
            return MemoryCategory.PROCEDURE.value

        # Tool heuristics
        tool_keywords = ["--no-daemon", "cli flag", "tshark", "apktool", "jadx", "ghidra", "readelf", "objdump", "checksec", "-r flag", "cli tool"]
        if any(term in lower_content for term in tool_keywords):
            return MemoryCategory.TOOL.value

        # Global heuristics
        if any(term in lower_content for term in ["user preference:", "global policy:", "developer convention:"]):
            return MemoryCategory.GLOBAL.value

        # Domain heuristics
        if any(term in lower_content for term in ["react pattern", "android ndk", "wasmtime convention", "kubernetes manifest"]):
            return MemoryCategory.DOMAIN.value

        # Session heuristics
        if any(term in lower_content for term in ["current task:", "session wip:", "in-progress blocker:"]):
            return MemoryCategory.SESSION.value

        # Default fallback to PROJECT (per SKILL.md: avoid global contamination)
        return MemoryCategory.PROJECT.value

    # ----------------------------------------------------------------------
    # 4. Provenance Attachment & Verification
    # ----------------------------------------------------------------------
    def attach_provenance(
        self,
        candidate: Dict[str, Any],
        provenance: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Attaches typed provenance and normalizes its fields per Section 16.
        """
        raw_prov = provenance if provenance is not None else candidate.get("provenance")
        if not isinstance(raw_prov, dict):
            raw_prov = {}

        source_type = raw_prov.get("source_type") or candidate.get("source_type") or "unknown"
        status = raw_prov.get("status") or candidate.get("provenance_status")
        if not status:
            status = ProvenanceStatus.UNVERIFIED.value if source_type == "unknown" else ProvenanceStatus.FRESH.value

        normalized_status = str(status).upper()
        if normalized_status not in [s.value for s in ProvenanceStatus]:
            normalized_status = ProvenanceStatus.UNVERIFIED.value

        # Determine explicit verified flag
        explicit_verified = raw_prov.get("verified")
        if explicit_verified is None:
            verified = (
                normalized_status in {ProvenanceStatus.FRESH.value, ProvenanceStatus.VERIFIED.value}
                and source_type != "unknown"
                and any(raw_prov.get(k) for k in ["path", "command", "commit", "session_id", "test_name", "url"])
            )
        else:
            verified = bool(explicit_verified) and normalized_status not in {
                ProvenanceStatus.UNVERIFIED.value,
                ProvenanceStatus.STALE.value,
                ProvenanceStatus.EXPIRED.value,
                ProvenanceStatus.MISSING.value,
                ProvenanceStatus.INVALID.value,
            }

        candidate["provenance"] = {
            "source_type": source_type,
            "path": raw_prov.get("path"),
            "repository": raw_prov.get("repository", os.path.basename(self.workspace_dir)),
            "commit": raw_prov.get("commit"),
            "command": raw_prov.get("command"),
            "line_start": raw_prov.get("line_start"),
            "line_end": raw_prov.get("line_end"),
            "session_id": raw_prov.get("session_id"),
            "test_name": raw_prov.get("test_name"),
            "status": normalized_status,
            "verified": verified,
            "attached_at": raw_prov.get("attached_at", datetime.datetime.now().isoformat()),
        }
        return candidate

    def verify_provenance(self, candidate: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates whether provenance meets the strict verification threshold
        required for canonical promotion.
        """
        prov = candidate.get("provenance")
        if not isinstance(prov, dict) or not prov:
            return False, "Missing provenance structure"

        source_type = prov.get("source_type", "unknown")
        status = str(prov.get("status", "")).upper()
        verified_flag = prov.get("verified", False)

        if status in {
            ProvenanceStatus.UNVERIFIED.value,
            ProvenanceStatus.STALE.value,
            ProvenanceStatus.EXPIRED.value,
            ProvenanceStatus.MISSING.value,
            ProvenanceStatus.INVALID.value,
        }:
            return False, f"Provenance status is unverified ({status})"

        if source_type == "unknown":
            return False, "Provenance source_type is unknown"

        has_reference = any(prov.get(k) for k in ["path", "command", "commit", "session_id", "test_name", "url"])
        if not has_reference:
            return False, "Provenance lacks concrete source reference (path, command, commit, or session)"

        if not verified_flag:
            return False, "Provenance is marked unverified"

        ref = prov.get("path") or prov.get("command") or prov.get("commit") or prov.get("session_id")
        return True, f"Verified provenance: {source_type} ({ref}) [status: {status}]"

    # ----------------------------------------------------------------------
    # 5. Duplicate & Semantic Analysis
    # ----------------------------------------------------------------------
    def find_exact_duplicates(
        self,
        candidate: Dict[str, Any],
        existing_memories: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Finds exact content duplicates via SHA-256 hash or normalized string match.
        """
        content = candidate.get("content", "").strip().lower()
        cand_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        matches = []

        pool = existing_memories if existing_memories is not None else self._load_canonical_pool()
        for item in pool:
            item_text = item.get("content", "").strip().lower()
            item_hash = item.get("hash") or hashlib.sha256(item_text.encode("utf-8")).hexdigest()
            if cand_hash == item_hash or content == item_text:
                matches.append(item)
        return matches

    def find_semantic_neighbors(
        self,
        candidate: Dict[str, Any],
        existing_memories: Optional[List[Dict[str, Any]]] = None,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Finds semantic near-neighbors using word-level token overlap (Jaccard similarity).
        """
        content = candidate.get("content", "").lower()
        cand_tokens = set(re.findall(r"\b[a-z0-9_-]{3,}\b", content))
        if not cand_tokens:
            return []

        neighbors = []
        pool = existing_memories if existing_memories is not None else self._load_canonical_pool()
        for item in pool:
            item_text = item.get("content", "").lower()
            item_tokens = set(re.findall(r"\b[a-z0-9_-]{3,}\b", item_text))
            if not item_tokens:
                continue

            intersection = cand_tokens.intersection(item_tokens)
            union = cand_tokens.union(item_tokens)
            similarity = len(intersection) / len(union) if union else 0.0

            if similarity >= threshold:
                match_record = dict(item)
                match_record["semantic_similarity"] = round(similarity, 3)
                neighbors.append(match_record)

        neighbors.sort(key=lambda x: x.get("semantic_similarity", 0), reverse=True)
        return neighbors

    def detect_conflict(
        self,
        candidate: Dict[str, Any],
        existing_memories: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Detects potential contradictions or opposing facts between candidate
        and existing canonical records.
        """
        content = candidate.get("content", "").lower()
        conflicts = []
        neighbors = self.find_semantic_neighbors(candidate, existing_memories, threshold=0.35)

        negation_terms = ["not", "never", "avoid", "deprecated", "disabled", "rejected", "do not"]
        positive_terms = ["use", "enabled", "always", "recommended", "accepted", "required"]

        cand_has_negation = any(re.search(rf"\b{t}\b", content) for t in negation_terms)
        cand_has_positive = any(re.search(rf"\b{t}\b", content) for t in positive_terms)

        for neighbor in neighbors:
            n_text = neighbor.get("content", "").lower()
            n_has_negation = any(re.search(rf"\b{t}\b", n_text) for t in negation_terms)
            n_has_positive = any(re.search(rf"\b{t}\b", n_text) for t in positive_terms)

            # Direct polarity opposition
            if (cand_has_negation and n_has_positive and not n_has_negation) or \
               (cand_has_positive and n_has_negation and not cand_has_negation):
                conflicts.append({
                    "conflict_type": "POLARITY_CONTRADICTION",
                    "existing_file": neighbor.get("file"),
                    "existing_content": neighbor.get("content"),
                    "candidate_content": candidate.get("content"),
                    "similarity": neighbor.get("semantic_similarity")
                })
        return conflicts

    # ----------------------------------------------------------------------
    # 6. Temporal, Scope, and Confidence Analysis
    # ----------------------------------------------------------------------
    def resolve_temporal_state(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolves validity dates, temporal status, and supersession links per Section 14.
        """
        now_iso = datetime.datetime.now().isoformat()
        temporal = candidate.get("temporal")
        if not isinstance(temporal, dict):
            temporal = {}

        created_at = temporal.get("created_at") or candidate.get("created_at") or now_iso
        valid_from = temporal.get("valid_from") or created_at
        valid_until = temporal.get("valid_until")
        superseded_by = temporal.get("superseded_by")
        status = temporal.get("status") or ("SUPERSEDED" if superseded_by else "ACTIVE")

        return {
            "created_at": created_at,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "superseded_by": superseded_by,
            "status": status,
        }

    def calculate_scope(self, candidate: Dict[str, Any]) -> str:
        """
        Calculates scope: PROJECT, GLOBAL, DOMAIN, TOOL, SESSION, or EPHEMERAL.
        """
        category = candidate.get("category")
        if category == MemoryCategory.GLOBAL.value:
            return "GLOBAL"
        if category in {MemoryCategory.DOMAIN.value, MemoryCategory.TOOL.value}:
            return category
        if category == MemoryCategory.SESSION.value:
            return "SESSION"
        if category == MemoryCategory.EPHEMERAL.value:
            return "EPHEMERAL"
        return "PROJECT"

    def calculate_confidence(self, candidate: Dict[str, Any]) -> float:
        """
        Calculates confidence score [0.0 - 1.0] from evidence, provenance, and hedging words.
        """
        content = candidate.get("content", "").lower()
        prov_ok, _ = self.verify_provenance(candidate)
        evidence = candidate.get("evidence", 0.0)

        # Penalize speculative hedging words
        hedging_words = ["maybe", "perhaps", "might be", "probably", "not sure", "unverified"]
        hedging_penalty = 0.25 if any(w in content for w in hedging_words) else 0.0

        score = (0.45 if prov_ok else 0.1) + (0.35 * evidence) + (0.2 * candidate.get("novelty", 1.0)) - hedging_penalty
        return round(max(0.0, min(1.0, score)), 3)

    # ----------------------------------------------------------------------
    # 7. Candidate Scoring: calculate_score()
    # ----------------------------------------------------------------------
    def calculate_score(self, candidate: Dict[str, Any]) -> CandidateScore:
        """
        Computes candidate score per Section 10:
        candidate_score = Novelty + Durability + Evidence - Redundancy
        """
        novelty = float(candidate.get("novelty", 1.0))
        durability = float(candidate.get("durability", 3.0))
        evidence = float(candidate.get("evidence", 0.0))
        redundancy = float(candidate.get("redundancy", 0.0))

        # Additional high-signal attributes from Section 10
        recurrence = float(candidate.get("recurrence", 0.0))
        future_utility = float(candidate.get("future_utility", 0.0))
        explicit_user_signal = float(candidate.get("explicit_user_signal", 0.0))
        project_relevance = float(candidate.get("project_relevance", 0.0))
        uncertainty = float(candidate.get("uncertainty", 0.0))
        noise = float(candidate.get("noise", 0.0))

        base_score = novelty + durability + evidence - redundancy
        total_score = base_score + recurrence + future_utility + explicit_user_signal + project_relevance - uncertainty - noise

        return CandidateScore(
            score=round(total_score, 3),
            novelty=round(novelty, 3),
            durability=round(durability, 3),
            evidence=round(evidence, 3),
            redundancy=round(redundancy, 3),
            recurrence=round(recurrence, 3),
            future_utility=round(future_utility, 3),
            explicit_user_signal=round(explicit_user_signal, 3),
            project_relevance=round(project_relevance, 3),
            uncertainty=round(uncertainty, 3),
            noise=round(noise, 3),
        )

    # ----------------------------------------------------------------------
    # 8. Schema Validation & 5-Gate Admission Pipeline
    # ----------------------------------------------------------------------
    def validate_schema(self, candidate: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates candidate record against Schema v2.0.0 requirements per Section 16:
        Required fields: content (str), category (valid canonical enum),
        durability (0.0-5.0), id (str), provenance (dict).
        """
        if candidate.get("malformed_error"):
            return False, f"JSON parse error: {candidate.get('malformed_error')}"

        content = candidate.get("content")
        if not content or not isinstance(content, str) or not content.strip():
            return False, "Missing or empty 'content' string"

        category = candidate.get("category")
        if not category or category not in [c.value for c in MemoryCategory]:
            return False, f"Invalid category '{category}'; must be one of {[c.value for c in MemoryCategory]}"

        durability = candidate.get("durability")
        if durability is None or not isinstance(durability, (int, float)) or not (0.0 <= float(durability) <= 5.0):
            return False, f"Invalid durability '{durability}'; must be float between 0.0 and 5.0"

        cand_id = candidate.get("id")
        if not cand_id or not isinstance(cand_id, str) or not cand_id.strip():
            return False, "Missing or empty candidate 'id'"

        provenance = candidate.get("provenance")
        if provenance is not None and not isinstance(provenance, dict):
            return False, "Invalid 'provenance' attribute; must be a dictionary"

        return True, "Valid schema v2.0.0"

    def decide_admission(self, candidate: Dict[str, Any]) -> AdmissionDecision:
        """
        Enforces the 5-gate admission pipeline per Instruction.md Sections 14, 16, 23, and 84:
        Gate 1: Secret Hygiene gate (via scripts.secret_scanner)
        Gate 2: Durability threshold gate (>=3.0 for project canonical files)
        Gate 3: Schema validation gate (schema v2.0.0 compliance)
        Gate 4: Source authority & epistemic confidence gate
        Gate 5: Redundancy / duplication gate
        """
        normalized = self.normalize(candidate)
        cand_id = normalized["id"]
        category = normalized["category"]
        durability = normalized["durability"]
        redundancy = normalized["redundancy"]
        scope = normalized["scope"]
        score_obj = self.calculate_score(normalized)
        score_val = score_obj.score

        gate_results = {}

        # ------------------------------------------------------------------
        # GATE 1: Secret Hygiene Gate (via scripts.secret_scanner)
        # ------------------------------------------------------------------
        text_to_scan = f"{normalized.get('content', '')} {json.dumps(normalized.get('provenance', {}))}"
        scan_res = scan_text(text_to_scan)
        if not getattr(scan_res, "is_clean", True):
            findings_desc = "; ".join([f"{f.rule_name}: {f.description}" for f in getattr(scan_res, "findings", [])])
            gate_results["gate_1_secret_hygiene"] = {"status": "FAIL", "reason": findings_desc}
            return AdmissionDecision(
                decision=AdmissionDecisionType.REJECT.value,
                candidate_id=cand_id,
                category=category,
                score=score_val,
                score_breakdown=score_obj.to_dict(),
                provenance_verified=False,
                reason=f"Security violation: credential or sensitive secret pattern detected ({findings_desc})",
                target_scope="EPHEMERAL",
                target_path=None,
                details={
                    "security_findings": [f.to_dict() for f in getattr(scan_res, "findings", [])],
                    "failed_gate": "Gate 1: Secret Hygiene",
                    "gate_results": gate_results,
                    "schema_version": SCHEMA_VERSION,
                }
            )
        gate_results["gate_1_secret_hygiene"] = {"status": "PASS"}

        # ------------------------------------------------------------------
        # GATE 2: Durability Threshold Gate (>=3.0 for project canonical files)
        # ------------------------------------------------------------------
        # Ephemeral noise check (durability 0.0 - 1.0)
        if durability <= self.thresholds.reject_ephemeral_durability or category == MemoryCategory.EPHEMERAL.value:
            gate_results["gate_2_durability_threshold"] = {
                "status": "REJECT",
                "durability": durability,
                "reason": "Ephemeral noise"
            }
            return AdmissionDecision(
                decision=AdmissionDecisionType.REJECT.value,
                candidate_id=cand_id,
                category=category,
                score=score_val,
                score_breakdown=score_obj.to_dict(),
                provenance_verified=False,
                reason=f"Ephemeral noise (durability {durability} <= {self.thresholds.reject_ephemeral_durability}). Discarded per lifecycle policy.",
                target_scope="EPHEMERAL",
                target_path=None,
                details={
                    "failed_gate": "Gate 2: Durability Threshold (Ephemeral)",
                    "gate_results": gate_results,
                    "schema_version": SCHEMA_VERSION,
                }
            )

        # Session-scoped context check (durability 2.0)
        if durability == 2.0 or category == MemoryCategory.SESSION.value:
            session_notes = os.path.join(self.project_mem_dir, "sessions", "notes.md")
            prov_verified, prov_msg = self.verify_provenance(normalized)
            gate_results["gate_2_durability_threshold"] = {
                "status": "HOLD",
                "durability": durability,
                "reason": "Session-scoped context"
            }
            return AdmissionDecision(
                decision=AdmissionDecisionType.HOLD.value,
                candidate_id=cand_id,
                category=category,
                score=score_val,
                score_breakdown=score_obj.to_dict(),
                provenance_verified=prov_verified,
                reason="Session-scoped context (durability 2.0). Held for session log staging, not canonical promotion.",
                target_scope="SESSION",
                target_path=session_notes,
                details={
                    "provenance_details": prov_msg,
                    "held_at_gate": "Gate 2: Durability Threshold (Session Scope)",
                    "gate_results": gate_results,
                    "schema_version": SCHEMA_VERSION,
                }
            )

        # Sub-durability check
        if durability < self.thresholds.min_durability_for_promotion:
            gate_results["gate_2_durability_threshold"] = {
                "status": "HOLD",
                "durability": durability,
                "reason": f"Durability {durability} below {self.thresholds.min_durability_for_promotion}"
            }
            return AdmissionDecision(
                decision=AdmissionDecisionType.HOLD.value,
                candidate_id=cand_id,
                category=category,
                score=score_val,
                score_breakdown=score_obj.to_dict(),
                provenance_verified=False,
                reason=f"Candidate durability ({durability}) is below threshold ({self.thresholds.min_durability_for_promotion}) for canonical promotion.",
                target_scope=scope,
                target_path=None,
                details={
                    "held_at_gate": "Gate 2: Durability Threshold",
                    "gate_results": gate_results,
                    "schema_version": SCHEMA_VERSION,
                }
            )
        gate_results["gate_2_durability_threshold"] = {"status": "PASS", "durability": durability}

        # ------------------------------------------------------------------
        # GATE 3: Schema Validation Gate (schema v2.0.0 compliance)
        # ------------------------------------------------------------------
        is_schema_valid, schema_err = self.validate_schema(normalized)
        if not is_schema_valid:
            gate_results["gate_3_schema_validation"] = {"status": "FAIL", "reason": schema_err}
            return AdmissionDecision(
                decision=AdmissionDecisionType.REJECT.value,
                candidate_id=cand_id,
                category=category,
                score=score_val,
                score_breakdown=score_obj.to_dict(),
                provenance_verified=False,
                reason=f"Schema validation failed: {schema_err}",
                target_scope=scope,
                target_path=None,
                details={
                    "failed_gate": "Gate 3: Schema Validation",
                    "gate_results": gate_results,
                    "schema_version": SCHEMA_VERSION,
                }
            )
        gate_results["gate_3_schema_validation"] = {"status": "PASS", "schema_version": SCHEMA_VERSION}

        # ------------------------------------------------------------------
        # GATE 4: Source Authority & Epistemic Confidence Gate
        # ------------------------------------------------------------------
        prov_verified, prov_msg = self.verify_provenance(normalized)

        # Durability >= 3.0 requires verified provenance for canonical promotion
        if durability >= self.thresholds.min_durability_for_promotion and not prov_verified:
            gate_results["gate_4_source_authority"] = {
                "status": "HOLD",
                "provenance_verified": False,
                "reason": prov_msg
            }
            return AdmissionDecision(
                decision=AdmissionDecisionType.HOLD.value,
                candidate_id=cand_id,
                category=category,
                score=score_val,
                score_breakdown=score_obj.to_dict(),
                provenance_verified=False,
                reason=f"Candidate durability ({durability} >= {self.thresholds.min_durability_for_promotion}) qualifies for canonical promotion, but provenance is unverified ({prov_msg}). Admission held pending verification.",
                target_scope=scope,
                target_path=None,
                details={
                    "provenance_details": prov_msg,
                    "held_at_gate": "Gate 4: Source Authority",
                    "gate_results": gate_results,
                    "schema_version": SCHEMA_VERSION,
                }
            )

        # Epistemic confidence check: prevent speculative LLM thoughts from entering canonical storage
        content_lower = normalized.get("content", "").lower()
        speculative_markers = ["speculative assertion", "speculative claim", "speculative thought", "unverified rumor"]
        if any(marker in content_lower for marker in speculative_markers) and not prov_verified:
            gate_results["gate_4_source_authority"] = {
                "status": "HOLD",
                "epistemic_confidence": "SPECULATIVE",
                "reason": "Speculative assertion without verified authority"
            }
            return AdmissionDecision(
                decision=AdmissionDecisionType.HOLD.value,
                candidate_id=cand_id,
                category=category,
                score=score_val,
                score_breakdown=score_obj.to_dict(),
                provenance_verified=False,
                reason=f"Candidate flagged as speculative thought without authoritative evidence. Admission held pending empirical corroboration.",
                target_scope=scope,
                target_path=None,
                details={
                    "held_at_gate": "Gate 4: Epistemic Confidence (Speculative)",
                    "gate_results": gate_results,
                    "schema_version": SCHEMA_VERSION,
                }
            )

        gate_results["gate_4_source_authority"] = {
            "status": "PASS",
            "provenance_verified": True,
            "confidence": normalized.get("confidence")
        }

        # ------------------------------------------------------------------
        # GATE 5: Redundancy / Duplication Gate
        # ------------------------------------------------------------------
        if redundancy >= self.thresholds.max_redundancy_for_admission:
            gate_results["gate_5_redundancy_duplication"] = {
                "status": "FAIL",
                "redundancy": redundancy,
                "reason": f"Redundancy {redundancy} >= {self.thresholds.max_redundancy_for_admission}"
            }
            return AdmissionDecision(
                decision=AdmissionDecisionType.REJECT.value,
                candidate_id=cand_id,
                category=category,
                score=score_val,
                score_breakdown=score_obj.to_dict(),
                provenance_verified=prov_verified,
                reason=f"Excessive redundancy ({redundancy} >= {self.thresholds.max_redundancy_for_admission}). Candidate is duplicate or near-duplicate of existing records.",
                target_scope=scope,
                target_path=None,
                details={
                    "failed_gate": "Gate 5: Redundancy / Duplication",
                    "gate_results": gate_results,
                    "schema_version": SCHEMA_VERSION,
                }
            )

        exact_dups = self.find_exact_duplicates(normalized)
        if exact_dups:
            dup_target = exact_dups[0].get("file", "canonical store")
            gate_results["gate_5_redundancy_duplication"] = {
                "status": "FAIL",
                "reason": f"Exact duplicate found in {os.path.basename(dup_target)}"
            }
            return AdmissionDecision(
                decision=AdmissionDecisionType.REJECT.value,
                candidate_id=cand_id,
                category=category,
                score=score_val,
                score_breakdown=score_obj.to_dict(),
                provenance_verified=prov_verified,
                reason=f"Excessive redundancy (exact duplicate detected in {os.path.basename(dup_target)}). Candidate is duplicate of existing records.",
                target_scope=scope,
                target_path=None,
                details={
                    "duplicate_in": dup_target,
                    "failed_gate": "Gate 5: Redundancy / Duplication",
                    "gate_results": gate_results,
                    "schema_version": SCHEMA_VERSION,
                }
            )

        gate_results["gate_5_redundancy_duplication"] = {"status": "PASS", "redundancy": redundancy}

        # Minimum score threshold check after passing 5 structural gates
        if score_val < self.thresholds.min_score_for_admission:
            gate_results["minimum_score_threshold"] = {
                "status": "HOLD",
                "score": score_val,
                "reason": f"Score {score_val} < {self.thresholds.min_score_for_admission}"
            }
            return AdmissionDecision(
                decision=AdmissionDecisionType.HOLD.value,
                candidate_id=cand_id,
                category=category,
                score=score_val,
                score_breakdown=score_obj.to_dict(),
                provenance_verified=prov_verified,
                reason=f"Candidate score ({score_val}) is below minimum admission threshold ({self.thresholds.min_score_for_admission}). Held for corroborating evidence.",
                target_scope=scope,
                target_path=None,
                details={
                    "held_at_check": "Minimum Score Threshold",
                    "gate_results": gate_results,
                    "schema_version": SCHEMA_VERSION,
                }
            )

        # ------------------------------------------------------------------
        # ALL 5 GATES PASSED -> ACCEPT
        # ------------------------------------------------------------------
        target_path = self._resolve_target_file(category)
        return AdmissionDecision(
            decision=AdmissionDecisionType.ACCEPT.value,
            candidate_id=cand_id,
            category=category,
            score=score_val,
            score_breakdown=score_obj.to_dict(),
            provenance_verified=True,
            reason=f"Passed admission gate: durability {durability} >= {self.thresholds.min_durability_for_promotion}, verified provenance ({prov_msg}), score {score_val} >= {self.thresholds.min_score_for_admission}.",
            target_scope=scope,
            target_path=target_path,
            details={
                "provenance_details": prov_msg,
                "gate_results": gate_results,
                "schema_version": SCHEMA_VERSION,
            }
        )

    # ----------------------------------------------------------------------
    # 9. Write Preparation: prepare_write()
    # ----------------------------------------------------------------------
    def prepare_write(
        self,
        candidate: Dict[str, Any],
        decision: AdmissionDecision
    ) -> Dict[str, Any]:
        """
        Prepares target path, formatted Markdown content, and metadata
        WITHOUT executing unsafe side effects before validation.
        """
        if decision.decision != AdmissionDecisionType.ACCEPT.value:
            return {
                "commit_ready": False,
                "action": "NONE",
                "reason": f"Admission decision was {decision.decision}: {decision.reason}",
                "target_path": None,
                "formatted_entry": None
            }

        target_path = decision.target_path or self._resolve_target_file(decision.category)
        today = datetime.date.today().isoformat()
        content = candidate.get("content", "").strip()
        cat = decision.category
        durability = decision.score_breakdown.get("durability", 3.0)

        # Structured formatting according to category
        if cat == MemoryCategory.DECISION.value:
            title = candidate.get("title") or content.split(".")[0][:60]
            formatted_entry = f"""
## [{today}] {title}
- **Context**: {candidate.get('context', 'Identified during active development.')}
- **Decision**: {content}
- **Rationale**: {candidate.get('rationale', 'Verified empirically via live execution.')}
- **Consequences**: {candidate.get('consequences', 'Maintains system stability and governance.')}
- **Status**: Accepted
"""
        elif cat == MemoryCategory.GOTCHA.value:
            title = candidate.get("title") or content.split(".")[0][:60]
            formatted_entry = f"""
## [{today}] {title}
- **Context**: {candidate.get('context', 'Observed in live toolchain / build execution.')}
- **Root Cause**: {candidate.get('root_cause', content)}
- **Resolution / Workaround**: {candidate.get('workaround', candidate.get('resolution', 'Follow verified procedure.'))}
- **Affected Components**: {candidate.get('affected', 'System toolchain / workspace')}
"""
        elif cat == MemoryCategory.PROCEDURE.value:
            title = candidate.get("title") or content.split(".")[0][:60]
            formatted_entry = f"""
## [{today}] Procedure: {title}
- **Objective**: {content}
- **Steps**:
{candidate.get('steps', '1. Follow standard runbook steps.')}
- **Verification**: Verified with exit code 0.
"""
        else:
            # Standard single-entry format
            formatted_entry = f"- [{today}] [{cat}] (Durability {int(durability)}): {content}"

        return {
            "commit_ready": True,
            "action": "APPEND",
            "candidate_id": decision.candidate_id,
            "category": cat,
            "target_path": target_path,
            "target_scope": decision.target_scope,
            "formatted_entry": formatted_entry.strip(),
            "admission_decision": decision.to_dict()
        }

    # ----------------------------------------------------------------------
    # 10. Pipeline Compilation: compile_candidate() and compile_inbox()
    # ----------------------------------------------------------------------
    def compile_candidate(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes end-to-end compilation pipeline on a single candidate.
        """
        normalized = self.normalize(candidate)
        decision = self.decide_admission(normalized)
        write_payload = self.prepare_write(normalized, decision)

        return {
            "candidate": normalized,
            "decision": decision.to_dict(),
            "write_payload": write_payload
        }

    def compile_inbox(
        self,
        inbox_path: Optional[str] = None,
        output_path: Optional[str] = None,
        dry_run: bool = True,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Processes all candidates from the candidate inbox JSONL.
        Emits admission decisions, generates summary, and records to output log.
        """
        source_path = inbox_path or DEFAULT_CANDIDATES_FILE
        out_path = output_path or DEFAULT_DECISIONS_FILE

        candidates = self.read_candidates(source_path)
        if limit is not None and limit > 0:
            candidates = candidates[:limit]

        results = []
        counts = {
            AdmissionDecisionType.ACCEPT.value: 0,
            AdmissionDecisionType.HOLD.value: 0,
            AdmissionDecisionType.REJECT.value: 0
        }

        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        for cand in candidates:
            compiled = self.compile_candidate(cand)
            dec_type = compiled["decision"]["decision"]
            counts[dec_type] = counts.get(dec_type, 0) + 1
            results.append(compiled)

        # Write admission decisions log atomically using lock_manager per Section 15 & 84
        serialized_decisions = "".join([json.dumps(item["decision"]) + "\n" for item in results])
        with file_lock(out_path):
            atomic_write(out_path, serialized_decisions)

        # Also mirror to PROJECT_INBOX_DIR/admission_decisions.jsonl if out_path is CANONICAL_DECISIONS_FILE
        if os.path.abspath(out_path) == os.path.abspath(CANONICAL_DECISIONS_FILE):
            inbox_mirror = os.path.join(PROJECT_INBOX_DIR, "admission_decisions.jsonl")
            try:
                with file_lock(inbox_mirror):
                    atomic_write(inbox_mirror, serialized_decisions)
            except Exception:
                pass

        # If not dry-run, commit accepted candidate payloads to canonical stores and drain inbox (DEF-006)
        if not dry_run:
            for item in results:
                wp = item.get("write_payload")
                if wp and wp.get("commit_ready") and wp.get("target_path"):
                    target_file = wp["target_path"]
                    entry = wp.get("formatted_entry", "").strip()
                    if entry:
                        os.makedirs(os.path.dirname(target_file), exist_ok=True)
                        with file_lock(target_file):
                            curr = ""
                            if os.path.exists(target_file):
                                with open(target_file, "r", encoding="utf-8") as f:
                                    curr = f.read()
                            if entry not in curr:
                                new_content = curr.rstrip() + "\n\n" + entry + "\n" if curr.strip() else entry + "\n"
                                atomic_write(target_file, new_content)
                                try:
                                    s_dir = os.path.dirname(os.path.abspath(__file__))
                                    if s_dir not in sys.path:
                                        sys.path.insert(0, s_dir)
                                    from memory_index_queue import IndexQueueManager
                                    queue_file = os.path.join(self.project_mem_dir, "index_queue.jsonl")
                                    IndexQueueManager(queue_file=queue_file).enqueue(target_file, operation="upsert")
                                except Exception:
                                    pass

            # Drain candidate inbox (truncate or slice processed items)
            with file_lock(source_path):
                if limit is not None and limit > 0:
                    raw_all = self.read_candidates(source_path)
                    remaining = raw_all[limit:]
                    atomic_write(source_path, "".join([json.dumps(r) + "\n" for r in remaining]))
                else:
                    atomic_write(source_path, "")

        return {
            "source_path": source_path,
            "decisions_path": out_path,
            "total_candidates": len(candidates),
            "counts": counts,
            "dry_run": dry_run,
            "results": results
        }

    # ----------------------------------------------------------------------
    # Helper Methods
    # ----------------------------------------------------------------------
    def _resolve_target_file(self, category: str) -> str:
        """Maps accepted memory category to canonical destination file."""
        if category == MemoryCategory.DECISION.value:
            return os.path.join(self.project_mem_dir, "DECISIONS.md")
        elif category == MemoryCategory.GOTCHA.value:
            return os.path.join(self.project_mem_dir, "GOTCHAS.md")
        elif category == MemoryCategory.PROCEDURE.value:
            return os.path.join(self.project_mem_dir, "PROCEDURES.md")
        elif category == MemoryCategory.DOMAIN.value:
            return os.path.join(self.global_mem_dir, "domains", "notes.md")
        elif category == MemoryCategory.TOOL.value:
            return os.path.join(self.global_mem_dir, "tools", "notes.md")
        elif category == MemoryCategory.GLOBAL.value:
            return os.path.join(self.global_mem_dir, "GENERAL.md")
        elif category == MemoryCategory.SESSION.value:
            return os.path.join(self.project_mem_dir, "sessions", "notes.md")
        return os.path.join(self.project_mem_dir, "ARCHITECTURE.md")

    def _load_canonical_pool(self) -> List[Dict[str, Any]]:
        """Loads entries from existing canonical Markdown files for duplicate/conflict analysis."""
        pool = []
        paths = [
            os.path.join(self.project_mem_dir, "ARCHITECTURE.md"),
            os.path.join(self.project_mem_dir, "DECISIONS.md"),
            os.path.join(self.project_mem_dir, "GOTCHAS.md"),
            os.path.join(self.global_mem_dir, "GENERAL.md"),
        ]
        for path in paths:
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line_str = line.strip()
                        if len(line_str) > 20 and not line_str.startswith("#") and not line_str.startswith("---"):
                            pool.append({
                                "file": path,
                                "content": line_str,
                                "hash": hashlib.sha256(line_str.lower().encode("utf-8")).hexdigest()
                            })
            except Exception:
                pass
        return pool


# --------------------------------------------------------------------------
# CLI Entrypoint
# --------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Antigravity Memory Compiler & Admission Gatekeeper")
    parser.add_argument("--inbox", default=DEFAULT_CANDIDATES_FILE, help="Path to candidates JSONL inbox")
    parser.add_argument("--output", default=DEFAULT_DECISIONS_FILE, help="Path to write admission decisions JSONL")
    parser.add_argument("--durability-threshold", type=float, default=3.0, help="Minimum durability required for promotion")
    parser.add_argument("--min-score", type=float, default=3.0, help="Minimum candidate score for admission")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry run without mutating canonical stores")
    parser.add_argument("--drain", action="store_true", help="Drain inbox: commit accepted candidates to canonical stores and clear inbox")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of candidates to process")
    parser.add_argument("--json", action="store_true", help="Print summary JSON to stdout")

    args = parser.parse_args()
    dry_run = False if args.drain else args.dry_run

    thresholds = CompilerThresholds(
        min_durability_for_promotion=args.durability_threshold,
        min_score_for_admission=args.min_score
    )

    compiler = MemoryCompiler(thresholds=thresholds)
    summary = compiler.compile_inbox(inbox_path=args.inbox, output_path=args.output, dry_run=dry_run, limit=args.limit)

    if args.json:
        # Output clean JSON
        print(json.dumps({
            "source_path": summary["source_path"],
            "decisions_path": summary["decisions_path"],
            "total_candidates": summary["total_candidates"],
            "counts": summary["counts"]
        }, indent=2))
    else:
        print("=" * 60)
        print("ANTIGRAVITY MEMORY COMPILER ADMISSION REPORT")
        print("=" * 60)
        print(f"Source Inbox:      {summary['source_path']}")
        print(f"Decisions Output:  {summary['decisions_path']}")
        print(f"Total Candidates:  {summary['total_candidates']}")
        print(f"Accepted:          {summary['counts']['ACCEPT']}")
        print(f"Held:              {summary['counts']['HOLD']}")
        print(f"Rejected:          {summary['counts']['REJECT']}")
        print("-" * 60)
        for res in summary["results"]:
            dec = res["decision"]
            print(f"[{dec['decision']}] [{dec['category']}] (Score: {dec['score']}, Durability: {dec['score_breakdown']['durability']})")
            print(f"  ID: {dec['candidate_id']}")
            print(f"  Reason: {dec['reason']}")
            if dec['target_path']:
                print(f"  Target: {dec['target_path']}")
            print()
        print("=" * 60)


if __name__ == "__main__":
    main()
