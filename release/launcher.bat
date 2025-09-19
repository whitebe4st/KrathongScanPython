@echo off
:: KrathongScanner Application Launcher

echo ============================================================
echo 🎯 KrathongScanner Applications
echo ============================================================
echo.
echo Choose an application to launch:
echo.
echo [1] Scanner_1-0          - Main scanning application
echo [2] template_management_1-0 - Template creation and management
echo [3] Exit
echo.

:menu
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo 🚀 Launching Scanner_1-0...
    cd /d "%~dp0scanner"
    start "" "Scanner_1-0.exe"
    goto end
)

if "%choice%"=="2" (
    echo.
    echo 🚀 Launching template_management_1-0...
    cd /d "%~dp0backend"
    start "" "template_management_1-0.exe"
    goto end
)

if "%choice%"=="3" (
    goto end
)

echo Invalid choice. Please enter 1, 2, or 3.
goto menu

:end
echo.
echo ✅ Application launched successfully!
pause
