@echo off
echo Starting KrathongScanner...
echo.
echo Make sure you have the following folder structure:
echo dist/
echo   KrathongScanner.exe
echo   data/
echo     markers/
echo       templates/
echo         mask1_final.png
echo         mask2_final.png
echo         mask3_final.png
echo         mask4_final.png
echo     processed_images/
echo.
echo Starting application...
cd /d "%~dp0dist"
KrathongScanner.exe --mode ui
pause
