@echo off
:: KrathongScanner Build Script
:: Compiles both Scanner and Template Management applications

echo ============================================================
echo 🏗️  KrathongScanner Build Script
echo ============================================================
echo Building Scanner_1-0 and template_management_1-0
echo ============================================================

:: Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ❌ PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ Failed to install PyInstaller
        pause
        exit /b 1
    )
    echo ✅ PyInstaller installed successfully
)

:: Ensure release directories exist
if not exist "release" mkdir release
if not exist "release\scanner" mkdir release\scanner
if not exist "release\backend" mkdir release\backend

echo.
echo 📦 Building Scanner_1-0...
echo ============================================================

:: Build the main scanner application
pyinstaller --clean --noconfirm scanner_build.spec
if errorlevel 1 (
    echo ❌ Scanner build failed
    pause
    exit /b 1
)

:: Move scanner to release/scanner
echo 📁 Moving Scanner_1-0 to release/scanner...
if exist "dist\Scanner_1-0" (
    xcopy "dist\Scanner_1-0" "release\scanner" /E /I /Y
    echo ✅ Scanner_1-0 moved to release/scanner
) else (
    echo ❌ Scanner build output not found
    pause
    exit /b 1
)

echo.
echo 📦 Building template_management_1-0...
echo ============================================================

:: Build the template creator application
pyinstaller --clean --noconfirm template_creator_build.spec
if errorlevel 1 (
    echo ❌ Template creator build failed
    pause
    exit /b 1
)

:: Move template creator to release/backend
echo 📁 Moving template_management_1-0 to release/backend...
if exist "dist\template_management_1-0" (
    xcopy "dist\template_management_1-0" "release\backend" /E /I /Y
    echo ✅ template_management_1-0 moved to release/backend
) else (
    echo ❌ Template creator build output not found
    pause
    exit /b 1
)

echo.
echo 🧹 Cleaning up build artifacts...
rmdir /s /q "build" 2>nul
rmdir /s /q "dist" 2>nul
del /q "*.spec~" 2>nul

echo.
echo ============================================================
echo ✅ Build Complete!
echo ============================================================
echo 📁 Scanner executable: release\scanner\Scanner_1-0.exe
echo 📁 Template Management: release\backend\template_management_1-0.exe
echo ============================================================

:: Show final directory structure
echo.
echo 📋 Release Directory Structure:
echo ├── release/
echo │   ├── scanner/
echo │   │   └── Scanner_1-0.exe
echo │   └── backend/
echo │       └── template_management_1-0.exe

echo.
echo 🎉 Both applications compiled successfully!
pause
