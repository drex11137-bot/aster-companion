#!/usr/bin/env python3
"""
Unit tests for iOS / Swift macOS Handoff Architecture verification.
Verifies toolchain boundaries, SweetPad platform constraints, and handoff schema validity.
"""

import json
import os
import shutil
import unittest


class TestIOSMacOSHandoffVerification(unittest.TestCase):
    def setUp(self):
        self.repo_root = "/workspaces/codespaces-blank"
        self.docs_path = os.path.join(self.repo_root, "docs", "ios-macos-handoff.md")
        self.schema_path = os.path.join(self.repo_root, "docs", "schemas", "ios-handoff.schema.json")
        self.sample_handoff_path = os.path.join(self.repo_root, "docs", "schemas", "sample-handoff.json")

    def test_01_documentation_exists_and_contains_required_sections(self):
        """Verify ios-macos-handoff.md exists and covers all Section 6 requirements."""
        self.assertTrue(os.path.isfile(self.docs_path), "ios-macos-handoff.md must exist")
        with open(self.docs_path, "r", encoding="utf-8") as f:
            content = f.read()

        required_terms = [
            "UNAVAILABLE_ON_CURRENT_PLATFORM",
            "sweetpad.sweetpad",
            "xcodebuild",
            "xcode-build-server",
            "SourceKit-LSP",
            "swift-format",
            "SwiftLint",
            "iOS Simulator",
            "Handoff Architecture",
            "buildServer.json",
        ]
        for term in required_terms:
            self.assertIn(term, content, f"Documentation must contain '{term}'")

    def test_02_sweetpad_native_binary_darwin_boundary(self):
        """Verify that SweetPad extension native binary is restricted to Darwin."""
        ext_dir = "/home/codespace/.vscode-remote/extensions"
        if not os.path.isdir(ext_dir):
            self.skipTest("VS Code remote extensions directory not found")

        sweetpad_dirs = [d for d in os.listdir(ext_dir) if "sweetpad.sweetpad" in d]
        if not sweetpad_dirs:
            self.skipTest("SweetPad extension not installed")

        sweetpad_path = os.path.join(ext_dir, sweetpad_dirs[0])
        native_dir = os.path.join(sweetpad_path, "native")
        if os.path.isdir(native_dir):
            files = os.listdir(native_dir)
            has_darwin = any("darwin" in f for f in files)
            has_linux = any("linux" in f for f in files)
            self.assertTrue(has_darwin, "SweetPad native module contains Darwin binaries")
            self.assertFalse(has_linux, "SweetPad native module must NOT contain Linux binaries")

    def test_03_xcode_tools_unavailable_on_linux(self):
        """Verify xcodebuild and xcrun are unavailable on Linux Codespace."""
        self.assertIsNone(shutil.which("xcodebuild"), "xcodebuild must be unavailable on Linux")
        self.assertIsNone(shutil.which("xcrun"), "xcrun must be unavailable on Linux")
        self.assertIsNone(shutil.which("simctl"), "simctl must be unavailable on Linux")

    def test_04_handoff_schema_and_sample_validity(self):
        """Verify handoff JSON schema and sample payload structure."""
        self.assertTrue(os.path.isfile(self.schema_path), "Schema file must exist")
        self.assertTrue(os.path.isfile(self.sample_handoff_path), "Sample handoff JSON must exist")

        with open(self.schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        with open(self.sample_handoff_path, "r", encoding="utf-8") as f:
            sample = json.load(f)

        # Validate with jsonschema library if present
        try:
            import jsonschema
            jsonschema.validate(instance=sample, schema=schema)
        except ImportError:
            pass

        # Validate required top-level keys
        for req in schema.get("required", []):
            self.assertIn(req, sample, f"Sample handoff must contain required key: '{req}'")

        self.assertEqual(sample["sourceEnvironment"]["platform"], "linux-codespace")
        self.assertIn("darwin", sample["targetEnvironment"]["platform"])
        self.assertIn("build", sample["actions"])
        self.assertIn("test", sample["actions"])

    def test_05_anti_hallucination_guidelines_present(self):
        """Verify anti-hallucination guardrails are strictly defined."""
        with open(self.docs_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("claim Xcode or `xcodebuild` is available locally", content)
        self.assertIn("claim an iOS Simulator is running", content)


if __name__ == "__main__":
    unittest.main()
