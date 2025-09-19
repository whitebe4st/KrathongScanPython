#!/usr/bin/env python3
"""
Continuous tunnel monitoring to catch disconnection events.
This script monitors both the API status and direct tunnel access.
"""

import json
import time
from datetime import datetime

import requests


def monitor_tunnel_continuously():
    """Monitor tunnel status continuously to catch disconnections."""

    print("🔍 CONTINUOUS TUNNEL MONITORING")
    print("=" * 50)
    print("Monitoring for 5 minutes to catch disconnection events...")
    print()

    start_time = time.time()
    check_interval = 10  # Check every 10 seconds
    total_checks = 0
    api_failures = 0
    tunnel_failures = 0
    last_public_url = None

    while time.time() - start_time < 300:  # 5 minutes
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            total_checks += 1

            # Check API status
            try:
                api_response = requests.get(
                    "http://localhost:5000/api/tunnel/status", timeout=5
                )
                if api_response.status_code == 200:
                    data = api_response.json()
                    current_url = data.get("public_url")
                    available = data.get("available", False)
                    is_running = data.get("is_running", False)

                    if not available or not is_running:
                        api_failures += 1
                        print(
                            f"[{timestamp}] ❌ API reports tunnel not available/running"
                        )
                        print(
                            f"                Available: {available}, Running: {is_running}"
                        )

                    # Check if URL changed
                    if current_url != last_public_url:
                        if last_public_url:
                            print(f"[{timestamp}] 🔄 Tunnel URL changed!")
                            print(f"                Old: {last_public_url}")
                            print(f"                New: {current_url}")
                        else:
                            print(f"[{timestamp}] 🆕 Initial tunnel URL: {current_url}")
                        last_public_url = current_url

                    # Test actual tunnel access
                    if current_url:
                        try:
                            tunnel_response = requests.get(current_url, timeout=8)
                            if tunnel_response.status_code != 200:
                                tunnel_failures += 1
                                print(
                                    f"[{timestamp}] ❌ Tunnel access failed: HTTP {tunnel_response.status_code}"
                                )
                        except requests.exceptions.RequestException as e:
                            tunnel_failures += 1
                            print(f"[{timestamp}] ❌ Tunnel access failed: {e}")
                    else:
                        print(f"[{timestamp}] ⚠️ No public URL available")

                else:
                    api_failures += 1
                    print(
                        f"[{timestamp}] ❌ API status check failed: HTTP {api_response.status_code}"
                    )

            except requests.exceptions.RequestException as e:
                api_failures += 1
                print(f"[{timestamp}] ❌ API connection failed: {e}")

            # Progress indicator
            if total_checks % 6 == 0:  # Every minute
                print(
                    f"[{timestamp}] ✅ Checked {total_checks} times - API failures: {api_failures}, Tunnel failures: {tunnel_failures}"
                )

            time.sleep(check_interval)

        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
            break
        except Exception as e:
            print(f"[{timestamp}] ❌ Monitor error: {e}")
            time.sleep(check_interval)

    # Final summary
    print("\n📊 MONITORING SUMMARY:")
    print(f"Total checks: {total_checks}")
    print(f"API failures: {api_failures}")
    print(f"Tunnel access failures: {tunnel_failures}")
    print(
        f"Success rate: {((total_checks - api_failures - tunnel_failures) / max(total_checks, 1)) * 100:.1f}%"
    )

    if api_failures == 0 and tunnel_failures == 0:
        print("✅ No tunnel disconnections detected during monitoring period")
        print("💡 The tunnel appears to be stable in this session")
    else:
        print("⚠️ Tunnel issues detected - may be intermittent or load-dependent")


if __name__ == "__main__":
    monitor_tunnel_continuously()
