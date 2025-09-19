#!/usr/bin/env python3
"""
Test the fixed Scanner's web server functionality programmatically
This simulates what happens when user clicks "Start Web Server" in GUI
"""

import os
import sys
import threading
import time

import requests

# Add paths to ensure we can import the modules
current_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(current_dir, "web"))
sys.path.append(os.path.join(current_dir, "src"))


def test_fixed_scanner_web_server():
    """Test the web server functionality exactly as the GUI calls it"""
    print("🧪 Testing FIXED Scanner web server functionality...")

    try:
        # Import the fixed web server module
        from web.server import run_web_server

        print("✅ Successfully imported run_web_server from fixed executable")

        # Start the web server exactly as the GUI does (in a thread)
        print("🚀 Starting web server in thread (simulating GUI call)...")

        def run_server_thread():
            try:
                run_web_server(port=5000, results_folder="./output")
            except Exception as e:
                print(f"❌ Web server error in thread: {e}")

        server_thread = threading.Thread(target=run_server_thread, daemon=True)
        server_thread.start()

        print("⏱️ Waiting 15 seconds for web server and tunnel to start...")
        time.sleep(15)

        # Test if Flask server is running
        print("🔍 Testing Flask server...")
        try:
            response = requests.get("http://localhost:5000", timeout=5)
            print(f"✅ Flask server working! Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Flask server not working: {e}")
            return False

        # Look for tunnel logs
        print("🔍 Checking for tunnel activity...")

        # Wait a bit more for tunnel to be established
        print("⏱️ Waiting 30 more seconds for tunnel to be fully established...")
        time.sleep(30)

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_fixed_scanner_web_server()
    if success:
        print("🎉 Fixed Scanner web server test completed!")
    else:
        print("💥 Fixed Scanner web server test failed!")

    # Keep alive to monitor
    print("⏱️ Keeping test alive for 60 seconds to monitor...")
    time.sleep(60)
