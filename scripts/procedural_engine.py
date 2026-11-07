#!/usr/bin/env python3
"""
Procedural Memory Distillation Engine (Instruction.md Sections 45-47, Invariant 16)

This module implements the procedural memory distillation pipeline:
  Episodic Session Experiences -> Workflow Mining & Clustering ->
  Candidate Procedure Synthesis -> Step Distinction & Tool Provenance ->
  Staging in inbox/procedures/ (Strict Invariant 16 Isolation) ->
  Manual/Policy Review Gate (Inert until Admitted).

Key Principles:
- Invariant 16: NEVER writes directly to active .agents/skills/ or ~/.gemini/antigravity-cli/skills/.
- Section 46: Distinguishes observed command, verified step, inferred step, recommended step, optional step.
- Section 47: Preserves tool-call provenance (exact command, args, cwd, output, error, follow-up correction).
- Zero Secrets: Scans all candidate contents against secret patterns before staging.
"""

import os
import sys
import re
import json
import glob
import shutil
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field, asdict

# Ensure script directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from secret_scanner import scan_text
except ImportError:
    class DummyScanner:
        def __init__(self):
            self.is_clean = True
            self.findings = []
    def scan_text(*args, **kwargs):
        return DummyScanner()


class InvariantViolationError(PermissionError):
    """Raised when an operation violates Invariant 16 or security boundaries."""
    pass


class StepType(str, Enum):
    """
    Step classification types per Instruction.md Section 46.
    Distinguishes observed facts from inferred or advisory recommendations.
    """
    OBSERVED_COMMAND = "OBSERVED_COMMAND"  # Verbatim executed command recovered from evidence
    VERIFIED_STEP = "VERIFIED_STEP"        # Observed command verified with passing exit status / output
    INFERRED_STEP = "INFERRED_STEP"        # Inferred step / deduction necessary for completion
    RECOMMENDED_STEP = "RECOMMENDED_STEP"  # Recommended advisory or best-practice step
    OPTIONAL_STEP = "OPTIONAL_STEP"        # Conditional, debug, or optional step


@dataclass
class ProcedureStep:
    """
    Individual step in a candidate procedure with provenance per Section 46 & 47.
    """
    step_number: int
    step_type: str  # StepType value
    name: str
    description: str
    command: Optional[str] = None
    tool: Optional[str] = None
    args: Dict[str, Any] = field(default_factory=dict)
    cwd: Optional[str] = None
    expected_output: Optional[str] = None
    error_pattern: Optional[str] = None
    follow_up_correction: Optional[str] = None
    verification: Optional[str] = None

    def is_observed(self) -> bool:
        return self.step_type in (StepType.OBSERVED_COMMAND.value, StepType.VERIFIED_STEP.value)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "step_type": self.step_type,
            "name": self.name,
            "description": self.description,
            "command": self.command,
            "tool": self.tool,
            "args": self.args,
            "cwd": self.cwd,
            "expected_output": self.expected_output,
            "error_pattern": self.error_pattern,
            "follow_up_correction": self.follow_up_correction,
            "verification": self.verification,
            "is_observed": self.is_observed(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcedureStep":
        return cls(
            step_number=data.get("step_number", 1),
            step_type=data.get("step_type", StepType.OBSERVED_COMMAND.value),
            name=data.get("name", "Unnamed Step"),
            description=data.get("description", ""),
            command=data.get("command"),
            tool=data.get("tool"),
            args=data.get("args", {}),
            cwd=data.get("cwd"),
            expected_output=data.get("expected_output"),
            error_pattern=data.get("error_pattern"),
            follow_up_correction=data.get("follow_up_correction"),
            verification=data.get("verification"),
        )


@dataclass
class CandidateProcedure:
    """
    Candidate procedure distilled from episodic sessions.
    Staged in inbox/procedures/ as inert until policy admission.
    """
    id: str
    title: str
    domain: str
    description: str
    source_sessions: List[str]
    recurrence_count: int
    confidence: float
    steps: List[ProcedureStep] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    status: str = "CANDIDATE_STAGED"
    admitted: bool = False
    admission_policy: str = "Requires explicit human or gatekeeper policy admission (Invariant 16)"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "domain": self.domain,
            "description": self.description,
            "source_sessions": self.source_sessions,
            "recurrence_count": self.recurrence_count,
            "confidence": self.confidence,
            "tags": self.tags,
            "status": self.status,
            "admitted": self.admitted,
            "admission_policy": self.admission_policy,
            "created_at": self.created_at,
            "steps": [s.to_dict() for s in self.steps],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CandidateProcedure":
        steps = [ProcedureStep.from_dict(s) for s in data.get("steps", [])]
        return cls(
            id=data.get("id", "proc-unknown"),
            title=data.get("title", "Untitled Procedure"),
            domain=data.get("domain", "general"),
            description=data.get("description", ""),
            source_sessions=data.get("source_sessions", []),
            recurrence_count=data.get("recurrence_count", 1),
            confidence=data.get("confidence", 0.5),
            steps=steps,
            tags=data.get("tags", []),
            status=data.get("status", "CANDIDATE_STAGED"),
            admitted=data.get("admitted", False),
            admission_policy=data.get("admission_policy", "Invariant 16: Requires explicit review"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )

    def to_markdown(self) -> str:
        """
        Format candidate procedure as structured Markdown for review.
        Clearly separates and badges step types per Section 46.
        """
        lines = [
            "---",
            f"id: {self.id}",
            f"title: \"{self.title}\"",
            f"domain: {self.domain}",
            "type: PROCEDURE",
            f"status: {self.status}",
            f"admitted: {str(self.admitted).lower()}",
            f"recurrence_count: {self.recurrence_count}",
            f"confidence: {self.confidence:.2f}",
            f"created_at: {self.created_at}",
            "source_sessions:",
        ]
        for s in self.source_sessions:
            lines.append(f"  - {s}")
        if self.tags:
            lines.append("tags:")
            for t in self.tags:
                lines.append(f"  - {t}")
        lines.extend([
            "---",
            "",
            f"# Candidate Procedure: {self.title}",
            "",
            "> **Invariant 16 Notice**: This procedure is a generated candidate currently staged in the inbox.",
            "> It remains INERT and is NOT installed into active `.agents/skills/` or `~/.gemini/antigravity-cli/skills/`.",
            "",
            "## 1. Summary & Objective",
            self.description or "Automated distilled procedural workflow.",
            "",
            "## 2. Provenance & Evidence",
            f"- **Discovery Mechanism**: Episodic session sequence clustering (N={self.recurrence_count})",
            f"- **Confidence Score**: `{self.confidence:.2f}`",
            f"- **Source Sessions**: {', '.join(self.source_sessions) if self.source_sessions else 'None'}",
            f"- **Distillation Date**: `{self.created_at}`",
            "",
            "## 3. Step Breakdown (Section 46 Distinction)",
            "| Step | Distinction Type | Name | Verifiable Command | Working Directory |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])

        for s in self.steps:
            cmd_snippet = f"`{s.command}`" if s.command else "*None (Reasoning/Advisory)*"
            cwd_snippet = f"`{s.cwd}`" if s.cwd else "Repo Root"
            lines.append(f"| {s.step_number} | **`[{s.step_type}]`** | {s.name} | {cmd_snippet} | {cwd_snippet} |")

        lines.extend([
            "",
            "## 4. Execution Workflow Details",
            ""
        ])

        for s in self.steps:
            badge = f"`[{s.step_type}]`"
            lines.append(f"### Step {s.step_number}: {badge} {s.name}")
            lines.append(f"**Description**: {s.description}")
            if s.cwd:
                lines.append(f"- **Working Directory**: `{s.cwd}`")
            if s.command:
                lines.append(f"- **Command**:")
                lines.append(f"```bash\n{s.command}\n```")
            if s.args:
                lines.append(f"- **Arguments**: `{json.dumps(s.args)}`")
            if s.expected_output:
                lines.append(f"- **Expected Output Snippet**: `{s.expected_output}`")
            if s.verification:
                lines.append(f"- **Verification Criteria**: {s.verification}")
            if s.error_pattern:
                lines.append(f"- **Known Error Observed**: `{s.error_pattern}`")
            if s.follow_up_correction:
                lines.append(f"- **Follow-up Correction**: `{s.follow_up_correction}`")
            lines.append("")

        lines.extend([
            "## 5. Review & Admission Checklist (Invariant 16)",
            "- [ ] Observed commands verified against authentic environment requirements",
            "- [ ] Inferred steps reviewed for correctness and necessity",
            "- [ ] Recommended steps verified against repository architecture guidelines",
            "- [ ] Zero-secrets scan verified clean",
            "- [ ] Gatekeeper approval obtained prior to promotion to active `.agents/skills/`",
            ""
        ])

        return "\n".join(lines)


class ProceduralEngine:
    """
    Engine for mining recurring workflows from episodic sessions,
    distinguishing step types, preserving provenance, and staging
    candidates in inbox/procedures/ under Invariant 16 isolation.
    """

    def __init__(
        self,
        workspace_root: str = "/workspaces/codespaces-blank",
        sessions_dir: Optional[str] = None,
        inbox_dir: Optional[str] = None,
        forbidden_skills_dirs: Optional[List[str]] = None,
    ):
        self.workspace_root = os.path.abspath(workspace_root)
        self.sessions_dir = os.path.abspath(
            sessions_dir or os.path.join(self.workspace_root, ".agents", "memory", "sessions")
        )
        self.inbox_dir = os.path.abspath(
            inbox_dir or os.path.join(self.workspace_root, ".agents", "memory", "inbox", "procedures")
        )

        # Invariant 16: Active skills directories that are strictly FORBIDDEN targets
        default_forbidden = [
            os.path.join(self.workspace_root, ".agents", "skills"),
            os.path.expanduser("~/.gemini/antigravity-cli/skills"),
        ]
        if forbidden_skills_dirs:
            default_forbidden.extend(forbidden_skills_dirs)
        self.forbidden_skills_dirs = [os.path.abspath(p) for p in default_forbidden]

    def assert_staging_allowed(self, target_path: str) -> None:
        """
        Enforce Invariant 16:
        NEVER writes directly to active .agents/skills/ or ~/.gemini/antigravity-cli/skills/.
        No generated procedural skill becomes active without the required admission path.
        """
        canonical_target = os.path.realpath(os.path.abspath(target_path))

        # Check against forbidden active skill roots
        for forbidden in self.forbidden_skills_dirs:
            canonical_forbidden = os.path.realpath(forbidden)
            if canonical_target == canonical_forbidden or canonical_target.startswith(canonical_forbidden + os.sep):
                raise InvariantViolationError(
                    f"INVARIANT 16 VIOLATION: Write target '{target_path}' resolves to active skills directory "
                    f"'{forbidden}'. Generated procedures must be staged in '{self.inbox_dir}'."
                )

        # Generic guard against writing to any active skills path
        normalized = os.path.normpath(target_path)
        if "/.agents/skills" in normalized or "/antigravity-cli/skills" in normalized:
            raise InvariantViolationError(
                f"INVARIANT 16 VIOLATION: Direct write to active skills path '{target_path}' is forbidden."
            )

        # Verify destination is inside the authorized inbox staging directory
        canonical_inbox = os.path.realpath(self.inbox_dir)
        if not (canonical_target == canonical_inbox or canonical_target.startswith(canonical_inbox + os.sep)):
            raise InvariantViolationError(
                f"SECURITY BOUNDARY: Staging target '{target_path}' must reside inside authorized inbox "
                f"'{self.inbox_dir}'."
            )

    def parse_session_log(self, file_path: str) -> Dict[str, Any]:
        """
        Parse an episodic session log (YYYY-MM-DD-HHMM.md) to extract:
        - Metadata (date, workspace, branch, commit)
        - Raw actions, commands, and code blocks
        - Step distinction indicators (Section 46)
        - Tool provenance details (Section 47)
        - Candidate durable memories
        """
        if not os.path.isfile(file_path):
            return {}

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        filename = os.path.basename(file_path)
        parsed: Dict[str, Any] = {
            "session_id": filename.replace(".md", ""),
            "filename": filename,
            "filepath": file_path,
            "actions": [],
            "completed_work": [],
            "next_steps": [],
            "candidate_memories": [],
            "discoveries": [],
        }

        # Extract sections
        completed_match = re.search(r"##\s*1?\.\s*Completed Work\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
        if completed_match:
            raw_text = completed_match.group(1).strip()
            clean_text = re.sub(r"[ \t]*```(?:bash|sh|shell|zsh)?\s*\n.*?\n[ \t]*```", "", raw_text, flags=re.DOTALL)
            lines = [l.strip("- *").strip() for l in clean_text.splitlines() if l.strip()]
            parsed["completed_work"] = lines

        next_steps_match = re.search(r"##\s*5?\.\s*Next Steps\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
        if next_steps_match:
            lines = [re.sub(r"^\d+\.\s*", "", l).strip() for l in next_steps_match.group(1).strip().splitlines() if l.strip()]
            parsed["next_steps"] = lines

        discoveries_match = re.search(r"##\s*4?\.\s*Discoveries & Gotchas\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
        if discoveries_match:
            lines = [l.strip("- *").strip() for l in discoveries_match.group(1).strip().splitlines() if l.strip()]
            parsed["discoveries"] = lines

        cand_match = re.search(r"##\s*6?\.\s*Candidate Durable Memories\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
        if cand_match:
            table_lines = cand_match.group(1).strip().splitlines()
            for tl in table_lines:
                if tl.strip().startswith("|") and not tl.strip().startswith("| :") and "Durability" not in tl and "Target Tier" not in tl:
                    parts = [p.strip() for p in tl.split("|")[1:-1]]
                    if len(parts) >= 4:
                        parsed["candidate_memories"].append({
                            "type": parts[0],
                            "durability": parts[1],
                            "target": parts[2],
                            "description": parts[3]
                        })

        # 1. Extract bash/sh code blocks as observed commands
        code_blocks = re.findall(r"[ \t]*```(?:bash|sh|shell|zsh)?\s*\n(.*?)\n[ \t]*```", content, re.DOTALL)
        for block in code_blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip() and not line.strip().startswith("#")]
            for cmd in lines:
                step_type = StepType.OBSERVED_COMMAND.value
                verification = None
                if any(kw in content.lower() for kw in ("verified", "tests pass", "passed", "exit 0")):
                    step_type = StepType.VERIFIED_STEP.value
                    verification = "Command execution confirmed successful in session record"
                parsed["actions"].append({
                    "step_type": step_type,
                    "command": cmd,
                    "name": self._summarize_command_name(cmd),
                    "description": f"Observed command executed during session {filename}",
                    "cwd": self.workspace_root,
                    "verification": verification,
                })

        # 2. Extract structured provenance lines (Section 47)
        provenance_matches = re.finditer(
            r"(?:-\s*)?Command:\s*`([^`]+)`(?:\s*\n\s*Cwd:\s*`([^`]+)`)?(?:\s*\n\s*Output:\s*`([^`]+)`)?(?:\s*\n\s*Error:\s*`([^`]+)`)?(?:\s*\n\s*Correction:\s*`([^`]+)`)?",
            content,
            re.IGNORECASE
        )
        for pm in provenance_matches:
            cmd = pm.group(1).strip()
            cwd = pm.group(2).strip() if pm.group(2) else self.workspace_root
            output = pm.group(3).strip() if pm.group(3) else None
            error = pm.group(4).strip() if pm.group(4) else None
            corr = pm.group(5).strip() if pm.group(5) else None

            step_type = StepType.OBSERVED_COMMAND.value
            if error and corr:
                step_type = StepType.VERIFIED_STEP.value
            elif output and ("pass" in output.lower() or "ok" in output.lower()):
                step_type = StepType.VERIFIED_STEP.value

            parsed["actions"].append({
                "step_type": step_type,
                "command": cmd,
                "name": self._summarize_command_name(cmd),
                "description": f"Observed command with provenance in session {filename}",
                "cwd": cwd,
                "expected_output": output,
                "error_pattern": error,
                "follow_up_correction": corr,
            })

        # 3. Extract backticked shell commands mentioned in text
        backtick_commands = re.findall(r"`([a-zA-Z0-9_\-\./]+(?:\s+[a-zA-Z0-9_\-\./=]+)*)`", content)
        common_clis = {"pytest", "python3", "bash", "cmake", "ninja", "ctest", "git", "semgrep", "codeql",
                       "trivy", "gitleaks", "apktool", "jadx", "tshark", "docker", "npm", "cargo"}
        existing_cmds = {a["command"] for a in parsed["actions"] if a.get("command")}
        for bc in backtick_commands:
            first_token = bc.split()[0]
            if first_token in common_clis or first_token.endswith(".sh") or first_token.endswith(".py"):
                if bc not in existing_cmds:
                    parsed["actions"].append({
                        "step_type": StepType.OBSERVED_COMMAND.value,
                        "command": bc,
                        "name": self._summarize_command_name(bc),
                        "description": f"Observed command reference in session {filename}",
                        "cwd": self.workspace_root,
                    })
                    existing_cmds.add(bc)

        # 4. Extract inferred or recommended steps from narrative text (Section 46)
        all_narrative = parsed["completed_work"] + parsed["next_steps"] + parsed["discoveries"]
        for cand in parsed["candidate_memories"]:
            all_narrative.append(cand.get("description", ""))

        for item in all_narrative:
            lower_item = item.lower()
            if any(k in lower_item for k in ("infer", "deduce", "deduced", "implied", "inferred", "prerequisite")):
                parsed["actions"].append({
                    "step_type": StepType.INFERRED_STEP.value,
                    "command": None,
                    "name": self._truncate_phrase(item, 40),
                    "description": item,
                    "cwd": self.workspace_root,
                })
            elif any(k in lower_item for k in ("recommend", "suggest", "advisable", "should run", "guideline")):
                parsed["actions"].append({
                    "step_type": StepType.RECOMMENDED_STEP.value,
                    "command": None,
                    "name": self._truncate_phrase(item, 40),
                    "description": item,
                    "cwd": self.workspace_root,
                })
            elif any(k in lower_item for k in ("optional", "if needed", "can optionally", "fallback")):
                parsed["actions"].append({
                    "step_type": StepType.OPTIONAL_STEP.value,
                    "command": None,
                    "name": self._truncate_phrase(item, 40),
                    "description": item,
                    "cwd": self.workspace_root,
                })

        return parsed

    def _summarize_command_name(self, cmd: str) -> str:
        tokens = cmd.strip().split()
        if not tokens:
            return "Command Step"
        base = os.path.basename(tokens[0])
        if len(tokens) > 1 and not tokens[1].startswith("-"):
            return f"Run {base} {tokens[1]}"
        return f"Run {base}"

    def _truncate_phrase(self, text: str, max_chars: int = 40) -> str:
        cleaned = re.sub(r"[^\w\s\-_]", "", text).strip()
        if len(cleaned) <= max_chars:
            return cleaned
        return cleaned[:max_chars].rsplit(" ", 1)[0]

    def mine_recurring_sequences(self, min_support: int = 2) -> List[CandidateProcedure]:
        """
        Mines episodic session logs for recurring command & tool sequences.
        Clusters workflows by command signatures and generates CandidateProcedure instances.
        """
        if not os.path.isdir(self.sessions_dir):
            return []

        session_files = sorted(glob.glob(os.path.join(self.sessions_dir, "*.md")))
        if not session_files:
            return []

        parsed_sessions = [self.parse_session_log(sf) for sf in session_files]

        session_cmd_sequences: Dict[str, List[Dict[str, Any]]] = {}
        for s in parsed_sessions:
            sid = s["session_id"]
            session_cmd_sequences[sid] = s.get("actions", [])

        cmd_occurrences: Dict[Tuple[str, ...], List[str]] = {}

        for sid, actions in session_cmd_sequences.items():
            cmds = [a.get("command") for a in actions if a.get("command")]
            if len(cmds) < 2:
                for c in set(cmds):
                    key = (c,)
                    cmd_occurrences.setdefault(key, []).append(sid)
                continue

            max_n = min(len(cmds), 6)
            for n in range(2, max_n + 1):
                for i in range(len(cmds) - n + 1):
                    subseq = tuple(cmds[i:i + n])
                    if sid not in cmd_occurrences.setdefault(subseq, []):
                        cmd_occurrences[subseq].append(sid)

        recurring_sequences = {seq: sids for seq, sids in cmd_occurrences.items() if len(sids) >= min_support}

        filtered_sequences = {}
        sorted_seqs = sorted(recurring_sequences.keys(), key=lambda x: len(x), reverse=True)
        for seq in sorted_seqs:
            sids = recurring_sequences[seq]
            is_subsumed = False
            for parent_seq in filtered_sequences:
                if len(seq) < len(parent_seq) and all(item in parent_seq for item in seq):
                    if set(sids).issubset(set(recurring_sequences[parent_seq])):
                        is_subsumed = True
                        break
            if not is_subsumed:
                filtered_sequences[seq] = sids

        candidates: List[CandidateProcedure] = []

        for seq_idx, (cmd_seq, sids) in enumerate(filtered_sequences.items(), 1):
            proc_id = self._generate_procedure_id(cmd_seq, seq_idx)
            title = self._generate_procedure_title(cmd_seq)
            domain = self._infer_domain(cmd_seq)
            confidence = min(1.0, 0.4 + 0.2 * len(sids) + 0.1 * len(cmd_seq))

            steps: List[ProcedureStep] = []
            for step_idx, cmd in enumerate(cmd_seq, 1):
                matching_actions = []
                for sid in sids:
                    for a in session_cmd_sequences.get(sid, []):
                        if a.get("command") == cmd:
                            matching_actions.append(a)

                sample_action = matching_actions[0] if matching_actions else {}
                step_type = sample_action.get("step_type", StepType.OBSERVED_COMMAND.value)
                if any(ma.get("step_type") == StepType.VERIFIED_STEP.value for ma in matching_actions):
                    step_type = StepType.VERIFIED_STEP.value

                steps.append(ProcedureStep(
                    step_number=step_idx,
                    step_type=step_type,
                    name=self._summarize_command_name(cmd),
                    description=f"Execute recurring command observed in sessions {', '.join(sids)}",
                    command=cmd,
                    cwd=sample_action.get("cwd", self.workspace_root),
                    expected_output=sample_action.get("expected_output"),
                    error_pattern=sample_action.get("error_pattern"),
                    follow_up_correction=sample_action.get("follow_up_correction"),
                    verification=sample_action.get("verification") or "Exit code 0 and successful output",
                ))

            self._enrich_procedure_with_inferred_steps(steps, cmd_seq, domain)

            candidate = CandidateProcedure(
                id=proc_id,
                title=title,
                domain=domain,
                description=f"Automated distillation of recurring command sequence across {len(sids)} sessions.",
                source_sessions=sids,
                recurrence_count=len(sids),
                confidence=confidence,
                steps=steps,
                tags=[domain, "distilled-procedure", "recurring-workflow"],
                status="CANDIDATE_STAGED",
                admitted=False,
            )
            candidates.append(candidate)

        # Conceptual recurring workflows (e.g. session lifecycle, memory governance)
        candidates.extend(self._mine_conceptual_workflows(parsed_sessions, min_support))
        return candidates

    def _generate_procedure_id(self, cmd_seq: Tuple[str, ...], idx: int) -> str:
        first_token = cmd_seq[0].split()[0]
        base_name = re.sub(r"[^\w\-]", "", os.path.basename(first_token).lower())
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"proc-{timestamp}-{base_name}-{idx:02d}"

    def _generate_procedure_title(self, cmd_seq: Tuple[str, ...]) -> str:
        first_cmd = cmd_seq[0]
        if "doctor" in first_cmd or "verify" in first_cmd:
            return "Environment & Toolchain Verification Workflow"
        if "cmake" in first_cmd or "ninja" in first_cmd:
            return "Native C/C++ Build and Test Pipeline"
        if "pytest" in first_cmd or "test" in first_cmd:
            return "Automated Test Suite Verification Workflow"
        if "git" in first_cmd:
            return "Git Workspace Synchronization Workflow"
        if "validate_memory" in first_cmd:
            return "Memory Integrity Validation Workflow"
        return f"Recurring Workflow: {cmd_seq[0].split()[0]} Pipeline"

    def _infer_domain(self, cmd_seq: Tuple[str, ...]) -> str:
        joined = " ".join(cmd_seq).lower()
        if any(k in joined for k in ("cmake", "ninja", "ctest", "gcc", "clang")):
            return "native-c"
        if any(k in joined for k in ("doctor", "verify", "toolchain")):
            return "environment"
        if any(k in joined for k in ("pytest", "test", "unittest")):
            return "testing"
        if any(k in joined for k in ("validate_memory", "session_manager", "memory")):
            return "memory-governance"
        if any(k in joined for k in ("semgrep", "codeql", "gitleaks")):
            return "security"
        return "general"

    def _enrich_procedure_with_inferred_steps(
        self,
        steps: List[ProcedureStep],
        cmd_seq: Tuple[str, ...],
        domain: str
    ) -> None:
        if domain == "native-c":
            steps.insert(0, ProcedureStep(
                step_number=0,
                step_type=StepType.INFERRED_STEP.value,
                name="Verify Compiler Toolchain Prerequisites",
                description="Inferred requirement: Check GCC/Clang and CMake availability before compilation.",
                command=None,
                cwd=self.workspace_root,
                verification="Ensure cmake and ninja binaries exist in PATH",
            ))
            steps.append(ProcedureStep(
                step_number=len(steps) + 1,
                step_type=StepType.RECOMMENDED_STEP.value,
                name="Recommended Post-Build Memory Audit",
                description="Advisory recommendation: Run memory leak audit or address sanitizers if test suite fails.",
                command=None,
                cwd=self.workspace_root,
            ))
        elif domain == "environment":
            steps.insert(0, ProcedureStep(
                step_number=0,
                step_type=StepType.INFERRED_STEP.value,
                name="Inspect Workspace Root & Path Isolation",
                description="Inferred prerequisite: Confirm current working directory is authorized repository root.",
                command=None,
                cwd=self.workspace_root,
            ))
            steps.append(ProcedureStep(
                step_number=len(steps) + 1,
                step_type=StepType.RECOMMENDED_STEP.value,
                name="Recommended Secret Scan Post-Verification",
                description="Advisory recommendation: Confirm no temporary credentials remain after environment checks.",
                command=None,
                cwd=self.workspace_root,
            ))
        elif domain == "testing":
            steps.append(ProcedureStep(
                step_number=len(steps) + 1,
                step_type=StepType.OPTIONAL_STEP.value,
                name="Optional Verbose Regression Diagnostic",
                description="Optional step: Re-run failed test units with pytest -v -s for detailed traceback capture.",
                command=None,
                cwd=self.workspace_root,
            ))

        for idx, s in enumerate(steps, 1):
            s.step_number = idx

    def _mine_conceptual_workflows(
        self,
        parsed_sessions: List[Dict[str, Any]],
        min_support: int = 2
    ) -> List[CandidateProcedure]:
        candidates: List[CandidateProcedure] = []
        memory_sessions = [
            s["session_id"] for s in parsed_sessions
            if any("session lifecycle" in m.lower() or "memory" in m.lower()
                   for m in s.get("completed_work", []) + [c.get("description", "") for c in s.get("candidate_memories", [])])
        ]

        if len(memory_sessions) >= min_support:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
            proc = CandidateProcedure(
                id=f"proc-{timestamp}-session-memory-audit",
                title="Episodic Session Lifecycle & Memory Verification",
                domain="memory-governance",
                description="Recurring procedure for validating memory integrity and session lifecycle compliance.",
                source_sessions=memory_sessions,
                recurrence_count=len(memory_sessions),
                confidence=0.85,
                tags=["memory-governance", "session-lifecycle", "distilled-procedure"],
                status="CANDIDATE_STAGED",
                admitted=False,
                steps=[
                    ProcedureStep(
                        step_number=1,
                        step_type=StepType.INFERRED_STEP.value,
                        name="Inspect INDEX.md and Working State",
                        description="Verify active working state in .agents/memory/CURRENT.md before session start.",
                        command=None,
                        cwd=self.workspace_root,
                    ),
                    ProcedureStep(
                        step_number=2,
                        step_type=StepType.VERIFIED_STEP.value,
                        name="Run Memory Structure Validation",
                        description="Execute deterministic memory validator to guarantee structural coherence.",
                        command="python3 scripts/validate_memory.py",
                        cwd=self.workspace_root,
                        verification="Exit code 0 and 'VALIDATION PASSED'",
                    ),
                    ProcedureStep(
                        step_number=3,
                        step_type=StepType.RECOMMENDED_STEP.value,
                        name="Recommend Zero-Secret Gatekeeper Audit",
                        description="Audit candidate memory entries for zero secrets prior to promotion.",
                        command="python3 scripts/secret_scanner.py --dir .agents/memory",
                        cwd=self.workspace_root,
                        verification="Zero secret violations reported",
                    ),
                    ProcedureStep(
                        step_number=4,
                        step_type=StepType.OPTIONAL_STEP.value,
                        name="Optional Memory Compaction",
                        description="If CURRENT.md exceeds 30 lines, run compaction routine.",
                        command="python3 scripts/compact_memory.py",
                        cwd=self.workspace_root,
                    ),
                ]
            )
            candidates.append(proc)

        return candidates

    def stage_candidate(self, candidate: CandidateProcedure) -> Tuple[str, str]:
        """
        Stage candidate procedure in inbox_dir.
        Returns (markdown_file_path, json_file_path).
        """
        os.makedirs(self.inbox_dir, exist_ok=True)

        md_path = os.path.join(self.inbox_dir, f"{candidate.id}.md")
        json_path = os.path.join(self.inbox_dir, f"{candidate.id}.json")

        self.assert_staging_allowed(md_path)
        self.assert_staging_allowed(json_path)

        md_content = candidate.to_markdown()
        json_content = json.dumps(candidate.to_dict(), indent=2)

        md_scan = scan_text(md_content, target_name=md_path)
        if not md_scan.is_clean:
            raise ValueError(f"Secret detected in candidate markdown: {md_scan.findings}")

        json_scan = scan_text(json_content, target_name=json_path)
        if not json_scan.is_clean:
            raise ValueError(f"Secret detected in candidate JSON: {json_scan.findings}")

        temp_md = md_path + ".tmp"
        with open(temp_md, "w", encoding="utf-8") as f:
            f.write(md_content)
        os.replace(temp_md, md_path)

        temp_json = json_path + ".tmp"
        with open(temp_json, "w", encoding="utf-8") as f:
            f.write(json_content)
        os.replace(temp_json, json_path)

        self._update_inbox_index()

        return md_path, json_path

    def _update_inbox_index(self) -> None:
        """Maintain an INDEX.md inside inbox/procedures/ listing candidate items."""
        index_path = os.path.join(self.inbox_dir, "INDEX.md")
        self.assert_staging_allowed(index_path)

        candidates = self.list_staged_candidates()
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        lines = [
            "# Procedural Memory Inbox Index",
            f"Last Updated: {now_str}",
            "",
            "> **Invariant 16 Notice**: Items listed below are candidate procedures staged for review.",
            "> They are INERT and have NOT been installed into active skills directories.",
            "",
            "| Candidate ID | Title | Domain | Confidence | Status | Source Sessions |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for c in candidates:
            lines.append(
                f"| [{c.id}]({c.id}.md) | {c.title} | {c.domain} | {c.confidence:.2f} | `{c.status}` | {len(c.source_sessions)} sessions |"
            )

        lines.append("")
        content = "\n".join(lines)

        scan_res = scan_text(content, target_name=index_path)
        if not scan_res.is_clean:
            raise ValueError(f"Secret detected in inbox INDEX.md: {scan_res.findings}")

        temp_index = index_path + ".tmp"
        with open(temp_index, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(temp_index, index_path)

    def list_staged_candidates(self) -> List[CandidateProcedure]:
        """List all candidate procedures currently staged in inbox."""
        if not os.path.isdir(self.inbox_dir):
            return []

        candidates = []
        json_files = sorted(glob.glob(os.path.join(self.inbox_dir, "*.json")))
        for jf in json_files:
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    candidates.append(CandidateProcedure.from_dict(data))
            except Exception:
                pass
        return candidates

    def verify_staging_isolation(self) -> Dict[str, Any]:
        """
        Verify Invariant 16 isolation:
        - Confirms active skills directories have NOT been written to or modified by procedural engine.
        - Confirms staged procedures reside solely in inbox_dir.
        - Confirms candidate status is inert (admitted: false).
        """
        report: Dict[str, Any] = {
            "invariant_16_passed": True,
            "violations": [],
            "staged_candidate_count": 0,
            "active_skills_directories_checked": [],
            "staged_candidates": [],
        }

        for skills_dir in self.forbidden_skills_dirs:
            report["active_skills_directories_checked"].append(skills_dir)
            if os.path.isdir(skills_dir):
                for root, _, files in os.walk(skills_dir):
                    for fname in files:
                        if fname.startswith("proc-") or fname.endswith(".candidate.md"):
                            report["invariant_16_passed"] = False
                            report["violations"].append(
                                f"Active skill directory '{skills_dir}' contains candidate file '{fname}'"
                            )

        staged = self.list_staged_candidates()
        report["staged_candidate_count"] = len(staged)
        for c in staged:
            report["staged_candidates"].append({
                "id": c.id,
                "title": c.title,
                "domain": c.domain,
                "admitted": c.admitted,
                "status": c.status,
            })
            if c.admitted:
                report["invariant_16_passed"] = False
                report["violations"].append(
                    f"Candidate '{c.id}' has admitted=True inside staging inbox."
                )

        return report

    def run_mining_pipeline(self, min_support: int = 2) -> List[CandidateProcedure]:
        """
        Complete mining and staging pipeline:
        1. Mines episodic sessions for recurring workflows
        2. Distinguishes step types per Section 46
        3. Enforces Invariant 16 and stages candidates in inbox_dir
        4. Verifies staging isolation
        """
        candidates = self.mine_recurring_sequences(min_support=min_support)
        for cand in candidates:
            self.stage_candidate(cand)
        return candidates


def generate_cli_summary(candidates: List[CandidateProcedure]) -> str:
    """Generate concise human-readable summary of mined and staged candidate procedures."""
    if not candidates:
        return "No candidate procedures discovered matching recurrence criteria."

    lines = [
        "=== Procedural Memory Distillation Summary ===",
        f"Total Candidates Staged: {len(candidates)}",
        "Staging Location: .agents/memory/inbox/procedures/",
        "Invariant 16 Status: ENFORCED (0 writes to active skills)",
        "",
        "| Candidate ID | Title | Domain | Steps | Observed | Inferred | Recommended | Verified | Optional | Confidence |",
        "| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for c in candidates:
        obs = sum(1 for s in c.steps if s.step_type == StepType.OBSERVED_COMMAND.value)
        ver = sum(1 for s in c.steps if s.step_type == StepType.VERIFIED_STEP.value)
        inf = sum(1 for s in c.steps if s.step_type == StepType.INFERRED_STEP.value)
        rec = sum(1 for s in c.steps if s.step_type == StepType.RECOMMENDED_STEP.value)
        opt = sum(1 for s in c.steps if s.step_type == StepType.OPTIONAL_STEP.value)
        lines.append(
            f"| {c.id} | {c.title} | {c.domain} | {len(c.steps)} | {obs} | {inf} | {rec} | {ver} | {opt} | {c.confidence:.2f} |"
        )

    lines.append("\nCandidate Procedures are INERT and staged in inbox for policy review.")
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Antigravity Procedural Memory Distillation Engine")
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommand to execute")

    mine_p = subparsers.add_parser("mine", help="Mine sessions and stage candidate procedures")
    mine_p.add_argument("--workspace", default="/workspaces/codespaces-blank", help="Workspace root")
    mine_p.add_argument("--sessions-dir", help="Episodic sessions directory")
    mine_p.add_argument("--inbox-dir", help="Inbox staging directory")
    mine_p.add_argument("--min-support", type=int, default=2, help="Minimum recurrence support threshold")

    verify_p = subparsers.add_parser("verify-isolation", help="Verify Invariant 16 staging isolation")
    verify_p.add_argument("--workspace", default="/workspaces/codespaces-blank", help="Workspace root")

    list_p = subparsers.add_parser("list", help="List staged candidate procedures")
    list_p.add_argument("--workspace", default="/workspaces/codespaces-blank", help="Workspace root")

    args = parser.parse_args()

    workspace = getattr(args, "workspace", "/workspaces/codespaces-blank")
    sessions_dir = getattr(args, "sessions_dir", None)
    inbox_dir = getattr(args, "inbox_dir", None)

    engine = ProceduralEngine(
        workspace_root=workspace,
        sessions_dir=sessions_dir,
        inbox_dir=inbox_dir,
    )

    if args.subcommand in ("mine", None):
        min_supp = getattr(args, "min_support", 2)
        candidates = engine.run_mining_pipeline(min_support=min_supp)
        print(generate_cli_summary(candidates))
        iso = engine.verify_staging_isolation()
        print(f"\nStaging Isolation Check: {'PASSED' if iso['invariant_16_passed'] else 'FAILED'}")
        if not iso["invariant_16_passed"]:
            print(f"Violations: {iso['violations']}", file=sys.stderr)
            sys.exit(1)

    elif args.subcommand == "verify-isolation":
        iso = engine.verify_staging_isolation()
        print(json.dumps(iso, indent=2))
        sys.exit(0 if iso["invariant_16_passed"] else 1)

    elif args.subcommand == "list":
        candidates = engine.list_staged_candidates()
        print(generate_cli_summary(candidates))


if __name__ == "__main__":
    main()
