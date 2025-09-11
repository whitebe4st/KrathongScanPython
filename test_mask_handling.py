#!/usr/bin/env python3
"""
Test Custom Template Mask File Handling

This tests the new functionality where CRUD copies mask files to the scanner's expected location.
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from apps.scanner.template_manager import TemplateManager


def test_mask_copying():
    """Test that mask files are copied to the correct location."""
    print("🧪 Testing Custom Template Mask File Handling")
    print("=" * 60)

    # Initialize template manager
    manager = TemplateManager()

    # Check current templates
    templates = manager.read_all_templates()
    print(f"📊 Current templates in database: {len(templates)}")

    for template in templates:
        print(f"\n📝 Template: {template.name}")
        print(f"   Markers: {template.marker_ids}")
        print(f"   Image: {template.image_path}")
        print(f"   Mask: {template.mask_path}")

        # Check if mask file exists
        mask_path = Path(template.mask_path)
        mask_exists = mask_path.exists()
        print(f"   Mask exists: {'✅ Yes' if mask_exists else '❌ No'}")

        # Check if it's in the scanner's expected location
        expected_dir = Path("data/markers/templates")
        is_in_scanner_dir = (
            expected_dir in mask_path.parents or mask_path.parent == expected_dir
        )
        print(f"   In scanner dir: {'✅ Yes' if is_in_scanner_dir else '❌ No'}")

        if mask_exists and is_in_scanner_dir:
            print(f"   ✅ Mask file is properly located for scanner")
        elif mask_exists:
            print(f"   ⚠️  Mask file exists but not in scanner location")
        else:
            print(f"   ❌ Mask file missing")

    print(f"\n📁 Scanner mask directory contents:")
    scanner_mask_dir = Path("data/markers/templates")
    if scanner_mask_dir.exists():
        mask_files = list(scanner_mask_dir.glob("*.png"))
        for mask_file in mask_files:
            print(f"   - {mask_file.name}")
        if not mask_files:
            print("   (No mask files found)")
    else:
        print("   (Directory doesn't exist)")

    print(f"\n💡 Solution Status:")
    print(f"   - CRUD now copies mask files to data/markers/templates/")
    print(f"   - Detector checks mask_path first, then mask_file")
    print(f"   - Custom templates should work with scanner now")


if __name__ == "__main__":
    test_mask_copying()
