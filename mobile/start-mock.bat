@echo off
echo ========================================
echo   Face Check-in System - Mock Mode
echo ========================================
echo.
echo Starting local server on port 3000...
echo.

cd /d "%~dp0"

start "" http://localhost:3000

python -m http.server 3000

pause
