#!/usr/bin/env python3
"""
Test script for Auto-Directory Mode.

This script demonstrates how to use the auto-directory mode and provides
a simple test setup.
"""

import sys
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_auto_directory_mode():
    """Test the auto-directory mode with a simple setup."""
    print("🧪 Testing Auto-Directory Mode")
    print("=" * 40)

    # Test directories
    test_dir = Path("test_auto_directory")
    input_dir = test_dir / "input"
    output_dir = test_dir / "output"

    # Create test directories
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 Test Input Directory: {input_dir}")
    print(f"📤 Test Output Directory: {output_dir}")

    # Check for test images
    test_images = (
        list(Path("data/test_images").glob("*.png"))
        if Path("data/test_images").exists()
        else []
    )

    if test_images:
        print(f"\n📸 Found {len(test_images)} test images in data/test_images/")
        print("💡 You can copy these to the input directory to test:")
        for img in test_images[:3]:  # Show first 3
            print(f"   - {img.name}")
    else:
        print("\n⚠️  No test images found in data/test_images/")
        print("💡 You can add krathong images to the input directory manually")

    print(f"\n🚀 To test the auto-directory mode:")
    print("-" * 40)
    print(f"1. Command Line Test:")
    print(
        f'   python main.py --mode auto-directory --input-dir "{input_dir}" --output-dir "{output_dir}"'
    )
    print(f"\n2. UI Test:")
    print(f"   python main.py")
    print(f"   Click '🔄 Auto-Directory Monitor'")
    print(f"   Select the input directory: {input_dir.absolute()}")
    print(f"\n3. Standalone Test:")
    print(f"   python run_auto_directory.py")

    print(f"\n📝 Test Steps:")
    print("-" * 15)
    print("1. Start the auto-directory monitor")
    print("2. Copy a krathong image to the input directory")
    print("3. Watch it get processed automatically")
    print("4. Check the output directory for results")

    print(f"\n✅ Test setup complete!")


def copy_test_image():
    """Copy a test image to the input directory for testing."""
    import shutil

    test_images = (
        list(Path("data/test_images").glob("*.png"))
        if Path("data/test_images").exists()
        else []
    )

    if not test_images:
        print("❌ No test images available to copy")
        return

    input_dir = Path("test_auto_directory/input")

    # Copy the first test image
    source_image = test_images[0]
    dest_image = input_dir / f"test_{int(time.time())}_{source_image.name}"

    try:
        shutil.copy2(source_image, dest_image)
        print(f"✅ Copied test image: {dest_image.name}")
        print(f"📁 Location: {dest_image}")
    except Exception as e:
        print(f"❌ Error copying test image: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "copy":
        copy_test_image()
    else:
        test_auto_directory_mode()
