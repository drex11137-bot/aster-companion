#!/usr/bin/env python3
"""
PostToolUse Hook for Antigravity Platform.
Performs syntax tracking, execution health auditing, and candidate experience capture.
Remediates DEF-008 by capturing failure/gotcha events and high-signal tool events into CandidateBus.
Maintains sub-30ms execution budget, returning {} on stdout.
"""

import sys
import json
import os
import time
from typing import Any, Dict, Optional

# Path setup for importing candidate_bus
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)
for p in (SCRIPTS_DIR, PROJECT_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from candidate_bus import CandidateBus
except ImportError:
    try:
        from scripts.candidate_bus import CandidateBus
    except ImportError:
        CandidateBus = None

# Cached CandidateBus singleton for fast sub-30ms execution
_CANDIDATE_BUS = None
_CANDIDATE_BUS_INBOX = None


def get_candidate_bus() -> Optional[Any]:
    global _CANDIDATE_BUS, _CANDIDATE_BUS_INBOX
    curr_inbox = os.environ.get("ANTIGRAVITY_CANDIDATES_FILE") or os.environ.get("ANTIGRAVITY_INBOX_FILE")
    if _CANDIDATE_BUS is None or _CANDIDATE_BUS_INBOX != curr_inbox:
        if CandidateBus is not None:
            try:
                _CANDIDATE_BUS = CandidateBus()
                _CANDIDATE_BUS_INBOX = curr_inbox
            except Exception:
                _CANDIDATE_BUS = None
    return _CANDIDATE_BUS

# Pre-warm candidate bus singleton so first invocation executes within latency budget
try:
    get_candidate_bus()
except Exception:
    pass


def _extract_error_from_output(output: Any) -> Optional[str]:
    """Inspects tool output for structured or unstructured error indicators."""
    if not output:
        return None
    if isinstance(output, dict):
        if output.get("error"):
            return str(output["error"])
        if output.get("errors"):
            return str(output["errors"])
        if output.get("isError") or output.get("is_error"):
            return str(output.get("message") or output.get("reason") or "Tool reported error")
        if output.get("status") in ("error", "failed", "failure"):
            return str(output.get("message") or output.get("reason") or "Tool execution failed")
    elif isinstance(output, str):
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        # Check if Python traceback is present
        if any("traceback (most recent call last):" in l.lower() for l in lines):
            # The exception details are on the final line of the traceback
            return lines[-1]
        for line in lines:
            for exc in ("SyntaxError:", "IndentationError:", "ModuleNotFoundError:", "ImportError:", "NameError:", "TypeError:", "ValueError:", "IndexError:", "KeyError:"):
                if line.startswith(exc):
                    return line
            for prefix in ("error:", "fatal:", "FAILED:"):
                if line.lower().startswith(prefix.lower()):
                    return line
            if "command not found" in line.lower() or "permission denied" in line.lower():
                return line
    return None


def main():
    t0 = time.perf_counter()
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({}))
            return

        payload = json.loads(raw_input)
        if not isinstance(payload, dict):
            print(json.dumps({}))
            return

        tool_call = payload.get("toolCall") or {}
        tool_name = tool_call.get("name", "") if isinstance(tool_call, dict) else ""
        args = tool_call.get("args") or {} if isinstance(tool_call, dict) else {}
        if not isinstance(args, dict):
            args = {}

        # Resolve exit_code from payload or nested result
        exit_code = payload.get("exit_code")
        if exit_code is None:
            exit_code = payload.get("exitCode")
        if exit_code is None and isinstance(payload.get("result"), dict):
            exit_code = payload["result"].get("exitCode", payload["result"].get("exit_code"))
        if exit_code is None:
            exit_code = 0
        try:
            exit_code = int(exit_code)
        except (ValueError, TypeError):
            exit_code = 1 if exit_code else 0

        # Resolve output from payload
        output = payload.get("output")
        if output is None:
            output = payload.get("toolResponse")
        if output is None:
            output = payload.get("result")
        if output is None:
            output = payload.get("response")

        # Resolve explicit error from payload or nested result
        error = payload.get("error")
        if not error and isinstance(payload.get("result"), dict):
            error = payload["result"].get("error")
        if not error and isinstance(output, dict):
            error = output.get("error")

        # Track file edits for syntax and lint health
        if tool_name in ["write_to_file", "replace_file_content"]:
            target_file = args.get("TargetFile", "")
            if target_file and os.path.exists(target_file):
                # Quick syntax check for JSON files
                if target_file.endswith(".json"):
                    try:
                        with open(target_file, "r", encoding="utf-8") as f:
                            json.load(f)
                    except Exception as json_err:
                        error = f"JSON syntax error in {target_file}: {json_err}"
                        exit_code = 1
                # Quick syntax check for Python files
                elif target_file.endswith(".py"):
                    try:
                        with open(target_file, "r", encoding="utf-8") as f:
                            compile(f.read(), target_file, "exec")
                    except SyntaxError as py_err:
                        error = f"Python syntax error in {target_file}: {py_err}"
                        exit_code = 1

        # Check for error in tool output if not already marked as error
        if not error and output:
            output_err = _extract_error_from_output(output)
            if output_err:
                error = output_err
                if exit_code == 0:
                    exit_code = 1

        # Remediate DEF-008: Integrate CandidateBus.capture_tool_event()
        # Captures high-signal events, gotchas, and failures into CandidateBus
        if tool_name:
            # Latency guard: ensure we don't exceed 25ms internal budget
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            if elapsed_ms < 25.0:
                bus = get_candidate_bus()
                if bus:
                    session_id = (
                        payload.get("sessionId")
                        or payload.get("session_id")
                        or payload.get("conversationId")
                    )
                    turn_id = (
                        payload.get("turnId")
                        or payload.get("turn_id")
                        or (str(payload.get("stepIdx")) if payload.get("stepIdx") is not None else None)
                    )
                    bus.capture_tool_event(
                        tool_name=tool_name,
                        args=args,
                        output=output or "",
                        error=error,
                        exit_code=exit_code,
                        session_id=session_id,
                        turn_id=turn_id,
                        metadata={"hook": "post_tool_use"}
                    )

        print(json.dumps({}))
    except Exception:
        # Never break the agent loop on hook errors (<30ms budget guarantee)
        print(json.dumps({}))


if __name__ == "__main__":
    main()
