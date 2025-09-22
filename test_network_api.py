#!/usr/bin/env python3
"""
Test script for KrathongScanner network API endpoints
"""

import json
import os
import sys
import threading
import time

import requests


def start_minimal_server():
    """Start the Flask server in minimal mode"""
    # Add the web directory to path
    web_dir = os.path.join(os.path.dirname(__file__), "web")
    sys.path.insert(0, web_dir)

    # Import the Flask app
    from server import app

    # Start server in background thread
    def run_server():
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(2)
    return True


def test_api_endpoints():
    """Test the network API endpoints"""
    base_url = "http://localhost:5000"

    print("🧪 Testing KrathongScanner Network API Endpoints")
    print("=" * 50)

    # Test 1: Latest scan endpoint
    print("\n1. Testing /api/latest_scan endpoint...")
    try:
        response = requests.get(f"{base_url}/api/latest_scan", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Download endpoint (should fail without filename)
    print("\n2. Testing /api/download/<filename> endpoint...")
    try:
        response = requests.get(f"{base_url}/api/download/test.png", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   Success: Image download endpoint working")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n✅ API testing complete!")


if __name__ == "__main__":
    print("🚀 Starting minimal Flask server for testing...")
    if start_minimal_server():
        print("✅ Server started, testing API endpoints...")
        test_api_endpoints()
    else:
        print("❌ Failed to start server")
