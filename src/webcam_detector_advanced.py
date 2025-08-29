"""
Advanced webcam-based ArUco marker detection system.

This module provides enhanced real-time detection with:
- Automatic capture when template is detected
- Better UI with status indicators
- Capture quality indicators
- Batch processing capabilities
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from aruco_detector import ArUcoDetector


class AdvancedWebcamDetector:
    """
    Advanced real-time webcam-based ArUco marker detection system.

    Features:
    - Real-time marker detection and visualization
    - Template identification and display
    - Automatic capture when template is detected
    - Quality indicators and status display
    - Batch processing capabilities
    - Enhanced UI with multiple overlays
    """

    def __init__(
        self,
        camera_index: int = 0,
        frame_width: int = 1280,
        frame_height: int = 720,
        fps: int = 30,
        auto_capture: bool = True,
        capture_delay: float = 2.0,
        min_markers: int = 4,
    ):
        """
        Initialize the advanced webcam detector.

        Args:
            camera_index: Camera device index
            frame_width: Desired frame width
            frame_height: Desired frame height
            fps: Target frames per second
            auto_capture: Enable automatic capture when template detected
            capture_delay: Delay before auto-capture (seconds)
            min_markers: Minimum markers required for capture
        """
        self.logger = self._setup_logger()
        self.camera_index = camera_index
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fps = fps
        self.auto_capture = auto_capture
        self.capture_delay = capture_delay
        self.min_markers = min_markers

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

        # Auto-capture state
        self.template_detected_time = None
        self.last_capture_time = 0
        self.capture_cooldown = 3.0  # Minimum time between captures

        # UI settings
        self.show_markers = True
        self.show_template_info = (
            False  # Disable template info box to avoid marker interference
        )
        self.show_fps = True
        self.show_status = True
        self.show_quality = True

        # Statistics
        self.total_frames = 0
        self.detection_frames = 0
        self.captures_made = 0

        # Notification system
        self.notification_text = ""
        self.notification_time = 0
        self.notification_duration = 3.0  # Show notification for 3 seconds

        self.logger.info(
            f"Advanced Webcam Detector initialized for camera {camera_index}"
        )

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
        """Start the webcam capture."""
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
        """Detect ArUco markers in a frame and identify template."""
        try:
            # Detect markers
            markers = self.aruco_detector.detect_markers(frame)

            if not markers:
                return [], None

            # Extract marker IDs
            marker_ids = [marker.id for marker in markers]

            # Detect template
            template_id = self.aruco_detector.detect_template(marker_ids)

            return markers, template_id

        except Exception as e:
            self.logger.error(f"Error detecting markers: {e}")
            return [], None

    def calculate_quality_score(self, markers: list, frame: np.ndarray) -> float:
        """
        Calculate quality score for the current detection.

        Args:
            markers: Detected markers
            frame: Current frame

        Returns:
            Quality score (0.0 to 1.0)
        """
        try:
            if not markers:
                return 0.0

            # Base score from number of markers
            marker_score = min(len(markers) / 4.0, 1.0)

            # Calculate marker size and position scores
            frame_height, frame_width = frame.shape[:2]
            center_x, center_y = frame_width // 2, frame_height // 2

            position_score = 0.0
            size_score = 0.0

            for marker in markers:
                # Position score (closer to center is better)
                center = marker.center
                distance_to_center = np.sqrt(
                    (center[0] - center_x) ** 2 + (center[1] - center_y) ** 2
                )
                max_distance = np.sqrt(center_x**2 + center_y**2)
                position_score += 1.0 - (distance_to_center / max_distance)

                # Size score (larger markers are better)
                corners = marker.corners
                area = cv2.contourArea(corners.astype(np.int32))
                max_area = (frame_width * frame_height) * 0.01  # 1% of frame
                size_score += min(area / max_area, 1.0)

            # Average scores
            position_score /= len(markers)
            size_score /= len(markers)

            # Combined score
            quality_score = marker_score * 0.4 + position_score * 0.3 + size_score * 0.3

            return min(quality_score, 1.0)

        except Exception as e:
            self.logger.error(f"Error calculating quality score: {e}")
            return 0.0

    def draw_markers(self, frame: np.ndarray, markers: list) -> np.ndarray:
        """Draw detected markers on the frame."""
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
        """Draw template information on the frame."""
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

    def draw_status_panel(self, frame: np.ndarray) -> np.ndarray:
        """Draw status panel with detection information."""
        try:
            # Status information
            status_text = [
                f"Frames: {self.total_frames}",
                f"Detections: {self.detection_frames}",
                f"Captures: {self.captures_made}",
                f"Detection Rate: {(self.detection_frames/max(self.total_frames, 1)*100):.1f}%",
            ]

            if self.current_template:
                status_text.append(f"Current: {self.current_template}")
                if self.auto_capture and self.template_detected_time:
                    time_since_detection = time.time() - self.template_detected_time
                    if time_since_detection < self.capture_delay:
                        remaining = self.capture_delay - time_since_detection
                        status_text.append(f"Auto-capture in: {remaining:.1f}s")
                    else:
                        status_text.append("Ready to capture!")
            else:
                status_text.append("No template detected")

            # Calculate panel position and size
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            line_height = 18

            # Get text dimensions
            max_width = 0
            for text in status_text:
                (text_width, _), _ = cv2.getTextSize(text, font, font_scale, thickness)
                max_width = max(max_width, text_width)

            panel_width = max_width + 15
            panel_height = len(status_text) * line_height + 15

            # Position panel in bottom-right corner
            panel_x = frame.shape[1] - panel_width - 10
            panel_y = frame.shape[0] - panel_height - 10

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
                1,
            )

            # Draw text
            for i, text in enumerate(status_text):
                y_pos = panel_y + 15 + i * line_height
                cv2.putText(
                    frame,
                    text,
                    (panel_x + 8, y_pos),
                    font,
                    font_scale,
                    (255, 255, 255),
                    thickness,
                )

        except Exception as e:
            self.logger.error(f"Error drawing status panel: {e}")

        return frame

    def draw_quality_indicator(
        self, frame: np.ndarray, quality_score: float
    ) -> np.ndarray:
        """Draw quality indicator on the frame."""
        try:
            if quality_score <= 0:
                return frame

            # Quality bar dimensions
            bar_width = 200
            bar_height = 20
            bar_x = 10
            bar_y = 60

            # Draw background bar
            cv2.rectangle(
                frame,
                (bar_x, bar_y),
                (bar_x + bar_width, bar_y + bar_height),
                (50, 50, 50),
                -1,
            )

            # Draw quality bar
            quality_width = int(bar_width * quality_score)
            color = (0, int(255 * quality_score), 0)  # Green based on quality
            cv2.rectangle(
                frame,
                (bar_x, bar_y),
                (bar_x + quality_width, bar_y + bar_height),
                color,
                -1,
            )

            # Draw border
            cv2.rectangle(
                frame,
                (bar_x, bar_y),
                (bar_x + bar_width, bar_y + bar_height),
                (255, 255, 255),
                2,
            )

            # Draw quality text
            quality_text = f"Quality: {quality_score:.1%}"
            cv2.putText(
                frame,
                quality_text,
                (bar_x + bar_width + 10, bar_y + 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

        except Exception as e:
            self.logger.error(f"Error drawing quality indicator: {e}")

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
        """Draw user instructions on the frame."""
        try:
            instructions = [
                "Press 'c' to capture manually",
                "Press 'q' to quit",
                "Press 'm' to toggle markers",
                "Press 'i' to toggle info",
                "Press 's' to toggle status",
                "Press 'a' to toggle auto-capture",
            ]

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.4
            thickness = 1
            line_height = 16

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
        """Capture current frame and process it."""
        try:
            current_time = time.time()

            # Check cooldown
            if current_time - self.last_capture_time < self.capture_cooldown:
                self.logger.info("Capture on cooldown")
                return False

            # Generate timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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
            if self.current_template and len(self.detected_markers) >= self.min_markers:
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
                    self.captures_made += 1
                    self.last_capture_time = current_time
                    return True
                else:
                    self.logger.error("Processing failed")
                    return False
            else:
                self.logger.warning(
                    "No template detected or insufficient markers, only saved raw frame"
                )
                self.last_capture_time = current_time
                return True

        except Exception as e:
            self.logger.error(f"Error capturing and processing: {e}")
            return False

    def check_auto_capture(self, frame: np.ndarray) -> bool:
        """Check if auto-capture should be triggered."""
        if not self.auto_capture or not self.current_template:
            return False

        current_time = time.time()

        # Check if we have enough markers
        if len(self.detected_markers) < self.min_markers:
            self.template_detected_time = None
            return False

        # Start detection timer
        if self.template_detected_time is None:
            self.template_detected_time = current_time
            return False

        # Check if delay has passed
        if current_time - self.template_detected_time >= self.capture_delay:
            # Check cooldown
            if current_time - self.last_capture_time >= self.capture_cooldown:
                return True

        return False

    def run(self):
        """Main webcam detection loop."""
        if not self.start_camera():
            return

        self.is_running = True
        self.logger.info("Starting advanced webcam detection loop")

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

                self.total_frames += 1

                # Detect markers and template
                markers, template_id = self.detect_markers_in_frame(frame)
                self.detected_markers = markers

                # Update detection statistics
                if markers:
                    self.detection_frames += 1

                # Update template state
                if template_id != self.current_template:
                    self.current_template = template_id
                    self.template_detected_time = None
                    if template_id:
                        self.current_template_config = (
                            self.aruco_detector.current_template_config
                        )
                        self.logger.info(f"Template detected: {template_id}")

                # Check auto-capture
                if self.check_auto_capture(frame):
                    if self.capture_and_process(frame):
                        success_msg = f"✅ Auto-captured: {self.current_template}"
                        print(success_msg)
                        self.show_notification(success_msg)
                        self.template_detected_time = None  # Reset for next capture

                # Calculate quality score
                quality_score = self.calculate_quality_score(markers, frame)

                # Draw overlays
                if self.show_markers:
                    frame = self.draw_markers(frame, markers)

                if self.show_template_info and template_id:
                    frame = self.draw_template_info(frame, template_id)

                if self.show_status:
                    frame = self.draw_status_panel(frame)

                if self.show_quality and markers:
                    frame = self.draw_quality_indicator(frame, quality_score)

                if self.show_fps:
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

                # Draw notification (if any)
                frame = self.draw_notification(frame)

                # Draw instructions
                frame = self.draw_instructions(frame)

                # Display frame
                cv2.imshow("Krathong Scanner - Advanced Webcam Detection", frame)

                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("c"):
                    if self.capture_and_process(frame):
                        success_msg = f"✅ Manual capture: {self.current_template}"
                        print(success_msg)
                        self.show_notification(success_msg)
                    else:
                        error_msg = "❌ Manual capture failed"
                        print(error_msg)
                        self.show_notification(error_msg)
                elif key == ord("m"):
                    self.show_markers = not self.show_markers
                    print(f"Markers: {'ON' if self.show_markers else 'OFF'}")
                elif key == ord("i"):
                    self.show_template_info = not self.show_template_info
                    print(f"Info: {'ON' if self.show_template_info else 'OFF'}")
                elif key == ord("s"):
                    self.show_status = not self.show_status
                    print(f"Status: {'ON' if self.show_status else 'OFF'}")
                elif key == ord("a"):
                    self.auto_capture = not self.auto_capture
                    print(f"Auto-capture: {'ON' if self.auto_capture else 'OFF'}")

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
            self.logger.info("Advanced webcam detection stopped")


def main():
    """Main function to run advanced webcam detection."""
    print("🎥 Krathong Scanner - Advanced Webcam Detection")
    print("=" * 50)
    print("Features:")
    print("  - Real-time template detection")
    print("  - Automatic capture when template detected")
    print("  - Quality indicators")
    print("  - Status monitoring")
    print("=" * 50)
    print("Controls:")
    print("  'c' - Manual capture")
    print("  'q' - Quit")
    print("  'm' - Toggle markers")
    print("  'i' - Toggle template info")
    print("  's' - Toggle status panel")
    print("  'a' - Toggle auto-capture")
    print("=" * 50)

    # Initialize advanced webcam detector
    detector = AdvancedWebcamDetector(
        camera_index=0,
        frame_width=1280,
        frame_height=720,
        fps=30,
        auto_capture=True,
        capture_delay=2.0,
        min_markers=4,
    )

    # Run detection loop
    detector.run()


if __name__ == "__main__":
    main()
