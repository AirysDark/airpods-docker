#!/usr/bin/env bash

# =========================
# Logging
# =========================
log()   { echo "[*] $*"; }
warn()  { echo "[!] $*" >&2; }
error() { echo "[ERROR] $*" >&2; }

# =========================
# Config
# =========================
# Use AP_API if defined, fallback to default
API="${AP_API:-http://localhost:5000}"

# =========================
# Dependency Checks
# =========================
_check_cmd() { command -v "$1" >/dev/null 2>&1; }

require_cmd() {
    if ! _check_cmd "$1"; then
        error "$1 is required but not installed"
        return 1
    fi
}

# =========================
# Bluetooth
# =========================
check_bt() {
    if ! _check_cmd hciconfig; then
        warn "hciconfig missing"
        return 1
    fi

    if ! hciconfig | grep -q "hci"; then
        warn "No Bluetooth adapter"
        return 1
    fi

    log "Bluetooth OK"
}

bt_up() {
    log "Enabling hci0..."
    hciconfig hci0 up || error "Failed to enable hci0"
}

bt_scan() {
    log "Scanning for devices..."
    timeout 10 hcitool scan
}

dump_bt() {
    hciconfig -a
}

# =========================
# API Helpers
# =========================
api() {
    require_cmd curl || return 1
    curl -s "$API/$1"
}

ap_connect() {
    log "Connecting to AirPods..."
    api "connect"
}

ap_state() {
    if _check_cmd jq; then
        api "state" | jq
    else
        api "state"
    fi
}

ap_noise() {
    api "noise/$1"
}

ap_ca() {
    api "ca/$1"
}

ap_adaptive() {
    api "adaptive/$1"
}

# =========================
# Shortcuts
# =========================
anc()   { ap_noise 2; }
trans() { ap_noise 3; }
adapt() { ap_noise 4; }

# =========================
# Dashboard (TUI)
# =========================
ap_dash() {
    if [ ! -f "/debug/app/dashboard.py" ]; then
        error "dashboard.py not found in /app"
        return 1
    fi

    require_cmd python || return 1

    log "Launching dashboard..."
    python /debug/app/dashboard.py
}

# =========================
# Packet Recorder
# =========================
ap_record_start() {
    log "[REC] Start recording"
    api "record/start"
}

ap_record_stop() {
    log "[REC] Stop recording"
    api "record/stop"
}

ap_record_save() {
    log "[REC] Save capture"
    api "record/save"
}

ap_replay() {
    log "[REC] Replay packets"
    api "record/replay"
}

# =========================
# Raw Packet Sender
# =========================
ap_raw() {
    require_cmd curl || return 1

    if [ -z "$1" ]; then
        error "Usage: ap_raw \"HEX_STRING\""
        return 1
    fi

    log "[RAW] Sending: $1"
    curl -s -X POST "$API/raw" -d "$1"
}

# =========================
# Auto Reconnect Loop
# =========================
ap_auto() {
    log "[AUTO] Starting reconnect loop (Ctrl+C to stop)..."

    while true; do
        if curl -s "$API/connect" >/dev/null; then
            log "[OK] Connected"
        else
            warn "[FAIL] Connection failed"
        fi

        sleep 10
    done
}

# =========================
# Debug Tools
# =========================
watch_state() {
    while true; do
        clear
        ap_state
        sleep 1
    done
}

# =========================
# Safety
# =========================
require_root() {
    if [ "$EUID" -ne 0 ]; then
        error "Run as root"
        return 1
    fi
}
