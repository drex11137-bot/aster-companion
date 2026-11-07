#!/usr/bin/env python3
"""
==============================================================================
ANTIGRAVITY FAILURE INJECTION & NEGATIVE TEST SUITE
Conforms to instruction.md Section 45 & Section 76 (Red-Team Falsification)
Tests that doctors, scanners, parsers, compilers, and security hooks detect
failures with non-zero exit codes, error diagnostics, and remediation messages.
==============================================================================
"""

import unittest
import os
import sys
import subprocess
import json
import tempfile
import shutil

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(WORKSPACE_ROOT, "scripts")
TOOLS_BIN = os.path.join(WORKSPACE_ROOT, "tools/bin")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


class TestFailureInjectionMCP(unittest.TestCase):
    """Failure injection tests for Model Context Protocol (MCP) configuration."""

    def test_01_invalid_mcp_json_syntax_rejected(self):
        """Verify that malformed JSON in MCP configuration is rejected."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tf:
            tf.write("{\n  \"mcpServers\": {\n    \"broken\": {\n      \"command\": \"npx\"\n    invalid_syntax\n  }\n}")
            bad_json_path = tf.name

        try:
            res = subprocess.run([sys.executable, "-c", f"""
import json, sys
try:
    with open("{bad_json_path}") as f:
        json.load(f)
    sys.exit(0)
except Exception:
    sys.exit(1)
"""], capture_output=True)
            self.assertEqual(res.returncode, 1, "Malformed MCP JSON must fail with exit code 1")
        finally:
            if os.path.exists(bad_json_path):
                os.remove(bad_json_path)

    def test_02_mcp_doctor_detects_malformed_config(self):
        """Verify that agy-mcp-doctor rejects malformed JSON config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = os.path.join(tmpdir, ".agents")
            os.makedirs(agents_dir, exist_ok=True)
            bad_mcp = os.path.join(agents_dir, "mcp_config.json")
            with open(bad_mcp, "w") as f:
                f.write("{ invalid json structure [[[")

            res = subprocess.run(["bash", os.path.join(TOOLS_BIN, "agy-mcp-doctor")], cwd=tmpdir, capture_output=True, text=True)
            self.assertIn("FAIL", res.stdout, "agy-mcp-doctor must report FAIL for malformed JSON")


class TestFailureInjectionPathAndBinaries(unittest.TestCase):
    """Failure injection tests for missing binaries and invalid PATH."""

    def test_03_env_doctor_detects_missing_required_binaries(self):
        """Verify that agy-env-doctor fails and outputs remediation when PATH is sanitized."""
        env = os.environ.copy()
        env["PATH"] = "/nonexistent/isolated/path"
        
        doctor_bin = os.path.join(TOOLS_BIN, "agy-env-doctor")
        res = subprocess.run([sys.executable, doctor_bin], env=env, capture_output=True, text=True)
        
        self.assertEqual(res.returncode, 1, "agy-env-doctor must exit with code 1 when required binaries are missing")
        self.assertIn("FAIL", res.stdout, "Output must contain FAIL status indicators")
        self.assertIn("Remediation Suggestions:", res.stdout, "Output must provide actionable remediation suggestions")

    def test_04_network_doctor_detects_missing_binaries(self):
        """Verify that agy-network-doctor fails when required network tools are missing."""
        env = os.environ.copy()
        env["PATH"] = "/nonexistent/isolated/path"
        
        doctor_bin = os.path.join(TOOLS_BIN, "agy-network-doctor")
        res = subprocess.run([sys.executable, doctor_bin, "--quick"], env=env, capture_output=True, text=True)
        
        self.assertEqual(res.returncode, 1, "agy-network-doctor must exit with code 1 when binaries are missing")
        self.assertIn("FAIL", res.stdout, "agy-network-doctor must flag missing tools as FAIL")

    def test_05_wasm_doctor_detects_missing_binaries(self):
        """Verify that agy-wasm-doctor fails when WebAssembly tools are missing."""
        env = os.environ.copy()
        env["PATH"] = "/nonexistent/isolated/path"
        
        doctor_bin = os.path.join(TOOLS_BIN, "agy-wasm-doctor")
        res = subprocess.run([sys.executable, doctor_bin], env=env, capture_output=True, text=True)
        
        self.assertEqual(res.returncode, 1, "agy-wasm-doctor must exit with code 1 on missing tools")
        self.assertIn("FAIL", res.stdout, "agy-wasm-doctor must flag missing tools as FAIL")


class TestFailureInjectionPCAP(unittest.TestCase):
    """Failure injection tests for corrupted and truncated PCAP fixtures."""

    def test_06_corrupted_pcap_capinfos_rejection(self):
        """Verify that capinfos rejects a corrupted PCAP file with non-zero exit code."""
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pcap") as tf:
            tf.write(b"CORRUPTED_PCAP_GARBAGE_HEADER_DATA_123456789\x00\xff\xfe\xfd")
            bad_pcap = tf.name

        try:
            res = subprocess.run(["capinfos", bad_pcap], capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0, "capinfos must reject corrupted PCAP header with non-zero return code")
        finally:
            if os.path.exists(bad_pcap):
                os.remove(bad_pcap)

    def test_07_corrupted_pcap_tshark_rejection(self):
        """Verify that tshark rejects a corrupted PCAP file with non-zero exit code."""
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pcap") as tf:
            tf.write(b"CORRUPTED_PCAP_GARBAGE_HEADER_DATA_123456789\x00\xff\xfe\xfd")
            bad_pcap = tf.name

        try:
            res = subprocess.run(["tshark", "-r", bad_pcap, "-q"], capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0, "tshark must reject corrupted PCAP with non-zero return code")
        finally:
            if os.path.exists(bad_pcap):
                os.remove(bad_pcap)

    def test_08_truncated_pcap_detection(self):
        """Verify that a truncated PCAP file causes parse errors in forensic tools."""
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pcap") as tf:
            # Write PCAP global header but truncate packet record header midway
            pcap_header = b"\xd4\xc3\xb2\xa1\x02\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00\x00\x01\x00\x00\x00"
            truncated_packet = b"\x00\x01\x02"  # Incomplete packet header (needs 16 bytes)
            tf.write(pcap_header + truncated_packet)
            trunc_pcap = tf.name

        try:
            res = subprocess.run(["capinfos", trunc_pcap], capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0, "capinfos must fail on truncated PCAP file")
        finally:
            if os.path.exists(trunc_pcap):
                os.remove(trunc_pcap)

    def test_09_corrupted_pcap_network_doctor_failure(self):
        """Verify that agy-network-doctor reports failure when pointed at corrupted fixture."""
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pcap") as tf:
            tf.write(b"INVALID_HEADER_NOT_A_REAL_CAPTURE")
            bad_pcap = tf.name

        try:
            doctor_bin = os.path.join(TOOLS_BIN, "agy-network-doctor")
            res = subprocess.run([sys.executable, doctor_bin, "--fixture", bad_pcap], capture_output=True, text=True)
            self.assertEqual(res.returncode, 1, "agy-network-doctor must exit with code 1 on corrupted fixture")
            self.assertIn("FAIL", res.stdout, "Doctor output must record functional check FAIL")
            self.assertIn("Remediation Suggestions:", res.stdout, "Doctor must output remediation guidance")
        finally:
            if os.path.exists(bad_pcap):
                os.remove(bad_pcap)


class TestFailureInjectionAndroidSDK(unittest.TestCase):
    """Failure injection tests for Android SDK path validation."""

    def test_10_missing_android_sdk_detected_by_doctor(self):
        """Verify that agy-android-doctor detects invalid ANDROID_HOME."""
        env = os.environ.copy()
        env["ANDROID_HOME"] = "/nonexistent/path/for/failure/test"
        
        res = subprocess.run(["bash", os.path.join(TOOLS_BIN, "agy-android-doctor")], env=env, capture_output=True, text=True)
        self.assertIn("not found", res.stdout.lower(), "agy-android-doctor must report not found for invalid SDK directory")

    def test_11_invalid_android_sdk_env_doctor_handling(self):
        """Verify that agy-env-doctor correctly handles invalid ANDROID_HOME."""
        env = os.environ.copy()
        env["ANDROID_HOME"] = "/nonexistent/path/for/failure/test"
        
        doctor_bin = os.path.join(TOOLS_BIN, "agy-env-doctor")
        res = subprocess.run([sys.executable, doctor_bin], env=env, capture_output=True, text=True)
        # Doctor should run without crashing and flag missing Android SDK tools
        self.assertIn("Android / Mobile", res.stdout)


class TestFailureInjectionCompilers(unittest.TestCase):
    """Failure injection tests for C/C++ compilation and build failures."""

    def test_12_malformed_c_syntax_compilation_failure(self):
        """Verify that GCC rejects intentionally broken C code."""
        bad_c_code = "int main(void) { invalid syntax !!! undefined_token += ; }"
        res = subprocess.run(["gcc", "-x", "c", "-", "-o", "/dev/null"], input=bad_c_code, capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0, "GCC must reject invalid C syntax with non-zero exit code")
        self.assertTrue(len(res.stderr) > 0, "Compiler stderr must contain diagnostic syntax error messages")

    def test_13_malformed_cpp_syntax_compilation_failure(self):
        """Verify that G++ rejects intentionally broken C++ template code."""
        bad_cpp_code = "#include <vector>\ntemplate <typename T class Broken { T val; }; int main() { return 0; }"
        res = subprocess.run(["g++", "-x", "c++", "-", "-o", "/dev/null"], input=bad_cpp_code, capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0, "G++ must reject invalid C++ template syntax")
        self.assertTrue(len(res.stderr) > 0, "Compiler stderr must report syntax errors")

    def test_14_broken_cmake_configure_failure(self):
        """Verify CMake fails on malformed CMakeLists.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cmake_file = os.path.join(tmpdir, "CMakeLists.txt")
            with open(cmake_file, "w") as f:
                f.write("cmake_minimum_required(VERSION 3.20)\nproject(Broken)\nset(BROKEN_SYNTAX (\n")
            
            res = subprocess.run(["cmake", "-B", os.path.join(tmpdir, "build")], cwd=tmpdir, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0, "CMake must fail on unclosed parentheses / syntax errors")


class TestFailureInjectionSecurityGate(unittest.TestCase):
    """Failure injection tests against PreToolUse security hook and SecretScanner."""

    def test_15_pre_tool_use_blocks_aws_access_key(self):
        """Verify PreToolUse hook intercepts and denies AWS Access Key ID."""
        prefix = "AK" + "IA"
        sample_key = prefix + "IOSFODNN7EXAMPLE"
        payload = json.dumps({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": f"export AWS_ACCESS_KEY_ID={sample_key}"}
            }
        })
        
        hook_script = os.path.join(SCRIPTS_DIR, "hooks/pre_tool_use.py")
        res = subprocess.run([sys.executable, hook_script], input=payload, capture_output=True, text=True)
        
        self.assertEqual(res.returncode, 0, "Hook script execution itself must succeed")
        data = json.loads(res.stdout.strip())
        self.assertEqual(data.get("decision"), "deny", "Hook must deny tool execution containing AWS Access Key")
        self.assertIn("Security violation", data.get("reason", ""), "Reason must specify security violation")

    def test_16_pre_tool_use_blocks_github_pat(self):
        """Verify PreToolUse hook intercepts and denies GitHub Personal Access Token."""
        prefix = "gh" + "p_"
        sample_pat = prefix + "1234567890abcdefghijklmnopqrstuvwxyz"
        payload = json.dumps({
            "toolCall": {
                "name": "write_to_file",
                "args": {"CodeContent": f"GITHUB_TOKEN = '{sample_pat}'"}
            }
        })
        
        hook_script = os.path.join(SCRIPTS_DIR, "hooks/pre_tool_use.py")
        res = subprocess.run([sys.executable, hook_script], input=payload, capture_output=True, text=True)
        
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout.strip())
        self.assertEqual(data.get("decision"), "deny", "Hook must deny tool execution containing GitHub PAT")

    def test_17_pre_tool_use_blocks_private_key(self):
        """Verify PreToolUse hook intercepts and denies RSA / OpenSSH private key."""
        header = "-----" + "BEGIN OPENSSH PRIVATE KEY" + "-----"
        payload = json.dumps({
            "toolCall": {
                "name": "replace_file_content",
                "args": {"ReplacementContent": f"{header}\nb3BlbnNzaC1rZXktdjEAAAA\n-----END OPENSSH PRIVATE KEY-----"}
            }
        })
        
        hook_script = os.path.join(SCRIPTS_DIR, "hooks/pre_tool_use.py")
        res = subprocess.run([sys.executable, hook_script], input=payload, capture_output=True, text=True)
        
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout.strip())
        self.assertEqual(data.get("decision"), "deny", "Hook must deny tool execution containing private key")

    def test_18_pre_tool_use_allows_clean_payload(self):
        """Verify PreToolUse hook allows clean and legitimate tool executions."""
        payload = json.dumps({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "python3 -m unittest discover tests -v"}
            }
        })
        
        hook_script = os.path.join(SCRIPTS_DIR, "hooks/pre_tool_use.py")
        res = subprocess.run([sys.executable, hook_script], input=payload, capture_output=True, text=True)
        
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout.strip())
        self.assertEqual(data.get("decision"), "allow", "Hook must allow clean commands")


class TestFailureInjectionWASM(unittest.TestCase):
    """Failure injection tests for WebAssembly assembler and validator."""

    def test_19_malformed_wat_syntax_failure(self):
        """Verify wat2wasm rejects invalid WebAssembly text syntax."""
        res = subprocess.run(["wat2wasm", "-", "-o", "/dev/null"], input=b"(module (func (broken_nonexistent_opcode_xyz)))", capture_output=True)
        self.assertNotEqual(res.returncode, 0, "wat2wasm must reject invalid WAT opcode")

    def test_20_corrupted_wasm_binary_validation_failure(self):
        """Verify wasm-validate rejects corrupted WebAssembly binary header."""
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".wasm") as tf:
            tf.write(b"\x00asm\x02\x00\x00\x00\xff\xff\xff\xff")  # Unsupported WASM version 2 + bad section
            bad_wasm = tf.name

        try:
            res = subprocess.run(["wasm-validate", bad_wasm], capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0, "wasm-validate must reject invalid WASM binary")
        finally:
            if os.path.exists(bad_wasm):
                os.remove(bad_wasm)


class TestFailureInjectionAgentPlatform(unittest.TestCase):
    """Failure injection tests for Agent master guide and hooks configuration."""

    def test_21_malformed_hooks_json_detection(self):
        """Verify that agy-agent-doctor detects malformed JSON in hooks.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = os.path.join(tmpdir, ".agents")
            os.makedirs(agents_dir, exist_ok=True)
            hooks_path = os.path.join(agents_dir, "hooks.json")
            with open(hooks_path, "w") as f:
                f.write("{ broken_json_hook: [")

            res = subprocess.run(["bash", os.path.join(TOOLS_BIN, "agy-agent-doctor")], cwd=tmpdir, capture_output=True, text=True)
            self.assertIn("FAIL", res.stdout, "agy-agent-doctor must report FAIL for malformed hooks.json")

    def test_22_missing_agents_md_detection(self):
        """Verify that agy-agent-doctor detects missing AGENTS.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            res = subprocess.run(["bash", os.path.join(TOOLS_BIN, "agy-agent-doctor")], cwd=tmpdir, capture_output=True, text=True)
            self.assertIn("FAIL", res.stdout, "agy-agent-doctor must report FAIL when AGENTS.md is missing")


if __name__ == "__main__":
    unittest.main()
