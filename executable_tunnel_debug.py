#!/usr/bin/env python3
"""
Executable-specific tunnel diagnostics.
This script will be bundled with the executable to debug tunnel issues
that only occur in the compiled environment.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests


def debug_executable_environment():
    """Debug the executable environment for tunnel issues."""

    print("🔍 EXECUTABLE TUNNEL DIAGNOSTICS")
    print("=" * 50)

    # Check if running from executable
    is_frozen = getattr(sys, "frozen", False)
    print(f"Running from executable: {is_frozen}")

    if is_frozen:
        print(f"Executable path: {sys.executable}")
        print(f"Internal path: {sys._MEIPASS}")

        # Check Node.js paths in executable
        internal_path = Path(sys._MEIPASS)
        nodejs_path = internal_path / "bin" / "nodejs"

        print(f"Internal Node.js path: {nodejs_path}")
        print(f"Node.js exists: {nodejs_path.exists()}")

        if nodejs_path.exists():
            node_exe = nodejs_path / "node.exe"
            instatunnel_cmd = nodejs_path / "instatunnel.cmd"

            print(f"node.exe exists: {node_exe.exists()}")
            print(f"instatunnel.cmd exists: {instatunnel_cmd.exists()}")

            # Test Node.js execution
            if node_exe.exists():
                try:
                    result = subprocess.run(
                        [str(node_exe), "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    print(f"Node.js version: {result.stdout.strip()}")
                except Exception as e:
                    print(f"❌ Node.js execution failed: {e}")

            # Test InstaTunnel execution
            if instatunnel_cmd.exists():
                try:
                    # Try to get instatunnel help
                    result = subprocess.run(
                        [str(instatunnel_cmd), "--help"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    print(f"InstaTunnel help (first 200 chars): {result.stdout[:200]}")
                except Exception as e:
                    print(f"❌ InstaTunnel execution failed: {e}")

    else:
        print("Running from Python source - tunnel issues don't occur here")
        return

    # Check environment variables
    print("\n🌍 ENVIRONMENT VARIABLES:")
    important_vars = ["PATH", "NODE_PATH", "TEMP", "TMP"]
    for var in important_vars:
        value = os.environ.get(var, "Not set")
        print(f"{var}: {value[:100]}...")

    # Check running processes
    print("\n🔍 CHECKING PROCESSES:")
    try:
        # Check for Node.js processes
        tasklist_result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq node.exe"], capture_output=True, text=True
        )
        node_processes = tasklist_result.stdout.count("node.exe")
        print(f"Node.js processes running: {node_processes}")

        # Check for InstaTunnel specifically
        if "instatunnel" in tasklist_result.stdout.lower():
            print("✅ InstaTunnel process detected")
        else:
            print("❌ No InstaTunnel process detected")

    except Exception as e:
        print(f"❌ Process check failed: {e}")

    # Test tunnel creation from executable
    print("\n🚇 TESTING TUNNEL CREATION FROM EXECUTABLE:")
    try:
        # Import the bundled tunnel module
        sys.path.insert(0, str(Path(sys._MEIPASS) / "src"))
        from tunneling.bundled_instatunnel import bundled_tunnel, start_instatunnel

        print("✅ Successfully imported bundled tunnel module")

        # Check if bundled tunnel is available
        if bundled_tunnel.is_available():
            print("✅ Bundled tunnel reports as available")

            # Get current tunnel status
            status = bundled_tunnel.get_tunnel_status()
            print(f"Current tunnel status: {json.dumps(status, indent=2)}")

            # Try to start a tunnel (only if none running)
            if not status.get("is_running", False):
                print("🚇 Attempting to start tunnel...")
                tunnel_url = start_instatunnel(5000)
                if tunnel_url:
                    print(f"✅ Tunnel started: {tunnel_url}")

                    # Test the tunnel after a delay
                    time.sleep(5)
                    print("🔍 Testing tunnel accessibility...")
                    try:
                        response = requests.get(tunnel_url, timeout=10)
                        print(f"Tunnel response status: {response.status_code}")
                    except Exception as e:
                        print(f"❌ Tunnel not accessible: {e}")
                else:
                    print("❌ Failed to start tunnel")
            else:
                print("ℹ️ Tunnel already running")

        else:
            print("❌ Bundled tunnel not available")

    except ImportError as e:
        print(f"❌ Failed to import tunnel module: {e}")
    except Exception as e:
        print(f"❌ Tunnel test failed: {e}")

    # Monitor for disconnections
    print("\n⏱️ MONITORING FOR DISCONNECTIONS (30 seconds)...")
    start_time = time.time()
    check_count = 0
    disconnect_count = 0

    while time.time() - start_time < 30:
        try:
            # Check if Flask is still responding
            response = requests.get("http://localhost:5000/api/status", timeout=3)
            if response.status_code == 200:
                data = response.json()
                public_url = data.get("public_url")

                if public_url:
                    # Test public URL
                    try:
                        pub_response = requests.get(public_url, timeout=5)
                        if pub_response.status_code != 200:
                            disconnect_count += 1
                            print(
                                f"⚠️ Tunnel disconnection detected (status: {pub_response.status_code})"
                            )
                    except:
                        disconnect_count += 1
                        print(f"⚠️ Tunnel disconnection detected (connection failed)")
                else:
                    print(f"⚠️ No public URL available at check {check_count}")

            check_count += 1
            time.sleep(3)

        except Exception as e:
            print(f"❌ Monitor check failed: {e}")
            break

    print(f"\n📊 MONITORING RESULTS:")
    print(f"Total checks: {check_count}")
    print(f"Disconnections detected: {disconnect_count}")
    print(
        f"Stability rate: {((check_count - disconnect_count) / max(check_count, 1)) * 100:.1f}%"
    )


if __name__ == "__main__":
    debug_executable_environment()
