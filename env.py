#!/usr/bin/env python3
import os
import stat
import shutil
import subprocess
import logging
import colorama
from logging import Formatter, LogRecord, Logger, StreamHandler
from typing import Any, Dict, List

# =========================
# Initialize colors
# =========================
colorama.init(autoreset=True)

handler: StreamHandler = StreamHandler()

class ColorFormatter(Formatter):
    COLORS: Dict[int, str] = {
        logging.DEBUG: colorama.Fore.BLUE,
        logging.INFO: colorama.Fore.GREEN,
        logging.WARNING: colorama.Fore.YELLOW,
        logging.ERROR: colorama.Fore.RED,
        logging.CRITICAL: colorama.Fore.MAGENTA,
    }

    def format(self, record: LogRecord) -> str:
        color: str = self.COLORS.get(record.levelno, "")
        prefix: str = f"{color}[{record.levelname}:{record.name}]{colorama.Style.RESET_ALL}"
        return f"{prefix} {record.getMessage()}"

handler.setFormatter(ColorFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger: Logger = logging.getLogger("airpods_env")

# =========================
# Container Environment Setup
# =========================
PROJECT_ROOT = "/debug"
AIRPODS_USER = "airpods"  # Default owner for scripts/folders during setup
NEW_USER = "airpods"  # Non-root user to create in container

SCRIPTS = [
    "/debug/airpods_start.py",
    "/debug/bashlib.sh",
    "/debug/airpods.py",
    "/debug/airpodsctl.py",
    "/debug/app/dashboard.py",
    "/debug/app/app.py",
    "/debug/system/battery.py",
    "/debug/system/control.py",
    "/debug/system/l2cap.py",
    "/debug/system/proximity.py",
    "/debug/system/ble_parser.py",
]

ENV_VARS = {
    "IN_DOCKER": "1",
    "APP_ROOT": PROJECT_ROOT,
    "PATH": f"{PROJECT_ROOT}:{PROJECT_ROOT}/scripts:{os.environ.get('PATH', '')}"
}

RADARE_DEB = "/drivers/radare2_6.1.2_amd64.deb"

# =========================
# Helper Functions
# =========================
def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"? Created directory: {path}")
    shutil.chown(path, user=AIRPODS_USER, group=AIRPODS_USER)

def chmod_x(path: str):
    if os.path.exists(path):
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC)
        shutil.chown(path, user=AIRPODS_USER, group=AIRPODS_USER)
        logger.info(f"? Made executable: {path}")
    else:
        logger.warning(f"Script not found: {path}")

def set_capabilities(path: str):
    if os.path.exists(path):
        try:
            subprocess.run(["setcap", "cap_net_raw,cap_net_admin+eip", path], check=True)
            logger.info(f"? Set capabilities for: {path}")
        except Exception as e:
            logger.warning(f"Failed to set capabilities: {e}")

def write_env_file(env_vars: dict, filepath: str = "/etc/profile.d/airpods_env.sh"):
    with open(filepath, "w") as f:
        for k, v in env_vars.items():
            f.write(f'export {k}="{v}"\n')
    logger.info(f"? Environment file created: {filepath}")

def install_deb_package(deb_path: str):
    """Install a .deb package if it exists."""
    if not os.path.exists(deb_path):
        logger.warning(f"[WARN] DEB package not found: {deb_path}, skipping installation")
        return
    logger.info(f"? Installing DEB package: {deb_path}")
    try:
        subprocess.run(["dpkg", "-i", deb_path], check=True)
        subprocess.run(["apt-get", "install", "-f", "-y"], check=True)  # Fix missing dependencies
        logger.info(f"? Package installed successfully: {deb_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"[ERROR] Failed to install DEB package: {deb_path} ({e})")

def create_non_root_user(username: str, groups: List[str] = None):
    """Create a non-root user if it doesn't exist and add to optional groups."""
    try:
        subprocess.run(["id", username], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"? User '{username}' already exists, skipping creation")
    except subprocess.CalledProcessError:
        cmd = ["useradd", "-ms", "/bin/bash", username]
        subprocess.run(cmd, check=True)
        logger.info(f"? Created user '{username}'")
        if groups:
            for group in groups:
                subprocess.run(["usermod", "-aG", group, username], check=True)
                logger.info(f"? Added user '{username}' to group '{group}'")

def chown_project_root(username: str, path: str):
    """Recursively change ownership of project root to the non-root user."""
    if os.path.exists(path):
        subprocess.run(["chown", "-R", f"{username}:{username}", path], check=True)
        logger.info(f"? Changed ownership of '{path}' to '{username}:{username}'")
    else:
        logger.warning(f"[WARN] Project root '{path}' does not exist, skipping chown")

def chown_bashrc(username: str):
    """Change ownership of the user's .bashrc in home directory."""
    bashrc_path = f"/home/{username}/.bashrc"
    if os.path.exists(bashrc_path):
        subprocess.run(["chown", f"{username}:{username}", bashrc_path], check=True)
        logger.info(f"? Changed ownership of '{bashrc_path}' to '{username}:{username}'")
    else:
        logger.warning(f"[WARN] {bashrc_path} not found, skipping chown")

def set_python_bin_capabilities():
    """Set capabilities on /usr/local/bin/python3 if it exists."""
    python_bin = "/usr/local/bin/python3"
    if os.path.exists(python_bin):
        try:
            subprocess.run(["setcap", "cap_net_raw,cap_net_admin+eip", python_bin], check=True)
            logger.info(f"? Set capabilities on {python_bin}")
        except Exception as e:
            logger.warning(f"[WARN] Failed to set capabilities on {python_bin}: {e}")
    else:
        logger.warning(f"[WARN] {python_bin} not found, skipping setcap")

# =========================
# Main Setup
# =========================
def main():
    logger.info("? Setting up container environment...")

    # Ensure /debug exists
    ensure_dir(PROJECT_ROOT)
    os.chdir(PROJECT_ROOT)
    logger.info(f"? Changed working directory to: {os.getcwd()}")

    # Make scripts executable
    logger.info("? Setting execution flags for scripts...")
    for script in SCRIPTS:
        chmod_x(script)

    # Write environment file
    write_env_file(ENV_VARS)

    # Set Python capabilities for BLE
    python_path = shutil.which("python3")
    if python_path:
        logger.info(f"? Setting Python capabilities for BLE: {python_path}")
        set_capabilities(python_path)

    # Set capabilities on /usr/local/bin/python3
    set_python_bin_capabilities()

    # Install radare2 DEB package
    install_deb_package(RADARE_DEB)

    # Create non-root user 'airpods' and add to bluetooth group
    create_non_root_user(NEW_USER, groups=["bluetooth"])

    # Recursively chown /debug to airpods user
    chown_project_root(NEW_USER, PROJECT_ROOT)

    # Ensure user's .bashrc is owned by airpods
    chown_bashrc(NEW_USER)

    logger.info("? Environment setup complete!")

if __name__ == "__main__":
    main()