#!/usr/bin/env python3
"""
Test the Flask server startup timing issue
This script will test if Flask server is ready when tunnel starts
"""

import threading
import time

import requests
from flask import Flask


def test_flask_startup_timing():
    """Test how long Flask takes to start"""
    print("🧪 Testing Flask startup timing...")

    app = Flask(__name__)

    @app.route("/")
    def home():
        return "Flask is ready!"

    def start_flask():
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

    # Start Flask in thread
    print("🚀 Starting Flask server...")
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # Test different wait times
    for wait_time in [1, 2, 3, 4, 5]:
        print(f"⏱️ Waiting {wait_time} seconds...")
        time.sleep(1)  # Wait 1 more second

        try:
            response = requests.get("http://localhost:5000", timeout=2)
            if response.status_code == 200:
                print(f"✅ Flask ready after {wait_time} seconds!")
                return wait_time
        except requests.exceptions.RequestException as e:
            print(f"❌ Flask not ready at {wait_time}s: {e}")

    print("❌ Flask never became ready!")
    return None


if __name__ == "__main__":
    test_flask_startup_timing()
