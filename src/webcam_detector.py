"""
Webcam-based ArUco marker detection system.

This module provides real-time detection of ArUco markers from webcam feed,
template identification, and image capture capabilities.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

from aruco_detector import ArUcoDetector


class WebcamDetector:
    """
    Real-time webcam-based ArUco marker detection system.

    Features:
    - Real-time marker detection and visualization
    - Template identification and display
    - Image capture and processing
    - Live preview with marker overlays
    """

    def __init__(
        self,
        camera_index: int = 0,
        frame_width: int = 1280,
        frame_height: int = 720,
        fps: int = 30,
    ):
        """
        Initialize the webcam detector.

        Args:
            camera_index: Camera device index (usually 0 for default camera)
            frame_width: Desired frame width
            frame_height: Desired frame height
            fps: Target frames per second
        """
        self.logger = self._setup_logger()
        self.camera_index = camera_index
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fps = fps

        # Initialize ArUco detector
        self.aruco_detector = ArUcoDetector()

        # Camera and processing state
        self.camera = None
        self.is_running = False
        self.current_template = None
        self.current_template_config = None
        self.detected_markers = []

        # Capture settings
        self.capture_dir = Path("data/webcam_captures")
        self.capture_dir.mkdir(parents=True, exist_ok=True)

        # UI settings
        self.show_markers = True
        self.show_template_info = (
            False  # Disable template info box to avoid marker interference
        )
        self.show_fps = True

        # Notification system
        self.notification_text = ""
        self.notification_time = 0
        self.notification_duration = 3.0  # Show notification for 3 seconds

        self.logger.info(f"Webcam Detector initialized for camera {camera_index}")

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the webcam detector."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def start_camera(self) -> bool:
        """
        Start the webcam capture.

        Returns:
            True if camera started successfully, False otherwise
        """
        try:
            self.camera = cv2.VideoCapture(self.camera_index)

            if not self.camera.isOpened():
                self.logger.error(f"Could not open camera {self.camera_index}")
                return False

            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)

            # Get actual camera properties
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.camera.get(cv2.CAP_PROP_FPS))

            self.logger.info(
                f"Camera started: {actual_width}x{actual_height} @ {actual_fps}fps"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error starting camera: {e}")
            return False

    def stop_camera(self):
        """Stop the webcam capture."""
        if self.camera:
            self.camera.release()
            self.camera = None
        self.is_running = False
        self.logger.info("Camera stopped")

    def detect_markers_in_frame(self, frame: np.ndarray) -> Tuple[list, Optional[str]]:
        """
        Detect ArUco markers in a frame and identify template.

        Args:
            frame: Input frame (BGR format)

        Returns:
            Tuple of (detected_markers, template_id)
        """
        try:
            # Detect markers
            markers = self.aruco_detector.detect_markers(frame)

            if not markers:
                return [], None

            # Extract marker IDs
            marker_ids = [marker.id for marker in markers]

            # Detect template (use partial detection for display, but require all markers for processing)
            template_id = self.aruco_detector.detect_template(
                marker_ids, use_partial=True
            )

            return markers, template_id

        except Exception as e:
            self.logger.error(f"Error detecting markers: {e}")
            return [], None

    def draw_markers(self, frame: np.ndarray, markers: list) -> np.ndarray:
        """
        Draw detected markers on the frame.

        Args:
            frame: Input frame
            markers: List of detected markers

        Returns:
            Frame with marker overlays
        """
        try:
            for marker in markers:
                # Draw marker corners
                corners = np.array(marker.corners, dtype=np.int32)
                cv2.polylines(frame, [corners], True, (0, 255, 0), 2)

                # Draw marker ID
                center = np.array(marker.center, dtype=np.int32)
                cv2.putText(
                    frame,
                    str(marker.id),
                    (center[0] - 10, center[1] + 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

                # Draw center point
                cv2.circle(frame, tuple(center), 4, (255, 0, 0), -1)

        except Exception as e:
            self.logger.error(f"Error drawing markers: {e}")

        return frame

    def draw_template_info(self, frame: np.ndarray, template_id: str) -> np.ndarray:
        """
        Draw template information on the frame.

        Args:
            frame: Input frame
            template_id: Detected template ID

        Returns:
            Frame with template information overlay
        """
        try:
            if not template_id:
                return frame

            template_config = self.aruco_detector.current_template_config
            if not template_config:
                return frame

            # Create info panel
            info_text = [
                f"Template: {template_id}",
                f"Name: {template_config['name']}",
                f"Description: {template_config['description']}",
            ]

            # Calculate panel position and size
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            line_height = 25

            # Get text dimensions
            max_width = 0
            for text in info_text:
                (text_width, _), _ = cv2.getTextSize(text, font, font_scale, thickness)
                max_width = max(max_width, text_width)

            panel_width = max_width + 20
            panel_height = len(info_text) * line_height + 20

            # Position panel in top-right corner, but avoid overlapping markers
            # Move it down and to the left to avoid the top-right marker area
            panel_x = frame.shape[1] - panel_width - 50  # More margin from right edge
            panel_y = 80  # Move down to avoid top marker area

            # Draw background panel
            cv2.rectangle(
                frame,
                (panel_x, panel_y),
                (panel_x + panel_width, panel_y + panel_height),
                (0, 0, 0),
                -1,
            )
            cv2.rectangle(
                frame,
                (panel_x, panel_y),
                (panel_x + panel_width, panel_y + panel_height),
                (255, 255, 255),
                2,
            )

            # Draw text
            for i, text in enumerate(info_text):
                y_pos = panel_y + 20 + i * line_height
                cv2.putText(
                    frame,
                    text,
                    (panel_x + 10, y_pos),
                    font,
                    font_scale,
                    (255, 255, 255),
                    thickness,
                )

        except Exception as e:
            self.logger.error(f"Error drawing template info: {e}")

        return frame

    def draw_fps(self, frame: np.ndarray, fps: float) -> np.ndarray:
        """
        Draw FPS counter on the frame.

        Args:
            frame: Input frame
            fps: Current FPS

        Returns:
            Frame with FPS overlay
        """
        try:
            fps_text = f"FPS: {fps:.1f}"
            cv2.putText(
                frame,
                fps_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )
        except Exception as e:
            self.logger.error(f"Error drawing FPS: {e}")

        return frame

    def show_notification(self, text: str):
        """Show a notification message on the HUD."""
        self.notification_text = text
        self.notification_time = time.time()

    def draw_notification(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw notification message on the frame.

        Args:
            frame: Input frame

        Returns:
            Frame with notification overlay
        """
        try:
            current_time = time.time()
            if (
                self.notification_text
                and current_time - self.notification_time < self.notification_duration
            ):
                # Calculate remaining time for fade effect
                remaining_time = self.notification_duration - (
                    current_time - self.notification_time
                )
                alpha = min(1.0, remaining_time / 0.5)  # Fade out in last 0.5 seconds

                # Get text dimensions
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.8
                thickness = 2
                (text_width, text_height), _ = cv2.getTextSize(
                    self.notification_text, font, font_scale, thickness
                )

                # Position notification in center-top
                panel_width = text_width + 40
                panel_height = text_height + 20
                panel_x = (frame.shape[1] - panel_width) // 2
                panel_y = 50

                # Draw background panel with alpha
                overlay = frame.copy()
                cv2.rectangle(
                    overlay,
                    (panel_x, panel_y),
                    (panel_x + panel_width, panel_y + panel_height),
                    (0, 0, 0),
                    -1,
                )
                cv2.rectangle(
                    overlay,
                    (panel_x, panel_y),
                    (panel_x + panel_width, panel_y + panel_height),
                    (255, 255, 255),
                    2,
                )

                # Blend with original frame
                frame = cv2.addWeighted(frame, 1 - alpha * 0.7, overlay, alpha * 0.7, 0)

                # Draw text
                color = (
                    (0, int(255 * alpha), 0)
                    if "✅" in self.notification_text
                    else (0, 0, int(255 * alpha))
                )
                cv2.putText(
                    frame,
                    self.notification_text,
                    (panel_x + 20, panel_y + panel_height - 5),
                    font,
                    font_scale,
                    color,
                    thickness,
                )

        except Exception as e:
            self.logger.error(f"Error drawing notification: {e}")

        return frame

    def draw_instructions(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw user instructions on the frame.

        Args:
            frame: Input frame

        Returns:
            Frame with instructions overlay
        """
        try:
            instructions = [
                "Press 'c' to capture and process",
                "Press 'q' to quit",
                "Press 'm' to toggle markers",
                "Press 'i' to toggle info",
                "Press 'f' to toggle FPS",
            ]

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            line_height = 20

            # Position at bottom-left
            start_y = frame.shape[0] - len(instructions) * line_height - 10

            for i, instruction in enumerate(instructions):
                y_pos = start_y + i * line_height
                cv2.putText(
                    frame,
                    instruction,
                    (10, y_pos),
                    font,
                    font_scale,
                    (255, 255, 255),
                    thickness,
                )

        except Exception as e:
            self.logger.error(f"Error drawing instructions: {e}")

        return frame

    def capture_and_process(self, frame: np.ndarray) -> bool:
        """
        Capture current frame and process it.

        Args:
            frame: Current frame to capture

        Returns:
            True if processing successful, False otherwise
        """
        try:
            # Generate timestamp for filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")

            # Create capture filename
            if self.current_template:
                capture_filename = f"{self.current_template}_{timestamp}.png"
            else:
                capture_filename = f"unknown_template_{timestamp}.png"

            capture_path = self.capture_dir / capture_filename

            # Save original frame
            cv2.imwrite(str(capture_path), frame)
            self.logger.info(f"Captured frame: {capture_path}")

            # Process the captured image
            if self.current_template:
                # Check if we have enough markers for processing
                if len(self.detected_markers) < 4:
                    self.logger.warning(
                        f"Only {len(self.detected_markers)} markers detected, need 4 for processing"
                    )
                    return False

                # Use template-specific processing
                output_filename = f"{self.current_template}_{timestamp}_processed.png"
                output_path = self.capture_dir / output_filename

                # Use a dummy mask path (will be overridden by template detection)
                success = self.aruco_detector.process_image(
                    str(capture_path),
                    "dummy_mask.png",  # Will be overridden
                    str(output_path),
                    use_homography=False,  # Start with simple cropping
                )

                if success:
                    self.logger.info(f"Processing completed: {output_path}")
                    return True
                else:
                    self.logger.error("Processing failed")
                    return False
            else:
                self.logger.warning("No template detected, only saved raw frame")
                return True

        except Exception as e:
            self.logger.error(f"Error capturing and processing: {e}")
            return False

    def run(self):
        """
        Main webcam detection loop.
        """
        if not self.start_camera():
            return

        self.is_running = True
        self.logger.info("Starting webcam detection loop")

        # FPS calculation
        frame_count = 0
        start_time = time.time()
        fps = 0

        try:
            while self.is_running:
                # Capture frame
                ret, frame = self.camera.read()
                if not ret:
                    self.logger.error("Failed to capture frame")
                    break

                # Detect markers and template
                markers, template_id = self.detect_markers_in_frame(frame)
                self.detected_markers = markers
                self.current_template = template_id

                # Update template config
                if template_id:
                    self.current_template_config = (
                        self.aruco_detector.current_template_config
                    )

                # Draw overlays
                if self.show_markers:
                    frame = self.draw_markers(frame, markers)

                if self.show_template_info and template_id:
                    frame = self.draw_template_info(frame, template_id)

                if self.show_fps:
                    frame = self.draw_fps(frame, fps)

                # Draw notification (if any)
                frame = self.draw_notification(frame)

                # Draw instructions
                frame = self.draw_instructions(frame)

                # Display frame
                cv2.imshow("Krathong Scanner - Webcam Detection", frame)

                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("c"):
                    if self.capture_and_process(frame):
                        success_msg = (
                            f"✅ Captured and processed: {self.current_template}"
                        )
                        print(success_msg)
                        self.show_notification(success_msg)
                    else:
                        if len(self.detected_markers) < 4:
                            error_msg = f"❌ Need 4 markers, only {len(self.detected_markers)} detected"
                        else:
                            error_msg = "❌ Capture/processing failed"
                        print(error_msg)
                        self.show_notification(error_msg)
                elif key == ord("m"):
                    self.show_markers = not self.show_markers
                    print(f"Markers: {'ON' if self.show_markers else 'OFF'}")
                elif key == ord("i"):
                    self.show_template_info = not self.show_template_info
                    print(f"Info: {'ON' if self.show_template_info else 'OFF'}")
                elif key == ord("f"):
                    self.show_fps = not self.show_fps
                    print(f"FPS: {'ON' if self.show_fps else 'OFF'}")

                # Calculate FPS
                frame_count += 1
                if frame_count % 30 == 0:  # Update FPS every 30 frames
                    current_time = time.time()
                    fps = 30 / (current_time - start_time)
                    start_time = current_time

        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        except Exception as e:
            self.logger.error(f"Error in detection loop: {e}")
        finally:
            self.stop_camera()
            cv2.destroyAllWindows()
            self.logger.info("Webcam detection stopped")


def main():
    """Main function to run webcam detection."""
    print("🎥 Krathong Scanner - Webcam Detection")
    print("=" * 40)
    print("Controls:")
    print("  'c' - Capture and process current frame")
    print("  'q' - Quit")
    print("  'm' - Toggle marker display")
    print("  'i' - Toggle template info")
    print("  'f' - Toggle FPS display")
    print("=" * 40)

    # Initialize webcam detector
    detector = WebcamDetector(
        camera_index=0, frame_width=1280, frame_height=720, fps=30
    )

    # Run detection loop
    detector.run()


if __name__ == "__main__":
    main()
