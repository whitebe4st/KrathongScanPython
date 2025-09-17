@echo off
REM Unified Template Creator Launcher
REM Launch the unified template creation application

echo Starting Unified Template Creator...
echo.

cd /d "G:\MotionSix\KrathongScanner"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Run the unified template creator
echo Launching unified template creator GUI...
python apps\unified_template_creator\main.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start unified template creator
    echo Check the logs for more details
    pause
    exit /b 1
)

echo.
echo Unified Template Creator closed successfully
pause
