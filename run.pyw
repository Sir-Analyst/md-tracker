import subprocess
import sys
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PYTHON = str(BASE_DIR / ".venv" / "Scripts" / "python.exe")
HOST = "127.0.0.1"
PORT = 8080
URL = f"http://{HOST}:{PORT}"


def main():
    proc = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "app.main:app", "--host", HOST, "--port", str(PORT)],
        cwd=str(BASE_DIR),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(2)
    webbrowser.open(URL)

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    main()
