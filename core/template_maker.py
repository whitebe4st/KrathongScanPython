"""
Core template maker for creating krathong templates with ArUco markers.
"""

from typing import List, Optional

import cv2
import numpy as np

from utils.config import Config


class KrathongTemplateMaker:
    """Core template maker for creating krathong templates with ArUco markers."""

    def __init__(self):
        """Initialize the template maker."""
        # Template specifications
        self.template_width = Config.TEMPLATE_WIDTH
        self.template_height = Config.TEMPLATE_HEIGHT
        self.drawing_width = Config.DRAWING_AREA_WIDTH
        self.drawing_height = Config.DRAWING_AREA_HEIGHT
        self.drawing_offset_x = (
            self.template_width - self.drawing_width
        ) // 2  # Center the drawing area
        self.drawing_offset_y = (
            self.template_height - self.drawing_height
        ) // 2  # Center the drawing area
        self.marker_size = Config.MARKER_SIZE
        self.outline_thickness = Config.DRAWING_AREA_BORDER

        # ArUco dictionary
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    def create_template_image(
        self,
        marker_ids: List[int],
        krathong_image: Optional[np.ndarray] = None,
        scale: float = 0.8,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> np.ndarray:
        """
        Create a template image with ArUco markers and optional krathong image.

        Args:
            marker_ids: List of 4 ArUco marker IDs [top_left, top_right, bottom_left, bottom_right]
            krathong_image: Optional krathong image to place in the template
            scale: Scale factor for the krathong image (0.1 to 1.5)
            offset_x: X offset for krathong image placement
            offset_y: Y offset for krathong image placement

        Returns:
            Template image as numpy array
        """
        # Create white template (BGR format)
        template = (
            np.ones((self.template_height, self.template_width, 3), dtype=np.uint8)
            * 255
        )

        # Generate ArUco markers
        markers = []
        for marker_id in marker_ids:
            marker = cv2.aruco.generateImageMarker(
                self.aruco_dict, marker_id, self.marker_size
            )
            markers.append(marker)

        # Place markers at the corners of the drawing area box (outside the box)
        marker_positions = [
            (
                self.drawing_offset_x - self.marker_size,
                self.drawing_offset_y - self.marker_size,
            ),  # Top-left corner (outside box)
            (
                self.drawing_offset_x + self.drawing_width,
                self.drawing_offset_y - self.marker_size,
            ),  # Top-right corner (outside box)
            (
                self.drawing_offset_x - self.marker_size,
                self.drawing_offset_y + self.drawing_height,
            ),  # Bottom-left corner (outside box)
            (
                self.drawing_offset_x + self.drawing_width,
                self.drawing_offset_y + self.drawing_height,
            ),  # Bottom-right corner (outside box)
        ]

        # Place markers on template
        for i, (marker, pos) in enumerate(zip(markers, marker_positions)):
            x, y = pos
            # Convert grayscale marker to 3-channel BGR if needed
            if len(marker.shape) == 2:
                marker_3ch = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)
            else:
                marker_3ch = marker
            template[y : y + self.marker_size, x : x + self.marker_size] = marker_3ch

        # Draw black outlined box in the center for drawing area
        cv2.rectangle(
            template,
            (self.drawing_offset_x, self.drawing_offset_y),
            (
                self.drawing_offset_x + self.drawing_width,
                self.drawing_offset_y + self.drawing_height,
            ),
            (0, 0, 0),
            self.outline_thickness,
        )

        # Place krathong image if provided
        if krathong_image is not None:
            self._place_krathong_image(
                template, krathong_image, scale, offset_x, offset_y
            )

        return template

    def _place_krathong_image(
        self,
        template: np.ndarray,
        krathong_image: np.ndarray,
        scale: float,
        offset_x: int,
        offset_y: int,
    ):
        """Place krathong image in the drawing area of the template."""
        # Resize krathong image
        height, width = krathong_image.shape[:2]
        new_width = int(width * scale)
        new_height = int(height * scale)

        if new_width > 0 and new_height > 0:
            # Only auto-scale if the image is way too big (more than 2x the drawing area)
            # This allows the user's scale setting to work for reasonable sizes
            if (
                new_width > self.drawing_width * 2
                or new_height > self.drawing_height * 2
            ):
                # Calculate scale to fit within drawing area
                scale_x = self.drawing_width / new_width
                scale_y = self.drawing_height / new_height
                fit_scale = min(scale_x, scale_y) * 0.9  # 90% to leave some margin

                new_width = int(new_width * fit_scale)
                new_height = int(new_height * fit_scale)
                print(
                    f"Debug: Auto-scaled down to fit (image was too large): {new_width}x{new_height}"
                )
            else:
                print(f"Debug: Using user scale setting: {new_width}x{new_height}")

            resized_krathong = cv2.resize(krathong_image, (new_width, new_height))

            # Calculate placement position (center of drawing area + offsets)
            center_x = self.drawing_offset_x + self.drawing_width // 2
            center_y = self.drawing_offset_y + self.drawing_height // 2

            start_x = center_x - new_width // 2 + offset_x
            start_y = center_y - new_height // 2 + offset_y

            # Ensure the image fits within the drawing area
            start_x = max(
                self.drawing_offset_x,
                min(start_x, self.drawing_offset_x + self.drawing_width - new_width),
            )
            start_y = max(
                self.drawing_offset_y,
                min(start_y, self.drawing_offset_y + self.drawing_height - new_height),
            )

            # Place the image
            if (
                start_x >= 0
                and start_y >= 0
                and start_x + new_width <= self.template_width
                and start_y + new_height <= self.template_height
            ):
                if len(resized_krathong.shape) == 3:
                    # Color image - handle transparency properly
                    if resized_krathong.shape[2] == 4:
                        # RGBA image - blend with template background
                        alpha = resized_krathong[:, :, 3] / 255.0
                        alpha = np.stack([alpha, alpha, alpha], axis=2)

                        # Convert RGBA to BGR for blending
                        krathong_bgr = cv2.cvtColor(
                            resized_krathong, cv2.COLOR_RGBA2BGR
                        )

                        # Blend with template background
                        template_roi = template[
                            start_y : start_y + new_height,
                            start_x : start_x + new_width,
                        ]
                        blended = (
                            krathong_bgr * alpha + template_roi * (1 - alpha)
                        ).astype(np.uint8)
                        template[
                            start_y : start_y + new_height,
                            start_x : start_x + new_width,
                        ] = blended
                    else:
                        # BGR image - place directly
                        template[
                            start_y : start_y + new_height,
                            start_x : start_x + new_width,
                        ] = resized_krathong
                else:
                    # Grayscale image - convert to BGR
                    template[
                        start_y : start_y + new_height, start_x : start_x + new_width
                    ] = cv2.cvtColor(resized_krathong, cv2.COLOR_GRAY2BGR)

    def remove_white_background(self, image: np.ndarray) -> np.ndarray:
        """
        Remove ALL white colors from krathong image.
        Aggressive approach to remove white backgrounds.
        """
        if len(image.shape) == 3:
            # Convert to different color spaces for better white detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            hsv = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            lab = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        # Method 1: HSV-based white detection
        # White has low saturation and high value
        lower_white_hsv = np.array([0, 0, 200])  # Low saturation, high value
        upper_white_hsv = np.array([180, 30, 255])
        mask_hsv = cv2.inRange(hsv, lower_white_hsv, upper_white_hsv)

        # Method 2: LAB-based white detection
        # White has high L (lightness) and neutral a, b
        lower_white_lab = np.array([200, 120, 120])  # High L, neutral a, b
        upper_white_lab = np.array([255, 135, 135])
        mask_lab = cv2.inRange(lab, lower_white_lab, upper_white_lab)

        # Method 3: Grayscale threshold
        _, mask_gray = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)

        # Method 4: RGB-based white detection
        if len(image.shape) == 3:
            # White has high values in all RGB channels
            b, g, r = cv2.split(image)
            mask_b = (b > 200).astype(np.uint8) * 255
            mask_g = (g > 200).astype(np.uint8) * 255
            mask_r = (r > 200).astype(np.uint8) * 255
            mask_rgb = cv2.bitwise_and(cv2.bitwise_and(mask_b, mask_g), mask_r)
        else:
            mask_rgb = np.zeros_like(gray)

        # Combine all masks (OR operation - if any method detects white, remove it)
        combined_mask = cv2.bitwise_or(mask_hsv, mask_lab)
        combined_mask = cv2.bitwise_or(combined_mask, mask_gray)
        if len(image.shape) == 3:
            combined_mask = cv2.bitwise_or(combined_mask, mask_rgb)

        # Invert mask so white areas become transparent
        mask = cv2.bitwise_not(combined_mask)

        # Apply morphological operations to clean up the mask
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Create result with alpha channel
        if len(image.shape) == 3:
            result = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            result[:, :, 3] = mask
        else:
            result = image.copy()
            result[mask == 0] = 255

        return result

    def generate_mask_from_cropped_image(self, cropped_image: np.ndarray) -> np.ndarray:
        """
        Generate a mask from a cropped krathong image using mask_maker.py logic.
        Creates a mask with the exact size of the template drawing area (779x457).

        Args:
            cropped_image: The cropped krathong image (BGR format)

        Returns:
            Binary mask as numpy array (0=background, 255=foreground) with size 779x457
        """
        # Convert to grayscale
        gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)

        # Threshold to create binary mask (inverted - white background becomes 0)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Create mask with template drawing area size (779x457)
        mask = np.zeros((self.drawing_height, self.drawing_width), dtype=np.uint8)

        if contours:
            # Find the largest contour (assumed to be the krathong)
            largest_contour = max(contours, key=cv2.contourArea)

            # Get bounding rectangle of the largest contour
            x, y, w, h = cv2.boundingRect(largest_contour)

            # Calculate center position in the template drawing area
            center_x = self.drawing_width // 2
            center_y = self.drawing_height // 2

            # Calculate the position to place the contour in the center
            # Scale the contour to fit within the drawing area if needed
            scale_factor = (
                min(self.drawing_width / w, self.drawing_height / h) * 0.8
            )  # 80% to leave margin

            if scale_factor < 1.0:
                # Scale down the contour
                scaled_contour = largest_contour * scale_factor
            else:
                scaled_contour = largest_contour

            # Get new bounding rectangle after scaling
            x_new, y_new, w_new, h_new = cv2.boundingRect(
                scaled_contour.astype(np.int32)
            )

            # Center the contour in the drawing area
            offset_x = center_x - (x_new + w_new // 2)
            offset_y = center_y - (y_new + h_new // 2)

            # Translate the contour to the center position
            translated_contour = scaled_contour + [offset_x, offset_y]

            # Draw the translated contour onto the mask
            cv2.drawContours(
                mask,
                [translated_contour.astype(np.int32)],
                -1,
                255,
                thickness=cv2.FILLED,
            )

            # Apply morphological operations to clean up the mask
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        return mask

    def remove_white_background_aggressive(self, image: np.ndarray) -> np.ndarray:
        """
        Remove white backgrounds while preserving important details like outlines.
        Balanced approach that removes backgrounds but keeps krathong details.
        """
        if len(image.shape) == 3:
            # Convert to different color spaces for better white detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            hsv = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            lab = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        # Method 1: HSV-based white detection (balanced)
        # White has low saturation and high value
        lower_white_hsv = np.array([0, 0, 220])  # Higher threshold to preserve details
        upper_white_hsv = np.array([180, 30, 255])  # Lower saturation tolerance
        mask_hsv = cv2.inRange(hsv, lower_white_hsv, upper_white_hsv)

        # Method 2: LAB-based white detection (balanced)
        # White has high L (lightness) and neutral a, b
        lower_white_lab = np.array([220, 120, 120])  # Higher L threshold
        upper_white_lab = np.array([255, 135, 135])  # Narrower a, b range
        mask_lab = cv2.inRange(lab, lower_white_lab, upper_white_lab)

        # Method 3: Grayscale threshold (balanced)
        _, mask_gray = cv2.threshold(
            gray, 230, 255, cv2.THRESH_BINARY
        )  # Higher threshold

        # Method 4: RGB-based white detection (balanced)
        if len(image.shape) == 3:
            # White has high values in all RGB channels
            b, g, r = cv2.split(image)
            mask_b = (b > 220).astype(np.uint8) * 255  # Higher threshold
            mask_g = (g > 220).astype(np.uint8) * 255
            mask_r = (r > 220).astype(np.uint8) * 255
            mask_rgb = cv2.bitwise_and(cv2.bitwise_and(mask_b, mask_g), mask_r)
        else:
            mask_rgb = np.zeros_like(gray)

        # Combine all masks (OR operation - if any method detects white, remove it)
        combined_mask = cv2.bitwise_or(mask_hsv, mask_lab)
        combined_mask = cv2.bitwise_or(combined_mask, mask_gray)
        if len(image.shape) == 3:
            combined_mask = cv2.bitwise_or(combined_mask, mask_rgb)

        # Invert mask so white areas become transparent
        mask = cv2.bitwise_not(combined_mask)

        # Apply morphological operations to clean up the mask
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Create result with alpha channel
        if len(image.shape) == 3:
            result = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            result[:, :, 3] = mask
        else:
            result = image.copy()
            result[mask == 0] = 255

        return result
