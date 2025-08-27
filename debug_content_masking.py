#!/usr/bin/env python3
"""
Debug script to visualize what the content-aware masking is actually doing.
This will help us see if it's working correctly or if we need to revert.
"""
import sys

sys.path.insert(0, "src")

from pathlib import Path

import cv2
import numpy as np

from aruco_detector.detector import ArUcoDetector


def debug_content_masking():
    print("🔍 Debugging Content-Aware Masking")
    print("=" * 40)

    # Initialize detector
    detector = ArUcoDetector(dict_type="4X4_50", marker_size=0.04)

    # Test with the straight image first
    image_path = "data/test_images/krathong_test2.png"
    mask_path = "data/markers/templates/krathong1_mask2.png"

    # Load images
    image = cv2.imread(image_path)
    mask_template = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

    if image is None or mask_template is None:
        print("❌ Could not load images!")
        return

    print(f"📸 Original image: {image.shape}")
    print(f"🎭 Mask template: {mask_template.shape}")

    # Step 1: Crop the image first (simulate the detection pipeline)
    markers = detector.detect_markers(image)
    corner_markers = detector.get_corner_markers(markers)
    cropped = detector._crop_marker_area(image, corner_markers)

    print(f"✂️ Cropped image: {cropped.shape}")

    # Step 2: Debug the content detection process
    image_gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

    # Find non-white pixels (drawing content)
    _, content_mask = cv2.threshold(image_gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Find contours of content
    contours, _ = cv2.findContours(
        content_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    print(f"🔍 Found {len(contours)} contours")

    if contours:
        # Find the largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        contour_area = cv2.contourArea(largest_contour)

        # Get the center of the content
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            content_center_x = int(M["m10"] / M["m00"])
            content_center_y = int(M["m01"] / M["m00"])
            print(f"📍 Content center: ({content_center_x}, {content_center_y})")
            print(f"📏 Content area: {contour_area} pixels")
        else:
            content_center_x = cropped.shape[1] // 2
            content_center_y = cropped.shape[0] // 2
            print(f"📍 Using image center: ({content_center_x}, {content_center_y})")
    else:
        content_center_x = cropped.shape[1] // 2
        content_center_y = cropped.shape[0] // 2
        print(
            f"📍 No content found, using image center: ({content_center_x}, {content_center_y})"
        )

    # Step 3: Show what the mask positioning does
    _, mask_binary = cv2.threshold(mask_template, 128, 255, cv2.THRESH_BINARY)

    # Calculate scale
    if contours:
        content_area = cv2.contourArea(largest_contour)
        image_area = cropped.shape[0] * cropped.shape[1]
        content_ratio = content_area / image_area
        scale_factor = max(0.3, min(1.2, content_ratio * 3))
    else:
        scale_factor = 1.0

    print(f"📊 Scale factor: {scale_factor:.2f}")

    # Create scaled mask
    new_mask_width = int(mask_template.shape[1] * scale_factor)
    new_mask_height = int(mask_template.shape[0] * scale_factor)
    scaled_mask = cv2.resize(mask_template, (new_mask_width, new_mask_height))

    print(f"🎭 Scaled mask: {new_mask_width}x{new_mask_height}")

    # Step 4: Save debug images to visualize what's happening
    output_dir = Path("data/test_output/debug")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save original cropped
    cv2.imwrite(str(output_dir / "01_cropped_original.png"), cropped)

    # Save content mask (what we detected as content)
    cv2.imwrite(str(output_dir / "02_content_mask.png"), content_mask)

    # Save image with content center marked
    debug_image = cropped.copy()
    cv2.circle(
        debug_image, (content_center_x, content_center_y), 10, (0, 0, 255), -1
    )  # Red dot
    cv2.circle(
        debug_image, (cropped.shape[1] // 2, cropped.shape[0] // 2), 10, (0, 255, 0), -1
    )  # Green dot (image center)

    # Draw largest contour if found
    if contours:
        cv2.drawContours(debug_image, [largest_contour], -1, (255, 0, 0), 2)

    cv2.imwrite(str(output_dir / "03_content_analysis.png"), debug_image)

    # Save the mask template and scaled mask
    cv2.imwrite(str(output_dir / "04_original_mask.png"), mask_template)
    cv2.imwrite(str(output_dir / "05_scaled_mask.png"), scaled_mask)

    # Step 5: Test the actual masking result
    masked_result = detector.apply_template_mask(cropped, mask_path)
    cv2.imwrite(str(output_dir / "06_final_masked_result.png"), masked_result)

    print(f"\n📁 Debug images saved to 'data/test_output/debug/':")
    print("   01_cropped_original.png - The cropped input")
    print("   02_content_mask.png - What we detected as content (white = content)")
    print(
        "   03_content_analysis.png - Red dot = detected center, Green dot = image center, Blue outline = largest contour"
    )
    print("   04_original_mask.png - Original mask template")
    print("   05_scaled_mask.png - Scaled mask")
    print("   06_final_masked_result.png - Final result")

    print(f"\n🎯 Analysis:")
    if contours and len(contours) > 0:
        print(f"✅ Content detection seems to be working")
        print(f"   - Found {len(contours)} contours")
        print(f"   - Content center: ({content_center_x}, {content_center_y})")
        print(f"   - Image center: ({cropped.shape[1]//2}, {cropped.shape[0]//2})")

        center_diff_x = abs(content_center_x - cropped.shape[1] // 2)
        center_diff_y = abs(content_center_y - cropped.shape[0] // 2)

        if center_diff_x < 50 and center_diff_y < 50:
            print(
                f"⚠️  Content center is very close to image center - might not need content-aware positioning"
            )
        else:
            print(
                f"✅ Content center is significantly different from image center - content-aware positioning should help"
            )
    else:
        print(f"❌ Content detection failed - no contours found")
        print(f"💡 This means the content-aware approach won't work well")


if __name__ == "__main__":
    debug_content_masking()
