"""
Unified Template Creator GUI

This module provides a single, streamlined interface that combines
template creation, editing, and database management into one application.
No more switching between separate tools!

Key Features:
- Interactive template creation with real-time preview
- Integrated database storage (saves directly to scanner.db)
- File export for distribution/backup
- Intelligent marker ID management
- Simplified user experience

Author: KrathongScanner Team
"""

import logging

# Import existing components
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from PIL import Image, ImageTk

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.scanner.template_manager import TemplateManager
from apps.template_maker.export import TemplateExporter
from database.models import TemplateData


class UnifiedTemplateCreatorGUI:
    """
    Unified Template Creator - Single application for template workflow.

    Combines template creation + database storage + file export
    into one streamlined interface.
    """

    def __init__(self):
        """Initialize the unified template creator."""
        self.logger = logging.getLogger(__name__)

        # Initialize backend components
        self.template_manager = TemplateManager()
        self.template_exporter = TemplateExporter()

        # UI state
        self.current_image = None
        self.current_mask = None
        self.crop_coords = None
        self.marker_ids = None

        # Create main window
        self.root = tk.Tk()
        self.root.title("🎯 Unified Template Creator - KrathongScanner")
        self.root.geometry("1400x900")
        self.root.configure(bg="#f0f0f0")

        # Setup UI
        self.setup_ui()
        self.setup_bindings()

        # Initialize status
        self.update_status("Ready to create templates", "info")

        self.logger.info("Unified Template Creator GUI initialized")

    def setup_ui(self):
        """Setup the main user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Left panel - Template Creation
        self.setup_creation_panel(main_frame)

        # Right panel - Configuration & Actions
        self.setup_config_panel(main_frame)

        # Bottom panel - Status & Progress
        self.setup_status_panel(main_frame)

        # Initialize database path after all UI is set up
        self.initialize_database_path()

    def setup_creation_panel(self, parent):
        """Setup the template creation panel (left side)."""
        # Creation panel frame
        creation_frame = ttk.LabelFrame(
            parent, text="📱 Template Creation", padding="10"
        )
        creation_frame.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5)
        )
        creation_frame.columnconfigure(0, weight=1)
        creation_frame.rowconfigure(1, weight=1)

        # Image loading section
        load_frame = ttk.Frame(creation_frame)
        load_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        load_frame.columnconfigure(1, weight=1)

        ttk.Button(load_frame, text="📂 Load Image", command=self.load_image).grid(
            row=0, column=0, padx=(0, 10)
        )

        self.image_path_label = ttk.Label(load_frame, text="No image loaded")
        self.image_path_label.grid(row=0, column=1, sticky=(tk.W, tk.E))

        # Image preview and editing canvas
        self.canvas_frame = ttk.Frame(creation_frame)
        self.canvas_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(0, weight=1)

        # Create canvas with scrollbars
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg="white",
            width=600,
            height=400,
            scrollregion=(0, 0, 1000, 1000),
        )

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(
            self.canvas_frame, orient="vertical", command=self.canvas.yview
        )
        h_scrollbar = ttk.Scrollbar(
            self.canvas_frame, orient="horizontal", command=self.canvas.xview
        )

        self.canvas.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Grid layout for canvas and scrollbars
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Cropping controls
        crop_frame = ttk.Frame(creation_frame)
        crop_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        ttk.Button(
            crop_frame, text="✂️ Start Cropping", command=self.start_cropping
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(crop_frame, text="🎭 Generate Mask", command=self.generate_mask).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        ttk.Button(
            crop_frame, text="👁️ Preview Template", command=self.preview_template
        ).pack(side=tk.LEFT)

    def setup_config_panel(self, parent):
        """Setup the configuration panel (right side)."""
        # Configuration panel frame
        config_frame = ttk.LabelFrame(
            parent, text="⚙️ Template Configuration", padding="10"
        )
        config_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        config_frame.columnconfigure(0, weight=1)

        row = 0

        # Template name
        ttk.Label(config_frame, text="Template Name:").grid(
            row=row, column=0, sticky=tk.W, pady=(0, 5)
        )
        row += 1

        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(
            config_frame, textvariable=self.name_var, font=("Arial", 11)
        )
        name_entry.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        name_entry.bind("<KeyRelease>", self.on_name_changed)
        row += 1

        # Marker ID section
        marker_frame = ttk.LabelFrame(
            config_frame, text="🎯 ArUco Markers", padding="10"
        )
        marker_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        marker_frame.columnconfigure(0, weight=1)
        row += 1

        # Auto assign markers
        self.auto_markers_var = tk.BooleanVar(value=True)
        auto_check = ttk.Checkbutton(
            marker_frame,
            text="Auto-assign marker IDs",
            variable=self.auto_markers_var,
            command=self.toggle_marker_assignment,
        )
        auto_check.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        # Manual marker assignment (initially disabled)
        self.marker_frame = ttk.Frame(marker_frame)
        self.marker_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))

        self.marker_vars = []
        for i in range(4):
            ttk.Label(self.marker_frame, text=f"Marker {i+1}:").grid(
                row=i, column=0, sticky=tk.W
            )
            var = tk.StringVar()
            entry = ttk.Entry(
                self.marker_frame, textvariable=var, width=10, state="disabled"
            )
            entry.grid(row=i, column=1, padx=(5, 0), pady=1)
            self.marker_vars.append(var)

        # Available markers info
        self.marker_info_label = ttk.Label(
            marker_frame, text="Available: 20-49 (30 markers)", foreground="green"
        )
        self.marker_info_label.grid(row=2, column=0, sticky=tk.W, pady=(10, 0))

        # Template dimensions
        dim_frame = ttk.LabelFrame(config_frame, text="📏 Dimensions", padding="10")
        dim_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        row += 1

        ttk.Label(dim_frame, text="Width:").grid(row=0, column=0, sticky=tk.W)
        self.width_var = tk.StringVar(value="1270")
        ttk.Entry(dim_frame, textvariable=self.width_var, width=10).grid(
            row=0, column=1, padx=(5, 10)
        )

        ttk.Label(dim_frame, text="Height:").grid(row=0, column=2, sticky=tk.W)
        self.height_var = tk.StringVar(value="720")
        ttk.Entry(dim_frame, textvariable=self.height_var, width=10).grid(
            row=0, column=3, padx=(5, 0)
        )

        # Export options
        export_frame = ttk.LabelFrame(
            config_frame, text="📤 Export Options", padding="10"
        )
        export_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        row += 1

        self.save_to_db_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            export_frame,
            text="💾 Save to Database (scanner.db)",
            variable=self.save_to_db_var,
        ).pack(anchor=tk.W)

        self.export_files_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            export_frame,
            text="📁 Export files (backup/distribution)",
            variable=self.export_files_var,
        ).pack(anchor=tk.W)

        # Action buttons
        action_frame = ttk.LabelFrame(config_frame, text="🚀 Actions", padding="10")
        action_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        action_frame.columnconfigure(0, weight=1)
        row += 1

        # Main action button
        self.main_action_btn = ttk.Button(
            action_frame,
            text="💾 Create Template",
            command=self.create_template,
            style="Accent.TButton",
        )
        self.main_action_btn.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Secondary actions
        btn_frame = ttk.Frame(action_frame)
        btn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        ttk.Button(
            btn_frame, text="📋 Manage Templates", command=self.open_template_manager
        ).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(btn_frame, text="🔄 Reset", command=self.reset_form).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0)
        )

        # Database status
        db_frame = ttk.LabelFrame(
            config_frame, text="🗄️ Database Configuration", padding="10"
        )
        db_frame.grid(row=row, column=0, sticky=(tk.W, tk.E))
        db_frame.columnconfigure(1, weight=1)

        # Database file selection
        ttk.Label(db_frame, text="Database File:").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5)
        )

        db_selection_frame = ttk.Frame(db_frame)
        db_selection_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        db_selection_frame.columnconfigure(0, weight=1)

        self.db_path_var = tk.StringVar()
        self.db_path_entry = ttk.Entry(
            db_selection_frame, textvariable=self.db_path_var, state="readonly"
        )
        self.db_path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(
            db_selection_frame, text="Browse...", command=self.browse_database_file
        ).grid(row=0, column=1)

        # Database options
        db_options_frame = ttk.Frame(db_frame)
        db_options_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        ttk.Button(
            db_options_frame,
            text="🔍 Auto-Find Scanner DB",
            command=self.auto_find_scanner_db,
        ).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(
            db_options_frame, text="🆕 Create New DB", command=self.create_new_database
        ).grid(row=0, column=1, padx=(5, 0))

        # Database status
        self.db_status_label = ttk.Label(db_frame, text="Checking connection...")
        self.db_status_label.grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 0)
        )

        # Database initialization moved to setup_ui after status panel is created

    def setup_status_panel(self, parent):
        """Setup the status panel (bottom)."""
        status_frame = ttk.Frame(parent)
        status_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0)
        )
        status_frame.columnconfigure(1, weight=1)

        # Status icon and text
        self.status_icon = ttk.Label(status_frame, text="ℹ️")
        self.status_icon.grid(row=0, column=0, padx=(0, 10))

        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.grid(row=0, column=1, sticky=(tk.W, tk.E))

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            status_frame, variable=self.progress_var, mode="determinate"
        )
        self.progress_bar.grid(row=0, column=2, padx=(10, 0), sticky=(tk.W, tk.E))
        self.progress_bar.grid_remove()  # Hidden by default

    def setup_bindings(self):
        """Setup keyboard and mouse bindings."""
        # Canvas mouse bindings for cropping
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Keyboard shortcuts
        self.root.bind("<Control-o>", lambda e: self.load_image())
        self.root.bind("<Control-s>", lambda e: self.create_template())
        self.root.bind("<Control-r>", lambda e: self.reset_form())
        self.root.bind("<F5>", lambda e: self.preview_template())

    # === UI Event Handlers ===

    def on_name_changed(self, event=None):
        """Handle template name changes."""
        name = self.name_var.get().strip()
        if name:
            # Check if template already exists
            existing = self.template_manager.read_template(name)
            if existing:
                self.update_status(f"⚠️ Template '{name}' already exists", "warning")
            else:
                self.update_status("Template name is available", "info")

    def toggle_marker_assignment(self):
        """Toggle between auto and manual marker assignment."""
        is_auto = self.auto_markers_var.get()
        state = "disabled" if is_auto else "normal"

        for i, var in enumerate(self.marker_vars):
            entry = self.marker_frame.grid_slaves(row=i, column=1)[0]
            entry.configure(state=state)
            if is_auto:
                var.set("")

    def on_canvas_click(self, event):
        """Handle canvas mouse click for cropping."""
        if self.current_image is None:
            return

        # Start cropping rectangle
        self.crop_start_x = self.canvas.canvasx(event.x)
        self.crop_start_y = self.canvas.canvasy(event.y)

        # Remove existing crop rectangle
        self.canvas.delete("crop_rect")

    def on_canvas_drag(self, event):
        """Handle canvas mouse drag for cropping."""
        if self.current_image is None or not hasattr(self, "crop_start_x"):
            return

        # Update crop rectangle
        self.canvas.delete("crop_rect")

        current_x = self.canvas.canvasx(event.x)
        current_y = self.canvas.canvasy(event.y)

        self.canvas.create_rectangle(
            self.crop_start_x,
            self.crop_start_y,
            current_x,
            current_y,
            outline="red",
            width=2,
            tags="crop_rect",
        )

    def on_canvas_release(self, event):
        """Handle canvas mouse release for cropping."""
        if self.current_image is None or not hasattr(self, "crop_start_x"):
            return

        # Finalize crop coordinates
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)

        # Ensure proper order (top-left to bottom-right)
        x1 = min(self.crop_start_x, end_x)
        y1 = min(self.crop_start_y, end_y)
        x2 = max(self.crop_start_x, end_x)
        y2 = max(self.crop_start_y, end_y)

        self.crop_coords = (int(x1), int(y1), int(x2), int(y2))

        self.update_status(f"Crop area selected: {self.crop_coords}", "info")

    # === Core Functionality ===

    def load_image(self):
        """Load an image for template creation."""
        file_path = filedialog.askopenfilename(
            title="Select template image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("All files", "*.*"),
            ],
        )

        if not file_path:
            return

        try:
            # Load image with OpenCV
            self.current_image = cv2.imread(file_path)
            if self.current_image is None:
                raise ValueError("Could not load image")

            # Convert BGR to RGB for display
            display_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)

            # Convert to PIL Image for tkinter
            pil_image = Image.fromarray(display_image)

            # Resize for display if too large
            display_width, display_height = 800, 600
            if pil_image.width > display_width or pil_image.height > display_height:
                pil_image.thumbnail(
                    (display_width, display_height), Image.Resampling.LANCZOS
                )

            # Convert to PhotoImage
            self.photo_image = ImageTk.PhotoImage(pil_image)

            # Clear canvas and display image
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)

            # Update canvas scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            # Update UI
            self.image_path_label.configure(text=Path(file_path).name)
            self.update_status(f"Image loaded: {Path(file_path).name}", "success")

            self.logger.info(f"Image loaded: {file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self.logger.error(f"Failed to load image: {e}")

    def start_cropping(self):
        """Start interactive cropping mode."""
        if self.current_image is None:
            messagebox.showwarning("Warning", "Please load an image first")
            return

        self.update_status("Click and drag to select crop area", "info")

    def generate_mask(self):
        """Generate mask from cropped area."""
        if self.current_image is None:
            messagebox.showwarning("Warning", "Please load an image first")
            return

        if self.crop_coords is None:
            messagebox.showwarning("Warning", "Please select a crop area first")
            return

        try:
            # Create mask from crop coordinates
            height, width = self.current_image.shape[:2]
            mask = np.zeros((height, width), dtype=np.uint8)

            x1, y1, x2, y2 = self.crop_coords
            # Scale coordinates to original image size
            scale_x = width / self.photo_image.width()
            scale_y = height / self.photo_image.height()

            x1 = int(x1 * scale_x)
            y1 = int(y1 * scale_y)
            x2 = int(x2 * scale_x)
            y2 = int(y2 * scale_y)

            # Fill crop area with white (255)
            mask[y1:y2, x1:x2] = 255

            self.current_mask = mask

            # Overlay mask on canvas
            self.display_mask_overlay()

            self.update_status("Mask generated from crop area", "success")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate mask: {e}")
            self.logger.error(f"Failed to generate mask: {e}")

    def display_mask_overlay(self):
        """Display mask overlay on canvas."""
        if self.current_mask is None:
            return

        try:
            # Create colored overlay
            mask_colored = np.zeros((*self.current_mask.shape, 3), dtype=np.uint8)
            mask_colored[:, :, 1] = self.current_mask  # Green channel

            # Convert to PIL and resize for display
            pil_mask = Image.fromarray(mask_colored)

            # Resize to match display image
            display_size = (self.photo_image.width(), self.photo_image.height())
            pil_mask = pil_mask.resize(display_size, Image.Resampling.NEAREST)

            # Make semi-transparent
            pil_mask.putalpha(128)  # 50% transparency

            # Convert to PhotoImage
            mask_photo = ImageTk.PhotoImage(pil_mask)

            # Remove existing overlay
            self.canvas.delete("mask_overlay")

            # Add overlay to canvas
            self.canvas.create_image(
                0, 0, anchor=tk.NW, image=mask_photo, tags="mask_overlay"
            )

            # Store reference to prevent garbage collection
            self.mask_photo = mask_photo

        except Exception as e:
            self.logger.error(f"Failed to display mask overlay: {e}")

    def preview_template(self):
        """Preview the template with markers."""
        if self.current_image is None:
            messagebox.showwarning("Warning", "Please load an image first")
            return

        try:
            # Get or assign marker IDs
            marker_ids = self.get_marker_ids()
            if not marker_ids:
                return

            # Create template preview
            preview_image = self.create_template_preview(marker_ids)

            # Show preview in new window
            self.show_preview_window(preview_image)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to preview template: {e}")
            self.logger.error(f"Failed to preview template: {e}")

    def create_template(self):
        """Create and save the template."""
        if not self.validate_inputs():
            return

        try:
            # Show progress
            self.show_progress("Creating template...")

            # Get inputs
            name = self.name_var.get().strip()
            marker_ids = self.get_marker_ids()
            if not marker_ids:
                self.hide_progress()
                return

            width = int(self.width_var.get())
            height = int(self.height_var.get())

            # Save current image and mask to temporary files
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)

            template_file = temp_dir / f"{name}_template.png"
            mask_file = temp_dir / f"{name}_mask.png"

            cv2.imwrite(str(template_file), self.current_image)
            if self.current_mask is not None:
                cv2.imwrite(str(mask_file), self.current_mask)
            else:
                # Create default mask (full image)
                h, w = self.current_image.shape[:2]
                default_mask = np.ones((h, w), dtype=np.uint8) * 255
                cv2.imwrite(str(mask_file), default_mask)

            # Create template data
            template_data = TemplateData(
                name=name,
                marker_ids=marker_ids,
                image_path=str(template_file),
                mask_path=str(mask_file),
                template_width=width,
                template_height=height,
            )

            # Save to database if requested
            if self.save_to_db_var.get():
                self.update_progress(30, "Saving to database...")
                success = self.template_manager.create_template(
                    name=name,
                    template_file=str(template_file),
                    mask_file=str(mask_file),
                    marker_ids=marker_ids,
                    template_width=width,
                    template_height=height,
                )

                if not success:
                    raise RuntimeError("Failed to save template to database")

            # Export files if requested
            if self.export_files_var.get():
                self.update_progress(60, "Exporting template files...")
                success = self.template_exporter.export_template_package(
                    template_data, self.current_image, self.current_mask
                )

                if not success:
                    raise RuntimeError("Failed to export template files")

            # Completion
            self.update_progress(100, "Template created successfully!")

            # Show success message
            success_msg = f"✅ Template '{name}' created successfully!\n\n"
            if self.save_to_db_var.get():
                success_msg += "• Saved to database (scanner.db)\n"
            if self.export_files_var.get():
                success_msg += "• Files exported for distribution\n"
            success_msg += f"• Marker IDs: {marker_ids}"

            messagebox.showinfo("Success", success_msg)

            # Reset form
            self.reset_form()

            self.logger.info(f"Template '{name}' created successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create template: {e}")
            self.logger.error(f"Failed to create template: {e}")
        finally:
            self.hide_progress()

    # === Helper Methods ===

    def validate_inputs(self) -> bool:
        """Validate all inputs before creating template."""
        # Check template name
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a template name")
            return False

        # Check if template already exists (if saving to database)
        if self.save_to_db_var.get():
            existing = self.template_manager.read_template(name)
            if existing:
                if not messagebox.askyesno(
                    "Template Exists", f"Template '{name}' already exists. Overwrite?"
                ):
                    return False

        # Check if image is loaded
        if self.current_image is None:
            messagebox.showerror("Error", "Please load an image first")
            return False

        # Check dimensions
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            if width <= 0 or height <= 0:
                raise ValueError("Dimensions must be positive")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid dimensions")
            return False

        # Check at least one export option is selected
        if not self.save_to_db_var.get() and not self.export_files_var.get():
            messagebox.showerror("Error", "Please select at least one export option")
            return False

        return True

    def get_marker_ids(self) -> Optional[List[int]]:
        """Get marker IDs (auto-assigned or manual)."""
        try:
            if self.auto_markers_var.get():
                # Auto-assign markers
                marker_ids = self.template_manager.get_next_available_markers()
                if not marker_ids:
                    messagebox.showerror("Error", "No available marker IDs")
                    return None
                return marker_ids
            else:
                # Manual marker IDs
                marker_ids = []
                for i, var in enumerate(self.marker_vars):
                    try:
                        marker_id = int(var.get())
                        if marker_id < 20 or marker_id > 49:
                            raise ValueError(f"Marker {i+1} must be between 20-49")
                        marker_ids.append(marker_id)
                    except ValueError as e:
                        messagebox.showerror("Error", f"Invalid marker ID: {e}")
                        return None

                # Check for duplicates
                if len(set(marker_ids)) != 4:
                    messagebox.showerror("Error", "Marker IDs must be unique")
                    return None

                # Validate availability
                if not self.template_manager.validate_marker_ids(marker_ids):
                    messagebox.showerror("Error", "Some marker IDs are already in use")
                    return None

                return marker_ids

        except Exception as e:
            messagebox.showerror("Error", f"Failed to get marker IDs: {e}")
            return None

    def create_template_preview(self, marker_ids: List[int]) -> np.ndarray:
        """Create template preview with markers."""
        # This would integrate with the existing template maker logic
        # For now, return the original image
        return self.current_image.copy()

    def show_preview_window(self, preview_image: np.ndarray):
        """Show template preview in new window."""
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Template Preview")
        preview_window.geometry("800x600")

        # Convert image for display
        display_image = cv2.cvtColor(preview_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(display_image)

        # Resize if needed
        if pil_image.width > 750 or pil_image.height > 550:
            pil_image.thumbnail((750, 550), Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(pil_image)

        # Create canvas and display
        canvas = tk.Canvas(
            preview_window, width=pil_image.width, height=pil_image.height
        )
        canvas.pack(expand=True)
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)

        # Keep reference
        canvas.image = photo

    def open_template_manager(self):
        """Open template management window."""
        # This would open a simplified template management interface
        messagebox.showinfo("Template Manager", "Template manager will open here")

    def reset_form(self):
        """Reset the form to initial state."""
        # Clear image
        self.current_image = None
        self.current_mask = None
        self.crop_coords = None

        # Clear canvas
        self.canvas.delete("all")

        # Reset form fields
        self.name_var.set("")
        self.width_var.set("1270")
        self.height_var.set("720")
        self.auto_markers_var.set(True)
        for var in self.marker_vars:
            var.set("")

        # Reset checkboxes
        self.save_to_db_var.set(True)
        self.export_files_var.set(True)

        # Reset UI state
        self.image_path_label.configure(text="No image loaded")
        self.toggle_marker_assignment()

        self.update_status("Form reset - ready for new template", "info")

    def check_database_connection(self):
        """Check database connection status."""
        try:
            # Test database connection
            templates = self.template_manager.read_all_templates()
            count = len(templates)

            self.db_status_label.configure(
                text=f"✅ Connected - {count} templates", foreground="green"
            )

            # Update marker availability
            self.update_marker_availability()

        except Exception as e:
            self.db_status_label.configure(text="❌ Database error", foreground="red")
            self.logger.error(f"Database connection error: {e}")

    def update_marker_availability(self):
        """Update marker availability display."""
        try:
            available_markers = self.template_manager.get_next_available_markers()
            if available_markers:
                remaining = len(self.template_manager.custom_marker_range) - len(
                    self.template_manager.get_used_marker_ids()
                )
                self.marker_info_label.configure(
                    text=f"Available: {remaining} markers remaining",
                    foreground="green" if remaining > 5 else "orange",
                )
            else:
                self.marker_info_label.configure(
                    text="⚠️ No markers available", foreground="red"
                )
        except Exception as e:
            self.logger.error(f"Failed to update marker availability: {e}")

    def show_progress(self, message: str):
        """Show progress bar with message."""
        self.progress_bar.grid()
        self.progress_var.set(0)
        self.update_status(message, "info")
        self.root.update()

    def update_progress(self, value: float, message: str = None):
        """Update progress bar value and message."""
        self.progress_var.set(value)
        if message:
            self.update_status(message, "info")
        self.root.update()

    def hide_progress(self):
        """Hide progress bar."""
        self.progress_bar.grid_remove()
        self.progress_var.set(0)

    def update_status(self, message: str, status_type: str = "info"):
        """Update status message with appropriate icon."""
        icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}

        colors = {
            "info": "blue",
            "success": "green",
            "warning": "orange",
            "error": "red",
        }

        self.status_icon.configure(text=icons.get(status_type, "ℹ️"))
        self.status_label.configure(
            text=message, foreground=colors.get(status_type, "black")
        )

        # Auto-clear non-permanent messages
        if status_type in ["info", "success"]:
            self.root.after(5000, lambda: self.update_status("Ready", "info"))

    def run(self):
        """Run the application."""
        try:
            # Center window on screen
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.root.geometry(f"{width}x{height}+{x}+{y}")

            # Start main loop
            self.root.mainloop()

        except Exception as e:
            self.logger.error(f"Error running application: {e}")
            messagebox.showerror("Fatal Error", f"Application error: {e}")

    # === Database Management Methods ===

    def initialize_database_path(self):
        """Initialize database path on startup."""
        try:
            # Import path utilities
            sys.path.insert(0, str(project_root))
            from path_utils import find_scanner_database_locations, get_database_path

            # Try to find scanner database first
            scanner_dbs = find_scanner_database_locations()
            if scanner_dbs:
                # Use first found scanner database
                self.db_path_var.set(str(scanner_dbs[0]))
                self.update_status(
                    f"Found scanner database: {scanner_dbs[0].name}", "success"
                )
            else:
                # Fall back to default path
                default_db = get_database_path()
                self.db_path_var.set(str(default_db))
                self.update_status("Using default database location", "info")

            # Update template manager with new database path
            self.update_template_manager_database()
            self.check_database_connection()

        except Exception as e:
            self.logger.error(f"Failed to initialize database path: {e}")
            self.update_status("Database initialization failed", "error")

    def browse_database_file(self):
        """Open file dialog to select database file."""
        try:
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
                    self.update_status(
                        f"Database updated: {validated_path.name}", "success"
                    )
                except (FileNotFoundError, ValueError) as e:
                    messagebox.showerror("Invalid Database", str(e))

        except Exception as e:
            self.logger.error(f"Failed to browse database file: {e}")
            messagebox.showerror("Error", f"Failed to select database: {e}")

    def auto_find_scanner_db(self):
        """Automatically find scanner database."""
        try:
            from path_utils import find_scanner_database_locations

            scanner_dbs = find_scanner_database_locations()
            if not scanner_dbs:
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
                self.update_status(
                    f"Scanner database found: {scanner_dbs[0].name}", "success"
                )
            else:
                # Multiple databases found - let user choose
                self.show_database_selection_dialog(scanner_dbs)

        except Exception as e:
            self.logger.error(f"Failed to auto-find scanner database: {e}")
            messagebox.showerror("Error", f"Failed to find scanner database: {e}")

    def show_database_selection_dialog(self, database_paths):
        """Show dialog to select from multiple found databases."""
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
                self.update_status(
                    f"Database selected: {selected_path.name}", "success"
                )
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
                self.update_status(
                    f"New database created: {Path(file_path).name}", "success"
                )

        except Exception as e:
            self.logger.error(f"Failed to create new database: {e}")
            messagebox.showerror("Error", f"Failed to create database: {e}")

    def update_template_manager_database(self):
        """Update template manager with current database path."""
        try:
            db_path = self.db_path_var.get()
            if db_path:
                # Reinitialize template manager with new database path
                from apps.scanner.template_manager import TemplateManager

                self.template_manager = TemplateManager(db_path)
                self.logger.info(f"Template manager updated with database: {db_path}")
        except Exception as e:
            self.logger.error(f"Failed to update template manager database: {e}")


# === Helper Functions ===


def main():
    """Main entry point for testing."""
    app = UnifiedTemplateCreatorGUI()
    app.run()


if __name__ == "__main__":
    main()
