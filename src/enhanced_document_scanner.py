"""
Enhanced Document Scanner using the robust approach from scantest.py.

This module provides:
- Robust document detection using multiple fallback methods
- Better handling of real photos with various lighting conditions
- Integration with ArUco detection pipeline
- Paper detection first, then ArUco detection, then mask application
"""

import logging
import time
from typing import List, Optional, Tuple

import cv2
import numpy as np


class EnhancedDocumentScanner:
    """
    Enhanced document scanner using the robust approach from scantest.py.

    Pipeline: detect paper -> detect aruco -> apply mask
    """

    def __init__(self, target_size: Tuple[int, int] = (1280, 720)):
        """
        Initialize the enhanced document scanner.

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
        Process image to detect and correct document perspective using robust methods.

        Args:
            image: Input image (BGR format)

        Returns:
            Tuple of (processed_image, success_flag)
        """
        try:
            # Find document contour using robust methods from scantest.py
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

            # Try multiple methods in order of reliability
            methods = [
                ("simplified paper boundary", self._find_paper_boundary_simple),
                ("largest rectangle", self._find_largest_rectangle),
                ("outermost paper boundary", self._find_outermost_paper_boundary),
                ("contour with preprocessing", self._find_contour_with_preprocessing),
                ("standard edge detection", self._find_contour_standard),
                ("adaptive threshold", self._find_contour_adaptive),
                ("morphology operations", self._find_contour_morphology),
                ("multi-canny", self._find_contour_multi_canny),
            ]

            for method_name, method_func in methods:
                try:
                    contour = method_func(gray, image_area)
                    if contour is not None:
                        self.logger.info(f"Document found using {method_name}")
                        return contour
                except Exception as e:
                    self.logger.debug(f"Method {method_name} failed: {e}")
                    continue

            # Final fallback: create a reasonable document boundary (80% of image)
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

    def _find_outermost_paper_boundary(
        self, gray: np.ndarray, image_area: int
    ) -> Optional[np.ndarray]:
        """Most aggressive method to find only the paper boundary, ignoring all internal content"""
        try:
            height, width = gray.shape

            # Strategy 1: Look for the paper as a bright region against dark background
            heavily_blurred = cv2.GaussianBlur(gray, (21, 21), 0)

            # Use Otsu thresholding on the heavily blurred image
            _, binary = cv2.threshold(
                heavily_blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            # Find the largest white region (should be the paper)
            contours, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if contours:
                # Get the largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)

                # Paper should be at least 30% of the image
                if area > image_area * 0.3:
                    # Get the convex hull to smooth out any irregularities
                    hull = cv2.convexHull(largest_contour)

                    # Approximate to rectangle
                    perimeter = cv2.arcLength(hull, True)
                    epsilon = 0.02 * perimeter
                    approx = cv2.approxPolyDP(hull, epsilon, True)

                    # If we don't get exactly 4 points, use minimum area rectangle
                    if len(approx) != 4:
                        rect = cv2.minAreaRect(hull)
                        box = cv2.boxPoints(rect)
                        approx = np.int0(box).reshape(-1, 1, 2)

                    # Make sure it's not the image border
                    if not self._is_image_border(approx, width, height):
                        return approx

            # Strategy 2: Edge-based approach with very specific filtering
            median_filtered = cv2.medianBlur(gray, 5)

            # Use very gentle edge detection
            edges = cv2.Canny(median_filtered, 30, 100, apertureSize=3)

            # Apply morphological operations to connect paper edge segments
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

            # Dilate to ensure paper edges are connected
            dilated = cv2.dilate(closed_edges, kernel, iterations=2)

            # Find contours
            contours, _ = cv2.findContours(
                dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Look for the largest contour that could be paper
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > image_area * 0.2:  # At least 20% of image
                    perimeter = cv2.arcLength(contour, True)
                    epsilon = 0.02 * perimeter
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    if 4 <= len(approx) <= 8:  # Reasonable number of sides
                        if len(approx) > 4:
                            # Convert to rectangle
                            rect = cv2.minAreaRect(contour)
                            box = cv2.boxPoints(rect)
                            approx = np.int0(box).reshape(-1, 1, 2)

                        if not self._is_image_border(approx, width, height):
                            valid_contours.append((approx, area))

            # Return the largest valid contour
            if valid_contours:
                valid_contours.sort(key=lambda x: x[1], reverse=True)  # Sort by area
                return valid_contours[0][0]

            return None

        except Exception as e:
            self.logger.error(f"Error in outermost boundary detection: {e}")
            return None

    def _find_contour_with_preprocessing(
        self, gray: np.ndarray, image_area: int
    ) -> Optional[np.ndarray]:
        """Enhanced method with better preprocessing - prioritizes document edges over internal content"""
        try:
            height, width = gray.shape

            # Method 1: Focus on document edges using dilated edges
            # Apply bilateral filter to reduce noise while keeping edges sharp
            filtered = cv2.bilateralFilter(gray, 9, 75, 75)

            # Use edge detection with lower thresholds to catch document boundaries
            edges = cv2.Canny(filtered, 30, 80, apertureSize=3)

            # Dilate to connect broken edges (document boundaries are often faint)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            dilated = cv2.dilate(edges, kernel, iterations=2)

            # Find contours - use RETR_EXTERNAL to get only outer contours
            contours, _ = cv2.findContours(
                dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            # Look for the largest valid document contour
            for contour in contours:
                perimeter = cv2.arcLength(contour, True)
                epsilon = (
                    0.015 * perimeter
                )  # Reduced epsilon for more accurate approximation
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) == 4:
                    area = cv2.contourArea(approx)

                    # Document should be a significant portion of the image (at least 25%)
                    # but not the entire image border
                    if image_area * 0.25 < area < image_area * 0.85:
                        if not self._is_image_border(approx, width, height):
                            if self._is_roughly_rectangular(approx):
                                # Additional check: ensure it's not too centered (likely internal content)
                                if not self._is_too_centered(approx, width, height):
                                    return approx

            return None

        except Exception as e:
            self.logger.error(f"Error in preprocessing method: {e}")
            return None

    def _find_contour_standard(
        self, gray: np.ndarray, image_area: int
    ) -> Optional[np.ndarray]:
        """Standard edge detection method - prioritizes document boundaries"""
        try:
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Use lower thresholds to catch faint document edges
            edged = cv2.Canny(blurred, 50, 120)

            # Use RETR_EXTERNAL to get only outer contours
            contours, _ = cv2.findContours(
                edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            height, width = gray.shape

            for contour in contours:
                epsilon = 0.015 * cv2.arcLength(
                    contour, True
                )  # More precise approximation
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) == 4:
                    area = cv2.contourArea(approx)
                    # Document should be substantial (at least 30% of image)
                    if image_area * 0.3 < area < image_area * 0.85:
                        if not self._is_image_border(approx, width, height):
                            if not self._is_too_centered(approx, width, height):
                                return approx
        except Exception as e:
            self.logger.error(f"Error in standard method: {e}")
        return None

    def _find_contour_adaptive(
        self, gray: np.ndarray, image_area: int
    ) -> Optional[np.ndarray]:
        """Adaptive threshold method"""
        try:
            # Apply adaptive threshold
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Find contours
            contours, _ = cv2.findContours(
                adaptive, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

            height, width = gray.shape

            for contour in contours:
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) == 4:
                    area = cv2.contourArea(approx)
                    # Filter out contours that are too small or too large (likely the image border)
                    if 10000 < area < image_area * 0.9:
                        # Check if it's not the image border
                        if not self._is_image_border(approx, width, height):
                            return approx
        except Exception as e:
            self.logger.error(f"Error in adaptive method: {e}")
        return None

    def _find_contour_morphology(
        self, gray: np.ndarray, image_area: int
    ) -> Optional[np.ndarray]:
        """Morphological operations method"""
        try:
            # Apply morphological operations
            kernel = np.ones((3, 3), np.uint8)
            morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)

            # Edge detection
            edged = cv2.Canny(morph, 50, 150)

            contours, _ = cv2.findContours(
                edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

            height, width = gray.shape

            for contour in contours:
                epsilon = 0.03 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) == 4:
                    area = cv2.contourArea(approx)
                    # Filter out contours that are too small or too large (likely the image border)
                    if 8000 < area < image_area * 0.9:
                        # Check if it's not the image border
                        if not self._is_image_border(approx, width, height):
                            return approx
        except Exception as e:
            self.logger.error(f"Error in morphology method: {e}")
        return None

    def _find_contour_multi_canny(
        self, gray: np.ndarray, image_area: int
    ) -> Optional[np.ndarray]:
        """Try multiple Canny threshold values"""
        try:
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            height, width = gray.shape

            # Try different threshold combinations
            threshold_pairs = [(50, 150), (30, 100), (100, 200), (75, 175), (40, 120)]

            for low, high in threshold_pairs:
                edged = cv2.Canny(blurred, low, high)

                contours, _ = cv2.findContours(
                    edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
                )
                contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

                for contour in contours:
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    if len(approx) == 4:
                        area = cv2.contourArea(approx)
                        # Filter out contours that are too small or too large (likely the image border)
                        if 5000 < area < image_area * 0.9:
                            # Check if it's not the image border
                            if not self._is_image_border(approx, width, height):
                                return approx
        except Exception as e:
            self.logger.error(f"Error in multi-canny method: {e}")
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

    def _is_image_border(self, contour: np.ndarray, width: int, height: int) -> bool:
        """Check if the contour is just the image border - now more restrictive"""
        # Reshape contour points
        pts = contour.reshape(4, 2)

        # Define tolerance for border detection (pixels from edge)
        tolerance = 100  # Very strict - increased to 100px from edge

        # Check if any points are very close to the image edges
        border_points = 0
        for point in pts:
            x, y = point
            if (
                x < tolerance
                or x > width - tolerance
                or y < tolerance
                or y > height - tolerance
            ):
                border_points += 1

        # If even 1 point is near the border, reject it (very strict)
        return border_points >= 1

    def _is_too_centered(self, contour: np.ndarray, width: int, height: int) -> bool:
        """Check if contour is too centered (likely internal content rather than document edge)"""
        try:
            pts = contour.reshape(4, 2)

            # Calculate bounding rectangle
            x_coords = pts[:, 0]
            y_coords = pts[:, 1]

            min_x, max_x = np.min(x_coords), np.max(x_coords)
            min_y, max_y = np.min(y_coords), np.max(y_coords)

            # Calculate margins from image edges
            left_margin = min_x
            right_margin = width - max_x
            top_margin = min_y
            bottom_margin = height - max_y

            # If all margins are substantial (>10% of image dimension), it's likely internal content
            margin_threshold_x = width * 0.1
            margin_threshold_y = height * 0.1

            large_margins = (
                left_margin > margin_threshold_x
                and right_margin > margin_threshold_x
                and top_margin > margin_threshold_y
                and bottom_margin > margin_threshold_y
            )

            return large_margins

        except:
            return False

    def _is_roughly_rectangular(self, contour: np.ndarray) -> bool:
        """Check if the contour is roughly rectangular"""
        try:
            # Get the four corners
            pts = contour.reshape(4, 2)

            # Calculate all side lengths
            def distance(p1, p2):
                return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

            # Calculate distances between consecutive points
            sides = []
            for i in range(4):
                side_length = distance(pts[i], pts[(i + 1) % 4])
                sides.append(side_length)

            # Check if opposite sides are roughly equal (within 20% tolerance)
            tolerance = 0.2
            side1, side2, side3, side4 = sides

            # Compare opposite sides
            ratio1 = (
                min(side1, side3) / max(side1, side3) if max(side1, side3) > 0 else 0
            )
            ratio2 = (
                min(side2, side4) / max(side2, side4) if max(side2, side4) > 0 else 0
            )

            # Both ratios should be close to 1 (similar lengths)
            return ratio1 > (1 - tolerance) and ratio2 > (1 - tolerance)

        except:
            return False

    def correct_perspective(
        self, image: np.ndarray, contour: np.ndarray
    ) -> Optional[np.ndarray]:
        """
        Correct perspective of the document using the detected contour.
        Uses the full document size without artificial limitations.

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

            # Use the full document size - no artificial limitations
            # This preserves the original document proportions and ArUco marker sizes
            self.logger.info(f"Document size: {max_width}x{max_height}")

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
