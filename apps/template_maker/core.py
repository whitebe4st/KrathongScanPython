"""
Core template creation functionality for Krathong templates.
"""

from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np


class KrathongTemplateMaker:
    """Core template creation logic."""

    def __init__(self):
        """Initialize the template maker."""
        # Template specifications
        self.template_width = 1270
        self.template_height = 720
        self.marker_size = 100
        self.drawing_area_width = 779
        self.drawing_area_height = 457

        # Marker positions (top-left corners)
        self.marker_positions = [
            (50, 50),  # Top-left
            (1120, 50),  # Top-right
            (50, 570),  # Bottom-left
            (1120, 570),  # Bottom-right
        ]

        # Drawing area bounds (centered)
        self.drawing_x = (self.template_width - self.drawing_area_width) // 2
        self.drawing_y = (self.template_height - self.drawing_area_height) // 2
        self.drawing_bounds = (
            self.drawing_x,
            self.drawing_y,
            self.drawing_x + self.drawing_area_width,
            self.drawing_y + self.drawing_area_height,
        )

    def create_template_image(
        self,
        marker_ids: List[int],
        image_path: Optional[str] = None,
        mask_path: Optional[str] = None,
        image_scale: float = 0.8,
        image_offset_x: int = 0,
        image_offset_y: int = 0,
    ) -> np.ndarray:
        """Create a complete template image with ArUco markers and optional krathong image."""

        # Create base template (white background)
        template = (
            np.ones((self.template_height, self.template_width, 3), dtype=np.uint8)
            * 255
        )

        # Add ArUco markers
        self._add_aruco_markers(template, marker_ids)

        # Add krathong image if provided
        if image_path:
            self._place_krathong_image(
                template,
                image_path,
                mask_path,
                image_scale,
                image_offset_x,
                image_offset_y,
            )

        return template

    def _add_aruco_markers(self, template: np.ndarray, marker_ids: List[int]):
        """Add ArUco markers to the template."""
        import cv2.aruco as aruco

        # Get ArUco dictionary
        aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)

        for i, marker_id in enumerate(marker_ids):
            # Generate marker
            marker_image = aruco.drawMarker(aruco_dict, marker_id, self.marker_size)

            # Convert to 3-channel
            marker_bgr = cv2.cvtColor(marker_image, cv2.COLOR_GRAY2BGR)

            # Get position
            x, y = self.marker_positions[i]

            # Place marker on template
            template[y : y + self.marker_size, x : x + self.marker_size] = marker_bgr

    def _place_krathong_image(
        self,
        template: np.ndarray,
        image_path: str,
        mask_path: Optional[str] = None,
        scale: float = 0.8,
        offset_x: int = 0,
        offset_y: int = 0,
    ):
        """Place krathong image in the drawing area."""

        # Load image
        krathong_image = cv2.imread(image_path)
        if krathong_image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Load mask if provided
        mask = None
        if mask_path and Path(mask_path).exists():
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

        # Resize image to fit drawing area with scale
        target_width = int(self.drawing_area_width * scale)
        target_height = int(self.drawing_area_height * scale)

        # Maintain aspect ratio
        h, w = krathong_image.shape[:2]
        aspect_ratio = w / h

        if target_width / target_height > aspect_ratio:
            # Height is limiting factor
            new_height = target_height
            new_width = int(new_height * aspect_ratio)
        else:
            # Width is limiting factor
            new_width = target_width
            new_height = int(new_width / aspect_ratio)

        # Resize image
        resized_image = cv2.resize(krathong_image, (new_width, new_height))

        # Resize mask if provided
        resized_mask = None
        if mask is not None:
            resized_mask = cv2.resize(mask, (new_width, new_height))

        # Calculate placement position (centered in drawing area + offset)
        center_x = self.drawing_x + self.drawing_area_width // 2
        center_y = self.drawing_y + self.drawing_area_height // 2

        start_x = center_x - new_width // 2 + offset_x
        start_y = center_y - new_height // 2 + offset_y

        # Ensure image stays within drawing bounds
        start_x = max(
            self.drawing_x,
            min(start_x, self.drawing_x + self.drawing_area_width - new_width),
        )
        start_y = max(
            self.drawing_y,
            min(start_y, self.drawing_y + self.drawing_area_height - new_height),
        )

        end_x = start_x + new_width
        end_y = start_y + new_height

        # Place image on template
        if resized_mask is not None:
            # Use mask for alpha blending
            mask_norm = resized_mask.astype(float) / 255.0
            mask_norm = np.stack([mask_norm] * 3, axis=-1)

            # Alpha blend
            template[start_y:end_y, start_x:end_x] = (
                template[start_y:end_y, start_x:end_x] * (1 - mask_norm)
                + resized_image * mask_norm
            ).astype(np.uint8)
        else:
            # Direct placement
            template[start_y:end_y, start_x:end_x] = resized_image

    def remove_white_background(
        self, image: np.ndarray, threshold: int = 240
    ) -> np.ndarray:
        """Remove white background from image."""

        # Convert to HSV for better white detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Create mask for white pixels
        # White pixels have low saturation and high value
        lower_white = np.array([0, 0, threshold])
        upper_white = np.array([180, 30, 255])
        white_mask = cv2.inRange(hsv, lower_white, upper_white)

        # Invert mask to get non-white pixels
        object_mask = cv2.bitwise_not(white_mask)

        # Apply morphological operations to clean up mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        object_mask = cv2.morphologyEx(object_mask, cv2.MORPH_CLOSE, kernel)
        object_mask = cv2.morphologyEx(object_mask, cv2.MORPH_OPEN, kernel)

        # Create result image with transparent background
        result = image.copy()

        # Set white pixels to transparent (or keep original for now)
        result[white_mask > 0] = [255, 255, 255]

        return result

    def create_mask_from_image(self, image: np.ndarray) -> np.ndarray:
        """Create a mask from the processed image."""

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Threshold to create binary mask
        _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

        # Clean up mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        return mask

    def get_template_info(self) -> dict:
        """Get template specifications."""
        return {
            "template_size": (self.template_width, self.template_height),
            "drawing_area_size": (self.drawing_area_width, self.drawing_area_height),
            "drawing_area_position": (self.drawing_x, self.drawing_y),
            "marker_size": self.marker_size,
            "marker_positions": self.marker_positions,
            "aruco_dictionary": "DICT_4X4_50",
            "marker_id_range": (0, 49),
        }
