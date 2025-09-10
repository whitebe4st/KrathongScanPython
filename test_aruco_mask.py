#!/usr/bin/env python3
"""
Test ArUco mask creation to debug rectangle detection.
"""

from pathlib import Path

import cv2
import numpy as np

from src.enhanced_rectangle_cropper import _create_aruco_mask


def test_aruco_mask():
    # Load test image
    image_path = "data/test_images/real_photo_test.jpg"
    image = cv2.imread(image_path)

    if image is None:
        print(f"❌ Could not load image: {image_path}")
        return

    print(f"📸 Loaded image: {image.shape}")

    # Create ArUco mask
    mask = _create_aruco_mask(image)

    # Save visualization
    debug_dir = Path("debug_aruco_mask")
    debug_dir.mkdir(exist_ok=True)

    # Save original image
    cv2.imwrite(str(debug_dir / "original.png"), image)

    # Save mask
    cv2.imwrite(str(debug_dir / "aruco_mask.png"), mask)

    # Create overlay showing what's masked
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    masked_gray = cv2.bitwise_and(gray, gray, mask=mask)

    # Create visualization showing original vs masked
    overlay = np.zeros_like(image)
    overlay[:, :, 0] = gray  # Original in red channel
    overlay[:, :, 1] = masked_gray  # Masked in green channel
    overlay[:, :, 2] = mask  # Mask in blue channel

    cv2.imwrite(str(debug_dir / "overlay.png"), overlay)
    cv2.imwrite(str(debug_dir / "masked_gray.png"), masked_gray)

    print(f"✅ Saved debug images to {debug_dir}")
    print(
        f"🔍 Mask statistics: min={mask.min()}, max={mask.max()}, unique={np.unique(mask)}"
    )


if __name__ == "__main__":
    test_aruco_mask()
