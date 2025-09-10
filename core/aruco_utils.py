"""
ArUco marker utilities for KrathongScanner.
"""

from typing import List, Optional, Tuple

import cv2
import numpy as np

from utils.config import Config


class ArucoUtils:
    """Utility functions for ArUco marker operations."""

    def __init__(self):
        """Initialize ArUco utilities."""
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.marker_size = Config.MARKER_SIZE
        self.max_marker_id = 49  # 4x4_50 dictionary has IDs 0-49

    def generate_marker(self, marker_id: int, size: Optional[int] = None) -> np.ndarray:
        """Generate a single ArUco marker."""
        if size is None:
            size = self.marker_size

        if not (0 <= marker_id <= self.max_marker_id):
            raise ValueError(
                f"Marker ID {marker_id} is out of range (0-{self.max_marker_id})"
            )

        return cv2.aruco.generateImageMarker(self.aruco_dict, marker_id, size)

    def generate_markers(
        self, marker_ids: List[int], size: Optional[int] = None
    ) -> List[np.ndarray]:
        """Generate multiple ArUco markers."""
        if size is None:
            size = self.marker_size

        markers = []
        for marker_id in marker_ids:
            if not (0 <= marker_id <= self.max_marker_id):
                raise ValueError(
                    f"Marker ID {marker_id} is out of range (0-{self.max_marker_id})"
                )
            markers.append(self.generate_marker(marker_id, size))

        return markers

    def add_marker_border(
        self, marker: np.ndarray, border_size: int = 20, border_color: int = 255
    ) -> np.ndarray:
        """Add border to marker image."""
        return cv2.copyMakeBorder(
            marker,
            border_size,
            border_size,
            border_size,
            border_size,
            cv2.BORDER_CONSTANT,
            value=border_color,
        )

    def add_marker_label(
        self,
        marker: np.ndarray,
        marker_id: int,
        font_scale: float = 0.5,
        color: Tuple[int, int, int] = (0, 0, 0),
    ) -> np.ndarray:
        """Add ID label to marker image."""
        # Add border first
        bordered = self.add_marker_border(marker)

        # Add text
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = f"ID: {marker_id}"
        text_size = cv2.getTextSize(text, font, font_scale, 1)[0]

        # Position text at top-left corner
        text_x = 5
        text_y = 15

        cv2.putText(bordered, text, (text_x, text_y), font, font_scale, color, 1)

        return bordered

    def detect_markers(self, image: np.ndarray) -> Tuple[List[int], List[np.ndarray]]:
        """Detect ArUco markers in image."""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Detect markers
        corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict)

        if ids is not None:
            return ids.flatten().tolist(), corners
        else:
            return [], []

    def draw_marker_corners(
        self, image: np.ndarray, corners: List[np.ndarray], ids: List[int]
    ) -> np.ndarray:
        """Draw detected marker corners on image."""
        result = image.copy()
        cv2.aruco.drawDetectedMarkers(result, corners, ids)
        return result

    def get_marker_center(self, corners: np.ndarray) -> Tuple[int, int]:
        """Get center point of a marker from its corners."""
        # corners is a 4x2 array of corner points
        center_x = int(np.mean(corners[:, 0]))
        center_y = int(np.mean(corners[:, 1]))
        return center_x, center_y

    def get_marker_orientation(self, corners: np.ndarray) -> float:
        """Get orientation angle of a marker from its corners."""
        # Calculate orientation from top-left to top-right corner
        top_left = corners[0]
        top_right = corners[1]

        dx = top_right[0] - top_left[0]
        dy = top_right[1] - top_left[1]

        angle = np.arctan2(dy, dx) * 180 / np.pi
        return angle

    def validate_marker_ids(self, marker_ids: List[int]) -> dict:
        """Validate marker IDs for a template."""
        validation_result = {"is_valid": True, "errors": [], "warnings": []}

        # Check count
        if len(marker_ids) != Config.MARKER_COUNT_PER_TEMPLATE:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"Template must have exactly {Config.MARKER_COUNT_PER_TEMPLATE} marker IDs"
            )

        # Check range
        for marker_id in marker_ids:
            if not (0 <= marker_id <= self.max_marker_id):
                validation_result["is_valid"] = False
                validation_result["errors"].append(
                    f"Marker ID {marker_id} is out of range (0-{self.max_marker_id})"
                )

        # Check duplicates
        if len(marker_ids) != len(set(marker_ids)):
            validation_result["is_valid"] = False
            validation_result["errors"].append("Duplicate marker IDs found")

        return validation_result

    def get_available_marker_ids(
        self, used_ids: List[int], count: int = 4
    ) -> List[int]:
        """Get available marker IDs from unused ones."""
        available_ids = []

        for marker_id in range(self.max_marker_id + 1):
            if marker_id not in used_ids:
                available_ids.append(marker_id)
                if len(available_ids) >= count:
                    break

        return available_ids

    def create_marker_sheet(
        self,
        marker_ids: List[int],
        markers_per_row: int = 4,
        marker_size: int = 200,
        spacing: int = 50,
    ) -> np.ndarray:
        """Create a sheet with multiple markers for printing."""
        if not marker_ids:
            return np.array([])

        # Calculate sheet dimensions
        rows = (len(marker_ids) + markers_per_row - 1) // markers_per_row
        cols = min(len(marker_ids), markers_per_row)

        sheet_width = cols * marker_size + (cols - 1) * spacing
        sheet_height = rows * marker_size + (rows - 1) * spacing

        # Create white sheet
        sheet = np.ones((sheet_height, sheet_width), dtype=np.uint8) * 255

        # Place markers
        for i, marker_id in enumerate(marker_ids):
            row = i // markers_per_row
            col = i % markers_per_row

            x = col * (marker_size + spacing)
            y = row * (marker_size + spacing)

            marker = self.generate_marker(marker_id, marker_size)
            sheet[y : y + marker_size, x : x + marker_size] = marker

        return sheet
