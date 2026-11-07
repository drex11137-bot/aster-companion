#!/usr/bin/env python3
"""
Unit and Integration Tests for Procedural Memory Distillation Engine.
Verifies Instruction.md Sections 45-47 and Invariant 16:
- Mining episodic session logs for recurring sequences
- Distinguishing observed commands from inferred, recommended, verified, optional steps
- Tool provenance preservation (exact commands, args, cwd, output, error, corrections)
- Invariant 16: NEVER writes to active skills; strictly stages in inbox/procedures/
- Zero-secret security gatekeeper enforcement
- Staging isolation verification
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone

# Add scripts directory to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from procedural_engine import (
    ProceduralEngine,
    CandidateProcedure,
    ProcedureStep,
    StepType,
    InvariantViolationError,
    generate_cli_summary,
)


class TestProceduralEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_proc_")
        self.workspace_root = os.path.join(self.temp_dir, "workspace")
        self.sessions_dir = os.path.join(self.workspace_root, ".agents", "memory", "sessions")
        self.inbox_dir = os.path.join(self.workspace_root, ".agents", "memory", "inbox", "procedures")
        self.active_skills_dir = os.path.join(self.workspace_root, ".agents", "skills")
        self.global_skills_dir = os.path.join(self.temp_dir, "global_skills")

        os.makedirs(self.sessions_dir, exist_ok=True)
        os.makedirs(self.inbox_dir, exist_ok=True)
        os.makedirs(self.active_skills_dir, exist_ok=True)
        os.makedirs(self.global_skills_dir, exist_ok=True)

        self.engine = ProceduralEngine(
            workspace_root=self.workspace_root,
            sessions_dir=self.sessions_dir,
            inbox_dir=self.inbox_dir,
            forbidden_skills_dirs=[self.active_skills_dir, self.global_skills_dir],
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_invariant_16_enforcement(self):
        """Invariant 16: NEVER writes directly to active skills directories."""
        forbidden_target = os.path.join(self.active_skills_dir, "malicious_proc.md")
        with self.assertRaises(InvariantViolationError) as ctx:
            self.engine.assert_staging_allowed(forbidden_target)
        self.assertIn("INVARIANT 16 VIOLATION", str(ctx.exception))

        forbidden_global = os.path.join(self.global_skills_dir, "global_proc.md")
        with self.assertRaises(InvariantViolationError) as ctx:
            self.engine.assert_staging_allowed(forbidden_global)
        self.assertIn("INVARIANT 16 VIOLATION", str(ctx.exception))

        valid_inbox_target = os.path.join(self.inbox_dir, "candidate.md")
        try:
            self.engine.assert_staging_allowed(valid_inbox_target)
        except InvariantViolationError:
            self.fail("assert_staging_allowed unexpectedly raised on valid inbox path")

    def test_session_log_parsing_and_distinctions(self):
        """Verify parsing of code blocks, provenance, and step distinctions per Section 46 & 47."""
        log_content = """# Session Log: 2026-09-02-1000

- **Date**: 2026-09-02T10:00:00Z
- **Workspace**: /workspaces/codespaces-blank

## 1. Completed Work
- Verified native compilation:
  ```bash
  cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
  ninja -C build
  ctest --test-dir build --output-on-failure
  ```
- Command: `gcc --version`
  Cwd: `/workspaces/codespaces-blank`
  Output: `gcc 13.2.0`
- Tests passed completely.

## 2. Unresolved Issues & Blockers
- None

## 4. Discoveries & Gotchas
- Inferred prerequisite: C compiler must support C11 standard.

## 5. Next Steps
1. Recommend periodic sanitization test runs with AddressSanitizer.
2. Optional: enable gcov coverage analysis if code changes exceed 500 lines.

## 6. Candidate Durable Memories
| Type | Durability (0-5) | Target Tier | Description & Rationale |
| :--- | :--- | :--- | :--- |
| PROJECT | 3 | PROJECT_MEMORY | Native build and test procedure validated |
"""
        log_path = os.path.join(self.sessions_dir, "2026-09-02-1000.md")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(log_content)

        parsed = self.engine.parse_session_log(log_path)
        self.assertEqual(parsed["session_id"], "2026-09-02-1000")

        step_types = [a["step_type"] for a in parsed["actions"]]
        self.assertIn(StepType.VERIFIED_STEP.value, step_types)
        self.assertIn(StepType.INFERRED_STEP.value, step_types)
        self.assertIn(StepType.RECOMMENDED_STEP.value, step_types)
        self.assertIn(StepType.OPTIONAL_STEP.value, step_types)

        gcc_action = next(a for a in parsed["actions"] if a.get("command") == "gcc --version")
        self.assertEqual(gcc_action["cwd"], "/workspaces/codespaces-blank")
        self.assertEqual(gcc_action["expected_output"], "gcc 13.2.0")

    def test_mining_recurring_sequences(self):
        """Verify mining identifies recurring command sequences across multiple sessions."""
        log1 = """# Session Log: 2026-09-02-1100
## 1. Completed Work
- Run test pipeline:
  ```bash
  pytest tests/unit/
  semgrep scan --config=auto
  ```
- Tests pass.
## 6. Candidate Durable Memories
| Type | Durability (0-5) | Target Tier | Description & Rationale |
| :--- | :--- | :--- | :--- |
| PROJECT | 3 | PROJECT_MEMORY | Unit test and security scan |
"""
        log2 = """# Session Log: 2026-09-02-1200
## 1. Completed Work
- Re-run test pipeline after refactor:
  ```bash
  pytest tests/unit/
  semgrep scan --config=auto
  ```
- Tests pass.
## 6. Candidate Durable Memories
| Type | Durability (0-5) | Target Tier | Description & Rationale |
| :--- | :--- | :--- | :--- |
| PROJECT | 3 | PROJECT_MEMORY | Unit test and security scan |
"""
        with open(os.path.join(self.sessions_dir, "2026-09-02-1100.md"), "w") as f:
            f.write(log1)
        with open(os.path.join(self.sessions_dir, "2026-09-02-1200.md"), "w") as f:
            f.write(log2)

        candidates = self.engine.mine_recurring_sequences(min_support=2)
        self.assertTrue(len(candidates) >= 1)

        test_cand = next((c for c in candidates if "pytest" in " ".join([s.command or "" for s in c.steps])), None)
        self.assertIsNotNone(test_cand)
        self.assertEqual(test_cand.recurrence_count, 2)
        self.assertEqual(test_cand.status, "CANDIDATE_STAGED")
        self.assertFalse(test_cand.admitted)

        commands = [s.command for s in test_cand.steps if s.command]
        self.assertIn("pytest tests/unit/", commands)
        self.assertIn("semgrep scan --config=auto", commands)

    def test_staging_and_isolation(self):
        """Verify candidates are staged in inbox/procedures/ with INDEX.md and active skills untouched."""
        step1 = ProcedureStep(
            step_number=1,
            step_type=StepType.OBSERVED_COMMAND.value,
            name="Run Doctor",
            description="Run diagnostics",
            command="python3 tools/bin/agy-env-doctor",
            cwd=self.workspace_root,
        )
        step2 = ProcedureStep(
            step_number=2,
            step_type=StepType.RECOMMENDED_STEP.value,
            name="Audit Secrets",
            description="Advisory: scan secrets",
            command=None,
            cwd=self.workspace_root,
        )
        cand = CandidateProcedure(
            id="proc-test-doctor",
            title="Doctor Diagnostic Workflow",
            domain="environment",
            description="Test candidate procedure",
            source_sessions=["2026-09-02-1100"],
            recurrence_count=2,
            confidence=0.9,
            steps=[step1, step2],
        )

        md_path, json_path = self.engine.stage_candidate(cand)
        self.assertTrue(os.path.isfile(md_path))
        self.assertTrue(os.path.isfile(json_path))
        self.assertTrue(md_path.startswith(self.inbox_dir))

        inbox_index = os.path.join(self.inbox_dir, "INDEX.md")
        self.assertTrue(os.path.isfile(inbox_index))
        with open(inbox_index, "r", encoding="utf-8") as f:
            index_content = f.read()
        self.assertIn("proc-test-doctor", index_content)

        active_files = os.listdir(self.active_skills_dir)
        self.assertEqual(len(active_files), 0)

        report = self.engine.verify_staging_isolation()
        self.assertTrue(report["invariant_16_passed"])
        self.assertEqual(report["staged_candidate_count"], 1)
        self.assertEqual(len(report["violations"]), 0)

    def test_secret_scanner_rejection(self):
        """Verify candidates containing secrets are blocked from staging."""
        fake_token = "".join(["sk-", "proj-", "1234567890abcdef1234567890abcdef1234567890"])
        secret_step = ProcedureStep(
            step_number=1,
            step_type=StepType.OBSERVED_COMMAND.value,
            name="Leak Secret",
            description="Bad step",
            command=f"export API_KEY={fake_token}",
            cwd=self.workspace_root,
        )
        bad_cand = CandidateProcedure(
            id="proc-bad-secret",
            title="Bad Secret Workflow",
            domain="security",
            description="Leaky candidate",
            source_sessions=["bad-session"],
            recurrence_count=2,
            confidence=0.8,
            steps=[secret_step],
        )

        with self.assertRaises(ValueError) as ctx:
            self.engine.stage_candidate(bad_cand)
        self.assertIn("Secret detected", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
