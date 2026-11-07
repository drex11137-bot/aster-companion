#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../scripts" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"

echo "============================================================"
echo "RUNNING FULL ANTIGRAVITY WORKSTATION TEST SUITE"
echo "============================================================"

TEST_OUTPUT_FILE=$(mktemp)
trap 'rm -f "${TEST_OUTPUT_FILE}"' EXIT

if python3 -m unittest discover -s /workspaces/codespaces-blank/tests -p "test_*.py" -v 2>&1 | tee "${TEST_OUTPUT_FILE}"; then
    TEST_COUNT=$(grep -E '^Ran [0-9]+ tests' "${TEST_OUTPUT_FILE}" | awk '{print $2}' || true)
    if [ -z "${TEST_COUNT}" ] || [ "${TEST_COUNT}" -eq 0 ]; then
        TEST_COUNT=$(grep -c " \.\.\. ok" "${TEST_OUTPUT_FILE}" || true)
    fi
    echo ""
    echo "============================================================"
    echo "DYNAMIC TEST VERIFICATION: ${TEST_COUNT} TESTS PASSED (100% PASS RATE)"
    echo "============================================================"
    exit 0
else
    EXIT_CODE=$?
    echo ""
    echo "============================================================"
    echo "[!] TEST SUITE FAILED WITH EXIT CODE ${EXIT_CODE}"
    echo "============================================================"
    exit ${EXIT_CODE}
fi
