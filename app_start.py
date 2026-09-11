import sys
import os
import subprocess
import venv
from pathlib import Path
from app.util import *

def check_python_version():
    if sys.version_info < MIN_PYTHON_VERSION:
        print(f"\n[!] ERROR: {APP_NAME} requires Python {'.'.join(map(str, MIN_PYTHON_VERSION))}+")
        print(f"Your version: {sys.version.split()[0]}")
        print("Please update Python and try again.\n")
        sys.exit(1)

def run_in_venv(venv_path: Path, command: list):
    if os.name == 'nt':
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        
    if not python_exe.exists():
        print(f"[!] Error: Could not find python executable in {venv_path}")
        sys.exit(1)
        
    full_command = [str(python_exe)] + command
    return subprocess.run(full_command, check=True)

def main():
    check_python_version()

    # Create Virtual Environment if missing
    if not VENV_DIR.exists():
        print(f"[*] Creating virtual environment in {VENV_DIR}...")
        venv.create(VENV_DIR, with_pip=True)

    # Install/Update Dependencies
    print("[*] Installing dependencies...")
    try:
        req_file = BASE_DIR / "requirements.txt"
        if req_file.exists():
            run_in_venv(VENV_DIR, ["-m", "pip", "install", "-q", "-r", str(req_file)])
        else:
            # If requirements.txt doesn't exist, we fallback to a direct install
            print("[!] No requirements.txt found. Installing core packages...")
            run_in_venv(VENV_DIR, ["-m", "pip", "install", "-q", "reflex", "sqlalchemy", "requests"])
    except subprocess.CalledProcessError as e:
        print(f"[!] Dependency installation failed: {e}")
        sys.exit(1)

    # Create data directories
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    # Launch the Core App
    try:
        run_in_venv(VENV_DIR, ["-m", "reflex", "run"])
    except subprocess.CalledProcessError as e:
        print(f"[!] Application crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()