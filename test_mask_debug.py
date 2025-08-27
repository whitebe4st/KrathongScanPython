#!/usr/bin/env python3
"""
Debug script to test template mask application step by step.
"""

import sys

sys.path.insert(0, "src")

from pathlib import Path

import cv2
import numpy as np

from aruco_detector.detector import ArUcoDetector


def debug_mask_application(image_path: str, mask_path: str, output_dir: str):
    """
    Debug the template mask application step by step.

    Args:
        image_path: Path to input image
        mask_path: Path to template mask
        output_dir: Directory for debug outputs
    """
    print("🔍 Debugging Template Mask Application")
    print("=" * 45)

    # Initialize detector
    detector = ArUcoDetector(dict_type="4X4_50", marker_size=0.04)

    # Load image and get perspective-corrected version
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image from {image_path}")
        return False

    # Get perspective-corrected image
    markers = detector.detect_markers(image)
    corner_markers = detector.get_corner_markers(markers)
    homography = detector.create_perspective_transform(corner_markers)
    corrected = detector.apply_perspective_correction(image, homography)

    # Load template mask
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        print(f"❌ Could not load mask from {mask_path}")
        return False

    # Resize mask to match corrected image size
    mask = cv2.resize(mask, (corrected.shape[1], corrected.shape[0]))

    print(f"📸 Corrected image size: {corrected.shape[1]}x{corrected.shape[0]}")
    print(f"🎭 Mask size: {mask.shape[1]}x{mask.shape[0]}")

    # Analyze mask
    mask_white_pixels = np.sum(mask == 255)
    mask_black_pixels = np.sum(mask == 0)
    total_pixels = mask.shape[0] * mask.shape[1]

    print(f"🎭 Mask analysis:")
    print(
        f"   White pixels: {mask_white_pixels} ({mask_white_pixels/total_pixels*100:.1f}%)"
    )
    print(
        f"   Black pixels: {mask_black_pixels} ({mask_black_pixels/total_pixels*100:.1f}%)"
    )

    # Analyze corrected image brightness
    gray_corrected = cv2.cvtColor(corrected, cv2.COLOR_BGR2GRAY)
    avg_brightness = np.mean(gray_corrected)
    print(f"💡 Corrected image brightness: {avg_brightness:.1f}/255")

    # Create debug outputs
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save corrected image
    cv2.imwrite(str(output_path / "01_corrected_image.png"), corrected)

    # Save mask
    cv2.imwrite(str(output_path / "02_template_mask.png"), mask)

    # Apply mask manually to see what happens
    white_background = np.ones_like(corrected) * 255
    mask_inv = cv2.bitwise_not(mask)

    # Apply mask to image
    masked_image = cv2.bitwise_and(corrected, corrected, mask=mask)
    cv2.imwrite(str(output_path / "03_masked_image.png"), masked_image)

    # Apply inverted mask to white background
    masked_background = cv2.bitwise_and(
        white_background, white_background, mask=mask_inv
    )
    cv2.imwrite(str(output_path / "04_masked_background.png"), masked_background)

    # Combine them
    final_result = cv2.add(masked_image, masked_background)
    cv2.imwrite(str(output_path / "05_final_result.png"), final_result)

    # Analyze final result
    gray_final = cv2.cvtColor(final_result, cv2.COLOR_BGR2GRAY)
    final_brightness = np.mean(gray_final)
    print(f"💡 Final result brightness: {final_brightness:.1f}/255")

    print(f"\n📁 Debug images saved to: {output_path}")
    print("Files created:")
    print("  01_corrected_image.png - Perspective corrected image")
    print("  02_template_mask.png - Template mask")
    print("  03_masked_image.png - Image after mask application")
    print("  04_masked_background.png - White background after mask")
    print("  05_final_result.png - Final combined result")

    return True


def main():
    """Main function to run the mask debug test."""
    test_image = "data/test_images/krathong_test1.png"
    template_mask = "data/markers/templates/krathong1_mask.png"
    debug_output = "data/test_output/mask_debug"

    success = debug_mask_application(test_image, template_mask, debug_output)

    if success:
        print("\n🎉 Debug completed!")
        print("Check the debug images to see what's happening at each step.")
    else:
        print("\n💥 Debug failed!")
        print("Check the logs above for details.")


if __name__ == "__main__":
    main()
