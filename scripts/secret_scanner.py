#!/usr/bin/env python3
"""
Secret Scanner & Security Gatekeeper for Antigravity Persistent Memory.
Phase 16 - Memory Security.

This module provides strict security scanning to prevent persisting:
- API keys (OpenAI, Anthropic, Google, AWS, GitHub, GitLab, Slack, Stripe, Hugging Face, etc.)
- OAuth tokens, access tokens, bearer tokens
- SSH private keys, RSA/ECDSA/OpenSSH headers, PGP keys
- Passwords, basic auth credentials, URI connection strings with passwords
- Cookies, session headers, session IDs, JWT tokens
- Private certificates and certificate requests
- Generic high-entropy secrets and credential assignments

Usage:
    CLI:
        python3 secret_scanner.py --file <path>
        python3 secret_scanner.py --text "candidate memory text"
        python3 secret_scanner.py --dir <directory_path>
        python3 secret_scanner.py --stdin
    Python:
        from scripts.secret_scanner import SecretScanner, scan_text, scan_file
        result = scan_text(candidate_memory_content)
        if not result.is_clean:
            print("Security violation:", result.summary_message)
"""

import os
import re
import sys
import math
import json
import argparse
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict


# Severity levels
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"


@dataclass
class ScanFinding:
    """Represents a single security finding/secret match."""
    rule_name: str
    category: str
    severity: str
    line_number: int
    matched_snippet_redacted: str
    line_content_redacted: str
    description: str
    confidence: str = "HIGH"  # HIGH, MEDIUM, LOW

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScanResult:
    """Represents the complete result of scanning a text or file."""
    status: str  # "PASS" or "FAIL"
    scanned_target: str  # file path, or "in-memory text", etc.
    total_lines: int
    findings: List[ScanFinding] = field(default_factory=list)
    execution_time_ms: float = 0.0

    @property
    def is_clean(self) -> bool:
        return self.status == "PASS" and len(self.findings) == 0

    @property
    def summary_message(self) -> str:
        if self.is_clean:
            return f"PASS: No secrets or security violations detected ({self.total_lines} lines scanned in {self.execution_time_ms:.2f}ms)."
        
        counts: Dict[str, int] = {}
        for f in self.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        
        counts_str = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
        return f"FAIL: {len(self.findings)} secret(s)/security violation(s) detected [{counts_str}] in {self.scanned_target} ({self.execution_time_ms:.2f}ms)."

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "is_clean": self.is_clean,
            "scanned_target": self.scanned_target,
            "total_lines": self.total_lines,
            "total_findings": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "execution_time_ms": self.execution_time_ms,
            "summary": self.summary_message,
        }


def calculate_entropy(text: str) -> float:
    """Calculate enhanced Shannon entropy of a string."""
    if not text:
        return 0.0
        
    # Enhanced: remove spaces and common punctuation to avoid natural language false positives
    clean_text = re.sub(r'[\s\'".,;:!?()[\]{}\\-]', '', text)
    if not clean_text:
        return 0.0
        
    entropy = 0.0
    length = len(clean_text)
    freq: Dict[str, int] = {}
    for char in clean_text:
        freq[char] = freq.get(char, 0) + 1
    for count in freq.values():
        p_x = count / length
        entropy += - p_x * math.log2(p_x)
    
    # Penalize purely lowercase or purely uppercase strings with no numbers (less likely to be a high-entropy secret)
    if clean_text.isalpha() and (clean_text.islower() or clean_text.isupper()):
        entropy *= 0.8
        
    return entropy


def redact_secret(secret_str: str) -> str:
    """Redact secret leaving only prefix/suffix for identification."""
    if not secret_str:
        return "[REDACTED]"
    secret_str = secret_str.strip()
    length = len(secret_str)
    if length <= 6:
        return "[REDACTED]"
    if length <= 12:
        return secret_str[:2] + "****" + secret_str[-2:]
    return secret_str[:4] + "****" + secret_str[-4:]


def redact_line(line: str, matched_str: str) -> str:
    """Return line content with the matched secret redacted."""
    if not matched_str or matched_str not in line:
        return line[:160]
    redacted = redact_secret(matched_str)
    return line.replace(matched_str, redacted)[:200]


# Known safe placeholders that should not trigger false positives
SAFE_PLACEHOLDER_KEYWORDS = [
    "your_api_key",
    "your_key",
    "your_token",
    "your_secret",
    "your_password",
    "your_openai_key",
    "your_anthropic_key",
    "your_aws_access_key",
    "your_aws_secret_key",
    "your_github_token",
    "my_api_key",
    "api_key_here",
    "secret_key_here",
    "insert_api_key",
    "insert_key",
    "replace_with_your",
    "dummy_key",
    "example_key",
    "test_key",
    "sample_key",
    "placeholder",
    "changeme",
    "redacted",
    "process.env.",
    "os.environ",
    "os.getenv",
]


class SecretScanner:
    """Strict security scanner for candidate memories, notes, and session logs."""

    def __init__(self, entropy_threshold: float = 3.5, min_entropy_len: int = 16):
        self.entropy_threshold = entropy_threshold
        self.min_entropy_len = min_entropy_len
        self._init_rules()

    def _init_rules(self):
        """Initialize scanning regular expressions grouped by security category."""
        # 1. API Keys
        self.api_key_rules = [
            (
                "OpenAI API Key (Project/Admin)",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"\b(sk-(?:proj|admin)-[A-Za-z0-9_\-]{20,})\b"),
                "OpenAI project or admin API key detected."
            ),
            (
                "OpenAI API Key (Standard)",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"\b(sk-[a-zA-Z0-9_\-]{20,64})\b"),
                "OpenAI standard API key detected."
            ),
            (
                "Anthropic API Key",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"\b(sk-ant-(?:api03-)?[a-zA-Z0-9_\-]{32,})\b"),
                "Anthropic Claude API key detected."
            ),
            (
                "Google Gemini / Cloud API Key",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"\b(AIza[0-9A-Za-z\-_]{35,45})\b"),
                "Google API / Gemini key detected."
            ),
            (
                "AWS Access Key ID",
                "API_KEY",
                SEVERITY_HIGH,
                re.compile(r"\b((?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16})\b"),
                "AWS Access Key ID detected."
            ),
            (
                "AWS Secret Access Key Assignment",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"(?i)\b(?:aws_secret_access_key|aws_secret_key|secret_access_key)\s*[:=]\s*[\"']?([A-Za-z0-9/+=]{40})[\"']?"),
                "AWS Secret Access Key assignment detected."
            ),
            (
                "GitHub Personal Access Token (Classic)",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"\b(ghp_[a-zA-Z0-9]{36})\b"),
                "GitHub Personal Access Token detected."
            ),
            (
                "GitHub Fine-grained PAT",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"\b(github_pat_[a-zA-Z0-9_]{50,100})\b"),
                "GitHub Fine-grained Personal Access Token detected."
            ),
            (
                "GitHub OAuth / App / Refresh Token",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"\b((?:gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36})\b"),
                "GitHub OAuth/App/Refresh token detected."
            ),
            (
                "GitLab Access Token",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"\b((?:glpat|glptt|glrt)-[0-9a-zA-Z_\-]{20,})\b"),
                "GitLab personal/trigger/runner token detected."
            ),
            (
                "Slack API Token",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"\b(xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9]*-[a-zA-Z0-9]{24,32})\b"),
                "Slack user or bot token detected."
            ),
            (
                "Slack Webhook URL",
                "API_KEY",
                SEVERITY_HIGH,
                re.compile(r"(https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+)"),
                "Slack incoming webhook URL with secret credentials detected."
            ),
            (
                "Stripe API Secret / Restricted Key",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"\b((?:sk|rk)_(?:live|test)_[0-9a-zA-Z]{24,})\b"),
                "Stripe API secret/restricted key detected."
            ),
            (
                "Hugging Face User Access Token",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"\b(hf_[a-zA-Z0-9]{34,})\b"),
                "Hugging Face user access token detected."
            ),
            (
                "AWS Session Token",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"(?i)\b(?:aws_session_token|session_token)\s*[:=]\s*[\"']?([A-Za-z0-9/+=]{16,})[\"']?"),
                "AWS Session Token assignment detected."
            ),
            (
                "DigitalOcean Personal Access Token",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"\b(dop_v1_[a-f0-9]{64})\b"),
                "DigitalOcean Personal Access Token detected."
            ),
            (
                "SendGrid API Key",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"\b(SG\.[a-zA-Z0-9_\-\.]{22}\.[a-zA-Z0-9_\-\.]{43})\b"),
                "SendGrid API Key detected."
            ),
            (
                "NPM Access Token",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"\b(npm_[a-zA-Z0-9]{36})\b"),
                "NPM access token detected."
            ),
            (
                "PyPI API Token",
                "API_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"\b(pypi-AgEIcHlwaS5vcmc[a-zA-Z0-9\-_]{50,})\b"),
                "PyPI API token detected."
            ),
        ]

        # 2. OAuth & Bearer Tokens
        self.token_rules = [
            (
                "Google OAuth Access Token",
                "OAUTH_TOKEN",
                SEVERITY_CRITICAL,
                re.compile(r"\b(ya29\.[0-9A-Za-z\-_]{25,})\b"),
                "Google OAuth 2.0 access token detected."
            ),
            (
                "Authorization Bearer / Token Header",
                "BEARER_TOKEN",
                SEVERITY_CRITICAL,
                re.compile(r"(?i)\bauthorization\s*:\s*(?:bearer|token)\s+([a-zA-Z0-9_\-\.=+]{20,})"),
                "Authorization Bearer header with token detected."
            ),
            (
                "Standalone Bearer Token",
                "BEARER_TOKEN",
                SEVERITY_HIGH,
                re.compile(r"(?i)\bbearer\s+([a-zA-Z0-9_\-\.=+]{30,})"),
                "Bearer token detected."
            ),
            (
                "JSON Web Token (JWT)",
                "JWT_TOKEN",
                SEVERITY_CRITICAL,
                re.compile(r"\b(eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})\b"),
                "JSON Web Token (JWT) detected."
            ),
        ]

        # 3. Private Keys & Certificates
        self.crypto_rules = [
            (
                "Private Key Header (OpenSSH/RSA/EC/DSA/PGP)",
                "PRIVATE_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"(-----BEGIN (?:RSA|OPENSSH|DSA|EC|ECDSA|PGP|ENCRYPTED)? ?PRIVATE KEY(?: BLOCK)?-----)"),
                "Private cryptographic key header detected."
            ),
            (
                "PuTTY Private Key Header",
                "PRIVATE_KEY",
                SEVERITY_CRITICAL,
                re.compile(r"(PuTTY-User-Key-File-[0-9]:)"),
                "PuTTY private key file header detected."
            ),
            (
                "Private Certificate Request / Encrypted Key",
                "PRIVATE_CERTIFICATE",
                SEVERITY_HIGH,
                re.compile(r"(-----BEGIN (?:CERTIFICATE REQUEST|ENCRYPTED PRIVATE KEY)-----)"),
                "Private certificate request or encrypted key detected."
            ),
        ]

        # 4. Passwords & Auth Credentials
        self.credential_rules = [
            (
                "URI with Embedded Credentials",
                "CREDENTIALS",
                SEVERITY_CRITICAL,
                re.compile(r"\b((?:postgres|postgresql|mysql|mongodb|redis|amqp|sftp|ftp|https?)://[a-zA-Z0-9_\.\-]+:([^@\s/:]{3,})@[a-zA-Z0-9_\.\-]+)"),
                "Connection URI containing embedded username and password detected."
            ),
            (
                "Basic Authorization Header",
                "CREDENTIALS",
                SEVERITY_CRITICAL,
                re.compile(r"(?i)\bauthorization\s*:\s*basic\s+([a-zA-Z0-9+/=]{12,})"),
                "Basic Authentication credentials header detected."
            ),
            (
                "Hardcoded Password Assignment",
                "PASSWORD",
                SEVERITY_CRITICAL,
                re.compile(r"(?i)\b(?:password|passwd|pwd|db_pass)\s*[:=]\s*[\"']([^\"'\n\r]{6,})[\"']"),
                "Hardcoded password or secret key assignment detected."
            ),
        ]

        # 5. Cookies & Session Headers
        self.session_rules = [
            (
                "Cookie / Session Header",
                "SESSION_COOKIE",
                SEVERITY_HIGH,
                re.compile(r"(?i)\b(?:set-cookie|cookie)\s*:\s*[^;\r\n]*(?:session(?:_id)?|token|auth|jwt|connect\.sid|PHPSESSID|JSESSIONID)=([^;\r\n\s]{8,})"),
                "Cookie or session header containing session tokens detected."
            ),
            (
                "Session ID Assignment",
                "SESSION_COOKIE",
                SEVERITY_MEDIUM,
                re.compile(r"(?i)\b(?:session_id|sessionid|sess_token)\s*[:=]\s*[\"']([a-zA-Z0-9_\-\.]{16,})[\"']"),
                "Explicit session ID token assignment detected."
            ),
        ]

        # 6. Generic High Entropy / Sensitive Variable Assignment
        self.generic_secret_pattern = re.compile(
            r"(?i)\b(?:secret|token|credential|api_key|access_key|auth_token|private_key|client_secret|secret_key|api_secret)\s*[:=]\s*[\"']([^\"'\r\n]{12,})[\"']"
        )

    def _is_safe_placeholder(self, matched_text: str, line_content: str) -> bool:
        """Check if matched text is an obvious placeholder, template variable, or doc example."""
        matched_clean = matched_text.strip().strip("\"'<>{}[]")
        
        # Check against list of safe placeholder keywords in the matched value
        matched_lower = matched_clean.lower()
        for safe in SAFE_PLACEHOLDER_KEYWORDS:
            if safe in matched_lower:
                return True
        
        # Check if matched text is a template variable syntax
        if matched_clean.startswith("<") and matched_clean.endswith(">"):
            return True
        if matched_clean.startswith("${") and matched_clean.endswith("}"):
            return True

        # Check if matched text is repeated dummy characters (e.g., 'xxxxxxxx', '00000000', '------')
        if len(set(matched_clean)) <= 2:
            return True

        return False

    def scan_line(self, line: str, line_num: int) -> List[ScanFinding]:
        """Scan a single line of text across all rule categories."""
        findings: List[ScanFinding] = []
        
        # Aggregate all structured rule sets
        all_rules = (
            self.api_key_rules +
            self.token_rules +
            self.crypto_rules +
            self.credential_rules +
            self.session_rules
        )

        for rule_name, category, severity, pattern, description in all_rules:
            for match in pattern.finditer(line):
                # Extract matched group or full match
                matched_str = match.group(1) if match.groups() else match.group(0)
                
                # Check for safe placeholders
                if self._is_safe_placeholder(matched_str, line):
                    continue

                finding = ScanFinding(
                    rule_name=rule_name,
                    category=category,
                    severity=severity,
                    line_number=line_num,
                    matched_snippet_redacted=redact_secret(matched_str),
                    line_content_redacted=redact_line(line, matched_str),
                    description=description,
                    confidence="HIGH"
                )
                findings.append(finding)

        # Generic high-entropy variable assignment check
        for match in self.generic_secret_pattern.finditer(line):
            matched_val = match.group(1)
            if self._is_safe_placeholder(matched_val, line):
                continue
            
            # If already caught by specific rule, skip
            if any(f.matched_snippet_redacted == redact_secret(matched_val) for f in findings):
                continue

            if len(matched_val) >= self.min_entropy_len:
                entropy = calculate_entropy(matched_val)
                if entropy >= self.entropy_threshold:
                    findings.append(ScanFinding(
                        rule_name="High-Entropy Generic Secret Assignment",
                        category="HIGH_ENTROPY_SECRET",
                        severity=SEVERITY_HIGH,
                        line_number=line_num,
                        matched_snippet_redacted=redact_secret(matched_val),
                        line_content_redacted=redact_line(line, matched_val),
                        description=f"Generic secret assignment with high Shannon entropy ({entropy:.2f} bits/symbol).",
                        confidence="MEDIUM"
                    ))

        return findings

    def scan_text(self, text: str, target_name: str = "in-memory text") -> ScanResult:
        """Scan full text string for secrets and security violations."""
        start_time = time.perf_counter()
        findings: List[ScanFinding] = []
        
        if not text:
            elapsed = (time.perf_counter() - start_time) * 1000.0
            return ScanResult(
                status="PASS",
                scanned_target=target_name,
                total_lines=0,
                findings=[],
                execution_time_ms=elapsed
            )

        lines = text.splitlines()
        for idx, line in enumerate(lines, 1):
            line_findings = self.scan_line(line, idx)
            findings.extend(line_findings)

        # Multi-line checks (e.g. multi-line private key blocks or cert blocks)
        if "-----BEGIN" in text and "PRIVATE KEY" in text:
            # If not already caught in line-by-line
            if not any(f.category == "PRIVATE_KEY" for f in findings):
                findings.append(ScanFinding(
                    rule_name="Multi-line Private Key Block",
                    category="PRIVATE_KEY",
                    severity=SEVERITY_CRITICAL,
                    line_number=1,
                    matched_snippet_redacted="-----BEGIN ... PRIVATE KEY-----",
                    line_content_redacted="[Multi-line private key block detected in candidate memory]",
                    description="Multi-line private cryptographic key block detected."
                ))

        elapsed = (time.perf_counter() - start_time) * 1000.0
        status = "FAIL" if findings else "PASS"
        return ScanResult(
            status=status,
            scanned_target=target_name,
            total_lines=len(lines),
            findings=findings,
            execution_time_ms=elapsed
        )

    def scan_file(self, file_path: str) -> ScanResult:
        """Scan an individual file on disk."""
        if not os.path.exists(file_path):
            return ScanResult(
                status="FAIL",
                scanned_target=file_path,
                total_lines=0,
                findings=[
                    ScanFinding(
                        rule_name="File Not Found",
                        category="ERROR",
                        severity=SEVERITY_HIGH,
                        line_number=0,
                        matched_snippet_redacted="",
                        line_content_redacted="",
                        description=f"File '{file_path}' does not exist."
                    )
                ],
                execution_time_ms=0.0
            )

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return self.scan_text(content, target_name=file_path)
        except Exception as e:
            return ScanResult(
                status="FAIL",
                scanned_target=file_path,
                total_lines=0,
                findings=[
                    ScanFinding(
                        rule_name="Read Error",
                        category="ERROR",
                        severity=SEVERITY_HIGH,
                        line_number=0,
                        matched_snippet_redacted="",
                        line_content_redacted="",
                        description=f"Error reading file '{file_path}': {str(e)}"
                    )
                ],
                execution_time_ms=0.0
            )

    def scan_directory(self, dir_path: str, recursive: bool = True) -> List[ScanResult]:
        """Scan all markdown, text, and json files in a directory."""
        results: List[ScanResult] = []
        if not os.path.exists(dir_path):
            return results

        scannable_exts = {".md", ".txt", ".json", ".yaml", ".yml", ".py", ".sh", ".env", ".cfg", ".ini"}

        for root, _, files in os.walk(dir_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in scannable_exts or file.startswith("."):
                    full_path = os.path.join(root, file)
                    results.append(self.scan_file(full_path))
            if not recursive:
                break

        return results


# Module-level convenience functions
_default_scanner = SecretScanner()


def scan_text(text: str, target_name: str = "in-memory text") -> ScanResult:
    """Convenience function to scan a text string with default scanner."""
    return _default_scanner.scan_text(text, target_name=target_name)


def scan_file(file_path: str) -> ScanResult:
    """Convenience function to scan a file with default scanner."""
    return _default_scanner.scan_file(file_path)


def scan_directory(dir_path: str, recursive: bool = True) -> List[ScanResult]:
    """Convenience function to scan a directory with default scanner."""
    return _default_scanner.scan_directory(dir_path, recursive=recursive)


def cli_main() -> int:
    """Command-line entry point for secret scanner."""
    parser = argparse.ArgumentParser(
        description="Antigravity Memory Security Gatekeeper & Secret Scanner (Phase 16)"
    )
    parser.add_argument("--file", "-f", type=str, help="Path to file to scan")
    parser.add_argument("--text", "-t", type=str, help="Direct text content to scan")
    parser.add_argument("--dir", "-d", type=str, help="Directory to scan recursively")
    parser.add_argument("--stdin", action="store_true", help="Read text to scan from standard input")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--strict", action="store_true", help="Enforce strict fail exit code on any findings")

    args = parser.parse_args()
    scanner = SecretScanner()

    results: List[ScanResult] = []

    if args.stdin:
        text = sys.stdin.read()
        results.append(scanner.scan_text(text, target_name="stdin"))
    elif args.text:
        results.append(scanner.scan_text(args.text, target_name="cli-text"))
    elif args.file:
        results.append(scanner.scan_file(args.file))
    elif args.dir:
        results.extend(scanner.scan_directory(args.dir))
    else:
        parser.print_help()
        return 0

    has_violations = any(not r.is_clean for r in results)

    if args.json:
        payload = {
            "overall_status": "FAIL" if has_violations else "PASS",
            "total_targets_scanned": len(results),
            "results": [r.to_dict() for r in results],
        }
        print(json.dumps(payload, indent=2))
    else:
        print("=" * 70)
        print("ANTIGRAVITY MEMORY SECURITY GATEKEEPER — SECRET SCAN REPORT")
        print("=" * 70)
        for res in results:
            if res.is_clean:
                print(f"✅ {res.summary_message}")
            else:
                print(f"❌ {res.summary_message}")
                for f in res.findings:
                    print(f"   - [Line {f.line_number}] [{f.severity}] {f.rule_name}")
                    print(f"     Description: {f.description}")
                    print(f"     Matched:     {f.matched_snippet_redacted}")
                    print(f"     Context:     {f.line_content_redacted.strip()}")
        print("=" * 70)
        print(f"OVERALL STATUS: {'FAIL (Secrets detected - memory write blocked)' if has_violations else 'PASS (Clean)'}")
        print("=" * 70)

    if has_violations and (args.strict or not args.json):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
