#!/usr/bin/env python3
"""
Test script to extract the area within ArUco markers WITHOUT homography.
This will crop the rectangular region defined by the marker centers.
"""

import sys

sys.path.insert(0, "src")

from pathlib import Path

import cv2
import numpy as np

from aruco_detector.detector import ArUcoDetector


def extract_marker_area_no_homography(image_path: str, output_path: str):
    """
    Extract the area within the 4 corner ArUco markers without homography.
    Just crop the rectangular region defined by marker centers.

    Args:
        image_path: Path to input image
        output_path: Path for output image
    """
    print("🎯 Testing Marker Area Extraction (No Homography)")
    print("=" * 50)

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

    # Step 3: Get the bounding box of the markers
    print("📐 Calculating bounding box...")

    # Use the detector's cropping method for precise extraction
    cropped = detector._crop_marker_area(image, corner_markers)

    print(f"📏 Cropped area size: {cropped.shape[1]}x{cropped.shape[0]} pixels")

    # Step 4: Save the cropped area
    print("✂️ Saving cropped area...")

    # Step 5: Save the cropped area
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    success = cv2.imwrite(str(output_file), cropped)
    if success:
        print("✅ Marker area cropped successfully!")
        print(f"📁 Check the output: {output_path}")

        # Print some info about the cropped area
        h, w = cropped.shape[:2]
        print(f"📏 Cropped area size: {w}x{h} pixels")

        # Calculate average brightness
        gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray)
        print(f"💡 Average brightness: {avg_brightness:.1f}/255")

        if avg_brightness > 200:
            print("⚠️ Warning: Image appears very bright/white")
        elif avg_brightness < 50:
            print("⚠️ Warning: Image appears very dark")
        else:
            print("✅ Brightness looks normal")

    else:
        print("❌ Failed to save cropped area")
        return False

    return True


def main():
    """Main function to run the no-homography extraction test."""
    test_image = "data/test_images/krathong_test2.png"
    output_image = "data/test_output/marker_area_no_homography_test2.png"

    success = extract_marker_area_no_homography(test_image, output_image)

    if success:
        print("\n🎉 Test completed successfully!")
        print("This shows the area without any perspective correction.")
        print("Compare this with the homography version to see the difference.")
    else:
        print("\n💥 Test failed!")
        print("Check the logs above for details.")


if __name__ == "__main__":
    main()
