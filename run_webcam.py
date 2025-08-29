#!/usr/bin/env python3
"""
Simple script to run the webcam detector.
"""
import sys

sys.path.insert(0, "src")

from webcam_detector import WebcamDetector


def main():
    """Run the webcam detector."""
    print("🎥 Starting Krathong Scanner Webcam Detection")
    print("=" * 50)
    print("Controls:")
    print("  'c' - Capture and process current frame")
    print("  'q' - Quit")
    print("  'm' - Toggle marker display")
    print("  'i' - Toggle template info")
    print("  'f' - Toggle FPS display")
    print("=" * 50)
    print("Make sure you have ArUco markers visible in the camera view!")
    print()

    # Initialize webcam detector
    detector = WebcamDetector(
        camera_index=0, frame_width=1280, frame_height=720, fps=30  # Use default camera
    )

    # Run detection loop
    detector.run()


if __name__ == "__main__":
    main()
