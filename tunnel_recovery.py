#!/usr/bin/env python3
"""
Tunnel Recovery Tool - Restart web server and tunnel when they stop
"""

import os
import subprocess
import sys
import threading
import time

import requests

# Add paths
current_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(current_dir, "web"))
sys.path.append(os.path.join(current_dir, "src"))


def restart_web_server():
    """Restart the web server with tunnel"""
    print("🚀 Restarting web server and tunnel...")

    try:
        # Import the web server
        from server import run_web_server

        print("✅ Imported web server module")

        # Start in background thread so this script doesn't hang
        def start_server():
            try:
                print("🌟 Starting web server in background...")
                run_web_server(port=5000, results_folder="./output")
            except Exception as e:
                print(f"❌ Server error: {e}")

        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()

        print("⏱️ Waiting for server to start...")

        # Wait and test if it's working
        max_wait = 30  # Maximum 30 seconds
        for i in range(max_wait):
            time.sleep(1)
            try:
                response = requests.get("http://localhost:5000", timeout=2)
                if response.status_code == 200:
                    print(f"✅ Web server started successfully! (after {i+1} seconds)")
                    print("🌐 Check the console for tunnel URL")
                    return True
            except:
                pass

            if i % 5 == 4:  # Every 5 seconds
                print(f"⏱️ Still waiting... ({i+1}/{max_wait})")

        print("❌ Web server failed to start within 30 seconds")
        return False

    except Exception as e:
        print(f"❌ Failed to restart web server: {e}")
        return False


def quick_fix():
    """Quick fix for tunnel not connected error"""
    print("🔧 Tunnel Quick Fix Tool")
    print("=" * 30)

    # Run diagnostics first
    print("1️⃣ Running diagnostics...")
    try:
        from quick_tunnel_check import check_tunnel_status

        check_tunnel_status()
    except:
        print("⚠️ Could not run full diagnostics")

    print("\n2️⃣ Attempting to restart web server...")
    success = restart_web_server()

    if success:
        print("\n✅ Web server restart completed!")
        print("💡 Your tunnel should now be working.")
        print("🎯 Look for the tunnel URL in the console output above.")
    else:
        print("\n❌ Web server restart failed!")
        print("💡 Try manually starting web server from Scanner GUI:")
        print("   1. Open Scanner application")
        print("   2. Click 'Start Web Server' button")
        print("   3. Wait for tunnel URL to appear")


if __name__ == "__main__":
    quick_fix()

    # Keep script alive for a few seconds to see results
    print("\n⏱️ Keeping script alive for 10 seconds...")
    time.sleep(10)
    print("🏁 Quick fix complete!")
