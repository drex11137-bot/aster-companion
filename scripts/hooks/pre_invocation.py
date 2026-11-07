#!/usr/bin/env python3
"""
PreInvocation Hook for Antigravity Persistent Memory.
Injects context reminder if previous session was interrupted or pending actions exist.
Ensures non-blocking execution (<50ms budget) and idempotence via state hashing.
"""

import sys
import json
import os
import hashlib
import tempfile

def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        input_data = {}

    try:
        session_id = input_data.get("conversationId") or input_data.get("session_id") or "default"
        cache_file = os.path.join(tempfile.gettempdir(), f"ag_preinv_{hashlib.sha256(session_id.encode()).hexdigest()}")
        
        if os.path.exists(cache_file):
            print(json.dumps({"injectSteps": []}))
            return

        workspace_paths = input_data.get("workspacePaths", [])
        ws_root = workspace_paths[0] if (workspace_paths and isinstance(workspace_paths, list)) else "/workspaces/codespaces-blank"
        current_md = os.path.join(ws_root, ".agents/memory/CURRENT.md")
        inject_steps = []
        
        if os.path.exists(current_md):
            with open(current_md, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(1024) # Read max 1KB for performance
                if "Current Objective" in content:
                    inject_steps.append({
                        "ephemeralMessage": "Antigravity Memory Directive: Memory is advisory. Inspect .agents/memory/INDEX.md and load only relevant context."
                    })

        try:
            with open(cache_file, "w") as f:
                f.write("1")
        except Exception:
            pass

        print(json.dumps({"injectSteps": inject_steps}))
    except Exception as e:
        print(json.dumps({"injectSteps": []}))

if __name__ == "__main__":
    main()
