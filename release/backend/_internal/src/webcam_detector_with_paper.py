"""
Enhanced webcam detector with paper detection and auto-zoom functionality.

This module combines:
- Paper detection and auto-zoom for consistent scaling
- ArUco marker detection and processing
- Real-time webcam processing with visual feedback
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

from aruco_detector import ArUcoDetector
from paper_detector import PaperDetector


class WebcamDetectorWithPaper:
    """
    Enhanced webcam detector with paper detection and auto-zoom.

    Features:
    - Paper detection and auto-zoom for consistent scaling
    - ArUco marker detection and processing
    - Real-time visual feedback
    - Manual capture with 'c' key
    """

    def __init__(self, camera_id: int = 0, capture_dir: str = "data/webcam_captures"):
        """
        Initialize the enhanced webcam detector.

        Args:
            camera_id: Camera device ID
            capture_dir: Directory to save captured images
        """
        self.logger = self._setup_logger()
        self.camera_id = camera_id
        # Use the provided capture directory or default
        if capture_dir and capture_dir != "data/webcam_captures":
            # Use the custom directory provided by the UI
            self.capture_dir = Path(capture_dir)
        else:
            # Use default directory
            self.capture_dir = Path(__file__).parent.parent / capture_dir
        
        self.capture_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Capture directory: {self.capture_dir}")

        # Initialize components
        self.paper_detector = PaperDetector(target_size=(1280, 720))
        self.aruco_detector = ArUcoDetector()

        # Camera and processing state
        self.cap = None
        self.is_running = False
        self.detected_markers = []
        self.current_template = None

        # UI settings
        self.show_markers = True
        self.show_paper_detection = True
        self.show_fps = True

        # Notification system
        self.notifications = []
        self.notification_duration = 3.0  # seconds

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
        """Start the camera capture."""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                self.logger.error(f"Could not open camera {self.camera_id}")
                return False

            # Set camera properties for better quality
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            self.logger.info(f"Camera {self.camera_id} started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error starting camera: {e}")
            return False

    def stop_camera(self):
        """Stop the camera capture."""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.logger.info("Camera stopped")

    def detect_markers_in_frame(self, frame: np.ndarray) -> Tuple[List, Optional[str]]:
        """
        Detect ArUco markers in the frame.

        Args:
            frame: Input frame

        Returns:
            Tuple of (markers, template_id)
        """
        try:
            # Detect markers
            markers = self.aruco_detector.detect_markers(frame)

            if markers:
                marker_ids = [marker.id for marker in markers]

                # Detect template (use partial detection for display)
                template_id = self.aruco_detector.detect_template(
                    marker_ids, use_partial=True
                )

                return markers, template_id
            else:
                return [], None

        except Exception as e:
            self.logger.error(f"Error detecting markers: {e}")
            return [], None

    def capture_and_process(self, frame: np.ndarray) -> bool:
        """
        Capture and process the current frame.

        Args:
            frame: Input frame (this should be the original frame, not processed)

        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Check if we have enough markers for processing
            if len(self.detected_markers) < 4:
                self.logger.warning(
                    f"Only {len(self.detected_markers)} markers detected, need 4 for processing"
                )
                return False

            # Generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Process the captured image
            if self.current_template:
                # Use template-specific processing
                output_filename = f"{self.current_template}_{timestamp}_processed.png"
                output_path = self.capture_dir / output_filename

                # Apply paper detection and auto-zoom to the frame before processing
                paper_contour = self.paper_detector.detect_paper_contour(frame)
                if paper_contour is not None:
                    # Use the auto-zoomed frame for processing
                    processed_frame, _ = self.paper_detector.process_with_auto_zoom(
                        frame
                    )
                    self.logger.info(
                        f"Paper detected, using auto-zoomed frame for processing"
                    )
                else:
                    # Use original frame if no paper detected
                    processed_frame = frame
                    self.logger.info(
                        f"No paper detected, using original frame for processing"
                    )

                # Process with ArUco detector (using homography for better perspective correction)
                self.logger.info(f"Processing image to: {output_path}")
                success = self.aruco_detector.process_frame(
                    processed_frame, output_path, use_homography=True
                )

                if success:
                    self.logger.info(f"Image processed and saved: {output_path}")
                    self.show_notification(
                        "✅ Image captured and processed successfully!"
                    )
                    return True
                else:
                    self.logger.error("Failed to process image")
                    self.show_notification("❌ Image processing failed")
                    return False
            else:
                self.logger.warning("No template detected for processing")
                self.show_notification("❌ No template detected")
                return False

        except Exception as e:
            self.logger.error(f"Error in capture_and_process: {e}")
            self.show_notification("❌ Capture/processing failed")
            return False

    def show_notification(self, message: str):
        """Add a notification message to display."""
        self.logger.info(f"Notification: {message}")
        self.notifications.append(
            {
                "message": message,
                "timestamp": time.time(),
                "color": (0, 255, 0) if "✅" in message else (0, 0, 255),
            }
        )

    def draw_ui(
        self, frame: np.ndarray, fps: float, markers: List, template_id: Optional[str]
    ):
        """
        Draw UI elements on the frame.

        Args:
            frame: Input frame
            fps: Current FPS
            markers: Detected markers
            template_id: Detected template ID
        """
        try:
            # Draw markers
            if self.show_markers and markers:
                self.draw_markers(frame, markers)

            # Draw FPS
            if self.show_fps:
                cv2.putText(
                    frame,
                    f"FPS: {fps:.1f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

            # Draw template info
            if template_id:
                cv2.putText(
                    frame,
                    f"Template: {template_id}",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 0),
                    2,
                )

            # Draw marker count
            cv2.putText(
                frame,
                f"Markers: {len(markers)}/4",
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2,
            )

            # Draw paper detection stability
            if hasattr(self.paper_detector, "stability_counter"):
                stability_color = (
                    (0, 255, 0)
                    if self.paper_detector.stability_counter > 3
                    else (255, 255, 0)
                )
                cv2.putText(
                    frame,
                    f"Paper Stability: {self.paper_detector.stability_counter}",
                    (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    stability_color,
                    2,
                )

            # Draw instructions
            cv2.putText(
                frame,
                "Press 'c' to capture, 'r' to reset stabilization, 'q' to quit",
                (10, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            # Draw notifications
            self.draw_notifications(frame)

        except Exception as e:
            self.logger.error(f"Error drawing UI: {e}")

    def draw_markers(self, frame: np.ndarray, markers: List):
        """Draw detected markers on the frame."""
        try:
            for marker in markers:
                # Convert to numpy arrays
                corners = np.array(marker.corners, dtype=np.int32)
                center = np.array(marker.center, dtype=np.int32)

                # Draw marker outline
                cv2.polylines(frame, [corners], True, (0, 255, 0), 2)

                # Draw marker center
                cv2.circle(frame, tuple(center), 5, (0, 0, 255), -1)

                # Draw marker ID
                cv2.putText(
                    frame,
                    str(marker.id),
                    tuple(center),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                )

        except Exception as e:
            self.logger.error(f"Error drawing markers: {e}")

    def draw_notifications(self, frame: np.ndarray):
        """Draw notification messages on the frame."""
        try:
            current_time = time.time()
            active_notifications = []

            for notification in self.notifications:
                age = current_time - notification["timestamp"]
                if age < self.notification_duration:
                    active_notifications.append(notification)
                else:
                    continue

            # Update notifications list
            self.notifications = active_notifications

            # Draw active notifications
            y_offset = 120
            for notification in active_notifications:
                age = current_time - notification["timestamp"]
                alpha = 1.0 - (age / self.notification_duration)  # Fade out effect

                # Create background rectangle
                text_size = cv2.getTextSize(
                    notification["message"], cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
                )[0]
                bg_rect = (10, y_offset - 25, text_size[0] + 20, text_size[1] + 10)

                # Draw background with alpha
                overlay = frame.copy()
                cv2.rectangle(
                    overlay,
                    (bg_rect[0], bg_rect[1]),
                    (bg_rect[0] + bg_rect[2], bg_rect[1] + bg_rect[3]),
                    (0, 0, 0),
                    -1,
                )
                frame = cv2.addWeighted(overlay, alpha * 0.7, frame, 1 - alpha * 0.7, 0)

                # Draw text
                cv2.putText(
                    frame,
                    notification["message"],
                    (15, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    notification["color"],
                    2,
                )

                y_offset += 40

        except Exception as e:
            self.logger.error(f"Error drawing notifications: {e}")

    def run(self):
        """Main processing loop."""
        try:
            if not self.start_camera():
                return

            self.is_running = True
            self.logger.info("Enhanced webcam detection started")

            fps_counter = 0
            fps_start_time = time.time()
            fps = 0

            while self.is_running:
                # Read frame
                ret, frame = self.cap.read()
                if not ret:
                    self.logger.error("Failed to read frame")
                    break

                # Detect markers in the original frame first
                markers, template_id = self.detect_markers_in_frame(frame)

                # Process frame with paper detection and auto-zoom
                (
                    processed_frame,
                    paper_detected,
                ) = self.paper_detector.process_with_auto_zoom(frame)

                # Update state
                self.detected_markers = markers
                self.current_template = template_id

                # Calculate FPS
                fps_counter += 1
                if fps_counter % 30 == 0:
                    current_time = time.time()
                    fps = 30 / (current_time - fps_start_time)
                    fps_start_time = current_time

                # Draw UI
                self.draw_ui(processed_frame, fps, markers, template_id)

                # Draw paper detection visualization
                if self.show_paper_detection:
                    paper_contour = self.paper_detector.detect_paper_contour(frame)
                    processed_frame = self.paper_detector.draw_paper_detection(
                        processed_frame, paper_contour
                    )

                # Display frame
                cv2.imshow("KrathongScanner - Enhanced", processed_frame)

                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("c"):
                    # Capture and process (use original frame)
                    success = self.capture_and_process(frame)
                    if not success:
                        if len(self.detected_markers) < 4:
                            error_msg = f"❌ Need 4 markers, only {len(self.detected_markers)} detected"
                        else:
                            error_msg = "❌ Capture/processing failed"
                        self.show_notification(error_msg)
                elif key == ord("m"):
                    # Toggle marker display
                    self.show_markers = not self.show_markers
                elif key == ord("p"):
                    # Toggle paper detection display
                    self.show_paper_detection = not self.show_paper_detection
                elif key == ord("f"):
                    # Toggle FPS display
                    self.show_fps = not self.show_fps
                elif key == ord("r"):
                    # Reset paper detection stabilization
                    self.paper_detector.reset_stabilization()
                    self.show_notification("🔄 Paper detection stabilization reset")

        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")

        finally:
            self.stop_camera()
            cv2.destroyAllWindows()
            self.is_running = False
            self.logger.info("Enhanced webcam detection stopped")


def main():
    """Main function to run the enhanced webcam detector."""
    detector = WebcamDetectorWithPaper()
    detector.run()


if __name__ == "__main__":
    main()
