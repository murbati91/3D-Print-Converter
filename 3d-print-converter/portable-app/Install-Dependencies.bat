@echo off
title 3D Print Converter - Installation
color 0B

echo ============================================
echo    3D Print Converter - First Time Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please download and install Python 3.11+ from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)

echo [OK] Python found
python --version
echo.

:: Install dependencies
echo Installing required packages...
echo.
pip install -r "%~dp0server\requirements.txt"

echo.
echo ============================================
echo    Installation Complete!
echo ============================================
echo.
echo You can now run "Start-3D-Converter.bat"
echo.
pause
