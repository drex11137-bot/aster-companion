#!/usr/bin/env bash
# =============================================================================
# scripts/chrome.sh — Hybrid Chrome DevTools launcher
# =============================================================================
# Usage:
#   scripts/chrome.sh --headless   Start headless Chromium + CDP on port 9222
#   scripts/chrome.sh --gui        Start Xvfb + headed Chromium + noVNC on 6080
#   scripts/chrome.sh --stop       Stop whichever mode is running
#   scripts/chrome.sh --status     Show current mode and CDP info
# =============================================================================

set -euo pipefail

CHROME_BIN="/home/codespace/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome"
PROFILE_DIR="/tmp/chrome-debug-profile"
CDP_PORT=9222
NOVNC_PORT=6080
DISPLAY_NUM=99
PID_FILE="/tmp/chrome-mode.pid"
MODE_FILE="/tmp/chrome-mode.txt"
CHROME_LOG="/tmp/chrome-debug.log"
XVFB_LOG="/tmp/xvfb.log"
NOVNC_LOG="/tmp/novnc.log"

check_chrome_bin() {
    if [ ! -f "$CHROME_BIN" ]; then
        echo "❌ Chromium binary not found at: $CHROME_BIN"
        exit 1
    fi
}

wait_for_cdp() {
    local retries=10
    for i in $(seq 1 $retries); do
        if curl -sf "http://localhost:${CDP_PORT}/json/version" > /dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    return 1
}

stop_all() {
    echo "🛑 Stopping all Chrome/Xvfb/noVNC processes..."
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        kill "$PID" 2>/dev/null && echo "   Stopped Chrome PID $PID" || true
        rm -f "$PID_FILE"
    fi
    pkill -f "remote-debugging-port=${CDP_PORT}" 2>/dev/null || true
    pkill -f "Xvfb :${DISPLAY_NUM}" 2>/dev/null || true
    pkill -f "websockify.*${NOVNC_PORT}" 2>/dev/null || true
    rm -f "$MODE_FILE"
    sleep 1
    echo "✅ All stopped."
}

start_headless() {
    check_chrome_bin
    echo "🚀 Starting Chromium in HEADLESS mode..."
    echo "   CDP port: ${CDP_PORT}"
    if [ -f "$MODE_FILE" ]; then
        echo "   (Stopping previous $(cat $MODE_FILE) mode first)"
        stop_all
    fi
    mkdir -p "$PROFILE_DIR"
    "$CHROME_BIN" \
        --headless=new \
        --no-sandbox \
        --disable-gpu \
        --remote-debugging-port=${CDP_PORT} \
        --remote-debugging-address=127.0.0.1 \
        --user-data-dir="$PROFILE_DIR" \
        --disable-dev-shm-usage \
        --no-first-run \
        --no-default-browser-check \
        > "$CHROME_LOG" 2>&1 &
    echo $! > "$PID_FILE"
    echo "headless" > "$MODE_FILE"
    echo "   Waiting for CDP..."
    if wait_for_cdp; then
        echo ""
        echo "✅ Headless Chrome is ready!"
        echo "   CDP:  http://localhost:${CDP_PORT}/json"
        echo "   Log:  $CHROME_LOG"
    else
        echo "❌ CDP did not respond. Check: $CHROME_LOG"
        tail -10 "$CHROME_LOG" 2>/dev/null || true
        exit 1
    fi
}

start_gui() {
    check_chrome_bin
    if ! command -v Xvfb &>/dev/null; then
        echo "❌ Xvfb not found. Run: sudo apt-get install -y xvfb"
        exit 1
    fi
    if ! command -v websockify &>/dev/null; then
        echo "❌ websockify not found. Run: sudo apt-get install -y novnc websockify"
        exit 1
    fi
    echo "🖥️  Starting Chromium in GUI mode..."
    echo "   CDP port:   ${CDP_PORT}"
    echo "   noVNC port: ${NOVNC_PORT}"
    if [ -f "$MODE_FILE" ]; then
        echo "   (Stopping previous $(cat $MODE_FILE) mode first)"
        stop_all
    fi
    # 1. Start virtual display
    echo "   Starting Xvfb display :${DISPLAY_NUM}..."
    Xvfb :${DISPLAY_NUM} -screen 0 1280x900x24 -ac +extension GLX +render -noreset \
        > "$XVFB_LOG" 2>&1 &
    sleep 1
    # 2. Start headed Chromium
    mkdir -p "$PROFILE_DIR"
    echo "   Starting headed Chromium..."
    DISPLAY=:${DISPLAY_NUM} "$CHROME_BIN" \
        --no-sandbox \
        --disable-gpu \
        --remote-debugging-port=${CDP_PORT} \
        --remote-debugging-address=127.0.0.1 \
        --user-data-dir="$PROFILE_DIR" \
        --disable-dev-shm-usage \
        --no-first-run \
        --no-default-browser-check \
        --window-size=1280,900 \
        > "$CHROME_LOG" 2>&1 &
    echo $! > "$PID_FILE"
    echo "gui" > "$MODE_FILE"
    # 3. noVNC bridge (Xvfb VNC port = 5900 + display number)
    VNC_PORT=$((5900 + DISPLAY_NUM))
    echo "   Starting noVNC bridge (VNC:${VNC_PORT} → HTTP:${NOVNC_PORT})..."
    websockify --web /usr/share/novnc/ ${NOVNC_PORT} localhost:${VNC_PORT} \
        > "$NOVNC_LOG" 2>&1 &
    sleep 2
    echo "   Waiting for CDP..."
    if wait_for_cdp; then
        echo ""
        echo "✅ GUI Chrome is ready!"
        echo "   CDP:   http://localhost:${CDP_PORT}/json"
        echo "   noVNC: http://localhost:${NOVNC_PORT}/vnc.html  ← open in your browser"
        echo "   Logs:  $CHROME_LOG | $XVFB_LOG | $NOVNC_LOG"
    else
        echo "❌ CDP did not respond. Check: $CHROME_LOG"
        tail -10 "$CHROME_LOG" 2>/dev/null || true
        exit 1
    fi
}

status() {
    if [ -f "$MODE_FILE" ]; then
        MODE=$(cat "$MODE_FILE")
        echo "🟢 Chrome is running in ${MODE^^} mode"
        echo ""
        CDP_INFO=$(curl -sf "http://localhost:${CDP_PORT}/json/version" 2>/dev/null)
        if [ -n "$CDP_INFO" ]; then
            echo "   CDP (port ${CDP_PORT}): ✅ responding"
            echo "$CDP_INFO" | python3 -m json.tool 2>/dev/null | grep -E '"Browser"' | sed 's/^/   /' || true
        else
            echo "   CDP (port ${CDP_PORT}): ❌ not responding"
        fi
        TABS=$(curl -sf "http://localhost:${CDP_PORT}/json" 2>/dev/null | python3 -c \
            "import sys,json; tabs=json.load(sys.stdin); print(f'   Open tabs: {len(tabs)}'); [print(f'     [{i+1}] {t.get(\"url\",\"(blank)\")}') for i,t in enumerate(tabs[:5])]" 2>/dev/null || true)
        echo "$TABS"
        [ "$MODE" = "gui" ] && echo "" && echo "   noVNC: http://localhost:${NOVNC_PORT}/vnc.html"
    else
        echo "⚫ Chrome is not running"
        echo "   bash scripts/chrome.sh --headless   (CDP only)"
        echo "   bash scripts/chrome.sh --gui        (visible via noVNC port ${NOVNC_PORT})"
    fi
}

case "${1:-}" in
    --headless) start_headless ;;
    --gui)      start_gui ;;
    --stop)     stop_all ;;
    --status)   status ;;
    *)
        echo "Chrome DevTools Hybrid Launcher"
        echo ""
        echo "Usage: scripts/chrome.sh [--headless | --gui | --stop | --status]"
        echo ""
        echo "  --headless   Invisible Chromium with CDP on port ${CDP_PORT}"
        echo "  --gui        Xvfb + headed Chromium + noVNC on port ${NOVNC_PORT}"
        echo "  --stop       Stop whichever mode is currently running"
        echo "  --status     Show mode, CDP info, and open tabs"
        echo ""
        echo "  Only one mode runs at a time. Starting one auto-stops the other."
        ;;
esac
