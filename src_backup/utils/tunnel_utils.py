"""
Node.js/NPX Detection and Bundling Utilities for KrathongScanner

This module handles Node.js detection and provides fallback solutions
for when NPX is not available (like in Python executables).
"""

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def detect_nodejs():
    """Detect if Node.js and NPX are available."""
    try:
        # Check Node.js
        node_result = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, timeout=5
        )
        node_available = node_result.returncode == 0

        # Check NPX
        npx_result = subprocess.run(
            ["npx", "--version"], capture_output=True, text=True, timeout=5
        )
        npx_available = npx_result.returncode == 0

        return {
            "node_available": node_available,
            "npx_available": npx_available,
            "node_version": node_result.stdout.strip() if node_available else None,
            "npx_version": npx_result.stdout.strip() if npx_available else None,
        }

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return {
            "node_available": False,
            "npx_available": False,
            "node_version": None,
            "npx_version": None,
        }


def get_bundled_localtunnel_path():
    """Get path to bundled LocalTunnel executable (if available)."""
    # Check if we're running from a PyInstaller bundle
    if hasattr(sys, "_MEIPASS"):
        bundled_path = os.path.join(sys._MEIPASS, "localtunnel", "localtunnel.exe")
        if os.path.exists(bundled_path):
            return bundled_path

    # Check for bundled version in application directory
    app_dir = Path(__file__).parent.parent
    bundled_paths = [
        app_dir / "bundled" / "localtunnel" / "localtunnel.exe",
        app_dir / "bundled" / "localtunnel.exe",
        app_dir / "localtunnel.exe",
    ]

    for path in bundled_paths:
        if path.exists():
            return str(path)

    return None


def start_tunnel_with_fallback(port=5000):
    """Start tunnel with multiple fallback methods."""
    # Method 1: Try NPX LocalTunnel
    nodejs_info = detect_nodejs()

    if nodejs_info["npx_available"]:
        try:
            print("🚇 Starting LocalTunnel via NPX...")
            process = subprocess.Popen(
                ["npx", "localtunnel", "--port", str(port), "--bypass-tunnel-reminder"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for tunnel URL
            for _ in range(30):
                line = process.stdout.readline()
                if line and "your url is:" in line:
                    import re

                    url_match = re.search(r"https://[^\s]+\.loca\.lt", line)
                    if url_match:
                        return url_match.group(0), process

            return None, process

        except Exception as e:
            print(f"NPX LocalTunnel failed: {e}")

    # Method 2: Try bundled LocalTunnel
    bundled_path = get_bundled_localtunnel_path()
    if bundled_path:
        try:
            print("🚇 Starting bundled LocalTunnel...")
            process = subprocess.Popen(
                [bundled_path, "--port", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for tunnel URL (similar to NPX method)
            for _ in range(30):
                line = process.stdout.readline()
                if line and "your url is:" in line:
                    import re

                    url_match = re.search(r"https://[^\s]+\.loca\.lt", line)
                    if url_match:
                        return url_match.group(0), process

            return None, process

        except Exception as e:
            print(f"Bundled LocalTunnel failed: {e}")

    # Method 3: Try other tunnel services (ngrok, bore, etc.)
    return try_alternative_tunnels(port)


def try_alternative_tunnels(port=5000):
    """Try alternative tunnel services."""
    # Try ngrok if available
    try:
        ngrok_path = shutil.which("ngrok")
        if ngrok_path:
            print("🚇 Trying ngrok...")
            process = subprocess.Popen(
                ["ngrok", "http", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            # Note: ngrok requires different URL extraction logic
            return None, process  # Simplified for now
    except Exception:
        pass

    print("❌ No tunnel service available")
    return None, None


def download_localtunnel_binary():
    """Download and prepare LocalTunnel binary for bundling."""
    try:
        import requests

        print("📥 Downloading LocalTunnel binary...")

        # This would download a standalone LocalTunnel binary
        # For now, we'll provide instructions instead
        return False

    except ImportError:
        print("❌ Requests library required for downloading")
        return False
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False


def create_tunnel_installer():
    """Create a simple tunnel installer for deployment."""
    installer_script = """
@echo off
title LocalTunnel Installer for KrathongScanner
echo Installing LocalTunnel for KrathongScanner...
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Node.js is not installed!
    echo.
    echo Please install Node.js from: https://nodejs.org
    echo Then run this installer again.
    pause
    exit /b 1
)

echo Node.js detected!
echo Installing LocalTunnel globally...
npm install -g localtunnel

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ LocalTunnel installed successfully!
    echo.
    echo You can now use the "Generate QR Link" feature in KrathongScanner.
) else (
    echo.
    echo ❌ Installation failed!
    echo Please check your internet connection and try again.
)

echo.
pause
"""

    installer_path = Path(__file__).parent.parent / "install_localtunnel.bat"

    try:
        with open(installer_path, "w") as f:
            f.write(installer_script)
        print(f"✅ Tunnel installer created: {installer_path}")
        return str(installer_path)
    except Exception as e:
        print(f"❌ Failed to create installer: {e}")
        return None


if __name__ == "__main__":
    # Test the detection system
    print("🔍 Testing Node.js/NPX detection...")

    info = detect_nodejs()
    print(f"Node.js available: {info['node_available']}")
    print(f"NPX available: {info['npx_available']}")

    if info["node_available"]:
        print(f"Node.js version: {info['node_version']}")
    if info["npx_available"]:
        print(f"NPX version: {info['npx_version']}")

    bundled = get_bundled_localtunnel_path()
    if bundled:
        print(f"Bundled LocalTunnel: {bundled}")
    else:
        print("No bundled LocalTunnel found")

    # Create installer
    installer = create_tunnel_installer()
    if installer:
        print(f"Installer ready: {installer}")
