#!/usr/bin/env python3
import os

# -------------------------
# Configuration
# -------------------------
ARCHIVE_FILE = "filesystem.tar.gz"  # Archive to delete

# -------------------------
# Delete the file if it exists
# -------------------------
if os.path.exists(ARCHIVE_FILE):
    os.remove(ARCHIVE_FILE)
    print(f"? Deleted '{ARCHIVE_FILE}'")
else:
    print(f"[WARN] '{ARCHIVE_FILE}' does not exist, nothing to delete")