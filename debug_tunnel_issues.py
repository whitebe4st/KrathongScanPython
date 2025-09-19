#!/usr/bin/env python3
"""
Debug tunnel connection issues
Check tunnel process status, connection stability, and identify disconnection causes
"""

import os
import sys
import threading
import time

import requests

# Add paths
current_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(current_dir, "src"))

from tunneling.bundled_instatunnel import (
    bundled_tunnel,
    get_bundled_tunnel_url,
    is_bundled_tunnel_available,
    is_bundled_tunnel_running,
    start_bundled_tunnel,
    stop_bundled_tunnel,
    test_bundled_tunnel_connection,
)


def debug_tunnel_connection_issues():
    """Debug comprehensive tunnel connection issues"""
    print("🔍 Debugging tunnel connection issues...")

    # Check if tunnel components are available
    print("\n1️⃣ Checking tunnel availability...")
    if is_bundled_tunnel_available():
        print("✅ Bundled InstaTunnel is available")
    else:
        print("❌ Bundled InstaTunnel is NOT available")
        return False

    # Check current tunnel status
    print("\n2️⃣ Checking current tunnel status...")
    current_url = get_bundled_tunnel_url()
    if current_url:
        print(f"🔗 Current tunnel URL: {current_url}")

        # Test current tunnel
        print("🔍 Testing current tunnel connection...")
        if test_bundled_tunnel_connection():
            print("✅ Current tunnel is working")
        else:
            print("❌ Current tunnel is broken")
    else:
        print("⚠️ No current tunnel URL")

    # Check if tunnel process is running
    print("\n3️⃣ Checking tunnel process status...")
    if is_bundled_tunnel_running():
        print("✅ Tunnel process is running")
    else:
        print("❌ Tunnel process is NOT running")

    # Get detailed status
    print("\n4️⃣ Getting detailed tunnel status...")
    try:
        status = bundled_tunnel.get_tunnel_status()
        print(f"📊 Detailed status:")
        for key, value in status.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ Failed to get detailed status: {e}")

    # Start fresh tunnel and monitor
    print("\n5️⃣ Starting fresh tunnel for monitoring...")
    stop_bundled_tunnel()  # Stop any existing tunnel
    time.sleep(2)

    tunnel_url = start_bundled_tunnel(5000)
    if tunnel_url:
        print(f"✅ Fresh tunnel started: {tunnel_url}")

        # Monitor tunnel for 60 seconds
        print("\n6️⃣ Monitoring tunnel stability for 60 seconds...")
        monitor_tunnel_stability(tunnel_url, duration=60)
    else:
        print("❌ Failed to start fresh tunnel")

    return True


def monitor_tunnel_stability(tunnel_url, duration=60):
    """Monitor tunnel connection stability over time"""
    print(f"⏱️ Monitoring {tunnel_url} for {duration} seconds...")

    start_time = time.time()
    test_count = 0
    success_count = 0

    while time.time() - start_time < duration:
        test_count += 1

        try:
            print(f"\n🔍 Test #{test_count} at {time.time() - start_time:.1f}s")

            # Check process status
            status = bundled_tunnel.get_tunnel_status()
            print(f"   Process alive: {status['process_alive']}")
            print(f"   Connection test: {status['connection_test']}")

            if status["error_message"]:
                print(f"   ⚠️ Error: {status['error_message']}")

            # Test connection manually
            response = requests.get(tunnel_url, timeout=10)
            if response.status_code == 200:
                success_count += 1
                print(f"   ✅ HTTP test passed (200)")
            else:
                print(f"   ⚠️ HTTP test failed ({response.status_code})")

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection failed: {e}")
        except Exception as e:
            print(f"   ❌ Test error: {e}")

        time.sleep(5)  # Test every 5 seconds

    print(f"\n📊 Monitoring complete:")
    print(f"   Total tests: {test_count}")
    print(f"   Successful: {success_count}")
    print(f"   Success rate: {success_count/test_count*100:.1f}%")


if __name__ == "__main__":
    try:
        debug_tunnel_connection_issues()
    except KeyboardInterrupt:
        print("\n🛑 Debugging interrupted by user")
    except Exception as e:
        print(f"\n💥 Debug failed: {e}")
    finally:
        print("\n🔚 Debug session complete")
