#!/usr/bin/env python3
"""
Debug script to check where PyInstaller is looking for bundled files.
"""

import os
import sys
from pathlib import Path


def debug_pyinstaller_paths():
    """Debug PyInstaller path resolution."""

    print("🔍 Debugging PyInstaller path resolution...")
    print(f"📍 Current working directory: {os.getcwd()}")
    print(f"📁 sys.executable: {sys.executable}")
    print(f"❄️ sys.frozen: {getattr(sys, 'frozen', False)}")

    if hasattr(sys, "_MEIPASS"):
        print(f"📂 sys._MEIPASS: {sys._MEIPASS}")
        meipass_path = Path(sys._MEIPASS)
        print(f"📁 _MEIPASS exists: {meipass_path.exists()}")

        if meipass_path.exists():
            print(f"📋 Contents of _MEIPASS:")
            try:
                for item in meipass_path.iterdir():
                    print(f"  📄 {item.name}")
            except Exception as e:
                print(f"  ❌ Error listing _MEIPASS: {e}")
    else:
        print("❌ sys._MEIPASS not available")

    # Check where the bundled tunnel code is looking
    print("\n🔍 Checking bundled tunnel path logic...")

    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        if hasattr(sys, "_MEIPASS"):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(sys.executable).parent / "_internal"
    else:
        # Running in development
        base_path = Path(__file__).parent

    print(f"📂 Calculated base_path: {base_path}")
    print(f"📁 Base path exists: {base_path.exists()}")

    nodejs_dir = base_path / "bin" / "nodejs"
    node_exe = nodejs_dir / "node.exe"
    instatunnel_cmd = nodejs_dir / "instatunnel.cmd"

    print(f"📂 Looking for nodejs_dir: {nodejs_dir}")
    print(f"📁 nodejs_dir exists: {nodejs_dir.exists()}")
    print(f"📄 node.exe exists: {node_exe.exists()}")
    print(f"📄 instatunnel.cmd exists: {instatunnel_cmd.exists()}")

    # Check the actual location where we put the files
    actual_internal = Path(sys.executable).parent / "_internal"
    print(f"\n📂 Actual _internal location: {actual_internal}")
    print(f"📁 _internal exists: {actual_internal.exists()}")

    if actual_internal.exists():
        actual_nodejs = actual_internal / "bin" / "nodejs"
        print(f"📂 Actual nodejs location: {actual_nodejs}")
        print(f"📁 Actual nodejs exists: {actual_nodejs.exists()}")

        if actual_nodejs.exists():
            actual_node_exe = actual_nodejs / "node.exe"
            actual_instatunnel = actual_nodejs / "instatunnel.cmd"
            print(f"📄 Actual node.exe exists: {actual_node_exe.exists()}")
            print(f"📄 Actual instatunnel.cmd exists: {actual_instatunnel.exists()}")


if __name__ == "__main__":
    print("=" * 60)
    print("🐛 PyInstaller Path Debug")
    print("=" * 60)

    debug_pyinstaller_paths()

    print("=" * 60)
