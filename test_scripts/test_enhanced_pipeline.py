#!/usr/bin/env python3
"""
Test script for the enhanced pipeline: detect paper -> detect aruco -> apply mask

This script tests the new enhanced document scanner approach integrated with
the existing ArUco detection pipeline.
"""

import logging
import sys
from pathlib import Path

import cv2
import numpy as np

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from aruco_detector import ArUcoDetector
from enhanced_auto_directory_detector import EnhancedAutoDirectoryDetector
from enhanced_document_scanner import EnhancedDocumentScanner


def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def test_enhanced_document_scanner():
    """Test the enhanced document scanner on a real photo."""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED DOCUMENT SCANNER")
    print("=" * 60)

    # Test image path
    test_image_path = "data/test_images/download.jpg"

    if not Path(test_image_path).exists():
        print(f"❌ Test image not found: {test_image_path}")
        return False

    # Load test image
    image = cv2.imread(test_image_path)
    if image is None:
        print(f"❌ Could not load image: {test_image_path}")
        return False

    print(f"✓ Loaded test image: {test_image_path}")
    print(f"  Original size: {image.shape[1]}x{image.shape[0]}")

    # Initialize enhanced document scanner
    scanner = EnhancedDocumentScanner()

    # Process the image
    print("\n🔍 Detecting document boundaries...")
    processed_image, success = scanner.process_image(image)

    if success:
        print(f"✅ Document detection successful!")
        print(
            f"  Processed size: {processed_image.shape[1]}x{processed_image.shape[0]}"
        )

        # Save the result for inspection
        output_path = "test_enhanced_document_result.png"
        cv2.imwrite(output_path, processed_image)
        print(f"  Saved result: {output_path}")

        return True
    else:
        print("❌ Document detection failed")
        return False


def test_enhanced_pipeline():
    """Test the complete enhanced pipeline."""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED PIPELINE")
    print("=" * 60)

    # Test image path
    test_image_path = "data/test_images/download.jpg"

    if not Path(test_image_path).exists():
        print(f"❌ Test image not found: {test_image_path}")
        return False

    # Initialize enhanced auto directory detector
    detector = EnhancedAutoDirectoryDetector(
        input_directory="data/test_images",
        output_directory="test_enhanced_output",
        use_document_detection=True,
    )

    # Process the test image
    print(f"🔍 Processing: {test_image_path}")
    success = detector.process_single_file(test_image_path)

    if success:
        print("✅ Enhanced pipeline completed successfully!")

        # Check output files
        output_dir = Path("test_enhanced_output")
        if output_dir.exists():
            output_files = list(output_dir.glob("*.png"))
            json_files = list(output_dir.glob("*.json"))

            print(f"  Output images: {len(output_files)}")
            print(f"  Metadata files: {len(json_files)}")

            for img_file in output_files:
                img = cv2.imread(str(img_file))
                if img is not None:
                    print(f"    {img_file.name}: {img.shape[1]}x{img.shape[0]}")

        return True
    else:
        print("❌ Enhanced pipeline failed")
        return False


def test_aruco_detection_on_document_corrected():
    """Test ArUco detection on document-corrected image."""
    print("\n" + "=" * 60)
    print("TESTING ARUCO DETECTION ON DOCUMENT-CORRECTED IMAGE")
    print("=" * 60)

    # Test image path
    test_image_path = "data/test_images/download.jpg"

    if not Path(test_image_path).exists():
        print(f"❌ Test image not found: {test_image_path}")
        return False

    # Load test image
    image = cv2.imread(test_image_path)
    if image is None:
        print(f"❌ Could not load image: {test_image_path}")
        return False

    print(f"✓ Loaded test image: {test_image_path}")
    print(f"  Original size: {image.shape[1]}x{image.shape[0]}")

    # Step 1: Document detection
    scanner = EnhancedDocumentScanner()
    print("\n🔍 Step 1: Document detection...")
    processed_image, doc_success = scanner.process_image(image)

    if not doc_success:
        print("❌ Document detection failed")
        return False

    print(f"✅ Document detection successful!")
    print(
        f"  Document-corrected size: {processed_image.shape[1]}x{processed_image.shape[0]}"
    )

    # Step 2: ArUco detection on document-corrected image
    detector = ArUcoDetector()
    print("\n🔍 Step 2: ArUco detection on document-corrected image...")
    markers = detector.detect_markers(processed_image)

    if not markers:
        print("❌ No ArUco markers detected on document-corrected image")
        return False

    print(f"✅ Found {len(markers)} ArUco markers!")
    for marker in markers:
        print(f"  Marker ID: {marker.id}")

    # Step 3: Get corner markers
    corner_markers = detector.get_corner_markers(markers)
    if corner_markers is None:
        print("❌ Could not find corner markers")
        return False

    print("✅ Corner markers found!")

    # Step 4: Apply cropping
    print("\n🔍 Step 3: Applying ArUco-based cropping...")
    cropped = detector._crop_marker_area(processed_image, corner_markers)

    print(f"✅ Cropping applied!")
    print(f"  Cropped size: {cropped.shape[1]}x{cropped.shape[0]}")

    # Save results
    cv2.imwrite("test_document_corrected.png", processed_image)
    cv2.imwrite("test_aruco_cropped.png", cropped)

    print("  Saved: test_document_corrected.png")
    print("  Saved: test_aruco_cropped.png")

    return True


def main():
    """Run all tests."""
    setup_logging()

    print("🧪 TESTING ENHANCED PIPELINE")
    print("Pipeline: detect paper -> detect aruco -> apply mask")

    # Test 1: Enhanced document scanner
    test1_success = test_enhanced_document_scanner()

    # Test 2: ArUco detection on document-corrected image
    test2_success = test_aruco_detection_on_document_corrected()

    # Test 3: Complete enhanced pipeline
    test3_success = test_enhanced_pipeline()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Enhanced Document Scanner: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"ArUco on Document-Corrected: {'✅ PASS' if test2_success else '❌ FAIL'}")
    print(f"Complete Enhanced Pipeline: {'✅ PASS' if test3_success else '❌ FAIL'}")

    if all([test1_success, test2_success, test3_success]):
        print("\n🎉 ALL TESTS PASSED! Enhanced pipeline is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")

    return all([test1_success, test2_success, test3_success])


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
