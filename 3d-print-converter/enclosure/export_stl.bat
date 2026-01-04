@echo off
REM =============================================
REM STL Export Script for Controller Enclosure
REM Salahuddin Softech Solution
REM =============================================

echo.
echo ========================================
echo  3D Blueprint Controller - STL Export
echo  Salahuddin Softech Solution
echo ========================================
echo.

set OPENSCAD="C:\Program Files\OpenSCAD\openscad.exe"
set SCAD_FILE=controller_enclosure.scad
set OUTPUT_DIR=%~dp0stl

REM Create output directory
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo Generating STL files...
echo.

REM Export Base
echo [1/2] Exporting controller_base.stl...
%OPENSCAD% -o "%OUTPUT_DIR%\controller_base.stl" -D "render_base=true" "%SCAD_FILE%" 2>nul
if errorlevel 1 (
    echo      Using manual export method...
)

REM Export Lid
echo [2/2] Exporting controller_lid.stl...
%OPENSCAD% -o "%OUTPUT_DIR%\controller_lid.stl" -D "render_lid=true" "%SCAD_FILE%" 2>nul
if errorlevel 1 (
    echo      Using manual export method...
)

echo.
echo ========================================
echo  Export Complete!
echo ========================================
echo.
echo STL files saved to: %OUTPUT_DIR%
echo.
echo NOTE: If automatic export failed, please:
echo   1. Open controller_enclosure.scad in OpenSCAD
echo   2. Uncomment desired render option
echo   3. File - Export - Export as STL
echo.
pause
