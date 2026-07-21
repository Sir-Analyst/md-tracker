import subprocess
import sys
import time
import webbrowser
import threading
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

HOST = "127.0.0.1"
PORT = 8080
URL = f"http://{HOST}:{PORT}"


def start_server():
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, log_level="error")


def main():
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    time.sleep(2)
    webbrowser.open(URL)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
