#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "RUNNING DEVCONTAINER HEALTH CHECK"
echo "============================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [ -x "${WORKSPACE_ROOT}/tools/bin/agy-env-doctor" ]; then
    "${WORKSPACE_ROOT}/tools/bin/agy-env-doctor"
elif [ -x "${WORKSPACE_ROOT}/tools/scripts/agy-env-doctor" ]; then
    "${WORKSPACE_ROOT}/tools/scripts/agy-env-doctor"
elif command -v agy-env-doctor >/dev/null 2>&1; then
    agy-env-doctor
else
    echo "[ERROR] agy-env-doctor executable not found in tools/bin, tools/scripts, or PATH." >&2
    exit 1
fi
