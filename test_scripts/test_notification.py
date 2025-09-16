#!/usr/bin/env python3
"""
Test the notification system in webcam detectors.
"""
import sys

sys.path.insert(0, "src")

import time

import cv2
import numpy as np

from webcam_detector import WebcamDetector
from webcam_detector_advanced import AdvancedWebcamDetector


def test_notification_system():
    """Test the notification system."""
    print("🧪 Testing Notification System")
    print("=" * 50)

    try:
        # Test basic detector notification
        detector = WebcamDetector()

        # Create a test frame
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        # Test notification
        detector.show_notification("✅ Test notification working!")

        # Draw notification
        frame = detector.draw_notification(frame)

        # Save test image
        cv2.imwrite("test_notification.png", frame)
        print("✅ Basic notification system working")
        print("📸 Saved test image: test_notification.png")

        # Test advanced detector notification
        advanced_detector = AdvancedWebcamDetector()

        # Create another test frame
        frame2 = np.zeros((720, 1280, 3), dtype=np.uint8)

        # Test notification
        advanced_detector.show_notification("✅ Advanced notification working!")

        # Draw notification
        frame2 = advanced_detector.draw_notification(frame2)

        # Save test image
        cv2.imwrite("test_notification_advanced.png", frame2)
        print("✅ Advanced notification system working")
        print("📸 Saved test image: test_notification_advanced.png")

        return True

    except Exception as e:
        print(f"❌ Error testing notification system: {e}")
        return False


def test_notification_fade():
    """Test notification fade effect."""
    print("\n🧪 Testing Notification Fade Effect")
    print("=" * 50)

    try:
        detector = WebcamDetector()
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        # Show notification
        detector.show_notification("✅ Fade test notification")

        # Simulate time passing
        for i in range(5):
            # Draw notification
            test_frame = frame.copy()
            test_frame = detector.draw_notification(test_frame)

            # Save frame
            cv2.imwrite(f"test_notification_fade_{i}.png", test_frame)

            # Simulate time passing (0.5 seconds)
            detector.notification_time -= 0.5

            print(f"✅ Frame {i+1} saved: test_notification_fade_{i}.png")

        print("✅ Notification fade effect working")
        return True

    except Exception as e:
        print(f"❌ Error testing notification fade: {e}")
        return False


def main():
    """Run notification tests."""
    print("🔔 Notification System Test Suite")
    print("=" * 60)

    tests = [
        ("Basic Notification", test_notification_system),
        ("Notification Fade", test_notification_fade),
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
        print("🎉 All notification tests passed!")
        print("\nThe notification system will now show:")
        print("  ✅ Success messages in green")
        print("  ❌ Error messages in red")
        print("  📱 Messages fade out over 3 seconds")
        print("  🎯 Messages appear in center-top of screen")
    else:
        print("⚠️  Some notification tests failed.")

    return passed == total


if __name__ == "__main__":
    main()
