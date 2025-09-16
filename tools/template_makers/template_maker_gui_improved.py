#!/usr/bin/env python3
"""
Improved Krathong Template Maker GUI

A clean, organized graphical interface for creating krathong templates
with ArUco markers for the KrathongScanner system.
"""

import json
import os
import shutil
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageTk

# Import the core functionality from the original file
try:
    from template_maker_gui import (
        ImageCropper,
        KrathongTemplateMaker,
        TemplatePreviewWindow,
    )
except ImportError:
    # If we can't import, we'll need to run this from the same directory
    pass


class ImprovedTemplateGUI:
    """Clean, organized template maker GUI."""

    def __init__(self):
        """Initialize the improved GUI."""
        self.root = tk.Tk()
        self.root.title("🎯 Krathong Template Maker - Improved")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)

        # Initialize template maker
        try:
            self.template_maker = KrathongTemplateMaker()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize template maker: {e}")
            sys.exit(1)

        # State variables
        self.template_name_var = tk.StringVar(value="my_template")
        self.output_dir_var = tk.StringVar(value="data/templates")
        self.marker_vars = [tk.StringVar(value=str(i)) for i in range(4)]
        self.status_var = tk.StringVar(value="Ready")
        self.image_path_var = tk.StringVar()
        self.mask_path_var = tk.StringVar()

        # Setup the interface
        self.setup_styles()
        self.create_main_layout()
        self.center_window()

    def setup_styles(self):
        """Configure modern styling."""
        style = ttk.Style()

        # Configure notebook style for clean tabs
        style.configure("TNotebook", tabposition="n")
        style.configure("TNotebook.Tab", padding=[15, 8])

        # Configure frame styles
        style.configure("Card.TFrame", relief="raised", borderwidth=1)
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("Info.TLabel", font=("Segoe UI", 9))

    def center_window(self):
        """Center window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_main_layout(self):
        """Create the main tabbed interface."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title header
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))

        title_label = ttk.Label(
            title_frame, text="🎯 Krathong Template Maker", style="Title.TLabel"
        )
        title_label.pack()

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create individual tabs
        self.create_basic_tab()
        self.create_advanced_tab()
        self.create_batch_tab()
        self.create_management_tab()

        # Status bar
        self.create_status_bar(main_frame)

    def create_basic_tab(self):
        """Create basic template creation tab."""
        tab_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(tab_frame, text="🎨 Basic Template")

        # Configure grid
        tab_frame.columnconfigure(0, weight=1)

        # Template settings card
        settings_card = self.create_card(tab_frame, "📝 Template Settings")
        settings_card.pack(fill=tk.X, pady=(0, 10))

        # Template name
        name_frame = ttk.Frame(settings_card)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="Template Name:", style="Heading.TLabel").pack(
            anchor=tk.W
        )
        ttk.Entry(
            name_frame, textvariable=self.template_name_var, font=("Segoe UI", 10)
        ).pack(fill=tk.X, pady=(5, 0))

        # Output directory
        output_frame = ttk.Frame(settings_card)
        output_frame.pack(fill=tk.X, pady=10)
        ttk.Label(output_frame, text="Output Directory:", style="Heading.TLabel").pack(
            anchor=tk.W
        )

        dir_input_frame = ttk.Frame(output_frame)
        dir_input_frame.pack(fill=tk.X, pady=(5, 0))
        dir_input_frame.columnconfigure(0, weight=1)

        ttk.Entry(
            dir_input_frame, textvariable=self.output_dir_var, font=("Segoe UI", 10)
        ).grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ttk.Button(
            dir_input_frame, text="Browse", command=self.browse_output_directory
        ).grid(row=0, column=1)

        # Markers card
        markers_card = self.create_card(tab_frame, "🎯 ArUco Markers")
        markers_card.pack(fill=tk.X, pady=(0, 10))

        # Quick presets
        preset_frame = ttk.Frame(markers_card)
        preset_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(preset_frame, text="Quick Presets:", style="Heading.TLabel").pack(
            anchor=tk.W
        )

        preset_buttons = ttk.Frame(preset_frame)
        preset_buttons.pack(fill=tk.X, pady=(5, 0))

        presets = [
            ("0,1,2,3", [0, 1, 2, 3]),
            ("4,5,6,7", [4, 5, 6, 7]),
            ("8,9,10,11", [8, 9, 10, 11]),
            ("Random", None),
        ]
        for i, (label, markers) in enumerate(presets):
            ttk.Button(
                preset_buttons,
                text=label,
                command=lambda m=markers: self.set_marker_preset(m),
            ).pack(side=tk.LEFT, padx=(0, 10))

        # Individual markers
        marker_grid = ttk.Frame(markers_card)
        marker_grid.pack(fill=tk.X)

        marker_labels = ["Top-Left:", "Top-Right:", "Bottom-Left:", "Bottom-Right:"]
        for i, label in enumerate(marker_labels):
            row = i // 2
            col = (i % 2) * 2
            ttk.Label(marker_grid, text=label).grid(
                row=row, column=col, sticky=tk.W, padx=(0, 10), pady=5
            )
            ttk.Entry(
                marker_grid,
                textvariable=self.marker_vars[i],
                width=8,
                font=("Segoe UI", 10),
            ).grid(row=row, column=col + 1, padx=(0, 20), pady=5)

        # Image card
        image_card = self.create_card(tab_frame, "🖼️ Optional Image")
        image_card.pack(fill=tk.X, pady=(0, 10))

        # Image path display
        image_display = ttk.Frame(image_card)
        image_display.pack(fill=tk.X, pady=(0, 10))
        image_display.columnconfigure(0, weight=1)

        ttk.Entry(
            image_display,
            textvariable=self.image_path_var,
            state="readonly",
            font=("Segoe UI", 10),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ttk.Button(
            image_display, text="Clear", command=lambda: self.image_path_var.set("")
        ).grid(row=0, column=1)

        # Image buttons
        image_buttons = ttk.Frame(image_card)
        image_buttons.pack(fill=tk.X)

        ttk.Button(
            image_buttons, text="📁 Browse & Crop", command=self.browse_image_file
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            image_buttons, text="✂️ Process Background", command=self.process_background
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Action buttons card
        action_card = self.create_card(tab_frame, "🚀 Actions")
        action_card.pack(fill=tk.X)

        action_buttons = ttk.Frame(action_card)
        action_buttons.pack()

        ttk.Button(
            action_buttons,
            text="👁️ Preview Template",
            command=self.preview_template,
            style="Accent.TButton",
        ).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Button(
            action_buttons,
            text="🎯 Create Template",
            command=self.create_template,
            style="Accent.TButton",
        ).pack(side=tk.LEFT)

    def create_advanced_tab(self):
        """Create advanced options tab."""
        tab_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(tab_frame, text="⚙️ Advanced")

        # Placeholder for advanced features
        ttk.Label(tab_frame, text="🔧 Advanced Features", style="Title.TLabel").pack(
            pady=20
        )
        ttk.Label(
            tab_frame,
            text="Advanced template customization options will be available here.",
            style="Info.TLabel",
        ).pack()

    def create_batch_tab(self):
        """Create batch processing tab."""
        tab_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(tab_frame, text="🏭 Batch")

        # Batch operations card
        batch_card = self.create_card(tab_frame, "🏭 Batch Operations")
        batch_card.pack(fill=tk.X, pady=(0, 10))

        batch_buttons = ttk.Frame(batch_card)
        batch_buttons.pack()

        ttk.Button(
            batch_buttons,
            text="📊 Sequential Templates",
            command=self.create_sequential_templates,
        ).pack(pady=5)
        ttk.Button(
            batch_buttons, text="📄 From Config File", command=self.create_from_config
        ).pack(pady=5)
        ttk.Button(
            batch_buttons,
            text="📝 Create Sample Config",
            command=self.create_sample_config,
        ).pack(pady=5)

    def create_management_tab(self):
        """Create template management tab."""
        tab_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(tab_frame, text="📁 Management")

        # Management operations card
        mgmt_card = self.create_card(tab_frame, "📁 Template Management")
        mgmt_card.pack(fill=tk.X)

        mgmt_buttons = ttk.Frame(mgmt_card)
        mgmt_buttons.pack()

        ttk.Button(
            mgmt_buttons, text="📋 List Templates", command=self.list_templates
        ).pack(pady=5)
        ttk.Button(
            mgmt_buttons, text="📂 Open Output Folder", command=self.open_output_folder
        ).pack(pady=5)
        ttk.Button(
            mgmt_buttons, text="📐 View Specifications", command=self.show_specifications
        ).pack(pady=5)

    def create_card(self, parent, title):
        """Create a styled card container."""
        card_frame = ttk.LabelFrame(
            parent, text=title, padding="15", style="Card.TFrame"
        )
        return card_frame

    def create_status_bar(self, parent):
        """Create status bar."""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            status_frame, mode="indeterminate", length=200
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        # Status label
        status_label = ttk.Label(
            status_frame, textvariable=self.status_var, style="Info.TLabel"
        )
        status_label.grid(row=0, column=1)

    # Event handlers and utility methods
    def set_marker_preset(self, markers):
        """Set marker IDs from preset."""
        if markers is None:
            import random

            markers = random.sample(range(50), 4)

        for i, marker_id in enumerate(markers):
            self.marker_vars[i].set(str(marker_id))

    def browse_output_directory(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory", initialdir=self.output_dir_var.get()
        )
        if directory:
            self.output_dir_var.set(directory)

    def browse_image_file(self):
        """Browse and crop image file."""
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("All files", "*.*"),
        ]

        filename = filedialog.askopenfilename(
            title="Select Krathong Image",
            filetypes=filetypes,
            initialdir=os.path.expanduser("~"),
        )

        if filename:
            self.open_image_cropper(filename)

    def open_image_cropper(self, image_path):
        """Open image cropping interface."""
        try:
            cropper = ImageCropper(self.root, image_path, self.template_maker)
            self.root.wait_window(cropper.window)

            if hasattr(cropper, "cropped_image") and cropper.cropped_image is not None:
                result = cropper.apply_crop()
                if result and len(result) == 2:
                    cropped_path, mask_path = result
                    self.image_path_var.set(cropped_path)
                    self.mask_path_var.set(mask_path)
                    self.update_status(f"Image processed: {Path(cropped_path).name}")
                else:
                    cropped_path = str(
                        Path(image_path).parent / f"{Path(image_path).stem}_cropped.png"
                    )
                    cv2.imwrite(cropped_path, cropper.cropped_image)
                    self.image_path_var.set(cropped_path)
                    self.update_status(f"Image cropped: {Path(cropped_path).name}")
            else:
                self.image_path_var.set(image_path)
                self.update_status(f"Selected: {Path(image_path).name}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process image: {e}")
            self.image_path_var.set(image_path)

    def process_background(self):
        """Process current image to remove background."""
        image_path = self.image_path_var.get().strip()
        if not image_path:
            messagebox.showwarning("No Image", "Please select an image first.")
            return

        try:
            image = cv2.imread(image_path)
            if image is None:
                messagebox.showerror("Error", "Could not load image.")
                return

            processed_image = self.template_maker.remove_white_background(image)
            processed_path = str(
                Path(image_path).parent / f"{Path(image_path).stem}_processed.png"
            )
            cv2.imwrite(processed_path, processed_image)

            self.image_path_var.set(processed_path)
            self.update_status(f"Background removed: {Path(processed_path).name}")
            messagebox.showinfo("Success", "Background removed successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process image: {e}")

    def validate_markers(self):
        """Validate marker inputs."""
        try:
            markers = []
            for var in self.marker_vars:
                marker_id = int(var.get().strip())
                if not 0 <= marker_id <= 49:
                    messagebox.showerror(
                        "Invalid Marker",
                        f"Marker ID {marker_id} must be between 0 and 49",
                    )
                    return None
                markers.append(marker_id)

            if len(set(markers)) != 4:
                messagebox.showerror(
                    "Duplicate Markers", "All marker IDs must be unique"
                )
                return None

            return markers
        except ValueError:
            messagebox.showerror(
                "Invalid Input", "Please enter valid numbers for all markers"
            )
            return None

    def preview_template(self):
        """Show template preview."""
        markers = self.validate_markers()
        if markers is None:
            return

        try:
            preview_window = TemplatePreviewWindow(
                self.root,
                self.template_maker,
                markers,
                image_path=self.image_path_var.get().strip() or None,
                mask_path=self.mask_path_var.get().strip() or None,
            )
        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to create preview: {e}")

    def create_template(self):
        """Create the template."""
        template_name = self.template_name_var.get().strip()
        if not template_name:
            messagebox.showerror("Error", "Please enter a template name")
            return

        markers = self.validate_markers()
        if markers is None:
            return

        try:
            self.progress_bar.start()
            self.update_status("Creating template...")

            output_dir = Path(self.output_dir_var.get())
            output_dir.mkdir(parents=True, exist_ok=True)

            # Create template
            template_image = self.template_maker.create_template_image(
                markers,
                image_path=self.image_path_var.get().strip() or None,
                mask_path=self.mask_path_var.get().strip() or None,
            )

            # Save template
            template_path = output_dir / f"{template_name}.png"
            cv2.imwrite(str(template_path), template_image)

            self.progress_bar.stop()
            self.update_status(f"Template created: {template_name}")
            messagebox.showinfo(
                "Success", f"Template created successfully!\nSaved to: {template_path}"
            )

        except Exception as e:
            self.progress_bar.stop()
            self.update_status("Error creating template")
            messagebox.showerror("Error", f"Failed to create template: {e}")

    def update_status(self, message):
        """Update status message."""
        self.status_var.set(message)
        self.root.update_idletasks()

    # Placeholder methods for batch and management features
    def create_sequential_templates(self):
        """Create sequential templates."""
        messagebox.showinfo(
            "Feature", "Sequential template creation feature coming soon!"
        )

    def create_from_config(self):
        """Create templates from config file."""
        messagebox.showinfo("Feature", "Config file creation feature coming soon!")

    def create_sample_config(self):
        """Create sample config file."""
        messagebox.showinfo("Feature", "Sample config creation feature coming soon!")

    def list_templates(self):
        """List existing templates."""
        messagebox.showinfo("Feature", "Template listing feature coming soon!")

    def open_output_folder(self):
        """Open output folder."""
        try:
            output_dir = Path(self.output_dir_var.get())
            if output_dir.exists():
                os.startfile(str(output_dir))
            else:
                messagebox.showwarning(
                    "Folder Not Found", f"Output directory does not exist: {output_dir}"
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")

    def show_specifications(self):
        """Show template specifications."""
        specs = """🎯 Krathong Template Specifications

Template Size: 1270 × 720 pixels
Drawing Area: 779 × 457 pixels (centered)
Marker Size: 100 × 100 pixels
ArUco Dictionary: 4X4_50
Supported Formats: PNG, JPG
Max Image Scale: 150%

Marker Positions:
• Top-Left: (50, 50)
• Top-Right: (1120, 50)
• Bottom-Left: (50, 570)
• Bottom-Right: (1120, 570)"""

        messagebox.showinfo("Template Specifications", specs)

    def run(self):
        """Start the application."""
        print("🎯 Starting Improved Krathong Template Maker GUI...")
        self.root.mainloop()


def main():
    """Main entry point."""
    try:
        app = ImprovedTemplateGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Startup Error", f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
