#!/usr/bin/env python3
import os
import sys
from datetime import datetime

# =========================
# Configuration
# =========================
LOG_DIR = r"C:\Users\AirysDark\AirPodsLogs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "debug.log")

# =========================
# Helper functions
# =========================
def start_debug(script_name=None):
    """
    Call at the top of your script.
    Redirects stdout/stderr to log file and prints to console.
    """
    global LOG_FILE

    tag = f"[{script_name}]" if script_name else "[Script]"

    # Open log file
    log_f = open(LOG_FILE, "a", encoding="utf-8")

    # Wrapper to write to both console and log
    class Tee:
        def __init__(self, stream, log_file):
            self.stream = stream
            self.log_file = log_file

        def write(self, message):
            self.stream.write(message)
            self.stream.flush()
            self.log_file.write(f"{tag} {message}")
            self.log_file.flush()

        def flush(self):
            self.stream.flush()
            self.log_file.flush()

    # Redirect stdout and stderr
    sys.stdout = Tee(sys.stdout, log_f)
    sys.stderr = Tee(sys.stderr, log_f)

    print(f"{tag} ===== START {datetime.now().isoformat()} =====")

def end_debug(script_name=None):
    """
    Call at the end of your script to mark end time in log.
    """
    tag = f"[{script_name}]" if script_name else "[Script]"
    print(f"{tag} ===== END {datetime.now().isoformat()} =====")