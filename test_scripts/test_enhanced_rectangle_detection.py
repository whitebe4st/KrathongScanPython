#!/usr/bin/env python3
"""
Test enhanced rectangle detection on real photos.
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import cv2
import numpy as np

from auto_directory_detector import AutoDirectoryDetector


def test_enhanced_detection():
    """Test the enhanced rectangle detection on real photos"""

    # Initialize detector with rectangle detection
    detector = AutoDirectoryDetector(
        input_directory="data/test_images",
        output_directory="test_enhanced_output",
        use_rectangle_detection=True,
    )

    # Test on a real photo
    test_image = "data/test_images/download.jpg"
    output_path = Path("test_enhanced_output/processed_download.png")

    print(f"Testing enhanced detection on: {test_image}")

    # Create output directory
    output_path.parent.mkdir(exist_ok=True)

    # Process the image
    success = detector.process_with_rectangle_detection(Path(test_image), output_path)

    if success:
        print(f"✅ Enhanced detection successful! Output: {output_path}")
        print(f"📁 Check the output file: {output_path.absolute()}")

        # Show some stats
        if output_path.exists():
            processed_img = cv2.imread(str(output_path))
            if processed_img is not None:
                h, w = processed_img.shape[:2]
                print(f"📏 Output dimensions: {w}x{h}")
    else:
        print("❌ Enhanced detection failed")

        # Try to show what the detector found
        image = cv2.imread(test_image)
        if image is not None:
            print(f"📸 Input image dimensions: {image.shape[1]}x{image.shape[0]}")

            # Test just the contour detection
            contour = detector.find_rectangle_contour(image)
            if contour is not None:
                print(f"🔍 Rectangle found but processing failed")
                area = cv2.contourArea(contour)
                print(f"📏 Rectangle area: {area}")
            else:
                print(f"🔍 No rectangle contour detected at all")


if __name__ == "__main__":
    test_enhanced_detection()
