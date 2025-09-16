#!/usr/bin/env python3
"""
Test the enhanced rectangle detection that looks for inner rectangles.
"""

import sys
from pathlib import Path

import cv2

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from enhanced_rectangle_cropper import detect_and_crop_rectangle_enhanced


def test_enhanced_detection():
    """Test the enhanced rectangle detection"""
    print("🎯 Testing Enhanced Rectangle Detection")
    print("=" * 50)

    # Test with the real photo
    test_image_path = "data/test_images/real_photo_test.jpg"
    if not Path(test_image_path).exists():
        print(f"❌ Test image not found: {test_image_path}")
        return

    image = cv2.imread(test_image_path)
    print(f"📏 Original image: {image.shape[1]}x{image.shape[0]}")

    # Test enhanced detection
    rect_cropped, rect_contour = detect_and_crop_rectangle_enhanced(image)

    if rect_cropped is not None:
        print(
            f"✅ Enhanced detection successful: {rect_cropped.shape[1]}x{rect_cropped.shape[0]}"
        )

        # Save result
        cv2.imwrite("enhanced_rectangle_crop.png", rect_cropped)
        print("💾 Saved enhanced crop to: enhanced_rectangle_crop.png")

        # Also save the original for comparison
        cv2.imwrite("original_for_comparison.png", image)
        print("💾 Saved original to: original_for_comparison.png")

        return True
    else:
        print("❌ Enhanced rectangle detection failed")
        return False


if __name__ == "__main__":
    test_enhanced_detection()
