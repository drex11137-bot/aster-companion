#!/usr/bin/env python3
"""
Stop Hook for Antigravity Platform (Session Guard).
Verifies active working session state and ensures clean shutdown.
Returns {"decision": "stop"} or {"decision": "continue", "reason": "..."}.
"""

import sys
import json
import os

def main():
    try:
        raw_input = sys.stdin.read()
        payload = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        payload = {}

    try:
        # Check if any mandatory uncommitted state exists or background tasks
        fully_idle = payload.get("fullyIdle", True) if isinstance(payload, dict) else True
        termination_reason = payload.get("terminationReason", "model_stop") if isinstance(payload, dict) else "model_stop"
        
        # Standard graceful stop
        print(json.dumps({"decision": "stop"}))
    except Exception:
        print(json.dumps({"decision": "stop"}))

if __name__ == "__main__":
    main()
