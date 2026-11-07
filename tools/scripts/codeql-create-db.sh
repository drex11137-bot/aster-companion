#!/usr/bin/env bash
# ==============================================================================
# CodeQL Database Creation Helper Script
# tools/scripts/codeql-create-db.sh
# Creates a CodeQL database for a target codebase with automatic language detection
# ==============================================================================

set -euo pipefail

# ANSI color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_help() {
    cat << HELPEOF
Usage: $(basename "$0") [OPTIONS] <database-output-dir> [source-root] [language] [build-command]

Arguments:
  <database-output-dir>   Path where the CodeQL database will be created.
  [source-root]           Root directory of the source code (default: current directory).
  [language]              Language identifier (e.g., python, javascript, cpp, java, go, ruby, rust).
                          If omitted, language will be auto-detected.
  [build-command]         Build command for compiled languages (e.g., "cmake --build build" or "make").

Options:
  -d, --db DIR            Database destination directory.
  -s, --source DIR        Source code directory.
  -l, --language LANG     Target language (python, javascript, cpp, java, go, ruby, csharp, swift, rust).
  -c, --command CMD       Build command for compiled languages.
  -o, --overwrite         Overwrite destination if database directory already exists.
  -v, --verbose           Enable verbose output.
  -h, --help              Show this help message.

Examples:
  $(basename "$0") /tmp/codeql-py-db ./fixtures/security python
  $(basename "$0") --db /tmp/cpp-db --source ./fixtures/c_native --language cpp --command "make" --overwrite
  $(basename "$0") /tmp/autodetect-db .
HELPEOF
}

# Defaults
DB_PATH=""
SOURCE_ROOT="."
LANGUAGE=""
BUILD_COMMAND=""
OVERWRITE=0
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
        -s|--source)
            SOURCE_ROOT="$2"
            shift 2
            ;;
        -l|--language)
            LANGUAGE="$2"
            shift 2
            ;;
        -c|--command)
            BUILD_COMMAND="$2"
            shift 2
            ;;
        -o|--overwrite)
            OVERWRITE=1
            shift
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

# Map positional arguments if options were not explicitly provided
if [[ -z "$DB_PATH" && ${#POSITIONAL_ARGS[@]} -gt 0 ]]; then
    DB_PATH="${POSITIONAL_ARGS[0]}"
fi
if [[ "$SOURCE_ROOT" == "." && ${#POSITIONAL_ARGS[@]} -gt 1 ]]; then
    SOURCE_ROOT="${POSITIONAL_ARGS[1]}"
fi
if [[ -z "$LANGUAGE" && ${#POSITIONAL_ARGS[@]} -gt 2 ]]; then
    LANGUAGE="${POSITIONAL_ARGS[2]}"
fi
if [[ -z "$BUILD_COMMAND" && ${#POSITIONAL_ARGS[@]} -gt 3 ]]; then
    BUILD_COMMAND="${POSITIONAL_ARGS[3]}"
fi

# Validation
if [[ -z "$DB_PATH" ]]; then
    echo -e "${RED}[ERROR] Database output path is required.${NC}" >&2
    show_help
    exit 1
fi

if [[ ! -d "$SOURCE_ROOT" ]]; then
    echo -e "${RED}[ERROR] Source root directory does not exist: $SOURCE_ROOT${NC}" >&2
    exit 1
fi

# Verify codeql CLI availability
if ! command -v codeql &> /dev/null; then
    echo -e "${RED}[ERROR] 'codeql' CLI not found in PATH.${NC}" >&2
    exit 1
fi

# Resolve source root to absolute path
SOURCE_ROOT="$(cd "$SOURCE_ROOT" && pwd)"

# Auto-detect language if not specified
if [[ -z "$LANGUAGE" ]]; then
    echo -e "${BLUE}[*] Auto-detecting source code language in: $SOURCE_ROOT...${NC}"
    if find "$SOURCE_ROOT" -maxdepth 3 -type f \( -name "*.py" \) | grep -q .; then
        LANGUAGE="python"
    elif find "$SOURCE_ROOT" -maxdepth 3 -type f \( -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" -o -name "package.json" \) | grep -q .; then
        LANGUAGE="javascript"
    elif find "$SOURCE_ROOT" -maxdepth 3 -type f \( -name "*.c" -o -name "*.cpp" -o -name "*.cc" -o -name "*.cxx" -o -name "*.h" -o -name "*.hpp" \) | grep -q .; then
        LANGUAGE="cpp"
    elif find "$SOURCE_ROOT" -maxdepth 3 -type f \( -name "*.java" \) | grep -q .; then
        LANGUAGE="java"
    elif find "$SOURCE_ROOT" -maxdepth 3 -type f \( -name "*.go" -o -name "go.mod" \) | grep -q .; then
        LANGUAGE="go"
    elif find "$SOURCE_ROOT" -maxdepth 3 -type f \( -name "*.rb" -o -name "Gemfile" \) | grep -q .; then
        LANGUAGE="ruby"
    elif find "$SOURCE_ROOT" -maxdepth 3 -type f \( -name "*.rs" -o -name "Cargo.toml" \) | grep -q .; then
        LANGUAGE="rust"
    elif find "$SOURCE_ROOT" -maxdepth 3 -type f \( -name "*.cs" \) | grep -q .; then
        LANGUAGE="csharp"
    elif find "$SOURCE_ROOT" -maxdepth 3 -type f \( -name "*.swift" \) | grep -q .; then
        LANGUAGE="swift"
    else
        echo -e "${RED}[ERROR] Could not auto-detect language in $SOURCE_ROOT. Please specify with --language <lang>.${NC}" >&2
        exit 1
    fi
    echo -e "${GREEN}[+] Detected language: ${LANGUAGE}${NC}"
fi

# Handle existing database directory
if [[ -d "$DB_PATH" ]]; then
    if [[ $OVERWRITE -eq 1 ]]; then
        echo -e "${YELLOW}[!] Target database directory exists. Overwriting: $DB_PATH${NC}"
        rm -rf "$DB_PATH"
    else
        echo -e "${RED}[ERROR] Database directory already exists: $DB_PATH (Use --overwrite / -o to replace)${NC}" >&2
        exit 1
    fi
fi

# Build CodeQL command arguments
CMD=("codeql" "database" "create" "$DB_PATH" "--source-root=$SOURCE_ROOT" "--language=$LANGUAGE" "--overwrite")

if [[ -n "$BUILD_COMMAND" ]]; then
    CMD+=("--command=$BUILD_COMMAND")
fi

if [[ $VERBOSE -eq 1 ]]; then
    CMD+=("-v")
fi

echo -e "${BLUE}[*] Creating CodeQL database:${NC}"
echo -e "    Database:  ${DB_PATH}"
echo -e "    Source:    ${SOURCE_ROOT}"
echo -e "    Language:  ${LANGUAGE}"
if [[ -n "$BUILD_COMMAND" ]]; then
    echo -e "    Build Cmd: ${BUILD_COMMAND}"
fi

START_TIME=$(date +%s)

# Execute database creation
"${CMD[@]}"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo -e "${GREEN}[✔] CodeQL database created successfully in ${DURATION}s at: ${DB_PATH}${NC}"
exit 0
