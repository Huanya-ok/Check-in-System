@echo off
echo ========================================
echo   Testing Mock Mode Setup
echo ========================================
echo.

cd /d "%~dp0"

echo Checking required files...
echo.

if exist "js\config.js" (
    echo [OK] config.js found
) else (
    echo [ERROR] config.js not found
)

if exist "js\mock-data.js" (
    echo [OK] mock-data.js found
) else (
    echo [ERROR] mock-data.js not found
)

if exist "js\common.js" (
    echo [OK] common.js found
) else (
    echo [ERROR] common.js not found
)

if exist "index.html" (
    echo [OK] index.html found
) else (
    echo [ERROR] index.html not found
)

echo.
echo Checking configuration...
findstr /C:"MOCK_MODE: true" js\config.js >nul
if %errorlevel% equ 0 (
    echo [OK] MOCK_MODE is enabled
) else (
    echo [WARNING] MOCK_MODE may not be enabled, please check config.js
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo To start Mock Mode:
echo   1. Double-click start-mock.bat
echo   2. Or run: python -m http.server 3000
echo   3. Open browser: http://localhost:3000
echo.
echo Test accounts:
echo   Student: zhangsan / 123456
echo   Student: lisi / 123456
echo   Teacher: teacher / teacher123
echo.
pause
