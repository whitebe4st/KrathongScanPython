@echo off
title Auto QR Generator for KrathongScanner
echo 🚀 Auto QR Generator for KrathongScanner
echo ========================================

:DETECT_TUNNEL
echo 🔍 Detecting LocalTunnel URL...

REM Start LocalTunnel and capture output
for /f "tokens=*" %%i in ('npx localtunnel --port 5000 --bypass-tunnel-reminder ^| findstr "your url is:"') do (
    set TUNNEL_OUTPUT=%%i
)

REM Extract the URL from the output
for /f "tokens=4" %%a in ("%TUNNEL_OUTPUT%") do set TUNNEL_URL=%%a

if defined TUNNEL_URL (
    echo ✅ Tunnel URL detected: %TUNNEL_URL%

    REM Update the server with the new URL
    echo 📱 Updating server and generating QR codes...

    curl -X POST http://localhost:5000/update_tunnel_url ^
         -H "Content-Type: application/json" ^
         -d "{\"url\":\"%TUNNEL_URL%\"}"

    if %ERRORLEVEL% EQU 0 (
        echo ✅ QR codes generated successfully!
        echo 🏬 Mall QR code ready for printing!
    ) else (
        echo ❌ Failed to update server
    )
) else (
    echo ⚠️ No tunnel URL detected
    echo 💡 Make sure LocalTunnel is running: npx localtunnel --port 5000 --bypass-tunnel-reminder
)

echo.
echo Press any key to detect again, or Ctrl+C to exit...
pause >nul
goto DETECT_TUNNEL
