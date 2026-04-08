#!/usr/bin/env python3
import os
import subprocess
import tarfile

# =========================
# Configuration
# =========================
TARGET_DIR = "/"           # Root of the container
FILE_UNPACK = "filesystem.tar.gz"  # Archive

# Directories that filesystem.py will ensure exist
DIRECTORIES = [
    "debug",
    "debug/app",
    "debug/static",
    "debug/system",
    "debug/head-tracking",
    "home/airpods",
    "driver"
    
]

# =========================
# Helper Functions
# =========================
def ensure_dir(path: str):
    """Create directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"? Created directory: {path}")
        
# ------------------------------
# Safety checks
# ------------------------------
if not os.path.isfile(FILE_UNPACK):
    print(f"Error: File '{FILE_UNPACK}' not found.")
    sys.exit(1)

# =========================
# unpack debug
# =========================

try:
    # Determine compression mode automatically
    if FILE_UNPACK.endswith(".tar.gz") or FILE_UNPACK.endswith(".tgz"):
        mode = "r:gz"
    elif FILE_UNPACK.endswith(".tar.bz2"):
        mode = "r:bz2"
    else:
        mode = "r:"  # Plain tar

    with tarfile.open(FILE_UNPACK, mode) as tar:
        # List contents
        print("Archive contents:")
        tar.list()

        # Extract all to target directory
        print(f"\nExtracting to '{TARGET_DIR}' ...")
        tar.extractall(path=TARGET_DIR)
        print("Extraction complete.")

except tarfile.TarError as e:
    print(f"Error reading archive: {e}")
    sys.exit(2)
except PermissionError:
    print("Permission denied: You need root privileges to extract to '/'")
    sys.exit(3)

# =========================
# Create required directories
# =========================
print("? Ensuring required directories exist...")
for d in DIRECTORIES:
    ensure_dir(os.path.join(TARGET_DIR, d))

# =========================
# Finish setup
# =========================
print("? Filesystem setup complete.")