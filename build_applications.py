#!/usr/bin/env python3
"""
KrathongScanner Build Script

Compiles both Scanner and Template Management applications using PyInstaller.
Creates executables in release/scanner and release/backend directories.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(command, description=""):
    """Run a command and handle errors."""
    print(f"🔧 {description}")
    print(f"   Command: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        print(f"   Error: {e.stderr}")
        return False


def check_pyinstaller():
    """Check if PyInstaller is installed, install if not."""
    try:
        import PyInstaller

        print("✅ PyInstaller found")
        return True
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        success = run_command(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            "Installing PyInstaller",
        )
        return success


def setup_directories():
    """Create release directories."""
    release_dir = Path("release")
    scanner_dir = release_dir / "scanner"
    backend_dir = release_dir / "backend"

    for directory in [release_dir, scanner_dir, backend_dir]:
        directory.mkdir(exist_ok=True)
        print(f"📁 Directory ready: {directory}")


def build_scanner():
    """Build the scanner application."""
    print("\n📦 Building Scanner_1-0...")
    print("=" * 60)

    # Build using PyInstaller
    success = run_command(
        ["pyinstaller", "--clean", "--noconfirm", "scanner_build.spec"],
        "Building Scanner with PyInstaller",
    )

    if not success:
        return False

    # Move to release directory
    dist_path = Path("dist/Scanner_1-0")
    release_path = Path("release/scanner")

    if dist_path.exists():
        # Remove existing files in release directory
        if release_path.exists():
            shutil.rmtree(release_path)

        # Copy new build
        shutil.copytree(dist_path, release_path)
        print(f"✅ Scanner_1-0 moved to {release_path}")
        return True
    else:
        print("❌ Scanner build output not found")
        return False


def build_template_creator():
    """Build the template creator application."""
    print("\n📦 Building template_management_1-0...")
    print("=" * 60)

    # Build using PyInstaller
    success = run_command(
        ["pyinstaller", "--clean", "--noconfirm", "template_creator_build.spec"],
        "Building Template Creator with PyInstaller",
    )

    if not success:
        return False

    # Move to release directory
    dist_path = Path("dist/template_management_1-0")
    release_path = Path("release/backend")

    if dist_path.exists():
        # Remove existing files in release directory
        if release_path.exists():
            shutil.rmtree(release_path)

        # Copy new build
        shutil.copytree(dist_path, release_path)
        print(f"✅ template_management_1-0 moved to {release_path}")
        return True
    else:
        print("❌ Template creator build output not found")
        return False


def cleanup():
    """Clean up build artifacts."""
    print("\n🧹 Cleaning up build artifacts...")

    for directory in ["build", "dist"]:
        if Path(directory).exists():
            shutil.rmtree(directory)
            print(f"🗑️  Removed {directory}/")

    # Remove any backup spec files
    for spec_backup in Path(".").glob("*.spec~"):
        spec_backup.unlink()
        print(f"🗑️  Removed {spec_backup}")


def show_results():
    """Show the final build results."""
    print("\n" + "=" * 60)
    print("✅ Build Complete!")
    print("=" * 60)

    scanner_exe = Path("release/scanner/Scanner_1-0.exe")
    template_exe = Path("release/backend/template_management_1-0.exe")

    print(f"📁 Scanner executable: {scanner_exe}")
    print(f"   Exists: {'✅' if scanner_exe.exists() else '❌'}")

    print(f"📁 Template Management: {template_exe}")
    print(f"   Exists: {'✅' if template_exe.exists() else '❌'}")

    print("\n📋 Release Directory Structure:")
    print("├── release/")
    print("│   ├── scanner/")
    print("│   │   └── Scanner_1-0.exe")
    print("│   └── backend/")
    print("│       └── template_management_1-0.exe")

    print("\n🎉 Both applications compiled successfully!")


def main():
    """Main build process."""
    print("=" * 60)
    print("🏗️  KrathongScanner Build Script")
    print("=" * 60)
    print("Building Scanner_1-0 and template_management_1-0")
    print("=" * 60)

    # Change to project root
    os.chdir(Path(__file__).parent)

    # Check dependencies
    if not check_pyinstaller():
        return 1

    # Setup directories
    setup_directories()

    # Build applications
    scanner_success = build_scanner()
    template_success = build_template_creator()

    # Cleanup
    cleanup()

    # Show results
    if scanner_success and template_success:
        show_results()
        return 0
    else:
        print("\n❌ Build failed for one or more applications")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
