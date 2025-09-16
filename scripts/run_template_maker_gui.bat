@echo off
title Template Maker GUI
echo 🎨 Starting Template Maker GUI...
echo ================================

cd /d "%~dp0\.."

echo.
echo Starting Template Maker GUI...
echo.

python apps/template_maker/main.py

echo.
echo Template Maker closed.
pause
