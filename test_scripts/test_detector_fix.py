#!/usr/bin/env python3
"""
Test script to verify the fixed detector behavior with TESTEST.png
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import cv2

from src.aruco_detector.detector import ArUcoDetector


def test_detector():
    print("=== Testing ArUco Detector with TESTEST.png ===")

    # Initialize detector
    detector = ArUcoDetector()

    # Load test image
    test_image_path = "data/templates/TESTTEST.png"
    if not Path(test_image_path).exists():
        print(f"❌ Test image not found: {test_image_path}")
        return

    image = cv2.imread(test_image_path)
    if image is None:
        print(f"❌ Failed to load image: {test_image_path}")
        return

    print(f"✅ Loaded image: {test_image_path}")
    print(f"📏 Image shape: {image.shape}")

    # Detect markers
    marker_data_list = detector.detect_markers(image)
    print(f"🔍 Detected {len(marker_data_list)} markers")

    if marker_data_list:
        marker_ids = [marker.id for marker in marker_data_list]
        print(f"🎯 Detected markers: {marker_ids}")

        # Detect template
        template_id = detector.detect_template(marker_ids)
        print(f"📋 Template detected: {template_id}")

        if template_id:
            # Get mask path
            mask_path = detector.get_template_mask_path()
            print(f"🎭 Mask path: {mask_path}")

            if mask_path and Path(mask_path).exists():
                print(f"✅ Mask file exists: {mask_path}")
                return True
            else:
                print(f"❌ Mask file not found or invalid: {mask_path}")
                return False
        else:
            print("❌ No template detected")
            return False
    else:
        print("❌ No markers detected")
        return False


if __name__ == "__main__":
    success = test_detector()
    if success:
        print("\n🎉 Test PASSED: Detector correctly identified template and mask!")
    else:
        print("\n💥 Test FAILED: Issues with template/mask detection")
    sys.exit(0 if success else 1)
