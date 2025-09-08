@echo off
echo School Device Monitor - Complete Deployment (Fixed)
echo ==================================================

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
REM Use the full path to pyinstaller
py -m PyInstaller --onefile --name detect detect.py
if errorlevel 1 (
    echo ERROR: Failed to create executable
    pause
    exit /b 1
)

echo.
echo Phase 3: Setting up Web Dashboard...
if not exist "templates" mkdir templates

echo.
echo Phase 4: Testing Basic Functionality...
echo Testing monitor...
py test_monitor.py

echo.
echo Phase 5: Starting Web Dashboard...
start "School Device Monitor Dashboard" py web_dashboard.py

echo.
echo Deployment Complete!
echo.
echo Services Available:
echo - Process Monitor: Ready to run with 'py detect.py'
echo - Web Dashboard: http://localhost:5000
echo - Event Viewer: 'py view_events.py stats'
echo.
echo Files Created:
echo - detect.exe (in dist folder)
echo - config.json (configuration)
echo - events.db (database)
echo.
echo Next Steps:
echo 1. Open http://localhost:5000 in your browser
echo 2. Run 'py detect.py' to start monitoring
echo 3. Configure email alerts in config.json if needed
echo.
pause
