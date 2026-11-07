#!/usr/bin/env bash
# ==============================================================================
# CodeQL Verification Script
# tools/scripts/codeql-verify.sh
# End-to-end verification of CodeQL CLI toolchain, database creation, and query execution
# ==============================================================================

set -euo pipefail

# ANSI color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CREATE_DB_SCRIPT="${SCRIPT_DIR}/codeql-create-db.sh"
ANALYZE_SCRIPT="${SCRIPT_DIR}/codeql-analyze.sh"

echo -e "${BOLD}${BLUE}==============================================================================${NC}"
echo -e "${BOLD}${BLUE}                 CodeQL CLI Verification & Diagnostic Test                    ${NC}"
echo -e "${BOLD}${BLUE}==============================================================================${NC}"

# 1. Verify CodeQL Binary
echo -e "\n${BLUE}[1/5] Checking CodeQL CLI executable...${NC}"
if ! command -v codeql &> /dev/null; then
    echo -e "${RED}[FAIL] 'codeql' command not found in PATH.${NC}"
    exit 1
fi
CODEQL_PATH=$(command -v codeql)
CODEQL_VER=$(codeql version 2>&1 | head -n 1)
echo -e "${GREEN}[✔] CodeQL binary: ${CODEQL_PATH}${NC}"
echo -e "${GREEN}[✔] CodeQL version: ${CODEQL_VER}${NC}"

# 2. Check Supported Languages
echo -e "\n${BLUE}[2/5] Checking available CodeQL extractors/languages...${NC}"
LANGS=$(codeql resolve languages 2>/dev/null | awk '{print $1}' | tr '\n' ' ' || true)
echo -e "${GREEN}[✔] Available languages: ${LANGS}${NC}"
for req_lang in python javascript cpp java; do
    if [[ " $LANGS " =~ " $req_lang " ]]; then
        echo -e "    - ${req_lang}: ${GREEN}AVAILABLE${NC}"
    else
        echo -e "    - ${req_lang}: ${YELLOW}MISSING${NC}"
    fi
done

# 3. Check Query Packs
echo -e "\n${BLUE}[3/5] Resolving CodeQL Query Packs...${NC}"
PACKS_COUNT=$(codeql resolve qlpacks 2>/dev/null | grep -c "codeql/" || true)
echo -e "${GREEN}[✔] Found ${PACKS_COUNT} CodeQL query pack references.${NC}"

# 4. Create Minimal Test Fixture & CodeQL Database
TEST_DIR=$(mktemp -d -t codeql-test-XXXXXX)
trap 'rm -rf "$TEST_DIR"' EXIT

echo -e "\n${BLUE}[4/5] Creating temporary Python test fixture and CodeQL database in ${TEST_DIR}...${NC}"

# Create a sample Python script with deliberate SQL injection and command injection
cat << 'PYEOF' > "${TEST_DIR}/vulnerable_app.py"
import os
import sqlite3

def get_user_data(username):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Insecure string formatting leading to SQL injection
    query = "SELECT * FROM users WHERE username = '%s'" % username
    cursor.execute(query)
    return cursor.fetchall()

def execute_system_action(cmd_input):
    # Insecure system command execution
    os.system("echo Processing: " + cmd_input)

if __name__ == "__main__":
    get_user_data("admin' OR '1'='1")
    execute_system_action("; ls -la")
PYEOF

DB_OUTPUT="${TEST_DIR}/test_db"
SARIF_OUTPUT="${TEST_DIR}/test_results.sarif"

if [[ -f "$CREATE_DB_SCRIPT" ]]; then
    bash "$CREATE_DB_SCRIPT" --db "$DB_OUTPUT" --source "$TEST_DIR" --language python --overwrite
else
    codeql database create "$DB_OUTPUT" --source-root="$TEST_DIR" --language=python --overwrite
fi

if [[ ! -d "$DB_OUTPUT" ]]; then
    echo -e "${RED}[FAIL] Database directory was not created: ${DB_OUTPUT}${NC}"
    exit 1
fi
echo -e "${GREEN}[✔] Test database successfully built at ${DB_OUTPUT}${NC}"

# 5. Run CodeQL Analysis on Test Fixture
echo -e "\n${BLUE}[5/5] Executing CodeQL analysis on test fixture...${NC}"
if [[ -f "$ANALYZE_SCRIPT" ]]; then
    bash "$ANALYZE_SCRIPT" --db "$DB_OUTPUT" --output "$SARIF_OUTPUT" --format sarif-latest --suite "python-security-extended.qls"
else
    codeql database analyze "$DB_OUTPUT" "python-security-extended.qls" --format=sarif-latest --output="$SARIF_OUTPUT" --threads=0
fi

if [[ ! -f "$SARIF_OUTPUT" ]]; then
    echo -e "${RED}[FAIL] SARIF results file was not created: ${SARIF_OUTPUT}${NC}"
    exit 1
fi

RESULTS_COUNT=0
if command -v jq &> /dev/null; then
    RESULTS_COUNT=$(jq '[.runs[].results[]?] | length' "$SARIF_OUTPUT" 2>/dev/null || echo "0")
fi

echo -e "${GREEN}[✔] CodeQL SARIF report generated successfully (${RESULTS_COUNT} alerts).${NC}"

echo -e "\n${BOLD}${GREEN}==============================================================================${NC}"
echo -e "${BOLD}${GREEN}                     CodeQL Verification Succeeded!                          ${NC}"
echo -e "${BOLD}${GREEN}==============================================================================${NC}"
exit 0
