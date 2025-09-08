@echo off
echo ========================================
echo KrathongScanner Web Server Launcher
echo ========================================
echo.

REM Change to the web directory
cd /d "%~dp0web"

echo Starting KrathongScanner Web Server...
echo.
echo Features:
echo - Mobile upload interface
echo - Automatic image processing
echo - Real-time progress tracking
echo - Ngrok tunnel for public access
echo - QR code generation for mobile
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist "..\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\venv\Scripts\activate.bat
)

REM Install dependencies if needed
echo Checking dependencies...
python -c "import flask" 2>nul || pip install flask
python -c "import qrcode" 2>nul || pip install qrcode
python -c "import requests" 2>nul || pip install requests

echo.
echo Starting server on http://localhost:5000
echo.

REM Start the Flask server
python server.py

echo.
echo Server stopped.
pause
