from pathlib import Path

MIN_PYTHON_VERSION = (3, 12)
APP_NAME = "Critical Hits"
BASE_DIR = Path(__file__).resolve().parent.parent
VENV_DIR = BASE_DIR / ".venv"
DATA_DIR = BASE_DIR / "data"
IMG_DIR = BASE_DIR / "uploaded_files" # Matches the output of rx.get_upload_dir()
ASSETS_DIR = BASE_DIR / "assets"
BASE_URL = "http://localhost:3000"

DEFAULT_IMAGE = "/images/noimg.jpg"

ROUTES = {
    "home": "/",
    "list": "/collection",
    "battle": "/arena",
    "login": "/login",
    "export": "/export"
}

# Image sizes defined by the IGDB API
IMG_SIZES = {
    "small_cover": "cover_small",     # 90 x 128
    "lg_cover": "cover_big",          # 264 x 374
    "small_screen": "screenshot_med", # 569 x 320
    "med_screen": "screenshot_big",   # 889 x 500
    "lg_screen": "screenshot_huge",   # 1280 x 720
    "720": "720p",                    # 1280 x 720
    "1080": "1080p",                  # 1920 x 1080
    "micro": "micro",                 # 35 x 35
    "thumb": "thumb",                 # 90 x 90
    "logo": "logo_med"                # 284 x 160
}