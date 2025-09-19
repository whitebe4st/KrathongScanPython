"""
Pure Python tunneling solution using pyngrok.
No Node.js or NPX required - everything bundled with the executable.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

try:
    from pyngrok import ngrok
    from pyngrok.conf import PyngrokConfig

    NGROK_AVAILABLE = True
except ImportError:
    NGROK_AVAILABLE = False


class PythonTunneling:
    """Pure Python tunneling without external dependencies."""

    def __init__(self):
        self.tunnel = None
        self.config = None

    def setup_ngrok(self) -> bool:
        """Setup ngrok configuration."""
        try:
            if not NGROK_AVAILABLE:
                return False

            # Use bundled ngrok binary if available
            ngrok_path = self._get_bundled_ngrok_path()
            if ngrok_path and os.path.exists(ngrok_path):
                self.config = PyngrokConfig(ngrok_path=ngrok_path)
            else:
                # Use system ngrok if available
                self.config = PyngrokConfig()

            return True
        except Exception as e:
            print(f"Failed to setup ngrok: {e}")
            return False

    def _get_bundled_ngrok_path(self) -> Optional[str]:
        """Get path to bundled ngrok binary."""
        if getattr(sys, "frozen", False):
            # Running in PyInstaller bundle
            base_path = sys._MEIPASS
        else:
            # Running in development
            base_path = Path(__file__).parent.parent.parent

        # Check for ngrok binary
        ngrok_exe = os.path.join(base_path, "bin", "ngrok.exe")
        if os.path.exists(ngrok_exe):
            return ngrok_exe

        return None

    def start_tunnel(
        self, port: int = 5000, subdomain: Optional[str] = None
    ) -> Optional[str]:
        """Start ngrok tunnel."""
        try:
            if not self.setup_ngrok():
                return None

            # Configure tunnel options
            tunnel_options = {"bind_tls": True}  # HTTPS only
            if subdomain:
                tunnel_options["subdomain"] = subdomain

            # Start tunnel
            if self.config:
                ngrok.set_config(self.config)

            self.tunnel = ngrok.connect(port, **tunnel_options)
            public_url = self.tunnel.public_url

            print(f"✅ Tunnel started: {public_url}")
            return public_url

        except Exception as e:
            print(f"❌ Failed to start tunnel: {e}")
            return None

    def stop_tunnel(self):
        """Stop the tunnel."""
        try:
            if self.tunnel:
                ngrok.disconnect(self.tunnel.public_url)
                self.tunnel = None
                print("🔌 Tunnel stopped")
        except Exception as e:
            print(f"⚠️ Error stopping tunnel: {e}")

    def get_tunnel_url(self) -> Optional[str]:
        """Get current tunnel URL."""
        try:
            if self.tunnel:
                return self.tunnel.public_url
            return None
        except:
            return None


# Alternative Option 2: LocalTunnel Python Implementation
class LocalTunnelPython:
    """Pure Python implementation similar to localtunnel."""

    def __init__(self):
        self.process = None
        self.url = None

    def start_tunnel(
        self, port: int = 5000, subdomain: Optional[str] = None
    ) -> Optional[str]:
        """Start tunnel using Python requests to localtunnel.me API."""
        try:
            import json

            import requests

            # Request tunnel from localtunnel.me
            data = {"port": port}
            if subdomain:
                data["subdomain"] = subdomain

            response = requests.post("https://localtunnel.me/api/tunnels", json=data)

            if response.status_code == 200:
                tunnel_info = response.json()
                self.url = tunnel_info.get("url")
                print(f"✅ LocalTunnel started: {self.url}")
                return self.url
            else:
                print(f"❌ Failed to create tunnel: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ LocalTunnel error: {e}")
            return None

    def get_tunnel_url(self) -> Optional[str]:
        """Get current tunnel URL."""
        return self.url


# Option 3: Custom Simple Tunneling Service
class SimpleTunneling:
    """Simple custom tunneling solution."""

    def __init__(self):
        self.tunnel_url = None

    def start_tunnel(self, port: int = 5000) -> Optional[str]:
        """Start simple tunnel (local network only)."""
        try:
            import socket

            # Get local IP
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)

            self.tunnel_url = f"http://{local_ip}:{port}"
            print(f"🌐 Local network access: {self.tunnel_url}")
            return self.tunnel_url

        except Exception as e:
            print(f"❌ Failed to get local IP: {e}")
            return None

    def get_tunnel_url(self) -> Optional[str]:
        """Get tunnel URL."""
        return self.tunnel_url
