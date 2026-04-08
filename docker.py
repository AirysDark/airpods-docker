#!/usr/bin/env python3
import subprocess
import sys
import os
import shutil
from pathlib import Path

# =========================
# Configuration
# =========================
BOOTSTRAP_SCRIPT = "bootstrap-packer.py"
FILESYSTEM_SCRIPT = "filesystem-packer.py"
ROOTFS_ARCHIVE = "rootfs_debootstrap.tar.gz"
FILESYSTEM_ARCHIVE = "filesystem.tar.gz"
DOCKER_TAG = "airpods"
DOCKERFILE_DIR = "."  # Directory containing Dockerfile
CONTAINER_ROOT = "./container_root"  # Temporary staging folder

# =========================
# Helper functions
# =========================
def run_with_progress(script: str, description: str):
    """Run a Python script and show simulated % progress."""
    if not os.path.exists(script):
        print(f"[ERROR] Script not found: {script}")
        sys.exit(1)

    print(f"? Running {description} ({script})...")

    process = subprocess.Popen(
        ["python3", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    total_lines = 20  # adjust if you know expected number of output lines
    lines_count = 0

    for line in process.stdout:
        print(line, end="")
        lines_count += 1
        percent = min(100, int((lines_count / total_lines) * 100))
        print(f"\r[{description}] Progress: {percent}%", end="")

    process.wait()
    print(f"\r[{description}] Progress: 100% - Done\n")

    if process.returncode != 0:
        print(f"[ERROR] {script} failed with code {process.returncode}")
        sys.exit(process.returncode)

def copy_and_unpack_archive(archive_path: str, target_dir: str):
    """Copy archive into container staging folder and unpack."""
    if not os.path.exists(archive_path):
        print(f"[ERROR] Archive not found: {archive_path}")
        sys.exit(1)

    os.makedirs(target_dir, exist_ok=True)
    dest_path = os.path.join(target_dir, os.path.basename(archive_path))
    shutil.copy2(archive_path, dest_path)
    print(f"? Copied {archive_path} -> {dest_path}")

    # Unpack archive
    print(f"? Unpacking {dest_path} to {target_dir}...")
    try:
        subprocess.run(["tar", "-xzf", dest_path, "-C", target_dir], check=True)
        print(f"? Unpacked {archive_path} successfully")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to unpack {archive_path}: {e}")
        sys.exit(1)

    # Remove archive after unpack
    os.remove(dest_path)
    print(f"? Removed archive {dest_path}")

# =========================
# Main orchestration
# =========================
def main():
    # Step 1: Run bootstrap-packer.py
    run_with_progress(BOOTSTRAP_SCRIPT, "Bootstrap Packer")

    # Step 2: Run filesystem-packer.py
    run_with_progress(FILESYSTEM_SCRIPT, "Filesystem Packer")

    # Step 3: Copy & unpack rootfs_debootstrap.tar.gz
    copy_and_unpack_archive(ROOTFS_ARCHIVE, CONTAINER_ROOT)

    # Step 4: Copy & unpack filesystem.tar.gz
    copy_and_unpack_archive(FILESYSTEM_ARCHIVE, CONTAINER_ROOT)

    # Step 5: Build Docker image using prepared container root
    print("? Building Docker image...")
    try:
        subprocess.run(
            ["docker", "build", "-t", DOCKER_TAG, DOCKERFILE_DIR],
            check=True
        )
        print(f"? Docker image '{DOCKER_TAG}' built successfully!")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Docker build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()