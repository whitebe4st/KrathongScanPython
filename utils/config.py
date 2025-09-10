"""
Configuration settings for KrathongScanner applications.
"""

from pathlib import Path
from typing import Any, Dict


class Config:
    """Configuration settings for KrathongScanner."""

    # Application settings
    APP_NAME = "KrathongScanner"
    VERSION = "2.0.0"

    # Template settings
    TEMPLATE_WIDTH = 1270
    TEMPLATE_HEIGHT = 720
    DRAWING_AREA_WIDTH = 779
    DRAWING_AREA_HEIGHT = 457
    DRAWING_AREA_BORDER = 4

    # ArUco settings
    ARUCO_DICT = "DICT_4X4_50"
    MARKER_SIZE = 200
    MARKER_COUNT_PER_TEMPLATE = 4

    # Database settings
    TEMPLATES_DB = "data/templates.db"
    SCANNER_DB = "data/scanner.db"

    # Directory settings
    DATA_DIR = Path("data")
    TEMPLATES_DIR = DATA_DIR / "templates"
    SCANNER_TEMPLATES_DIR = DATA_DIR / "scanner_templates"
    EXPORTS_DIR = DATA_DIR / "exports"
    PROCESSED_DIR = DATA_DIR / "processed"

    # File settings
    SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]
    SUPPORTED_VIDEO_FORMATS = [".mp4", ".avi", ".mov", ".mkv"]

    # UI settings
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    PREVIEW_WIDTH = 600
    PREVIEW_HEIGHT = 400

    # Processing settings
    DEFAULT_IMAGE_SCALE = 0.8
    DEFAULT_IMAGE_OFFSET_X = 0
    DEFAULT_IMAGE_OFFSET_Y = 0
    DEFAULT_MASK_SCALE = 1.0
    DEFAULT_MASK_OFFSET_X = 0
    DEFAULT_MASK_OFFSET_Y = 0

    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        directories = [
            cls.DATA_DIR,
            cls.TEMPLATES_DIR,
            cls.SCANNER_TEMPLATES_DIR,
            cls.EXPORTS_DIR,
            cls.PROCESSED_DIR,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_template_config(cls) -> Dict[str, Any]:
        """Get template configuration."""
        return {
            "width": cls.TEMPLATE_WIDTH,
            "height": cls.TEMPLATE_HEIGHT,
            "drawing_area": {
                "width": cls.DRAWING_AREA_WIDTH,
                "height": cls.DRAWING_AREA_HEIGHT,
                "border": cls.DRAWING_AREA_BORDER,
            },
            "aruco": {
                "dict": cls.ARUCO_DICT,
                "marker_size": cls.MARKER_SIZE,
                "marker_count": cls.MARKER_COUNT_PER_TEMPLATE,
            },
        }

    @classmethod
    def get_ui_config(cls) -> Dict[str, Any]:
        """Get UI configuration."""
        return {
            "window": {"width": cls.WINDOW_WIDTH, "height": cls.WINDOW_HEIGHT},
            "preview": {"width": cls.PREVIEW_WIDTH, "height": cls.PREVIEW_HEIGHT},
        }

    @classmethod
    def get_processing_config(cls) -> Dict[str, Any]:
        """Get processing configuration."""
        return {
            "image": {
                "scale": cls.DEFAULT_IMAGE_SCALE,
                "offset_x": cls.DEFAULT_IMAGE_OFFSET_X,
                "offset_y": cls.DEFAULT_IMAGE_OFFSET_Y,
            },
            "mask": {
                "scale": cls.DEFAULT_MASK_SCALE,
                "offset_x": cls.DEFAULT_MASK_OFFSET_X,
                "offset_y": cls.DEFAULT_MASK_OFFSET_Y,
            },
        }
