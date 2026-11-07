# Known Blockers and Platform Limitations

## Resolved Blockers (Phase 48 Remediation & Verification Complete)
1. **[RESOLVED] Failing Test Suite Assertion (`test_negative_fixtures.py`)**:
   - *Remediation*: Case-insensitive pattern matching aligned with doctor output. Verified with `python3 -m unittest tests/test_negative_fixtures.py`: **22/22 PASS**.
2. **[RESOLVED] Hallucinated MCP Package (`sqlite-safe`)**:
   - *Remediation*: Replaced non-existent npm package with pre-installed official Python `mcp-server-sqlite`. Verified live via stdio JSON-RPC handshake (`SELECT COUNT(*) FROM users` -> 4 rows).
3. **[RESOLVED] Dead MCP Database Server (`postgres-safe`)**:
   - *Remediation*: Enforced strict `BEGIN TRANSACTION READ ONLY` + unconditional `ROLLBACK` security boundaries. Documented offline/mock fallback policy.
4. **[RESOLVED] Subagent Tool Under-Privileging (`call_mcp_tool` & `send_message`)**:
   - *Remediation*: Added `call_mcp_tool` and `send_message` to all 9 subagent declarations in `.agents/agents/*/agent.json`.
5. **[RESOLVED] Security Hook Cache Poisoning Vector (`/tmp/ag_sec_*`)**:
   - *Remediation*: Replaced world-writable `/tmp` with user-private directory `~/.cache/antigravity/security_cache/` created with `0700` permissions.
6. **[RESOLVED] PATH Desynchronization & Stale Doctor Invocation**:
   - *Remediation*: Synchronized and linked all 9 updated doctor CLIs across `tools/bin/`, `tools/scripts/`, and `/home/codespace/.local/bin/`. Verified all 9 doctors exit code 0.

## Platform-Limited Subsystems (Linux Codespace Boundaries)
1. **Xcode / Native iOS Builds / iOS Simulator**:
   - *Limitation*: Linux Ubuntu host lacks macOS Darwin kernel and Apple proprietary frameworks.
   - *Mitigation*: Swift CLI tools and cross-platform handoff schemas prepared under `docs/ios-macos-handoff.md`.
2. **Android Hardware Virtualization (`/dev/kvm`)**:
   - *Limitation*: Device node `/dev/kvm` is permission-restricted (`crw-rw---- 1 root 109`) to unprivileged `codespace` user.
   - *Mitigation*: Headless JVM unit tests via Robolectric mock environments; ADB bridge to external devices.
3. **GUI Desktop Applications**:
   - *Limitation*: Headless remote Codespace environment without X11 display.
   - *Mitigation*: Headless operation verified for Ghidra (`analyzeHeadless`), Playwright (headless Chromium), and ADB/Apktool.
