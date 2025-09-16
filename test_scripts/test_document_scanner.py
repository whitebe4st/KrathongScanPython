#!/usr/bin/env python3
"""
Test script to see what the DocumentScanner does to an image.
"""

import sys
from pathlib import Path

import cv2
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from document_scanner import DocumentScanner


def test_document_scanner(image_path):
    """Test the document scanner on a specific image."""

    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Could not load image: {image_path}")
        return

    print(f"Original image size: {image.shape}")

    # Initialize document scanner
    scanner = DocumentScanner()

    # Process image
    processed, success = scanner.process_image(image)

    if success:
        print(f"✅ Document detected and corrected!")
        print(f"Processed image size: {processed.shape}")

        # Save both images for comparison
        original_path = Path(image_path)
        output_dir = original_path.parent / "document_scanner_test"
        output_dir.mkdir(exist_ok=True)

        # Save original
        original_output = output_dir / f"{original_path.stem}_original.jpg"
        cv2.imwrite(str(original_output), image)
        print(f"Saved original: {original_output}")

        # Save processed
        processed_output = output_dir / f"{original_path.stem}_processed.jpg"
        cv2.imwrite(str(processed_output), processed)
        print(f"Saved processed: {processed_output}")

        # Show both images
        cv2.imshow("Original", cv2.resize(image, (800, 600)))
        cv2.imshow("Processed", cv2.resize(processed, (800, 600)))
        print("Press any key to close windows...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    else:
        print("❌ No document detected, using original image")
        print(f"Processed image size: {processed.shape}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_document_scanner.py <image_path>")
        print("Example: python test_document_scanner.py data/test_images/download.jpg")
        sys.exit(1)

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        sys.exit(1)

    test_document_scanner(image_path)
