#!/usr/bin/env bash
# ==============================================================================
# network-toolcheck.sh — Network Analysis & Forensics Toolchain Verification
# ==============================================================================
# Verifies presence, version, and execution capability of all Section 19 tools:
# tshark, tcpdump, capinfos, editcap, mergecap, dumpcap, nmap, scapy.
# Assesses live capture vs offline forensic capabilities.
# ==============================================================================

set -euo pipefail

# Color formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

TOTAL_TESTS=0
PASSED_TESTS=0
WARNED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BOLD}${CYAN}      NETWORK ANALYSIS & PACKET FORENSICS TOOLCHAIN CHECK           ${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo -e "Host Architecture: $(uname -m) / Kernel: $(uname -r)"
echo -e "User ID:           $(id -u -n) (UID: $(id -u), GID: $(id -g))"
echo -e "Timestamp:         $(date -u '+%Y-%m-%d %H:%M:%SZ')"
echo -e "${BLUE}----------------------------------------------------------------------${NC}"

printf "%-18s %-10s %-25s %-20s\n" "TOOL / COMPONENT" "STATUS" "VERSION" "NOTES"
printf "%-18s %-10s %-25s %-20s\n" "----------------" "------" "-------" "-----"

check_cli_tool() {
    local tool_name="$1"
    local version_cmd="$2"
    local required="${3:-true}"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if command -v "$tool_name" &>/dev/null; then
        local version
        version=$(eval "$version_cmd" 2>&1 | head -n 1 | tr -d '\r\n')
        # Truncate version string if too long
        if [[ ${#version} -gt 24 ]]; then
            version="${version:0:22}..."
        fi
        printf "%-18s ${GREEN}%-10s${NC} %-25s %-20s\n" "$tool_name" "PASS" "$version" "Binary available"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        if [[ "$required" == "true" ]]; then
            printf "%-18s ${RED}%-10s${NC} %-25s %-20s\n" "$tool_name" "FAIL" "NOT FOUND" "Required tool missing"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        else
            printf "%-18s ${YELLOW}%-10s${NC} %-25s %-20s\n" "$tool_name" "OPTIONAL" "NOT FOUND" "Optional tool"
            WARNED_TESTS=$((WARNED_TESTS + 1))
        fi
    fi
}

# 1. Check Wireshark suite CLI tools
check_cli_tool "tshark" "tshark --version | head -n 1 | awk '{print \$1, \$2}'" "true"
check_cli_tool "tcpdump" "tcpdump --version 2>&1 | head -n 1 | awk '{print \$1, \$3}'" "true"
check_cli_tool "capinfos" "capinfos -v 2>&1 | head -n 1 | awk '{print \$1, \$2}'" "true"
check_cli_tool "editcap" "editcap -v 2>&1 | head -n 1 | awk '{print \$1, \$2}'" "true"
check_cli_tool "mergecap" "mergecap -v 2>&1 | head -n 1 | awk '{print \$1, \$2}'" "true"
check_cli_tool "dumpcap" "dumpcap -v 2>&1 | head -n 1 | awk '{print \$1, \$2}'" "true"
check_cli_tool "nmap" "nmap --version | head -n 1 | awk '{print \$1, \$3}'" "true"

# 2. Check Python Scapy module
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if python3 -c "import scapy; print(scapy.__version__)" &>/dev/null; then
    SCAPY_VER=$(python3 -c "import scapy; print(scapy.__version__)" 2>/dev/null || echo "installed")
    printf "%-18s ${GREEN}%-10s${NC} %-25s %-20s\n" "scapy (Python3)" "PASS" "v${SCAPY_VER}" "Library importable"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    printf "%-18s ${RED}%-10s${NC} %-25s %-20s\n" "scapy (Python3)" "FAIL" "NOT FOUND" "Python scapy missing"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo -e "${BLUE}----------------------------------------------------------------------${NC}"
echo -e "\n${BOLD}${CYAN}           CAPTURE PRIVILEGE & CAPABILITY ASSESSMENT                 ${NC}"
echo -e "${BLUE}----------------------------------------------------------------------${NC}"

# Check dumpcap capabilities & permissions
DUMPCAP_PATH=$(command -v dumpcap || echo "")
if [[ -n "$DUMPCAP_PATH" ]]; then
    GETCAP_OUT=$(getcap "$DUMPCAP_PATH" 2>/dev/null || true)
    if [[ -n "$GETCAP_OUT" ]]; then
        echo -e "dumpcap Linux Capabilities: ${GREEN}${GETCAP_OUT}${NC}"
    else
        echo -e "dumpcap Linux Capabilities: ${YELLOW}None configured (standard non-root)${NC}"
    fi
    
    # Test if current user can run live capture without sudo
    if timeout 1 dumpcap -i lo -c 1 -w /dev/null &>/dev/null; then
        echo -e "Live Interface Capture:     ${GREEN}ENABLED (Unprivileged capture supported)${NC}"
    elif sudo timeout 1 dumpcap -i lo -c 1 -w /dev/null &>/dev/null; then
        echo -e "Live Interface Capture:     ${YELLOW}PRIVILEGED ONLY (Requires sudo / CAP_NET_ADMIN / CAP_NET_RAW)${NC}"
    else
        echo -e "Live Interface Capture:     ${YELLOW}RESTRICTED (Container environment limits raw socket access)${NC}"
    fi
else
    echo -e "dumpcap: ${RED}Not installed${NC}"
fi

# Offline PCAP capability test
SAMPLE_PCAP="/workspaces/codespaces-blank/fixtures/network/sample.pcap"
if [[ -f "$SAMPLE_PCAP" ]] && command -v tshark &>/dev/null; then
    if tshark -r "$SAMPLE_PCAP" -c 1 &>/dev/null; then
        echo -e "Offline PCAP Forensics:     ${GREEN}VERIFIED & FULLY FUNCTIONAL${NC}"
    else
        echo -e "Offline PCAP Forensics:     ${RED}FAILED TO READ SAMPLE PCAP${NC}"
    fi
else
    echo -e "Offline PCAP Forensics:     ${YELLOW}PENDING FIXTURE GENERATION${NC}"
fi

echo -e "${BLUE}======================================================================${NC}"
echo -e "Summary: Total: ${TOTAL_TESTS} | Passed: ${GREEN}${PASSED_TESTS}${NC} | Warnings/Optional: ${YELLOW}${WARNED_TESTS}${NC} | Failed: ${RED}${FAILED_TESTS}${NC}"

if [[ "$FAILED_TESTS" -eq 0 ]]; then
    echo -e "${BOLD}${GREEN}[✔] Network Analysis Toolchain is Ready for Use.${NC}"
    exit 0
else
    echo -e "${BOLD}${RED}[✖] Network Analysis Toolchain has unmet requirements.${NC}"
    exit 1
fi
