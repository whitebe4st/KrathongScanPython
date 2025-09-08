@echo off
title QR Code Generator for KrathongScanner
color 0A

echo.
echo ===================================================
echo        🚀 QR Code Generator for KrathongScanner
echo ===================================================
echo.

:MAIN_MENU
echo What would you like to do?
echo.
echo 1. Generate QR code for a tunnel URL
echo 2. Start LocalTunnel and generate QR code
echo 3. Exit
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" goto MANUAL_QR
if "%choice%"=="2" goto AUTO_TUNNEL
if "%choice%"=="3" goto EXIT
echo Invalid choice. Please try again.
goto MAIN_MENU

:MANUAL_QR
echo.
set /p url="🌐 Enter the tunnel URL: "
if "%url%"=="" (
    echo ❌ No URL provided
    goto MAIN_MENU
)

echo.
echo 📱 Generating QR code...
G:\MotionSix\KrathongScanner\venv\Scripts\python.exe G:\MotionSix\KrathongScanner\generate_qr.py "%url%"

echo.
echo Press any key to continue...
pause >nul
goto MAIN_MENU

:AUTO_TUNNEL
echo.
echo 🚇 Starting LocalTunnel...
echo 💡 Keep this window open to maintain the tunnel
echo.

start "LocalTunnel" cmd /k "npx localtunnel --port 5000 --bypass-tunnel-reminder"

echo.
echo ⏳ Waiting for tunnel to establish...
timeout /t 5 >nul

echo.
set /p tunnel_url="📝 Enter the tunnel URL from the other window: "

if not "%tunnel_url%"=="" (
    echo.
    echo 📱 Generating QR code...
    G:\MotionSix\KrathongScanner\venv\Scripts\python.exe G:\MotionSix\KrathongScanner\generate_qr.py "%tunnel_url%"
)

echo.
echo Press any key to continue...
pause >nul
goto MAIN_MENU

:EXIT
echo.
echo 👋 Thank you for using QR Code Generator!
echo.
timeout /t 2 >nul
exit
