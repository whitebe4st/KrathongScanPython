"""
Document scanner using OpenCV for robust paper/document detection.

This module provides:
- Advanced document detection using edge detection and contour analysis
- Perspective correction using getPerspectiveTransform
- Better handling of real photos with various lighting conditions
- Integration with existing ArUco detection pipeline
"""

import logging
import time
from typing import List, Optional, Tuple

import cv2
import numpy as np


class DocumentScanner:
    """
    Advanced document scanner using OpenCV for robust paper/document detection.

    Based on the robust approach from scantest.py with multiple fallback methods.
    """

    def __init__(self, target_size: Tuple[int, int] = (1280, 720)):
        """
        Initialize the document scanner.

        Args:
            target_size: Target size for perspective correction (width, height)
        """
        self.logger = self._setup_logger()
        self.target_size = target_size

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the document scanner."""
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

    def process_image(self, image: np.ndarray) -> Tuple[np.ndarray, bool]:
        """
        Process image to detect and correct document perspective.

        Args:
            image: Input image (BGR format)

        Returns:
            Tuple of (processed_image, success_flag)
        """
        try:
            # Find document contour
            contour = self.find_document_contour(image)
            if contour is None:
                self.logger.warning("No document contour found")
                return image, False

            # Apply perspective correction
            corrected = self.correct_perspective(image, contour)
            if corrected is None:
                self.logger.warning("Perspective correction failed")
                return image, False

            self.logger.info("Document detected and perspective corrected successfully")
            return corrected, True

        except Exception as e:
            self.logger.error(f"Error processing image: {e}")
            return image, False

    def find_document_contour(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Find the document contour using the robust approach from scantest.py"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Get image dimensions
            height, width = image.shape[:2]
            image_area = height * width

            # Method 1: Simplified paper boundary detection (most reliable)
            contour = self._find_paper_boundary_simple(gray, image_area)
            if contour is not None:
                self.logger.info(
                    "Document found using simplified paper boundary detection"
                )
                return contour

            # Method 2: Largest rectangle fallback
            contour = self._find_largest_rectangle(gray, image_area)
            if contour is not None:
                self.logger.info("Document found using largest rectangle fallback")
                return contour

            # Method 3: Fallback to reasonable document boundary (80% of image)
            margin_x = int(width * 0.1)
            margin_y = int(height * 0.1)

            fallback_contour = np.array(
                [
                    [margin_x, margin_y],
                    [width - margin_x, margin_y],
                    [width - margin_x, height - margin_y],
                    [margin_x, height - margin_y],
                ]
            ).reshape(-1, 1, 2)

            self.logger.info("Using fallback document boundary (80% of image)")
            return fallback_contour

        except Exception as e:
            self.logger.error(f"Error finding document contour: {e}")
            return None

    def _find_paper_boundary_simple(
        self, gray: np.ndarray, image_area: int
    ) -> Optional[np.ndarray]:
        """Simplified paper boundary detection focusing on reliability"""
        try:
            height, width = gray.shape

            # Method 1: Heavy blur + Otsu thresholding (most reliable for paper detection)
            heavily_blurred = cv2.GaussianBlur(gray, (51, 51), 0)  # Very heavy blur

            # Use Otsu thresholding to separate paper from background
            _, binary = cv2.threshold(
                heavily_blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            # Find the largest contour (should be the paper)
            contours, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)

                # Paper should be at least 20% of the image
                if area > image_area * 0.2:
                    # Use convex hull and then minimum area rectangle for clean boundaries
                    hull = cv2.convexHull(largest_contour)
                    rect = cv2.minAreaRect(hull)
                    box = cv2.boxPoints(rect)
                    contour = np.array(box, dtype=np.int32).reshape(-1, 1, 2)

                    # Make sure it's not the entire image
                    if not self._is_full_image(contour, width, height):
                        return contour

            # Method 2: Edge detection with very low thresholds
            blurred = cv2.GaussianBlur(gray, (9, 9), 0)
            edges = cv2.Canny(blurred, 10, 50, apertureSize=3)

            # Dilate edges to connect paper boundaries
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
            dilated = cv2.dilate(edges, kernel, iterations=3)

            # Find contours
            contours, _ = cv2.findContours(
                dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Look for rectangular contours
            for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
                area = cv2.contourArea(contour)

                if area > image_area * 0.15:  # At least 15% of image
                    # Try to approximate as rectangle
                    perimeter = cv2.arcLength(contour, True)
                    epsilon = 0.02 * perimeter
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    if len(approx) >= 4:
                        if len(approx) > 4:
                            # Convert to minimum area rectangle
                            rect = cv2.minAreaRect(contour)
                            box = cv2.boxPoints(rect)
                            approx = np.array(box, dtype=np.int32).reshape(-1, 1, 2)

                        if not self._is_full_image(approx, width, height):
                            return approx

            return None

        except Exception as e:
            self.logger.error(f"Error in simplified paper boundary detection: {e}")
            return None

    def _find_largest_rectangle(
        self, gray: np.ndarray, image_area: int
    ) -> Optional[np.ndarray]:
        """Find the largest reasonable rectangle in the image"""
        try:
            height, width = gray.shape

            # Apply adaptive threshold
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Find contours
            contours, _ = cv2.findContours(
                adaptive, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )

            best_contour = None
            best_area = 0

            for contour in contours:
                area = cv2.contourArea(contour)

                # Must be substantial but not the whole image
                if image_area * 0.1 < area < image_area * 0.95:
                    perimeter = cv2.arcLength(contour, True)
                    epsilon = 0.02 * perimeter
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    if len(approx) == 4:
                        if not self._is_full_image(approx, width, height):
                            if area > best_area:
                                best_area = area
                                best_contour = approx

                    elif len(approx) > 4:
                        # Convert to rectangle
                        rect = cv2.minAreaRect(contour)
                        box = cv2.boxPoints(rect)
                        rect_approx = np.array(box, dtype=np.int32).reshape(-1, 1, 2)

                        if not self._is_full_image(rect_approx, width, height):
                            if area > best_area:
                                best_area = area
                                best_contour = rect_approx

            return best_contour

        except Exception as e:
            self.logger.error(f"Error in largest rectangle detection: {e}")
            return None

    def _is_full_image(self, contour: np.ndarray, width: int, height: int) -> bool:
        """Check if contour covers almost the entire image"""
        pts = contour.reshape(4, 2)

        # Calculate bounding box
        min_x, min_y = np.min(pts, axis=0)
        max_x, max_y = np.max(pts, axis=0)

        # Check margins from edges
        margin_threshold = 30  # pixels

        return (
            min_x < margin_threshold
            and min_y < margin_threshold
            and max_x > width - margin_threshold
            and max_y > height - margin_threshold
        )

    def correct_perspective(
        self, image: np.ndarray, contour: np.ndarray
    ) -> Optional[np.ndarray]:
        """
        Correct perspective of the document using the detected contour.

        Args:
            image: Input image (BGR format)
            contour: Document contour (4 points)

        Returns:
            Perspective-corrected image if successful, None otherwise
        """
        try:
            # Order the contour points (top-left, top-right, bottom-right, bottom-left)
            ordered_points = self._order_points(contour.reshape(4, 2))

            # Calculate the width and height of the new image
            width_a = np.linalg.norm(ordered_points[0] - ordered_points[1])
            width_b = np.linalg.norm(ordered_points[2] - ordered_points[3])
            max_width = max(int(width_a), int(width_b))

            height_a = np.linalg.norm(ordered_points[0] - ordered_points[3])
            height_b = np.linalg.norm(ordered_points[1] - ordered_points[2])
            max_height = max(int(height_a), int(height_b))

            # Limit the output size to prevent "zoomed in too much" effect
            # Use conservative size to preserve ArUco markers
            max_reasonable_width = 800  # Conservative size
            max_reasonable_height = 600  # Conservative size

            if max_width > max_reasonable_width or max_height > max_reasonable_height:
                # Scale down proportionally
                scale_w = max_reasonable_width / max_width
                scale_h = max_reasonable_height / max_height
                scale = min(scale_w, scale_h)

                max_width = int(max_width * scale)
                max_height = int(max_height * scale)

                self.logger.info(
                    f"Scaled document size to preserve ArUco markers: {max_width}x{max_height}"
                )

            # Define destination points
            dst = np.array(
                [
                    [0, 0],
                    [max_width - 1, 0],
                    [max_width - 1, max_height - 1],
                    [0, max_height - 1],
                ],
                dtype=np.float32,
            )

            # Calculate perspective transformation matrix
            matrix = cv2.getPerspectiveTransform(ordered_points.astype(np.float32), dst)

            # Apply perspective transformation
            warped = cv2.warpPerspective(image, matrix, (max_width, max_height))

            self.logger.info(f"Perspective corrected: {max_width}x{max_height}")
            return warped

        except Exception as e:
            self.logger.error(f"Error in perspective correction: {e}")
            return None

    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """
        Order points in the order: top-left, top-right, bottom-right, bottom-left.

        Args:
            pts: Array of 4 points

        Returns:
            Ordered array of points
        """
        rect = np.zeros((4, 2), dtype="float32")

        # Sum and difference to find corners
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)

        rect[0] = pts[np.argmin(s)]  # top-left
        rect[2] = pts[np.argmax(s)]  # bottom-right
        rect[1] = pts[np.argmin(diff)]  # top-right
        rect[3] = pts[np.argmax(diff)]  # bottom-left

        return rect
