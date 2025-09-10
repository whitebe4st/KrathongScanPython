"""
Bundled InstaTunnel implementation using portable Node.js.
This module uses the bundled Node.js and InstaTunnel to avoid external dependencies.
"""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional


class BundledInstaTunnel:
    """InstaTunnel implementation using bundled Node.js - no external dependencies required."""

    def __init__(self):
        self.tunnel_process = None
        self.tunnel_url = None
        self.is_running = False

    def _get_bundled_paths(self):
        """Get paths to bundled Node.js and InstaTunnel."""
        if getattr(sys, "frozen", False):
            # Running as PyInstaller bundle
            base_path = Path(sys._MEIPASS)
        else:
            # Running in development
            base_path = Path(__file__).parent.parent.parent

        nodejs_dir = base_path / "bin" / "nodejs"
        node_exe = nodejs_dir / "node.exe"
        instatunnel_cmd = nodejs_dir / "instatunnel.cmd"

        return node_exe, instatunnel_cmd, nodejs_dir

    def is_available(self) -> bool:
        """Check if bundled InstaTunnel is available."""
        try:
            node_exe, instatunnel_cmd, _ = self._get_bundled_paths()
            return node_exe.exists() and instatunnel_cmd.exists()
        except Exception:
            return False

    def start_tunnel(
        self, port: int = 5000, subdomain: Optional[str] = None
    ) -> Optional[str]:
        """Start InstaTunnel using bundled Node.js."""
        try:
            if not self.is_available():
                print("❌ Bundled InstaTunnel not found")
                return None

            node_exe, instatunnel_cmd, nodejs_dir = self._get_bundled_paths()

            print(f"🚀 Starting bundled InstaTunnel on port {port}...")
            print(f"🔧 Node.js path: {node_exe}")
            print(f"🔧 InstaTunnel path: {instatunnel_cmd}")
            print(f"🔧 Working directory: {nodejs_dir}")

            # Build command
            cmd = [str(instatunnel_cmd), str(port)]
            if subdomain:
                cmd.extend(["--subdomain", subdomain])

            print(f"🔧 Command: {' '.join(cmd)}")

            # Start InstaTunnel process with proper environment
            env = os.environ.copy()
            env["NODE_PATH"] = str(nodejs_dir / "node_modules")

            self.tunnel_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=str(nodejs_dir),
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                if sys.platform == "win32"
                else 0,
            )

            print(f"🔧 Process ID: {self.tunnel_process.pid}")

            # Parse output for tunnel URL
            url = self._parse_tunnel_output()
            if url:
                self.tunnel_url = url
                self.is_running = True
                print(f"✅ Bundled InstaTunnel started: {url}")

                # Wait a moment for the tunnel to fully establish
                time.sleep(2)

                # Check if process is still running
                if self.tunnel_process and self.tunnel_process.poll() is None:
                    print("✅ Tunnel process is still running")

                    # Test the connection
                    print("🔍 Testing tunnel connection...")
                    if self.test_tunnel_connection():
                        print("✅ Tunnel connection test passed")
                    else:
                        print("⚠️ Tunnel connection test failed")
                        # Read any additional output
                        self._debug_tunnel_status()
                else:
                    print("❌ Tunnel process has terminated unexpectedly")
                    self._debug_tunnel_status()

                return url
            else:
                print("❌ Failed to start bundled InstaTunnel")
                self._debug_tunnel_status()
                return None

        except Exception as e:
            print(f"❌ Bundled InstaTunnel error: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _parse_tunnel_output(self) -> Optional[str]:
        """Parse InstaTunnel output to extract the public URL."""
        if not self.tunnel_process:
            return None

        # Read output lines looking for URL
        timeout = 30  # 30 second timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.tunnel_process.poll() is not None:
                # Process ended unexpectedly
                stderr_output = ""
                if self.tunnel_process.stderr:
                    stderr_output = self.tunnel_process.stderr.read()
                print(
                    f"❌ InstaTunnel process ended unexpectedly. Exit code: {self.tunnel_process.returncode}"
                )
                if stderr_output:
                    print(f"❌ Error output: {stderr_output}")
                break

            try:
                # Read line with timeout
                line = self.tunnel_process.stdout.readline()
                if not line:
                    time.sleep(0.1)
                    continue

                line = line.strip()
                print(f"🚀 InstaTunnel: {line}")

                # Look for URL patterns
                if "Your app is now live at" in line:
                    # Extract URL from line like "🚀 Your app is now live at https://abc123.instatunnel.my"
                    parts = line.split("at ")
                    if len(parts) > 1:
                        url = parts[-1].strip()
                        if url.startswith("http"):
                            # Start background thread to keep reading output
                            self._start_output_monitor()
                            return url

                elif "instatunnel.my" in line and "http" in line:
                    # Fallback: look for any line containing instatunnel.my URL
                    import re

                    urls = re.findall(r"https://[a-zA-Z0-9.-]+\.instatunnel\.my", line)
                    if urls:
                        # Start background thread to keep reading output
                        self._start_output_monitor()
                        return urls[0]

            except Exception as e:
                print(f"⚠️ Error reading InstaTunnel output: {e}")
                time.sleep(0.1)

        return None

    def _start_output_monitor(self):
        """Start background thread to monitor InstaTunnel output and keep process alive."""

        def monitor_output():
            try:
                while self.tunnel_process and self.tunnel_process.poll() is None:
                    line = self.tunnel_process.stdout.readline()
                    if line:
                        # Handle encoding issues properly
                        if isinstance(line, bytes):
                            line = line.decode("utf-8", errors="replace")
                        line = line.strip()
                        if line:  # Only print non-empty lines
                            print(f"🔗 InstaTunnel: {line}")
                    else:
                        time.sleep(0.1)
            except Exception as e:
                print(f"⚠️ InstaTunnel monitor error: {e}")

        monitor_thread = threading.Thread(target=monitor_output, daemon=True)
        monitor_thread.start()

    def _debug_tunnel_status(self):
        """Debug tunnel process status and output."""
        try:
            if self.tunnel_process:
                print(
                    f"🔧 Process status: {'Running' if self.tunnel_process.poll() is None else 'Terminated'}"
                )
                print(f"🔧 Return code: {self.tunnel_process.returncode}")

                # Try to read any remaining output
                try:
                    if self.tunnel_process.stdout:
                        remaining_output = self.tunnel_process.stdout.read()
                        if remaining_output:
                            print(f"📄 Remaining stdout: {remaining_output}")
                except:
                    pass

                try:
                    if self.tunnel_process.stderr:
                        error_output = self.tunnel_process.stderr.read()
                        if error_output:
                            print(f"❌ Error output: {error_output}")
                except:
                    pass
            else:
                print("🔧 No tunnel process")
        except Exception as e:
            print(f"⚠️ Debug error: {e}")

    def stop_tunnel(self):
        """Stop the InstaTunnel process."""
        try:
            if self.tunnel_process:
                self.tunnel_process.terminate()
                self.tunnel_process.wait(timeout=5)
                self.tunnel_process = None

            self.tunnel_url = None
            self.is_running = False
            print("🔌 Bundled InstaTunnel stopped")

        except Exception as e:
            print(f"⚠️ Error stopping bundled InstaTunnel: {e}")

    def get_tunnel_url(self) -> Optional[str]:
        """Get the current tunnel URL."""
        return self.tunnel_url if self.is_running else None

    def is_tunnel_running(self) -> bool:
        """Check if tunnel is currently running."""
        if not self.tunnel_process:
            return False

        # Check if process is still alive
        if self.tunnel_process.poll() is not None:
            self.is_running = False
            print(
                f"⚠️ InstaTunnel process ended. Exit code: {self.tunnel_process.returncode}"
            )
            return False

        return self.is_running

    def test_tunnel_connection(self) -> bool:
        """Test if the tunnel URL is actually accessible."""
        if not self.tunnel_url:
            print("❌ No tunnel URL to test")
            return False

        try:
            import urllib.error
            import urllib.request

            print(f"🔍 Testing connection to: {self.tunnel_url}")

            # Try to access the tunnel URL
            req = urllib.request.Request(self.tunnel_url)
            req.add_header("User-Agent", "KrathongScanner/1.0")

            with urllib.request.urlopen(req, timeout=10) as response:
                status = response.status
                print(f"📡 HTTP Status: {status}")

                # Read a small portion of the response
                try:
                    content = response.read(100).decode("utf-8", errors="ignore")
                    print(f"📄 Response preview: {content[:50]}...")
                except:
                    pass

                return status == 200

        except urllib.error.URLError as e:
            print(f"⚠️ Tunnel connection test failed: {e}")
            if hasattr(e, "code"):
                print(f"📡 HTTP Error Code: {e.code}")
            if hasattr(e, "reason"):
                print(f"📡 Reason: {e.reason}")
            return False
        except Exception as e:
            print(f"⚠️ Tunnel test error: {e}")
            return False

    def get_tunnel_status(self) -> dict:
        """Get comprehensive tunnel status information."""
        status = {
            "is_running": False,
            "tunnel_url": None,
            "process_alive": False,
            "connection_test": False,
            "error_message": None,
        }

        try:
            # Check if we have a tunnel URL
            status["tunnel_url"] = self.tunnel_url

            # Check if process is alive
            if self.tunnel_process:
                process_alive = self.tunnel_process.poll() is None
                status["process_alive"] = process_alive

                if not process_alive:
                    status[
                        "error_message"
                    ] = f"Process terminated with code: {self.tunnel_process.returncode}"
                else:
                    # Test connection if process is alive and we have a URL
                    if self.tunnel_url:
                        status["connection_test"] = self.test_tunnel_connection()
                        status["is_running"] = status["connection_test"]
                    else:
                        status["error_message"] = "No tunnel URL available"
            else:
                status["error_message"] = "No tunnel process"

        except Exception as e:
            status["error_message"] = f"Status check error: {e}"

        return status


# Global instance
bundled_tunnel = BundledInstaTunnel()


def start_bundled_tunnel(
    port: int = 5000, subdomain: Optional[str] = None
) -> Optional[str]:
    """Convenience function to start bundled InstaTunnel."""
    return bundled_tunnel.start_tunnel(port, subdomain)


def stop_bundled_tunnel():
    """Convenience function to stop bundled InstaTunnel."""
    bundled_tunnel.stop_tunnel()


def get_bundled_tunnel_url() -> Optional[str]:
    """Convenience function to get tunnel URL."""
    return bundled_tunnel.get_tunnel_url()


def is_bundled_tunnel_available() -> bool:
    """Convenience function to check if bundled InstaTunnel is available."""
    return bundled_tunnel.is_available()


def is_bundled_tunnel_running() -> bool:
    """Convenience function to check if bundled InstaTunnel is running."""
    return bundled_tunnel.is_tunnel_running()


def test_bundled_tunnel_connection() -> bool:
    """Convenience function to test bundled tunnel connection."""
    return bundled_tunnel.test_tunnel_connection()
