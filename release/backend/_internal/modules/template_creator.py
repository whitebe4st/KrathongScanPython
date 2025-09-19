"""
Template Creator Module

Handles template creation with ArUco markers, krathong image placement,
and template saving with metadata. Extracted and modularized from
core/template_maker.py and template_maker_gui.py.

Key Features:
- Template creation with ArUco markers
- Krathong image placement and scaling
- Template and mask saving
- Metadata generation and embedding
- Output directory management

Author: KrathongScanner Team
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


class TemplateFormat(Enum):
    """Template output formats."""

    PNG = "png"
    JPG = "jpg"
    TIFF = "tiff"


@dataclass
class TemplateSettings:
    """Template creation settings."""

    template_name: str
    marker_ids: List[int]
    scale: float = 0.8
    offset_x: int = 0
    offset_y: int = 0
    output_dir: str = "data/templates"
    save_mask: bool = True
    embed_metadata: bool = True


@dataclass
class TemplateMetadata:
    """Template metadata structure."""

    template_name: str
    aruco_ids: List[int]
    template_file: str
    mask_file: Optional[str]
    template_width: int
    template_height: int
    created_at: str
    marker_positions: Dict[str, int]
    dictionary_type: str
    image_settings: Dict[str, Any]


class TemplateCreator:
    """
    Template creation system with ArUco markers and krathong placement.

    Creates templates with proper marker positioning, krathong image placement,
    and handles saving with metadata.
    """

    def __init__(self, template_width: int = 1123, template_height: int = 794):
        """Initialize the template creator."""
        self.logger = logging.getLogger(__name__)

        # Template dimensions (A4 at 150 DPI)
        self.template_width = template_width
        self.template_height = template_height

        # Drawing area (inside the markers)
        self.drawing_width = 779
        self.drawing_height = 457
        self.drawing_offset_x = 172
        self.drawing_offset_y = 169

        # ArUco marker settings
        self.marker_size = 100
        self.outline_thickness = 3
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

        self.logger.info("TemplateCreator initialized")

    def _get_drawing_area(self) -> Tuple[int, int, int, int]:
        """
        Get the drawing area coordinates.

        Returns:
            Tuple of (x1, y1, x2, y2) coordinates
        """
        return (
            self.drawing_offset_x,
            self.drawing_offset_y,
            self.drawing_offset_x + self.drawing_width,
            self.drawing_offset_y + self.drawing_height,
        )

    def create_template(
        self,
        settings: TemplateSettings,
        krathong_image: Optional[np.ndarray] = None,
        mask_image: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, TemplateMetadata]:
        """
        Create a complete template with ArUco markers and krathong image.

        Args:
            settings: Template creation settings
            krathong_image: Optional krathong image to place in template
            mask_image: Optional mask image for saving

        Returns:
            Tuple of (template_image, metadata)
        """
        try:
            # Validate marker IDs
            if len(settings.marker_ids) != 4:
                raise ValueError(
                    "Exactly 4 marker IDs required [top_left, top_right, bottom_left, bottom_right]"
                )

            # Create template image
            template_image = self._create_template_image(
                marker_ids=settings.marker_ids,
                krathong_image=krathong_image,
                scale=settings.scale,
                offset_x=settings.offset_x,
                offset_y=settings.offset_y,
            )

            # Save template and mask
            output_paths = self._save_template_files(
                template_image=template_image, mask_image=mask_image, settings=settings
            )

            # Create metadata
            metadata = self._create_metadata(settings, output_paths)

            # Save metadata
            if settings.embed_metadata:
                self._save_metadata(metadata, settings.output_dir)

            self.logger.info(f"Template created successfully: {settings.template_name}")
            return template_image, metadata

        except Exception as e:
            self.logger.error(f"Template creation failed: {e}")
            raise

    def _create_template_image(
        self,
        marker_ids: List[int],
        krathong_image: Optional[np.ndarray] = None,
        scale: float = 0.8,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> np.ndarray:
        """Create the template image with markers and krathong."""
        # Create white template background (BGR format)
        template = (
            np.ones((self.template_height, self.template_width, 3), dtype=np.uint8)
            * 255
        )

        # Generate and place ArUco markers
        markers = []
        for marker_id in marker_ids:
            marker = cv2.aruco.generateImageMarker(
                self.aruco_dict, marker_id, self.marker_size
            )
            markers.append(marker)

        # Define marker positions (outside the drawing area box)
        marker_positions = [
            (
                self.drawing_offset_x - self.marker_size,
                self.drawing_offset_y - self.marker_size,
            ),  # Top-left
            (
                self.drawing_offset_x + self.drawing_width,
                self.drawing_offset_y - self.marker_size,
            ),  # Top-right
            (
                self.drawing_offset_x - self.marker_size,
                self.drawing_offset_y + self.drawing_height,
            ),  # Bottom-left
            (
                self.drawing_offset_x + self.drawing_width,
                self.drawing_offset_y + self.drawing_height,
            ),  # Bottom-right
        ]

        # Place markers on template
        for marker, (x, y) in zip(markers, marker_positions):
            # Convert grayscale marker to BGR if needed
            if len(marker.shape) == 2:
                marker_bgr = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)
            else:
                marker_bgr = marker

            template[y : y + self.marker_size, x : x + self.marker_size] = marker_bgr

        # Draw black outlined box for drawing area
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

        if new_width <= 0 or new_height <= 0:
            self.logger.warning("Invalid krathong image dimensions after scaling")
            return

        # Auto-scale if image is too large (more than 2x the drawing area)
        if new_width > self.drawing_width * 2 or new_height > self.drawing_height * 2:
            scale_x = self.drawing_width / new_width
            scale_y = self.drawing_height / new_height
            fit_scale = min(scale_x, scale_y) * 0.9  # 90% to leave margin

            new_width = int(new_width * fit_scale)
            new_height = int(new_height * fit_scale)
            self.logger.debug(
                f"Auto-scaled krathong image to fit: {new_width}x{new_height}"
            )

        # Resize the image
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

        # Place the image on template
        if (
            start_x >= 0
            and start_y >= 0
            and start_x + new_width <= self.template_width
            and start_y + new_height <= self.template_height
        ):
            if len(resized_krathong.shape) == 3:
                if resized_krathong.shape[2] == 4:
                    # RGBA image - handle transparency
                    alpha = resized_krathong[:, :, 3] / 255.0
                    alpha = np.stack([alpha, alpha, alpha], axis=2)

                    # Convert RGBA to BGR for blending
                    krathong_bgr = cv2.cvtColor(resized_krathong, cv2.COLOR_RGBA2BGR)

                    # Blend with template background
                    template_roi = template[
                        start_y : start_y + new_height, start_x : start_x + new_width
                    ]
                    blended = (
                        krathong_bgr * alpha + template_roi * (1 - alpha)
                    ).astype(np.uint8)
                    template[
                        start_y : start_y + new_height, start_x : start_x + new_width
                    ] = blended
                else:
                    # BGR image - place directly
                    template[
                        start_y : start_y + new_height, start_x : start_x + new_width
                    ] = resized_krathong
            else:
                # Grayscale image - convert to BGR and place
                krathong_bgr = cv2.cvtColor(resized_krathong, cv2.COLOR_GRAY2BGR)
                template[
                    start_y : start_y + new_height, start_x : start_x + new_width
                ] = krathong_bgr

    def _save_template_files(
        self,
        template_image: np.ndarray,
        mask_image: Optional[np.ndarray],
        settings: TemplateSettings,
    ) -> Dict[str, Path]:
        """Save template and mask files."""
        # Create output directory
        output_dir = Path(settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_paths = {}

        # Save template image
        template_filename = f"{settings.template_name}.png"
        template_path = output_dir / template_filename

        success = cv2.imwrite(str(template_path), template_image)
        if not success:
            raise RuntimeError(f"Failed to save template image: {template_path}")

        output_paths["template"] = template_path
        self.logger.info(f"Template saved: {template_path}")

        # Save mask if provided and requested
        if mask_image is not None and settings.save_mask:
            mask_filename = f"{settings.template_name}_mask.png"
            mask_path = output_dir / mask_filename

            success = cv2.imwrite(str(mask_path), mask_image)
            if success:
                output_paths["mask"] = mask_path
                self.logger.info(f"Mask saved: {mask_path}")
            else:
                self.logger.warning(f"Failed to save mask: {mask_path}")

        return output_paths

    def _create_metadata(
        self, settings: TemplateSettings, output_paths: Dict[str, Path]
    ) -> TemplateMetadata:
        """Create template metadata."""
        return TemplateMetadata(
            template_name=settings.template_name,
            aruco_ids=settings.marker_ids,
            template_file=str(output_paths["template"]),
            mask_file=str(output_paths["mask"]) if "mask" in output_paths else None,
            template_width=self.template_width,
            template_height=self.template_height,
            created_at=datetime.now().isoformat(),
            marker_positions={
                "top_left": settings.marker_ids[0],
                "top_right": settings.marker_ids[1],
                "bottom_left": settings.marker_ids[2],
                "bottom_right": settings.marker_ids[3],
            },
            dictionary_type="4X4_50",
            image_settings={
                "scale": settings.scale,
                "offset_x": settings.offset_x,
                "offset_y": settings.offset_y,
            },
        )

    def _save_metadata(self, metadata: TemplateMetadata, output_dir: str):
        """Save template metadata to JSON file."""
        try:
            output_path = Path(output_dir) / f"{metadata.template_name}_metadata.json"

            # Convert dataclass to dict
            metadata_dict = {
                "template_name": metadata.template_name,
                "aruco_ids": metadata.aruco_ids,
                "template_file": metadata.template_file,
                "mask_file": metadata.mask_file,
                "template_width": metadata.template_width,
                "template_height": metadata.template_height,
                "created_at": metadata.created_at,
                "marker_positions": metadata.marker_positions,
                "dictionary_type": metadata.dictionary_type,
                "image_settings": metadata.image_settings,
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(metadata_dict, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Metadata saved: {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to save metadata: {e}")

    def load_metadata(self, metadata_path: str) -> Optional[TemplateMetadata]:
        """Load template metadata from JSON file."""
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return TemplateMetadata(
                template_name=data["template_name"],
                aruco_ids=data["aruco_ids"],
                template_file=data["template_file"],
                mask_file=data.get("mask_file"),
                template_width=data["template_width"],
                template_height=data["template_height"],
                created_at=data["created_at"],
                marker_positions=data["marker_positions"],
                dictionary_type=data["dictionary_type"],
                image_settings=data["image_settings"],
            )

        except Exception as e:
            self.logger.error(f"Failed to load metadata: {e}")
            return None

    def validate_template(self, template_image: np.ndarray) -> Dict[str, Any]:
        """Validate template image and return analysis."""
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "info": {},
            }

            # Check dimensions
            h, w = template_image.shape[:2]
            validation_result["info"]["dimensions"] = (w, h)

            if w != self.template_width or h != self.template_height:
                validation_result["warnings"].append(
                    f"Template dimensions ({w}x{h}) don't match expected ({self.template_width}x{self.template_height})"
                )

            # Check for ArUco markers
            gray = (
                cv2.cvtColor(template_image, cv2.COLOR_BGR2GRAY)
                if len(template_image.shape) == 3
                else template_image
            )
            corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict)

            if ids is not None:
                validation_result["info"]["detected_markers"] = len(ids)
                validation_result["info"]["marker_ids"] = ids.flatten().tolist()

                if len(ids) != 4:
                    validation_result["warnings"].append(
                        f"Expected 4 markers, found {len(ids)}"
                    )
            else:
                validation_result["errors"].append("No ArUco markers detected")
                validation_result["valid"] = False

            # Check drawing area
            drawing_area = template_image[
                self.drawing_offset_y : self.drawing_offset_y + self.drawing_height,
                self.drawing_offset_x : self.drawing_offset_x + self.drawing_width,
            ]

            if drawing_area.size > 0:
                validation_result["info"]["drawing_area_size"] = drawing_area.shape
            else:
                validation_result["errors"].append("Invalid drawing area")
                validation_result["valid"] = False

            return validation_result

        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation failed: {e}"],
                "warnings": [],
                "info": {},
            }

    def get_template_info(self) -> Dict[str, Any]:
        """Get template creator configuration information."""
        return {
            "template_dimensions": {
                "width": self.template_width,
                "height": self.template_height,
            },
            "drawing_area": {
                "width": self.drawing_width,
                "height": self.drawing_height,
                "offset_x": self.drawing_offset_x,
                "offset_y": self.drawing_offset_y,
            },
            "marker_settings": {
                "size": self.marker_size,
                "outline_thickness": self.outline_thickness,
                "dictionary": "DICT_4X4_50",
            },
            "supported_formats": [fmt.value for fmt in TemplateFormat],
        }

    def set_template_dimensions(self, width: int, height: int):
        """Set custom template dimensions."""
        self.template_width = width
        self.template_height = height
        self.logger.info(f"Template dimensions updated: {width}x{height}")

    def set_drawing_area(self, width: int, height: int, offset_x: int, offset_y: int):
        """Set custom drawing area."""
        self.drawing_width = width
        self.drawing_height = height
        self.drawing_offset_x = offset_x
        self.drawing_offset_y = offset_y
        self.logger.info(
            f"Drawing area updated: {width}x{height} at ({offset_x}, {offset_y})"
        )


def create_template_from_dict(
    config: Dict[str, Any],
    krathong_image: Optional[np.ndarray] = None,
    mask_image: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, TemplateMetadata]:
    """
    Convenience function to create template from configuration dictionary.

    Args:
        config: Configuration dictionary with template settings
        krathong_image: Optional krathong image
        mask_image: Optional mask image

    Returns:
        Tuple of (template_image, metadata)
    """
    creator = TemplateCreator()

    settings = TemplateSettings(
        template_name=config["template_name"],
        marker_ids=config["marker_ids"],
        scale=config.get("scale", 0.8),
        offset_x=config.get("offset_x", 0),
        offset_y=config.get("offset_y", 0),
        output_dir=config.get("output_dir", "data/templates"),
        save_mask=config.get("save_mask", True),
        embed_metadata=config.get("embed_metadata", True),
    )

    return creator.create_template(settings, krathong_image, mask_image)


if __name__ == "__main__":
    # Test the template creator
    import tkinter as tk
    from tkinter import filedialog

    # Test template creation
    creator = TemplateCreator()

    # Create test settings
    settings = TemplateSettings(
        template_name="test_template",
        marker_ids=[0, 1, 2, 3],
        scale=0.8,
        offset_x=0,
        offset_y=0,
        output_dir="test_output",
    )

    print("Creating test template...")
    template_image, metadata = creator.create_template(settings)

    print(f"Template created: {template_image.shape}")
    print(f"Metadata: {metadata.template_name}")

    # Validate template
    validation = creator.validate_template(template_image)
    print(f"Validation: {validation}")

    print("Template creator test completed!")
