@echo off
cd /d "%~dp0"
echo Starting MD Tracker...
echo Dashboard: http://127.0.0.1:8080
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
