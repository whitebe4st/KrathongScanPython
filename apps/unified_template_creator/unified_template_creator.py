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

# Add the project root to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# Import path utilities
from path_utils import ensure_directories, get_database_path

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

# Import database components
try:
    sys.path.insert(0, str(current_dir.parent.parent))
    from database.models import TemplateData
    from database.registry import LocalTemplateRegistry
except ImportError:
    print("Warning: Database components not available")
    TemplateData = None
    LocalTemplateRegistry = None


class UnifiedTemplateCreator:
    """
    Unified Template Creator Application

    Combines all extracted modules to provide complete template creation functionality
    with proper workflow management and database integration.
    """

    def __init__(self, database_path: Optional[str] = None):
        """Initialize the unified template creator.

        Args:
            database_path: Optional path to scanner.db file. If None, uses default path.
        """
        self.setup_logging()

        # Add update throttling
        self.update_timer = None
        self.update_pending = False
        self.logger = logging.getLogger(__name__)

        # Initialize modules
        self.image_loader = ImageLoader()
        self.cropping_system = CroppingSystem()
        self.image_processor = ImageProcessor()
        self.template_creator = TemplateCreator()

        # Initialize database
        self.db_registry = None
        if LocalTemplateRegistry is not None:
            try:
                if database_path:
                    # Use provided database path
                    db_path = Path(database_path)
                    self.logger.info(f"Using custom database path: {db_path}")
                else:
                    # Use default database path
                    db_path = get_database_path()
                    self.logger.info(f"Using default database path: {db_path}")

                self.db_registry = LocalTemplateRegistry(str(db_path))
                self.logger.info(f"Database connected: {db_path}")
            except Exception as e:
                self.logger.error(f"Database connection failed: {e}")
                self.db_registry = None

        # State variables
        self.current_image = None
        self.cropped_image = None
        self.mask_image = None
        self.template_image = None

        # Settings
        self.template_name = ""
        self.marker_ids = [
            20,
            21,
            22,
            23,
        ]  # Use available range (20-49, excluding hardcoded 0-19)
        self.output_directory = Path("data/templates")

        # UI state
        self.preview_window = None

        # Create main window
        self.root = tk.Tk()
        self.root.title("Unified Template Creator")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)  # Make window resizable

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

        # Initialize database path after all UI is set up
        self.initialize_database_path()

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

        # Setup template creation tab
        self.setup_template_creation_tab(template_frame)

        # 4. Database Templates Tab
        db_frame = ttk.Frame(self.notebook)
        self.notebook.add(db_frame, text="4. Database Templates")

        # Setup database templates tab
        self.setup_database_templates_tab(db_frame)

    def setup_template_creation_tab(self, template_frame):
        """Setup the template creation tab UI."""

        # Split into left and right panels
        left_panel = ttk.Frame(template_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        right_panel = ttk.Frame(template_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, expand=True, padx=(5, 0))

        # Template canvas
        self.template_canvas = PreviewCanvas(left_panel, width=800, height=600)
        self.template_canvas.pack(fill=tk.BOTH, expand=True)

        # Create scrollable frame for right panel contents
        self.setup_scrollable_right_panel(right_panel)

    def setup_scrollable_right_panel(self, right_panel):
        """Set up a scrollable right panel for template controls."""
        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(right_panel, highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_panel, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Template settings
        settings_frame = ttk.LabelFrame(
            scrollable_frame, text="Template Settings", padding="10"
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

        # Add suggestion button and status
        suggestion_frame = ttk.Frame(marker_frame)
        suggestion_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(
            suggestion_frame,
            text="Suggest Available IDs",
            command=self.suggest_available_ids,
        ).pack(side=tk.LEFT)

        self.id_status_label = ttk.Label(
            suggestion_frame,
            text="Click 'Suggest Available IDs' to check database",
            foreground="gray",
        )
        self.id_status_label.pack(side=tk.LEFT, padx=(10, 0))

        marker_input_frame = ttk.Frame(marker_frame)
        marker_input_frame.pack(fill=tk.X, pady=5)

        self.marker_vars = []
        self.marker_status_labels = []  # Track status of each ID
        marker_labels = ["Top-Left:", "Top-Right:", "Bottom-Left:", "Bottom-Right:"]

        for i, label in enumerate(marker_labels):
            row_frame = ttk.Frame(marker_input_frame)
            row_frame.pack(fill=tk.X, pady=1)

            ttk.Label(row_frame, text=label, width=12).pack(side=tk.LEFT)
            var = tk.IntVar(value=self.marker_ids[i])
            self.marker_vars.append(var)

            entry = ttk.Entry(row_frame, textvariable=var, width=5)
            entry.pack(side=tk.LEFT, padx=(5, 0))

            # Add status label for this ID
            status_label = ttk.Label(row_frame, text="", width=15)
            status_label.pack(side=tk.LEFT, padx=(5, 0))
            self.marker_status_labels.append(status_label)

            # Bind change event to check ID availability
            var.trace_add(
                "write", lambda *args, idx=i: self.check_marker_id_status(idx)
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
            scrollable_frame, text="Image Adjustment", padding="10"
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

        # Mask adjustment controls
        mask_adjust_frame = ttk.LabelFrame(
            scrollable_frame, text="Mask Adjustment", padding="10"
        )
        mask_adjust_frame.pack(fill=tk.X, pady=(0, 10))

        self.mask_adjustment_controls = ControlPanel(mask_adjust_frame, "")
        self.mask_adjustment_controls.pack(fill=tk.X)

        self.mask_adjustment_controls.add_slider(
            "mask_scale",
            "Mask Scale:",
            0.1,
            2.0,
            initial=1.0,
            callback=self.on_mask_adjustment_change,
        )
        self.mask_adjustment_controls.add_slider(
            "mask_offset_x",
            "Mask X Offset:",
            -100,
            100,
            initial=0,
            callback=self.on_mask_adjustment_change,
        )
        self.mask_adjustment_controls.add_slider(
            "mask_offset_y",
            "Mask Y Offset:",
            -100,
            100,
            initial=0,
            callback=self.on_mask_adjustment_change,
        )

        # Preview controls
        preview_frame = ttk.LabelFrame(
            scrollable_frame, text="Preview Controls", padding="10"
        )
        preview_frame.pack(fill=tk.X, pady=(0, 10))

        # Show mask overlay checkbox
        self.template_show_mask_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            preview_frame,
            text="Show Mask Overlay",
            variable=self.template_show_mask_var,
            command=self.on_mask_overlay_toggle,
        ).pack(anchor=tk.W, pady=(0, 10))

        # Preview template button
        ttk.Button(
            preview_frame,
            text="👁️ Preview Template",
            command=self.preview_template,
        ).pack(fill=tk.X)

        # Database Configuration
        db_frame = ttk.LabelFrame(
            scrollable_frame, text="🗄️ Database Configuration", padding="10"
        )
        db_frame.pack(fill=tk.X, pady=(0, 10))

        # Database file selection
        ttk.Label(db_frame, text="Database File:").pack(anchor=tk.W, pady=(0, 5))

        db_selection_frame = ttk.Frame(db_frame)
        db_selection_frame.pack(fill=tk.X, pady=(0, 10))

        self.db_path_var = tk.StringVar()
        self.db_path_entry = ttk.Entry(
            db_selection_frame, textvariable=self.db_path_var, state="readonly"
        )
        self.db_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(
            db_selection_frame, text="Browse...", command=self.browse_database_file
        ).pack(side=tk.RIGHT)

        # Database options
        db_options_frame = ttk.Frame(db_frame)
        db_options_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            db_options_frame,
            text="🔍 Auto-Find Scanner DB",
            command=self.auto_find_scanner_db,
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            db_options_frame, text="🆕 Create New DB", command=self.create_new_database
        ).pack(side=tk.LEFT)

        # Database status
        self.db_status_label = ttk.Label(db_frame, text="Checking connection...")
        self.db_status_label.pack(anchor=tk.W, pady=(10, 0))

    def setup_status_bar(self, parent):
        """Set up the status bar."""
        self.status_bar = ttk.Frame(parent)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.status_bar, textvariable=self.status_var).pack(side=tk.LEFT)

        # Database status
        db_status = (
            "💾 DB: ✅ Connected"
            if self.db_registry is not None
            else "💾 DB: ❌ Not Connected"
        )
        self.db_status_var = tk.StringVar(value=db_status)
        ttk.Label(
            self.status_bar,
            textvariable=self.db_status_var,
            foreground="green" if self.db_registry else "red",
        ).pack(side=tk.LEFT, padx=(20, 0))

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.status_bar, variable=self.progress_var, length=200, mode="determinate"
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))

        # Initial check of marker ID status
        self.root.after(100, self.initial_marker_id_check)

    def initial_marker_id_check(self):
        """Perform initial check of marker ID availability."""
        for i in range(4):
            self.check_marker_id_status(i)

    def on_mask_adjustment_change(self, value=None):
        """Handle mask adjustment control changes by updating preview."""
        # Only update preview if we have a mask and the preview controls are set up
        if (
            hasattr(self, "mask_image")
            and self.mask_image is not None
            and hasattr(self, "template_show_mask_var")
            and self.template_show_mask_var.get()
        ):
            self.preview_template()

    def setup_database_templates_tab(self, db_frame):
        """Setup the database templates tab UI."""
        # Main container with padding
        main_container = ttk.Frame(db_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header section
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header_frame, text="Database Templates", font=("Arial", 14, "bold")
        ).pack(side=tk.LEFT)

        # Refresh button
        ttk.Button(
            header_frame, text="🔄 Refresh", command=self.refresh_templates_list
        ).pack(side=tk.RIGHT)

        # Create horizontal paned window for list and preview
        paned_window = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Left panel - Templates list
        left_panel = ttk.Frame(paned_window)
        paned_window.add(left_panel, weight=1)

        # Templates list section
        list_frame = ttk.LabelFrame(left_panel, text="Existing Templates", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Create Treeview for templates
        columns = ("Name", "Marker IDs", "Created", "Status")
        self.templates_tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", height=12
        )

        # Configure column headings and widths
        self.templates_tree.heading("Name", text="Template Name")
        self.templates_tree.heading("Marker IDs", text="Marker IDs")
        self.templates_tree.heading("Created", text="Created Date")
        self.templates_tree.heading("Status", text="Status")

        self.templates_tree.column("Name", width=150)
        self.templates_tree.column("Marker IDs", width=120)
        self.templates_tree.column("Created", width=120)
        self.templates_tree.column("Status", width=80)

        # Bind selection event
        self.templates_tree.bind("<<TreeviewSelect>>", self.on_template_selected)

        # Scrollbars for the treeview
        tree_scroll_y = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.templates_tree.yview
        )
        tree_scroll_x = ttk.Scrollbar(
            list_frame, orient=tk.HORIZONTAL, command=self.templates_tree.xview
        )
        self.templates_tree.configure(
            yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set
        )

        # Pack treeview and scrollbars
        self.templates_tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")

        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        # Right panel - Template preview
        right_panel = ttk.Frame(paned_window)
        paned_window.add(right_panel, weight=1)

        # Template preview section
        preview_frame = ttk.LabelFrame(
            right_panel, text="Template Preview", padding="10"
        )
        preview_frame.pack(fill=tk.BOTH, expand=True)

        # Template canvas for preview
        self.db_template_canvas = PreviewCanvas(preview_frame, width=400, height=300)
        self.db_template_canvas.pack(fill=tk.BOTH, expand=True)

        # Template details section
        details_frame = ttk.LabelFrame(
            right_panel, text="Template Details", padding="10"
        )
        details_frame.pack(fill=tk.X, pady=(10, 0))

        # Details labels
        self.template_name_detail = ttk.Label(details_frame, text="Name: -")
        self.template_name_detail.pack(anchor=tk.W, pady=1)

        self.template_ids_detail = ttk.Label(details_frame, text="Marker IDs: -")
        self.template_ids_detail.pack(anchor=tk.W, pady=1)

        self.template_size_detail = ttk.Label(details_frame, text="Size: -")
        self.template_size_detail.pack(anchor=tk.W, pady=1)

        self.template_date_detail = ttk.Label(details_frame, text="Created: -")
        self.template_date_detail.pack(anchor=tk.W, pady=1)

        self.template_path_detail = ttk.Label(details_frame, text="Path: -")
        self.template_path_detail.pack(anchor=tk.W, pady=1)

        # Action buttons section
        action_frame = ttk.Frame(main_container)
        action_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            action_frame, text="View Full Size", command=self.view_selected_template
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            action_frame, text="Delete Template", command=self.delete_selected_template
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            action_frame, text="Export Template", command=self.export_selected_template
        ).pack(side=tk.LEFT)

        # Info section
        info_frame = ttk.LabelFrame(
            main_container, text="Database Information", padding="10"
        )
        info_frame.pack(fill=tk.X, pady=(10, 0))

        self.db_info_label = ttk.Label(
            info_frame, text="Click 'Refresh' to load templates from database"
        )
        self.db_info_label.pack(anchor=tk.W)

        # Initial load of templates
        self.refresh_templates_list()

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
                # Create mask overlay on template using krathong image positioning + mask adjustments

                # Get krathong image position for reference (but don't scale mask by krathong scale)
                height, width = self.cropped_image.shape[:2]

                # Get drawing area (same as krathong placement)
                drawing_area = self.template_creator._get_drawing_area()
                x1, y1, x2, y2 = drawing_area
                drawing_width = x2 - x1
                drawing_height = y2 - y1

                # Calculate krathong center position for reference
                center_x = x1 + drawing_width // 2
                center_y = y1 + drawing_height // 2

                # Get current template settings for krathong position
                settings = self.get_template_settings()
                krathong_start_x = (
                    center_x - int(width * settings.scale) // 2 + settings.offset_x
                )
                krathong_start_y = (
                    center_y - int(height * settings.scale) // 2 + settings.offset_y
                )

                # Ensure krathong bounds
                krathong_start_x = max(
                    x1,
                    min(
                        krathong_start_x,
                        x1 + drawing_width - int(width * settings.scale),
                    ),
                )
                krathong_start_y = max(
                    y1,
                    min(
                        krathong_start_y,
                        y1 + drawing_height - int(height * settings.scale),
                    ),
                )

                # Now apply mask-specific adjustments (independent of krathong scale)
                mask_scale = self.mask_adjustment_controls.get_value("mask_scale")
                mask_offset_x = self.mask_adjustment_controls.get_value("mask_offset_x")
                mask_offset_y = self.mask_adjustment_controls.get_value("mask_offset_y")

                # Use mask's original dimensions as base, only scaled by mask_scale
                mask_height, mask_width = self.mask_image.shape[:2]
                final_mask_width = max(1, int(mask_width * mask_scale))
                final_mask_height = max(1, int(mask_height * mask_scale))

                # Position mask relative to krathong center, with mask-specific offsets
                mask_center_x = (
                    krathong_start_x + int(width * settings.scale) // 2 + mask_offset_x
                )
                mask_center_y = (
                    krathong_start_y + int(height * settings.scale) // 2 + mask_offset_y
                )

                mask_start_x = int(mask_center_x - final_mask_width // 2)
                mask_start_y = int(mask_center_y - final_mask_height // 2)
                mask_end_x = mask_start_x + final_mask_width
                mask_end_y = mask_start_y + final_mask_height

                # Ensure mask bounds are within image
                mask_start_x = max(0, mask_start_x)
                mask_start_y = max(0, mask_start_y)
                mask_end_x = min(display_image.shape[1], mask_end_x)
                mask_end_y = min(display_image.shape[0], mask_end_y)

                actual_width = mask_end_x - mask_start_x
                actual_height = mask_end_y - mask_start_y

                if actual_width > 0 and actual_height > 0:
                    # Resize mask to match final dimensions
                    mask_resized = cv2.resize(
                        self.mask_image, (final_mask_width, final_mask_height)
                    )

                    # Resize mask to fit actual bounds if needed
                    if (
                        actual_width != final_mask_width
                        or actual_height != final_mask_height
                    ):
                        mask_final = cv2.resize(
                            mask_resized, (actual_width, actual_height)
                        )
                    else:
                        mask_final = mask_resized

                    # Create colored mask overlay (bright semi-transparent red)
                    mask_overlay = np.zeros(
                        (display_image.shape[0], display_image.shape[1], 3),
                        dtype=np.uint8,
                    )
                    # Use bright red color (BGR format: Blue, Green, Red)
                    mask_overlay[
                        mask_start_y:mask_end_y, mask_start_x:mask_end_x
                    ] = cv2.merge(
                        [
                            np.zeros_like(mask_final),  # Blue: 0
                            np.zeros_like(mask_final),  # Green: 0
                            mask_final,  # Red: mask values
                        ]
                    )

                    # Blend with template - increased visibility
                    alpha = 0.2  # Semi-transparent overlay
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
            # Continue gracefully - don't break the UI

    def schedule_template_preview_update(self):
        """Schedule a throttled template preview update to prevent flickering."""
        if self.update_timer:
            self.root.after_cancel(self.update_timer)

        # Schedule update after a small delay to prevent rapid firing
        self.update_timer = self.root.after(100, self.update_template_preview)

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
        # Use throttled update to prevent flickering
        self.schedule_template_preview_update()

    def on_mask_adjustment_change(self, value):
        """Handle mask adjustment control changes."""
        # Update immediately for responsive feedback
        self.preview_template()
        # Also use throttled update to prevent flickering during rapid adjustments
        self.schedule_template_preview_update()

    def on_mask_overlay_toggle(self):
        """Handle mask overlay toggle."""
        # Update template preview when mask overlay is toggled
        self.schedule_template_preview_update()

    def suggest_available_ids(self):
        """Suggest available marker IDs based on database."""
        try:
            if not self.db_registry:
                self.id_status_label.config(
                    text="Database not connected", foreground="red"
                )
                return

            # Get used marker IDs from database
            used_ids = set(self.db_registry.get_used_marker_ids())

            # Find available IDs (20-49 for ArUco 4x4_50, excluding hardcoded 0-19)
            available_ids = []
            for i in range(20, 50):  # Start from 20 to avoid hardcoded range
                if i not in used_ids:
                    available_ids.append(i)

            if len(available_ids) >= 4:
                # Suggest first 4 available IDs
                suggested_ids = available_ids[:4]

                # Update the marker variables
                for i, marker_id in enumerate(suggested_ids):
                    self.marker_vars[i].set(marker_id)

                self.id_status_label.config(
                    text=f"Suggested IDs: {', '.join(map(str, suggested_ids))}",
                    foreground="green",
                )

                # Update status for all IDs
                for i in range(4):
                    self.check_marker_id_status(i)

            else:
                self.id_status_label.config(
                    text=f"Only {len(available_ids)} IDs available", foreground="orange"
                )

        except Exception as e:
            self.logger.error(f"Error suggesting IDs: {e}")
            self.id_status_label.config(
                text="Error checking database", foreground="red"
            )

    def check_marker_id_status(self, index):
        """Check if a specific marker ID is already in use."""
        try:
            if not self.db_registry or index >= len(self.marker_vars):
                return

            marker_id = self.marker_vars[index].get()
            used_ids = set(self.db_registry.get_used_marker_ids())

            if marker_id in used_ids:
                self.marker_status_labels[index].config(
                    text="⚠️ In Use", foreground="red"
                )
            else:
                self.marker_status_labels[index].config(
                    text="✅ Available", foreground="green"
                )

        except Exception as e:
            self.logger.error(f"Error checking marker ID status: {e}")
            self.marker_status_labels[index].config(text="❓ Unknown", foreground="gray")

    def refresh_templates_list(self):
        """Refresh the templates list from database."""
        try:
            if not self.db_registry:
                self.db_info_label.config(text="Database not connected")
                return

            # Clear existing items
            for item in self.templates_tree.get_children():
                self.templates_tree.delete(item)

            # Get templates from database
            templates = self.db_registry.get_templates()

            if not templates:
                self.db_info_label.config(text="No templates found in database")
                return

            # Populate the tree
            for template in templates:
                marker_ids_str = ", ".join(map(str, template.marker_ids))
                status = "Active" if template.is_active else "Inactive"

                # Format date
                try:
                    from datetime import datetime

                    created_date = datetime.fromisoformat(template.created_at).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                except:
                    created_date = template.created_at

                self.templates_tree.insert(
                    "",
                    "end",
                    values=(template.name, marker_ids_str, created_date, status),
                )

            self.db_info_label.config(
                text=f"Found {len(templates)} templates in database"
            )

        except Exception as e:
            self.logger.error(f"Error refreshing templates list: {e}")
            self.db_info_label.config(text=f"Error loading templates: {e}")

    def on_template_selected(self, event):
        """Handle template selection in the database templates tab."""
        try:
            selected_item = self.templates_tree.selection()
            if not selected_item:
                self.clear_template_preview()
                return

            # Get selected template name
            template_name = self.templates_tree.item(selected_item[0])["values"][0]

            # Get template from database
            template = self.db_registry.get_template_by_name(template_name)
            if not template:
                self.clear_template_preview()
                return

            # Update template details
            self.update_template_details(template)

            # Load and display template image
            self.load_template_image(template)

        except Exception as e:
            self.logger.error(f"Error handling template selection: {e}")
            self.clear_template_preview()

    def update_template_details(self, template):
        """Update the template details panel."""
        try:
            marker_ids_str = ", ".join(map(str, template.marker_ids))

            # Format date
            try:
                from datetime import datetime

                created_date = datetime.fromisoformat(template.created_at).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            except:
                created_date = template.created_at

            self.template_name_detail.config(text=f"Name: {template.name}")
            self.template_ids_detail.config(text=f"Marker IDs: {marker_ids_str}")
            self.template_size_detail.config(
                text=f"Size: {template.template_width}x{template.template_height}"
            )
            self.template_date_detail.config(text=f"Created: {created_date}")
            self.template_path_detail.config(text=f"Path: {template.image_path}")

        except Exception as e:
            self.logger.error(f"Error updating template details: {e}")

    def load_template_image(self, template):
        """Load and display template image in preview canvas."""
        try:
            from pathlib import Path

            import cv2

            # Check if image file exists
            image_path = Path(template.image_path)
            if not image_path.exists():
                # Try relative path from project root
                project_root = Path(__file__).parent.parent.parent
                image_path = project_root / template.image_path

            if image_path.exists():
                # Load image
                image = cv2.imread(str(image_path))
                if image is not None:
                    self.db_template_canvas.display_image(image)
                    self.template_size_detail.config(
                        text=f"Size: {image.shape[1]}x{image.shape[0]} ({template.template_width}x{template.template_height})"
                    )
                else:
                    self.show_template_not_found()
            else:
                self.show_template_not_found()

        except Exception as e:
            self.logger.error(f"Error loading template image: {e}")
            self.show_template_not_found()

    def show_template_not_found(self):
        """Show placeholder when template image is not found."""
        import numpy as np

        # Create a placeholder image
        placeholder = np.ones((300, 400, 3), dtype=np.uint8) * 240

        # Add text to placeholder
        cv2.putText(
            placeholder,
            "Template Image",
            (120, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (100, 100, 100),
            2,
        )
        cv2.putText(
            placeholder,
            "Not Found",
            (140, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (100, 100, 100),
            2,
        )

        self.db_template_canvas.display_image(placeholder)

    def clear_template_preview(self):
        """Clear the template preview and details."""
        # Clear details
        self.template_name_detail.config(text="Name: -")
        self.template_ids_detail.config(text="Marker IDs: -")
        self.template_size_detail.config(text="Size: -")
        self.template_date_detail.config(text="Created: -")
        self.template_path_detail.config(text="Path: -")

        # Clear image preview
        import numpy as np

        placeholder = np.ones((300, 400, 3), dtype=np.uint8) * 250
        cv2.putText(
            placeholder,
            "Select Template",
            (120, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (150, 150, 150),
            2,
        )
        cv2.putText(
            placeholder,
            "to Preview",
            (130, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (150, 150, 150),
            2,
        )
        self.db_template_canvas.display_image(placeholder)

    def view_selected_template(self):
        """View full-size template in popup window."""
        try:
            selected_item = self.templates_tree.selection()
            if not selected_item:
                messagebox.showwarning("Warning", "Please select a template to view")
                return

            template_name = self.templates_tree.item(selected_item[0])["values"][0]
            template = self.db_registry.get_template_by_name(template_name)

            if not template:
                messagebox.showerror("Error", "Template not found in database")
                return

            # Create popup window
            popup = tk.Toplevel(self.root)
            popup.title(f"Full Template View: {template.name}")
            popup.geometry("800x600")
            popup.transient(self.root)
            popup.grab_set()

            # Main container
            main_frame = ttk.Frame(popup)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Template info header
            info_frame = ttk.LabelFrame(
                main_frame, text="Template Information", padding="10"
            )
            info_frame.pack(fill=tk.X, pady=(0, 10))

            marker_ids_str = ", ".join(map(str, template.marker_ids))

            ttk.Label(
                info_frame, text=f"Name: {template.name}", font=("Arial", 10, "bold")
            ).pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Marker IDs: {marker_ids_str}").pack(
                anchor=tk.W
            )
            ttk.Label(
                info_frame,
                text=f"Size: {template.template_width} x {template.template_height}",
            ).pack(anchor=tk.W)
            ttk.Label(
                info_frame,
                text=f"Status: {'Active' if template.is_active else 'Inactive'}",
            ).pack(anchor=tk.W)

            # Template image frame
            image_frame = ttk.LabelFrame(
                main_frame, text="Template Image", padding="10"
            )
            image_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            # Full-size template canvas
            full_canvas = PreviewCanvas(image_frame, width=760, height=400)
            full_canvas.pack(fill=tk.BOTH, expand=True)

            # Load and display full-size image
            try:
                from pathlib import Path

                import cv2

                image_path = Path(template.image_path)
                if not image_path.exists():
                    project_root = Path(__file__).parent.parent.parent
                    image_path = project_root / template.image_path

                if image_path.exists():
                    image = cv2.imread(str(image_path))
                    if image is not None:
                        full_canvas.display_image(image, fit_to_canvas=True)
                    else:
                        self.show_image_not_found_popup(full_canvas)
                else:
                    self.show_image_not_found_popup(full_canvas)

            except Exception as e:
                self.logger.error(f"Error loading full template image: {e}")
                self.show_image_not_found_popup(full_canvas)

            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X)

            ttk.Button(button_frame, text="Close", command=popup.destroy).pack(
                side=tk.RIGHT
            )

            # Center the popup
            popup.update_idletasks()
            x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
            y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
            popup.geometry(f"+{x}+{y}")

        except Exception as e:
            self.logger.error(f"Error viewing template: {e}")
            messagebox.showerror("Error", f"Failed to view template: {e}")

    def show_image_not_found_popup(self, canvas):
        """Show image not found in popup canvas."""
        import numpy as np

        placeholder = np.ones((400, 600, 3), dtype=np.uint8) * 240
        cv2.putText(
            placeholder,
            "Template Image Not Found",
            (150, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (100, 100, 100),
            2,
        )
        cv2.putText(
            placeholder,
            "File may have been moved or deleted",
            (120, 220),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (150, 150, 150),
            1,
        )
        canvas.display_image(placeholder)

    def delete_selected_template(self):
        """Delete the selected template from database."""
        try:
            selected_item = self.templates_tree.selection()
            if not selected_item:
                messagebox.showwarning("Warning", "Please select a template to delete")
                return

            template_name = self.templates_tree.item(selected_item[0])["values"][0]

            # Confirm deletion
            response = messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to delete template '{template_name}'?\n\n"
                "This action cannot be undone.",
            )

            if not response:
                return

            # Delete from database
            success = self.db_registry.delete_template(template_name)

            if success:
                messagebox.showinfo(
                    "Success", f"Template '{template_name}' deleted successfully"
                )
                self.refresh_templates_list()  # Refresh the list
            else:
                messagebox.showerror(
                    "Error", f"Failed to delete template '{template_name}'"
                )

        except Exception as e:
            self.logger.error(f"Error deleting template: {e}")
            messagebox.showerror("Error", f"Failed to delete template: {e}")

    def export_selected_template(self):
        """Export the selected template files."""
        try:
            selected_item = self.templates_tree.selection()
            if not selected_item:
                messagebox.showwarning("Warning", "Please select a template to export")
                return

            template_name = self.templates_tree.item(selected_item[0])["values"][0]
            template = self.db_registry.get_template_by_name(template_name)

            if not template:
                messagebox.showerror("Error", "Template not found in database")
                return

            # Choose export directory
            from tkinter import filedialog

            export_dir = filedialog.askdirectory(title="Select Export Directory")

            if not export_dir:
                return

            export_path = Path(export_dir)
            template_folder = export_path / f"template_{template.name}"
            template_folder.mkdir(exist_ok=True)

            # Copy template files if they exist
            import shutil

            files_exported = []

            if Path(template.image_path).exists():
                shutil.copy2(
                    template.image_path,
                    template_folder / f"{template.name}_template.png",
                )
                files_exported.append("Template image")

            if Path(template.mask_path).exists():
                shutil.copy2(
                    template.mask_path, template_folder / f"{template.name}_mask.png"
                )
                files_exported.append("Mask image")

            # Create info file
            info_file = template_folder / f"{template.name}_info.txt"
            with open(info_file, "w") as f:
                f.write(f"Template Name: {template.name}\n")
                f.write(f"Marker IDs: {', '.join(map(str, template.marker_ids))}\n")
                f.write(
                    f"Size: {template.template_width} x {template.template_height}\n"
                )
                f.write(f"Created: {template.created_at}\n")
                f.write(f"Status: {'Active' if template.is_active else 'Inactive'}\n")

            files_exported.append("Template info")

            messagebox.showinfo(
                "Export Complete",
                f"Template '{template.name}' exported successfully!\n\n"
                f"Location: {template_folder}\n"
                f"Files: {', '.join(files_exported)}",
            )

        except Exception as e:
            self.logger.error(f"Error exporting template: {e}")
            messagebox.showerror("Error", f"Failed to export template: {e}")

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

                    # Apply mask overlay if checkbox is checked
                    display_image = template_image.copy()
                    print(
                        f"DEBUG: template_show_mask_var.get() = {self.template_show_mask_var.get()}"
                    )
                    print(
                        f"DEBUG: hasattr(self, 'mask_image') = {hasattr(self, 'mask_image')}"
                    )
                    print(
                        f"DEBUG: self.mask_image is not None = {self.mask_image is not None if hasattr(self, 'mask_image') else 'N/A'}"
                    )
                    if (
                        self.template_show_mask_var.get()
                        and hasattr(self, "mask_image")
                        and self.mask_image is not None
                    ):
                        print("DEBUG: Applying mask overlay")
                        # Create mask overlay on template using krathong image positioning + mask adjustments

                        # Get krathong image position for reference (but don't scale mask by krathong scale)
                        height, width = self.cropped_image.shape[:2]

                        # Get drawing area (same as krathong placement)
                        drawing_area = self.template_creator._get_drawing_area()
                        x1, y1, x2, y2 = drawing_area
                        drawing_width = x2 - x1
                        drawing_height = y2 - y1

                        # Calculate krathong center position for reference
                        center_x = x1 + drawing_width // 2
                        center_y = y1 + drawing_height // 2

                        krathong_start_x = (
                            center_x
                            - int(width * settings.scale) // 2
                            + settings.offset_x
                        )
                        krathong_start_y = (
                            center_y
                            - int(height * settings.scale) // 2
                            + settings.offset_y
                        )

                        # Ensure krathong bounds
                        krathong_start_x = max(
                            x1,
                            min(
                                krathong_start_x,
                                x1 + drawing_width - int(width * settings.scale),
                            ),
                        )
                        krathong_start_y = max(
                            y1,
                            min(
                                krathong_start_y,
                                y1 + drawing_height - int(height * settings.scale),
                            ),
                        )

                        # Now apply mask-specific adjustments (independent of krathong scale)
                        mask_scale = self.mask_adjustment_controls.get_value(
                            "mask_scale"
                        )
                        mask_offset_x = self.mask_adjustment_controls.get_value(
                            "mask_offset_x"
                        )
                        mask_offset_y = self.mask_adjustment_controls.get_value(
                            "mask_offset_y"
                        )

                        # Use mask's original dimensions as base, only scaled by mask_scale
                        mask_height, mask_width = self.mask_image.shape[:2]
                        final_mask_width = max(1, int(mask_width * mask_scale))
                        final_mask_height = max(1, int(mask_height * mask_scale))

                        # Position mask relative to krathong center, with mask-specific offsets
                        mask_center_x = (
                            krathong_start_x
                            + int(width * settings.scale) // 2
                            + mask_offset_x
                        )
                        mask_center_y = (
                            krathong_start_y
                            + int(height * settings.scale) // 2
                            + mask_offset_y
                        )

                        mask_start_x = int(mask_center_x - final_mask_width // 2)
                        mask_start_y = int(mask_center_y - final_mask_height // 2)
                        mask_end_x = mask_start_x + final_mask_width
                        mask_end_y = mask_start_y + final_mask_height

                        print(
                            f"DEBUG: Krathong position: ({krathong_start_x}, {krathong_start_y}) {int(width * settings.scale)}x{int(height * settings.scale)}"
                        )
                        print(
                            f"DEBUG: Mask adjustments: scale={mask_scale}, offset=({mask_offset_x}, {mask_offset_y})"
                        )
                        print(
                            f"DEBUG: Final mask: ({mask_start_x}, {mask_start_y}) to ({mask_end_x}, {mask_end_y})"
                        )

                        # Resize mask to match final dimensions
                        mask_resized = cv2.resize(
                            self.mask_image, (final_mask_width, final_mask_height)
                        )

                        # Create colored mask overlay (bright semi-transparent red)
                        mask_overlay = np.zeros(
                            (display_image.shape[0], display_image.shape[1], 3),
                            dtype=np.uint8,
                        )

                        # Ensure mask bounds are within image
                        mask_start_x = max(0, mask_start_x)
                        mask_start_y = max(0, mask_start_y)
                        mask_end_x = min(display_image.shape[1], mask_end_x)
                        mask_end_y = min(display_image.shape[0], mask_end_y)

                        actual_width = mask_end_x - mask_start_x
                        actual_height = mask_end_y - mask_start_y

                        if actual_width > 0 and actual_height > 0:
                            # Resize mask to fit actual bounds
                            mask_final = cv2.resize(
                                mask_resized, (actual_width, actual_height)
                            )

                            # Apply red overlay where mask is active
                            mask_overlay[
                                mask_start_y:mask_end_y, mask_start_x:mask_end_x
                            ] = cv2.merge(
                                [
                                    np.zeros_like(mask_final),  # Blue: 0
                                    np.zeros_like(mask_final),  # Green: 0
                                    mask_final,  # Red: mask values
                                ]
                            )

                            # Blend with template
                            display_image = cv2.addWeighted(
                                display_image, 0.8, mask_overlay, 0.2, 0
                            )
                            print("DEBUG: Mask overlay applied successfully")
                        else:
                            print("DEBUG: Mask has zero size, skipping overlay")
                    else:
                        print("DEBUG: Mask overlay conditions not met")

                    self.template_canvas.display_image(display_image)
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

                # Save to database if available
                db_saved = False
                if self.db_registry is not None and TemplateData is not None:
                    try:
                        # Create TemplateData object
                        template_data = TemplateData(
                            name=settings.template_name,
                            marker_ids=settings.marker_ids,
                            image_path=str(
                                Path(settings.output_dir)
                                / f"{settings.template_name}.png"
                            ),
                            mask_path=str(
                                Path(settings.output_dir)
                                / f"{settings.template_name}_mask.png"
                            )
                            if self.mask_image is not None
                            else "",
                            template_width=template_image.shape[1],
                            template_height=template_image.shape[0],
                        )

                        # Save to database
                        success = self.db_registry.save_template(template_data)
                        if success:
                            db_saved = True
                            self.logger.info(
                                f"Template '{settings.template_name}' saved to database"
                            )
                        else:
                            self.logger.warning(
                                f"Failed to save template '{settings.template_name}' to database"
                            )
                    except Exception as e:
                        self.logger.error(f"Database save error: {e}")

                # Update status and show success message
                self.update_status("Template created successfully", 100)

                success_msg = (
                    f"Template '{settings.template_name}' created successfully!\n\n"
                )
                success_msg += f"📁 Files saved to: {settings.output_dir}\n"
                if db_saved:
                    success_msg += "💾 Saved to database (scanner.db)\n"
                    success_msg += "✅ Template is immediately available to scanner"
                else:
                    success_msg += (
                        "⚠️ Database save failed - template only saved as files"
                    )

                show_info_dialog(self.root, "Success", success_msg)
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

            # Check for uniqueness
            if len(set(marker_ids)) != 4:
                show_error_dialog(self.root, "Error", "All 4 marker IDs must be unique")
                return False

            # Check for conflicts with existing templates (if database connected)
            if self.db_registry:
                used_ids = set(self.db_registry.get_used_marker_ids())
                conflicting_ids = [id for id in marker_ids if id in used_ids]

                if conflicting_ids:
                    response = messagebox.askyesno(
                        "Warning",
                        f"Marker IDs {conflicting_ids} are already in use by other templates.\n\n"
                        "This may cause detection conflicts. Do you want to continue anyway?\n\n"
                        "Click 'Suggest Available IDs' to get unused marker IDs.",
                    )
                    if not response:
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

    # === Database Management Methods ===

    def initialize_database_path(self):
        """Initialize database path on startup."""
        try:
            # Import path utilities
            from path_utils import find_scanner_database_locations, get_database_path

            # Try to find scanner database first
            scanner_dbs = find_scanner_database_locations()
            if scanner_dbs:
                # Use first found scanner database
                self.db_path_var.set(str(scanner_dbs[0]))
                self.update_status(f"Found scanner database: {scanner_dbs[0].name}")
            else:
                # Fall back to default path
                default_db = get_database_path()
                self.db_path_var.set(str(default_db))
                self.update_status("Using default database location")

            # Update template manager with new database path
            self.update_template_manager_database()
            self.check_database_connection()

        except Exception as e:
            self.logger.error(f"Failed to initialize database path: {e}")
            self.update_status("Database initialization failed")

    def browse_database_file(self):
        """Open file dialog to select database file."""
        try:
            from tkinter import filedialog

            file_path = filedialog.askopenfilename(
                title="Select Scanner Database File",
                filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
                initialdir=self.db_path_var.get()
                if self.db_path_var.get()
                else str(Path.cwd()),
            )

            if file_path:
                # Validate database file
                from path_utils import get_custom_database_path

                try:
                    validated_path = get_custom_database_path(file_path)
                    self.db_path_var.set(str(validated_path))
                    self.update_template_manager_database()
                    self.check_database_connection()
                    self.update_status(f"Database updated: {validated_path.name}")
                except (FileNotFoundError, ValueError) as e:
                    show_error_dialog(self.root, "Invalid Database", str(e))

        except Exception as e:
            self.logger.error(f"Failed to browse database file: {e}")
            show_error_dialog(self.root, "Error", f"Failed to select database: {e}")

    def auto_find_scanner_db(self):
        """Automatically find scanner database."""
        try:
            from path_utils import find_scanner_database_locations

            scanner_dbs = find_scanner_database_locations()
            if not scanner_dbs:
                from tkinter import messagebox

                messagebox.showinfo(
                    "No Scanner Database",
                    "No scanner database found. Make sure the scanner application is installed or choose a database file manually.",
                )
                return

            if len(scanner_dbs) == 1:
                # Single database found - use it
                self.db_path_var.set(str(scanner_dbs[0]))
                self.update_template_manager_database()
                self.check_database_connection()
                self.update_status(f"Scanner database found: {scanner_dbs[0].name}")
            else:
                # Multiple databases found - let user choose
                self.show_database_selection_dialog(scanner_dbs)

        except Exception as e:
            self.logger.error(f"Failed to auto-find scanner database: {e}")
            show_error_dialog(
                self.root, "Error", f"Failed to find scanner database: {e}"
            )

    def show_database_selection_dialog(self, database_paths):
        """Show dialog to select from multiple found databases."""
        from tkinter import messagebox

        dialog = tk.Toplevel(self.root)
        dialog.title("Select Scanner Database")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_reqwidth() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_reqheight() // 2)
        dialog.geometry(f"+{x}+{y}")

        from tkinter import ttk

        ttk.Label(
            dialog,
            text="Multiple scanner databases found. Please select one:",
            font=("Arial", 11),
        ).pack(pady=10)

        # Listbox with scrollbar
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(
            list_frame, yscrollcommand=scrollbar.set, font=("Arial", 10)
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        # Populate listbox
        for db_path in database_paths:
            listbox.insert(tk.END, str(db_path))

        if database_paths:
            listbox.selection_set(0)  # Select first item

        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)

        def select_database():
            selection = listbox.curselection()
            if selection:
                selected_path = database_paths[selection[0]]
                self.db_path_var.set(str(selected_path))
                self.update_template_manager_database()
                self.check_database_connection()
                dialog.destroy()

        ttk.Button(btn_frame, text="Select", command=select_database).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(
            side=tk.LEFT, padx=5
        )

    def create_new_database(self):
        """Create a new database file."""
        try:
            from tkinter import filedialog

            file_path = filedialog.asksaveasfilename(
                title="Create New Database File",
                defaultextension=".db",
                filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
                initialfilename="scanner.db",
            )

            if file_path:
                # Create new database
                import sqlite3

                Path(file_path).parent.mkdir(parents=True, exist_ok=True)

                # Create database with proper schema
                from apps.scanner.template_manager import TemplateManager

                temp_manager = TemplateManager(str(file_path))
                temp_manager.connection.close()  # Close the connection

                self.db_path_var.set(file_path)
                self.update_template_manager_database()
                self.check_database_connection()
                self.update_status(f"New database created: {Path(file_path).name}")

        except Exception as e:
            self.logger.error(f"Failed to create new database: {e}")
            show_error_dialog(self.root, "Error", f"Failed to create database: {e}")

    def update_template_manager_database(self):
        """Update template manager with current database path."""
        try:
            # Reinitialize database registry with new path
            db_path = self.db_path_var.get()
            if db_path and LocalTemplateRegistry is not None:
                self.db_registry = LocalTemplateRegistry(db_path)
                self.logger.info(f"Database registry updated with database: {db_path}")
        except Exception as e:
            self.logger.error(f"Failed to update database registry: {e}")
            self.db_registry = None

    def check_database_connection(self):
        """Check database connection status."""
        try:
            # Test database connection
            if self.db_registry:
                templates = self.db_registry.get_templates()
                count = len(templates)
                self.db_status_label.configure(
                    text=f"✅ Connected - {count} templates", foreground="green"
                )
            else:
                self.db_status_label.configure(
                    text="❌ Database error", foreground="red"
                )

        except Exception as e:
            self.db_status_label.configure(text="❌ Database error", foreground="red")
            self.logger.error(f"Database connection error: {e}")

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
