#!/usr/bin/env bash
# ==============================================================================
# ANTIGRAVITY ENGINEERING WORKSTATION - BOOTSTRAP SCRIPT
# Location: .devcontainer/scripts/bootstrap.sh
# Purpose: Idempotent automated workstation provisioning, path setup, and verification.
# Conforms to instruction.md Section 5 and Section 34.
# ==============================================================================

set -euo pipefail

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "\n${CYAN}${BOLD}=== $1 ===${NC}"
}

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPTS_DIR="${WORKSPACE_ROOT}/.devcontainer/scripts"
TOOLS_DIR="${WORKSPACE_ROOT}/tools/scripts"
BIN_DIR="${WORKSPACE_ROOT}/tools/bin"

log_section "1. Initializing Environment & Environment Variables"

export ANDROID_HOME="/usr/local/android-sdk"
export ANDROID_SDK_ROOT="/usr/local/android-sdk"
export GHIDRA_HOME="/usr/local/ghidra"
export CODEQL_HOME="/usr/local/codeql"
if [ -d "/usr/lib/jvm/java-21-openjdk-amd64" ]; then
    export JAVA_HOME="/usr/lib/jvm/java-21-openjdk-amd64"
elif [ -d "/usr/lib/jvm/java-17-openjdk-amd64" ]; then
    export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
fi

export PATH="${ANDROID_HOME}/cmdline-tools/latest/bin:${ANDROID_HOME}/platform-tools:${ANDROID_HOME}/build-tools/34.0.0:${GHIDRA_HOME}/support:${CODEQL_HOME}:/usr/local/jadx/bin:${BIN_DIR}:${TOOLS_DIR}:${HOME}/.local/bin:${HOME}/.gemini/antigravity-cli/bin:${PATH}"

# Persist environment to user profile if not present
USER_RC="${HOME}/.bashrc"
if [ -f "${USER_RC}" ]; then
    if ! grep -q "ANDROID_HOME" "${USER_RC}"; then
        log_info "Writing workstation environment variables to ${USER_RC}..."
        cat << 'EOF' >> "${USER_RC}"

# >>> Antigravity Workstation Environment >>>
export ANDROID_HOME="/usr/local/android-sdk"
export ANDROID_SDK_ROOT="/usr/local/android-sdk"
export GHIDRA_HOME="/usr/local/ghidra"
export CODEQL_HOME="/usr/local/codeql"
[ -d "/usr/lib/jvm/java-21-openjdk-amd64" ] && export JAVA_HOME="/usr/lib/jvm/java-21-openjdk-amd64"
export PATH="/usr/local/android-sdk/cmdline-tools/latest/bin:/usr/local/android-sdk/platform-tools:/usr/local/android-sdk/build-tools/34.0.0:/usr/local/ghidra/support:/usr/local/codeql:/usr/local/jadx/bin:/workspaces/codespaces-blank/tools/bin:/workspaces/codespaces-blank/tools/scripts:${HOME}/.local/bin:${HOME}/.gemini/antigravity-cli/bin:${PATH}"
# <<< Antigravity Workstation Environment <<<
EOF
        log_success "Environment variables registered in ${USER_RC}."
    fi
fi

log_section "2. Ensuring Directory Structure and Permissions"
mkdir -p "${HOME}/.local/bin" \
         "${BIN_DIR}" \
         "${TOOLS_DIR}" \
         "${WORKSPACE_ROOT}/docs" \
         "${WORKSPACE_ROOT}/.agents/memory" \
         "${WORKSPACE_ROOT}/.agents/skills"

# Create /usr/local directories safely
for dir in "${ANDROID_HOME}" "${GHIDRA_HOME}" "${CODEQL_HOME}" "/usr/local/jadx"; do
    if [ ! -d "${dir}" ]; then
        if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
            sudo mkdir -p "${dir}"
            sudo chown -R "$(id -u):$(id -g)" "${dir}"
        else
            mkdir -p "${dir}" 2>/dev/null || true
        fi
    fi
done

# Make scripts executable
if [ -d "${SCRIPTS_DIR}" ]; then
    chmod +x "${SCRIPTS_DIR}"/*.sh 2>/dev/null || true
fi
if [ -d "${TOOLS_DIR}" ]; then
    chmod +x "${TOOLS_DIR}"/* 2>/dev/null || true
fi
if [ -d "${BIN_DIR}" ]; then
    chmod +x "${BIN_DIR}"/* 2>/dev/null || true
fi

log_section "3. Checking and Initializing Android SDK Licenses"
if command -v sdkmanager >/dev/null 2>&1; then
    log_info "Accepting Android SDK licenses..."
    timeout 5 bash -c "yes | sdkmanager --licenses" >/dev/null 2>&1 || true
    log_success "Android SDK licenses accepted."
else
    log_warn "sdkmanager not found in current PATH. Android toolchain will be initialized upon image rebuild."
fi

log_section "4. Setting up Project Tooling Symlinks"
# Symlink tools into ~/.local/bin for global accessibility
for tool in "${TOOLS_DIR}"/* "${BIN_DIR}"/*; do
    if [ -f "${tool}" ] && [ -x "${tool}" ]; then
        tool_name="$(basename "${tool}")"
        ln -sf "${tool}" "${HOME}/.local/bin/${tool_name}"
    fi
done

log_section "5. Verifying Installation & Executing Toolchain Verifier"
if [ -f "${SCRIPTS_DIR}/verify-toolchain.sh" ]; then
    bash "${SCRIPTS_DIR}/verify-toolchain.sh"
else
    log_warn "verify-toolchain.sh not found yet at ${SCRIPTS_DIR}/verify-toolchain.sh"
fi

log_section "Bootstrap Complete"
log_success "Antigravity Workstation DevContainer environment initialized successfully."
