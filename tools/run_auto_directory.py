#!/usr/bin/env python3
"""
Standalone Auto-Directory Monitor for KrathongScanner.

This script can be used to test the auto-directory functionality independently.
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auto_directory_detector import run_auto_directory_detection


def main():
    """Main function for standalone auto-directory monitoring."""
    print("🔄 KrathongScanner - Auto-Directory Monitor")
    print("=" * 50)

    # Get input directory
    while True:
        input_dir = input(
            "\n📁 Enter directory to monitor for new krathong images: "
        ).strip()
        if input_dir and Path(input_dir).exists():
            break
        elif input_dir:
            print(f"❌ Directory does not exist: {input_dir}")
        else:
            print("❌ Please enter a valid directory path")

    # Get output directory (optional)
    output_dir = input(
        "\n📤 Enter output directory (press Enter for default 'data/processed_images'): "
    ).strip()
    if not output_dir:
        output_dir = "data/processed_images"

    # Get check interval (optional)
    interval_input = input(
        "\n⏱️  Enter check interval in seconds (press Enter for default 2.0): "
    ).strip()
    try:
        check_interval = float(interval_input) if interval_input else 2.0
    except ValueError:
        check_interval = 2.0
        print("⚠️  Invalid interval, using default 2.0 seconds")

    print(f"\n🚀 Starting Auto-Directory Monitor...")
    print(f"📁 Input: {input_dir}")
    print(f"📤 Output: {output_dir}")
    print(f"⏱️  Interval: {check_interval}s")
    print(f"\n💡 Drop krathong images into the input folder!")
    print(f"🛑 Press Ctrl+C to stop\n")

    try:
        # Start monitoring
        run_auto_directory_detection(input_dir, output_dir, check_interval)
    except KeyboardInterrupt:
        print(f"\n👋 Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
