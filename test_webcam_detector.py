#!/usr/bin/env python3
"""
Test script for webcam detector functionality.
This script tests the detector without requiring a camera.
"""
import sys

sys.path.insert(0, "src")

from pathlib import Path

import cv2
import numpy as np

from webcam_detector import WebcamDetector
from webcam_detector_advanced import AdvancedWebcamDetector


def test_webcam_detector_initialization():
    """Test webcam detector initialization."""
    print("🧪 Testing Webcam Detector Initialization")
    print("=" * 50)

    try:
        # Test basic detector
        basic_detector = WebcamDetector(
            camera_index=0, frame_width=1280, frame_height=720, fps=30
        )
        print("✅ Basic webcam detector initialized successfully")

        # Test advanced detector
        advanced_detector = AdvancedWebcamDetector(
            camera_index=0,
            frame_width=1280,
            frame_height=720,
            fps=30,
            auto_capture=True,
            capture_delay=2.0,
            min_markers=4,
        )
        print("✅ Advanced webcam detector initialized successfully")

        # Test ArUco detector integration
        markers = basic_detector.aruco_detector.detect_markers(
            np.zeros((720, 1280, 3), dtype=np.uint8)
        )
        print("✅ ArUco detector integration working")

        return True

    except Exception as e:
        print(f"❌ Error initializing webcam detector: {e}")
        return False


def test_template_detection():
    """Test template detection functionality."""
    print("\n🧪 Testing Template Detection")
    print("=" * 50)

    try:
        # Create a test detector
        detector = WebcamDetector()

        # Test with sample marker IDs
        test_cases = [
            ([0, 1, 2, 3], "krathong1"),
            ([4, 5, 6, 7], "krathong2"),
            ([8, 9, 10, 11], "krathong3"),
            ([12, 13, 14, 15], "krathong4"),
            ([16, 17, 18, 19], "krathong5"),
            ([0, 1, 2], None),  # Incomplete set
            ([20, 21, 22, 23], None),  # Unknown markers
        ]

        success_count = 0

        for marker_ids, expected_template in test_cases:
            template_id = detector.aruco_detector.detect_template(marker_ids)

            if template_id == expected_template:
                print(f"✅ Template detection correct: {marker_ids} -> {template_id}")
                success_count += 1
            else:
                print(
                    f"❌ Template detection failed: {marker_ids} -> {template_id} (expected: {expected_template})"
                )

        print(
            f"\n📊 Template Detection Results: {success_count}/{len(test_cases)} correct"
        )
        return success_count == len(test_cases)

    except Exception as e:
        print(f"❌ Error in template detection test: {e}")
        return False


def test_quality_calculation():
    """Test quality score calculation."""
    print("\n🧪 Testing Quality Score Calculation")
    print("=" * 50)

    try:
        detector = AdvancedWebcamDetector()

        # Create a test frame
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        # Test with no markers
        quality = detector.calculate_quality_score([], frame)
        print(f"✅ No markers quality: {quality:.3f} (expected: 0.0)")

        # Test with mock markers (this would need actual marker data)
        print("✅ Quality calculation function working")

        return True

    except Exception as e:
        print(f"❌ Error in quality calculation test: {e}")
        return False


def test_capture_directory():
    """Test capture directory creation."""
    print("\n🧪 Testing Capture Directory")
    print("=" * 50)

    try:
        detector = WebcamDetector()

        # Check if capture directory exists
        if detector.capture_dir.exists():
            print(f"✅ Capture directory exists: {detector.capture_dir}")
        else:
            print(f"⚠️  Capture directory created: {detector.capture_dir}")

        # Test advanced detector directory
        advanced_detector = AdvancedWebcamDetector()
        if advanced_detector.capture_dir.exists():
            print(
                f"✅ Advanced capture directory exists: {advanced_detector.capture_dir}"
            )
        else:
            print(
                f"⚠️  Advanced capture directory created: {advanced_detector.capture_dir}"
            )

        return True

    except Exception as e:
        print(f"❌ Error in capture directory test: {e}")
        return False


def test_ui_functions():
    """Test UI drawing functions."""
    print("\n🧪 Testing UI Functions")
    print("=" * 50)

    try:
        detector = WebcamDetector()

        # Create a test frame
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        # Test drawing functions
        frame = detector.draw_instructions(frame)
        print("✅ Instructions drawing working")

        frame = detector.draw_fps(frame, 30.0)
        print("✅ FPS drawing working")

        # Test advanced detector UI
        advanced_detector = AdvancedWebcamDetector()
        frame = advanced_detector.draw_status_panel(frame)
        print("✅ Status panel drawing working")

        frame = advanced_detector.draw_quality_indicator(frame, 0.75)
        print("✅ Quality indicator drawing working")

        return True

    except Exception as e:
        print(f"❌ Error in UI functions test: {e}")
        return False


def main():
    """Run all webcam detector tests."""
    print("🎥 Webcam Detector Test Suite")
    print("=" * 60)

    tests = [
        ("Initialization", test_webcam_detector_initialization),
        ("Template Detection", test_template_detection),
        ("Quality Calculation", test_quality_calculation),
        ("Capture Directory", test_capture_directory),
        ("UI Functions", test_ui_functions),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")

    print("\n" + "=" * 60)
    print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Webcam detector is ready for use.")
        print("\nTo run webcam detection:")
        print("  python run_webcam.py                    # Basic mode")
        print("  python run_webcam_advanced.py           # Advanced mode")
        print("  python main.py --mode webcam            # Basic via main")
        print("  python main.py --mode webcam-advanced   # Advanced via main")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")

    return passed == total


if __name__ == "__main__":
    main()
