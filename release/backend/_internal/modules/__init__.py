"""
Unified Template Creator Modules

Modular template creation system extracted from original template_maker_gui.py.
Each module handles a specific aspect of the template creation workflow.

Modules:
- image_loader: Handles krathong image loading and validation
- cropping_system: Interactive image cropping and selection
- image_processor: Background removal and mask generation
- template_creator: Template creation with ArUco markers
- ui_components: Reusable UI components and dialogs

Author: KrathongScanner Team
"""

__version__ = "1.0.0"
__author__ = "KrathongScanner Team"

from .cropping_system import CroppingSystem

# Module exports
from .image_loader import ImageLoader
from .image_processor import (
    BackgroundRemovalMethod,
    ImageProcessor,
    MaskGenerationMethod,
)
from .template_creator import TemplateCreator, TemplateMetadata, TemplateSettings
from .ui_components import (
    ControlPanel,
    CoordinateInput,
    FileSelector,
    PreviewCanvas,
    TemplatePreviewWindow,
    center_window,
    show_error_dialog,
    show_info_dialog,
)

__all__ = [
    "ImageLoader",
    "CroppingSystem",
    "ImageProcessor",
    "BackgroundRemovalMethod",
    "MaskGenerationMethod",
    "TemplateCreator",
    "TemplateSettings",
    "TemplateMetadata",
    "PreviewCanvas",
    "ControlPanel",
    "CoordinateInput",
    "TemplatePreviewWindow",
    "FileSelector",
    "show_info_dialog",
    "show_error_dialog",
    "center_window",
]
