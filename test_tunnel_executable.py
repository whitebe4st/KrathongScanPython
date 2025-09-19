#!/usr/bin/env python3
"""
Test script to verify tunnel functionality in the compiled executable.
This will test if the bundled Node.js and InstaTunnel work correctly.
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def test_tunnel_from_executable():
    """Test tunnel functionality when running from the compiled executable context."""

    print("🧪 Testing InstaTunnel functionality in executable context...")
    print(f"📍 Current working directory: {os.getcwd()}")
    print(f"📁 Executable location: {sys.executable}")
    print(f"🐍 Python path: {sys.path}")

    # Check if we're running in frozen mode (PyInstaller)
    if getattr(sys, "frozen", False):
        print("❄️ Running in frozen mode (compiled executable)")
        base_dir = Path(sys.executable).parent
    else:
        print("🔥 Running in development mode")
        base_dir = Path(__file__).parent

    print(f"📂 Base directory: {base_dir}")

    # Look for Node.js files
    if getattr(sys, "frozen", False):
        # In frozen mode, look in _internal
        nodejs_dir = base_dir / "_internal" / "bin" / "nodejs"
    else:
        # In development mode, look in bin
        nodejs_dir = base_dir / "bin" / "nodejs"

    print(f"🔍 Looking for Node.js in: {nodejs_dir}")

    if nodejs_dir.exists():
        print("✅ Node.js directory found!")

        # Check for critical files
        node_exe = nodejs_dir / "node.exe"
        instatunnel_cmd = nodejs_dir / "instatunnel.cmd"

        print(f"📁 Node.exe exists: {node_exe.exists()}")
        print(f"📁 InstaTunnel.cmd exists: {instatunnel_cmd.exists()}")

        if node_exe.exists() and instatunnel_cmd.exists():
            print("✅ All required tunnel files found!")

            # Now test the actual tunnel functionality
            try:
                print("\n🚀 Testing InstaTunnel import and availability...")

                # Import tunnel functionality
                sys.path.append(str(base_dir / "src"))
                from tunneling.bundled_instatunnel import (
                    get_bundled_tunnel_url,
                    is_bundled_tunnel_available,
                    start_bundled_tunnel,
                    test_bundled_tunnel_connection,
                )

                print("✅ Successfully imported tunnel modules!")

                # Test availability
                print("\n🔍 Checking tunnel availability...")
                available = is_bundled_tunnel_available()
                print(f"📡 Tunnel available: {available}")

                if available:
                    print("\n🚀 Starting tunnel test (this may take a moment)...")

                    # Test starting tunnel on a test port
                    test_port = 5000
                    tunnel_url = start_bundled_tunnel(test_port)

                    if tunnel_url:
                        print(f"✅ Tunnel started successfully!")
                        print(f"🌍 Public URL: {tunnel_url}")

                        # Test connection
                        print("\n🔗 Testing tunnel connection...")
                        connection_test = test_bundled_tunnel_connection()
                        print(f"📡 Connection test result: {connection_test}")

                        return True
                    else:
                        print("❌ Failed to start tunnel")
                        return False
                else:
                    print("❌ Tunnel not available")
                    return False

            except Exception as e:
                print(f"❌ Error testing tunnel: {e}")
                import traceback

                traceback.print_exc()
                return False

        else:
            print("❌ Missing required tunnel files")
            return False
    else:
        print("❌ Node.js directory not found")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🔬 InstaTunnel Executable Test")
    print("=" * 60)

    success = test_tunnel_from_executable()

    print("\n" + "=" * 60)
    if success:
        print("✅ TUNNEL TEST PASSED!")
        print("🎉 InstaTunnel is working correctly in the executable!")
    else:
        print("❌ TUNNEL TEST FAILED!")
        print("💔 InstaTunnel is not working in the executable!")
    print("=" * 60)
