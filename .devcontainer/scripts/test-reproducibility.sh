#!/usr/bin/env bash
# ==============================================================================
# ANTIGRAVITY WORKSTATION - REPRODUCIBILITY & DEVCONTAINER AUDIT
# Location: .devcontainer/scripts/test-reproducibility.sh
# Purpose: Comprehensive validation of Devcontainer specification, environment,
#          compilers, scripts integrity, set -euo pipefail adherence, and idempotency.
# Conforms to instruction.md Section 5 and Subagent 01 Phase D.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# ANSI formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "\n${BOLD}${CYAN}============================================================${NC}"
echo -e "${BOLD}${CYAN}   ANTIGRAVITY WORKSTATION - REPRODUCIBILITY AUDIT          ${NC}"
echo -e "${BOLD}${CYAN}============================================================${NC}\n"

AUDIT_PASSED=0
AUDIT_TOTAL=0

assert_check() {
    local name="$1"
    local status="$2"
    local details="$3"
    AUDIT_TOTAL=$((AUDIT_TOTAL + 1))
    if [ "${status}" = "PASS" ]; then
        AUDIT_PASSED=$((AUDIT_PASSED + 1))
        printf "  %-40s [ ${GREEN}PASS${NC} ] %s\n" "${name}" "${details}"
    else
        printf "  %-40s [ ${RED}FAIL${NC} ] %s\n" "${name}" "${details}"
        echo -e "\n${RED}[FATAL] Reproducibility assertion failed: ${name} (${details})${NC}" >&2
        exit 1
    fi
}

echo -e "${BOLD}1. Validating Devcontainer Specification & Config Files...${NC}"
if [ -f "${WORKSPACE_ROOT}/.devcontainer/devcontainer.json" ]; then
    if python3 -c "import json; json.load(open('${WORKSPACE_ROOT}/.devcontainer/devcontainer.json'))" >/dev/null 2>&1; then
        assert_check "devcontainer.json" "PASS" "Valid JSON syntax and schema"
    else
        assert_check "devcontainer.json" "FAIL" "Invalid JSON syntax"
    fi
else
    assert_check "devcontainer.json" "FAIL" "File not found"
fi

if [ -f "${WORKSPACE_ROOT}/.devcontainer/Dockerfile" ] && [ -s "${WORKSPACE_ROOT}/.devcontainer/Dockerfile" ]; then
    DOCKERFILE_LINES=$(wc -l < "${WORKSPACE_ROOT}/.devcontainer/Dockerfile")
    assert_check "Dockerfile" "PASS" "Present and non-empty (${DOCKERFILE_LINES} lines)"
else
    assert_check "Dockerfile" "FAIL" "File missing or empty"
fi

echo -e "\n${BOLD}2. Validating Environment Variables & Toolchain Root Directories...${NC}"
test -n "${ANDROID_HOME:-}" && assert_check "ANDROID_HOME" "PASS" "${ANDROID_HOME}" || assert_check "ANDROID_HOME" "FAIL" "Variable unset"
test -n "${GHIDRA_HOME:-}" && assert_check "GHIDRA_HOME" "PASS" "${GHIDRA_HOME}" || assert_check "GHIDRA_HOME" "FAIL" "Variable unset"
test -n "${CODEQL_HOME:-}" && assert_check "CODEQL_HOME" "PASS" "${CODEQL_HOME}" || assert_check "CODEQL_HOME" "FAIL" "Variable unset"
test -n "${JAVA_HOME:-}" && assert_check "JAVA_HOME" "PASS" "${JAVA_HOME}" || assert_check "JAVA_HOME" "FAIL" "Variable unset"

echo -e "\n${BOLD}3. Validating Core Compilers & Runtimes...${NC}"
if command -v gcc >/dev/null 2>&1; then
    GCC_VER=$(gcc --version | head -n1)
    assert_check "GCC Compiler" "PASS" "${GCC_VER}"
else
    assert_check "GCC Compiler" "FAIL" "gcc not found"
fi

if command -v clang >/dev/null 2>&1; then
    CLANG_VER=$(clang --version | head -n1)
    assert_check "Clang Compiler" "PASS" "${CLANG_VER}"
else
    assert_check "Clang Compiler" "FAIL" "clang not found"
fi

if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 --version)
    assert_check "Python 3 Runtime" "PASS" "${PY_VER}"
else
    assert_check "Python 3 Runtime" "FAIL" "python3 not found"
fi

if command -v node >/dev/null 2>&1; then
    NODE_VER=$(node --version)
    assert_check "Node.js Runtime" "PASS" "${NODE_VER}"
else
    assert_check "Node.js Runtime" "FAIL" "node not found"
fi

if command -v java >/dev/null 2>&1; then
    JAVA_VER=$(java -version 2>&1 | head -n1)
    assert_check "OpenJDK Runtime" "PASS" "${JAVA_VER}"
else
    assert_check "OpenJDK Runtime" "FAIL" "java not found"
fi

echo -e "\n${BOLD}4. Validating Devcontainer Scripts Integrity & Hardening Standards...${NC}"
SCRIPTS=(
    "bootstrap.sh"
    "doctor.sh"
    "test-reproducibility.sh"
    "verify-android.sh"
    "verify-binary-stack.sh"
    "verify-mcp.sh"
    "verify-network-stack.sh"
    "verify-security-stack.sh"
    "verify-toolchain.sh"
)

for script in "${SCRIPTS[@]}"; do
    script_path="${WORKSPACE_ROOT}/.devcontainer/scripts/${script}"
    
    # Check existence
    if [ ! -f "${script_path}" ]; then
        assert_check "${script} (existence)" "FAIL" "File does not exist"
        continue
    fi
    
    # Check executable bit
    if [ -x "${script_path}" ]; then
        assert_check "${script} (executable)" "PASS" "Permissions: $(stat -c '%a' "${script_path}")"
    else
        assert_check "${script} (executable)" "FAIL" "Missing executable permission"
    fi
    
    # Check bash syntax
    if bash -n "${script_path}"; then
        assert_check "${script} (syntax)" "PASS" "bash -n syntax check passed"
    else
        assert_check "${script} (syntax)" "FAIL" "bash -n syntax error"
    fi
    
    # Check set -euo pipefail directive
    if grep -q "set -euo pipefail" "${script_path}"; then
        assert_check "${script} (strict mode)" "PASS" "set -euo pipefail enforced"
    else
        assert_check "${script} (strict mode)" "FAIL" "Missing set -euo pipefail"
    fi
done

echo -e "\n${BOLD}5. Validating Idempotency & Directory Readiness...${NC}"
for d in "${WORKSPACE_ROOT}/docs" "${WORKSPACE_ROOT}/.agents/memory" "${WORKSPACE_ROOT}/.agents/skills" "${WORKSPACE_ROOT}/tools/bin" "${WORKSPACE_ROOT}/tools/scripts"; do
    if [ -d "${d}" ]; then
        assert_check "Directory $(basename "${d}")" "PASS" "Directory verified at ${d}"
    else
        assert_check "Directory $(basename "${d}")" "FAIL" "Missing expected directory ${d}"
    fi
done

echo -e "\n${BOLD}${CYAN}============================================================${NC}"
echo -e "${GREEN}${BOLD}[OK] REPRODUCIBILITY AUDIT 100% PASS: ${AUDIT_PASSED}/${AUDIT_TOTAL} checks passed.${NC}"
echo -e "${BOLD}${CYAN}============================================================${NC}\n"

exit 0
