#!/usr/bin/env python3
"""
Test script to extract the area within ArUco markers.
This will help us see what content is actually being captured.
"""

import sys

sys.path.insert(0, "src")

from pathlib import Path

import cv2
import numpy as np

from aruco_detector.detector import ArUcoDetector


def extract_marker_area(image_path: str, output_path: str):
    """
    Extract the area within the 4 corner ArUco markers.

    Args:
        image_path: Path to input image
        output_path: Path for output image
    """
    print("🎯 Testing Marker Area Extraction")
    print("=" * 40)

    # Initialize detector
    detector = ArUcoDetector(dict_type="4X4_50", marker_size=0.04)

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image from {image_path}")
        return False

    print(f"📸 Input image: {image_path}")
    print(f"💾 Output: {output_path}")
    print()

    # Step 1: Detect ArUco markers
    print("🔍 Detecting markers...")
    markers = detector.detect_markers(image)
    if not markers:
        print("❌ No markers detected")
        return False

    # Step 2: Get corner markers
    print("📍 Finding corner markers...")
    corner_markers = detector.get_corner_markers(markers)
    if corner_markers is None:
        print("❌ Could not find all corner markers")
        return False

    # Step 3: Create perspective transform
    print("🔄 Creating perspective transform...")
    homography = detector.create_perspective_transform(corner_markers)
    if homography is None:
        print("❌ Could not create perspective transform")
        return False

    # Step 4: Apply perspective correction (extract marker area)
    print("✂️ Extracting marker area...")
    corrected = detector.apply_perspective_correction(image, homography)

    # Step 5: Save the extracted area
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    success = cv2.imwrite(str(output_file), corrected)
    if success:
        print("✅ Marker area extracted successfully!")
        print(f"📁 Check the output: {output_path}")

        # Print some info about the extracted area
        h, w = corrected.shape[:2]
        print(f"📏 Extracted area size: {w}x{h} pixels")

        # Calculate average brightness to see if it's too white
        gray = cv2.cvtColor(corrected, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray)
        print(f"💡 Average brightness: {avg_brightness:.1f}/255")

        if avg_brightness > 200:
            print("⚠️ Warning: Image appears very bright/white")
        elif avg_brightness < 50:
            print("⚠️ Warning: Image appears very dark")
        else:
            print("✅ Brightness looks normal")

    else:
        print("❌ Failed to save extracted area")
        return False

    return True


def main():
    """Main function to run the marker area extraction test."""
    test_image = "data/test_images/krathong_test1.png"
    output_image = "data/test_output/marker_area_only.png"

    success = extract_marker_area(test_image, output_image)

    if success:
        print("\n🎉 Test completed successfully!")
        print("This shows you exactly what area is being captured by the markers.")
        print("If this looks good, then the issue is with the template mask.")
        print("If this is too white, then the perspective correction needs adjustment.")
    else:
        print("\n💥 Test failed!")
        print("Check the logs above for details.")


if __name__ == "__main__":
    main()
