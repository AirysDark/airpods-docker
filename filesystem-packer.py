#!/usr/bin/env python3
import tarfile
import os

# -------------------------
# Configuration
# -------------------------
ARCHIVE_NAME = "filesystem.tar.gz"  # Output archive




# Files to include: source path -> target path in archive
FILES_TO_ADD = {
    ".bashrc": "home/airpods/.bashrc",
    "airpods.py": "debug/airpods.py",
    "airpods_start.py": "debug/airpods_start.py",
    "airpodsctl.py": "debug/airpodsctl.py",
    "debug.py": "debug/debug.py",
    "docker-compose.yml": "debug/docker-compose.yml",
}

# Folders to include: source folder -> target folder in archive
FOLDERS_TO_ADD = {
    "driver": "driver",
    "app": "debug/app",
    "head-tracking": "debug/head-tracking",
    "system": "debug/system",
    "static": "debug/static",
}

# -------------------------
# Create tar.gz archive
# -------------------------
with tarfile.open(ARCHIVE_NAME, "w:gz") as tar:
    # Add files
    for src, target in FILES_TO_ADD.items():
        if os.path.exists(src):
            tar.add(src, arcname=target)
            print(f"? Added file {src} -> {target}")
        else:
            print(f"[WARN] File not found: {src}")

    # Add folders recursively
    for src_folder, target_folder in FOLDERS_TO_ADD.items():
        if os.path.exists(src_folder):
            for root, dirs, files in os.walk(src_folder):
                for f in files:
                    full_path = os.path.join(root, f)
                    # Compute relative path inside archive
                    rel_path = os.path.relpath(full_path, src_folder)
                    arcname = os.path.join(target_folder, rel_path)
                    tar.add(full_path, arcname=arcname)
                    print(f"? Added file {full_path} -> {arcname}")
        else:
            print(f"[WARN] Folder not found: {src_folder}")

print(f"? Archive '{ARCHIVE_NAME}' created successfully")