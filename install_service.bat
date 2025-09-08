@echo off
echo School Device Monitor - Service Installation
echo ============================================

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as administrator - OK
) else (
    echo ERROR: This script must be run as administrator
    pause
    exit /b 1
)

REM Create executable if it doesn't exist
if not exist "dist\detect.exe" (
    echo Creating executable...
    py -m pip install pyinstaller
    pyinstaller --onefile --name detect detect.py
    if errorlevel 1 (
        echo ERROR: Failed to create executable
        pause
        exit /b 1
    )
)

REM Download NSSM if not present
if not exist "nssm.exe" (
    echo Downloading NSSM...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip'"
    powershell -Command "Expand-Archive -Path 'nssm.zip' -DestinationPath '.' -Force"
    copy "nssm-2.24\win64\nssm.exe" "nssm.exe"
    rmdir /s /q "nssm-2.24"
    del "nssm.zip"
)

REM Install service
echo Installing School Device Monitor service...
nssm install SchoolDeviceMonitor "%~dp0dist\detect.exe"
nssm set SchoolDeviceMonitor AppDirectory "%~dp0"
nssm set SchoolDeviceMonitor Description "School Device Monitor - Process Detection Service"
nssm set SchoolDeviceMonitor Start SERVICE_AUTO_START

REM Start service
echo Starting service...
nssm start SchoolDeviceMonitor

echo.
echo Service installation complete!
echo Service name: SchoolDeviceMonitor
echo.
echo To manage the service:
echo   Start:   nssm start SchoolDeviceMonitor
echo   Stop:    nssm stop SchoolDeviceMonitor
echo   Restart: nssm restart SchoolDeviceMonitor
echo   Remove:  nssm remove SchoolDeviceMonitor confirm
echo.
pause
