#!/usr/bin/env python3
"""
Test script for ArUco detection system.
"""

import sys

sys.path.insert(0, "src")

from aruco_detector.detector import ArUcoDetector


def main():
    print("🎯 Testing ArUco Detection System (No Homography)")
    print("=" * 50)

    # Initialize detector
    detector = ArUcoDetector(dict_type="4X4_50", marker_size=0.04)

    # Define paths
    test_image = "data/test_images/krathong_test2.png"
    template_mask = "data/markers/templates/krathong1_mask2.png"
    output_image = "data/test_output/krathong_test2_processed.png"

    print(f"📸 Test image: {test_image}")
    print(f"🎭 Template mask: {template_mask}")
    print(f"💾 Output: {output_image}")
    print()

    # Process the image with simple cropping (no homography)
    print("🔄 Processing image (simple cropping)...")
    success = detector.process_image(test_image, template_mask, output_image)

    if success:
        print("✅ Image processing completed successfully!")
        print(f"📁 Check the output: {output_image}")
        print(f"📄 Metadata: {output_image.replace('.png', '.json')}")
    else:
        print("❌ Image processing failed!")
        print("Check the logs above for details.")


if __name__ == "__main__":
    main()
