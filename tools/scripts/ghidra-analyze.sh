#!/usr/bin/env bash
# ==============================================================================
# ghidra-analyze.sh — Automated Ghidra Headless Binary Analysis & Decompilation
#
# Part of Antigravity Engineering Workstation Toolchain (Section 12)
#
# Usage:
#   ghidra-analyze.sh [options] <binary_path>
#
# Exit Codes:
#   0 - Success (analysis completed, outputs generated)
#   1 - Invalid arguments / target binary not found
#   2 - Environment / dependency error (Java or Ghidra missing)
#   3 - Ghidra Headless Analyzer execution error
# ==============================================================================

set -euo pipefail

# ------------------------------------------------------------------------------
# Colors and Styling
# ------------------------------------------------------------------------------
BOLD="\033[1m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
BLUE="\033[1;34m"
CYAN="\033[1;36m"
NC="\033[0m"

log_info()  { echo -e "${BLUE}[*]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[+]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
log_error() { echo -e "${RED}[-]${NC} $*" >&2; }

# ------------------------------------------------------------------------------
# Configuration & Defaults
# ------------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GHIDRA_SCRIPTS_DIR="${SCRIPT_DIR}/ghidra_scripts"
GHIDRA_HOME="${GHIDRA_HOME:-/usr/local/ghidra}"

# Ensure Java 21+ is available if sdkman is installed
if [ -d "/usr/local/sdkman/candidates/java/21.0.10-ms" ]; then
    export JAVA_HOME="/usr/local/sdkman/candidates/java/21.0.10-ms"
    export PATH="${JAVA_HOME}/bin:${PATH}"
elif [ -d "/usr/local/sdkman/candidates/java/current" ]; then
    export JAVA_HOME="/usr/local/sdkman/candidates/java/current"
    export PATH="${JAVA_HOME}/bin:${PATH}"
fi

TARGET_BIN=""
OUTPUT_DIR=""
PROJECT_DIR=""
PROJECT_NAME=""
KEEP_PROJECT=false
POST_SCRIPT="DecompileAndSummarize.java"
EXTRA_SCRIPTS=()
MAX_CPU=""
TIMEOUT=""
VERBOSE=false
LOG_FILE=""

# ------------------------------------------------------------------------------
# Help / Usage
# ------------------------------------------------------------------------------
show_help() {
    echo -e "${BOLD}Ghidra Headless Binary Analyzer${NC}"
    echo ""
    echo -e "${BOLD}USAGE:${NC}"
    echo -e "    ghidra-analyze.sh [OPTIONS] <binary_path>"
    echo ""
    echo -e "${BOLD}DESCRIPTION:${NC}"
    echo -e "    Automates headless static analysis and decompiler extraction for native binaries"
    echo -e "    (ELF, PE, Mach-O, Raw, etc.) using Ghidra 11.x headless analyzer."
    echo ""
    echo -e "${BOLD}OPTIONS:${NC}"
    echo -e "    -o, --output-dir <DIR>      Directory to store decompiled C code and summary"
    echo -e "                                (default: ./ghidra_output_<binary_basename>)"
    echo -e "    -p, --project-dir <DIR>     Directory for Ghidra project database"
    echo -e "                                (default: temporary directory in /tmp)"
    echo -e "    -n, --project-name <NAME>   Project name (default: GhidraProj_<basename>)"
    echo -e "    -k, --keep-project          Retain the Ghidra project directory after analysis"
    echo -e "    -s, --script <SCRIPT>       Specify custom Ghidra post-script"
    echo -e "    -c, --max-cpu <CORES>       Limit maximum CPU cores for analysis"
    echo -e "    -t, --timeout <SECONDS>     Timeout in seconds for analysis per binary"
    echo -e "    -v, --verbose               Enable verbose analyzeHeadless standard output"
    echo -e "    -h, --help                  Show this help message and exit"
    echo ""
    echo -e "${BOLD}EXIT CODES:${NC}"
    echo -e "    0   Success"
    echo -e "    1   Invalid arguments / Target not found"
    echo -e "    2   Missing Java 21+ or Ghidra installation"
    echo -e "    3   Ghidra analysis execution failure"
    echo ""
    echo -e "${BOLD}EXAMPLES:${NC}"
    echo -e "    # Analyze an ELF binary and decompile all functions to ./ghidra_output_sample/"
    echo -e "    ghidra-analyze.sh /path/to/binary"
    echo ""
    echo -e "    # Specify custom output directory and persist Ghidra project for later inspection"
    echo -e "    ghidra-analyze.sh -o ./analysis_results -p ./ghidra_db -k /path/to/binary"
}

# ------------------------------------------------------------------------------
# Argument Parsing
# ------------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -p|--project-dir)
            PROJECT_DIR="$2"
            shift 2
            ;;
        -n|--project-name)
            PROJECT_NAME="$2"
            shift 2
            ;;
        -k|--keep-project)
            KEEP_PROJECT=true
            shift
            ;;
        -s|--script)
            POST_SCRIPT="$2"
            shift 2
            ;;
        -c|--max-cpu)
            MAX_CPU="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -*)
            log_error "Unknown option: $1"
            echo "Run 'ghidra-analyze.sh --help' for usage."
            exit 1
            ;;
        *)
            if [ -z "$TARGET_BIN" ]; then
                TARGET_BIN="$1"
            else
                log_error "Multiple target binaries specified: '$TARGET_BIN' and '$1'"
                exit 1
            fi
            shift
            ;;
    esac
done

# ------------------------------------------------------------------------------
# Pre-Flight Validation
# ------------------------------------------------------------------------------
if [ -z "$TARGET_BIN" ]; then
    log_error "Missing required target binary argument."
    echo "Usage: ghidra-analyze.sh [OPTIONS] <binary_path>"
    exit 1
fi

if [ ! -f "$TARGET_BIN" ]; then
    log_error "Target binary not found: $TARGET_BIN"
    exit 1
fi

# Resolve absolute path for target binary
TARGET_BIN="$(cd "$(dirname "$TARGET_BIN")" && pwd)/$(basename "$TARGET_BIN")"
BIN_BASENAME="$(basename "$TARGET_BIN")"

# Check Java Runtime
if ! command -v java >/dev/null 2>&1; then
    log_error "Java runtime not found on PATH. OpenJDK 21+ is required for Ghidra 11.x."
    exit 2
fi

JAVA_VERSION_OUTPUT="$(java -version 2>&1 | head -n 1)"
log_info "Java Runtime: ${JAVA_VERSION_OUTPUT}"

# Check Ghidra Installation
if [ ! -d "$GHIDRA_HOME" ] || [ ! -x "${GHIDRA_HOME}/support/analyzeHeadless" ]; then
    log_error "Ghidra headless analyzer not found at: ${GHIDRA_HOME}/support/analyzeHeadless"
    log_error "Please install Ghidra or set GHIDRA_HOME environment variable."
    exit 2
fi

HEADLESS_ANALYZER="${GHIDRA_HOME}/support/analyzeHeadless"

# ------------------------------------------------------------------------------
# Project & Output Directory Setup
# ------------------------------------------------------------------------------
if [ -z "$OUTPUT_DIR" ]; then
    OUTPUT_DIR="$(pwd)/ghidra_output_${BIN_BASENAME}"
fi
mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"
LOG_FILE="${OUTPUT_DIR}/ghidra_analysis.log"

IS_TEMP_PROJ=false
if [ -z "$PROJECT_DIR" ]; then
    PROJECT_DIR="$(mktemp -d -t ghidra_proj_XXXXXX)"
    IS_TEMP_PROJ=true
else
    mkdir -p "$PROJECT_DIR"
    PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"
fi

if [ -z "$PROJECT_NAME" ]; then
    PROJECT_NAME="GhidraProj_${BIN_BASENAME}"
fi

# Cleanup handler
cleanup() {
    local exit_code=$?
    if [ "$IS_TEMP_PROJ" = true ] && [ "$KEEP_PROJECT" = false ]; then
        if [ -d "$PROJECT_DIR" ]; then
            rm -rf "$PROJECT_DIR" 2>/dev/null || true
        fi
    fi
    exit $exit_code
}
trap cleanup EXIT INT TERM

# ------------------------------------------------------------------------------
# Ghidra Execution
# ------------------------------------------------------------------------------
echo -e "${BOLD}${CYAN}======================================================${NC}"
echo -e "${BOLD}${CYAN}   Ghidra 11.x Headless Analysis Pipeline             ${NC}"
echo -e "${BOLD}${CYAN}======================================================${NC}"
log_info "Target Binary:     ${BOLD}${TARGET_BIN}${NC}"
log_info "Ghidra Home:       ${GHIDRA_HOME}"
log_info "Project Directory: ${PROJECT_DIR}"
log_info "Project Name:      ${PROJECT_NAME}"
log_info "Output Directory:  ${OUTPUT_DIR}"
log_info "Log File:          ${LOG_FILE}"

CMD_ARGS=(
    "$PROJECT_DIR"
    "$PROJECT_NAME"
    "-import" "$TARGET_BIN"
    "-overwrite"
    "-scriptPath" "${GHIDRA_SCRIPTS_DIR};${GHIDRA_HOME}/Ghidra/Features/Base/ghidra_scripts"
)

if [ "$KEEP_PROJECT" = false ] && [ "$IS_TEMP_PROJ" = true ]; then
    CMD_ARGS+=("-deleteProject")
fi

if [ -n "$MAX_CPU" ]; then
    CMD_ARGS+=("-max-cpu" "$MAX_CPU")
fi

if [ -n "$TIMEOUT" ]; then
    CMD_ARGS+=("-analysisTimeoutPerFile" "$TIMEOUT")
fi

if [ -n "$POST_SCRIPT" ]; then
    CMD_ARGS+=("-postScript" "$POST_SCRIPT" "$OUTPUT_DIR")
fi

log_info "Executing analyzeHeadless..."
START_TIME="$(date +%s)"

if [ "$VERBOSE" = true ]; then
    set +e
    "$HEADLESS_ANALYZER" "${CMD_ARGS[@]}" 2>&1 | tee "$LOG_FILE"
    ANALYSIS_EXIT_CODE=$?
    set -e
else
    set +e
    "$HEADLESS_ANALYZER" "${CMD_ARGS[@]}" > "$LOG_FILE" 2>&1
    ANALYSIS_EXIT_CODE=$?
    set -e
fi

END_TIME="$(date +%s)"
DURATION=$((END_TIME - START_TIME))

if [ $ANALYSIS_EXIT_CODE -ne 0 ]; then
    log_error "Ghidra headless analysis failed with exit code: ${ANALYSIS_EXIT_CODE}"
    log_error "See log file for details: ${LOG_FILE}"
    exit 3
fi

# ------------------------------------------------------------------------------
# Output Summary & Verification
# ------------------------------------------------------------------------------
SUMMARY_FILE="${OUTPUT_DIR}/${BIN_BASENAME}.summary.txt"
DECOMPILED_FILE="${OUTPUT_DIR}/${BIN_BASENAME}.decompiled.c"

echo ""
echo -e "${BOLD}${GREEN}======================================================${NC}"
echo -e "${BOLD}${GREEN}   Analysis Completed Successfully in ${DURATION}s           ${NC}"
echo -e "${BOLD}${GREEN}======================================================${NC}"

if [ -f "$SUMMARY_FILE" ]; then
    log_ok "Decompiled Summary: ${SUMMARY_FILE}"
    # Print key sections of the summary
    grep -E "Language:|Format:|Total Functions:|Successfully Decompiled:|Failed:" "$SUMMARY_FILE" | while read -r line; do
        echo -e "  ${CYAN}•${NC} $line"
    done
else
    log_warn "Summary file not created (custom postscript may not have written standard summary)."
fi

if [ -f "$DECOMPILED_FILE" ]; then
    DECOMP_LINES="$(wc -l < "$DECOMPILED_FILE")"
    log_ok "Decompiled C Code:  ${DECOMPILED_FILE} (${DECOMP_LINES} lines)"
fi

log_ok "Full Analysis Log:  ${LOG_FILE}"

if [ "$KEEP_PROJECT" = true ]; then
    log_info "Ghidra Project DB:  ${PROJECT_DIR}/${PROJECT_NAME}.gpr"
fi

exit 0
