#!/usr/bin/env python3
"""
Enhanced Template Maker with Registry Integration

A comprehensive template maker system with ArUco marker placement,
automatic unique ID allocation, and template registry management.

Features:
- Automatic unique ArUco marker ID assignment
- Template registry integration for conflict prevention
- Interactive preview with real-time adjustments
- Professional template creation workflow
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

# Add tools to path for cross-tool imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
from template_registry import get_next_unique_ids, get_registry, register_template

# Import ArUco generator (assuming it exists)
try:
    from src.aruco_generator.generator import SimpleArucoGenerator
except ImportError:
    print("⚠️  ArUco generator not found. Creating placeholder...")

    class SimpleArucoGenerator:
        def __init__(self, *args, **kwargs):
            pass

        def generate_marker(self, marker_id, size):
            # Create a simple placeholder marker
            marker = np.ones((size, size), dtype=np.uint8) * 255
            cv2.putText(
                marker,
                str(marker_id),
                (size // 4, size // 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                size // 100,
                0,
                2,
            )
            return marker


logger = logging.getLogger(__name__)


class EnhancedKrathongTemplateMaker:
    """
    Enhanced template maker with registry integration and automatic ID management.
    """

    def __init__(self, template_width: int = 1280, template_height: int = 720):
        """
        Initialize the enhanced template maker.

        Args:
            template_width: Width of template in pixels
            template_height: Height of template in pixels
        """
        self.template_width = template_width
        self.template_height = template_height

        # Calculate drawing area (inner box for krathong placement)
        self.drawing_width = 779
        self.drawing_height = 457

        # Calculate drawing area position (centered)
        self.drawing_x = (template_width - self.drawing_width) // 2
        self.drawing_y = (template_height - self.drawing_height) // 2

        # ArUco settings
        self.marker_size = 100

        # Initialize ArUco generator
        try:
            self.aruco_generator = SimpleArucoGenerator()
            print("🎯 ArUco generator initialized")
        except Exception as e:
            print(f"⚠️  ArUco generator error: {e}")
            self.aruco_generator = SimpleArucoGenerator()

        # Get registry instance
        self.registry = get_registry()

        print(f"🎯 Enhanced Template Maker initialized")
        print(f"📐 Template size: {template_width}x{template_height}")
        print(f"📦 Drawing area: {self.drawing_width}x{self.drawing_height}")
        print(f"🎯 Marker size: {self.marker_size}x{self.marker_size}")

    def get_auto_assigned_ids(self) -> List[int]:
        """
        Get automatically assigned unique marker IDs.

        Returns:
            List of 4 unique marker IDs
        """
        return get_next_unique_ids()

    def create_template_with_registry(
        self,
        template_name: str,
        client_name: str = "",
        marker_ids: Optional[List[int]] = None,
        image_path: Optional[str] = None,
        image_scale: float = 0.8,
        image_offset_x: int = 0,
        image_offset_y: int = 0,
        output_dir: str = "data/templates",
    ) -> Tuple[bool, str]:
        """
        Create template with automatic registry integration.

        Args:
            template_name: Name for the template
            client_name: Client name for registry
            marker_ids: Marker IDs to use (auto-assigned if None)
            image_path: Path to image to include
            image_scale: Scale factor for image
            image_offset_x: X offset for image placement
            image_offset_y: Y offset for image placement
            output_dir: Directory to save template

        Returns:
            Tuple of (success, message)
        """
        try:
            # Auto-assign marker IDs if not provided
            if marker_ids is None:
                marker_ids = self.get_auto_assigned_ids()
                print(f"🎯 Auto-assigned marker IDs: {marker_ids}")

            # Check if IDs are available (double-check)
            if not self.registry.is_id_combination_available(marker_ids):
                return False, f"Marker IDs {marker_ids} are already in use"

            # Create template
            template_img = self.create_template_image(
                marker_ids=marker_ids,
                image_path=image_path,
                image_scale=image_scale,
                image_offset_x=image_offset_x,
                image_offset_y=image_offset_y,
            )

            # Ensure output directory exists
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Save template
            template_file = output_path / f"{template_name}.png"
            cv2.imwrite(str(template_file), template_img)

            # Create template metadata JSON
            metadata = {
                "template_name": template_name,
                "created_date": self.registry.registry_data["registry_info"][
                    "last_updated"
                ],
                "template_size": {
                    "width": self.template_width,
                    "height": self.template_height,
                },
                "drawing_area": {
                    "width": self.drawing_width,
                    "height": self.drawing_height,
                    "offset_x": self.drawing_x,
                    "offset_y": self.drawing_y,
                },
                "aruco_markers": {
                    "dictionary": "4X4_50",
                    "marker_size": self.marker_size,
                    "ids": marker_ids,
                },
                "image_settings": {
                    "has_image": image_path is not None,
                    "scale": image_scale,
                    "offset_x": image_offset_x,
                    "offset_y": image_offset_y,
                },
            }

            # Save metadata JSON
            metadata_file = output_path / f"{template_name}.json"
            import json

            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            # Register in template registry
            image_settings = {
                "scale": image_scale,
                "offset_x": image_offset_x,
                "offset_y": image_offset_y,
                "has_image": image_path is not None,
            }

            success = self.registry.register_template(
                template_name=template_name,
                marker_ids=marker_ids,
                client_name=client_name,
                template_file_path=str(template_file),
                image_settings=image_settings,
            )

            if success:
                print(f"✅ Template '{template_name}' created and registered")
                print(f"📁 Template file: {template_file}")
                print(f"📄 Metadata file: {metadata_file}")
                print(f"🎯 Marker IDs: {marker_ids}")
                return True, f"Template created successfully at {template_file}"
            else:
                return False, "Failed to register template in registry"

        except Exception as e:
            logger.error(f"Template creation failed: {e}")
            return False, f"Template creation failed: {e}"

    def create_template_image(
        self,
        marker_ids: List[int],
        image_path: Optional[str] = None,
        image_scale: float = 0.8,
        image_offset_x: int = 0,
        image_offset_y: int = 0,
    ) -> np.ndarray:
        """
        Create the actual template image with markers and optional image.

        Args:
            marker_ids: List of 4 marker IDs to use
            image_path: Path to image to include
            image_scale: Scale factor for image
            image_offset_x: X offset for image placement
            image_offset_y: Y offset for image placement

        Returns:
            Template image as numpy array
        """
        # Create white template
        template = (
            np.ones((self.template_height, self.template_width, 3), dtype=np.uint8)
            * 255
        )

        # Draw drawing area outline (light gray)
        cv2.rectangle(
            template,
            (self.drawing_x, self.drawing_y),
            (self.drawing_x + self.drawing_width, self.drawing_y + self.drawing_height),
            (200, 200, 200),
            2,
        )

        # Place image if provided
        if image_path and os.path.exists(image_path):
            self.place_image_in_template(
                template, image_path, image_scale, image_offset_x, image_offset_y
            )

        # Place ArUco markers at corners (outside the drawing area)
        self.place_markers_on_template(template, marker_ids)

        return template

    def place_image_in_template(
        self,
        template: np.ndarray,
        image_path: str,
        scale: float,
        offset_x: int,
        offset_y: int,
    ):
        """
        Place an image in the template's drawing area.

        Args:
            template: Template image to modify
            image_path: Path to image to place
            scale: Scale factor for the image
            offset_x: X offset within drawing area
            offset_y: Y offset within drawing area
        """
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                print(f"⚠️  Could not load image: {image_path}")
                return

            # Calculate scaled size
            img_height, img_width = img.shape[:2]
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)

            # Resize image
            img_resized = cv2.resize(img, (new_width, new_height))

            # Calculate position within drawing area
            img_x = self.drawing_x + (self.drawing_width - new_width) // 2 + offset_x
            img_y = self.drawing_y + (self.drawing_height - new_height) // 2 + offset_y

            # Ensure image stays within drawing area
            img_x = max(
                self.drawing_x,
                min(img_x, self.drawing_x + self.drawing_width - new_width),
            )
            img_y = max(
                self.drawing_y,
                min(img_y, self.drawing_y + self.drawing_height - new_height),
            )

            # Place image on template
            template[
                img_y : img_y + new_height, img_x : img_x + new_width
            ] = img_resized

            print(f"📷 Image placed: {new_width}x{new_height} at ({img_x}, {img_y})")

        except Exception as e:
            print(f"⚠️  Image placement error: {e}")

    def place_markers_on_template(self, template: np.ndarray, marker_ids: List[int]):
        """
        Place ArUco markers at the corners of the template.

        Args:
            template: Template image to modify
            marker_ids: List of 4 marker IDs
        """
        # Marker positions (outside drawing area)
        positions = [
            (50, 50),  # Top-left
            (self.template_width - 50 - self.marker_size, 50),  # Top-right
            (50, self.template_height - 50 - self.marker_size),  # Bottom-left
            (
                self.template_width - 50 - self.marker_size,
                self.template_height - 50 - self.marker_size,
            ),  # Bottom-right
        ]

        for i, (marker_id, (x, y)) in enumerate(zip(marker_ids, positions)):
            try:
                # Generate marker
                marker = self.aruco_generator.generate_marker(
                    marker_id, self.marker_size
                )

                # Convert to 3-channel if needed
                if len(marker.shape) == 2:
                    marker_3ch = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)
                else:
                    marker_3ch = marker

                # Place marker on template
                template[
                    y : y + self.marker_size, x : x + self.marker_size
                ] = marker_3ch

                print(f"📍 Marker {marker_id} placed at ({x}, {y})")

            except Exception as e:
                print(f"⚠️  Marker placement error for ID {marker_id}: {e}")

    def generate_preview(
        self,
        marker_ids: List[int],
        image_path: Optional[str] = None,
        image_scale: float = 0.8,
        image_offset_x: int = 0,
        image_offset_y: int = 0,
    ) -> np.ndarray:
        """
        Generate a preview of the template.

        Args:
            marker_ids: List of marker IDs
            image_path: Path to image to include
            image_scale: Scale factor for image
            image_offset_x: X offset for image
            image_offset_y: Y offset for image

        Returns:
            Preview image as numpy array
        """
        return self.create_template_image(
            marker_ids=marker_ids,
            image_path=image_path,
            image_scale=image_scale,
            image_offset_x=image_offset_x,
            image_offset_y=image_offset_y,
        )

    def suggest_template_name(self, client_name: str = "") -> str:
        """
        Suggest a template name for the client.

        Args:
            client_name: Name of the client

        Returns:
            Suggested template name
        """
        return self.registry.suggest_template_name(client_name)

    def get_registry_stats(self) -> dict:
        """Get template registry statistics."""
        return self.registry.get_registry_stats()


if __name__ == "__main__":
    # Test the enhanced template maker
    print("🎯 Testing Enhanced Template Maker with Registry")

    # Create template maker
    maker = EnhancedKrathongTemplateMaker()

    # Test auto-ID assignment
    auto_ids = maker.get_auto_assigned_ids()
    print(f"Auto-assigned IDs: {auto_ids}")

    # Create test template
    success, message = maker.create_template_with_registry(
        template_name="test_template_registry",
        client_name="Test Client",
        marker_ids=auto_ids,
    )

    print(f"Template creation: {success}")
    print(f"Message: {message}")

    # Show registry stats
    stats = maker.get_registry_stats()
    print(f"Registry stats: {stats}")

    print("✅ Enhanced template maker test completed")
