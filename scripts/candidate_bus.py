#!/usr/bin/env python3
"""
Candidate Memory Bus & Experience Capture Subsystem.
Implements Instruction.md Section 9 (Candidate Memory Pipeline) and Sections 90-93
(Automatic Capture, Stop Hook Design, Post-Tool Capture, Tool Output Filtering).

This module provides the CandidateBus class which:
1. Captures memory candidates from tool execution events and session turns.
2. Stages candidates in .agents/memory/inbox/candidates.jsonl.
3. Scans candidates for secrets via scripts/secret_scanner.py before staging;
   strictly rejects any secrets immediately.
4. Generates deterministic candidate_id via SHA-256 hash of normalized content
   for strict idempotency.
5. Prevents capture of routine noise (ls, simple echo, status checks, greetings).
6. Preserves structured provenance (command, exit code, session, tool args, output hash).
"""

import os
import sys
import re
import json
import time
import hashlib
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Safe file locking from lock_manager
try:
    from scripts.lock_manager import file_lock
except ImportError:
    from contextlib import contextmanager
    @contextmanager
    def file_lock(filepath, timeout=5.0):
        yield f"{filepath}.lock"

# Secret scanner integration
try:
    from scripts.secret_scanner import scan_text, SecretScanner, ScanResult
except ImportError:
    scan_text = None
    SecretScanner = None

# Default paths
DEFAULT_INBOX_DIR = PROJECT_ROOT / ".agents" / "memory" / "inbox"
DEFAULT_INBOX_FILE = DEFAULT_INBOX_DIR / "candidates.jsonl"
DEFAULT_REJECTED_FILE = DEFAULT_INBOX_DIR / "rejected_secrets.jsonl"

# High-signal candidate categories per Instruction.md Section 9
CATEGORIES = {
    "DURABLE_DISCOVERY": "new durable discovery",
    "ARCHITECTURAL_DECISION": "architectural decision",
    "EXPLICIT_CORRECTION": "explicit correction",
    "BUG_ROOT_CAUSE": "important bug root cause",
    "SUCCESSFUL_FIX": "successful fix",
    "REUSABLE_WORKAROUND": "reusable workaround",
    "TOOL_BEHAVIOR": "tool-specific behavior",
    "PROJECT_CONVENTION": "project convention",
    "USER_PREFERENCE": "user preference",
    "REPEATED_WORKFLOW": "repeated workflow",
    "REJECTED_APPROACH": "rejected approach",
    "CRITICAL_SECURITY_LESSON": "critical security lesson",
    "GENERAL_CANDIDATE": "general candidate insight",
}


@dataclass
class Candidate:
    """
    Structured candidate memory record.
    Staged in .agents/memory/inbox/candidates.jsonl before promotion.
    """
    candidate_id: str
    content: str
    normalized_content: str
    category: str
    source_type: str  # "tool_event", "session_turn", "manual", etc.
    created_at: str
    confidence: float = 0.8
    provenance: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "STAGED"  # STAGED, PROMOTED, REJECTED, SUPERSEDED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Candidate":
        return cls(
            candidate_id=data.get("candidate_id", ""),
            content=data.get("content", ""),
            normalized_content=data.get("normalized_content", ""),
            category=data.get("category", "GENERAL_CANDIDATE"),
            source_type=data.get("source_type", "manual"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            confidence=float(data.get("confidence", 0.8)),
            provenance=data.get("provenance", {}) or {},
            metadata=data.get("metadata", {}) or {},
            status=data.get("status", "STAGED"),
        )


@dataclass
class StageResult:
    """Result of candidate staging operation."""
    success: bool
    candidate_id: str
    status: str  # "STAGED", "ALREADY_EXISTS", "REJECTED_SECRET", "FILTERED_NOISE", "ERROR"
    reason: Optional[str] = None
    candidate: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Content Normalization & Hash Generation
# ---------------------------------------------------------------------------

def normalize_content(content: str) -> str:
    """
    Normalizes candidate text for deterministic hashing and deduplication.
    - Strips leading and trailing whitespace
    - Standardizes newline representations
    - Strips trailing whitespace per line
    - Collapses consecutive empty lines
    - Trims leading/trailing whitespace
    """
    if not content:
        return ""
    text = content.replace("\r\n", "\n").replace("\r", "\n")
    raw_lines = text.split("\n")
    cleaned_lines: List[str] = []
    
    for line in raw_lines:
        trimmed = line.rstrip()
        if not trimmed:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
        else:
            cleaned_lines.append(trimmed)
            
    return "\n".join(cleaned_lines).strip()


def compute_candidate_id(normalized_content: str) -> str:
    """Computes deterministic SHA-256 candidate ID from normalized content."""
    return hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Routine Noise Filtering (Instruction.md Section 9, 93)
# ---------------------------------------------------------------------------

# Commands that represent routine operational noise
NOISE_COMMAND_NAMES = {
    "ls", "dir", "pwd", "whoami", "id", "date", "uptime", "hostname",
    "uname", "true", "false", "clear", "echo"
}

# Subcommands that represent routine status checks
STATUS_CHECK_PATTERNS = [
    re.compile(r"^git\s+status(\s+.*)?$", re.IGNORECASE),
    re.compile(r"^git\s+diff\s*$", re.IGNORECASE),
    re.compile(r"^(systemctl\s+status(\s+.*)?|service\s+[\w\-.]+\s+status.*)$", re.IGNORECASE),
    re.compile(r"^(systemctl\s+is-active|systemctl\s+is-enabled)", re.IGNORECASE),
    re.compile(r"^docker\s+(ps|status|inspect)", re.IGNORECASE),
    re.compile(r"^curl\s+(-I|--head)\s+https?://", re.IGNORECASE),
    re.compile(r"^ping\s+(-c\s+\d+\s+)?[\w\-.]+$", re.IGNORECASE),
    re.compile(r"^which\s+[\w\-.]+$", re.IGNORECASE),
    re.compile(r"^test\s+-[fe]\s+.*$", re.IGNORECASE),
    re.compile(r"^find\s+[\w/.-]+\s+-maxdepth\s+\d+\s*$", re.IGNORECASE),
]

# Conversational routine noise patterns
CONVERSATIONAL_NOISE_PATTERNS = [
    re.compile(r"^(hello|hi|hey|greetings|good\s+(morning|afternoon|evening))\b.*$", re.IGNORECASE),
    re.compile(r"^(ok|okay|k|ack|acknowledged|understood|got\s+it|will\s+do|done|sure|sounds\s+good|proceed|yes|no|yep|nope)[!.? ]*$", re.IGNORECASE),
    re.compile(r"^(thanks|thank\s+you|thx|cheers)[!.? ]*$", re.IGNORECASE),
    re.compile(r"^(i\s+will\s+(proceed|start|begin|do\s+that)|proceeding\s+now|working\s+on\s+it)[!.? ]*$", re.IGNORECASE),
]


def is_tool_noise(
    tool_name: str,
    args: Optional[Dict[str, Any]] = None,
    output: Any = "",
    exit_code: int = 0,
    error: Any = None,
) -> Tuple[bool, str]:
    """
    Determines if a tool execution event is routine operational noise.
    Returns (is_noise: bool, reason: str).
    """
    # A failed tool execution or error is never routine noise
    if exit_code != 0 or bool(error):
        return False, ""

    args = args or {}

    # Read-only exploration tools without mutation or errors
    if tool_name in ["list_dir", "find_by_name", "list_resources"]:
        return True, f"Exploratory read tool '{tool_name}' is routine operational noise"

    # Routine task status checks
    if tool_name == "manage_task":
        action = args.get("Action", "")
        if action in ["status", "list"]:
            return True, f"manage_task action '{action}' is a routine status check"

    # Shell commands inspection
    if tool_name == "run_command":
        cmd_line = args.get("CommandLine", "").strip()
        if not cmd_line:
            return True, "Empty command line"

        # Split into initial command token
        first_token = cmd_line.split()[0].lower() if cmd_line.split() else ""
        base_cmd = os.path.basename(first_token)

        # 1. Routine directory / file listings: ls, dir, pwd
        if base_cmd in ["ls", "dir", "pwd", "whoami", "id", "date", "uptime", "hostname", "uname", "clear"]:
            return True, f"Command '{base_cmd}' is routine inspection noise"

        # 2. Simple echo command (without file redirection or piping)
        if base_cmd == "echo":
            if not any(token in cmd_line for token in [">", ">>", "|", ";", "&"]):
                return True, "Simple echo command without mutation or pipeline is routine noise"

        # 3. Status checks
        for pattern in STATUS_CHECK_PATTERNS:
            if pattern.match(cmd_line):
                return True, f"Command '{cmd_line}' matched routine status check pattern"

        # 4. Trivial zero-output success commands
        out_str = str(output or "").strip()
        if exit_code == 0 and not out_str and base_cmd in ["true", "test"]:
            return True, f"Zero-output clean execution for '{base_cmd}'"

    return False, ""


def is_turn_noise(user_input: Optional[str], assistant_response: Optional[str] = None) -> Tuple[bool, str]:
    """
    Determines if a conversation turn is routine conversational noise.
    Returns (is_noise: bool, reason: str).
    """
    user_text = (user_input or "").strip()
    assist_text = (assistant_response or "").strip()

    # Empty turn
    if not user_text and not assist_text:
        return True, "Empty turn content"

    # Check user input against conversational noise patterns
    if user_text:
        for pattern in CONVERSATIONAL_NOISE_PATTERNS:
            if pattern.match(user_text):
                # Unless assistant response contains explicit architectural/durable keywords
                high_signal_keywords = ["always", "never", "must", "convention", "rule", "architect", "root cause", "workaround"]
                if not any(kw in assist_text.lower() for kw in high_signal_keywords):
                    return True, f"Turn matched routine conversational noise pattern: '{user_text}'"

    # Very short single-word or trivial utterance
    tokens = user_text.lower().split()
    if len(tokens) <= 3:
        if all(t.strip("!.,?") in {"hello", "hi", "hey", "ok", "okay", "ack", "thanks", "done", "yes", "no", "sure"} for t in tokens):
            return True, f"Short trivial utterance: '{user_text}'"

    return False, ""


# ---------------------------------------------------------------------------
# Candidate Bus Core
# ---------------------------------------------------------------------------

class CandidateBus:
    """
    Candidate Memory Bus for experience capture, deduplication, and staging.
    Stages candidates in .agents/memory/inbox/candidates.jsonl.
    """

    def __init__(
        self,
        inbox_file: Optional[str] = None,
        rejected_file: Optional[str] = None,
        scanner: Optional[Any] = None,
        auto_scan_secrets: bool = True
    ):
        env_inbox = os.environ.get("ANTIGRAVITY_CANDIDATES_FILE") or os.environ.get("ANTIGRAVITY_INBOX_FILE")
        self.inbox_path = Path(inbox_file) if inbox_file else (Path(env_inbox) if env_inbox else DEFAULT_INBOX_FILE)

        env_rejected = os.environ.get("ANTIGRAVITY_REJECTED_FILE")
        self.rejected_path = Path(rejected_file) if rejected_file else (Path(env_rejected) if env_rejected else DEFAULT_REJECTED_FILE)
        self.auto_scan_secrets = auto_scan_secrets
        
        # Initialize scanner
        if scanner:
            self.scanner = scanner
        elif SecretScanner is not None:
            self.scanner = SecretScanner()
        else:
            self.scanner = None

        # Ensure directory structure exists
        self._ensure_inbox_dir()
        self._cached_seen_ids: Set[str] = set()
        self._cached_inbox_mtime: float = 0.0
        self._cached_inbox_size: int = 0

    def _ensure_inbox_dir(self):
        """Ensures the inbox directory exists."""
        self.inbox_path.parent.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------------
    # Secret Scanning Gatekeeper
    # -----------------------------------------------------------------------

    def scan_candidate_security(self, candidate: Candidate) -> Tuple[bool, Optional[str]]:
        """
        Scans all candidate fields for secret material using secret_scanner.py.
        Returns (is_clean: bool, violation_summary: Optional[str]).
        """
        if not self.auto_scan_secrets:
            return True, None

        # Gather all text representations of the candidate to scan
        scan_payloads = [
            ("content", candidate.content),
            ("normalized_content", candidate.normalized_content),
            ("provenance", json.dumps(candidate.provenance or {})),
            ("metadata", json.dumps(candidate.metadata or {})),
        ]

        for field_name, text_val in scan_payloads:
            if not text_val:
                continue

            if self.scanner:
                result = self.scanner.scan_text(text_val, target_name=f"candidate.{field_name}")
                if not result.is_clean:
                    return False, f"Secret detected in candidate {field_name}: {result.summary_message}"
            elif scan_text:
                result = scan_text(text_val, target_name=f"candidate.{field_name}")
                if not result.is_clean:
                    return False, f"Secret detected in candidate {field_name}: {result.summary_message}"

        return True, None

    def _record_rejected_secret(self, candidate: Candidate, reason: str):
        """
        Safely records rejected candidate metadata without logging the secret value.
        """
        rejection_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candidate_id": candidate.candidate_id,
            "category": candidate.category,
            "source_type": candidate.source_type,
            "reason": reason,
            "provenance_summary": {
                "tool_name": candidate.provenance.get("tool_name"),
                "session_id": candidate.provenance.get("session_id"),
                "turn_id": candidate.provenance.get("turn_id"),
            }
        }
        try:
            with file_lock(str(self.rejected_path), timeout=5.0):
                with open(self.rejected_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rejection_entry) + "\n")
        except Exception:
            pass  # Avoid breaking execution on logging error

    # -----------------------------------------------------------------------
    # Staging & Idempotency Engine
    # -----------------------------------------------------------------------

    def stage_candidate(
        self,
        content: str,
        category: str = "GENERAL_CANDIDATE",
        source_type: str = "manual",
        provenance: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        confidence: float = 0.8
    ) -> StageResult:
        """
        Validates, checks for secrets, and stages a candidate in candidates.jsonl.
        Enforces strict SHA-256 idempotency.
        """
        content = (content or "").strip()
        if not content:
            return StageResult(
                success=False,
                candidate_id="",
                status="ERROR",
                reason="Candidate content cannot be empty"
            )

        norm_content = normalize_content(content)
        cand_id = compute_candidate_id(norm_content)

        candidate = Candidate(
            candidate_id=cand_id,
            content=content,
            normalized_content=norm_content,
            category=category,
            source_type=source_type,
            created_at=datetime.now(timezone.utc).isoformat(),
            confidence=confidence,
            provenance=provenance or {},
            metadata=metadata or {},
            status="STAGED"
        )

        # 1. Security scan: strictly reject any secrets
        is_clean, violation = self.scan_candidate_security(candidate)
        if not is_clean:
            self._record_rejected_secret(candidate, violation or "Secret detected")
            return StageResult(
                success=False,
                candidate_id=cand_id,
                status="REJECTED_SECRET",
                reason=violation,
                candidate=None
            )

        # 2. Stage to inbox with file lock for concurrency safety and idempotency
        self._ensure_inbox_dir()
        inbox_file_str = str(self.inbox_path)

        with file_lock(inbox_file_str, timeout=5.0):
            # Check for duplicate candidate_id with mtime/size caching
            if self.inbox_path.exists():
                stat = self.inbox_path.stat()
                if stat.st_mtime != self._cached_inbox_mtime or stat.st_size != self._cached_inbox_size:
                    existing_ids: Set[str] = set()
                    with open(self.inbox_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if '"candidate_id": "' in line:
                                start = line.find('"candidate_id": "') + len('"candidate_id": "')
                                end = line.find('"', start)
                                if end != -1:
                                    existing_ids.add(line[start:end])
                    self._cached_seen_ids = existing_ids
                    self._cached_inbox_mtime = stat.st_mtime
                    self._cached_inbox_size = stat.st_size
            else:
                self._cached_seen_ids = set()
                self._cached_inbox_mtime = 0.0
                self._cached_inbox_size = 0

            # Idempotency check: candidate already staged
            if cand_id in self._cached_seen_ids:
                return StageResult(
                    success=True,
                    candidate_id=cand_id,
                    status="ALREADY_EXISTS",
                    reason=f"Candidate {cand_id} already staged in inbox (idempotent)",
                    candidate=candidate.to_dict()
                )

            # Append new candidate record
            with open(self.inbox_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(candidate.to_dict()) + "\n")
                f.flush()

            self._cached_seen_ids.add(cand_id)
            try:
                stat = self.inbox_path.stat()
                self._cached_inbox_mtime = stat.st_mtime
                self._cached_inbox_size = stat.st_size
            except Exception:
                pass

        return StageResult(
            success=True,
            candidate_id=cand_id,
            status="STAGED",
            reason=f"Candidate {cand_id} successfully staged in inbox",
            candidate=candidate.to_dict()
        )

    # -----------------------------------------------------------------------
    # Experience Capture: Tool Execution Events (Instruction.md Section 92-93)
    # -----------------------------------------------------------------------

    def capture_tool_event(
        self,
        tool_name: str,
        args: Optional[Dict[str, Any]] = None,
        output: Any = "",
        error: Any = None,
        exit_code: int = 0,
        session_id: Optional[str] = None,
        turn_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StageResult:
        """
        Captures memory candidate from a tool execution event.
        - Filters out routine noise (ls, simple echo, status checks).
        - Extracts high-signal operational discoveries, failures, workarounds, or state mutations.
        - Attaches typed provenance and output hashes per Section 93.
        """
        args = args or {}
        out_str = str(output or "")
        err_str = str(error or "") if error else ""

        # 1. Noise filtering
        is_noise, noise_reason = is_tool_noise(tool_name, args, output=out_str, exit_code=exit_code, error=err_str)
        if is_noise:
            return StageResult(
                success=False,
                candidate_id="",
                status="FILTERED_NOISE",
                reason=noise_reason
            )

        # 2. Output hashing & excerpt per Instruction.md Section 93
        output_combined = (out_str + "\n" + err_str).strip()
        output_hash = hashlib.sha256(output_combined.encode("utf-8")).hexdigest() if output_combined else ""
        output_excerpt = output_combined[:500] if output_combined else ""

        # Build typed provenance
        provenance = {
            "source_type": "tool_event",
            "tool_name": tool_name,
            "command": args.get("CommandLine") or args.get("command") or "",
            "cwd": args.get("Cwd") or "",
            "exit_code": exit_code,
            "session_id": session_id,
            "turn_id": turn_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "output_hash": output_hash,
            "output_excerpt": output_excerpt,
            "affected_files": [args.get("TargetFile")] if args.get("TargetFile") else [],
        }

        # 3. Candidate content & category extraction based on tool type & outcome
        candidate_content = ""
        category = "GENERAL_CANDIDATE"

        if tool_name == "run_command":
            cmd = args.get("CommandLine", "").strip()
            if exit_code != 0 or err_str:
                category = "BUG_ROOT_CAUSE"
                error_summary = err_str.strip() or output_excerpt.strip() or f"Exit code {exit_code}"
                candidate_content = f"Command failed: `{cmd}` with exit code {exit_code}. Error: {error_summary}"
            else:
                # High-signal command success (e.g. test, build, install, security scan)
                category = "SUCCESSFUL_FIX" if any(w in cmd for w in ["fix", "patch", "repair"]) else "REPEATED_WORKFLOW"
                candidate_content = f"Executed command successfully: `{cmd}`. Result: {output_excerpt.strip() or 'Completed with exit code 0'}"

        elif tool_name in ["write_to_file", "replace_file_content"]:
            target_file = args.get("TargetFile", "")
            description = args.get("Description", "") or args.get("Instruction", "")
            if exit_code != 0 or err_str:
                category = "BUG_ROOT_CAUSE"
                error_summary = err_str.strip() or output_excerpt.strip() or f"Exit code {exit_code}"
                candidate_content = f"File modification failed for `{target_file}` ({tool_name}): {error_summary}"
            else:
                category = "ARCHITECTURAL_DECISION" if any(w in description.lower() for w in ["architect", "design", "refactor"]) else "PROJECT_CONVENTION"
                candidate_content = f"Updated `{target_file}`: {description or 'Modified file content'}"

        else:
            if exit_code != 0 or err_str:
                category = "BUG_ROOT_CAUSE"
                error_summary = err_str.strip() or output_excerpt.strip() or f"Exit code {exit_code}"
                candidate_content = f"Tool `{tool_name}` failed with exit code {exit_code}. Error: {error_summary}"
            else:
                category = "TOOL_BEHAVIOR"
                candidate_content = f"Tool `{tool_name}` execution: {output_excerpt.strip() or 'Executed successfully'}"

        # 4. Stage candidate
        return self.stage_candidate(
            content=candidate_content,
            category=category,
            source_type="tool_event",
            provenance=provenance,
            metadata=metadata or {},
            confidence=0.85 if exit_code == 0 else 0.9
        )

    # -----------------------------------------------------------------------
    # Experience Capture: Session Turns (Instruction.md Section 90)
    # -----------------------------------------------------------------------

    def capture_session_turn(
        self,
        user_input: Optional[str] = None,
        assistant_response: Optional[str] = None,
        session_id: Optional[str] = None,
        turn_id: Optional[str] = None,
        turn_index: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StageResult:
        """
        Captures memory candidate from a session turn.
        - Filters routine conversational noise (greetings, acknowledgments).
        - Identifies high-signal user preferences, corrections, or decisions.
        - Stages candidate with session turn provenance.
        """
        user_text = (user_input or "").strip()
        assist_text = (assistant_response or "").strip()

        # 1. Noise filtering
        is_noise, noise_reason = is_turn_noise(user_text, assist_text)
        if is_noise:
            return StageResult(
                success=False,
                candidate_id="",
                status="FILTERED_NOISE",
                reason=noise_reason
            )

        # 2. High-signal semantic classification & extraction
        category = "GENERAL_CANDIDATE"
        content_extracted = ""

        # Check for explicit user preferences or rules
        lower_user = user_text.lower()
        if any(kw in lower_user for kw in ["always", "never", "must", "prefer", "convention", "rule"]):
            category = "USER_PREFERENCE"
            content_extracted = user_text
        # Check for architectural decisions or guidelines
        elif any(kw in lower_user for kw in ["architect", "decision", "design", "pattern", "structure"]):
            category = "ARCHITECTURAL_DECISION"
            content_extracted = user_text
        # Check for corrections
        elif any(kw in lower_user for kw in ["don't do that", "that is wrong", "incorrect", "correction", "do not use"]):
            category = "EXPLICIT_CORRECTION"
            content_extracted = user_text
        # Check for bug root causes or problem descriptions
        elif any(kw in lower_user for kw in ["bug", "error", "failed", "crash", "issue", "root cause"]):
            category = "BUG_ROOT_CAUSE"
            content_extracted = user_text
        else:
            # Fallback to combined turn representation
            category = "PROJECT_CONVENTION"
            content_extracted = user_text if user_text else assist_text

        # Provenance
        provenance = {
            "source_type": "session_turn",
            "session_id": session_id,
            "turn_id": turn_id,
            "turn_index": turn_index,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_prompt_snippet": user_text[:200] if user_text else "",
            "assistant_response_snippet": assist_text[:200] if assist_text else "",
        }

        return self.stage_candidate(
            content=content_extracted,
            category=category,
            source_type="session_turn",
            provenance=provenance,
            metadata=metadata or {},
            confidence=0.85
        )

    # -----------------------------------------------------------------------
    # Inbox Query & Inspection APIs
    # -----------------------------------------------------------------------

    def list_candidates(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Reads and filters candidates currently in inbox."""
        candidates: List[Dict[str, Any]] = []
        if not self.inbox_path.exists():
            return candidates

        with file_lock(str(self.inbox_path), timeout=5.0):
            with open(self.inbox_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                        if category and item.get("category") != category:
                            continue
                        if status and item.get("status") != status:
                            continue
                        candidates.append(item)
                    except json.JSONDecodeError:
                        continue
        return candidates

    def get_candidate(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific candidate by candidate_id."""
        for item in self.list_candidates():
            if item.get("candidate_id") == candidate_id:
                return item
        return None

    def clear_inbox(self) -> int:
        """Clears all staged candidates from inbox (primarily for testing/maintenance)."""
        if not self.inbox_path.exists():
            return 0

        with file_lock(str(self.inbox_path), timeout=5.0):
            count = len(self.list_candidates())
            with open(self.inbox_path, "w", encoding="utf-8") as f:
                f.write("")
        return count


# ---------------------------------------------------------------------------
# CLI & Self-Test Verification
# ---------------------------------------------------------------------------

def run_self_tests() -> bool:
    """Executes thorough self-test of candidate bus, secret scanning, and idempotency."""
    print("=== CandidateBus Self-Test & Verification ===")
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_inbox = Path(tmp_dir) / "candidates.jsonl"
        tmp_rejected = Path(tmp_dir) / "rejected.jsonl"
        bus = CandidateBus(inbox_file=str(tmp_inbox), rejected_file=str(tmp_rejected))

        # Test 1: Clean candidate staging
        print("\n[Test 1] Staging synthetic high-signal candidate...")
        c1_content = "Always compile native C++ modules with -Wall -Wextra -Werror in this workspace."
        res1 = bus.stage_candidate(
            content=c1_content,
            category="PROJECT_CONVENTION",
            source_type="manual",
            provenance={"user": "engineer", "env": "devcontainer"}
        )
        assert res1.success is True, f"Failed clean staging: {res1.reason}"
        assert res1.status == "STAGED", f"Unexpected status: {res1.status}"
        assert len(res1.candidate_id) == 64, "candidate_id must be 64-char SHA-256"
        print(f"  ✓ Candidate staged: {res1.candidate_id} (status={res1.status})")

        # Test 2: Idempotency on duplicate content
        print("\n[Test 2] Staging duplicate event (verifying idempotency)...")
        res2 = bus.stage_candidate(
            content="   " + c1_content + "   \n\n",  # White-space variation should normalize identically
            category="PROJECT_CONVENTION",
            source_type="manual"
        )
        assert res2.success is True, "Duplicate staging should succeed idempotently"
        assert res2.status == "ALREADY_EXISTS", f"Expected ALREADY_EXISTS, got {res2.status}"
        assert res2.candidate_id == res1.candidate_id, "Candidate ID must match exactly"
        
        # Verify inbox has exactly 1 entry
        candidates = bus.list_candidates()
        assert len(candidates) == 1, f"Expected 1 candidate in inbox, found {len(candidates)}"
        print(f"  ✓ Idempotency verified: identical candidate_id {res2.candidate_id}, 1 staged record")

        # Test 3: Secret rejection gatekeeper (constructed dynamically to avoid static scan trip)
        print("\n[Test 3] Testing secret rejection gatekeeper...")
        key_prefix = "sk" + "-proj-"
        key_body = "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"
        secret_sample = f"export TEST_KEY={key_prefix}{key_body}\nUse this in scripts."
        res3 = bus.stage_candidate(
            content=secret_sample,
            category="PROJECT_CONVENTION"
        )
        assert res3.success is False, "Secret candidate must be rejected"
        assert res3.status == "REJECTED_SECRET", f"Expected REJECTED_SECRET, got {res3.status}"
        print(f"  ✓ Secret candidate rejected immediately: {res3.reason}")

        # Ensure no secret entered the inbox
        candidates = bus.list_candidates()
        assert len(candidates) == 1, "Secret candidate must never enter candidates.jsonl"
        assert tmp_rejected.exists(), "Rejected secret must be recorded in rejection ledger"
        print("  ✓ Inbox remains clean (0 secret leaks)")

        # Test 4: Routine noise filtering on tool events
        print("\n[Test 4] Testing routine tool noise filtering...")
        noise_cmd_res = bus.capture_tool_event(
            tool_name="run_command",
            args={"CommandLine": "ls -la /workspaces"},
            output="drwxr-xr-x ...",
            exit_code=0
        )
        assert noise_cmd_res.status == "FILTERED_NOISE", f"Expected FILTERED_NOISE for ls, got {noise_cmd_res.status}"
        print(f"  ✓ Tool noise filtered: 'ls -la' -> {noise_cmd_res.reason}")

        noise_echo_res = bus.capture_tool_event(
            tool_name="run_command",
            args={"CommandLine": "echo 'build done'"},
            output="build done",
            exit_code=0
        )
        assert noise_echo_res.status == "FILTERED_NOISE", "Simple echo must be filtered"
        print(f"  ✓ Tool noise filtered: simple echo -> {noise_echo_res.reason}")

        noise_status_res = bus.capture_tool_event(
            tool_name="run_command",
            args={"CommandLine": "git status --short"},
            output="",
            exit_code=0
        )
        assert noise_status_res.status == "FILTERED_NOISE", "git status must be filtered"
        print(f"  ✓ Tool noise filtered: git status -> {noise_status_res.reason}")

        # Test 5: High-signal tool capture
        print("\n[Test 5] Testing high-signal tool event capture...")
        high_signal_tool = bus.capture_tool_event(
            tool_name="run_command",
            args={"CommandLine": "ninja -C build", "Cwd": "/workspaces/codespaces-blank"},
            output="FAILED: CMakeFiles/app.dir/main.cpp.o\nundefined reference to `foo`",
            exit_code=1,
            session_id="sess-42",
            turn_id="turn-7"
        )
        assert high_signal_tool.success is True, f"Failed high-signal capture: {high_signal_tool.reason}"
        assert high_signal_tool.status == "STAGED", f"Expected STAGED, got {high_signal_tool.status}"
        print(f"  ✓ High-signal build failure captured: {high_signal_tool.candidate_id}")

        # Test 6: Conversational noise filtering on session turns
        print("\n[Test 6] Testing conversational turn noise filtering...")
        turn_noise = bus.capture_session_turn(user_input="hello", assistant_response="Hi! How can I help?")
        assert turn_noise.status == "FILTERED_NOISE", f"Expected FILTERED_NOISE, got {turn_noise.status}"
        print(f"  ✓ Turn noise filtered: 'hello' -> {turn_noise.reason}")

        # Test 7: High-signal session turn capture
        print("\n[Test 7] Testing high-signal session turn capture...")
        turn_signal = bus.capture_session_turn(
            user_input="Always use --no-daemon when running gradlew on this machine.",
            assistant_response="Understood, I will enforce --no-daemon for all gradle invocations.",
            session_id="sess-42",
            turn_id="turn-8"
        )
        assert turn_signal.success is True, f"Failed high-signal turn: {turn_signal.reason}"
        assert turn_signal.status == "STAGED", f"Expected STAGED, got {turn_signal.status}"
        print(f"  ✓ High-signal preference turn captured: {turn_signal.candidate_id}")

    print("\n✓ ALL SELF-TESTS PASSED SUCCESSFULLY.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Candidate Memory Bus CLI (Phase 4)")
    parser.add_argument("--test", action="store_true", help="Run comprehensive test and verification suite")
    parser.add_argument("--list", action="store_true", help="List staged candidates in inbox")
    parser.add_argument("--category", type=str, help="Filter candidate list by category")
    parser.add_argument("--inspect", type=str, help="Inspect detailed JSON of specific candidate_id")
    parser.add_argument("--stage-content", type=str, help="Stage raw candidate content string")
    parser.add_argument("--source", type=str, default="manual", help="Source type for staged content")
    parser.add_argument("--inbox", type=str, help="Override inbox file path")
    parser.add_argument("--clear", action="store_true", help="Clear candidates in inbox")

    args = parser.parse_args()
    bus = CandidateBus(inbox_file=args.inbox)

    if args.test:
        success = run_self_tests()
        sys.exit(0 if success else 1)

    if args.clear:
        count = bus.clear_inbox()
        print(f"Cleared {count} candidate(s) from inbox: {bus.inbox_path}")
        return

    if args.stage_content:
        res = bus.stage_candidate(
            content=args.stage_content,
            category=args.category or "GENERAL_CANDIDATE",
            source_type=args.source
        )
        print(json.dumps(res.to_dict(), indent=2))
        return

    if args.inspect:
        cand = bus.get_candidate(args.inspect)
        if cand:
            print(json.dumps(cand, indent=2))
        else:
            print(f"Candidate not found: {args.inspect}", file=sys.stderr)
            sys.exit(1)
        return

    if args.list:
        candidates = bus.list_candidates(category=args.category)
        print(f"Inbox: {bus.inbox_path} ({len(candidates)} staged candidates)")
        for idx, c in enumerate(candidates, 1):
            print(f"{idx}. [{c.get('category')}] {c.get('candidate_id')[:16]}... | {c.get('content')[:70]}")
        return

    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
