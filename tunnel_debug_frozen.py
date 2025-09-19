#!/usr/bin/env python3
"""
Direct test script that will be run by the actual Scanner executable in frozen mode.
This will help us see exactly what's happening when the real Scanner tries to use the tunnel.
"""

import os
import sys
from pathlib import Path


def main():
    print("=" * 60)
    print("🔍 TUNNEL DEBUG - Running from actual Scanner executable")
    print("=" * 60)

    print(f"🐍 Python executable: {sys.executable}")
    print(f"❄️ Frozen mode: {getattr(sys, 'frozen', False)}")
    print(f"📂 Current working dir: {os.getcwd()}")

    if hasattr(sys, "_MEIPASS"):
        print(f"📁 sys._MEIPASS: {sys._MEIPASS}")
    else:
        print("❌ sys._MEIPASS not available")

    # Test path resolution logic from bundled_instatunnel
    if getattr(sys, "frozen", False):
        base_path = Path(sys.executable).parent / "_internal"
        print(f"🔧 Using frozen path logic")
    else:
        base_path = Path(__file__).parent.parent.parent
        print(f"🔧 Using development path logic")

    print(f"📂 Calculated base_path: {base_path}")
    print(f"📁 Base path exists: {base_path.exists()}")

    nodejs_dir = base_path / "bin" / "nodejs"
    node_exe = nodejs_dir / "node.exe"
    instatunnel_cmd = nodejs_dir / "instatunnel.cmd"

    print(f"📂 Node.js directory: {nodejs_dir}")
    print(f"📁 Node.js dir exists: {nodejs_dir.exists()}")
    print(f"📄 node.exe exists: {node_exe.exists()}")
    print(f"📄 instatunnel.cmd exists: {instatunnel_cmd.exists()}")

    if nodejs_dir.exists():
        print(f"📋 Contents of nodejs directory:")
        try:
            for item in nodejs_dir.iterdir():
                print(f"  📄 {item.name}")
        except Exception as e:
            print(f"  ❌ Error listing directory: {e}")

    # Test tunnel availability
    try:
        print("\n🔍 Testing tunnel import and availability...")
        sys.path.insert(0, str(base_path))  # Ensure we can import

        from tunneling.bundled_instatunnel import is_bundled_tunnel_available

        available = is_bundled_tunnel_available()
        print(f"📡 Tunnel available: {available}")

        if available:
            print("✅ SUCCESS: Tunnel is available!")
        else:
            print("❌ FAILED: Tunnel is not available!")

    except Exception as e:
        print(f"❌ ERROR importing tunnel: {e}")
        import traceback

        traceback.print_exc()

    print("=" * 60)


if __name__ == "__main__":
    main()
