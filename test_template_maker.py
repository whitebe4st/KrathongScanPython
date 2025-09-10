#!/usr/bin/env python3
"""
Test script for the Krathong Template Maker
"""

import cv2
import numpy as np

from template_maker_gui import KrathongTemplateMaker


def test_template_creation():
    """Test basic template creation."""
    print("🎯 Testing Krathong Template Maker...")

    # Initialize template maker
    maker = KrathongTemplateMaker()

    # Test 1: Create template without krathong image
    print("Test 1: Creating template without krathong image...")
    template = maker.create_template_image(marker_ids=[0, 1, 2, 3])
    cv2.imwrite("test_template_basic.png", template)
    print("✅ Basic template created: test_template_basic.png")

    # Test 2: Create template with a simple test image
    print("Test 2: Creating template with test krathong image...")

    # Create a simple test krathong image (white background with black outline)
    test_krathong = np.ones((200, 200, 3), dtype=np.uint8) * 255  # White background
    cv2.circle(test_krathong, (100, 100), 80, (0, 0, 0), 3)  # Black circle outline
    cv2.imwrite("test_krathong.png", test_krathong)

    # Remove white background
    processed_krathong = maker.remove_white_background(test_krathong)
    cv2.imwrite("test_krathong_processed.png", processed_krathong)

    # Create template with krathong image
    template_with_krathong = maker.create_template_image(
        marker_ids=[4, 5, 6, 7],
        krathong_image=processed_krathong,
        scale=0.5,
        offset_x=0,
        offset_y=0,
    )
    cv2.imwrite("test_template_with_krathong.png", template_with_krathong)
    print("✅ Template with krathong created: test_template_with_krathong.png")

    # Test 3: Create mask
    print("Test 3: Creating mask...")
    mask = maker.create_mask(processed_krathong)
    cv2.imwrite("test_mask.png", mask)
    print("✅ Mask created: test_mask.png")

    print("\n🎉 All tests completed successfully!")
    print("Check the generated files:")
    print("- test_template_basic.png (template without krathong)")
    print("- test_krathong.png (original test krathong)")
    print("- test_krathong_processed.png (processed krathong)")
    print("- test_template_with_krathong.png (template with krathong)")
    print("- test_mask.png (generated mask)")


if __name__ == "__main__":
    test_template_creation()
