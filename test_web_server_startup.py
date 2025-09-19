#!/usr/bin/env python3
"""
Test the actual web server startup as it happens in the GUI
This replicates the exact sequence from run_web_server()
"""

import os
import sys
import threading
import time

import requests

# Add the src and web directories to Python path
current_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(current_dir, "src"))
sys.path.append(os.path.join(current_dir, "web"))

from tunneling.bundled_instatunnel import (
    is_bundled_tunnel_available,
    start_bundled_tunnel,
)


def test_actual_web_server_startup():
    """Test the actual web server startup sequence"""
    print("🧪 Testing actual web server startup sequence...")

    # Import the Flask app from the web server
    from server import app

    host = "0.0.0.0"
    port = 5000

    print(f"🚀 Starting Flask server on {host}:{port}...")

    # Start Flask server in a separate thread (exactly like in run_web_server)
    def start_flask_server():
        app.run(host=host, port=port, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=start_flask_server, daemon=True)
    flask_thread.start()

    # Wait a moment for Flask server to start (exactly like in run_web_server)
    print("⏱️ Waiting 3 seconds for Flask to start...")
    time.sleep(3)

    # Test if Flask is ready
    print("🔍 Testing if Flask is ready...")
    try:
        response = requests.get(f"http://localhost:{port}", timeout=5)
        print(f"✅ Flask is ready! Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Flask is NOT ready: {e}")
        return False

    # Now test tunnel creation (exactly like in run_web_server)
    print("🚀 Starting InstaTunnel...")
    if is_bundled_tunnel_available():
        url = start_bundled_tunnel(port)
        if url:
            print(f"✅ Tunnel created: {url}")

            # Test tunnel connection
            print("🔍 Testing tunnel connection...")
            try:
                response = requests.get(url, timeout=10)
                print(f"✅ Tunnel works! Status: {response.status_code}")
                return True
            except requests.exceptions.RequestException as e:
                print(f"❌ Tunnel connection failed: {e}")
                return False
        else:
            print("❌ Failed to create tunnel")
            return False
    else:
        print("❌ Bundled tunnel not available")
        return False


if __name__ == "__main__":
    success = test_actual_web_server_startup()
    if success:
        print("🎉 Web server startup test PASSED!")
    else:
        print("💥 Web server startup test FAILED!")

    # Keep alive for a bit to see results
    print("⏱️ Keeping alive for 30 seconds to test tunnel...")
    time.sleep(30)
