# Build MDTracker.exe
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Building MDTracker.exe ===" -ForegroundColor Cyan

& (Join-Path $ProjectRoot ".venv\Scripts\pip.exe") install pyinstaller -q

& (Join-Path $ProjectRoot ".venv\Scripts\pyinstaller.exe") `
    --name MDTracker `
    --onefile `
    --windowed `
    --icon (Join-Path $ProjectRoot "icon.ico") `
    --add-data "app;app" `
    --add-data "icon.ico;." `
    --distpath (Join-Path $ProjectRoot "dist") `
    --workpath (Join-Path $ProjectRoot "build") `
    --specpath $ProjectRoot `
    (Join-Path $ProjectRoot "run.pyw")

Write-Host ""
Write-Host "=== Build Complete ===" -ForegroundColor Green
Write-Host "Output: dist\MDTracker.exe" -ForegroundColor Gray
