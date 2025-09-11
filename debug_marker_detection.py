#!/usr/bin/env python3
"""
Debug Marker Detection Tool

This tool helps diagnose marker detection issues when importing images for scanning.
It will show what markers are detected in an image and whether they match known templates.
"""

import sys
from pathlib import Path

import cv2

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from apps.scanner.template_manager import TemplateManager
from src.aruco_detector.detector import ArUcoDetector


def debug_image_markers(image_path: str):
    """Debug marker detection for a specific image."""
    print(f"🔍 Debugging marker detection for: {image_path}")
    print("=" * 60)

    # Initialize components
    detector = ArUcoDetector()
    manager = TemplateManager()

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image: {image_path}")
        return

    print(f"✅ Image loaded: {image.shape[1]}x{image.shape[0]} pixels")

    # Get available templates
    templates = manager.read_all_templates()
    print(f"\n📊 Available templates in scanner.db:")
    for template in templates:
        status = "✅ Active" if template.is_active else "❌ Inactive"
        print(f"   - {template.name}: markers {template.marker_ids} ({status})")

    print(f"\n🎯 Hardcoded templates:")
    hardcoded = {
        "krathong1": [0, 1, 2, 3],
        "krathong2": [4, 5, 6, 7],
        "krathong3": [8, 9, 10, 11],
        "krathong4": [12, 13, 14, 15],
        "krathong5": [16, 17, 18, 19],
    }
    for name, markers in hardcoded.items():
        print(f"   - {name}: markers {markers}")

    # Detect markers
    print(f"\n🔍 Detecting markers in image...")
    markers = detector.detect_markers(image)

    if not markers:
        print("❌ No markers detected in image!")
        print("\n💡 Possible solutions:")
        print("   1. Check if image contains ArUco markers")
        print("   2. Verify markers are clear and not distorted")
        print("   3. Try improving image lighting/quality")
        print("   4. Make sure markers use 4X4_50 dictionary")
        return

    print(f"✅ Found {len(markers)} markers:")
    detected_ids = []
    for marker in markers:
        print(f"   - Marker ID {marker.id} at center {marker.center}")
        detected_ids.append(marker.id)

    # Check template matching
    print(f"\n🎯 Template matching:")
    template_id = detector.detect_template(detected_ids)

    if template_id:
        print(f"✅ Matched template: {template_id}")

        # Check corner markers
        corner_markers = detector.get_corner_markers(markers)
        if corner_markers:
            print(f"✅ Found corner markers for perspective correction")
        else:
            print(f"⚠️  No corner markers found - may affect cropping")
    else:
        print(f"❌ No template matched detected markers: {detected_ids}")
        print(f"\n💡 Solutions:")
        print(f"   1. Add a custom template with markers {detected_ids}")
        print(f"   2. Use template maker to create matching template")
        print(f"   3. Check if markers match expected template pattern")

    # Additional diagnostics
    print(f"\n📋 Marker ID analysis:")
    for marker_id in detected_ids:
        if marker_id in detector.marker_to_template:
            template_name = detector.marker_to_template[marker_id]
            print(f"   - ID {marker_id}: belongs to template '{template_name}'")
        else:
            print(f"   - ID {marker_id}: not assigned to any template")


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python debug_marker_detection.py <image_path>")
        print("\nExample:")
        print("  python debug_marker_detection.py data/test_images/krathong_test1.png")
        return

    image_path = sys.argv[1]
    if not Path(image_path).exists():
        print(f"❌ Image file not found: {image_path}")
        return

    debug_image_markers(image_path)


if __name__ == "__main__":
    main()
