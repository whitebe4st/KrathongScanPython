#!/usr/bin/env python3
"""
Enhanced tunnel monitoring and recovery system for KrathongScanner.
This script continuously monitors tunnel health and automatically restarts
disconnected tunnels to maintain reliable public access.
"""

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import requests


class TunnelMonitor:
    """Monitor and maintain tunnel connections."""

    def __init__(self, local_port=5000, check_interval=30):
        self.local_port = local_port
        self.check_interval = check_interval
        self.tunnel_url = None
        self.is_monitoring = False
        self.monitor_thread = None

    def check_flask_server(self):
        """Check if Flask server is running on the local port."""
        try:
            response = requests.get(f"http://localhost:{self.local_port}", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def check_tunnel_connection(self):
        """Check if tunnel is connected and accessible."""
        if not self.tunnel_url:
            return False

        try:
            response = requests.get(self.tunnel_url, timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def restart_tunnel(self):
        """Restart the InstaTunnel connection."""
        print("🔄 Restarting InstaTunnel connection...")

        try:
            # Import the tunnel module
            if getattr(sys, "frozen", False):
                # Running in compiled executable
                sys.path.insert(
                    0, str(Path(sys.executable).parent / "_internal" / "src")
                )
            else:
                # Running from source
                sys.path.insert(0, str(Path(__file__).parent / "src"))

            from tunneling.bundled_instatunnel import start_instatunnel

            # Kill existing tunnel processes
            try:
                # Kill any existing node processes (InstaTunnel)
                subprocess.run(
                    ["taskkill", "/f", "/im", "node.exe"],
                    capture_output=True,
                    check=False,
                )
                time.sleep(2)
            except:
                pass

            # Start new tunnel
            new_url = start_instatunnel(self.local_port)
            if new_url:
                self.tunnel_url = new_url
                print(f"✅ Tunnel restarted successfully: {new_url}")
                return True
            else:
                print("❌ Failed to restart tunnel")
                return False

        except Exception as e:
            print(f"❌ Error restarting tunnel: {e}")
            return False

    def monitor_loop(self):
        """Main monitoring loop."""
        print(f"🔍 Starting tunnel monitoring (checking every {self.check_interval}s)")

        consecutive_failures = 0
        max_failures = 3

        while self.is_monitoring:
            try:
                flask_ok = self.check_flask_server()
                tunnel_ok = self.check_tunnel_connection() if self.tunnel_url else False

                if not flask_ok:
                    print("⚠️ Flask server not responding on localhost:5000")
                    consecutive_failures += 1
                elif not tunnel_ok and self.tunnel_url:
                    print(f"⚠️ Tunnel not responding: {self.tunnel_url}")
                    consecutive_failures += 1
                else:
                    if consecutive_failures > 0:
                        print("✅ All services healthy")
                    consecutive_failures = 0

                # Restart tunnel if too many failures
                if consecutive_failures >= max_failures and self.tunnel_url:
                    print(
                        f"❌ {consecutive_failures} consecutive failures - restarting tunnel"
                    )
                    if self.restart_tunnel():
                        consecutive_failures = 0
                    else:
                        # If restart fails, wait longer before trying again
                        time.sleep(self.check_interval * 2)
                        continue

                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                time.sleep(self.check_interval)

        print("🛑 Tunnel monitoring stopped")

    def start_monitoring(self, tunnel_url=None):
        """Start the monitoring thread."""
        if self.is_monitoring:
            print("⚠️ Monitoring already active")
            return

        self.tunnel_url = tunnel_url
        self.is_monitoring = True

        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

        print("✅ Tunnel monitoring started")

    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("✅ Tunnel monitoring stopped")


# Global monitor instance
tunnel_monitor = None


def start_tunnel_monitoring(tunnel_url=None, local_port=5000, check_interval=30):
    """Start tunnel monitoring with the given parameters."""
    global tunnel_monitor

    if tunnel_monitor is None:
        tunnel_monitor = TunnelMonitor(local_port, check_interval)

    tunnel_monitor.start_monitoring(tunnel_url)
    return tunnel_monitor


def stop_tunnel_monitoring():
    """Stop tunnel monitoring."""
    global tunnel_monitor

    if tunnel_monitor:
        tunnel_monitor.stop_monitoring()


if __name__ == "__main__":
    # Standalone tunnel monitor
    print("🚀 KrathongScanner Tunnel Monitor")
    print("=" * 40)

    monitor = TunnelMonitor(local_port=5000, check_interval=15)

    try:
        # Check if Flask is running
        if monitor.check_flask_server():
            print("✅ Flask server detected on localhost:5000")

            # Try to get tunnel URL from a status endpoint
            try:
                response = requests.get(
                    "http://localhost:5000/api/tunnel-status", timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    tunnel_url = data.get("public_url")
                    if tunnel_url:
                        print(f"✅ Found existing tunnel: {tunnel_url}")
                        monitor.start_monitoring(tunnel_url)
                    else:
                        print("⚠️ No tunnel URL found - monitoring Flask only")
                        monitor.start_monitoring()
            except:
                print("⚠️ Could not get tunnel status - monitoring Flask only")
                monitor.start_monitoring()

            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping monitor...")
                monitor.stop_monitoring()
        else:
            print("❌ Flask server not running on localhost:5000")
            print("💡 Please start the web server first")

    except Exception as e:
        print(f"❌ Monitor startup failed: {e}")
