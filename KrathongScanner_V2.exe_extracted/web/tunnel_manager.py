"""
Improved tunnel module for KrathongScanner Web Server
Optimized for mall deployment with multiple tunnel fallbacks
"""

import os
import subprocess
import sys
import time


def start_reliable_tunnel(port=5000, timeout=30):
    """
    Start reliable public tunnel for mall deployment
    Tries multiple services for maximum reliability
    """
    print("🚇 Starting public tunnel for mall deployment...")

    # Try multiple tunnel services in order of reliability
    tunnel_methods = [
        ("LocalTunnel", start_localtunnel_npx),
        ("pyngrok", start_ngrok_tunnel),
        ("Bore.pub", start_bore_tunnel),
        ("Serveo SSH", start_serveo_tunnel),
    ]

    for method_name, method_func in tunnel_methods:
        try:
            print(f"🔄 Trying {method_name}...")
            tunnel_url = method_func(port, timeout)
            if tunnel_url:
                print(f"✅ {method_name} tunnel established: {tunnel_url}")
                return tunnel_url, method_name
            else:
                print(f"❌ {method_name} failed")
        except Exception as e:
            print(f"❌ {method_name} error: {e}")

    print("❌ All tunnel methods failed!")
    print("💡 Mall deployment requires public URL. Recommendations:")
    print("   1. Install Node.js for LocalTunnel: https://nodejs.org")
    print("   2. Setup ngrok token: https://ngrok.com")
    print("   3. Check firewall/network settings")
    return None, None


def start_localtunnel_npx(port=5000, timeout=20):
    """Use LocalTunnel via npx (most reliable for mall deployment)"""
    try:
        print("🌐 Starting LocalTunnel via npx...")

        # First check if npx is available
        npx_check = subprocess.run(["npx", "--version"], capture_output=True, text=True)
        if npx_check.returncode != 0:
            print("❌ npx not found - install Node.js from https://nodejs.org")
            return None

        # Start localtunnel with npx
        lt_process = subprocess.Popen(
            ["npx", "localtunnel", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
        )

        print("⏳ Waiting for LocalTunnel URL...")

        # Wait for URL with better parsing
        start_time = time.time()
        while time.time() - start_time < timeout:
            if lt_process.poll() is not None:
                stdout, stderr = lt_process.communicate()
                print(f"LocalTunnel stdout: {stdout}")
                print(f"LocalTunnel stderr: {stderr}")
                break

            # Check stdout
            line = lt_process.stdout.readline()
            if line:
                print(f"📝 LocalTunnel: {line.strip()}")
                if "loca.lt" in line:
                    import re

                    url_match = re.search(r"https://[a-zA-Z0-9-]+\.loca\.lt", line)
                    if url_match:
                        return url_match.group(0)

            # Check stderr for URL as well
            line = lt_process.stderr.readline()
            if line:
                print(f"📝 LocalTunnel err: {line.strip()}")
                if "loca.lt" in line:
                    import re

                    url_match = re.search(r"https://[a-zA-Z0-9-]+\.loca\.lt", line)
                    if url_match:
                        return url_match.group(0)

            time.sleep(0.5)

        # Cleanup
        if lt_process.poll() is None:
            lt_process.terminate()

        return None

    except FileNotFoundError:
        print("❌ npx not found - install Node.js")
        return None
    except Exception as e:
        print(f"LocalTunnel error: {e}")
        return None


def start_ngrok_tunnel(port=5000, timeout=15):
    """Use pyngrok with improved error handling"""
    try:
        from pyngrok import ngrok

        print("🔧 Attempting ngrok tunnel...")
        tunnel = ngrok.connect(port, "http", bind_tls=True)
        return tunnel.public_url

    except Exception as e:
        if "authtoken" in str(e).lower():
            print("🔐 ngrok requires authentication")
            print("💡 Quick setup:")
            print("   1. Visit https://ngrok.com and sign up (free)")
            print("   2. Get your auth token from dashboard")
            print("   3. Run: ngrok authtoken YOUR_TOKEN")
            print("   4. Restart the server")
        else:
            print(f"ngrok error: {e}")
        return None


def start_bore_tunnel(port=5000, timeout=15):
    """Use bore.pub as alternative tunnel"""
    try:
        print("🕳️ Trying bore.pub tunnel...")

        # Check if bore is installed
        bore_check = subprocess.run(
            ["bore", "--version"], capture_output=True, text=True
        )
        if bore_check.returncode != 0:
            # Try to install bore via cargo if available
            cargo_check = subprocess.run(
                ["cargo", "--version"], capture_output=True, text=True
            )
            if cargo_check.returncode == 0:
                print("📦 Installing bore via cargo...")
                install_result = subprocess.run(
                    ["cargo", "install", "bore-cli"], capture_output=True, text=True
                )
                if install_result.returncode != 0:
                    return None
            else:
                return None

        # Start bore tunnel
        bore_process = subprocess.Popen(
            ["bore", "local", str(port), "--to", "bore.pub"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait for URL
        start_time = time.time()
        while time.time() - start_time < timeout:
            if bore_process.poll() is not None:
                break

            line = bore_process.stdout.readline()
            if line and "bore.pub" in line:
                import re

                url_match = re.search(r"https://[^\s]+\.bore\.pub", line)
                if url_match:
                    return url_match.group(0)

            time.sleep(0.5)

        if bore_process.poll() is None:
            bore_process.terminate()

        return None

    except Exception:
        return None


def start_serveo_tunnel(port=5000, timeout=15):
    """Serveo SSH tunnel as final fallback"""
    try:
        print("🔧 Trying SSH tunnel via serveo.net...")

        # Check if SSH is available
        ssh_check = subprocess.run(["ssh", "-V"], capture_output=True, text=True)
        if ssh_check.returncode != 0:
            print("❌ SSH not available")
            return None

        serveo_process = subprocess.Popen(
            [
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "ConnectTimeout=10",
                "-R",
                f"80:localhost:{port}",
                "serveo.net",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
        )

        start_time = time.time()
        while time.time() - start_time < timeout:
            if serveo_process.poll() is not None:
                break

            line = serveo_process.stderr.readline()
            if line and "https://" in line:
                import re

                url_match = re.search(r"https://[^\s]+\.serveo\.net", line)
                if url_match:
                    return url_match.group(0)

            time.sleep(1)

        if serveo_process.poll() is None:
            serveo_process.terminate()

        return None

    except Exception:
        return None


def generate_mall_deployment_qr(public_url):
    """Generate QR code specifically for mall deployment"""
    try:
        import io
        import os

        import qrcode

        print(f"📱 Generating mall deployment QR code for: {public_url}")

        # Create high-quality QR code for mall displays
        qr = qrcode.QRCode(
            version=2,  # Slightly larger for better scanning
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
            box_size=12,  # Larger boxes for better visibility
            border=6,  # Larger border
        )
        qr.add_data(public_url)
        qr.make(fit=True)

        # Create high-contrast image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save to multiple locations for display
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        os.makedirs(static_dir, exist_ok=True)

        # Save high-quality QR for printing/display
        mall_qr_path = os.path.join(static_dir, "qr_mall_display.png")
        img.save(mall_qr_path, dpi=(300, 300))  # High DPI for printing

        # Save regular QR for web
        web_qr_path = os.path.join(static_dir, "qr_public.png")
        img.save(web_qr_path)

        print(f"📱 Mall display QR saved: {mall_qr_path}")
        print(f"🌐 Web QR saved: {web_qr_path}")

        return mall_qr_path, web_qr_path

    except Exception as e:
        print(f"❌ Failed to generate QR codes: {e}")
        return None, None
