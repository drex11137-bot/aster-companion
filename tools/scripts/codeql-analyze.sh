#!/usr/bin/env bash
# ==============================================================================
# CodeQL Database Analysis Helper Script
# tools/scripts/codeql-analyze.sh
# Analyzes a CodeQL database with security query suites and generates SARIF/CSV reports
# ==============================================================================

set -euo pipefail

# ANSI color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

show_help() {
    cat << HELPEOF
Usage: $(basename "$0") [OPTIONS] <database-path> [output-file] [output-format] [query-suite]

Arguments:
  <database-path>         Path to the CodeQL database directory.
  [output-file]           Path to save the analysis results (default: <db-name>-results.sarif).
  [output-format]         Format: sarif-latest, csv, json (default: sarif-latest).
  [query-suite]           Query suite, QL pack, or .ql file to execute (e.g. "python-security-extended.qls").

Options:
  -d, --db DIR            CodeQL database directory.
  -o, --output FILE       Output file destination.
  -f, --format FORMAT     Output format (sarif-latest, csv, json). Default: sarif-latest.
  -q, --suite SUITE       Query suite / pack (e.g. "python-security-extended.qls", "cpp-security-extended.qls").
  -t, --threads NUM       Number of threads to use (default: 0 = all cores).
  -m, --ram MB            Maximum RAM to use in MB (default: auto).
  -v, --verbose           Enable verbose output.
  -h, --help              Show this help message.

Examples:
  $(basename "$0") /tmp/codeql-py-db ./results.sarif
  $(basename "$0") --db /tmp/cpp-db --format csv --output ./cpp-findings.csv
  $(basename "$0") /tmp/codeql-py-db ./py-results.sarif sarif-latest python-security-extended.qls
HELPEOF
}

# Defaults
DB_PATH=""
OUTPUT_FILE=""
OUTPUT_FORMAT="sarif-latest"
QUERY_SUITE=""
THREADS="0"
RAM=""
VERBOSE=0

# Parse options
POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--db)
            DB_PATH="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -f|--format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -q|--suite)
            QUERY_SUITE="$2"
            shift 2
            ;;
        -t|--threads)
            THREADS="$2"
            shift 2
            ;;
        -m|--ram)
            RAM="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        *)
            POSITIONAL_ARGS+=("$1")
            shift
            ;;
    esac
done

# Map positional arguments
if [[ -z "$DB_PATH" && ${#POSITIONAL_ARGS[@]} -gt 0 ]]; then
    DB_PATH="${POSITIONAL_ARGS[0]}"
fi
if [[ -z "$OUTPUT_FILE" && ${#POSITIONAL_ARGS[@]} -gt 1 ]]; then
    OUTPUT_FILE="${POSITIONAL_ARGS[1]}"
fi
if [[ "$OUTPUT_FORMAT" == "sarif-latest" && ${#POSITIONAL_ARGS[@]} -gt 2 ]]; then
    OUTPUT_FORMAT="${POSITIONAL_ARGS[2]}"
fi
if [[ -z "$QUERY_SUITE" && ${#POSITIONAL_ARGS[@]} -gt 3 ]]; then
    QUERY_SUITE="${POSITIONAL_ARGS[3]}"
fi

# Validation
if [[ -z "$DB_PATH" ]]; then
    echo -e "${RED}[ERROR] Database path is required.${NC}" >&2
    show_help
    exit 1
fi

if [[ ! -d "$DB_PATH" ]]; then
    echo -e "${RED}[ERROR] Database directory does not exist: $DB_PATH${NC}" >&2
    exit 1
fi

# Verify codeql CLI availability
if ! command -v codeql &> /dev/null; then
    echo -e "${RED}[ERROR] 'codeql' CLI not found in PATH.${NC}" >&2
    exit 1
fi

# Determine Language from Database Metadata
LANGUAGE=""
if [[ -f "$DB_PATH/codeql-database.yml" ]]; then
    LANGUAGE=$(grep -E "^primaryLanguage:" "$DB_PATH/codeql-database.yml" | head -n 1 | awk '{print $2}' | tr -d '"' | tr -d "'" || true)
fi

if [[ -z "$LANGUAGE" ]]; then
    if [[ -d "$DB_PATH/db-python" ]]; then
        LANGUAGE="python"
    elif [[ -d "$DB_PATH/db-javascript" ]]; then
        LANGUAGE="javascript"
    elif [[ -d "$DB_PATH/db-cpp" ]]; then
        LANGUAGE="cpp"
    elif [[ -d "$DB_PATH/db-java" ]]; then
        LANGUAGE="java"
    elif [[ -d "$DB_PATH/db-go" ]]; then
        LANGUAGE="go"
    elif [[ -d "$DB_PATH/db-ruby" ]]; then
        LANGUAGE="ruby"
    elif [[ -d "$DB_PATH/db-rust" ]]; then
        LANGUAGE="rust"
    elif [[ -d "$DB_PATH/db-csharp" ]]; then
        LANGUAGE="csharp"
    elif [[ -d "$DB_PATH/db-swift" ]]; then
        LANGUAGE="swift"
    fi
fi

# Default Output File if not provided
if [[ -z "$OUTPUT_FILE" ]]; then
    DB_NAME=$(basename "$DB_PATH")
    EXT="sarif"
    if [[ "$OUTPUT_FORMAT" == "csv" ]]; then
        EXT="csv"
    elif [[ "$OUTPUT_FORMAT" == "json" ]]; then
        EXT="json"
    fi
    OUTPUT_FILE="${DB_NAME}-results.${EXT}"
fi

# Default Query Suite if not provided
if [[ -z "$QUERY_SUITE" ]]; then
    if [[ -n "$LANGUAGE" ]]; then
        QUERY_SUITE="${LANGUAGE}-security-extended.qls"
    else
        QUERY_SUITE="code-scanning.qls"
    fi
fi

# Ensure parent directory of output file exists
OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
mkdir -p "$OUTPUT_DIR"

# Build analysis command
CMD=("codeql" "database" "analyze" "$DB_PATH" "$QUERY_SUITE" "--format=$OUTPUT_FORMAT" "--output=$OUTPUT_FILE" "--threads=$THREADS")

if [[ -n "$RAM" ]]; then
    CMD+=("--ram=$RAM")
fi

if [[ $VERBOSE -eq 1 ]]; then
    CMD+=("-v")
fi

echo -e "${BLUE}[*] Executing CodeQL Database Analysis:${NC}"
echo -e "    Database:    ${DB_PATH}"
echo -e "    Language:    ${LANGUAGE:-unknown}"
echo -e "    Query Suite: ${QUERY_SUITE}"
echo -e "    Format:      ${OUTPUT_FORMAT}"
echo -e "    Output:      ${OUTPUT_FILE}"
echo -e "    Threads:     ${THREADS}"

START_TIME=$(date +%s)

# Execute CodeQL analysis
if ! "${CMD[@]}"; then
    if [[ "$QUERY_SUITE" == *"-security-extended.qls" ]]; then
        FALLBACK_SUITE="${LANGUAGE}-code-scanning.qls"
        echo -e "${YELLOW}[!] Retrying with fallback suite: ${FALLBACK_SUITE}...${NC}"
        CMD=("codeql" "database" "analyze" "$DB_PATH" "$FALLBACK_SUITE" "--format=$OUTPUT_FORMAT" "--output=$OUTPUT_FILE" "--threads=$THREADS")
        "${CMD[@]}"
    else
        echo -e "${RED}[ERROR] CodeQL analysis failed.${NC}" >&2
        exit 1
    fi
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo -e "${GREEN}[✔] CodeQL analysis completed successfully in ${DURATION}s.${NC}"
echo -e "${GREEN}[✔] Results written to: ${OUTPUT_FILE}${NC}"

# Summarize findings if SARIF or CSV
if [[ -f "$OUTPUT_FILE" ]]; then
    if [[ "$OUTPUT_FORMAT" == *"sarif"* ]]; then
        if command -v jq &> /dev/null; then
            FINDINGS_COUNT=$(jq '[.runs[].results[]?] | length' "$OUTPUT_FILE" 2>/dev/null || echo "0")
            echo -e "${CYAN}[*] Summary: Found ${FINDINGS_COUNT} total security alert(s).${NC}"
            if [[ "$FINDINGS_COUNT" -gt 0 ]]; then
                echo -e "${YELLOW}[!] Top Findings:${NC}"
                jq -r '.runs[].results[]? | "  - [\(.level // "warning")] \(.ruleId // "custom-rule"): \(.message.text // "") (\(.locations[0].physicalLocation.artifactLocation.uri // "unknown"):\(.locations[0].physicalLocation.region.startLine // "1"))"' "$OUTPUT_FILE" 2>/dev/null | head -n 10 || true
            fi
        fi
    elif [[ "$OUTPUT_FORMAT" == "csv" ]]; then
        LINES=$(wc -l < "$OUTPUT_FILE")
        echo -e "${CYAN}[*] Summary: Found ${LINES} CSV record(s) / alert(s).${NC}"
    fi
fi

exit 0
