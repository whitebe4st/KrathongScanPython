#!/usr/bin/env python3
"""
Advanced webcam detection script with automatic capture.
"""
import sys

sys.path.insert(0, "src")

from webcam_detector_advanced import AdvancedWebcamDetector


def main():
    """Run the advanced webcam detector."""
    print("🎥 Krathong Scanner - Advanced Webcam Detection")
    print("=" * 60)
    print("Features:")
    print("  ✅ Real-time template detection")
    print("  ✅ Automatic capture when template detected")
    print("  ✅ Quality indicators and status monitoring")
    print("  ✅ Manual capture controls")
    print("=" * 60)
    print("Controls:")
    print("  'c' - Manual capture")
    print("  'q' - Quit")
    print("  'm' - Toggle marker display")
    print("  'i' - Toggle template info")
    print("  's' - Toggle status panel")
    print("  'a' - Toggle auto-capture")
    print("=" * 60)
    print("Make sure you have ArUco markers visible in the camera view!")
    print("The system will automatically capture when a template is detected.")
    print()

    # Initialize advanced webcam detector
    detector = AdvancedWebcamDetector(
        camera_index=0,  # Use default camera
        frame_width=1280,
        frame_height=720,
        fps=30,
        auto_capture=True,  # Enable automatic capture
        capture_delay=2.0,  # Wait 2 seconds after template detection
        min_markers=4,  # Require all 4 markers
    )

    # Run detection loop
    detector.run()


if __name__ == "__main__":
    main()
