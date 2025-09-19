#!/usr/bin/env python3
"""
Quick tunnel diagnostics - no hanging, just fast checks
"""

import os
import subprocess
import sys
import time

import requests

# Add paths
current_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(current_dir, "src"))


def check_tunnel_processes():
    """Check if any InstaTunnel processes are running"""
    print("🔍 Checking for InstaTunnel processes...")

    try:
        # Use tasklist to find node processes
        result = subprocess.run(
            ["tasklist", "/fi", "imagename eq node.exe"],
            capture_output=True,
            text=True,
            shell=True,
        )

        if "node.exe" in result.stdout:
            print("✅ Found Node.js processes (likely InstaTunnel)")
            # Count lines with node.exe
            node_processes = [
                line for line in result.stdout.split("\n") if "node.exe" in line
            ]
            print(f"   Found {len(node_processes)} node.exe processes")
            return True
        else:
            print("❌ No Node.js processes found")
            return False
    except Exception as e:
        print(f"⚠️ Cannot check processes: {e}")
        return False


def check_port_5000():
    """Check if anything is listening on port 5000"""
    print("🔍 Checking port 5000...")

    try:
        response = requests.get("http://localhost:5000", timeout=3)
        print(f"✅ Port 5000 responding: HTTP {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Nothing listening on port 5000")
        return False
    except requests.exceptions.Timeout:
        print("⚠️ Port 5000 timeout")
        return False
    except Exception as e:
        print(f"❌ Port 5000 error: {e}")
        return False


def test_tunnel_url(url):
    """Test if a tunnel URL is working"""
    if not url:
        print("❌ No tunnel URL provided")
        return False

    print(f"🔍 Testing tunnel URL: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ Tunnel responding: HTTP {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Tunnel connection refused")
        return False
    except requests.exceptions.Timeout:
        print("❌ Tunnel timeout")
        return False
    except Exception as e:
        print(f"❌ Tunnel error: {e}")
        return False


def check_tunnel_status():
    """Quick tunnel status check"""
    print("🧪 Quick Tunnel Diagnostics")
    print("=" * 40)

    # Check processes
    processes = check_tunnel_processes()

    # Check local port
    local_working = check_port_5000()

    # Try to get tunnel URL from global variable if possible
    tunnel_url = None
    try:
        # Try to import and check if server is running
        import importlib.util

        server_spec = importlib.util.spec_from_file_location(
            "server", os.path.join(current_dir, "web", "server.py")
        )
        if server_spec and server_spec.loader:
            server_module = importlib.util.module_from_spec(server_spec)
            server_spec.loader.exec_module(server_module)
            tunnel_url = getattr(server_module, "public_url", None)

        if tunnel_url:
            print(f"🔗 Found tunnel URL: {tunnel_url}")
        else:
            print("❌ No tunnel URL found in global variable")
    except Exception as e:
        print(f"⚠️ Cannot access tunnel URL: {e}")

    # Test tunnel if we have URL
    tunnel_working = False
    if tunnel_url:
        tunnel_working = test_tunnel_url(tunnel_url)

    # Summary
    print("\n📊 Diagnosis Summary:")
    print(f"   InstaTunnel processes: {'✅' if processes else '❌'}")
    print(f"   Local port 5000: {'✅' if local_working else '❌'}")
    print(f"   Tunnel URL working: {'✅' if tunnel_working else '❌'}")

    if processes and local_working and not tunnel_working:
        print("\n💡 Likely issue: Tunnel URL exists but connection is broken")
        print("   Solution: Restart tunnel or check InstaTunnel service")
    elif not processes and local_working:
        print("\n💡 Likely issue: Flask running but no tunnel process")
        print("   Solution: Start InstaTunnel")
    elif not local_working:
        print("\n💡 Likely issue: Flask web server not running")
        print("   Solution: Start web server first")
    else:
        print("\n✅ Everything looks good!")


if __name__ == "__main__":
    check_tunnel_status()
    print("\n🏁 Diagnostics complete - no hanging!")
