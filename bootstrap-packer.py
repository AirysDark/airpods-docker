#!/usr/bin/env python3
import os
import tarfile

# -------------------------
# Configuration
# -------------------------
SRC_FOLDER = "rootfs_debootstrap"   # Folder to archive (must be in the same dir as this script)
DEST_TAR = "rootfs_debootstrap.tar.gz"  # Output tar.gz file

# -------------------------
# Check folder exists
# -------------------------
if not os.path.exists(SRC_FOLDER):
    raise FileNotFoundError(f"Source folder '{SRC_FOLDER}' not found in {os.getcwd()}")

# -------------------------
# Create tar.gz archive
# -------------------------
with tarfile.open(DEST_TAR, "w:gz") as tar:
    # Add the folder and all its contents
    tar.add(SRC_FOLDER, arcname=os.path.basename(SRC_FOLDER))
    print(f"? Archived '{SRC_FOLDER}' -> '{DEST_TAR}'")

print("? Done.")