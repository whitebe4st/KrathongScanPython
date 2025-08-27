#!/usr/bin/env python3
"""
Clean up automated mask files and revert to hand-optimized approach.
"""
import os
from pathlib import Path


def cleanup_automated_masks():
    """Remove automated mask files and keep only hand-optimized ones."""
    print("🧹 Cleaning Up Automated Masks")
    print("=" * 35)

    # Directory containing masks
    masks_dir = Path("data/markers/templates")

    if not masks_dir.exists():
        print(f"❌ Masks directory not found: {masks_dir}")
        return

    print(f"📁 Cleaning directory: {masks_dir}")

    # Files to keep (hand-optimized)
    keep_files = {
        "krathong1_mask.png",
        "krathong1_mask2.png",
        "krathong1_mask_final.png",
    }

    # Files to remove (automated/generated)
    remove_patterns = [
        "1_mask.png",
        "1_optimized_*.png",
        "1_positioned_*.png",
        "1_custom_*.png",
        "*_comparison.png",
        "converted_from_existing.png",
    ]

    print(f"\n🔍 SCANNING FOR AUTOMATED MASKS:")
    print("-" * 35)

    files_to_remove = []
    files_to_keep = []

    # Scan all files in the directory
    for file_path in masks_dir.iterdir():
        if file_path.is_file():
            filename = file_path.name

            # Check if it's a file to keep
            if filename in keep_files:
                files_to_keep.append(filename)
                print(f"✅ KEEP: {filename} (hand-optimized)")
                continue

            # Check if it matches removal patterns
            should_remove = False
            for pattern in remove_patterns:
                if pattern.startswith("*") and pattern.endswith("*"):
                    # Contains pattern
                    middle = pattern[1:-1]
                    if middle in filename:
                        should_remove = True
                        break
                elif pattern.startswith("*"):
                    # Ends with pattern
                    suffix = pattern[1:]
                    if filename.endswith(suffix):
                        should_remove = True
                        break
                elif pattern.endswith("*"):
                    # Starts with pattern
                    prefix = pattern[:-1]
                    if filename.startswith(prefix):
                        should_remove = True
                        break
                else:
                    # Exact match
                    if filename == pattern:
                        should_remove = True
                        break

            if should_remove:
                files_to_remove.append(file_path)
                print(f"🗑️  REMOVE: {filename} (automated)")
            else:
                files_to_keep.append(filename)
                print(f"❓ KEEP: {filename} (unknown, keeping safe)")

    print(f"\n📊 CLEANUP SUMMARY:")
    print("-" * 20)
    print(f"Files to keep: {len(files_to_keep)}")
    print(f"Files to remove: {len(files_to_remove)}")

    if files_to_remove:
        print(f"\n🗑️  REMOVING AUTOMATED MASKS:")
        print("-" * 32)

        for file_path in files_to_remove:
            try:
                file_path.unlink()
                print(f"✅ Removed: {file_path.name}")
            except Exception as e:
                print(f"❌ Failed to remove {file_path.name}: {e}")

    print(f"\n📋 REMAINING MASKS:")
    print("-" * 20)

    remaining_files = list(masks_dir.glob("*.png"))
    if remaining_files:
        for file_path in sorted(remaining_files):
            file_size = file_path.stat().st_size
            print(f"📄 {file_path.name} ({file_size:,} bytes)")
    else:
        print("No mask files remaining")

    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 20)
    print("1. Use krathong1_mask_final.png as your production mask")
    print("2. It was hand-optimized and working well")
    print("3. Focus on other features while mask automation matures")
    print("4. The automated system can be improved later when needed")

    print(f"\n🎯 NEXT STEPS:")
    print("-" * 15)
    print("1. Update your detector to use:")
    print("   data/markers/templates/krathong1_mask_final.png")
    print("2. Test the system with the hand-optimized mask")
    print("3. Continue with other development priorities")

    print(f"\n🧹 Cleanup completed!")
    print("Back to reliable hand-optimized masks! 🎨")


if __name__ == "__main__":
    cleanup_automated_masks()
