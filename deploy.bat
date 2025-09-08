@echo off
echo School Device Monitor - Complete Deployment
echo ==========================================

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as administrator - OK
) else (
    echo ERROR: This script must be run as administrator
    pause
    exit /b 1
)

echo.
echo Phase 1: Installing Dependencies...
py -m pip install -r requirements.txt
py -m pip install pyinstaller flask

echo.
echo Phase 2: Creating Executable...
pyinstaller --onefile --name detect detect.py

echo.
echo Phase 3: Setting up Web Dashboard...
if not exist "templates" mkdir templates
copy "templates\dashboard.html" "templates\dashboard.html" >nul 2>&1

echo.
echo Phase 4: Installing Windows Service...
call install_service.bat

echo.
echo Phase 5: Starting Web Dashboard...
start "School Device Monitor Dashboard" py web_dashboard.py

echo.
echo Deployment Complete!
echo.
echo Services Available:
echo - Process Monitor: Running as Windows Service
echo - Web Dashboard: http://localhost:5000
echo.
echo Files Created:
echo - detect.exe (in dist folder)
echo - config.json (configuration)
echo - events.db (database)
echo.
pause
