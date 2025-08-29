"""
Paper detection and auto-zoom functionality for KrathongScanner.

This module provides:
- Paper rectangle detection using contour analysis
- Auto-zoom to standard size for consistent processing
- Integration with existing ArUco detection pipeline
"""

import logging
import time
from typing import List, Optional, Tuple

import cv2
import numpy as np


class PaperDetector:
    """
    Detects paper rectangles and provides auto-zoom functionality.

    Features:
    - Paper boundary detection using contour analysis
    - Auto-zoom to standard size for consistent processing
    - Fallback to original frame if detection fails
    """

    def __init__(self, target_size: Tuple[int, int] = (1280, 720)):
        """
        Initialize the paper detector.

        Args:
            target_size: Target size for auto-zoom (width, height)
        """
        self.logger = self._setup_logger()
        self.target_size = target_size
        self.min_paper_area = 50000  # Minimum area to consider as paper
        self.max_paper_area = 1000000  # Maximum area to consider as paper

        # Stabilization parameters
        self.stabilization_frames = 15  # Number of frames to average (increased)
        self.detection_threshold = (
            0.8  # Minimum detection confidence to update (increased)
        )
        self.stable_contour = None  # Store the last stable contour
        self.contour_history = []  # History of detected contours
        self.stability_counter = 0  # Counter for stable detections
        self.last_update_time = 0  # Time of last update
        self.update_interval = 3.0  # Minimum seconds between updates (increased)
        self.min_stability_count = 5  # Minimum stable detections before updating

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the paper detector."""
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

    def detect_paper_contour(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect paper rectangle contour in the frame with stabilization.

        Args:
            frame: Input frame (BGR format)

        Returns:
            Paper contour if detected, None otherwise
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Edge detection
            edges = cv2.Canny(blurred, 50, 150)

            # Find contours
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if not contours:
                return self._get_stable_contour()

            # Find the best paper contour
            paper_contour = self._find_best_paper_contour(contours)

            if paper_contour is not None:
                # Update stabilization
                return self._update_stabilization(paper_contour)
            else:
                return self._get_stable_contour()

        except Exception as e:
            self.logger.error(f"Error detecting paper contour: {e}")
            return self._get_stable_contour()

    def _find_best_paper_contour(
        self, contours: List[np.ndarray]
    ) -> Optional[np.ndarray]:
        """
        Find the best contour that represents a paper rectangle.

        Args:
            contours: List of detected contours

        Returns:
            Best paper contour if found, None otherwise
        """
        best_contour = None
        best_score = 0

        for contour in contours:
            # Calculate contour area
            area = cv2.contourArea(contour)

            # Skip contours that are too small or too large
            if area < self.min_paper_area or area > self.max_paper_area:
                continue

            # Approximate contour to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Check if it's approximately rectangular (4 corners)
            if len(approx) == 4:
                # Calculate rectangularity score
                rect_area = cv2.contourArea(approx)
                rect_score = rect_area / area if area > 0 else 0

                # Additional score for being close to target aspect ratio
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / h if h > 0 else 0
                target_ratio = self.target_size[0] / self.target_size[1]
                ratio_score = 1.0 - min(
                    abs(aspect_ratio - target_ratio) / target_ratio, 1.0
                )

                # Combined score
                score = rect_score * 0.7 + ratio_score * 0.3

                if score > best_score:
                    best_score = score
                    best_contour = approx

        return best_contour

    def _update_stabilization(self, new_contour: np.ndarray) -> np.ndarray:
        """
        Update stabilization with new contour detection.

        Args:
            new_contour: Newly detected contour

        Returns:
            Stabilized contour
        """
        current_time = time.time()

        # Add to history
        self.contour_history.append(new_contour)

        # Keep only recent history
        if len(self.contour_history) > self.stabilization_frames:
            self.contour_history.pop(0)

        # Check if we should update the stable contour
        should_update = False

        # Update if we have enough history and enough time has passed
        if (
            len(self.contour_history) >= self.stabilization_frames
            and current_time - self.last_update_time > self.update_interval
        ):
            # Check if contours are similar (stable detection)
            if self._are_contours_similar(self.contour_history):
                self.stability_counter += 1
                # Only update if we have enough stable detections
                if self.stability_counter >= self.min_stability_count:
                    should_update = True
            else:
                self.stability_counter = 0

        # Update stable contour if conditions are met
        if should_update or self.stable_contour is None:
            self.stable_contour = self._average_contours(self.contour_history)
            self.last_update_time = current_time
            self.logger.info(
                f"Updated stable contour (stability: {self.stability_counter})"
            )

        return self.stable_contour

    def _get_stable_contour(self) -> Optional[np.ndarray]:
        """
        Get the current stable contour.

        Returns:
            Stable contour if available, None otherwise
        """
        return self.stable_contour

    def _are_contours_similar(self, contours: List[np.ndarray]) -> bool:
        """
        Check if contours are similar enough to be considered stable.

        Args:
            contours: List of contours to compare

        Returns:
            True if contours are similar, False otherwise
        """
        if len(contours) < 2:
            return False

        # Calculate areas of all contours
        areas = [cv2.contourArea(contour) for contour in contours]

        # Check if areas are within 10% of each other
        mean_area = np.mean(areas)
        area_variance = np.std(areas) / mean_area

        return area_variance < 0.05  # 5% variance threshold (more strict)

    def _average_contours(self, contours: List[np.ndarray]) -> np.ndarray:
        """
        Average multiple contours to create a stable contour.

        Args:
            contours: List of contours to average

        Returns:
            Averaged contour
        """
        if not contours:
            return None

        if len(contours) == 1:
            return contours[0]

        # Convert contours to points and average them
        all_points = []
        for contour in contours:
            points = contour.reshape(-1, 2)
            all_points.append(points)

        # Average the points
        avg_points = np.mean(all_points, axis=0)

        # Convert back to contour format
        return avg_points.reshape(-1, 1, 2).astype(np.int32)

    def reset_stabilization(self):
        """Reset stabilization state."""
        self.stable_contour = None
        self.contour_history = []
        self.stability_counter = 0
        self.last_update_time = 0
        self.logger.info("Paper detection stabilization reset")

    def auto_zoom_to_paper(
        self, frame: np.ndarray, paper_contour: np.ndarray
    ) -> np.ndarray:
        """
        Auto-zoom the paper to target size using perspective transform.

        Args:
            frame: Input frame
            paper_contour: Detected paper contour

        Returns:
            Zoomed and cropped frame
        """
        try:
            # Get the four corners of the paper contour
            corners = paper_contour.reshape(4, 2)

            # Sort corners to get proper order: top-left, top-right, bottom-right, bottom-left
            corners = self._sort_corners(corners)

            # Calculate the width and height of the paper
            width = max(
                np.linalg.norm(corners[1] - corners[0]),  # Top edge
                np.linalg.norm(corners[2] - corners[3]),  # Bottom edge
            )
            height = max(
                np.linalg.norm(corners[3] - corners[0]),  # Left edge
                np.linalg.norm(corners[2] - corners[1]),  # Right edge
            )

            # Calculate scaling factor to match target size
            scale_x = self.target_size[0] / width
            scale_y = self.target_size[1] / height
            scale = min(scale_x, scale_y)  # Maintain aspect ratio

            # Calculate new dimensions
            new_width = int(width * scale)
            new_height = int(height * scale)

            # Define destination points for perspective transform
            dst_points = np.array(
                [
                    [0, 0],  # Top-left
                    [new_width, 0],  # Top-right
                    [new_width, new_height],  # Bottom-right
                    [0, new_height],  # Bottom-left
                ],
                dtype=np.float32,
            )

            # Convert source corners to float32
            src_points = corners.astype(np.float32)

            # Calculate perspective transform matrix
            transform_matrix = cv2.getPerspectiveTransform(src_points, dst_points)

            # Apply perspective transform
            warped = cv2.warpPerspective(
                frame,
                transform_matrix,
                (new_width, new_height),
                flags=cv2.INTER_LANCZOS4,
            )

            # Create output frame with target size
            output = np.zeros(
                (self.target_size[1], self.target_size[0], 3), dtype=np.uint8
            )

            # Center the warped image
            start_x = (self.target_size[0] - new_width) // 2
            start_y = (self.target_size[1] - new_height) // 2
            output[
                start_y : start_y + new_height, start_x : start_x + new_width
            ] = warped

            return output

        except Exception as e:
            self.logger.error(f"Error in auto-zoom: {e}")
            return frame

    def _sort_corners(self, corners: np.ndarray) -> np.ndarray:
        """
        Sort corners to get proper order: top-left, top-right, bottom-right, bottom-left.

        Args:
            corners: Array of 4 corner points

        Returns:
            Sorted corners array
        """
        # Find the center point
        center = np.mean(corners, axis=0)

        # Separate corners into top and bottom based on y-coordinate
        top_corners = []
        bottom_corners = []

        for corner in corners:
            if corner[1] < center[1]:
                top_corners.append(corner)
            else:
                bottom_corners.append(corner)

        # Sort top corners by x-coordinate (left to right)
        top_corners = sorted(top_corners, key=lambda p: p[0])

        # Sort bottom corners by x-coordinate (left to right)
        bottom_corners = sorted(bottom_corners, key=lambda p: p[0])

        # Return in order: top-left, top-right, bottom-right, bottom-left
        return np.array(
            [top_corners[0], top_corners[1], bottom_corners[1], bottom_corners[0]]
        )

    def process_with_auto_zoom(self, frame: np.ndarray) -> Tuple[np.ndarray, bool]:
        """
        Process frame with paper detection and auto-zoom.

        Args:
            frame: Input frame

        Returns:
            Tuple of (processed_frame, success_flag)
        """
        try:
            # Detect paper contour
            paper_contour = self.detect_paper_contour(frame)

            if paper_contour is not None and self.is_paper_detection_stable():
                # Auto-zoom to target size
                zoomed_frame = self.auto_zoom_to_paper(frame, paper_contour)
                # Only log occasionally to avoid spam
                if hasattr(self, "_last_log_time"):
                    current_time = time.time()
                    if current_time - self._last_log_time > 5.0:  # Log every 5 seconds
                        self.logger.info("Paper detected and auto-zoomed")
                        self._last_log_time = current_time
                else:
                    self.logger.info("Paper detected and auto-zoomed")
                    self._last_log_time = time.time()
                return zoomed_frame, True
            else:
                # Fallback to original frame
                # Only log occasionally to avoid spam
                if hasattr(self, "_last_no_paper_log_time"):
                    current_time = time.time()
                    if (
                        current_time - self._last_no_paper_log_time > 10.0
                    ):  # Log every 10 seconds
                        self.logger.warning(
                            "No paper detected or unstable, using original frame"
                        )
                        self._last_no_paper_log_time = current_time
                else:
                    self.logger.warning(
                        "No paper detected or unstable, using original frame"
                    )
                    self._last_no_paper_log_time = time.time()
                return frame, False

        except Exception as e:
            self.logger.error(f"Error in process_with_auto_zoom: {e}")
            return frame, False

    def is_paper_detection_stable(self) -> bool:
        """
        Check if paper detection is stable enough for auto-zoom.

        Returns:
            True if detection is stable, False otherwise
        """
        return (
            self.stable_contour is not None
            and self.stability_counter >= self.min_stability_count
            and len(self.contour_history) >= self.stabilization_frames
        )

    def draw_paper_detection(
        self, frame: np.ndarray, paper_contour: Optional[np.ndarray]
    ) -> np.ndarray:
        """
        Draw paper detection visualization on frame.

        Args:
            frame: Input frame
            paper_contour: Detected paper contour

        Returns:
            Frame with detection visualization
        """
        try:
            if paper_contour is not None:
                # Draw paper contour (green line)
                cv2.drawContours(frame, [paper_contour], -1, (0, 255, 0), 2)

                # Draw corner points
                corners = paper_contour.reshape(4, 2)
                for i, corner in enumerate(corners):
                    cv2.circle(frame, tuple(corner.astype(int)), 5, (255, 0, 255), -1)
                    cv2.putText(
                        frame,
                        str(i),
                        tuple(corner.astype(int)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 0, 255),
                        1,
                    )

                # Add text
                x, y, w, h = cv2.boundingRect(paper_contour)
                cv2.putText(
                    frame,
                    "Paper Detected",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )
            else:
                # Add "No Paper" text
                cv2.putText(
                    frame,
                    "No Paper Detected",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2,
                )

            return frame

        except Exception as e:
            self.logger.error(f"Error drawing paper detection: {e}")
            return frame


def main():
    """Test the paper detector with a sample image."""
    import sys
    from pathlib import Path

    if len(sys.argv) != 2:
        print("Usage: python paper_detector.py <image_path>")
        return

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        return

    # Load image
    frame = cv2.imread(str(image_path))
    if frame is None:
        print(f"Could not load image: {image_path}")
        return

    # Initialize paper detector
    detector = PaperDetector()

    # Process with auto-zoom
    processed_frame, success = detector.process_with_auto_zoom(frame)

    # Detect paper contour for visualization
    paper_contour = detector.detect_paper_contour(frame)

    # Draw detection visualization
    frame_with_detection = detector.draw_paper_detection(frame.copy(), paper_contour)

    # Display results
    cv2.imshow("Original with Detection", frame_with_detection)
    cv2.imshow("Auto-zoomed", processed_frame)

    print(f"Paper detection: {'Success' if success else 'Failed'}")
    print("Press any key to exit...")

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
