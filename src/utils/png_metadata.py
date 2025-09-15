"""
PNG Metadata Utilities for KrathongScanner Template System.

This module provides utilities for embedding and reading metadata in PNG images
using PNG text chunks. This allows template images to be self-describing with
embedded marker IDs, template names, and other metadata.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image
from PIL.PngImagePlugin import PngInfo

logger = logging.getLogger(__name__)


class PNGMetadataManager:
    """Manager for PNG text chunk metadata operations."""

    # Metadata keys for PNG text chunks
    NAMESPACE = "KrathongScanner"
    KEY_MARKER_IDS = f"{NAMESPACE}:marker_ids"
    KEY_TEMPLATE_NAME = f"{NAMESPACE}:template_name"
    KEY_VERSION = f"{NAMESPACE}:version"
    KEY_CREATED_DATE = f"{NAMESPACE}:created_date"
    KEY_SCALE = f"{NAMESPACE}:scale"
    KEY_OFFSET_X = f"{NAMESPACE}:offset_x"
    KEY_OFFSET_Y = f"{NAMESPACE}:offset_y"
    KEY_MASK_PATH = f"{NAMESPACE}:mask_path"

    CURRENT_VERSION = "2.0"

    @classmethod
    def embed_template_metadata(
        cls,
        image_path: str,
        marker_ids: List[int],
        template_name: str,
        scale: Optional[float] = None,
        offset_x: Optional[int] = None,
        offset_y: Optional[int] = None,
        mask_path: Optional[str] = None,
        created_date: Optional[str] = None,
    ) -> bool:
        """
        Embed template metadata in PNG text chunks.

        Args:
            image_path: Path to PNG image file
            marker_ids: List of 4 marker IDs
            template_name: Name of the template
            scale: Template scale factor
            offset_x: X offset for template positioning
            offset_y: Y offset for template positioning
            mask_path: Path to associated mask file
            created_date: Creation date (ISO format)

        Returns:
            bool: Success status
        """
        try:
            # Load the image
            img = Image.open(image_path)

            # Create metadata info
            metadata = PngInfo()

            # Core metadata
            metadata.add_text(cls.KEY_MARKER_IDS, json.dumps(marker_ids))
            metadata.add_text(cls.KEY_TEMPLATE_NAME, template_name)
            metadata.add_text(cls.KEY_VERSION, cls.CURRENT_VERSION)

            # Optional metadata
            if created_date:
                metadata.add_text(cls.KEY_CREATED_DATE, created_date)
            if scale is not None:
                metadata.add_text(cls.KEY_SCALE, str(scale))
            if offset_x is not None:
                metadata.add_text(cls.KEY_OFFSET_X, str(offset_x))
            if offset_y is not None:
                metadata.add_text(cls.KEY_OFFSET_Y, str(offset_y))
            if mask_path:
                metadata.add_text(cls.KEY_MASK_PATH, mask_path)

            # Save image with metadata
            img.save(image_path, pnginfo=metadata)

            logger.info(f"✅ Embedded metadata in {image_path}")
            logger.debug(f"   Marker IDs: {marker_ids}")
            logger.debug(f"   Template: {template_name}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to embed metadata in {image_path}: {e}")
            return False

    @classmethod
    def read_template_metadata(cls, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Read template metadata from PNG text chunks.

        Args:
            image_path: Path to PNG image file

        Returns:
            dict: Metadata dictionary or None if not found
        """
        try:
            img = Image.open(image_path)

            # Check if image has text metadata
            if not hasattr(img, "text") or not img.text:
                logger.debug(f"No text metadata found in {image_path}")
                return None

            # Extract KrathongScanner metadata
            metadata = {}

            # Core metadata
            if cls.KEY_MARKER_IDS in img.text:
                try:
                    metadata["marker_ids"] = json.loads(img.text[cls.KEY_MARKER_IDS])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid marker_ids JSON in {image_path}")

            if cls.KEY_TEMPLATE_NAME in img.text:
                metadata["template_name"] = img.text[cls.KEY_TEMPLATE_NAME]

            if cls.KEY_VERSION in img.text:
                metadata["version"] = img.text[cls.KEY_VERSION]

            # Optional metadata
            if cls.KEY_CREATED_DATE in img.text:
                metadata["created_date"] = img.text[cls.KEY_CREATED_DATE]

            if cls.KEY_SCALE in img.text:
                try:
                    metadata["scale"] = float(img.text[cls.KEY_SCALE])
                except ValueError:
                    logger.warning(f"Invalid scale value in {image_path}")

            if cls.KEY_OFFSET_X in img.text:
                try:
                    metadata["offset_x"] = int(img.text[cls.KEY_OFFSET_X])
                except ValueError:
                    logger.warning(f"Invalid offset_x value in {image_path}")

            if cls.KEY_OFFSET_Y in img.text:
                try:
                    metadata["offset_y"] = int(img.text[cls.KEY_OFFSET_Y])
                except ValueError:
                    logger.warning(f"Invalid offset_y value in {image_path}")

            if cls.KEY_MASK_PATH in img.text:
                metadata["mask_path"] = img.text[cls.KEY_MASK_PATH]

            # Only return metadata if we found KrathongScanner data
            if metadata:
                logger.info(f"✅ Read metadata from {image_path}")
                logger.debug(f"   Found keys: {list(metadata.keys())}")
                return metadata
            else:
                logger.debug(f"No KrathongScanner metadata found in {image_path}")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to read metadata from {image_path}: {e}")
            return None

    @classmethod
    def has_template_metadata(cls, image_path: str) -> bool:
        """
        Check if image has KrathongScanner template metadata.

        Args:
            image_path: Path to PNG image file

        Returns:
            bool: True if metadata is present
        """
        try:
            img = Image.open(image_path)
            if hasattr(img, "text") and img.text:
                return (
                    cls.KEY_MARKER_IDS in img.text or cls.KEY_TEMPLATE_NAME in img.text
                )
            return False
        except Exception:
            return False

    @classmethod
    def extract_marker_ids(cls, image_path: str) -> Optional[List[int]]:
        """
        Quick extraction of just marker IDs from image metadata.

        Args:
            image_path: Path to PNG image file

        Returns:
            list: Marker IDs or None if not found
        """
        metadata = cls.read_template_metadata(image_path)
        return metadata.get("marker_ids") if metadata else None

    @classmethod
    def validate_metadata(cls, metadata: Dict[str, Any]) -> bool:
        """
        Validate template metadata structure.

        Args:
            metadata: Metadata dictionary

        Returns:
            bool: True if metadata is valid
        """
        # Check required fields
        if "marker_ids" not in metadata:
            return False

        marker_ids = metadata["marker_ids"]
        if not isinstance(marker_ids, list) or len(marker_ids) != 4:
            return False

        # Check marker IDs are integers in valid range
        try:
            for mid in marker_ids:
                if not isinstance(mid, int) or mid < 0 or mid > 1023:  # ArUco 4x4 range
                    return False
        except (TypeError, ValueError):
            return False

        return True

    @classmethod
    def list_images_with_metadata(cls, directory: str) -> List[Dict[str, Any]]:
        """
        List all PNG images with KrathongScanner metadata in a directory.

        Args:
            directory: Directory path to search

        Returns:
            list: List of dictionaries with file path and metadata
        """
        results = []
        directory_path = Path(directory)

        if not directory_path.exists():
            logger.warning(f"Directory not found: {directory}")
            return results

        for png_file in directory_path.glob("*.png"):
            metadata = cls.read_template_metadata(str(png_file))
            if metadata:
                results.append(
                    {
                        "file_path": str(png_file),
                        "file_name": png_file.name,
                        "metadata": metadata,
                    }
                )

        logger.info(f"Found {len(results)} PNG files with metadata in {directory}")
        return results


def embed_template_metadata(
    image_path: str, marker_ids: List[int], template_name: str, **kwargs
) -> bool:
    """Convenience function for embedding template metadata."""
    return PNGMetadataManager.embed_template_metadata(
        image_path, marker_ids, template_name, **kwargs
    )


def read_template_metadata(image_path: str) -> Optional[Dict[str, Any]]:
    """Convenience function for reading template metadata."""
    return PNGMetadataManager.read_template_metadata(image_path)


def extract_marker_ids(image_path: str) -> Optional[List[int]]:
    """Convenience function for extracting marker IDs."""
    return PNGMetadataManager.extract_marker_ids(image_path)
