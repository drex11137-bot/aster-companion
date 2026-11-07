#!/usr/bin/env python3
"""
Memory Reconciler for Antigravity Persistent Memory.
Implements memory reconciliation, conflict resolution, bitemporality, and rollback
per Instruction.md Sections 12, 14, 15, and 84.

Key Capabilities:
1. Compares candidate memories against canonical records in .agents/memory/.
2. Distinguishes duplicate, refinement, complement, and true contradiction.
3. Applies bitemporal semantics:
   - observed_at: when the fact occurred / was observed
   - recorded_at: when the system recorded it
   - valid_from: start of domain validity
   - valid_until: end of domain validity (None when active)
   - supersedes: list of replaced record IDs
4. Marks superseded canonical facts with:
   [SUPERSEDED on YYYY-MM-DD by id:XYZ]
   without destroying historical context or evidence.
5. Logs transactions to:
   .agents/memory-upgrade/decisions/reconciliation_log.jsonl
   to support full atomic rollback.
6. Bitemporal time-travel querying (what was true at time T, what did we believe at time T).
"""

import os
import sys
import re
import json
import uuid
import difflib
import hashlib
import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field, asdict

# Add scripts directory to path for sibling imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from secret_scanner import scan_text
except ImportError:
    class DummyScanResult:
        is_clean = True
        findings = []
    def scan_text(t, target_name=None):
        return DummyScanResult()

try:
    from lock_manager import file_lock, atomic_write
except ImportError:
    from contextlib import contextmanager
    @contextmanager
    def file_lock(filepath, timeout=5.0):
        yield f"{filepath}.lock"

    def atomic_write(filepath, content):
        import tempfile
        dirname = os.path.dirname(filepath) or '.'
        os.makedirs(dirname, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=dirname, prefix="atomic_", suffix=".tmp")
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp_path, filepath)

try:
    from memory_index_queue import IndexQueueManager
except ImportError:
    try:
        from scripts.memory_index_queue import IndexQueueManager
    except ImportError:
        IndexQueueManager = None

try:
    from memory_compiler import MemoryCompiler, AdmissionDecisionType
except ImportError:
    try:
        from scripts.memory_compiler import MemoryCompiler, AdmissionDecisionType
    except ImportError:
        MemoryCompiler = None
        AdmissionDecisionType = None


# ============================================================================
# Enums and Data Models
# ============================================================================

class ReconciliationAction(str, Enum):
    ADD = "ADD"
    NOOP = "NOOP"
    MERGE = "MERGE"
    UPDATE = "UPDATE"
    SUPERSEDE = "SUPERSEDE"
    HOLD = "HOLD"
    REJECT = "REJECT"
    ARCHIVE = "ARCHIVE"
    ROLLBACK = "ROLLBACK"


class ConflictClassification(str, Enum):
    DUPLICATE = "DUPLICATE"
    REFINEMENT = "REFINEMENT"
    COMPLEMENT = "COMPLEMENT"
    CONTRADICTION = "CONTRADICTION"
    NEW_FACT = "NEW_FACT"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    EPHEMERAL_DISCARD = "EPHEMERAL_DISCARD"


@dataclass
class CandidateMemory:
    id: str = field(default_factory=lambda: f"cand-{datetime.date.today().isoformat()}-{uuid.uuid4().hex[:8]}")
    type: str = "PROJECT"  # EPHEMERAL, SESSION, PROJECT, DOMAIN, TOOL, GLOBAL, DECISION, GOTCHA, PROCEDURE
    scope: str = "PROJECT"
    title: str = ""
    content: str = ""
    target_file: Optional[str] = None
    durability: int = 3
    confidence: str = "VERIFIED"
    source: str = "live execution"
    evidence: str = ""
    context: str = ""  # Environment, platform, pre-conditions (e.g. "production", "local development")
    observed_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    recorded_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    valid_from: str = field(default_factory=lambda: datetime.date.today().isoformat())
    valid_until: Optional[str] = None
    supersedes: List[str] = field(default_factory=list)
    git_commit: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CanonicalRecord:
    id: str
    file_path: str
    title: str
    type: str
    scope: str
    status: str  # ACTIVE, SUPERSEDED, DEPRECATED, REVIEW
    content: str
    raw_text: str
    line_start: int
    line_end: int
    core_claim: str = ""  # Primary assertion (e.g. ### What section)
    confidence: str = "VERIFIED"
    source: str = "unknown"
    context: str = ""
    observed_at: Optional[str] = None
    recorded_at: Optional[str] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    supersedes: List[str] = field(default_factory=list)
    superseded_by: Optional[str] = None
    superseded_date: Optional[str] = None
    superseded_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_active(self) -> bool:
        return self.status.upper() == "ACTIVE" and not self.superseded_by


@dataclass
class ReconciliationResult:
    candidate_id: str
    action: ReconciliationAction
    classification: ConflictClassification
    reason: str
    target_file: str
    superseded_records: List[str] = field(default_factory=list)
    merged_record_id: Optional[str] = None
    transaction_id: Optional[str] = None
    success: bool = True
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["action"] = self.action.value
        d["classification"] = self.classification.value
        return d


# ============================================================================
# Memory Reconciler Class
# ============================================================================

class MemoryReconciler:
    """
    Autonomous Memory Reconciler implementing Section 12, 14, 15, and 84.
    """

    DEFAULT_WORKSPACE = "/workspaces/codespaces-blank"
    DEFAULT_MEMORY_DIR = os.path.join(DEFAULT_WORKSPACE, ".agents", "memory")
    DEFAULT_LOG_FILE = os.path.join(
        DEFAULT_WORKSPACE, ".agents", "memory-upgrade", "decisions", "reconciliation_log.jsonl"
    )

    def __init__(
        self,
        memory_dir: Optional[str] = None,
        log_file: Optional[str] = None,
        workspace_dir: Optional[str] = None,
        index_queue_manager: Optional[Any] = None,
    ):
        self.workspace_dir = workspace_dir or self.DEFAULT_WORKSPACE
        self.memory_dir = memory_dir or os.path.join(self.workspace_dir, ".agents", "memory")
        self.log_file = log_file or os.path.join(
            self.workspace_dir, ".agents", "memory-upgrade", "decisions", "reconciliation_log.jsonl"
        )
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        os.makedirs(self.memory_dir, exist_ok=True)

        if index_queue_manager is not None:
            self.index_queue_manager = index_queue_manager
        elif IndexQueueManager is not None:
            queue_file = os.path.join(self.memory_dir, "index_queue.jsonl")
            health_file = os.path.join(self.memory_dir, "index_health.json")
            lease_file = os.path.join(self.memory_dir, "index_writer.lease")
            try:
                self.index_queue_manager = IndexQueueManager(
                    queue_file=queue_file,
                    health_file=health_file,
                    lease_file=lease_file,
                )
            except Exception:
                self.index_queue_manager = None
        else:
            self.index_queue_manager = None

    # ------------------------------------------------------------------------
    # Parsing Canonical Records from .agents/memory/
    # ------------------------------------------------------------------------

    def scan_canonical_records(self, target_file: Optional[str] = None) -> List[CanonicalRecord]:
        """
        Scans and parses canonical markdown files in memory_dir.
        Extracts structured records, headings, bitemporal tags, and status.
        """
        files_to_scan = []
        if target_file:
            files_to_scan = [target_file]
        else:
            if os.path.exists(self.memory_dir):
                for f in os.listdir(self.memory_dir):
                    if f.endswith(".md") and f not in ("INDEX.md", "CURRENT.md"):
                        files_to_scan.append(os.path.join(self.memory_dir, f))

        records: List[CanonicalRecord] = []
        for file_path in files_to_scan:
            if not os.path.exists(file_path):
                continue
            records.extend(self._parse_file_records(file_path))

        return records

    def _parse_file_records(self, file_path: str) -> List[CanonicalRecord]:
        """Parses individual markdown records from a canonical memory file."""
        records = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        lines = content.splitlines()
        section_starts = []
        for idx, line in enumerate(lines):
            if line.startswith("## ") and not line.startswith("### "):
                section_starts.append(idx)

        if not section_starts:
            for idx, line in enumerate(lines):
                if re.match(r"^-\s+\[\d{4}-\d{2}-\d{2}\]", line):
                    section_starts.append(idx)

        for i, start_idx in enumerate(section_starts):
            end_idx = section_starts[i + 1] if i + 1 < len(section_starts) else len(lines)
            chunk_lines = lines[start_idx:end_idx]
            raw_text = "\n".join(chunk_lines)

            record = self._parse_chunk(file_path, chunk_lines, start_idx + 1, end_idx)
            if record:
                records.append(record)

        return records

    def _parse_chunk(
        self, file_path: str, lines: List[str], line_start: int, line_end: int
    ) -> Optional[CanonicalRecord]:
        """Parses a markdown section into a CanonicalRecord."""
        header_line = lines[0].strip() if lines else ""
        raw_text = "\n".join(lines)

        # Extract title and date from header
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", header_line)
        header_date = date_match.group(1) if date_match else None

        # Check for supersession tags: [SUPERSEDED on YYYY-MM-DD by id:XYZ]
        superseded_pattern = r"\[SUPERSEDED\s+on\s+(\d{4}-\d{2}-\d{2})\s+by\s+id:([^\]]+)\]"
        sup_match = re.search(superseded_pattern, raw_text)
        superseded_date = sup_match.group(1) if sup_match else None
        superseded_by = sup_match.group(2) if sup_match else None

        # Extract bitemporal comment tag if present:
        # <!-- bitemporal: id=XYZ observed_at=... valid_from=... valid_until=... supersedes=... superseded_by=... -->
        bitemp_match = re.search(r"<!--\s*bitemporal:(.*?)\s*-->", raw_text)
        bitemp_data = {}
        if bitemp_match:
            pairs = re.findall(r'(\w+)=(".*?"|\S+)', bitemp_match.group(1))
            for k, v in pairs:
                bitemp_data[k] = v.strip('"')

        # Identify Record ID (priority: explicit bitemporal ID -> ADR ID -> generated slug)
        adr_match = re.search(r"\b(ADR-\d+)\b", header_line)
        adr_id = adr_match.group(1) if adr_match else None

        rec_id = bitemp_data.get("id") or adr_id
        if not superseded_by:
            superseded_by = bitemp_data.get("superseded_by")

        # Parse Type, Scope, Confidence, Source, Status
        meta_line = ""
        for line in lines[1:5]:
            if "**Type:**" in line or "**Status:**" in line:
                meta_line = line
                break

        def extract_meta(key: str, default: str) -> str:
            m = re.search(rf"\*\*{key}:\*\*\s*([^\s\*]+)", meta_line)
            return m.group(1) if m else default

        mtype = extract_meta("Type", "PROJECT")
        scope = extract_meta("Scope", "PROJECT")
        confidence = extract_meta("Confidence", "VERIFIED")
        source = extract_meta("Source", "canonical")
        status = extract_meta("Status", "ACTIVE")

        if superseded_by or "SUPERSEDED" in header_line or "SUPERSEDED" in meta_line:
            status = "SUPERSEDED"

        # Determine clean title
        clean_title = re.sub(r"^##\s*", "", header_line)
        clean_title = re.sub(r"\[SUPERSEDED.*?\]", "", clean_title).strip()

        # If no explicit ID, create deterministic ID from file and title
        if not rec_id:
            title_slug = re.sub(r"[^\w]+", "-", clean_title.lower()).strip("-")
            rec_id = f"{os.path.splitext(os.path.basename(file_path))[0].lower()}-{title_slug[:32]}"

        # Parse body content and core claim (### What)
        content_lines = []
        what_lines = []
        in_what = False
        for line in lines:
            if line.startswith("## ") or line == meta_line or line.startswith("<!-- bitemporal"):
                continue
            content_lines.append(line)
            if line.strip().startswith("### What"):
                in_what = True
                continue
            elif in_what and line.strip().startswith("### "):
                in_what = False
            elif in_what:
                what_lines.append(line)

        body_content = "\n".join(content_lines).strip()
        core_claim = "\n".join(what_lines).strip() if what_lines else body_content

        # Extract context if present (e.g. environment: production)
        context = ""
        ctx_match = re.search(r"(?:Context|Environment):\s*(.*)", raw_text, re.IGNORECASE)
        if ctx_match:
            context = ctx_match.group(1).strip()

        if adr_id:
            bitemp_data["adr_id"] = adr_id

        return CanonicalRecord(
            id=rec_id,
            file_path=file_path,
            title=clean_title,
            type=mtype,
            scope=scope,
            status=status,
            content=body_content,
            core_claim=core_claim,
            raw_text=raw_text,
            line_start=line_start,
            line_end=line_end,
            confidence=confidence,
            source=source,
            context=context,
            observed_at=bitemp_data.get("observed_at") or header_date or datetime.date.today().isoformat(),
            recorded_at=bitemp_data.get("recorded_at") or header_date or datetime.date.today().isoformat(),
            valid_from=bitemp_data.get("valid_from") or header_date or datetime.date.today().isoformat(),
            valid_until=bitemp_data.get("valid_until") or (superseded_date if status == "SUPERSEDED" else None),
            supersedes=[s.strip() for s in bitemp_data.get("supersedes", "").split(",") if s.strip()],
            superseded_by=superseded_by,
            superseded_date=superseded_date,
            superseded_at=bitemp_data.get("superseded_at"),
            metadata=bitemp_data,
        )

    # ------------------------------------------------------------------------
    # Conflict Resolution & Relationship Classification (Section 14)
    # ------------------------------------------------------------------------

    def normalize_title(self, t: str) -> str:
        """Strips dates, ADR tags, and punctuation for semantic topic matching."""
        clean = re.sub(r"^(?:\d{4}-\d{2}-\d{2}\s*—?\s*|adr-\d+:?\s*|\[.*?\]\s*)+", "", t, flags=re.I).strip().lower()
        clean = re.sub(r"[^\w\s]", " ", clean)
        return re.sub(r"\s+", " ", clean).strip()

    def normalize_text(self, text: str) -> str:
        """Normalizes text for comparison."""
        clean = re.sub(r"\s+", " ", text.lower().strip())
        return clean

    def classify_relationship(
        self, candidate: CandidateMemory, existing: CanonicalRecord
    ) -> Tuple[ConflictClassification, str]:
        """
        Distinguishes duplicate, refinement, complement, and true contradiction
        per Instruction.md Section 14.
        """
        cand_title_norm = self.normalize_title(candidate.title)
        exist_title_norm = self.normalize_title(existing.title)
        titles_match = (
            cand_title_norm == exist_title_norm
            or (cand_title_norm and exist_title_norm and cand_title_norm in exist_title_norm)
            or (cand_title_norm and exist_title_norm and exist_title_norm in cand_title_norm)
            or difflib.SequenceMatcher(None, cand_title_norm, exist_title_norm).ratio() > 0.8
        )

        cand_content_norm = self.normalize_text(candidate.content)
        exist_core_norm = self.normalize_text(existing.core_claim or existing.content)
        exist_full_norm = self.normalize_text(existing.content)

        # 1. Check for Scope Difference / Complement (Section 14: SQLite local vs Postgres prod)
        env_patterns = [
            (r"\b(local\s*dev(?:elopment)?|dev(?:elopment)?)\b", "development"),
            (r"\b(prod(?:uction)?)\b", "production"),
            (r"\b(test(?:ing)?|ci|staging)\b", "test_staging"),
            (r"\b(frontend|ui|browser)\b", "frontend"),
            (r"\b(backend|server|api)\b", "backend"),
            (r"\b(linux|macos|darwin|windows|android|ios)\b", "platform"),
        ]

        cand_envs = set()
        exist_envs = set()
        cand_eval_str = f"{candidate.context} {candidate.title} {candidate.content}".lower()
        exist_eval_str = f"{existing.context} {existing.title} {existing.content}".lower()

        for pattern, env_label in env_patterns:
            if re.search(pattern, cand_eval_str):
                cand_envs.add(env_label)
            if re.search(pattern, exist_eval_str):
                exist_envs.add(env_label)

        if cand_envs and exist_envs and not (cand_envs & exist_envs):
            return (
                ConflictClassification.COMPLEMENT,
                f"Scope/environment difference ({', '.join(sorted(cand_envs))} vs {', '.join(sorted(exist_envs))}). Both are valid.",
            )

        # 2. Check for Explicit or Direct Contradiction
        contradiction_reason = self._detect_direct_contradiction(candidate, existing)
        if contradiction_reason:
            return ConflictClassification.CONTRADICTION, contradiction_reason

        # 3. Exact or Core Duplicate (content matches what is already recorded)
        cand_hash = hashlib.sha256(cand_content_norm.encode("utf-8")).hexdigest()
        exist_core_hash = hashlib.sha256(exist_core_norm.encode("utf-8")).hexdigest()

        if cand_hash == exist_core_hash or cand_content_norm == exist_core_norm:
            return ConflictClassification.DUPLICATE, f"Exact content match with core claim of record {existing.id}."

        if titles_match:
            # Check if candidate content is identical to or contained in existing core claim
            claim_sim = difflib.SequenceMatcher(None, cand_content_norm, exist_core_norm).ratio()
            if claim_sim > 0.88 or cand_content_norm in exist_full_norm:
                return ConflictClassification.DUPLICATE, f"Duplicate fact already documented in {existing.id}."

            # 4. Refinement: same topic, compatible claims, but candidate adds more detail/guidance
            if len(cand_content_norm) > len(exist_core_norm) and (
                exist_core_norm in cand_content_norm or claim_sim > 0.45
            ):
                return (
                    ConflictClassification.REFINEMENT,
                    f"Candidate adds detailed refinement and clarification to existing record {existing.id}.",
                )

        # 5. Semantic Near-Duplicate check
        full_sim = difflib.SequenceMatcher(None, cand_content_norm, exist_core_norm).ratio()
        if full_sim > 0.85:
            return ConflictClassification.DUPLICATE, f"High semantic similarity ({full_sim:.2f}) with record {existing.id}."

        # 6. Topics overlap check
        if self._topics_overlap(candidate, existing):
            if self._has_negation_conflict(candidate, existing):
                return (
                    ConflictClassification.CONTRADICTION,
                    f"Direct negation/opposing statement found regarding subject '{existing.title}'.",
                )
            return (
                ConflictClassification.COMPLEMENT,
                f"Related topic '{existing.title}' with complementary context.",
            )

        return ConflictClassification.NEW_FACT, "No significant collision with existing record."

    def _detect_direct_contradiction(
        self, candidate: CandidateMemory, existing: CanonicalRecord
    ) -> Optional[str]:
        """Detects explicit version, architecture, or tool contradictions on the same entity."""
        c_full = f"{candidate.title} {candidate.content}".lower()
        e_full = f"{existing.title} {existing.content}".lower()

        # A. Explicit supersession directive
        if candidate.supersedes and (
            existing.id in candidate.supersedes
            or existing.metadata.get("adr_id") in candidate.supersedes
        ):
            return f"Candidate explicitly designates {existing.id} for supersession."

        # B. Version Contradictions (e.g. Antigravity 1.1.23 vs 1.1.25, Python 3.11 vs 3.12)
        version_pattern = r"\b(python|node|openjdk|java|gcc|clang|antigravity|agy|go|rust|gradle)\b[^\n\d]*?(\d+(?:\.\d+)+)"
        c_vers = dict(re.findall(version_pattern, c_full))
        e_vers = dict(re.findall(version_pattern, e_full))

        for tool, c_ver in c_vers.items():
            if tool in e_vers and e_vers[tool] != c_ver:
                return f"Version conflict for {tool}: existing={e_vers[tool]} vs candidate={c_ver}"

        # C. Architecture Contradictions (e.g. monolithic vs microservices for the same project)
        arch_pattern = r"\barchitecture\s*:\s*(monolithic|microservices|serverless|event-driven)\b"
        c_arch = re.search(arch_pattern, c_full)
        e_arch = re.search(arch_pattern, e_full)
        if c_arch and e_arch and c_arch.group(1) != e_arch.group(1):
            return f"Architecture conflict: existing={e_arch.group(1)} vs candidate={c_arch.group(1)}"

        # D. Primary Tool Conflict (e.g. package manager npm vs pnpm)
        pkg_pattern = r"\b(?:primary\s+)?package\s+manager\s+(?:is|to|use)?\s*(npm|pnpm|yarn|bun)\b"
        c_pkg = re.search(pkg_pattern, c_full)
        e_pkg = re.search(pkg_pattern, e_full)
        if c_pkg and e_pkg and c_pkg.group(1) != e_pkg.group(1):
            return f"Package manager conflict: existing={e_pkg.group(1)} vs candidate={c_pkg.group(1)}"

        # E. Direct negation
        if self._has_negation_conflict(candidate, existing) and self.normalize_title(candidate.title) == self.normalize_title(existing.title):
            return f"Direct opposing directive regarding '{existing.title}'."

        return None

    def _topics_overlap(self, candidate: CandidateMemory, existing: CanonicalRecord) -> bool:
        """Determines if candidate and existing record discuss the same topic/entity."""
        c_words = set(re.findall(r"\b\w{4,}\b", self.normalize_title(candidate.title)))
        e_words = set(re.findall(r"\b\w{4,}\b", self.normalize_title(existing.title)))
        if not c_words or not e_words:
            return False
        return len(c_words & e_words) / min(len(c_words), len(e_words)) >= 0.5

    def _has_negation_conflict(self, candidate: CandidateMemory, existing: CanonicalRecord) -> bool:
        """Checks if statements have opposing polarity (e.g. enable vs disable, deprecated vs supported)."""
        c_full = f"{candidate.title} {candidate.content}".lower()
        e_full = f"{existing.title} {existing.content}".lower()

        negation_pairs = [
            (r"\benabled?\b", r"\bdisabled?\b"),
            (r"\bsupported\b", r"\b(?:unsupported|deprecated)\b"),
            (r"\brequired\b", r"\boptional\b"),
            (r"\ballow(?:ed)?\b", r"\b(?:prohibit(?:ed)?|block(?:ed)?|forbid(?:den)?)\b"),
            (r"\breplace(?:d|s)?\b", r"\bdecouple\b"),
        ]
        for p1, p2 in negation_pairs:
            if (re.search(p1, c_full) and re.search(p2, e_full)) or (
                re.search(p2, c_full) and re.search(p1, e_full)
            ):
                return True
        return False

    # ------------------------------------------------------------------------
    # Core Reconciliation Workflow (Section 12)
    # ------------------------------------------------------------------------

    def reconcile_candidate(
        self,
        candidate_data: Union[CandidateMemory, Dict[str, Any]],
        dry_run: bool = False,
    ) -> ReconciliationResult:
        """
        Reconciles a candidate memory against canonical records in .agents/memory/.
        """
        if isinstance(candidate_data, dict):
            candidate = CandidateMemory(**candidate_data)
        else:
            candidate = candidate_data

        # 1. Durability Gate (Section 10, 12, Skill memory-promote)
        if candidate.durability <= 1:
            return ReconciliationResult(
                candidate_id=candidate.id,
                action=ReconciliationAction.REJECT,
                classification=ConflictClassification.EPHEMERAL_DISCARD,
                reason=f"Candidate durability {candidate.durability} is classified as ephemeral noise (0-1). Discarded.",
                target_file=candidate.target_file or "none",
                success=True,
            )

        # 2. Secret Scan Gate (Zero Secrets Policy)
        full_cand_text = f"{candidate.title}\n{candidate.content}\n{candidate.evidence}"
        scan_res = scan_text(full_cand_text, target_name=f"candidate:{candidate.id}")
        if not scan_res.is_clean:
            findings_summary = "; ".join(
                [f"[{f.severity}] {f.description} (rule: {f.rule_name})" for f in scan_res.findings]
            )
            return ReconciliationResult(
                candidate_id=candidate.id,
                action=ReconciliationAction.REJECT,
                classification=ConflictClassification.SECURITY_VIOLATION,
                reason=f"Security gatekeeper rejected candidate due to secret patterns: {findings_summary}",
                target_file=candidate.target_file or "none",
                success=False,
            )

        # 3. Route target file if not explicitly set
        target_file = candidate.target_file
        if not target_file:
            target_file = self._route_target_file(candidate.type)
        candidate.target_file = target_file

        # 4. Compare against canonical records in target_file or entire project memory
        existing_records = self.scan_canonical_records(target_file)

        conflict_found: Optional[CanonicalRecord] = None
        conflict_type: ConflictClassification = ConflictClassification.NEW_FACT
        conflict_reason: str = "New authoritative fact to add."

        for rec in existing_records:
            if not rec.is_active():
                continue
            classification, reason = self.classify_relationship(candidate, rec)

            if classification == ConflictClassification.DUPLICATE:
                conflict_found = rec
                conflict_type = classification
                conflict_reason = reason
                break
            elif classification == ConflictClassification.CONTRADICTION:
                conflict_found = rec
                conflict_type = classification
                conflict_reason = reason
                break
            elif classification == ConflictClassification.REFINEMENT:
                if conflict_type not in (ConflictClassification.CONTRADICTION, ConflictClassification.DUPLICATE):
                    conflict_found = rec
                    conflict_type = classification
                    conflict_reason = reason
            elif classification == ConflictClassification.COMPLEMENT:
                if conflict_type == ConflictClassification.NEW_FACT:
                    conflict_type = classification
                    conflict_reason = reason

        # 5. Determine Action and Execute Mutation
        today_str = datetime.date.today().isoformat()
        tx_id = f"tx-{today_str}-{uuid.uuid4().hex[:8]}"

        if conflict_type == ConflictClassification.DUPLICATE:
            # NOOP: Candidate already exists
            return ReconciliationResult(
                candidate_id=candidate.id,
                action=ReconciliationAction.NOOP,
                classification=ConflictClassification.DUPLICATE,
                reason=f"NOOP: {conflict_reason}",
                target_file=target_file,
                merged_record_id=conflict_found.id if conflict_found else None,
                transaction_id=tx_id,
                success=True,
            )

        elif conflict_type == ConflictClassification.CONTRADICTION and conflict_found:
            # SUPERSEDE: Existing fact superseded by new candidate
            if conflict_found.id not in candidate.supersedes:
                candidate.supersedes.append(conflict_found.id)
            candidate.valid_from = candidate.valid_from or today_str
            candidate.valid_until = None

            if dry_run:
                return ReconciliationResult(
                    candidate_id=candidate.id,
                    action=ReconciliationAction.SUPERSEDE,
                    classification=ConflictClassification.CONTRADICTION,
                    reason=f"[DRY RUN] Would supersede {conflict_found.id}: {conflict_reason}",
                    target_file=target_file,
                    superseded_records=[conflict_found.id],
                    transaction_id=tx_id,
                    success=True,
                )

            success = self._apply_supersede(
                target_file=target_file,
                old_record=conflict_found,
                candidate=candidate,
                tx_id=tx_id,
                reason=conflict_reason,
            )

            return ReconciliationResult(
                candidate_id=candidate.id,
                action=ReconciliationAction.SUPERSEDE,
                classification=ConflictClassification.CONTRADICTION,
                reason=f"SUPERSEDED: {conflict_reason}",
                target_file=target_file,
                superseded_records=[conflict_found.id],
                transaction_id=tx_id,
                success=success,
            )

        elif conflict_type == ConflictClassification.REFINEMENT and conflict_found:
            # UPDATE / MERGE
            if dry_run:
                return ReconciliationResult(
                    candidate_id=candidate.id,
                    action=ReconciliationAction.UPDATE,
                    classification=ConflictClassification.REFINEMENT,
                    reason=f"[DRY RUN] Would update/merge into {conflict_found.id}: {conflict_reason}",
                    target_file=target_file,
                    merged_record_id=conflict_found.id,
                    transaction_id=tx_id,
                    success=True,
                )

            success = self._apply_update(
                target_file=target_file,
                old_record=conflict_found,
                candidate=candidate,
                tx_id=tx_id,
                reason=conflict_reason,
            )

            return ReconciliationResult(
                candidate_id=candidate.id,
                action=ReconciliationAction.UPDATE,
                classification=ConflictClassification.REFINEMENT,
                reason=f"REFINED: {conflict_reason}",
                target_file=target_file,
                merged_record_id=conflict_found.id,
                transaction_id=tx_id,
                success=success,
            )

        else:
            # ADD (New fact or Complement)
            action = ReconciliationAction.ADD
            classification = conflict_type

            if dry_run:
                return ReconciliationResult(
                    candidate_id=candidate.id,
                    action=action,
                    classification=classification,
                    reason=f"[DRY RUN] Would add to canonical memory: {conflict_reason}",
                    target_file=target_file,
                    transaction_id=tx_id,
                    success=True,
                )

            success = self._apply_add(
                target_file=target_file,
                candidate=candidate,
                tx_id=tx_id,
                classification=classification,
                reason=conflict_reason,
            )

            return ReconciliationResult(
                candidate_id=candidate.id,
                action=action,
                classification=classification,
                reason=f"ADDED: {conflict_reason}",
                target_file=target_file,
                transaction_id=tx_id,
                success=success,
            )

    def reconcile_batch(
        self, candidates: List[Union[CandidateMemory, Dict[str, Any]]], dry_run: bool = False
    ) -> List[ReconciliationResult]:
        """Reconciles multiple candidate memories sequentially."""
        results = []
        for cand in candidates:
            res = self.reconcile_candidate(cand, dry_run=dry_run)
            results.append(res)
        return results

    # ------------------------------------------------------------------------
    # Execution Mutations & Supersession Formatting (Section 15, 84)
    # ------------------------------------------------------------------------

    def _apply_supersede(
        self,
        target_file: str,
        old_record: CanonicalRecord,
        candidate: CandidateMemory,
        tx_id: str,
        reason: str,
        operation: str = "supersede",
    ) -> bool:
        """
        Marks superseded canonical facts with [SUPERSEDED on YYYY-MM-DD by id:XYZ]
        without destroying history, applies bitemporal semantics with RFC3339 timestamps,
        appends new record, enqueues index update, and logs transaction for full rollback.
        """
        today_str = datetime.date.today().isoformat()
        now_rfc3339 = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        supersede_tag = f"[SUPERSEDED on {today_str} by id:{candidate.id}]"

        with file_lock(target_file):
            with open(target_file, "r", encoding="utf-8") as f:
                before_content = f.read()

            lines = before_content.splitlines()
            old_start = old_record.line_start - 1
            old_end = old_record.line_end

            chunk_lines = lines[old_start:old_end]
            updated_chunk_lines = []

            for idx, line in enumerate(chunk_lines):
                if idx == 0 and line.startswith("## ") and supersede_tag not in line:
                    updated_chunk_lines.append(f"{line.strip()} {supersede_tag}")
                elif "**Status:**" in line:
                    updated_line = re.sub(
                        r"\*\*Status:\*\*\s*[^\s\*]+",
                        f"**Status:** SUPERSEDED {supersede_tag}",
                        line,
                    )
                    updated_chunk_lines.append(updated_line)
                else:
                    updated_chunk_lines.append(line)

            # Insert bitemporal tag for old record with RFC3339 timestamps
            obs_at = old_record.observed_at or now_rfc3339
            rec_at = old_record.recorded_at or now_rfc3339
            v_from = old_record.valid_from or today_str
            bitemp_comment = (
                f"<!-- bitemporal: id={old_record.id} observed_at={obs_at} "
                f"recorded_at={rec_at} valid_from={v_from} "
                f"valid_until={today_str} superseded_by={candidate.id} superseded_at={now_rfc3339} -->"
            )
            insert_pos = 2 if len(updated_chunk_lines) > 2 else 1
            updated_chunk_lines.insert(insert_pos, bitemp_comment)

            new_lines = lines[:old_start] + updated_chunk_lines + lines[old_end:]
            mid_content = "\n".join(new_lines)

            # Format and append new candidate entry
            new_entry = self._format_new_record(candidate)
            after_content = mid_content.rstrip() + "\n\n" + new_entry.strip() + "\n"

            val = scan_text(after_content, target_name=target_file)
            if not val.is_clean:
                raise ValueError("Mutation contains secret violations.")

            atomic_write(target_file, after_content)

            self._log_transaction(
                tx_id=tx_id,
                action=ReconciliationAction.SUPERSEDE,
                classification=ConflictClassification.CONTRADICTION,
                candidate=candidate,
                target_file=target_file,
                superseded_ids=[old_record.id],
                before_content=before_content,
                after_content=after_content,
                reason=reason,
            )

            # DEF-009: Enqueue index job whenever canonical files are modified
            self._enqueue_index_update(target_file, operation=operation)

        return True

    _execute_supersede = _apply_supersede

    def _apply_update(
        self,
        target_file: str,
        old_record: CanonicalRecord,
        candidate: CandidateMemory,
        tx_id: str,
        reason: str,
        operation: str = "update",
    ) -> bool:
        """Enriches an existing record with refined information."""
        today_str = datetime.date.today().isoformat()
        with file_lock(target_file):
            with open(target_file, "r", encoding="utf-8") as f:
                before_content = f.read()

            lines = before_content.splitlines()
            old_start = old_record.line_start - 1
            old_end = old_record.line_end

            chunk_lines = lines[old_start:old_end]
            refinement_note = f"\n### Refinement ({today_str})\n- {candidate.content.strip()}\n"
            chunk_lines.append(refinement_note)

            new_lines = lines[:old_start] + chunk_lines + lines[old_end:]
            after_content = "\n".join(new_lines)

            atomic_write(target_file, after_content)

            self._log_transaction(
                tx_id=tx_id,
                action=ReconciliationAction.UPDATE,
                classification=ConflictClassification.REFINEMENT,
                candidate=candidate,
                target_file=target_file,
                superseded_ids=[],
                before_content=before_content,
                after_content=after_content,
                reason=reason,
            )

            # DEF-009: Enqueue index job whenever canonical files are modified
            self._enqueue_index_update(target_file, operation=operation)

        return True

    _execute_refinement_update = _apply_update

    def _apply_add(
        self,
        target_file: str,
        candidate: CandidateMemory,
        tx_id: str,
        classification: ConflictClassification,
        reason: str,
        operation: str = "add",
    ) -> bool:
        """Adds a new fact or complement record to canonical memory."""
        with file_lock(target_file):
            before_content = ""
            if os.path.exists(target_file):
                with open(target_file, "r", encoding="utf-8") as f:
                    before_content = f.read()

            new_entry = self._format_new_record(candidate)
            if before_content.strip():
                after_content = before_content.rstrip() + "\n\n" + new_entry.strip() + "\n"
            else:
                title = os.path.splitext(os.path.basename(target_file))[0].replace("-", " ").title()
                header = f"# Project {title}\nLast Updated: {datetime.date.today().isoformat()}\n\n"
                after_content = header + new_entry.strip() + "\n"

            val = scan_text(after_content, target_name=target_file)
            if not val.is_clean:
                raise ValueError("Mutation contains secret violations.")

            atomic_write(target_file, after_content)

            self._log_transaction(
                tx_id=tx_id,
                action=ReconciliationAction.ADD,
                classification=classification,
                candidate=candidate,
                target_file=target_file,
                superseded_ids=[],
                before_content=before_content,
                after_content=after_content,
                reason=reason,
            )

            # DEF-009: Enqueue index job whenever canonical files are modified
            self._enqueue_index_update(target_file, operation=operation)

        return True

    _execute_add = _apply_add

    def _enqueue_index_update(self, target_file: str, operation: str = "upsert") -> None:
        """Enqueues canonical modification into IndexQueueManager (DEF-009)."""
        if self.index_queue_manager is not None:
            try:
                self.index_queue_manager.enqueue(target_file, operation=operation)
                return
            except Exception:
                pass
        if IndexQueueManager is not None:
            try:
                queue_file = os.path.join(self.memory_dir, "index_queue.jsonl")
                health_file = os.path.join(self.memory_dir, "index_health.json")
                lease_file = os.path.join(self.memory_dir, "index_writer.lease")
                mgr = IndexQueueManager(
                    queue_file=queue_file,
                    health_file=health_file,
                    lease_file=lease_file,
                )
                mgr.enqueue(target_file, operation=operation)
            except Exception:
                pass

    def _format_new_record(self, candidate: CandidateMemory) -> str:
        """Formats a candidate memory entry for canonical storage."""
        today_str = datetime.date.today().isoformat()
        now_rfc3339 = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        supersedes_str = ",".join(candidate.supersedes) if candidate.supersedes else ""

        obs_at = candidate.observed_at or now_rfc3339
        rec_at = candidate.recorded_at or now_rfc3339
        v_from = candidate.valid_from or today_str

        bitemp_comment = (
            f"<!-- bitemporal: id={candidate.id} observed_at={obs_at} "
            f"recorded_at={rec_at} valid_from={v_from} "
            f"valid_until=None supersedes={supersedes_str} -->"
        )

        title = candidate.title if candidate.title else f"{candidate.type} Entry"
        if not re.match(r"^\d{4}-\d{2}-\d{2}", title):
            header = f"## {today_str} — {title}"
        else:
            header = f"## {title}"

        status_line = (
            f"**Type:** {candidate.type} **Scope:** {candidate.scope} "
            f"**Confidence:** {candidate.confidence} **Source:** {candidate.source} **Status:** ACTIVE"
        )

        why_section = f"### Why\n{candidate.metadata.get('why', 'Identified and verified in active workflow.')}\n"
        evidence_section = f"### Evidence\n{candidate.evidence or candidate.metadata.get('evidence', 'Empirical observation in runtime.')}\n"
        notes_section = ""
        if candidate.supersedes:
            notes_section = f"### Notes\nSupersedes {', '.join(candidate.supersedes)}.\n"

        entry = f"""{header}
{status_line}
{bitemp_comment}
### What
{candidate.content.strip()}
{why_section}
{evidence_section}
{notes_section}"""
        return entry

    def _route_target_file(self, mtype: str) -> str:
        """Determines target markdown file in .agents/memory/ based on type."""
        mtype = mtype.upper()
        if mtype == "DECISION":
            return os.path.join(self.memory_dir, "DECISIONS.md")
        elif mtype == "GOTCHA":
            return os.path.join(self.memory_dir, "GOTCHAS.md")
        elif mtype == "PROCEDURE":
            return os.path.join(self.memory_dir, "PROCEDURES.md")
        else:
            return os.path.join(self.memory_dir, "ARCHITECTURE.md")

    # ------------------------------------------------------------------------
    # Transaction Logging & Full Rollback (Section 84)
    # ------------------------------------------------------------------------

    def _log_transaction(
        self,
        tx_id: str,
        action: ReconciliationAction,
        classification: ConflictClassification,
        candidate: CandidateMemory,
        target_file: str,
        superseded_ids: List[str],
        before_content: str,
        after_content: str,
        reason: str,
    ):
        """Logs transaction to reconciliation_log.jsonl with full snapshot to support rollback."""
        tx_record = {
            "transaction_id": tx_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "action": action.value,
            "classification": classification.value,
            "candidate_id": candidate.id,
            "candidate": candidate.to_dict(),
            "target_file": target_file,
            "superseded_records": superseded_ids,
            "reason": reason,
            "before_content": before_content,
            "after_content": after_content,
            "reverted": False,
        }

        with file_lock(self.log_file):
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(tx_record) + "\n")

    def rollback(self, transaction_id: Optional[str] = None) -> bool:
        """
        Performs atomic rollback of a reconciliation transaction per Section 84.
        Restores exact pre-transaction canonical state.
        If transaction_id is None, rolls back the most recent active transaction.
        """
        if not os.path.exists(self.log_file):
            print("No reconciliation transactions found to rollback.")
            return False

        with file_lock(self.log_file):
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            transactions = []
            for line in lines:
                line_str = line.strip()
                if line_str:
                    try:
                        transactions.append(json.loads(line_str))
                    except json.JSONDecodeError:
                        continue

            target_tx = None
            target_idx = -1

            if transaction_id:
                for idx, tx in enumerate(reversed(transactions)):
                    if tx.get("transaction_id") == transaction_id and not tx.get("reverted"):
                        target_tx = tx
                        target_idx = len(transactions) - 1 - idx
                        break
            else:
                for idx, tx in enumerate(reversed(transactions)):
                    if (
                        not tx.get("reverted")
                        and tx.get("action") in (
                            ReconciliationAction.SUPERSEDE.value,
                            ReconciliationAction.ADD.value,
                            ReconciliationAction.UPDATE.value,
                        )
                    ):
                        target_tx = tx
                        target_idx = len(transactions) - 1 - idx
                        break

            if not target_tx:
                print(f"No rollback target found for transaction_id: {transaction_id or 'latest'}")
                return False

            target_file = target_tx["target_file"]
            before_content = target_tx["before_content"]

            with file_lock(target_file):
                atomic_write(target_file, before_content)

            transactions[target_idx]["reverted"] = True

            rollback_event = {
                "transaction_id": f"rollback-{target_tx['transaction_id']}",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "action": ReconciliationAction.ROLLBACK.value,
                "target_transaction_id": target_tx["transaction_id"],
                "target_file": target_file,
                "status": "SUCCESS",
            }
            transactions.append(rollback_event)

            new_log_content = "\n".join([json.dumps(t) for t in transactions]) + "\n"
            atomic_write(self.log_file, new_log_content)

        print(f"ROLLBACK SUCCESSFUL: Reverted transaction {target_tx['transaction_id']} on {target_file}")
        return True

    def get_transaction_history(self) -> List[Dict[str, Any]]:
        """Returns all recorded transactions from reconciliation_log.jsonl."""
        if not os.path.exists(self.log_file):
            return []
        with open(self.log_file, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    # ------------------------------------------------------------------------
    # Bitemporal Querying & Time Travel (Section 15)
    # ------------------------------------------------------------------------

    def query_as_of(
        self,
        valid_at: Optional[str] = None,
        recorded_at: Optional[str] = None,
        target_file: Optional[str] = None,
    ) -> List[CanonicalRecord]:
        """
        Bitemporal query answering:
        - "What is true now?"
        - "What was true at time T?"
        - "What did we believe at time T?"
        """
        all_records = self.scan_canonical_records(target_file)
        results = []

        now_str = datetime.date.today().isoformat()
        query_valid = (valid_at or now_str)[:10]
        query_record = (recorded_at or now_str)[:10]

        for rec in all_records:
            v_from = (rec.valid_from or rec.observed_at or "0000-01-01")[:10]
            v_until = (rec.valid_until or "9999-12-31")[:10]
            rec_time = (rec.recorded_at or "0000-01-01")[:10]

            # Check valid time window: valid_from <= query_valid <= valid_until
            # If superseded on valid_until, it was valid up to that date
            valid_match = v_from <= query_valid <= v_until if rec.is_active() else v_from <= query_valid < v_until
            if query_valid == v_from:
                valid_match = True

            # Check transaction/record time window: recorded_at <= query_record
            record_match = rec_time <= query_record

            if valid_match and record_match:
                results.append(rec)

        return results

    # ------------------------------------------------------------------------
    # Candidate Inbox Drainage (DEF-006)
    # ------------------------------------------------------------------------

    def _convert_dict_to_candidate(
        self, item: Dict[str, Any], target_category: Optional[str] = None
    ) -> CandidateMemory:
        """Converts raw candidate dict from candidates.jsonl into CandidateMemory."""
        cand_id = item.get("id") or item.get("candidate_id") or f"cand-{uuid.uuid4().hex[:8]}"
        raw_cat = target_category or item.get("category") or item.get("type") or "PROJECT"
        cat_upper = raw_cat.upper()

        if "DECISION" in cat_upper or "ADR" in cat_upper:
            mtype = "DECISION"
        elif any(k in cat_upper for k in ("GOTCHA", "BUG", "WORKAROUND", "TRAP", "SECURITY")):
            mtype = "GOTCHA"
        elif "PROCEDURE" in cat_upper or "WORKFLOW" in cat_upper or "RUNBOOK" in cat_upper:
            mtype = "PROCEDURE"
        elif "TOOL" in cat_upper or "CLI" in cat_upper:
            mtype = "TOOL"
        else:
            mtype = "PROJECT"

        content = (item.get("content") or item.get("text") or "").strip()
        title = item.get("title")
        if not title:
            first_line = content.split("\n")[0].strip()
            first_sent = first_line.split(".")[0].strip()
            title = first_sent[:60] if first_sent else f"{mtype} Entry"

        prov = item.get("provenance") or {}
        evidence = item.get("evidence", "")
        if not evidence and isinstance(prov, dict):
            if prov.get("command"):
                evidence = f"Command: {prov.get('command')}"
            elif prov.get("path"):
                evidence = f"Source: {prov.get('path')} (commit: {prov.get('commit', 'HEAD')})"

        context = item.get("context", "")
        durability_raw = item.get("durability", 3.0)
        try:
            durability = int(round(float(durability_raw)))
        except (ValueError, TypeError):
            durability = 3

        target_file = item.get("target_file") or self._route_target_file(mtype)

        now_rfc3339 = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        obs_at = item.get("created_at") or now_rfc3339

        return CandidateMemory(
            id=cand_id,
            type=mtype,
            scope=item.get("scope", "PROJECT"),
            title=title,
            content=content,
            target_file=target_file,
            durability=durability,
            confidence=str(item.get("confidence", "VERIFIED")),
            source=str(prov.get("source_type") or item.get("source", "inbox")),
            evidence=str(evidence or "Empirical observation in runtime"),
            context=str(context),
            observed_at=obs_at,
            recorded_at=now_rfc3339,
            valid_from=datetime.date.today().isoformat(),
            supersedes=item.get("supersedes", []) or [],
            metadata=item.get("metadata") or {},
        )

    def drain_candidates(
        self,
        inbox_file: Optional[str] = None,
        dry_run: bool = False,
        target_categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Drains pending accepted candidates from .agents/memory/inbox/candidates.jsonl
        into canonical memory files (DECISIONS.md, GOTCHAS.md, etc.) per DEF-006.
        Updates candidate status to PROMOTED or REJECTED.
        """
        inbox_path = inbox_file or os.path.join(self.memory_dir, "inbox", "candidates.jsonl")
        if not os.path.exists(inbox_path):
            alt_path = os.path.join(self.workspace_dir, ".agents", "memory", "inbox", "candidates.jsonl")
            if os.path.exists(alt_path):
                inbox_path = alt_path
            else:
                return {
                    "inbox_path": inbox_path,
                    "total_candidates": 0,
                    "promoted_count": 0,
                    "rejected_count": 0,
                    "held_count": 0,
                    "results": [],
                    "dry_run": dry_run,
                }

        compiler = None
        if MemoryCompiler is not None:
            try:
                compiler = MemoryCompiler(workspace_dir=self.workspace_dir)
            except Exception:
                compiler = None

        with file_lock(inbox_path, timeout=5.0):
            with open(inbox_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            items = []
            for line in lines:
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    record = json.loads(line_str)
                    items.append(record)
                except json.JSONDecodeError:
                    continue

            results = []
            promoted_count = 0
            rejected_count = 0
            held_count = 0

            for item in items:
                status = item.get("status", "STAGED").upper()
                if status in ("PROMOTED", "REJECTED"):
                    continue

                content = (item.get("content") or "").strip()
                # Routine or test fixture noise check
                if re.match(r"^Command failed:\s*`?test(?:\s+\d+)?`?\s+with exit code", content):
                    item["status"] = "REJECTED"
                    item["rejected_reason"] = "Synthetic test fixture execution noise"
                    rejected_count += 1
                    continue

                decision = "ACCEPT"
                category = item.get("category", "PROJECT")
                reason = "Passed gatekeeper"

                if compiler is not None:
                    try:
                        compiled = compiler.compile_candidate(item)
                        decision = compiled["decision"]["decision"]
                        category = compiled["candidate"].get("category", category)
                        reason = compiled["decision"].get("reason", reason)
                    except Exception:
                        pass
                else:
                    dur = float(item.get("durability", 3.0))
                    prov = item.get("provenance", {})
                    verified = prov.get("verified", True) if isinstance(prov, dict) else True
                    if dur <= 1.0:
                        decision = "REJECT"
                        reason = "Durability <= 1.0 (ephemeral)"
                    elif dur == 2.0 or verified is False:
                        decision = "HOLD"
                        reason = "Session durability or unverified provenance"
                    else:
                        decision = "ACCEPT"

                if decision == "REJECT":
                    item["status"] = "REJECTED"
                    item["rejected_reason"] = reason
                    rejected_count += 1
                    continue
                elif decision == "HOLD":
                    item["status"] = "HELD"
                    held_count += 1
                    continue

                # Decision is ACCEPT
                if target_categories:
                    cat_norm = category.upper()
                    if not any(tc.upper() in cat_norm for tc in target_categories):
                        continue

                cand_mem = self._convert_dict_to_candidate(item, target_category=category)
                rec_result = self.reconcile_candidate(cand_mem, dry_run=dry_run)
                results.append(rec_result)

                if rec_result.success:
                    item["status"] = "PROMOTED"
                    item["reconciled_action"] = rec_result.action.value
                    item["target_file"] = rec_result.target_file
                    item["promoted_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    promoted_count += 1
                else:
                    item["status"] = "REJECTED"
                    item["rejected_reason"] = rec_result.reason
                    rejected_count += 1

            if not dry_run:
                new_inbox_content = "\n".join([json.dumps(it) for it in items]) + ("\n" if items else "")
                atomic_write(inbox_path, new_inbox_content)

        return {
            "inbox_path": inbox_path,
            "total_candidates": len(items),
            "promoted_count": promoted_count,
            "rejected_count": rejected_count,
            "held_count": held_count,
            "results": [r.to_dict() for r in results],
            "dry_run": dry_run,
        }

    drain_inbox = drain_candidates
    drain_pending_candidates = drain_candidates


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Antigravity Autonomous Memory Reconciler")
    parser.add_argument("--reconcile", action="store_true", help="Reconcile a candidate fact")
    parser.add_argument("--title", type=str, help="Candidate title/subject")
    parser.add_argument("--content", type=str, help="Candidate content/assertion")
    parser.add_argument("--type", type=str, default="PROJECT", help="Memory type (DECISION, GOTCHA, PROJECT, etc.)")
    parser.add_argument("--durability", type=int, default=3, help="Durability score (0-5)")
    parser.add_argument("--context", type=str, default="", help="Context / environment")
    parser.add_argument("--evidence", type=str, default="Live verification", help="Empirical evidence")
    parser.add_argument("--supersedes", type=str, default="", help="Comma-separated record IDs to supersede")
    parser.add_argument("--candidate-file", type=str, help="Path to JSON file containing candidate memory")
    parser.add_argument("--rollback", nargs="?", const="LATEST", help="Rollback transaction (ID or LATEST)")
    parser.add_argument("--history", action="store_true", help="Display reconciliation transaction history")
    parser.add_argument("--query-as-of", type=str, help="Bitemporal query: valid as of YYYY-MM-DD")
    parser.add_argument("--drain-candidates", action="store_true", help="Drain pending accepted candidates from inbox into canonical memory")
    parser.add_argument("--drain", action="store_true", help="Alias for --drain-candidates")
    parser.add_argument("--inbox", type=str, default=None, help="Path to candidates.jsonl inbox")
    parser.add_argument("--dry-run", action="store_true", help="Simulate reconciliation without mutations")

    args = parser.parse_args()
    reconciler = MemoryReconciler()

    if args.drain_candidates or args.drain:
        summary = reconciler.drain_candidates(inbox_file=args.inbox, dry_run=args.dry_run)
        print(json.dumps(summary, indent=2))
        sys.exit(0)

    if args.history:
        history = reconciler.get_transaction_history()
        print(f"Total Transactions: {len(history)}")
        for tx in history:
            status = "REVERTED" if tx.get("reverted") else "ACTIVE"
            print(f"[{tx.get('timestamp')}] {tx.get('transaction_id')} - Action: {tx.get('action')} - Class: {tx.get('classification')} [{status}]")
        return

    if args.rollback:
        tx_id = None if args.rollback == "LATEST" else args.rollback
        success = reconciler.rollback(tx_id)
        sys.exit(0 if success else 1)

    if args.query_as_of:
        results = reconciler.query_as_of(valid_at=args.query_as_of)
        print(f"=== BITEMPORAL VIEW AS OF {args.query_as_of} ===")
        print(f"Active records: {len(results)}")
        for r in results:
            print(f"- [{r.id}] ({r.type}) {r.title} [Status: {r.status}]")
        return

    if args.reconcile:
        candidate_obj = None
        if args.candidate_file:
            with open(args.candidate_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                candidate_obj = CandidateMemory(**data)
        elif args.title and args.content:
            supersedes_list = [s.strip() for s in args.supersedes.split(",") if s.strip()]
            candidate_obj = CandidateMemory(
                title=args.title,
                content=args.content,
                type=args.type,
                durability=args.durability,
                context=args.context,
                evidence=args.evidence,
                supersedes=supersedes_list,
            )
        else:
            print("Error: --reconcile requires either --candidate-file or both --title and --content.")
            sys.exit(1)

        result = reconciler.reconcile_candidate(candidate_obj, dry_run=args.dry_run)
        print(json.dumps(result.to_dict(), indent=2))
        sys.exit(0 if result.success else 1)

    parser.print_help()


if __name__ == "__main__":
    main()
