"""
Auto QR Generator for KrathongScanner
Automatically detects LocalTunnel URLs and generates QR codes
"""

import json
import re
import subprocess
import time

import requests


def detect_tunnel_url():
    """Detect LocalTunnel URL"""
    try:
        print("🔍 Starting LocalTunnel...")
        process = subprocess.Popen(
            ["npx", "localtunnel", "--port", "5000", "--bypass-tunnel-reminder"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait for tunnel to establish
        for _ in range(30):  # Wait up to 30 seconds
            line = process.stdout.readline()
            if line and "your url is:" in line:
                url_match = re.search(r"https://[^\s]+\.loca\.lt", line)
                if url_match:
                    return url_match.group(0), process
            time.sleep(1)

        return None, process

    except Exception as e:
        print(f"❌ Error starting tunnel: {e}")
        return None, None


def update_server_url(url):
    """Update server with new tunnel URL"""
    try:
        response = requests.post(
            "http://localhost:5000/update_tunnel_url", json={"url": url}, timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server updated successfully!")
            print(f"🌐 New URL: {data['new_url']}")
            print(f"🏬 Mall QR saved: {data['mall_qr_path']}")
            return True
        else:
            print(f"❌ Server update failed: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error updating server: {e}")
        return False


def main():
    print("🚀 Auto QR Generator for KrathongScanner")
    print("=" * 50)

    # Detect tunnel URL
    tunnel_url, tunnel_process = detect_tunnel_url()

    if tunnel_url:
        print(f"✅ Tunnel established: {tunnel_url}")

        # Update server
        if update_server_url(tunnel_url):
            print("📱 QR codes generated automatically!")
            print("🏬 Ready for mall deployment!")

            # Keep tunnel running
            try:
                print("\n💡 Tunnel is running. Press Ctrl+C to stop...")
                tunnel_process.wait()
            except KeyboardInterrupt:
                print("\n🔄 Stopping tunnel...")
                tunnel_process.terminate()

        else:
            print("❌ Failed to update server")
            tunnel_process.terminate()
    else:
        print("❌ Failed to establish tunnel")
        print("💡 Make sure Node.js is installed and server is running")


if __name__ == "__main__":
    main()
