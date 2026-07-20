import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "md_tracker.db"
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"

HOST = "127.0.0.1"
PORT = 8080

SCAN_DIRS = [
    str(Path.home() / "Desktop"),
    r"C:\Desktop",
]
