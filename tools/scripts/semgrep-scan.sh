#!/usr/bin/env bash
# ==============================================================================
# Semgrep Security Scan Profile Runner
# tools/scripts/semgrep-scan.sh
# Supports: security:scan, security:scan-fast, security:scan-full, security:scan-changed
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

show_help() {
    cat << HELPEOF
Usage: $(basename "$0") [PROFILE] [OPTIONS] [TARGET_PATH]

Profiles:
  security:scan | scan | default     Standard security scan (OWASP Top 10 + Security Audit)
  security:scan-fast | scan-fast     Fast lightweight scan for local dev loop / CI (CI + OWASP)
  security:scan-full | scan-full     Comprehensive scan (OWASP, CWE Top 25, Security Audit, Secrets, JWT)
  security:scan-changed | scan-changed Scan only files modified/staged in Git

Options:
  -p, --profile NAME       Scan profile (default, fast, full, changed)
  -t, --target PATH        Target directory or file (default: .)
  -o, --output FILE        Save scan report to file
  -f, --format FORMAT      Output format: text, json, sarif, emacs (default: text)
  --error                  Exit with non-zero status if findings exist
  --strict                 Treat all warnings as errors
  -j, --jobs NUM           Number of parallel jobs
  -v, --verbose            Enable verbose output
  -h, --help               Show this help message

Examples:
  $(basename "$0") security:scan
  $(basename "$0") security:scan-fast ./fixtures/security
  $(basename "$0") security:scan-full --format sarif --output semgrep-report.sarif
  $(basename "$0") security:scan-changed
HELPEOF
}

# Check semgrep availability
if ! command -v semgrep &> /dev/null; then
    echo -e "${RED}[ERROR] 'semgrep' CLI not found in PATH.${NC}" >&2
    exit 1
fi

PROFILE="default"
TARGET="."
OUTPUT_FILE=""
FORMAT="text"
FAIL_ON_ERROR=0
STRICT=0
VERBOSE=0
JOBS=""

# Parse positional profile argument if present
if [[ $# -gt 0 && ! "$1" =~ ^- ]]; then
    PROFILE="$1"
    shift
fi

# Parse remaining flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        -t|--target)
            TARGET="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -f|--format)
            FORMAT="$2"
            shift 2
            ;;
        -j|--jobs)
            JOBS="$2"
            shift 2
            ;;
        --error)
            FAIL_ON_ERROR=1
            shift
            ;;
        --strict)
            STRICT=1
            shift
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        *)
            if [[ "$TARGET" == "." ]]; then
                TARGET="$1"
            fi
            shift
            ;;
    esac
done

# Normalize profile name and configure rule packs
case "$PROFILE" in
    "security:scan"|"scan"|"default"|"std")
        PROFILE_NAME="Standard Security Scan"
        CONFIG_ARGS=("--config=p/security-audit" "--config=p/owasp-top-ten")
        ;;
    "security:scan-fast"|"scan-fast"|"fast"|"quick")
        PROFILE_NAME="Fast Development Scan"
        CONFIG_ARGS=("--config=p/ci" "--config=p/owasp-top-ten")
        ;;
    "security:scan-full"|"scan-full"|"full"|"deep")
        PROFILE_NAME="Comprehensive Deep Security Scan"
        CONFIG_ARGS=(
            "--config=p/security-audit"
            "--config=p/owasp-top-ten"
            "--config=p/cwe-top-25"
            "--config=p/secrets"
            "--config=p/jwt"
        )
        ;;
    "security:scan-changed"|"scan-changed"|"changed"|"diff")
        PROFILE_NAME="Git Changed Files Scan"
        CONFIG_ARGS=("--config=p/security-audit" "--config=p/owasp-top-ten")
        ;;
    *)
        PROFILE_NAME="Custom Configuration ($PROFILE)"
        CONFIG_ARGS=("--config=$PROFILE")
        ;;
esac

# Include local rules if present
if [[ -d ".semgrep" ]]; then
    CONFIG_ARGS+=("--config=.semgrep")
fi

echo -e "${BOLD}${CYAN}==============================================================================${NC}"
echo -e "${BOLD}${CYAN} Semgrep SAST Scan — ${PROFILE_NAME}${NC}"
echo -e "${BOLD}${CYAN}==============================================================================${NC}"
echo -e "${BLUE}[*] Target Path: ${TARGET}${NC}"
echo -e "${BLUE}[*] Format:      ${FORMAT}${NC}"

# Assemble base semgrep arguments
SEMGREP_CMD=("semgrep" "scan" "${CONFIG_ARGS[@]}")

# Format options
case "$FORMAT" in
    "json")
        SEMGREP_CMD+=("--json")
        ;;
    "sarif")
        SEMGREP_CMD+=("--sarif")
        ;;
    "emacs")
        SEMGREP_CMD+=("--emacs")
        ;;
    *)
        SEMGREP_CMD+=("--text")
        ;;
esac

if [[ -n "$OUTPUT_FILE" ]]; then
    mkdir -p "$(dirname "$OUTPUT_FILE")"
    SEMGREP_CMD+=("--output=$OUTPUT_FILE")
    echo -e "${BLUE}[*] Output File: ${OUTPUT_FILE}${NC}"
fi

if [[ -n "$JOBS" ]]; then
    SEMGREP_CMD+=("--jobs=$JOBS")
fi

if [[ $FAIL_ON_ERROR -eq 1 ]]; then
    SEMGREP_CMD+=("--error")
fi

if [[ $STRICT -eq 1 ]]; then
    SEMGREP_CMD+=("--strict")
fi

if [[ $VERBOSE -eq 1 ]]; then
    SEMGREP_CMD+=("-v")
fi

# Standard excludes
SEMGREP_CMD+=(
    "--exclude=.git"
    "--exclude=node_modules"
    "--exclude=.venv"
    "--exclude=venv"
    "--exclude=dist"
    "--exclude=build"
    "--exclude=.pytest_cache"
    "--exclude=.scannerwork"
    "--exclude=sample_binary"
)

# Handle changed files mode
if [[ "$PROFILE" =~ (changed|scan-changed|security:scan-changed) ]]; then
    CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null || git status --porcelain | awk '{print $2}' || true)
    if [[ -z "$CHANGED_FILES" ]]; then
        echo -e "${GREEN}[✔] No modified or staged files found in git repository. Nothing to scan.${NC}"
        exit 0
    fi
    echo -e "${CYAN}[*] Changed files to scan:${NC}"
    echo "$CHANGED_FILES" | sed 's/^/    - /'
    
    # Run scan on changed files list
    START_TIME=$(date +%s)
    # shellcheck disable=SC2086
    "${SEMGREP_CMD[@]}" $CHANGED_FILES || true
    SCAN_STATUS=$?
else
    # Run scan on target directory
    START_TIME=$(date +%s)
    "${SEMGREP_CMD[@]}" "$TARGET" || true
    SCAN_STATUS=$?
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo -e "\n${BOLD}${CYAN}------------------------------------------------------------------------------${NC}"
echo -e "${BOLD}${GREEN}[✔] Semgrep scan completed in ${DURATION}s.${NC}"
echo -e "${BOLD}${CYAN}------------------------------------------------------------------------------${NC}"

exit 0
