#!/usr/bin/env python3
"""
Debug script to test if rectangle detection works in web server context.
"""

import os
import sys
from pathlib import Path

# Set up the same environment as the web server
print("🔍 Testing Rectangle Detection in Web Server Context")
print("=" * 60)

# Change to the correct directory (same as web server)
os.chdir(Path(__file__).parent)
print(f"📁 Working directory: {os.getcwd()}")

# Test the import exactly like the web server does
try:
    print("\n1️⃣ Testing import...")
    from src.rectangle_cropper import detect_and_crop_rectangle

    print("✅ Import successful")

    # Test with an actual image
    print("\n2️⃣ Testing detection...")
    import cv2

    test_image_path = "data/test_images/real_photo_test.jpg"
    if Path(test_image_path).exists():
        image = cv2.imread(test_image_path)
        print(f"📏 Loaded image: {image.shape[1]}x{image.shape[0]}")

        # Test detection exactly like web server
        rect_cropped, rect_contour = detect_and_crop_rectangle(image)

        if rect_cropped is not None:
            print(
                f"✅ Rectangle detection successful: {rect_cropped.shape[1]}x{rect_cropped.shape[0]}"
            )
            print(
                f"📐 Contour found: {rect_contour.shape if rect_contour is not None else 'None'}"
            )

            # Test the resize logic exactly like web server
            TARGET_W, TARGET_H = 779, 457
            if rect_cropped.shape[1] != TARGET_W or rect_cropped.shape[0] != TARGET_H:
                processing_image = cv2.resize(
                    rect_cropped,
                    (TARGET_W, TARGET_H),
                    interpolation=cv2.INTER_LANCZOS4,
                )
                print(f"📏 Resized to {TARGET_W}x{TARGET_H} for mask alignment")
            else:
                processing_image = rect_cropped
                print(f"📏 No resize needed, already {TARGET_W}x{TARGET_H}")

            # Save result
            cv2.imwrite("web_server_test_crop.png", processing_image)
            print("💾 Saved test result to: web_server_test_crop.png")

        else:
            print("❌ Rectangle detection returned None")
            print("🔍 Let's debug why...")

            # Debug the detection process
            from src.rectangle_cropper import find_rectangle_contour

            contour = find_rectangle_contour(image)
            if contour is None:
                print("❌ find_rectangle_contour returned None")

                # Try manual debugging
                import numpy as np

                h, w = image.shape[:2]
                min_area = 0.08 * (h * w)
                print(f"📐 Image size: {w}x{h}, Min area: {min_area}")

                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                print(f"📐 Gray image: {gray.shape}")

                # Test Canny edge detection
                edges = cv2.Canny(gray, 50, 150)
                contours, _ = cv2.findContours(
                    edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                print(f"🔍 Found {len(contours)} contours with Canny")

                if contours:
                    largest = max(contours, key=cv2.contourArea)
                    largest_area = cv2.contourArea(largest)
                    print(
                        f"📐 Largest contour area: {largest_area} (min required: {min_area})"
                    )

                    peri = cv2.arcLength(largest, True)
                    approx = cv2.approxPolyDP(largest, 0.02 * peri, True)
                    print(f"📐 Largest contour vertices: {len(approx)}")

            else:
                print(f"✅ find_rectangle_contour found contour: {contour.shape}")
    else:
        print(f"❌ Test image not found: {test_image_path}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
print("🏁 Test complete")
