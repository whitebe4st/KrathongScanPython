#!/usr/bin/env python3
"""
Debug script to test masking logic step by step.
"""
import sys

sys.path.insert(0, "src")

from pathlib import Path

import cv2
import numpy as np

from aruco_detector.detector import ArUcoDetector


def debug_masking():
    print("🎯 Debugging Masking Logic")
    print("=" * 40)

    # Initialize detector
    detector = ArUcoDetector(dict_type="4X4_50", marker_size=0.04)

    # Load test image
    test_image = "data/test_images/krathong_test2.png"
    template_mask = "data/markers/templates/krathong1_mask2.png"

    # Load image
    image = cv2.imread(test_image)
    if image is None:
        print(f"❌ Could not load image from {test_image}")
        return

    # Load mask
    mask = cv2.imread(template_mask, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        print(f"❌ Could not load mask from {template_mask}")
        return

    print(f"📸 Image size: {image.shape}")
    print(f"🎭 Mask size: {mask.shape}")

    # Analyze mask
    unique_values, counts = np.unique(mask, return_counts=True)
    print(f"🎭 Mask pixel values: {dict(zip(unique_values, counts))}")

    # Detect markers and crop
    markers = detector.detect_markers(image)
    if not markers:
        print("❌ No markers detected")
        return

    corner_markers = detector.get_corner_markers(markers)
    if corner_markers is None:
        print("❌ Could not find all corner markers")
        return

    # Crop the area
    cropped = detector._crop_marker_area(image, corner_markers)
    print(f"✂️ Cropped size: {cropped.shape}")

    # Resize mask to match cropped image
    mask_resized = cv2.resize(mask, (cropped.shape[1], cropped.shape[0]))
    print(f"🎭 Resized mask size: {mask_resized.shape}")

    # Analyze resized mask
    unique_values, counts = np.unique(mask_resized, return_counts=True)
    print(f"🎭 Resized mask pixel values: {dict(zip(unique_values, counts))}")

    # Test masking logic
    print("\n🔍 Testing masking logic...")

    # Create white background
    white_background = np.ones_like(cropped) * 255

    # Create a binary mask: treat gray pixels (above threshold) as white areas to extract
    # Threshold: treat pixels with value > 128 as "white" areas to keep
    _, binary_mask = cv2.threshold(mask_resized, 128, 255, cv2.THRESH_BINARY)

    # Convert to BGRA for transparency
    bgra_image = cv2.cvtColor(cropped, cv2.COLOR_BGR2BGRA)

    # Create alpha channel from binary mask
    # White areas in mask (255) = fully opaque (255)
    # Black areas in mask (0) = fully transparent (0)
    alpha_channel = binary_mask

    # Apply the alpha channel
    bgra_image[:, :, 3] = alpha_channel

    # Apply the binary mask to the BGR channels
    # Keep original colors where mask is white, make black where mask is black
    masked_bgr = cv2.bitwise_and(
        bgra_image[:, :, :3], bgra_image[:, :, :3], mask=binary_mask
    )
    bgra_image[:, :, :3] = masked_bgr

    final_result = bgra_image

    # Save debug images
    debug_dir = Path("data/test_output/debug_masking")
    debug_dir.mkdir(parents=True, exist_ok=True)

    cv2.imwrite(str(debug_dir / "01_cropped.png"), cropped)
    cv2.imwrite(str(debug_dir / "02_mask_resized.png"), mask_resized)
    cv2.imwrite(str(debug_dir / "03_binary_mask.png"), binary_mask)
    cv2.imwrite(str(debug_dir / "04_alpha_channel.png"), alpha_channel)
    cv2.imwrite(str(debug_dir / "05_final_result.png"), final_result)

    print(f"📁 Debug images saved to {debug_dir}")

    # Analyze final result
    gray_result = cv2.cvtColor(final_result, cv2.COLOR_BGR2GRAY)
    unique_values, counts = np.unique(gray_result, return_counts=True)
    print(f"🎨 Final result pixel values: {dict(zip(unique_values, counts))}")

    # Test cropping masked area
    print("\n✂️ Testing masked area cropping...")
    cropped_result = detector._crop_masked_area(final_result)
    print(f"📏 Cropped result size: {cropped_result.shape}")

    cv2.imwrite(str(debug_dir / "07_cropped_result.png"), cropped_result)

    print("✅ Debug completed!")


if __name__ == "__main__":
    debug_masking()
