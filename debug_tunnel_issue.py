#!/usr/bin/env python3
"""
Debug script to test tunnel functionality and identify the URL reuse issue.
"""

import os
import sys
import time
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))


def test_tunnel_creation():
    """Test the tunnel creation process to see what's happening."""

    print("🔍 Debug: Testing tunnel creation process...")
    print("=" * 60)

    try:
        # Import the web server module
        from web.server import public_url, start_instatunnel

        print(f"1. Current global public_url: {public_url}")
        print()

        # Test 1: Call start_instatunnel first time
        print("🧪 Test 1: First tunnel creation attempt")
        print("-" * 40)
        url1 = start_instatunnel(5000)
        print(f"Result: {url1}")
        print()

        # Check global state after first call
        print(f"Global public_url after first call: {public_url}")
        print()

        # Test 2: Call start_instatunnel second time (should reuse)
        print("🧪 Test 2: Second tunnel creation attempt (should reuse)")
        print("-" * 40)
        url2 = start_instatunnel(5000)
        print(f"Result: {url2}")
        print()

        # Check if URLs are the same
        print(f"URLs match: {url1 == url2}")
        print()

        # Test 3: Test the URL accessibility
        print("🧪 Test 3: Testing URL accessibility")
        print("-" * 40)
        if url1:
            try:
                import urllib.request

                with urllib.request.urlopen(url1, timeout=10) as response:
                    print(f"✅ URL {url1} is accessible (status: {response.status})")
            except Exception as e:
                print(f"❌ URL {url1} is NOT accessible: {e}")
        else:
            print("❌ No URL to test")
        print()

        # Test 4: Check bundled tunnel status
        print("🧪 Test 4: Checking bundled tunnel status")
        print("-" * 40)
        try:
            from tunneling.bundled_instatunnel import (
                get_bundled_tunnel_url,
                is_bundled_tunnel_available,
                is_bundled_tunnel_running,
                test_bundled_tunnel_connection,
            )

            print(f"Bundled tunnel available: {is_bundled_tunnel_available()}")
            print(f"Bundled tunnel running: {is_bundled_tunnel_running()}")
            print(f"Bundled tunnel URL: {get_bundled_tunnel_url()}")
            print(f"Bundled tunnel connection test: {test_bundled_tunnel_connection()}")

        except Exception as e:
            print(f"❌ Error checking bundled tunnel status: {e}")

        print()
        print("=" * 60)
        print("🎯 Summary:")
        print(f"- First URL: {url1}")
        print(f"- Second URL: {url2}")
        print(f"- URLs are identical: {url1 == url2}")
        print(f"- Global state persists: {public_url is not None}")

    except Exception as e:
        print(f"❌ Error during tunnel testing: {e}")
        import traceback

        traceback.print_exc()


def test_fresh_tunnel_creation():
    """Test creating a fresh tunnel by clearing global state."""

    print("\n🔍 Debug: Testing fresh tunnel creation...")
    print("=" * 60)

    try:
        # Import and reset global state
        import web.server

        web.server.public_url = None

        print("✅ Global public_url reset to None")

        # Now test tunnel creation
        from web.server import start_instatunnel

        print("🧪 Testing tunnel creation with clean state")
        print("-" * 40)
        url = start_instatunnel(5000)
        print(f"Fresh tunnel URL: {url}")

        if url:
            # Test accessibility
            try:
                import urllib.request

                with urllib.request.urlopen(url, timeout=10) as response:
                    print(
                        f"✅ Fresh URL {url} is accessible (status: {response.status})"
                    )
            except Exception as e:
                print(f"❌ Fresh URL {url} is NOT accessible: {e}")

    except Exception as e:
        print(f"❌ Error during fresh tunnel testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 KrathongScanner Tunnel Debug Tool")
    print("=" * 60)

    # Test the current behavior
    test_tunnel_creation()

    # Test with fresh state
    test_fresh_tunnel_creation()

    print("\n✅ Debug testing complete!")
