#!/usr/bin/env python3
"""
Simple script to test tunnel from within the executable context.
This will be embedded in the Scanner itself.
"""

import os
import sys
from pathlib import Path


def test_tunnel_in_executable():
    """Test tunnel when actually running from the Scanner executable."""

    print("🔍 Testing tunnel in executable mode...")
    print(f"Frozen: {getattr(sys, 'frozen', False)}")
    print(f"Executable: {sys.executable}")

    try:
        # Import the tunnel functionality
        from tunneling.bundled_instatunnel import (
            is_bundled_tunnel_available,
            start_bundled_tunnel,
        )

        print("✅ Tunnel modules imported successfully!")

        # Test availability
        available = is_bundled_tunnel_available()
        print(f"Tunnel available: {available}")

        if available:
            print("🚀 Starting tunnel test...")
            tunnel_url = start_bundled_tunnel(5001)  # Use different port

            if tunnel_url:
                print(f"✅ SUCCESS! Tunnel started: {tunnel_url}")
                return True
            else:
                print("❌ FAILED! Tunnel could not start")
                return False
        else:
            print("❌ FAILED! Tunnel not available")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_tunnel_in_executable()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
