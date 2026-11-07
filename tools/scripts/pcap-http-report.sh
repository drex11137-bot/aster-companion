#!/usr/bin/env bash
# ==============================================================================
# pcap-http-report.sh — Forensic HTTP Traffic Inspection & Reporting Tool
# ==============================================================================
# Extracts, correlates, and analyzes HTTP requests and responses from PCAP files.
# Identifies endpoints, client user-agents, server banners, payloads, and status codes.
# ==============================================================================

set -euo pipefail

# Color formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

usage() {
    echo -e "${BOLD}Usage:${NC} $0 <path-to-pcap-file> [output-report-file]"
    echo ""
    echo "Arguments:"
    echo "  <path-to-pcap-file>     Path to .pcap or .pcapng file"
    echo "  [output-report-file]    Optional path to save full report output"
    echo ""
    echo "Examples:"
    echo "  $0 /workspaces/codespaces-blank/fixtures/network/sample.pcap"
    echo "  $0 /workspaces/codespaces-blank/fixtures/network/sample.pcap http_report.txt"
    exit 1
}

# Target file determination
if [[ $# -lt 1 ]]; then
    DEFAULT_PCAP="/workspaces/codespaces-blank/fixtures/network/sample.pcap"
    if [[ -f "$DEFAULT_PCAP" ]]; then
        PCAP_FILE="$DEFAULT_PCAP"
        echo -e "${YELLOW}[!] No PCAP specified. Using default fixture: ${PCAP_FILE}${NC}\n"
    else
        usage
    fi
else
    PCAP_FILE="$1"
fi

OUTPUT_FILE="${2:-}"

if [[ ! -f "$PCAP_FILE" ]]; then
    echo -e "${RED}[ERROR] PCAP file not found: ${PCAP_FILE}${NC}" >&2
    exit 2
fi

# Ensure tshark is present
if ! command -v tshark &>/dev/null; then
    echo -e "${RED}[ERROR] tshark is not installed or not in PATH.${NC}" >&2
    exit 3
fi

generate_report() {
    echo -e "${BLUE}======================================================================${NC}"
    echo -e "${BOLD}${CYAN}            PCAP HTTP FORENSIC ANALYSIS REPORT                       ${NC}"
    echo -e "${BLUE}======================================================================${NC}"
    echo -e "${BOLD}Capture File:${NC}  $(realpath "$PCAP_FILE")"
    echo -e "${BOLD}Analysis Time:${NC} $(date -u '+%Y-%m-%d %H:%M:%SZ')"
    echo -e "${BLUE}----------------------------------------------------------------------${NC}"

    # Check if any HTTP packets exist
    HTTP_COUNT=$(tshark -r "$PCAP_FILE" -Y "http" -T fields -e frame.number 2>/dev/null | wc -l || echo 0)
    if [[ "$HTTP_COUNT" -eq 0 ]]; then
        echo -e "${YELLOW}[!] No HTTP packets found in $(basename "$PCAP_FILE").${NC}"
        echo -e "${BLUE}======================================================================${NC}"
        return 0
    fi

    # 1. Summary Metrics
    REQ_COUNT=$(tshark -r "$PCAP_FILE" -Y "http.request" -T fields -e frame.number 2>/dev/null | wc -l || echo 0)
    RESP_COUNT=$(tshark -r "$PCAP_FILE" -Y "http.response" -T fields -e frame.number 2>/dev/null | wc -l || echo 0)

    echo -e "\n${BOLD}${GREEN}[1] TRAFFIC OVERVIEW${NC}"
    echo -e "${BLUE}----------------------------------------------------------------------${NC}"
    echo -e "Total HTTP Packets:   ${BOLD}${HTTP_COUNT}${NC}"
    echo -e "HTTP Requests:        ${BOLD}${REQ_COUNT}${NC}"
    echo -e "HTTP Responses:       ${BOLD}${RESP_COUNT}${NC}"

    # 2. Unique Hostnames & Endpoints
    echo -e "\n${BOLD}${GREEN}[2] UNIQUE HOSTNAMES & DOMAINS${NC}"
    echo -e "${BLUE}----------------------------------------------------------------------${NC}"
    tshark -r "$PCAP_FILE" -Y "http.host" -T fields -e http.host 2>/dev/null | sort -u | while read -r host; do
        [[ -n "$host" ]] && echo -e " • ${CYAN}${host}${NC}"
    done

    # 3. HTTP Requests Detail
    echo -e "\n${BOLD}${GREEN}[3] HTTP REQUESTS LOG${NC}"
    echo -e "${BLUE}----------------------------------------------------------------------${NC}"
    printf "%-6s %-7s %-24s %-28s %-25s\n" "FRAME" "METHOD" "HOST" "URI" "USER-AGENT"
    printf "%-6s %-7s %-24s %-28s %-25s\n" "-----" "------" "----" "---" "----------"
    tshark -r "$PCAP_FILE" -Y "http.request" -T fields \
        -e frame.number -e http.request.method -e http.host -e http.request.uri -e http.user_agent \
        -E header=n -E separator="|" 2>/dev/null | \
        awk -F"|" '{ printf "%-6s %-7s %-24s %-28s %-25s\n", $1, $2, substr($3,1,24), substr($4,1,28), substr($5,1,25) }'

    # 4. HTTP Responses Detail
    echo -e "\n${BOLD}${GREEN}[4] HTTP RESPONSES LOG${NC}"
    echo -e "${BLUE}----------------------------------------------------------------------${NC}"
    printf "%-6s %-8s %-18s %-24s %-12s %-20s\n" "FRAME" "STATUS" "CODE PHRASE" "CONTENT-TYPE" "LENGTH" "SERVER BANNER"
    printf "%-6s %-8s %-18s %-24s %-12s %-20s\n" "-----" "------" "-----------" "------------" "------" "-------------"
    tshark -r "$PCAP_FILE" -Y "http.response" -T fields \
        -e frame.number -e http.response.code -e http.response.phrase -e http.content_type -e http.content_length -e http.server \
        -E header=n -E separator="|" 2>/dev/null | \
        awk -F"|" '{ printf "%-6s %-8s %-18s %-24s %-12s %-20s\n", $1, $2, substr($3,1,18), substr($4,1,24), ($5=="" ? "N/A" : $5), substr($6,1,20) }'

    # 5. Security & Anomaly Indicators
    echo -e "\n${BOLD}${GREEN}[5] FORENSIC & SECURITY INDICATORS${NC}"
    echo -e "${BLUE}----------------------------------------------------------------------${NC}"
    
    # Check 4xx / 5xx error responses
    ERRORS_4XX_5XX=$(tshark -r "$PCAP_FILE" -Y "http.response.code >= 400" -T fields -e frame.number -e http.response.code -e http.response.phrase 2>/dev/null || true)
    if [[ -n "$ERRORS_4XX_5XX" ]]; then
        echo -e "${YELLOW}[!] Client/Server Errors Detected (>= 400):${NC}"
        echo "$ERRORS_4XX_5XX" | awk '{ printf "  - Frame %s: HTTP %s (%s)\n", $1, $2, $3 }'
    else
        echo -e "${GREEN}[✔] No HTTP 4xx/5xx error status codes encountered.${NC}"
    fi

    # Check POST requests with payload bodies
    POST_REQS=$(tshark -r "$PCAP_FILE" -Y 'http.request.method == "POST"' -T fields -e frame.number -e http.host -e http.request.uri 2>/dev/null || true)
    if [[ -n "$POST_REQS" ]]; then
        echo -e "\n${YELLOW}[!] HTTP POST Operations (Potential Data Submission/Auth):${NC}"
        echo "$POST_REQS" | awk '{ printf "  - Frame %s: POST %s%s\n", $1, $2, $3 }'
    fi

    # Check Authorization Headers
    AUTH_FRAMES=$(tshark -r "$PCAP_FILE" -Y "http.authorization" -T fields -e frame.number -e http.authorization 2>/dev/null || true)
    if [[ -n "$AUTH_FRAMES" ]]; then
        echo -e "\n${RED}[!] HTTP Authorization Credentials Disclosed in Cleartext:${NC}"
        echo "$AUTH_FRAMES" | awk '{ printf "  - Frame %s: %s\n", $1, $2 }'
    else
        echo -e "\n${GREEN}[✔] No cleartext Authorization headers observed.${NC}"
    fi

    echo -e "\n${BLUE}======================================================================${NC}"
    echo -e "${BOLD}${GREEN}[✔] HTTP Forensic Report Generated Successfully.${NC}"
    echo -e "${BLUE}======================================================================${NC}"
}

if [[ -n "$OUTPUT_FILE" ]]; then
    # Generate report and tee to output file without ANSI codes for clean text
    generate_report | tee >(sed -r "s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[mGK]//g" > "$OUTPUT_FILE")
    echo -e "\n${GREEN}[+] Report saved to: ${OUTPUT_FILE}${NC}"
else
    generate_report
fi
