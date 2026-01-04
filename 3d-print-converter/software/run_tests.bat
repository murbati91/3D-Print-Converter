@echo off
REM Quick test runner for API settings test suite
REM This script checks if the server is running and runs tests

echo ======================================================================
echo 3D ESP-Print API Settings Test Runner
echo ======================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python or add it to your PATH
    pause
    exit /b 1
)

REM Check if server is running
echo Checking if server is running on http://localhost:8000...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: Server does not appear to be running!
    echo.
    echo Please start the server first:
    echo   python server.py
    echo.
    echo Press any key to try running tests anyway, or Ctrl+C to cancel...
    pause >nul
)

echo.
echo Running API settings tests...
echo ======================================================================
echo.

REM Run the tests
python test_api_settings.py

REM Check result
if errorlevel 1 (
    echo.
    echo ======================================================================
    echo Tests FAILED - Please review the output above
    echo ======================================================================
    pause
    exit /b 1
) else (
    echo.
    echo ======================================================================
    echo Tests PASSED - All tests completed successfully
    echo ======================================================================
    pause
    exit /b 0
)
