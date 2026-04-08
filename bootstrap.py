#!/usr/bin/env python3
import os
import stat
import shutil
import subprocess
import logging
import debug
from logging import Formatter, LogRecord, Logger, StreamHandler


debug.start_debug("bootstrap")
# =========================
# Initialize logging with colors
# =========================
try:
    import colorama
    colorama.init(autoreset=True)
    use_colors = True
except ImportError:
    use_colors = False

handler: StreamHandler = StreamHandler()
class ColorFormatter(Formatter):
    COLORS = {
        logging.DEBUG: colorama.Fore.BLUE if use_colors else "",
        logging.INFO: colorama.Fore.GREEN if use_colors else "",
        logging.WARNING: colorama.Fore.YELLOW if use_colors else "",
        logging.ERROR: colorama.Fore.RED if use_colors else "",
        logging.CRITICAL: colorama.Fore.MAGENTA if use_colors else "",
    }
    def format(self, record: LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")
        prefix = f"{color}[{record.levelname}:{record.name}]{colorama.Style.RESET_ALL if use_colors else ''}"
        return f"{prefix} {record.getMessage()}"

handler.setFormatter(ColorFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger: Logger = logging.getLogger("bootstrap")

# =========================
# Configuration
# =========================
BOOT_SYSTEM = "rootfs_debootstrap.tar.gz"
EXTRACT_DIR = "/"  # Extract to root
PROJECT_ROOT = "/"             # Root of the container
TARGET_ROOT = "/"  

SYSTEM_PACKAGES = [
    "bluetooth",
    "bluez",
    "bluez-tools",
    "libbluetooth-dev",
    "curl",
    "jq",
    "bash",
    "sudo",
    "iproute2",
    "git",
    # Build tools needed for PyBluez and other Python packages
    "build-essential",
    "python3-dev",
    "libffi-dev",
    "libssl-dev",
    "libcap2-bin",  # Ensure setcap exists
]

PYTHON_REQUIREMENTS = "/tmp/requirements.txt"

# =========================
# Required directories at container root
# =========================
REQUIRED_DIRS = [
    "/driver",
    "/debug",
    "/debug/app",
    "/debug/system",
    "/debug/head-tracking",
    "/debug/static",
]

# =========================
# Helper functions
# =========================
def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"? Created directory: {path}")

# =========================
# Create required directories
# =========================
logger.info("? Creating required directories at root...")
for d in REQUIRED_DIRS:
    ensure_dir(d)


# =========================
# Resolve full path to archive
# =========================
script_dir = os.path.dirname(os.path.abspath(__file__))
boot_path = os.path.join(script_dir, BOOT_SYSTEM)

if not os.path.exists(boot_path):
    logger.error(f"{BOOT_SYSTEM} not found at {boot_path}")
    exit(1)

logger.info(f"? Extracting {BOOT_SYSTEM} to {TARGET_ROOT}...")

# =========================
# Extract tar.gz archive
# =========================
try:
    with tarfile.open(boot_path, "r:gz") as tar:
        tar.extractall(path=TARGET_ROOT)
    logger.info(f"? Extraction complete!")
except Exception as e:
    logger.error(f"[ERROR] Failed to extract {BOOT_SYSTEM}: {e}")
    exit(1)

# =========================
# Copy requirements.txt to /tmp/
# =========================
if os.path.exists("requirements.txt"):
    shutil.copy("requirements.txt", PYTHON_REQUIREMENTS)
    logger.info(f"? requirements.txt copied to {PYTHON_REQUIREMENTS}")
else:
    logger.warning("requirements.txt not found, skipping copy")

# =========================
# Optional: Set capabilities for Python (BLE)
# =========================
python_path = shutil.which("python3")
if python_path:
    try:
        subprocess.run(["setcap", "cap_net_raw,cap_net_admin+eip", python_path], check=True)
        logger.info(f"? Python capabilities set for BLE: {python_path}")
    except Exception as e:
        logger.warning(f"Failed to set Python capabilities: {e}")

# =========================
# Install system packages + build tools
# =========================
logger.info("? Installing system dependencies and build tools...")
try:
    subprocess.run(["apt-get", "update"], check=True)
    subprocess.run(["apt-get", "install", "-y", "--no-install-recommends"] + SYSTEM_PACKAGES, check=True)
    subprocess.run(["rm", "-rf", "/var/lib/apt/lists/*"], check=True)
    logger.info("? System dependencies and build tools installed")
except Exception as e:
    logger.error(f"Failed to install system dependencies and build tools: {e}")

# =========================
# Install Python requirements
# =========================
if os.path.exists(PYTHON_REQUIREMENTS):
    logger.info("? Installing Python dependencies...")
    try:
        subprocess.run(["python3", "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run(["python3", "-m", "pip", "install", "--no-cache-dir", "-r", PYTHON_REQUIREMENTS], check=True)
        logger.info("? Python dependencies installed")
    except Exception as e:
        logger.error(f"Failed to install Python dependencies: {e}")
else:
    logger.warning(f"{PYTHON_REQUIREMENTS} not found, skipping pip install")


debug.end_debug("bootstrap")

logger.info("? Bootstrap setup complete!")