#!/usr/bin/env bash
# ==============================================================================
# PCAP-SUMMARY: Summarize Packet Capture Metadata and Traffic Flows
# Location: tools/scripts/pcap-summary.sh
# Purpose: Outputs packet count, protocols, conversations, and capture statistics.
# Conforms to instruction.md Section 19.
# ==============================================================================

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <pcap_file>"
    exit 1
fi

PCAP_FILE="$1"

if [ ! -f "${PCAP_FILE}" ]; then
    echo "Error: PCAP file '${PCAP_FILE}' does not exist."
    exit 1
fi

echo "================================================================="
echo "                  PCAP FORENSIC SUMMARY REPORT                   "
echo "================================================================="
echo "File: ${PCAP_FILE}"

if command -v capinfos >/dev/null 2>&1; then
    echo -e "\n--- File & Capture Statistics (capinfos) ---"
    capinfos -c -d -u -s -e -y -i "${PCAP_FILE}"
fi

if command -v tshark >/dev/null 2>&1; then
    echo -e "\n--- Protocol Hierarchy Statistics ---"
    tshark -n -r "${PCAP_FILE}" -q -z io,phs

    echo -e "\n--- IP Conversations Summary ---"
    tshark -n -r "${PCAP_FILE}" -q -z conv,ip

    echo -e "\n--- Top DNS Queries ---"
    tshark -n -r "${PCAP_FILE}" -Y "dns.flags.response == 0" -T fields -e dns.qry.name 2>/dev/null | sort | uniq -c | sort -nr | head -n 10 || true
else
    echo "Note: tshark is required for in-depth protocol dissection."
fi
