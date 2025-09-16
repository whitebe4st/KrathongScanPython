#!/usr/bin/env python3
"""
Debug script to see what the DocumentScanner is doing step by step.
"""

import sys
from pathlib import Path

import cv2
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def debug_document_detection(image_path):
    """Debug the document detection process step by step."""

    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Could not load image: {image_path}")
        return

    print(f"Original image size: {image.shape}")

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Edge detection
    edges = cv2.Canny(thresh, 50, 150)

    # Morphological operations
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    print(f"Found {len(contours)} contours")

    if not contours:
        print("No contours found")
        return

    # Sort contours by area
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    # Check first 10 contours
    image_area = image.shape[0] * image.shape[1]
    print(f"Image area: {image_area}")

    for i, contour in enumerate(contours[:10]):
        area = cv2.contourArea(contour)
        area_ratio = area / image_area

        # Approximate the contour
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Check if it's a quadrilateral
        is_quad = len(approx) == 4

        # Check aspect ratio
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / h if h > 0 else 0

        print(
            f"Contour {i}: area={area:.0f} ({area_ratio:.3f}), "
            f"corners={len(approx)}, is_quad={is_quad}, "
            f"aspect_ratio={aspect_ratio:.3f}, bbox={w}x{h}"
        )

        # Check constraints
        area_ok = 0.1 <= area_ratio <= 0.9
        aspect_ok = 0.3 <= aspect_ratio <= 3.0

        print(f"  Area OK: {area_ok}, Aspect OK: {aspect_ok}")

        if is_quad and area_ok and aspect_ok:
            print(f"  ✅ This contour would be selected!")
            break

    # Save debug images
    output_dir = Path(image_path).parent / "debug_document_scanner"
    output_dir.mkdir(exist_ok=True)

    # Save intermediate steps
    cv2.imwrite(str(output_dir / "1_original.jpg"), image)
    cv2.imwrite(str(output_dir / "2_gray.jpg"), gray)
    cv2.imwrite(str(output_dir / "3_blurred.jpg"), blurred)
    cv2.imwrite(str(output_dir / "4_thresh.jpg"), thresh)
    cv2.imwrite(str(output_dir / "5_edges.jpg"), edges)

    # Draw contours on original image
    contour_image = image.copy()
    cv2.drawContours(contour_image, contours[:5], -1, (0, 255, 0), 2)
    cv2.imwrite(str(output_dir / "6_contours.jpg"), contour_image)

    print(f"Debug images saved to: {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_document_scanner.py <image_path>")
        sys.exit(1)

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        sys.exit(1)

    debug_document_detection(image_path)
