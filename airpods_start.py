#!/usr/bin/env python3
import subprocess
import shutil
import time
import logging
from pathlib import Path
import os
import debug

debug.start_debug("airpods_start")

# =========================
# Logging setup
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="[*] %(message)s"
)
log = logging.info
warn = lambda msg: logging.warning("[!] " + msg)
error = lambda msg: logging.error("[ERROR] " + msg)

# =========================
# Configuration
# =========================
APP_API = os.environ.get("AP_API", "http://localhost:5050")
DASH = Path("/debug/app/dashboard.py")   # Corrected path
WEB = Path("/debug/app/app.py")

# =========================
# Functions
# =========================
def auto_connect(timeout: int = 10) -> bool:
    """Scan for AirPods and pair/connect automatically."""
    log("Scanning for AirPods...")

    if shutil.which("hcitool") is None:
        error("hcitool not found. Install bluetooth tools.")
        return False

    try:
        # Scan for devices
        scan_cmd = f"timeout {timeout} hcitool scan"
        result = subprocess.run(scan_cmd, shell=True, capture_output=True, text=True)
        mac = None
        for line in result.stdout.splitlines():
            if "AirPods" in line:
                mac = line.split()[0]
                break
        if mac is None:
            warn("No AirPods found")
            return False

        log(f"Pairing and connecting to {mac}...")
        if shutil.which("bluetoothctl") is None:
            error("bluetoothctl not found. Install bluez package.")
            return False

        bt_cmds = f"pair {mac}\nconnect {mac}\ntrust {mac}\nexit\n"
        subprocess.run(["bluetoothctl"], input=bt_cmds, text=True, check=False)
        log(f"AirPods paired & connected: {mac}")
        return True
    except Exception as e:
        error(f"Auto-connect failed: {e}")
        return False

def launch_web():
    """Launch web dashboard only."""
    if not WEB.is_file():
        error(f"app.py not found at {WEB}")
        return
    log("Starting web server (Flask + SocketIO)...")
    subprocess.Popen(["python3", str(WEB)])

def launch_tui():
    """Optional: launch dashboard.py manually."""
    if not DASH.is_file():
        error(f"dashboard.py not found at {DASH}")
        return
    log("Launching TUI dashboard (manual use only)...")
    subprocess.Popen(["python3", str(DASH)])

# =========================
# Main
# =========================
def main():
    log("Starting AirPods auto-launch sequence...")

    if not auto_connect():
        log("[INFO] Skipping auto-connect (no AirPods found)")

    # Launch web dashboard
    launch_web()

    # Optional: do not launch TUI automatically
    # Uncomment to launch manually:
    # launch_tui()

    log("Dashboard running. Web: http://localhost:5050")
    log("TUI dashboard is available via dashboard.py manually.")

    # Keep main process alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Shutting down dashboards...")

debug.end_debug("airpods_start")

if __name__ == "__main__":
    main()