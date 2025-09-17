"""
Unified Template Creator

Main application that combines all extracted modules to provide complete
template creation functionality. Replaces the original 3537-line template_maker_gui.py
with a modular, maintainable architecture.

Key Features:
- Complete krathong image import and cropping workflow
- Interactive mask generation and preview
- Template creation with ArUco markers
- Background removal with multiple methods
- Template and mask adjustment tools
- Database integration for template management

Author: KrathongScanner Team
"""

import logging
import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

# Add the modules directory to the path
current_dir = Path(__file__).parent
modules_dir = current_dir / "modules"
sys.path.insert(0, str(modules_dir))

from cropping_system import CroppingSystem

# Import our modules
from image_loader import ImageLoader
from image_processor import (
    BackgroundRemovalMethod,
    ImageProcessor,
    MaskGenerationMethod,
)
from template_creator import TemplateCreator, TemplateSettings
from ui_components import (
    ControlPanel,
    CoordinateInput,
    FileSelector,
    PreviewCanvas,
    TemplatePreviewWindow,
    center_window,
    show_error_dialog,
    show_info_dialog,
)

# Import from core if available
try:
    sys.path.insert(0, str(current_dir.parent.parent / "core"))
    from template_maker import KrathongTemplateMaker
except ImportError:
    print("Warning: Core template_maker not found, using built-in functionality")
    KrathongTemplateMaker = None


class UnifiedTemplateCreator:
    """
    Unified Template Creator Application

    Combines all extracted modules to provide complete template creation functionality
    with proper workflow management and database integration.
    """

    def __init__(self):
        """Initialize the unified template creator."""
        self.setup_logging()
        self.logger = logging.getLogger(__name__)

        # Initialize modules
        self.image_loader = ImageLoader()
        self.cropping_system = CroppingSystem()
        self.image_processor = ImageProcessor()
        self.template_creator = TemplateCreator()

        # State variables
        self.current_image = None
        self.cropped_image = None
        self.mask_image = None
        self.template_image = None

        # Settings
        self.template_name = ""
        self.marker_ids = [0, 1, 2, 3]
        self.output_directory = Path("data/templates")

        # UI state
        self.preview_window = None

        # Create main window
        self.root = tk.Tk()
        self.root.title("Unified Template Creator")
        self.root.geometry("1200x800")

        self.setup_ui()

        self.logger.info("Unified Template Creator initialized")

    def setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("unified_template_creator.log"),
            ],
        )

    def setup_ui(self):
        """Set up the main user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Image Import and Cropping
        self.setup_import_tab()

        # Tab 2: Background Removal and Mask Generation
        self.setup_processing_tab()

        # Tab 3: Template Creation
        self.setup_template_tab()

        # Status bar
        self.setup_status_bar(main_frame)

        # Connect cropping system to canvas
        self.cropping_system.set_canvas(self.image_canvas.canvas)

        center_window(self.root, 1200, 800)

    def setup_import_tab(self):
        """Set up the image import and cropping tab."""
        # Create tab frame
        import_frame = ttk.Frame(self.notebook)
        self.notebook.add(import_frame, text="1. Import & Crop")

        # Split into left and right panels
        left_panel = ttk.Frame(import_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        right_panel = ttk.Frame(import_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        # Image canvas
        self.image_canvas = PreviewCanvas(left_panel, width=800, height=600)
        self.image_canvas.pack(fill=tk.BOTH, expand=True)

        # Bind cropping events
        self.image_canvas.bind_event("<Button-1>", self.on_crop_start)
        self.image_canvas.bind_event("<B1-Motion>", self.on_crop_drag)
        self.image_canvas.bind_event("<ButtonRelease-1>", self.on_crop_end)

        # Right panel controls
        # File selector
        file_frame = ttk.LabelFrame(right_panel, text="Krathong Image", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_selector = FileSelector(
            file_frame,
            title="Select Krathong Image",
            file_types=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("All files", "*.*"),
            ],
            callback=self.on_image_selected,
        )
        self.file_selector.pack(fill=tk.X)

        # Crop controls
        crop_frame = ttk.LabelFrame(right_panel, text="Crop Controls", padding="10")
        crop_frame.pack(fill=tk.X, pady=(0, 10))

        self.crop_coords = CoordinateInput(
            crop_frame, "Crop Area", self.on_crop_coords_changed
        )
        self.crop_coords.pack(fill=tk.X, pady=5)

        # Crop buttons
        crop_buttons = [
            {"text": "Auto Detect", "command": self.auto_detect_crop},
            {"text": "Quick Crop", "command": self.quick_crop},
            {"text": "Reset Crop", "command": self.reset_crop},
            {"text": "Apply Crop", "command": self.apply_crop},
        ]

        for btn_config in crop_buttons:
            ttk.Button(crop_frame, **btn_config).pack(fill=tk.X, pady=2)

        # Preview button
        ttk.Button(
            crop_frame, text="Preview Cropped", command=self.preview_cropped
        ).pack(fill=tk.X, pady=(10, 0))

    def setup_processing_tab(self):
        """Set up the background removal and mask generation tab."""
        # Create tab frame
        processing_frame = ttk.Frame(self.notebook)
        self.notebook.add(processing_frame, text="2. Process & Mask")

        # Split into left and right panels
        left_panel = ttk.Frame(processing_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        right_panel = ttk.Frame(processing_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        # Processing canvas
        self.processing_canvas = PreviewCanvas(left_panel, width=800, height=600)
        self.processing_canvas.pack(fill=tk.BOTH, expand=True)

        # Background removal controls
        bg_frame = ttk.LabelFrame(right_panel, text="Background Removal", padding="10")
        bg_frame.pack(fill=tk.X, pady=(0, 10))

        # Method selection
        ttk.Label(bg_frame, text="Method:").pack(anchor=tk.W)
        self.bg_method_var = tk.StringVar(value="aggressive")

        methods = [
            ("Standard", "standard"),
            ("Aggressive", "aggressive"),
            ("Smart", "smart"),
            ("HSV Based", "hsv_based"),
            ("LAB Based", "lab_based"),
            ("Threshold", "threshold"),
        ]

        for text, value in methods:
            ttk.Radiobutton(
                bg_frame, text=text, variable=self.bg_method_var, value=value
            ).pack(anchor=tk.W)

        ttk.Button(
            bg_frame, text="Remove Background", command=self.remove_background
        ).pack(fill=tk.X, pady=(10, 0))

        # Mask generation controls
        mask_frame = ttk.LabelFrame(right_panel, text="Mask Generation", padding="10")
        mask_frame.pack(fill=tk.X, pady=(0, 10))

        # Mask method selection
        ttk.Label(mask_frame, text="Method:").pack(anchor=tk.W)
        self.mask_method_var = tk.StringVar(value="contour")

        mask_methods = [
            ("Contour", "contour"),
            ("Threshold", "threshold"),
            ("Edge Detection", "edge_detection"),
            ("Color Segmentation", "color_segmentation"),
        ]

        for text, value in mask_methods:
            ttk.Radiobutton(
                mask_frame, text=text, variable=self.mask_method_var, value=value
            ).pack(anchor=tk.W)

        ttk.Button(mask_frame, text="Generate Mask", command=self.generate_mask).pack(
            fill=tk.X, pady=(10, 0)
        )

        # Preview controls
        preview_frame = ttk.LabelFrame(right_panel, text="Preview", padding="10")
        preview_frame.pack(fill=tk.X, pady=(0, 10))

        self.show_original_var = tk.BooleanVar(value=True)
        self.show_processed_var = tk.BooleanVar(value=False)
        self.show_mask_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(
            preview_frame,
            text="Show Original",
            variable=self.show_original_var,
            command=self.update_processing_preview,
        ).pack(anchor=tk.W)
        ttk.Checkbutton(
            preview_frame,
            text="Show Processed",
            variable=self.show_processed_var,
            command=self.update_processing_preview,
        ).pack(anchor=tk.W)
        ttk.Checkbutton(
            preview_frame,
            text="Show Mask",
            variable=self.show_mask_var,
            command=self.update_processing_preview,
        ).pack(anchor=tk.W)

    def setup_template_tab(self):
        """Set up the template creation tab."""
        # Create tab frame
        template_frame = ttk.Frame(self.notebook)
        self.notebook.add(template_frame, text="3. Create Template")

        # Split into left and right panels
        left_panel = ttk.Frame(template_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        right_panel = ttk.Frame(template_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        # Template canvas
        self.template_canvas = PreviewCanvas(left_panel, width=800, height=600)
        self.template_canvas.pack(fill=tk.BOTH, expand=True)

        # Template settings
        settings_frame = ttk.LabelFrame(
            right_panel, text="Template Settings", padding="10"
        )
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Template name
        ttk.Label(settings_frame, text="Template Name:").pack(anchor=tk.W)
        self.template_name_var = tk.StringVar()
        ttk.Entry(settings_frame, textvariable=self.template_name_var).pack(
            fill=tk.X, pady=(0, 10)
        )

        # Marker IDs
        marker_frame = ttk.Frame(settings_frame)
        marker_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(marker_frame, text="ArUco Marker IDs:").pack(anchor=tk.W)

        marker_input_frame = ttk.Frame(marker_frame)
        marker_input_frame.pack(fill=tk.X, pady=5)

        self.marker_vars = []
        marker_labels = ["Top-Left:", "Top-Right:", "Bottom-Left:", "Bottom-Right:"]

        for i, label in enumerate(marker_labels):
            row_frame = ttk.Frame(marker_input_frame)
            row_frame.pack(fill=tk.X, pady=1)

            ttk.Label(row_frame, text=label, width=12).pack(side=tk.LEFT)
            var = tk.IntVar(value=self.marker_ids[i])
            self.marker_vars.append(var)
            ttk.Entry(row_frame, textvariable=var, width=5).pack(
                side=tk.LEFT, padx=(5, 0)
            )

        # Output directory
        ttk.Label(settings_frame, text="Output Directory:").pack(
            anchor=tk.W, pady=(10, 0)
        )
        self.output_dir_var = tk.StringVar(value=str(self.output_directory))

        dir_frame = ttk.Frame(settings_frame)
        dir_frame.pack(fill=tk.X, pady=5)

        ttk.Entry(dir_frame, textvariable=self.output_dir_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(dir_frame, text="Browse", command=self.browse_output_dir).pack(
            side=tk.RIGHT, padx=(5, 0)
        )

        # Adjustment controls
        adjust_frame = ttk.LabelFrame(
            right_panel, text="Image Adjustment", padding="10"
        )
        adjust_frame.pack(fill=tk.X, pady=(0, 10))

        self.adjustment_controls = ControlPanel(adjust_frame, "")
        self.adjustment_controls.pack(fill=tk.X)

        self.adjustment_controls.add_slider(
            "scale", "Scale:", 0.1, 1.5, initial=0.8, callback=self.on_adjustment_change
        )
        self.adjustment_controls.add_slider(
            "offset_x",
            "X Offset:",
            -200,
            200,
            initial=0,
            callback=self.on_adjustment_change,
        )
        self.adjustment_controls.add_slider(
            "offset_y",
            "Y Offset:",
            -200,
            200,
            initial=0,
            callback=self.on_adjustment_change,
        )

        # Template preview controls
        preview_frame = ttk.LabelFrame(
            right_panel, text="Template Preview", padding="10"
        )
        preview_frame.pack(fill=tk.X, pady=(0, 10))

        self.template_show_original_var = tk.BooleanVar(value=True)
        self.template_show_mask_var = tk.BooleanVar(value=False)
        self.template_show_overlay_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(
            preview_frame,
            text="Show Original Image",
            variable=self.template_show_original_var,
            command=self.update_template_preview,
        ).pack(anchor=tk.W)
        ttk.Checkbutton(
            preview_frame,
            text="Show Mask Overlay",
            variable=self.template_show_mask_var,
            command=self.update_template_preview,
        ).pack(anchor=tk.W)
        ttk.Checkbutton(
            preview_frame,
            text="Show Template Overlay",
            variable=self.template_show_overlay_var,
            command=self.update_template_preview,
        ).pack(anchor=tk.W)

        # Action buttons
        action_frame = ttk.LabelFrame(right_panel, text="Actions", padding="10")
        action_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            action_frame, text="Preview Template", command=self.preview_template
        ).pack(fill=tk.X, pady=2)
        ttk.Button(
            action_frame, text="Create Template", command=self.create_template
        ).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Save Template", command=self.save_template).pack(
            fill=tk.X, pady=2
        )

    def setup_status_bar(self, parent):
        """Set up the status bar."""
        self.status_bar = ttk.Frame(parent)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.status_bar, textvariable=self.status_var).pack(side=tk.LEFT)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.status_bar, variable=self.progress_var, length=200, mode="determinate"
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))

    def update_status(self, message: str, progress: float = 0.0):
        """Update status bar."""
        self.status_var.set(message)
        self.progress_var.set(progress)
        self.root.update_idletasks()

    # Event handlers
    def on_image_selected(self, file_path: str):
        """Handle image selection."""
        if file_path:
            try:
                self.update_status("Loading image...", 10)

                # Load image using image loader
                success = self.image_loader.load_image(file_path)

                if success:
                    self.current_image = self.image_loader.get_image()
                    self.image_canvas.display_image(self.current_image)

                    # Initialize cropping system with image and scale factor
                    self.cropping_system.set_image(self.current_image)
                    height, width = self.current_image.shape[:2]
                    self.cropping_system.set_image_properties(
                        width, height, self.image_canvas.scale_factor
                    )

                    self.update_status(f"Image loaded: {file_path}", 100)
                    self.logger.info(f"Image loaded successfully: {file_path}")
                else:
                    show_error_dialog(self.root, "Error", "Failed to load image")
                    self.update_status("Error loading image", 0)

            except Exception as e:
                self.logger.error(f"Error loading image: {e}")
                show_error_dialog(self.root, "Error", f"Error loading image: {e}")
                self.update_status("Error", 0)
        else:
            # Clear image
            self.current_image = None
            self.image_canvas.display_image(None)
            self.update_status("Image cleared", 0)

    def on_crop_start(self, event):
        """Handle crop start."""
        if self.current_image is not None:
            img_x, img_y = self.image_canvas.canvas_to_image_coords(event.x, event.y)
            self.cropping_system.start_selection(img_x, img_y)

    def on_crop_drag(self, event):
        """Handle crop drag."""
        if self.current_image is not None and self.cropping_system.is_selecting():
            img_x, img_y = self.image_canvas.canvas_to_image_coords(event.x, event.y)
            self.cropping_system.update_selection(img_x, img_y)
            self.update_crop_overlay()

    def on_crop_end(self, event):
        """Handle crop end."""
        if self.current_image is not None:
            img_x, img_y = self.image_canvas.canvas_to_image_coords(event.x, event.y)
            coords = self.cropping_system.end_selection(img_x, img_y)

            if coords:
                x1, y1, x2, y2 = coords
                self.crop_coords.set_coordinates(x1, y1, x2, y2)
                self.update_crop_overlay()

    def on_crop_coords_changed(self, coords):
        """Handle crop coordinates change."""
        x1, y1, x2, y2 = coords
        self.cropping_system.set_selection(x1, y1, x2, y2)
        self.update_crop_overlay()

    def update_crop_overlay(self):
        """Update crop overlay on canvas."""
        coords = self.cropping_system.get_selection()
        if coords:
            x1, y1, x2, y2 = coords
            canvas_coords = [
                *self.image_canvas.image_to_canvas_coords(x1, y1),
                *self.image_canvas.image_to_canvas_coords(x2, y2),
            ]

            self.image_canvas.remove_overlay("crop_rect")
            self.image_canvas.add_overlay(
                "crop_rect",
                "rectangle",
                canvas_coords,
                outline="blue",
                width=2,
                dash=(5, 5),
            )

    def auto_detect_crop(self):
        """Auto-detect crop area."""
        try:
            if self.current_image is not None:
                self.update_status("Auto-detecting crop area...", 30)

                coords = self.cropping_system.auto_detect_bounds()
                if coords:
                    x1, y1, x2, y2 = coords
                    self.crop_coords.set_coordinates(x1, y1, x2, y2)
                    self.update_crop_overlay()
                    self.update_status("Auto-detection complete", 100)
                else:
                    show_error_dialog(
                        self.root, "Error", "Could not auto-detect crop area"
                    )
                    self.update_status("Auto-detection failed", 0)
        except Exception as e:
            self.logger.error(f"Auto-detection error: {e}")
            show_error_dialog(self.root, "Error", f"Auto-detection failed: {e}")
            self.update_status("Error", 0)

    def quick_crop(self):
        """Perform quick crop of entire image."""
        try:
            if self.current_image is not None:
                h, w = self.current_image.shape[:2]
                margin = min(w, h) // 20  # 5% margin
                self.crop_coords.set_coordinates(margin, margin, w - margin, h - margin)
                self.update_crop_overlay()
                self.update_status("Quick crop applied", 100)
        except Exception as e:
            self.logger.error(f"Quick crop error: {e}")

    def reset_crop(self):
        """Reset crop selection."""
        self.cropping_system.clear_selection()
        self.crop_coords.clear()
        self.image_canvas.remove_overlay("crop_rect")
        self.update_status("Crop reset", 0)

    def apply_crop(self):
        """Apply crop to image."""
        try:
            if self.current_image is not None:
                coords = self.cropping_system.get_selection()
                if coords:
                    self.update_status("Applying crop...", 50)

                    self.cropped_image = self.cropping_system.crop_image()
                    if self.cropped_image is not None:
                        # Switch to processing tab
                        self.notebook.select(1)
                        self.processing_canvas.display_image(self.cropped_image)
                        self.update_status("Crop applied successfully", 100)
                    else:
                        show_error_dialog(self.root, "Error", "Failed to crop image")
                        self.update_status("Crop failed", 0)
                else:
                    show_error_dialog(self.root, "Error", "No crop area selected")
        except Exception as e:
            self.logger.error(f"Crop application error: {e}")
            show_error_dialog(self.root, "Error", f"Crop failed: {e}")
            self.update_status("Error", 0)

    def preview_cropped(self):
        """Preview cropped image."""
        if self.current_image is not None:
            coords = self.cropping_system.get_selection()
            if coords:
                preview_image = self.cropping_system.get_preview()
                if preview_image is not None:
                    # Show in a popup window
                    self.show_image_popup("Crop Preview", preview_image)

    def remove_background(self):
        """Remove background from image."""
        try:
            if self.cropped_image is not None:
                self.update_status("Removing background...", 50)

                method_name = self.bg_method_var.get()
                method = BackgroundRemovalMethod(method_name)

                processed_image = self.image_processor.remove_background(
                    self.cropped_image, method
                )

                if processed_image is not None:
                    self.cropped_image = processed_image
                    self.update_processing_preview()
                    self.update_status("Background removed", 100)
                else:
                    show_error_dialog(self.root, "Error", "Background removal failed")
                    self.update_status("Background removal failed", 0)

        except Exception as e:
            self.logger.error(f"Background removal error: {e}")
            show_error_dialog(self.root, "Error", f"Background removal failed: {e}")
            self.update_status("Error", 0)

    def generate_mask(self):
        """Generate mask from processed image."""
        try:
            if self.cropped_image is not None:
                self.update_status("Generating mask...", 50)

                method_name = self.mask_method_var.get()
                method = MaskGenerationMethod(method_name)

                self.mask_image = self.image_processor.generate_mask(
                    self.cropped_image, method
                )

                if self.mask_image is not None:
                    self.update_processing_preview()
                    self.update_status("Mask generated", 100)
                else:
                    show_error_dialog(self.root, "Error", "Mask generation failed")
                    self.update_status("Mask generation failed", 0)

        except Exception as e:
            self.logger.error(f"Mask generation error: {e}")
            show_error_dialog(self.root, "Error", f"Mask generation failed: {e}")
            self.update_status("Error", 0)

    def update_processing_preview(self):
        """Update processing preview based on checkbox states."""
        if self.show_original_var.get() and self.current_image is not None:
            self.processing_canvas.display_image(self.current_image)
        elif self.show_processed_var.get() and self.cropped_image is not None:
            self.processing_canvas.display_image(self.cropped_image)
        elif self.show_mask_var.get() and self.mask_image is not None:
            # Convert grayscale mask to BGR for display
            mask_bgr = cv2.cvtColor(self.mask_image, cv2.COLOR_GRAY2BGR)
            self.processing_canvas.display_image(mask_bgr)

    def update_template_preview(self):
        """Update template preview based on checkbox states."""
        try:
            if self.cropped_image is None:
                return

            # Start with base template or cropped image
            if hasattr(self, "template_image") and self.template_image is not None:
                # Use existing template as base
                display_image = self.template_image.copy()
            else:
                # Create basic template preview
                settings = self.get_template_settings()
                display_image = self.template_creator._create_template_image(
                    marker_ids=settings.marker_ids,
                    krathong_image=self.cropped_image,
                    scale=settings.scale,
                    offset_x=settings.offset_x,
                    offset_y=settings.offset_y,
                )
                if display_image is None:
                    return

            # Apply overlays based on checkbox states
            if (
                self.template_show_mask_var.get()
                and hasattr(self, "mask_image")
                and self.mask_image is not None
            ):
                # Create mask overlay on template
                # Get drawing area bounds
                drawing_area = self.template_creator._get_drawing_area()
                x1, y1, x2, y2 = drawing_area

                # Resize mask to match krathong area in template
                mask_resized = cv2.resize(self.mask_image, (x2 - x1, y2 - y1))

                # Create colored mask overlay (semi-transparent red)
                mask_overlay = np.zeros(
                    (display_image.shape[0], display_image.shape[1], 3), dtype=np.uint8
                )
                mask_overlay[y1:y2, x1:x2] = cv2.merge(
                    [
                        mask_resized,
                        np.zeros_like(mask_resized),
                        np.zeros_like(mask_resized),
                    ]
                )

                # Blend with template
                alpha = 0.3  # Transparency
                display_image = cv2.addWeighted(
                    display_image, 1 - alpha, mask_overlay, alpha, 0
                )

            if not self.template_show_original_var.get():
                # Darken the krathong image area if "Show Original Image" is unchecked
                drawing_area = self.template_creator._get_drawing_area()
                x1, y1, x2, y2 = drawing_area
                overlay = display_image.copy()
                overlay[y1:y2, x1:x2] = overlay[y1:y2, x1:x2] * 0.3  # Darken to 30%
                display_image = overlay

            # Update template canvas
            self.template_canvas.display_image(display_image)

        except Exception as e:
            self.logger.error(f"Template preview update error: {e}")

    def browse_output_dir(self):
        """Browse for output directory."""
        from tkinter import filedialog

        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)
            self.output_directory = Path(directory)

    def on_adjustment_change(self, value):
        """Handle adjustment control changes."""
        self.preview_template()

    def preview_template(self):
        """Preview template with current settings."""
        try:
            if self.cropped_image is not None:
                self.update_status("Generating template preview...", 50)

                # Get current settings
                settings = self.get_template_settings()

                # Create template
                template_image = self.template_creator._create_template_image(
                    marker_ids=settings.marker_ids,
                    krathong_image=self.cropped_image,
                    scale=settings.scale,
                    offset_x=settings.offset_x,
                    offset_y=settings.offset_y,
                )

                if template_image is not None:
                    self.template_image = template_image
                    self.template_canvas.display_image(template_image)
                    self.update_status("Template preview ready", 100)
                else:
                    show_error_dialog(self.root, "Error", "Template preview failed")
                    self.update_status("Template preview failed", 0)

        except Exception as e:
            self.logger.error(f"Template preview error: {e}")
            show_error_dialog(self.root, "Error", f"Template preview failed: {e}")
            self.update_status("Error", 0)

    def create_template(self):
        """Create and save template."""
        try:
            if not self.validate_template_settings():
                return

            self.update_status("Creating template...", 30)

            # Get settings
            settings = self.get_template_settings()

            # Create template
            template_image, metadata = self.template_creator.create_template(
                settings=settings,
                krathong_image=self.cropped_image,
                mask_image=self.mask_image,
            )

            if template_image is not None:
                self.template_image = template_image
                self.template_canvas.display_image(template_image)

                self.update_status("Template created successfully", 100)
                show_info_dialog(
                    self.root,
                    "Success",
                    f"Template '{settings.template_name}' created successfully!\n\n"
                    f"Files saved to: {settings.output_dir}",
                )
            else:
                show_error_dialog(self.root, "Error", "Template creation failed")
                self.update_status("Template creation failed", 0)

        except Exception as e:
            self.logger.error(f"Template creation error: {e}")
            show_error_dialog(self.root, "Error", f"Template creation failed: {e}")
            self.update_status("Error", 0)

    def save_template(self):
        """Save current template."""
        if self.template_image is not None:
            try:
                settings = self.get_template_settings()
                output_path = (
                    Path(settings.output_dir) / f"{settings.template_name}.png"
                )

                success = cv2.imwrite(str(output_path), self.template_image)
                if success:
                    show_info_dialog(
                        self.root, "Success", f"Template saved to:\n{output_path}"
                    )
                else:
                    show_error_dialog(self.root, "Error", "Failed to save template")
            except Exception as e:
                self.logger.error(f"Template save error: {e}")
                show_error_dialog(self.root, "Error", f"Save failed: {e}")
        else:
            show_error_dialog(self.root, "Error", "No template to save")

    def get_template_settings(self) -> TemplateSettings:
        """Get current template settings."""
        marker_ids = [var.get() for var in self.marker_vars]

        return TemplateSettings(
            template_name=self.template_name_var.get().strip(),
            marker_ids=marker_ids,
            scale=self.adjustment_controls.get_value("scale"),
            offset_x=int(self.adjustment_controls.get_value("offset_x")),
            offset_y=int(self.adjustment_controls.get_value("offset_y")),
            output_dir=self.output_dir_var.get(),
            save_mask=True,
            embed_metadata=True,
        )

    def validate_template_settings(self) -> bool:
        """Validate template settings."""
        template_name = self.template_name_var.get().strip()
        if not template_name:
            show_error_dialog(self.root, "Error", "Template name is required")
            return False

        if self.cropped_image is None:
            show_error_dialog(self.root, "Error", "No krathong image loaded")
            return False

        # Validate marker IDs
        try:
            marker_ids = [var.get() for var in self.marker_vars]
            if len(set(marker_ids)) != 4:
                show_error_dialog(self.root, "Error", "Marker IDs must be unique")
                return False
        except:
            show_error_dialog(self.root, "Error", "Invalid marker IDs")
            return False

        return True

    def show_image_popup(self, title: str, image: np.ndarray):
        """Show image in popup window."""
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("600x400")

        canvas = PreviewCanvas(popup, width=580, height=380)
        canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        canvas.display_image(image)

        center_window(popup, 600, 400)

    def run(self):
        """Run the application."""
        try:
            self.logger.info("Starting Unified Template Creator")
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            self.logger.info("Application closed")


def main():
    """Main entry point."""
    try:
        app = UnifiedTemplateCreator()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
