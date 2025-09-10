#!/usr/bin/env python3
"""
Debug script to investigate cropping issues.
This will test all aspects of the rectangle detection and cropping pipeline.
"""

import sys
from pathlib import Path

import cv2
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from aruco_detector import ArUcoDetector
from auto_directory_detector import AutoDirectoryDetector


def test_full_pipeline():
    """Test the complete pipeline to see what's happening"""
    print("🔍 Full Pipeline Debug Test")
    print("=" * 50)

    # Test image
    test_image_path = "data/test_images/real_photo_test.jpg"
    if not Path(test_image_path).exists():
        print(f"❌ Test image not found: {test_image_path}")
        return

    # Load image
    image = cv2.imread(test_image_path)
    print(f"📏 Original image: {image.shape[1]}x{image.shape[0]}")

    # Test 1: AutoDirectoryDetector with rectangle detection
    print("\n1️⃣ Testing AutoDirectoryDetector with rectangle detection...")
    detector = AutoDirectoryDetector(
        input_directory="temp_input",
        output_directory="temp_output",
        use_rectangle_detection=True,
    )

    # Process image
    result = detector.process_image(test_image_path)
    if result:
        print(f"✅ AutoDirectoryDetector processed successfully")
        print(f"📁 Output: {result}")
    else:
        print("❌ AutoDirectoryDetector failed")

    # Test 2: Manual rectangle detection
    print("\n2️⃣ Testing manual rectangle detection...")
    corners = detector.find_rectangle_contour(image)
    if corners is not None:
        print(f"✅ Rectangle corners found: {corners.shape}")
        corners_reshaped = corners.reshape(4, 2)

        # Apply transformation
        cropped = detector.four_point_transform(image, corners_reshaped)
        if cropped is not None:
            print(f"📐 Manually cropped result: {cropped.shape[1]}x{cropped.shape[0]}")

            # Save manual result
            cv2.imwrite("debug_manual_crop.png", cropped)
            print("💾 Saved manual crop to: debug_manual_crop.png")
        else:
            print("❌ Manual transformation failed")
    else:
        print("❌ No rectangle corners found manually")

    # Test 3: ArUco detector for comparison
    print("\n3️⃣ Testing ArUco detector for comparison...")
    aruco_detector = ArUcoDetector()
    try:
        markers = aruco_detector.detect_markers(image)
        if markers:
            print(f"✅ ArUco detection found {len(markers)} markers")
            template_result = aruco_detector.detect_template(image)
            if template_result:
                print(f"✅ ArUco template detection successful")
            else:
                print("❌ ArUco template detection failed")
        else:
            print("❌ No ArUco markers found")
    except Exception as e:
        print(f"❌ ArUco detection error: {e}")


def test_different_approaches():
    """Test different cropping approaches"""
    print("\n🧪 Testing Different Cropping Approaches")
    print("=" * 50)

    test_image_path = "data/test_images/real_photo_test.jpg"
    image = cv2.imread(test_image_path)

    # Approach 1: Simple contour detection
    print("\n🔹 Approach 1: Simple contour detection")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        # Find largest contour
        largest_contour = max(contours, key=cv2.contourArea)

        # Approximate to rectangle
        epsilon = 0.02 * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)

        if len(approx) == 4:
            print(f"✅ Simple approach found rectangle: {approx.reshape(4, 2)}")

            # Apply transformation
            detector = AutoDirectoryDetector("temp", "temp")
            cropped = detector.four_point_transform(image, approx.reshape(4, 2))
            if cropped is not None:
                cv2.imwrite("debug_simple_crop.png", cropped)
                print(f"💾 Simple crop saved: {cropped.shape[1]}x{cropped.shape[0]}")
        else:
            print(f"❌ Simple approach found {len(approx)} points, not 4")

    # Approach 2: Morphological operations
    print("\n🔹 Approach 2: Morphological operations")
    kernel = np.ones((5, 5), np.uint8)
    morphed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        epsilon = 0.02 * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)

        if len(approx) == 4:
            print(f"✅ Morphological approach found rectangle")
            detector = AutoDirectoryDetector("temp", "temp")
            cropped = detector.four_point_transform(image, approx.reshape(4, 2))
            if cropped is not None:
                cv2.imwrite("debug_morph_crop.png", cropped)
                print(
                    f"💾 Morphological crop saved: {cropped.shape[1]}x{cropped.shape[0]}"
                )

    # Approach 3: Adaptive threshold
    print("\n🔹 Approach 3: Adaptive threshold")
    adaptive = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    contours, _ = cv2.findContours(adaptive, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        epsilon = 0.02 * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)

        if len(approx) == 4:
            print(f"✅ Adaptive threshold found rectangle")
            detector = AutoDirectoryDetector("temp", "temp")
            cropped = detector.four_point_transform(image, approx.reshape(4, 2))
            if cropped is not None:
                cv2.imwrite("debug_adaptive_crop.png", cropped)
                print(f"💾 Adaptive crop saved: {cropped.shape[1]}x{cropped.shape[0]}")


def main():
    """Main debug function"""
    print("🚀 Starting Comprehensive Cropping Debug")
    print("=" * 60)

    # Test full pipeline
    test_full_pipeline()

    # Test different approaches
    test_different_approaches()

    print("\n✅ Debug complete! Check the generated debug_*.png files")
    print("📁 Files generated:")
    for file in Path(".").glob("debug_*.png"):
        print(f"   - {file}")


if __name__ == "__main__":
    main()
