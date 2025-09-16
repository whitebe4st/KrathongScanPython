#!/usr/bin/env python3
"""
Clean up temporary test scripts used for mask automation experiments.
"""
import os
from pathlib import Path


def cleanup_test_scripts():
    """Remove temporary test scripts and keep only essential ones."""
    print("🧹 Cleaning Up Test Scripts")
    print("=" * 30)

    # Current directory
    project_dir = Path(".")

    # Scripts to remove (temporary/experimental)
    remove_scripts = [
        "adjust_mask_position.py",
        "create_positioned_masks.py",
        "create_custom_sized_masks.py",
        "test_positioned_masks.py",
        "test_custom_sized_masks.py",
        "convert_artwork_to_mask.py",
        "test_converted_artwork_mask.py",
        "cleanup_automated_masks.py",
        "cleanup_test_scripts.py",  # This script itself
    ]

    # Scripts to keep (essential/production)
    keep_scripts = ["main.py", "test_detection.py", "test_homography_direct.py"]

    print(f"📁 Scanning project directory: {project_dir}")

    print(f"\n🔍 SCANNING FOR TEST SCRIPTS:")
    print("-" * 32)

    files_removed = []
    files_kept = []

    for script_name in remove_scripts:
        script_path = project_dir / script_name
        if script_path.exists():
            try:
                script_path.unlink()
                files_removed.append(script_name)
                print(f"🗑️  Removed: {script_name}")
            except Exception as e:
                print(f"❌ Failed to remove {script_name}: {e}")
        else:
            print(f"⚪ Not found: {script_name}")

    print(f"\n✅ ESSENTIAL SCRIPTS KEPT:")
    print("-" * 26)

    for script_name in keep_scripts:
        script_path = project_dir / script_name
        if script_path.exists():
            files_kept.append(script_name)
            print(f"📄 {script_name}")
        else:
            print(f"⚠️  Missing: {script_name}")

    print(f"\n📊 CLEANUP SUMMARY:")
    print("-" * 20)
    print(f"Scripts removed: {len(files_removed)}")
    print(f"Essential scripts kept: {len(files_kept)}")

    print(f"\n🎯 PRODUCTION SETUP:")
    print("-" * 20)
    print("✅ Hand-optimized mask: krathong1_mask_final.png")
    print("✅ Detection system: src/aruco_detector/detector.py")
    print("✅ Test script: test_detection.py")
    print("✅ Main entry: main.py")

    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 20)
    print("1. Your system is now clean and production-ready")
    print("2. Use krathong1_mask_final.png as your mask")
    print("3. Focus on other features (WebSocket API, etc.)")
    print("4. Mask automation can be revisited later if needed")

    print(f"\n🚀 Ready for production development!")


if __name__ == "__main__":
    cleanup_test_scripts()
