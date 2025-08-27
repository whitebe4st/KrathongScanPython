"""
Simple ArUco Marker Generator.

This class generates ArUco markers with minimal complexity.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import numpy as np


class ArUcoMarkerGenerator:
    """
    Simple ArUco marker generator for basic needs.
    """

    def __init__(
        self,
        dict_type: str = "4X4_50",
        marker_size: int = 200,
        output_dir: str = "data/aruco_markers",
    ):
        """
        Initialize the simple ArUco marker generator.

        Args:
            dict_type: ArUco dictionary type (default: "4X4_50")
            marker_size: Size of the generated marker in pixels (default: 200)
            output_dir: Directory to save generated markers
        """
        self.logger = self._setup_logger()
        self.dict_type = dict_type
        self.marker_size = marker_size
        self.output_dir = Path(output_dir)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ArUco dictionary
        self.aruco_dict = self._get_aruco_dict()

        self.logger.info(
            f"Simple ArUco Generator initialized with {dict_type} dictionary"
        )

    def _setup_logger(self):
        """Simple logger setup."""
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

    def _get_aruco_dict(self) -> cv2.aruco.Dictionary:
        """Get the ArUco dictionary."""
        dict_mapping = {
            "4X4_50": cv2.aruco.DICT_4X4_50,
            "4X4_100": cv2.aruco.DICT_4X4_100,
            "5X5_50": cv2.aruco.DICT_5X5_50,
            "6X6_50": cv2.aruco.DICT_6X6_50,
        }

        if self.dict_type not in dict_mapping:
            self.logger.warning(
                f"Unknown dictionary type: {self.dict_type}. Using 4X4_50"
            )
            self.dict_type = "4X4_50"

        return cv2.aruco.getPredefinedDictionary(dict_mapping[self.dict_type])

    def generate_marker(
        self, marker_id: int, filename: Optional[str] = None, add_border: bool = True
    ) -> np.ndarray:
        """
        Generate a single ArUco marker.

        Args:
            marker_id: ID of the marker to generate
            filename: Optional filename to save the marker
            add_border: Whether to add a white border around the marker

        Returns:
            Generated marker image as numpy array
        """
        try:
            # Check if marker ID is valid
            if marker_id >= self.aruco_dict.bytesList.shape[0]:
                raise ValueError(
                    f"Marker ID {marker_id} is invalid for {self.dict_type} dictionary"
                )

            # Generate the marker
            marker_img = cv2.aruco.generateImageMarker(
                self.aruco_dict, marker_id, self.marker_size
            )

            # Convert to BGR for OpenCV
            marker_img = cv2.cvtColor(marker_img, cv2.COLOR_GRAY2BGR)

            # Add border if requested
            if add_border:
                border_size = self.marker_size // 10
                marker_img = cv2.copyMakeBorder(
                    marker_img,
                    border_size,
                    border_size,
                    border_size,
                    border_size,
                    cv2.BORDER_CONSTANT,
                    value=(255, 255, 255),  # White border
                )

            # Save if filename provided
            if filename:
                filepath = self.output_dir / filename
                cv2.imwrite(str(filepath), marker_img)
                self.logger.info(f"Marker {marker_id} saved to {filepath}")

            return marker_img

        except Exception as e:
            self.logger.error(f"Error generating marker {marker_id}: {e}")
            raise

    def generate_simple_markers(self, count: int = 4) -> Dict[int, np.ndarray]:
        """
        Generate a simple set of markers with IDs 0, 1, 2, 3...

        Args:
            count: Number of markers to generate (default: 4)

        Returns:
            Dictionary mapping marker IDs to generated images
        """
        generated_markers = {}

        for marker_id in range(count):
            try:
                filename = f"marker_{marker_id}.png"
                marker_img = self.generate_marker(marker_id, filename, add_border=True)
                generated_markers[marker_id] = marker_img
                print(f"✓ Generated marker_{marker_id}.png")

            except Exception as e:
                print(f"✗ Failed to generate marker {marker_id}: {e}")
                continue

        print(f"Generated {len(generated_markers)} markers successfully")
        return generated_markers

    def get_dictionary_info(self) -> Dict[str, Any]:
        """Get basic information about the current ArUco dictionary."""
        return {
            "dict_type": self.dict_type,
            "marker_size": self.marker_size,
            "total_markers": self.aruco_dict.bytesList.shape[0],
        }
