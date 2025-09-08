@echo off
echo ========================================
echo    KrathongScanner Mall Deployment
echo ========================================
echo.

echo 🏬 Setting up for mall deployment...
echo.

REM Check if ngrok is available
ngrok version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ ngrok found!
    echo 🔧 Starting server with ngrok tunnel...
    echo.

    REM Start ngrok in background
    start /B ngrok http 5000 --log=stdout > ngrok.log 2>&1

    REM Wait a moment for ngrok to start
    timeout /t 5 /nobreak >nul

    REM Start the Python server
    echo 🚀 Starting KrathongScanner Web Server...
    python web/server.py

) else (
    echo ❌ ngrok not found!
    echo.
    echo 💡 Quick setup:
    echo 1. Download ngrok from: https://ngrok.com/download
    echo 2. Extract ngrok.exe to this folder or add to PATH
    echo 3. Sign up at ngrok.com and get auth token
    echo 4. Run: ngrok authtoken YOUR_TOKEN
    echo 5. Run this script again
    echo.
    pause
)

echo.
echo 🔄 Cleaning up...
taskkill /f /im ngrok.exe >nul 2>&1
echo ✅ Done!
pause
