from pathlib import Path

MIN_PYTHON_VERSION = (3, 12)
APP_NAME = "Critical Hits"
BASE_DIR = Path(__file__).resolve().parent.parent
VENV_DIR = BASE_DIR / ".venv"
DATA_DIR = BASE_DIR / "data"
IMG_DIR = BASE_DIR / "uploaded_files" # Matches the output of rx.get_upload_dir()
ASSETS_DIR = BASE_DIR / "assets"