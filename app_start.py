import sys
import os
import subprocess
import venv
import re
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

    # Checking for .env config file
    env_path = BASE_DIR / ".env"
    env_template = (
        "REFLEX_HOT_RELOAD_OVERRIDE_PATHS=app\n\n"
        "# Add your API key here\n"
        "RAWG_API_KEY=\n"
    )

    if not env_path.exists():
        print("[*] Configuration file (.env) not found. Creating template...")
        with open(env_path, "w") as f:
            f.write(env_template)
        print(f"[!] A template .env file has been created at {env_path}")
        print("[!] Before starting: Open this file, add your RAWG_API_KEY, and save it.")
        print("[!] Then, run the application again.\n")
        sys.exit(0)
    else:
        # Check if the API key is actually defined in .env
        with open(env_path, "r") as f:
            env_content = f.read()
            if not re.search(r"RAWG_API_KEY\s*=\s*\S+", env_content):
                print("[!] ERROR: RAWG_API_KEY is missing from your .env file.")
                print(f"Please edit {env_path} and add your key.")
                sys.exit(1)

    # Create Virtual Environment if missing
    if not VENV_DIR.exists():
        print(f"[*] Creating virtual environment in {VENV_DIR}...")
        venv.create(VENV_DIR, with_pip=True)

    # Install/Update Dependencies
    try:
        print("[*] Installing dependencies...")
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

    db_file = BASE_DIR / "data" / "gamerank.db"
    if not db_file.exists():
        try:
            print("[*] Creating application database...")
            run_in_venv(VENV_DIR, ["-m", "reflex", "db", "init"])
        except subprocess.CalledProcessError as e:
            print(f"[!] Error creating database: {e}")
            sys.exit(1)

    # Launch the Core App
    try:
        print("[*] Launching application...")
        run_in_venv(VENV_DIR, ["-m", "reflex", "run"])
    except subprocess.CalledProcessError as e:
        print(f"[!] Application crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()