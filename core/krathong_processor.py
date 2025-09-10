"""
Krathong processor for image processing and template application.
"""

from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

from core.aruco_utils import ArucoUtils
from database.models import TemplateData
from utils.image_utils import ImageUtils


class KrathongProcessor:
    """Processes krathong images using templates."""

    def __init__(self):
        """Initialize krathong processor."""
        self.aruco_utils = ArucoUtils()
        self.image_utils = ImageUtils()

    def process_image(
        self, image: np.ndarray, template_data: TemplateData
    ) -> Optional[np.ndarray]:
        """
        Process image using the specified template.

        Args:
            image: Input image to process
            template_data: Template data containing marker IDs and paths

        Returns:
            Processed image or None if processing failed
        """
        try:
            # Load template image
            template_image = self.image_utils.load_image(Path(template_data.image_path))
            if template_image is None:
                print(f"Failed to load template image: {template_data.image_path}")
                return None

            # Load mask image
            mask_image = self.image_utils.load_image(Path(template_data.mask_path))
            if mask_image is None:
                print(f"Failed to load mask image: {template_data.mask_path}")
                return None

            # Detect markers in input image
            detected_ids, corners = self.aruco_utils.detect_markers(image)

            if not detected_ids:
                print("No markers detected in input image")
                return None

            # Find template markers in detected markers
            template_marker_ids = template_data.marker_ids
            template_corners = []

            for i, marker_id in enumerate(template_marker_ids):
                if marker_id in detected_ids:
                    marker_index = detected_ids.index(marker_id)
                    template_corners.append(
                        corners[marker_index][0]
                    )  # Get first (and only) marker
                else:
                    print(f"Template marker {marker_id} not found in detected markers")
                    return None

            # Calculate homography
            homography = self._calculate_homography(template_corners, template_data)
            if homography is None:
                print("Failed to calculate homography")
                return None

            # Apply homography to transform image
            processed_image = self._apply_homography(image, homography, template_data)

            return processed_image

        except Exception as e:
            print(f"Error processing image: {e}")
            return None

    def _calculate_homography(
        self, detected_corners: List[np.ndarray], template_data: TemplateData
    ) -> Optional[np.ndarray]:
        """Calculate homography matrix from detected markers."""
        try:
            # Define template marker positions (corners of drawing area)
            template_width = template_data.template_width
            template_height = template_data.template_height
            drawing_width = 779  # From config
            drawing_height = 457  # From config

            # Calculate marker positions in template
            marker_size = 100  # From config
            drawing_offset_x = (template_width - drawing_width) // 2
            drawing_offset_y = (template_height - drawing_height) // 2

            template_points = np.array(
                [
                    [
                        drawing_offset_x - marker_size,
                        drawing_offset_y - marker_size,
                    ],  # Top-left
                    [
                        drawing_offset_x + drawing_width,
                        drawing_offset_y - marker_size,
                    ],  # Top-right
                    [
                        drawing_offset_x - marker_size,
                        drawing_offset_y + drawing_height,
                    ],  # Bottom-left
                    [
                        drawing_offset_x + drawing_width,
                        drawing_offset_y + drawing_height,
                    ],  # Bottom-right
                ],
                dtype=np.float32,
            )

            # Extract detected marker centers
            detected_points = []
            for corners in detected_corners:
                center = self.aruco_utils.get_marker_center(corners)
                detected_points.append(center)

            detected_points = np.array(detected_points, dtype=np.float32)

            # Calculate homography
            homography, _ = cv2.findHomography(detected_points, template_points)

            return homography

        except Exception as e:
            print(f"Error calculating homography: {e}")
            return None

    def _apply_homography(
        self, image: np.ndarray, homography: np.ndarray, template_data: TemplateData
    ) -> np.ndarray:
        """Apply homography transformation to image."""
        try:
            # Get template dimensions
            template_width = template_data.template_width
            template_height = template_data.template_height

            # Apply homography
            warped_image = cv2.warpPerspective(
                image, homography, (template_width, template_height)
            )

            # Load and apply mask
            mask_path = Path(template_data.mask_path)
            if mask_path.exists():
                mask = self.image_utils.load_image(mask_path)
                if mask is not None:
                    # Convert mask to grayscale if needed
                    if len(mask.shape) == 3:
                        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

                    # Apply mask
                    warped_image = cv2.bitwise_and(
                        warped_image, warped_image, mask=mask
                    )

            return warped_image

        except Exception as e:
            print(f"Error applying homography: {e}")
            return image

    def detect_krathong_region(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Detect krathong region in image using contour detection."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Find contours
            contours, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if not contours:
                return None

            # Find largest contour
            largest_contour = max(contours, key=cv2.contourArea)

            # Create mask
            mask = np.zeros_like(gray)
            cv2.drawContours(mask, [largest_contour], -1, 255, thickness=cv2.FILLED)

            return mask

        except Exception as e:
            print(f"Error detecting krathong region: {e}")
            return None

    def enhance_image(self, image: np.ndarray) -> np.ndarray:
        """Enhance image quality."""
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

            # Split channels
            l, a, b = cv2.split(lab)

            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)

            # Merge channels
            enhanced_lab = cv2.merge([l, a, b])

            # Convert back to BGR
            enhanced_image = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

            return enhanced_image

        except Exception as e:
            print(f"Error enhancing image: {e}")
            return image
