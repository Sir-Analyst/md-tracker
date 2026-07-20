# MD Tracker - Setup Script
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== MD Tracker Setup ===" -ForegroundColor Cyan
Write-Host ""

# 1. Create venv if not exists
$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv (Join-Path $ProjectRoot ".venv")
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
}

# 2. Install dependencies
Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
& $venvPython -m pip install -r (Join-Path $ProjectRoot "requirements.txt") -q
Write-Host "[OK] Dependencies installed" -ForegroundColor Green

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start:" -ForegroundColor White
Write-Host "  .\launch.bat" -ForegroundColor Gray
