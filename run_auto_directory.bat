@echo off
echo KrathongScanner - Auto-Directory Mode
echo =====================================
echo.
echo This mode will monitor a directory for new krathong images
echo and automatically process them using the same pipeline
echo as Import and Webcam modes.
echo.
echo Available options:
echo   1. Use the main application: main.py --mode auto-directory
echo   2. Use standalone script: run_auto_directory.py
echo   3. Use with command line arguments
echo.
echo Examples:
echo   python main.py --mode auto-directory
echo   python main.py --mode auto-directory --input-dir "C:\MyKrathongs" --output-dir "C:\Processed"
echo   python run_auto_directory.py
echo.
pause
