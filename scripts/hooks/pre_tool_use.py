#!/usr/bin/env python3
"""
PreToolUse Hook for Antigravity Persistent Memory.
Intercepts tool calls to prevent writing secrets or credentials.
Ensures non-blocking execution (<50ms performance budget), 
idempotence via state hashing, and graceful handling of failures.
"""

import sys
import json
import os
import hashlib
import tempfile
import time

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

CACHE_TTL_SECONDS = int(os.environ.get("ANTIGRAVITY_CACHE_TTL", 86400))

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    try:
        tool_call = payload.get("toolCall") or {}
        name = tool_call.get("name", "") if isinstance(tool_call, dict) else ""
        args = tool_call.get("args") or {} if isinstance(tool_call, dict) else {}
        if not isinstance(args, dict):
            args = {}

        parts = []
        if "CodeContent" in args and args["CodeContent"] is not None:
            parts.append(str(args["CodeContent"]))
        if "ReplacementContent" in args and args["ReplacementContent"] is not None:
            parts.append(str(args["ReplacementContent"]))
        if "CommandLine" in args and args["CommandLine"] is not None:
            parts.append(str(args["CommandLine"]))
        if "Input" in args and args["Input"] is not None:
            parts.append(str(args["Input"]))
        if "Content" in args and args["Content"] is not None:
            parts.append(str(args["Content"]))

        content_to_scan = "\n".join(parts)

        if content_to_scan:
            content_hash = hashlib.sha256(content_to_scan.encode("utf-8")).hexdigest()
            cache_file = None
            try:
                secure_cache_dir = os.path.expanduser("~/.cache/antigravity/security_cache")
                os.makedirs(secure_cache_dir, mode=0o700, exist_ok=True)
                cache_file = os.path.join(secure_cache_dir, f"ag_sec_{content_hash}")
                if os.path.exists(cache_file):
                    st = os.stat(cache_file)
                    now = time.time()
                    if st.st_size > 0 and 0 <= (now - st.st_mtime) < CACHE_TTL_SECONDS:
                        print(json.dumps({"decision": "allow"}))
                        return
            except Exception:
                cache_file = None
                
            from secret_scanner import scan_text
            res = scan_text(content_to_scan)
            if not res.is_clean:
                reasons = [f"{f.description} ({f.matched_snippet_redacted})" for f in res.findings]
                output = {
                    "decision": "deny",
                    "reason": f"Security violation: Tool execution blocked due to secret detection: {'; '.join(reasons)}"
                }
                print(json.dumps(output))
                return
                
            if cache_file:
                try:
                    with open(cache_file, "w") as f:
                        f.write("1")
                except Exception:
                    pass

        print(json.dumps({"decision": "allow"}))
    except Exception as e:
        # Fail-closed security gate
        print(json.dumps({"decision": "deny", "reason": "PreToolUse security gate exception (fail-closed)"}))

if __name__ == "__main__":
    main()
