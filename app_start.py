import sys
import os
import subprocess
import venv
import re
import logging
from pathlib import Path
from app.util import MIN_PYTHON_VERSION, APP_NAME, BASE_DIR, VENV_DIR, DATA_DIR, IMG_DIR

logger = logging.getLogger(__name__)

def check_python_version():
    """
    Verifies that the user has the required Python version (>=3.12) installed
    """
    if sys.version_info < MIN_PYTHON_VERSION:
        logger.error(f"\n[!] ERROR: {APP_NAME} requires Python {'.'.join(map(str, MIN_PYTHON_VERSION))}+")
        logger.error(f"Your version: {sys.version.split()[0]}")
        logger.error("Please update Python and try again.\n")
        sys.exit(1)

def check_dotenv():
    """
    Checks the .env file for necessary variables
    If .env doesn't exist, creates a template and exits
    """
    env_path = BASE_DIR / ".env"
    env_template = (
        "REFLEX_HOT_RELOAD_OVERRIDE_PATHS=app\n\n"
        "# If using your own IGDB API credentials, update to your client string\n"
        "IGDB_CLIENT=jxaie3smxn6w1gp5tg6gmziy147lik\n\n"
        "# Add your client secret here\n"
        "IGDB_SECRET=\n"
    )

    if not env_path.exists():
        logger.info("[*] Configuration file (.env) not found. Creating template...")
        with open(env_path, "w") as f:
            f.write(env_template)
        logger.info(f"[!] A template .env file has been created at {env_path}")
        logger.info("[!] Before starting: Open this file, add your IGDB_SECRET, and save it.")
        logger.info("[!] Then, run the application again.\n")
        sys.exit(0)
    else:
        # Check if the API key is actually defined in .env
        with open(env_path, "r") as f:
            env_content = f.read()
            if not re.search(r"IGDB_SECRET\s*=\s*\S+", env_content):
                logger.error("[!] ERROR: IGDB_SECRET is missing from your .env file.")
                logger.error(f"Please edit {env_path} and add your key.")
                sys.exit(1)

def create_venv():
    """
    Creates the python virtual environment to use for the app
    """
    if not VENV_DIR.exists():
        logger.info(f"[*] Creating virtual environment in {VENV_DIR}...")
        venv.create(VENV_DIR, with_pip=True)

def venv_py(venv_path: Path, command: list):
    """
    Runs the specified Python command using the app's virtual environment

    Args:
        venv_path: Path to the virtual environment directory
        command: List of arguments to pass to the venv's python command
    """
    if os.name == 'nt':
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        
    if not python_exe.exists():
        logger.error(f"[!] Error: Could not find python executable in {venv_path}")
        sys.exit(1)
        
    full_command = [str(python_exe)] + command
    return subprocess.run(full_command, check=True)

def install_deps():
    """
    Installs dependencies into the venv using requirements.txt
    """
    try:
        logger.info("[*] Installing dependencies...")
        req_file = BASE_DIR / "requirements.txt"
        if req_file.exists():
            venv_py(VENV_DIR, ["-m", "pip", "install", "-q", "-r", str(req_file)])
        else:
            # If requirements.txt doesn't exist, we fallback to a direct install
            logger.error("[!] No requirements.txt found. Installing core packages...")
            venv_py(VENV_DIR, ["-m", "pip", "install", "-q", "reflex", "sqlalchemy", "requests"])

        # Installing chromium for playwright image generation
        venv_py(VENV_DIR, ["-m", "playwright", "install", "chromium"])
    except subprocess.CalledProcessError as e:
        logger.error(f"[!] Dependency installation failed: {e}")
        sys.exit(1)

def create_db():
    """
    Checks if the application database file exists, initializing the Reflex DB if not
    """
    db_file = BASE_DIR / "data" / "CH-Data.db"
    if not db_file.exists():
        try:
            logger.info("[*] Creating application database...")
            venv_py(VENV_DIR, ["-m", "reflex", "db", "init"])
        except subprocess.CalledProcessError as e:
            logger.error(f"[!] Error creating database: {e}")
            sys.exit(1)

def launch_reflex():
    """
    Launches the Reflex application
    """
    try:
        logger.info("[*] Launching application...")
        venv_py(VENV_DIR, ["-m", "reflex", "run"])
    except subprocess.CalledProcessError as e:
        logger.error(f"[!] Application crashed: {e}")
        sys.exit(1)

def main():
    # Configure the root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            # logging.FileHandler("critical_hits.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Verifying python version
    check_python_version()

    # Checking for .env config file
    check_dotenv()

    # Create Virtual Environment if missing
    create_venv()

    # Install/Update Dependencies
    install_deps()

    # Create data directories
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    # Create app database
    create_db()

    # Launch the Core App
    launch_reflex()

if __name__ == "__main__":
    main()