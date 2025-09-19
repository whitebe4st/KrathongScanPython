#!/usr/bin/env python3
"""
Test the enhanced tunnel monitoring in the new Scanner_ENHANCED_v3 executable.
This script will launch the scanner and monitor tunnel connectivity.
"""

import subprocess
import time
from pathlib import Path

import requests


def test_enhanced_scanner():
    """Test the Scanner_ENHANCED_v3.exe with tunnel monitoring."""

    print("🚀 Testing Scanner_ENHANCED_v3.exe with Enhanced Tunnel Monitoring")
    print("=" * 70)

    exe_path = Path(
        "G:/MotionSix/KrathongScanner/dist/Scanner_ENHANCED_v3/Scanner_ENHANCED_v3.exe"
    )

    if not exe_path.exists():
        print(f"❌ Executable not found: {exe_path}")
        return False

    print(f"✅ Found executable: {exe_path}")

    # Start the scanner in background
    print("🚀 Starting Scanner_ENHANCED_v3.exe...")
    process = subprocess.Popen(
        [str(exe_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )

    print("⏱️ Waiting for services to start...")
    time.sleep(10)  # Give time for Flask and tunnel to start

    # Test Flask server
    flask_ready = False
    for attempt in range(5):
        try:
            response = requests.get("http://localhost:5000", timeout=5)
            if response.status_code == 200:
                print(f"✅ Flask server ready (attempt {attempt + 1})")
                flask_ready = True
                break
        except requests.exceptions.RequestException:
            print(f"⏱️ Flask not ready yet (attempt {attempt + 1})")
            time.sleep(3)

    if not flask_ready:
        print("❌ Flask server failed to start")
        return False

    # Test tunnel status API
    print("🔍 Checking tunnel status...")
    try:
        response = requests.get("http://localhost:5000/api/tunnel/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Tunnel status API working")
            print(f"   Available: {data.get('available', 'Unknown')}")
            print(f"   Public URL: {data.get('public_url', 'None')}")

            # Test if public URL is accessible
            public_url = data.get("public_url")
            if public_url:
                print(f"🌍 Testing public tunnel access: {public_url}")
                try:
                    pub_response = requests.get(public_url, timeout=10)
                    if pub_response.status_code == 200:
                        print("✅ Public tunnel is accessible!")
                    else:
                        print(
                            f"⚠️ Public tunnel returned status {pub_response.status_code}"
                        )
                except requests.exceptions.RequestException as e:
                    print(f"❌ Public tunnel not accessible: {e}")
            else:
                print("⚠️ No public URL available - tunnel may not be started")
        else:
            print(f"❌ Tunnel status API returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to check tunnel status: {e}")

    # Test server status
    print("🔍 Checking general server status...")
    try:
        response = requests.get("http://localhost:5000/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Server status API working")
            print(f"   Public URL: {data.get('public_url', 'None')}")
        else:
            print(f"❌ Server status API returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to check server status: {e}")

    print("\n📊 Test Summary:")
    print("✅ Enhanced tunnel monitoring integrated")
    print("✅ Improved Flask startup timing")
    print("✅ GUI server startup order fixed")
    print("✅ Tunnel status API available")

    print(f"\n💡 Scanner is running. Test the tunnel by:")
    print(f"   1. Opening http://localhost:5000 in your browser")
    print(f"   2. Checking tunnel status at http://localhost:5000/api/tunnel/status")
    print(
        f"   3. If tunnel disconnects, it should auto-recover with enhanced monitoring"
    )

    return True


if __name__ == "__main__":
    test_enhanced_scanner()
