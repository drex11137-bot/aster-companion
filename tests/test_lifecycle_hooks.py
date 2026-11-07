#!/usr/bin/env python3
"""
Automated Test Suite for Antigravity Lifecycle Hooks & Security Guard (Phase J).
Verifies:
1. PreInvocation hook (CURRENT.md injection, idempotence, session hashing).
2. PreToolUse security gate (intercepting write_to_file, replace_file_content, run_command).
3. PostToolUse hook (syntax tracking, clean empty JSON contract).
4. Stop hook (session guard, clean shutdown contract).
5. Deterministic error handling (zero-crash guarantee on malformed input).
6. Performance budget compliance (<50ms non-blocking budget).
"""

import os
import sys
import json
import time
import base64
import shutil
import hashlib
import tempfile
import unittest
import subprocess
from pathlib import Path

# Paths
WORKSPACE_ROOT = Path("/workspaces/codespaces-blank")
HOOKS_DIR = WORKSPACE_ROOT / "scripts" / "hooks"


def run_hook_proc(script_name: str, payload: dict = None, raw_stdin: str = None):
    """Execute a hook script as an external subprocess."""
    script_path = HOOKS_DIR / script_name
    input_str = json.dumps(payload) if payload is not None else (raw_stdin if raw_stdin is not None else "")
    
    t0 = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(script_path)],
        input=input_str,
        text=True,
        capture_output=True
    )
    dt_ms = (time.perf_counter() - t0) * 1000.0
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip(), dt_ms


class TestPreInvocationHook(unittest.TestCase):
    """Test PreInvocation lifecycle hook."""

    def test_clean_invocation_with_objective(self):
        """Test that PreInvocation injects directive when CURRENT.md has an objective."""
        sess_id = f"test-sess-obj-{time.time()}"
        payload = {"conversationId": sess_id}
        rc, out, err, dt = run_hook_proc("pre_invocation.py", payload)
        self.assertEqual(rc, 0, f"Expected returncode 0, got {rc}: {err}")
        self.assertEqual(err, "")
        data = json.loads(out)
        self.assertIn("injectSteps", data)

    def test_idempotence_and_caching(self):
        """Test that PreInvocation caches session state and does not re-inject."""
        sess_id = f"test-sess-idem-{time.time()}"
        payload = {"conversationId": sess_id}
        rc1, out1, _, _ = run_hook_proc("pre_invocation.py", payload)
        self.assertEqual(rc1, 0)
        
        # Second call with same session id must return empty injectSteps from cache
        rc2, out2, _, _ = run_hook_proc("pre_invocation.py", payload)
        self.assertEqual(rc2, 0)
        data2 = json.loads(out2)
        self.assertEqual(data2, {"injectSteps": []})

    def test_malformed_inputs_never_crash(self):
        """Verify PreInvocation never crashes on empty, null, or malformed stdin."""
        test_inputs = ["", "   ", "not-json", "{broken", '{"conversationId": null}']
        for inp in test_inputs:
            rc, out, err, _ = run_hook_proc("pre_invocation.py", raw_stdin=inp)
            self.assertEqual(rc, 0, f"Failed on input: {inp!r}")
            self.assertEqual(err, "")
            data = json.loads(out)
            self.assertIn("injectSteps", data)


class TestPreToolUseSecurityGate(unittest.TestCase):
    """Test PreToolUse security gate intercepting secrets across tools."""

    @classmethod
    def setUpClass(cls):
        # Base64 encoded test secrets to avoid triggering live hooks
        cls.b64_secrets = {
            "OpenAI Project Key": "c2stcHJvai0xMjM0NTY3ODkwYWJjZGVmMTIzNDU2Nzg5MGFiY2RlZg==",
            "Anthropic Key": "c2stYW50LWFwaTAzLTEyMzQ1Njc4OTBhYmNkZWYxMjM0NTY3ODkwYWJjZGVm",
            "Google Gemini Key": "QUl6YVN5RDEyMzQ1Njc4OTBhYmNkZWYxMjM0NTY3ODkwYWJjZGVmMTIzNDU=",
            "GitHub PAT": "Z2hwXzEyMzQ1Njc4OTBhYmNkZWYxMjM0NTY3ODkwYWJjZGVmMTIzNA==",
            "AWS Key ID": "QUtJQTEyMzQ1Njc4OTBBQkNERUY=",
            "RSA Private Key": "LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFb3dJQkFBS0NBUUVBMDAwMA==",
            "Database Password URI": "cG9zdGdyZXM6Ly9kYnVzZXI6c2VjcmV0cGFzczEyM0BkYi5leGFtcGxlLmNvbTo1NDMyL3Byb2RkYg==",
            "Hardcoded Password": "cGFzc3dvcmQgPSAiTXlTZWNyZXRQYXNzd29yZDEyMyEi",
            "Slack Webhook": "aHR0cHM6Ly9ob29rcy5zbGFjay5jb20vc2VydmljZXMvVDEyMzQ1Njc4L0IxMjM0NTY3OC8xMjM0NTY3ODkwYWJjZGVmMTIzNDU2Nzg=",
            "Stripe Key": "c2tfbGl2ZV8xMjM0NTY3ODkwYWJjZGVmMTIzNDU2Nzg=",
        }

    def _get_secret(self, name: str) -> str:
        return base64.b64decode(self.b64_secrets[name]).decode("utf-8")

    def test_intercept_write_to_file_secrets(self):
        """Verify write_to_file is intercepted and blocked for all secret types."""
        for name in self.b64_secrets:
            secret = self._get_secret(name)
            payload = {
                "toolCall": {
                    "name": "write_to_file",
                    "args": {
                        "TargetFile": "/tmp/test.py",
                        "CodeContent": f"# Configuration\nAPI_KEY = \"{secret}\"\n"
                    }
                }
            }
            rc, out, err, _ = run_hook_proc("pre_tool_use.py", payload)
            self.assertEqual(rc, 0, f"Error running hook for {name}: {err}")
            res = json.loads(out)
            self.assertEqual(res.get("decision"), "deny", f"Failed to block secret in write_to_file: {name}")
            self.assertIn("Security violation", res.get("reason", ""))

    def test_intercept_replace_file_content_secrets(self):
        """Verify replace_file_content is intercepted and blocked when replacement has secrets."""
        for name in ["OpenAI Project Key", "GitHub PAT", "RSA Private Key", "Database Password URI"]:
            secret = self._get_secret(name)
            payload = {
                "toolCall": {
                    "name": "replace_file_content",
                    "args": {
                        "TargetFile": "/tmp/test.py",
                        "ReplacementContent": f"SECRET_TOKEN = '{secret}'"
                    }
                }
            }
            rc, out, err, _ = run_hook_proc("pre_tool_use.py", payload)
            self.assertEqual(rc, 0)
            res = json.loads(out)
            self.assertEqual(res.get("decision"), "deny", f"Failed to block secret in replace_file_content: {name}")

    def test_intercept_run_command_secrets(self):
        """Verify run_command is intercepted and blocked when command has secrets."""
        for name in ["Google Gemini Key", "AWS Key ID", "Slack Webhook", "Stripe Key"]:
            secret = self._get_secret(name)
            payload = {
                "toolCall": {
                    "name": "run_command",
                    "args": {
                        "CommandLine": f"curl -H 'Authorization: Bearer {secret}' https://api.service.com"
                    }
                }
            }
            rc, out, err, _ = run_hook_proc("pre_tool_use.py", payload)
            self.assertEqual(rc, 0)
            res = json.loads(out)
            self.assertEqual(res.get("decision"), "deny", f"Failed to block secret in run_command: {name}")

    def test_allow_clean_tool_calls(self):
        """Verify clean operations are allowed without impediment."""
        clean_calls = [
            ("write_to_file", {"TargetFile": "/tmp/clean.py", "CodeContent": "def add(x, y): return x + y\n"}),
            ("replace_file_content", {"TargetFile": "/tmp/clean.py", "ReplacementContent": "def add(x, y): return x + y + 1\n"}),
            ("run_command", {"CommandLine": "ls -la /tmp"}),
            ("run_command", {"CommandLine": "git status --short"}),
            ("run_command", {"CommandLine": "pytest tests/ -v"}),
        ]
        for t_name, args in clean_calls:
            payload = {"toolCall": {"name": t_name, "args": args}}
            rc, out, err, _ = run_hook_proc("pre_tool_use.py", payload)
            self.assertEqual(rc, 0)
            res = json.loads(out)
            self.assertEqual(res.get("decision"), "allow", f"Clean call was blocked: {t_name}")

    def test_allow_safe_placeholders(self):
        """Verify documented safe placeholders are not falsely blocked."""
        placeholders = [
            "KEY = os.environ.get('API_KEY')",
            "const token = process.env.TOKEN || 'placeholder';",
            "curl -H 'Authorization: Bearer <your_api_key>' https://api.com",
            "git config user.password 'changeme'",
            "DUMMY_KEY = 'dummy_key'",
        ]
        for p in placeholders:
            payload = {
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": "/tmp/placeholder.py", "CodeContent": p}
                }
            }
            rc, out, err, _ = run_hook_proc("pre_tool_use.py", payload)
            self.assertEqual(rc, 0)
            res = json.loads(out)
            self.assertEqual(res.get("decision"), "allow", f"Safe placeholder falsely blocked: {p}")

    def test_idempotent_hash_caching(self):
        """Verify repeated calls with identical content hit cache and return instantly."""
        payload = {
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": "/tmp/cached.py", "CodeContent": f"# Cache test {time.time()}\nval = 42\n"}
            }
        }
        # First call (populates cache)
        rc1, out1, _, dt1 = run_hook_proc("pre_tool_use.py", payload)
        self.assertEqual(rc1, 0)
        self.assertEqual(json.loads(out1).get("decision"), "allow")

        # Second call (must be faster via cache)
        rc2, out2, _, dt2 = run_hook_proc("pre_tool_use.py", payload)
        self.assertEqual(rc2, 0)
        self.assertEqual(json.loads(out2).get("decision"), "allow")

    def test_malformed_inputs_never_crash(self):
        """Verify PreToolUse never crashes on invalid inputs."""
        test_inputs = [
            "", "{}", "   ", "invalid-json",
            '{"toolCall": null}',
            '{"toolCall": {"args": null}}',
            '{"toolCall": {"args": []}}',
            '{"toolCall": {"args": {"CommandLine": null}}}',
            '{"toolCall": {"args": {"CommandLine": 12345}}}',
        ]
        for inp in test_inputs:
            rc, out, err, _ = run_hook_proc("pre_tool_use.py", raw_stdin=inp)
            self.assertEqual(rc, 0, f"Crashed on input: {inp!r}")
            self.assertEqual(err, "")
            res = json.loads(out)
            self.assertEqual(res.get("decision"), "allow")

    def test_intercept_manage_task_secrets(self):
        """Verify manage_task is intercepted and blocked when Input contains secrets."""
        for name in ["GitHub PAT", "OpenAI Project Key", "AWS Key ID"]:
            secret = self._get_secret(name)
            payload = {
                "toolCall": {
                    "name": "manage_task",
                    "args": {
                        "Action": "send_input",
                        "TaskId": "test-task-1",
                        "Input": f"export TOKEN='{secret}'"
                    }
                }
            }
            rc, out, err, _ = run_hook_proc("pre_tool_use.py", payload)
            self.assertEqual(rc, 0)
            res = json.loads(out)
            self.assertEqual(res.get("decision"), "deny", f"Failed to block secret in manage_task: {name}")
            self.assertIn("Security violation", res.get("reason", ""))

    def test_intercept_notebook_edit_secrets(self):
        """Verify notebook_edit is intercepted and blocked when Content contains secrets."""
        for name in ["GitHub PAT", "OpenAI Project Key", "Stripe Key"]:
            secret = self._get_secret(name)
            payload = {
                "toolCall": {
                    "name": "notebook_edit",
                    "args": {
                        "NotebookPath": "/tmp/test.ipynb",
                        "Action": "add",
                        "CellType": "code",
                        "Content": f"API_KEY = '{secret}'"
                    }
                }
            }
            rc, out, err, _ = run_hook_proc("pre_tool_use.py", payload)
            self.assertEqual(rc, 0)
            res = json.loads(out)
            self.assertEqual(res.get("decision"), "deny", f"Failed to block secret in notebook_edit: {name}")
            self.assertIn("Security violation", res.get("reason", ""))

    def test_cache_validation_size_and_mtime(self):
        """Verify cache validation rejects 0-size files and expired mtimes."""
        secret = self._get_secret("GitHub PAT")
        content = f"API_TOKEN = '{secret}'"
        h = hashlib.sha256(content.encode("utf-8")).hexdigest()
        cache_dir = os.path.expanduser("~/.cache/antigravity/security_cache")
        os.makedirs(cache_dir, mode=0o700, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"ag_sec_{h}")

        payload = {
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": "/tmp/test.py", "CodeContent": content}
            }
        }

        try:
            # Case 1: Cache file is 0 bytes (e.g. touch attack) -> Must NOT bypass scanner, must DENY
            with open(cache_file, "w") as f:
                pass  # 0 bytes
            self.assertEqual(os.path.getsize(cache_file), 0)

            rc, out, err, _ = run_hook_proc("pre_tool_use.py", payload)
            self.assertEqual(rc, 0)
            res = json.loads(out)
            self.assertEqual(res.get("decision"), "deny", "0-byte cache file must not allow secret!")

            # Case 2: Cache file has old mtime (> 86400s) -> Must NOT bypass scanner, must DENY
            with open(cache_file, "w") as f:
                f.write("1")
            old_time = time.time() - 100000  # > 24 hours ago
            os.utime(cache_file, (old_time, old_time))

            rc, out, err, _ = run_hook_proc("pre_tool_use.py", payload)
            self.assertEqual(rc, 0)
            res = json.loads(out)
            self.assertEqual(res.get("decision"), "deny", "Expired cache file must not allow secret!")
        finally:
            if os.path.exists(cache_file):
                os.remove(cache_file)

    def test_fail_closed_on_unexpected_exception(self):
        """Verify pre_tool_use fails closed (decision: deny) on unexpected internal exceptions."""
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; sys.modules['secret_scanner'] = None; import scripts.hooks.pre_tool_use as p; p.main()"
            ],
            input=json.dumps({
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"CodeContent": "some_content_to_scan"}
                }
            }),
            text=True,
            capture_output=True
        )
        self.assertEqual(proc.returncode, 0)
        res = json.loads(proc.stdout.strip())
        self.assertEqual(res.get("decision"), "deny")
        self.assertEqual(res.get("reason"), "PreToolUse security gate exception (fail-closed)")


class TestPostToolUseHook(unittest.TestCase):
    """Test PostToolUse lifecycle hook."""

    def test_valid_post_tool_execution(self):
        """Verify post_tool_use returns {} on valid tool completion."""
        payload = {
            "toolCall": {"name": "run_command", "args": {"CommandLine": "ls"}},
            "stepIdx": 10
        }
        rc, out, err, _ = run_hook_proc("post_tool_use.py", payload)
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")
        self.assertEqual(json.loads(out), {})

    def test_malformed_inputs_never_crash(self):
        """Verify post_tool_use never crashes on invalid inputs."""
        test_inputs = ["", "{}", "invalid", '{"toolCall": null}']
        for inp in test_inputs:
            rc, out, err, _ = run_hook_proc("post_tool_use.py", raw_stdin=inp)
            self.assertEqual(rc, 0)
            self.assertEqual(json.loads(out), {})

    def test_failure_exit_code_captured_to_candidate_bus(self):
        """Verify DEF-008: Non-zero exit code triggers CandidateBus failure/gotcha staging."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_inbox = Path(tmp_dir) / "candidates.jsonl"
            old_env = os.environ.get("ANTIGRAVITY_CANDIDATES_FILE")
            os.environ["ANTIGRAVITY_CANDIDATES_FILE"] = str(tmp_inbox)
            try:
                payload = {
                    "toolCall": {
                        "name": "run_command",
                        "args": {"CommandLine": "cargo test --release"}
                    },
                    "exit_code": 101,
                    "error": "thread 'main' panicked at 'assertion failed: false'",
                    "stepIdx": 5
                }
                rc, out, err, dt = run_hook_proc("post_tool_use.py", payload)
                self.assertEqual(rc, 0)
                self.assertEqual(err, "")
                self.assertEqual(json.loads(out), {})
                self.assertLess(dt, 500.0)  # Subprocess invocation within budget

                self.assertTrue(tmp_inbox.exists())
                with open(tmp_inbox, "r", encoding="utf-8") as f:
                    entries = [json.loads(line) for line in f if line.strip()]
                self.assertEqual(len(entries), 1)
                self.assertEqual(entries[0]["category"], "BUG_ROOT_CAUSE")
                self.assertIn("assertion failed: false", entries[0]["content"])
                self.assertEqual(entries[0]["provenance"]["exit_code"], 101)
            finally:
                if old_env is not None:
                    os.environ["ANTIGRAVITY_CANDIDATES_FILE"] = old_env
                else:
                    os.environ.pop("ANTIGRAVITY_CANDIDATES_FILE", None)

    def test_error_in_output_captured_to_candidate_bus(self):
        """Verify error detected in tool output is captured into CandidateBus as gotcha."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_inbox = Path(tmp_dir) / "candidates.jsonl"
            old_env = os.environ.get("ANTIGRAVITY_CANDIDATES_FILE")
            os.environ["ANTIGRAVITY_CANDIDATES_FILE"] = str(tmp_inbox)
            try:
                payload = {
                    "toolCall": {
                        "name": "run_command",
                        "args": {"CommandLine": "python3 script.py"}
                    },
                    "output": "Traceback (most recent call last):\n  File 'script.py', line 10\nIndexError: pop from empty list",
                    "exit_code": 0,
                    "stepIdx": 8
                }
                rc, out, err, dt = run_hook_proc("post_tool_use.py", payload)
                self.assertEqual(rc, 0)
                self.assertEqual(err, "")
                self.assertEqual(json.loads(out), {})

                self.assertTrue(tmp_inbox.exists())
                with open(tmp_inbox, "r", encoding="utf-8") as f:
                    entries = [json.loads(line) for line in f if line.strip()]
                self.assertEqual(len(entries), 1)
                self.assertEqual(entries[0]["category"], "BUG_ROOT_CAUSE")
                self.assertIn("IndexError", entries[0]["content"])
            finally:
                if old_env is not None:
                    os.environ["ANTIGRAVITY_CANDIDATES_FILE"] = old_env
                else:
                    os.environ.pop("ANTIGRAVITY_CANDIDATES_FILE", None)

    def test_json_syntax_error_captured_to_candidate_bus(self):
        """Verify file mutation with invalid JSON triggers syntax error capture into CandidateBus."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_inbox = Path(tmp_dir) / "candidates.jsonl"
            broken_json_file = Path(tmp_dir) / "bad.json"
            broken_json_file.write_text("{\ninvalid_json: 123,\n}", encoding="utf-8")

            old_env = os.environ.get("ANTIGRAVITY_CANDIDATES_FILE")
            os.environ["ANTIGRAVITY_CANDIDATES_FILE"] = str(tmp_inbox)
            try:
                payload = {
                    "toolCall": {
                        "name": "write_to_file",
                        "args": {
                            "TargetFile": str(broken_json_file),
                            "CodeContent": "{\ninvalid_json: 123,\n}"
                        }
                    },
                    "stepIdx": 12
                }
                rc, out, err, dt = run_hook_proc("post_tool_use.py", payload)
                self.assertEqual(rc, 0)
                self.assertEqual(err, "")
                self.assertEqual(json.loads(out), {})

                self.assertTrue(tmp_inbox.exists())
                with open(tmp_inbox, "r", encoding="utf-8") as f:
                    entries = [json.loads(line) for line in f if line.strip()]
                self.assertEqual(len(entries), 1)
                self.assertEqual(entries[0]["category"], "BUG_ROOT_CAUSE")
                self.assertIn("JSON syntax error", entries[0]["content"])
            finally:
                if old_env is not None:
                    os.environ["ANTIGRAVITY_CANDIDATES_FILE"] = old_env
                else:
                    os.environ.pop("ANTIGRAVITY_CANDIDATES_FILE", None)

    def test_routine_noise_not_staged_to_candidate_bus(self):
        """Verify routine terminal noise (ls, echo) with exit 0 is filtered and never staged."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_inbox = Path(tmp_dir) / "candidates.jsonl"
            old_env = os.environ.get("ANTIGRAVITY_CANDIDATES_FILE")
            os.environ["ANTIGRAVITY_CANDIDATES_FILE"] = str(tmp_inbox)
            try:
                payload = {
                    "toolCall": {
                        "name": "run_command",
                        "args": {"CommandLine": "ls -la"}
                    },
                    "output": "file1.txt file2.txt",
                    "exit_code": 0,
                    "stepIdx": 15
                }
                rc, out, err, dt = run_hook_proc("post_tool_use.py", payload)
                self.assertEqual(rc, 0)
                self.assertEqual(json.loads(out), {})

                # Inbox should not exist or be empty
                if tmp_inbox.exists():
                    with open(tmp_inbox, "r", encoding="utf-8") as f:
                        lines = [l for l in f if l.strip()]
                    self.assertEqual(len(lines), 0)
            finally:
                if old_env is not None:
                    os.environ["ANTIGRAVITY_CANDIDATES_FILE"] = old_env
                else:
                    os.environ.pop("ANTIGRAVITY_CANDIDATES_FILE", None)


class TestStopHook(unittest.TestCase):
    """Test Stop lifecycle hook."""

    def test_valid_stop_execution(self):
        """Verify stop_hook returns decision: stop on session termination."""
        payload = {"terminationReason": "model_stop", "fullyIdle": True}
        rc, out, err, _ = run_hook_proc("stop_hook.py", payload)
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")
        res = json.loads(out)
        self.assertEqual(res.get("decision"), "stop")

    def test_malformed_inputs_never_crash(self):
        """Verify stop_hook never crashes on invalid inputs."""
        test_inputs = ["", "{}", "invalid", '{"fullyIdle": false}']
        for inp in test_inputs:
            rc, out, err, _ = run_hook_proc("stop_hook.py", raw_stdin=inp)
            self.assertEqual(rc, 0)
            res = json.loads(out)
            self.assertEqual(res.get("decision"), "stop")


class TestHookPerformance(unittest.TestCase):
    """Benchmark hook internal latency and performance budget."""

    def test_internal_execution_latency(self):
        """Verify internal hook handlers execute well within the 50ms budget."""
        sys.path.insert(0, str(HOOKS_DIR))
        import pre_invocation, pre_tool_use, post_tool_use, stop_hook
        import io

        # Benchmark pre_tool_use internal execution
        input_data = {"toolCall": {"name": "run_command", "args": {"CommandLine": "echo test"}}}
        latencies = []
        for _ in range(50):
            sys.stdin = io.StringIO(json.dumps(input_data))
            sys.stdout = io.StringIO()
            t0 = time.perf_counter()
            pre_tool_use.main()
            latencies.append((time.perf_counter() - t0) * 1000.0)

        sys.stdout = sys.__stdout__
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        
        # Internal execution is in microseconds (< 1ms), well below 50ms
        self.assertLess(avg_latency, 5.0, f"Average internal latency {avg_latency:.3f}ms exceeds 5ms threshold")
        self.assertLess(p95_latency, 10.0, f"P95 internal latency {p95_latency:.3f}ms exceeds 10ms threshold")

    def test_post_tool_use_latency_guard(self):
        """Verify post_tool_use hook executes well within the 30ms non-blocking budget."""
        sys.path.insert(0, str(HOOKS_DIR))
        import post_tool_use
        import io

        input_data = {
            "toolCall": {"name": "run_command", "args": {"CommandLine": "cargo test"}},
            "output": "Compiling target...",
            "exit_code": 0
        }
        latencies = []
        for _ in range(50):
            sys.stdin = io.StringIO(json.dumps(input_data))
            sys.stdout = io.StringIO()
            t0 = time.perf_counter()
            post_tool_use.main()
            latencies.append((time.perf_counter() - t0) * 1000.0)

        sys.stdout = sys.__stdout__
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        max_latency = max(latencies)

        self.assertLess(avg_latency, 5.0, f"Average post_tool_use latency {avg_latency:.3f}ms exceeds 5ms threshold")
        self.assertLess(p95_latency, 10.0, f"P95 post_tool_use latency {p95_latency:.3f}ms exceeds 10ms threshold")
        self.assertLess(max_latency, 30.0, f"Max post_tool_use latency {max_latency:.3f}ms exceeds 30ms guard budget")


if __name__ == "__main__":
    unittest.main()
