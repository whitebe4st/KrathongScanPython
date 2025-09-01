@echo off
echo Starting KrathongScanner...
echo.
echo Available modes:
echo   - UI Mode (default): Just run the executable
echo   - Command Line: KrathongScanner.exe --mode [ui|webcam|auto]
echo.
echo Starting in UI mode...
echo.

cd /d "%~dp0"
start "" "dist\KrathongScanner.exe"

echo KrathongScanner started!
pause

