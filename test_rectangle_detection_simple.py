#!/usr/bin/env python3
"""
Simple test to verify rectangle detection is working correctly.
"""

import sys
from pathlib import Path

import cv2
import numpy as np

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from auto_directory_detector import AutoDirectoryDetector


def test_rectangle_detection():
    """Test rectangle detection on real photos."""

    # Test image path
    test_image = "data/test_images/real_photo_test.jpg"
    output_dir = "temp_test_output"

    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)

    # Create detector with rectangle detection enabled
    detector = AutoDirectoryDetector(
        input_directory="temp_input",
        output_directory=output_dir,
        use_rectangle_detection=True,
        use_homography=True,
    )

    # Test direct rectangle detection
    print(f"🧪 Testing rectangle detection on: {test_image}")

    if not Path(test_image).exists():
        print(f"❌ Test image not found: {test_image}")
        return False

    # Load test image
    image = cv2.imread(test_image)
    if image is None:
        print(f"❌ Could not load image: {test_image}")
        return False

    print(f"📏 Input image dimensions: {image.shape[1]}x{image.shape[0]}")

    # Test rectangle detection
    try:
        corners = detector.find_rectangle_contour(image)
        if corners is not None:
            print(f"✅ Rectangle detected! Corners found: {corners.shape}")
            print(f"📍 Corner coordinates: {corners.tolist()}")

            # Reshape corners for four_point_transform (needs to be (4, 2) not (4, 1, 2))
            corners_reshaped = corners.reshape(4, 2)
            print(f"📐 Reshaped corners: {corners_reshaped.shape} - {corners_reshaped}")

            # Test perspective correction
            corrected = detector.four_point_transform(image, corners_reshaped)
            if corrected is not None:
                print(
                    f"📐 Perspective corrected image: {corrected.shape[1]}x{corrected.shape[0]}"
                )

                # Save result
                output_path = Path(output_dir) / "test_rectangle_result.png"
                cv2.imwrite(str(output_path), corrected)
                print(f"💾 Saved result to: {output_path}")
                return True
            else:
                print("❌ Perspective correction failed")
                return False
        else:
            print("❌ No rectangle detected")
            return False

    except Exception as e:
        print(f"❌ Rectangle detection failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🔍 Testing Rectangle Detection")
    print("=" * 50)

    success = test_rectangle_detection()

    if success:
        print("\n✅ Rectangle detection test PASSED!")
    else:
        print("\n❌ Rectangle detection test FAILED!")

    print("=" * 50)
