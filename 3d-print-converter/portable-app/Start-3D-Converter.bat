@echo off
title 3D Print Converter
color 0A

echo ============================================
echo    3D Print Converter - Starting...
echo ============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

:: Set paths
set "APP_DIR=%~dp0"
set "SERVER_DIR=%APP_DIR%server"

:: Check if dependencies are installed
echo [1/3] Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install fastapi uvicorn python-multipart ezdxf trimesh numpy shapely svgpathtools rich
)

:: Start the server in background
echo [2/3] Starting conversion server...
start /min cmd /c "cd /d "%SERVER_DIR%" && python server.py"

:: Wait for server to start
echo [3/3] Waiting for server...
timeout /t 3 /nobreak >nul

:: Open the web app
echo.
echo ============================================
echo    Server running at http://localhost:8000
echo    Opening 3D Print Converter...
echo ============================================
echo.
start "" "%APP_DIR%3D-Converter-App.html"

echo Press any key to stop the server and exit...
pause >nul

:: Kill the server
taskkill /f /im python.exe /fi "WINDOWTITLE eq *server*" >nul 2>&1
echo Server stopped. Goodbye!
