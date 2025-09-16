#!/usr/bin/env python3
"""
Clean and Organized Krathong Template Maker GUI

A completely redesigned, modular interface for creating krathong templates.
This replaces the messy 3000+ line template_maker_gui.py with a clean, organized structure.
"""

import json
import os
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

# Import our modular components
from apps.template_maker import KrathongTemplateMaker, crop_image, preview_template


class CleanTemplateGUI:
    """Clean, organized template maker interface."""

    def __init__(self):
        """Initialize the clean GUI."""
        self.root = tk.Tk()
        self.root.title("🎯 Krathong Template Maker - Clean Edition")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)

        # Try to set the icon
        try:
            icon_path = Path("krathong.ico")
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass

        # Initialize core components
        try:
            self.template_maker = KrathongTemplateMaker()
        except Exception as e:
            messagebox.showerror(
                "Initialization Error", f"Failed to initialize template maker: {e}"
            )
            sys.exit(1)

        # Application state
        self.init_variables()

        # Setup interface
        self.setup_modern_styles()
        self.create_interface()
        self.center_window()

    def init_variables(self):
        """Initialize application variables."""
        self.template_name = tk.StringVar(value="my_template")
        self.output_directory = tk.StringVar(value="data/templates")
        self.selected_image_path = tk.StringVar()
        self.selected_mask_path = tk.StringVar()
        self.status_message = tk.StringVar(value="Ready to create templates")

        # Marker variables
        self.marker_ids = [tk.StringVar(value=str(i)) for i in range(4)]

        # Template info
        self.template_info = self.template_maker.get_template_info()

    def setup_modern_styles(self):
        """Configure modern styling."""
        style = ttk.Style()

        # Configure modern theme
        try:
            style.theme_use("clam")  # Modern looking theme
        except:
            pass

        # Custom styles
        style.configure(
            "Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#2c3e50"
        )
        style.configure(
            "Heading.TLabel", font=("Segoe UI", 12, "bold"), foreground="#34495e"
        )
        style.configure(
            "Subheading.TLabel", font=("Segoe UI", 10, "bold"), foreground="#7f8c8d"
        )
        style.configure("Info.TLabel", font=("Segoe UI", 9), foreground="#95a5a6")
        style.configure("Success.TLabel", font=("Segoe UI", 9), foreground="#27ae60")
        style.configure("Warning.TLabel", font=("Segoe UI", 9), foreground="#e67e22")

        # Custom button styles
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Success.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Warning.TButton", font=("Segoe UI", 10))

        # Notebook style
        style.configure("TNotebook", tabposition="n")
        style.configure("TNotebook.Tab", padding=[20, 10], font=("Segoe UI", 10))

    def center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_interface(self):
        """Create the main interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        self.create_header(main_frame)

        # Main content area with notebook
        self.create_main_content(main_frame)

        # Status bar
        self.create_status_bar(main_frame)

    def create_header(self, parent):
        """Create the application header."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        # Title and subtitle
        title_label = ttk.Label(
            header_frame, text="🎯 Krathong Template Maker", style="Title.TLabel"
        )
        title_label.pack()

        subtitle_label = ttk.Label(
            header_frame, text="Clean & Organized Edition", style="Info.TLabel"
        )
        subtitle_label.pack(pady=(5, 0))

        # Quick info panel
        info_frame = ttk.Frame(header_frame)
        info_frame.pack(fill=tk.X, pady=(10, 0))

        info_text = (
            f"Template Size: {self.template_info['template_size'][0]}×{self.template_info['template_size'][1]}px | "
            f"Drawing Area: {self.template_info['drawing_area_size'][0]}×{self.template_info['drawing_area_size'][1]}px | "
            f"ArUco: {self.template_info['aruco_dictionary']}"
        )

        ttk.Label(info_frame, text=info_text, style="Info.TLabel").pack()

    def create_main_content(self, parent):
        """Create the main content area with tabs."""
        # Create notebook
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Create tabs
        self.create_basic_tab()
        self.create_advanced_tab()
        self.create_management_tab()

    def create_basic_tab(self):
        """Create the basic template creation tab."""
        # Tab frame
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="🎨 Create Template")

        # Configure grid
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)

        # Left column - Settings
        left_frame = ttk.Frame(tab)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.create_template_settings(left_frame)
        self.create_marker_settings(left_frame)

        # Right column - Image and Actions
        right_frame = ttk.Frame(tab)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self.create_image_settings(right_frame)
        self.create_action_buttons(right_frame)

    def create_template_settings(self, parent):
        """Create template settings section."""
        settings_frame = ttk.LabelFrame(
            parent, text="📝 Template Settings", padding="15"
        )
        settings_frame.pack(fill=tk.X, pady=(0, 15))

        # Template name
        ttk.Label(
            settings_frame, text="Template Name:", style="Subheading.TLabel"
        ).pack(anchor=tk.W)
        name_entry = ttk.Entry(
            settings_frame, textvariable=self.template_name, font=("Segoe UI", 11)
        )
        name_entry.pack(fill=tk.X, pady=(5, 15))

        # Output directory
        ttk.Label(
            settings_frame, text="Output Directory:", style="Subheading.TLabel"
        ).pack(anchor=tk.W)

        dir_frame = ttk.Frame(settings_frame)
        dir_frame.pack(fill=tk.X, pady=(5, 0))
        dir_frame.columnconfigure(0, weight=1)

        dir_entry = ttk.Entry(
            dir_frame, textvariable=self.output_directory, font=("Segoe UI", 11)
        )
        dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        browse_btn = ttk.Button(
            dir_frame, text="Browse", command=self.browse_output_directory
        )
        browse_btn.grid(row=0, column=1)

    def create_marker_settings(self, parent):
        """Create marker settings section."""
        marker_frame = ttk.LabelFrame(parent, text="🎯 ArUco Markers", padding="15")
        marker_frame.pack(fill=tk.X, pady=(0, 15))

        # Quick presets
        ttk.Label(marker_frame, text="Quick Presets:", style="Subheading.TLabel").pack(
            anchor=tk.W
        )

        preset_frame = ttk.Frame(marker_frame)
        preset_frame.pack(fill=tk.X, pady=(5, 15))

        presets = [
            ("0-3", [0, 1, 2, 3]),
            ("4-7", [4, 5, 6, 7]),
            ("8-11", [8, 9, 10, 11]),
            ("Random", None),
        ]

        for i, (label, markers) in enumerate(presets):
            btn = ttk.Button(
                preset_frame,
                text=label,
                command=lambda m=markers: self.set_marker_preset(m),
            )
            btn.pack(side=tk.LEFT, padx=(0, 10) if i < len(presets) - 1 else 0)

        # Individual markers
        ttk.Label(
            marker_frame, text="Individual Markers (0-49):", style="Subheading.TLabel"
        ).pack(anchor=tk.W, pady=(15, 5))

        markers_grid = ttk.Frame(marker_frame)
        markers_grid.pack(fill=tk.X)

        marker_labels = ["Top-Left:", "Top-Right:", "Bottom-Left:", "Bottom-Right:"]
        for i, label in enumerate(marker_labels):
            row = i // 2
            col = (i % 2) * 2

            ttk.Label(markers_grid, text=label).grid(
                row=row, column=col, sticky=tk.W, padx=(0, 10), pady=5
            )

            marker_entry = ttk.Entry(
                markers_grid,
                textvariable=self.marker_ids[i],
                width=8,
                font=("Segoe UI", 11),
            )
            marker_entry.grid(
                row=row, column=col + 1, padx=(0, 20) if col == 0 else 0, pady=5
            )

    def create_image_settings(self, parent):
        """Create image settings section."""
        image_frame = ttk.LabelFrame(parent, text="🖼️ Optional Image", padding="15")
        image_frame.pack(fill=tk.X, pady=(0, 15))

        # Current image display
        ttk.Label(image_frame, text="Selected Image:", style="Subheading.TLabel").pack(
            anchor=tk.W
        )

        image_display_frame = ttk.Frame(image_frame)
        image_display_frame.pack(fill=tk.X, pady=(5, 15))
        image_display_frame.columnconfigure(0, weight=1)

        self.image_display = ttk.Entry(
            image_display_frame,
            textvariable=self.selected_image_path,
            state="readonly",
            font=("Segoe UI", 10),
        )
        self.image_display.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        clear_btn = ttk.Button(
            image_display_frame, text="Clear", command=self.clear_image
        )
        clear_btn.grid(row=0, column=1)

        # Image actions
        ttk.Label(image_frame, text="Image Actions:", style="Subheading.TLabel").pack(
            anchor=tk.W
        )

        image_actions = ttk.Frame(image_frame)
        image_actions.pack(fill=tk.X, pady=(5, 0))

        browse_btn = ttk.Button(
            image_actions,
            text="📁 Browse & Crop",
            command=self.browse_and_crop_image,
            style="Primary.TButton",
        )
        browse_btn.pack(fill=tk.X, pady=(0, 5))

        process_btn = ttk.Button(
            image_actions, text="✂️ Process Current", command=self.process_current_image
        )
        process_btn.pack(fill=tk.X)

    def create_action_buttons(self, parent):
        """Create main action buttons."""
        action_frame = ttk.LabelFrame(parent, text="🚀 Actions", padding="15")
        action_frame.pack(fill=tk.X)

        # Preview button
        preview_btn = ttk.Button(
            action_frame,
            text="👁️ Preview Template",
            command=self.preview_template,
            style="Primary.TButton",
        )
        preview_btn.pack(fill=tk.X, pady=(0, 10))

        # Create button
        create_btn = ttk.Button(
            action_frame,
            text="🎯 Create Template",
            command=self.create_template,
            style="Success.TButton",
        )
        create_btn.pack(fill=tk.X)

        # Separator
        ttk.Separator(action_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(15, 15))

        # Quick actions
        ttk.Label(action_frame, text="Quick Actions:", style="Subheading.TLabel").pack(
            anchor=tk.W, pady=(0, 5)
        )

        quick_frame = ttk.Frame(action_frame)
        quick_frame.pack(fill=tk.X)

        open_folder_btn = ttk.Button(
            quick_frame, text="📂 Output Folder", command=self.open_output_folder
        )
        open_folder_btn.pack(fill=tk.X, pady=(0, 5))

        specs_btn = ttk.Button(
            quick_frame, text="📐 Specifications", command=self.show_specifications
        )
        specs_btn.pack(fill=tk.X)

    def create_advanced_tab(self):
        """Create the advanced features tab."""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="⚙️ Advanced")

        # Batch operations
        batch_frame = ttk.LabelFrame(tab, text="🏭 Batch Operations", padding="15")
        batch_frame.pack(fill=tk.X, pady=(0, 15))

        batch_buttons = [
            ("📊 Sequential Templates", self.create_sequential_templates),
            ("📄 From Config File", self.create_from_config),
            ("📝 Create Sample Config", self.create_sample_config),
        ]

        for text, command in batch_buttons:
            btn = ttk.Button(batch_frame, text=text, command=command)
            btn.pack(fill=tk.X, pady=(0, 5))

        # Advanced image processing
        processing_frame = ttk.LabelFrame(
            tab, text="🔧 Advanced Processing", padding="15"
        )
        processing_frame.pack(fill=tk.X)

        ttk.Label(
            processing_frame,
            text="Advanced image processing features coming soon!",
            style="Info.TLabel",
        ).pack(pady=20)

    def create_management_tab(self):
        """Create the template management tab."""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="📁 Management")

        # Template management
        mgmt_frame = ttk.LabelFrame(tab, text="📁 Template Management", padding="15")
        mgmt_frame.pack(fill=tk.X, pady=(0, 15))

        mgmt_buttons = [
            ("📋 List Templates", self.list_templates),
            ("🔍 Find Templates", self.find_templates),
            ("🗑️ Clean Old Templates", self.clean_templates),
        ]

        for text, command in mgmt_buttons:
            btn = ttk.Button(mgmt_frame, text=text, command=command)
            btn.pack(fill=tk.X, pady=(0, 5))

        # Settings
        settings_frame = ttk.LabelFrame(
            tab, text="⚙️ Application Settings", padding="15"
        )
        settings_frame.pack(fill=tk.X)

        ttk.Label(
            settings_frame,
            text="Application settings and preferences coming soon!",
            style="Info.TLabel",
        ).pack(pady=20)

    def create_status_bar(self, parent):
        """Create the status bar."""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(15, 0))
        status_frame.columnconfigure(0, weight=1)

        # Progress bar
        self.progress_bar = ttk.Progressbar(status_frame, mode="indeterminate")
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, 15))

        # Status label
        status_label = ttk.Label(
            status_frame, textvariable=self.status_message, style="Info.TLabel"
        )
        status_label.grid(row=0, column=1)

    # Event handlers
    def set_marker_preset(self, markers):
        """Set marker IDs from preset."""
        if markers is None:
            import random

            markers = random.sample(range(50), 4)

        for i, marker_id in enumerate(markers):
            self.marker_ids[i].set(str(marker_id))

    def browse_output_directory(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory", initialdir=self.output_directory.get()
        )
        if directory:
            self.output_directory.set(directory)

    def browse_and_crop_image(self):
        """Browse for image and open crop dialog."""
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("All files", "*.*"),
        ]

        filename = filedialog.askopenfilename(
            title="Select Krathong Image", filetypes=filetypes
        )

        if filename:

            def on_crop_complete(image_path, mask_path):
                if image_path:
                    self.selected_image_path.set(image_path)
                    if mask_path:
                        self.selected_mask_path.set(mask_path)
                    self.update_status(f"Image processed: {Path(image_path).name}")

            try:
                crop_image(self.root, filename, on_crop_complete)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open image cropper: {e}")
                self.selected_image_path.set(filename)

    def process_current_image(self):
        """Process the currently selected image."""
        image_path = self.selected_image_path.get()
        if not image_path:
            messagebox.showwarning("No Image", "Please select an image first.")
            return

        try:
            import cv2

            image = cv2.imread(image_path)
            if image is None:
                messagebox.showerror("Error", "Could not load image.")
                return

            processed_image = self.template_maker.remove_white_background(image)

            # Save processed image
            input_path = Path(image_path)
            processed_path = input_path.parent / f"{input_path.stem}_processed.png"
            cv2.imwrite(str(processed_path), processed_image)

            self.selected_image_path.set(str(processed_path))
            self.update_status(f"Background processed: {processed_path.name}")
            messagebox.showinfo("Success", "Background processing completed!")

        except Exception as e:
            messagebox.showerror("Error", f"Could not process image: {e}")

    def clear_image(self):
        """Clear the selected image."""
        self.selected_image_path.set("")
        self.selected_mask_path.set("")
        self.update_status("Image cleared")

    def validate_inputs(self):
        """Validate all inputs before creating template."""
        # Validate template name
        if not self.template_name.get().strip():
            messagebox.showerror("Validation Error", "Please enter a template name.")
            return False

        # Validate markers
        try:
            markers = []
            for var in self.marker_ids:
                marker_id = int(var.get().strip())
                if not 0 <= marker_id <= 49:
                    messagebox.showerror(
                        "Validation Error",
                        f"Marker ID {marker_id} must be between 0 and 49.",
                    )
                    return False
                markers.append(marker_id)

            if len(set(markers)) != 4:
                messagebox.showerror(
                    "Validation Error", "All marker IDs must be unique."
                )
                return False

        except ValueError:
            messagebox.showerror(
                "Validation Error", "Please enter valid numbers for all markers."
            )
            return False

        return True

    def get_marker_list(self):
        """Get the current marker list."""
        return [int(var.get().strip()) for var in self.marker_ids]

    def preview_template(self):
        """Show template preview."""
        if not self.validate_inputs():
            return

        try:
            markers = self.get_marker_list()
            image_path = self.selected_image_path.get().strip() or None
            mask_path = self.selected_mask_path.get().strip() or None

            preview_template(
                self.root, self.template_maker, markers, image_path, mask_path
            )

        except Exception as e:
            messagebox.showerror("Preview Error", f"Could not create preview: {e}")

    def create_template(self):
        """Create the template."""
        if not self.validate_inputs():
            return

        try:
            self.progress_bar.start()
            self.update_status("Creating template...")

            # Prepare parameters
            template_name = self.template_name.get().strip()
            markers = self.get_marker_list()
            image_path = self.selected_image_path.get().strip() or None
            mask_path = self.selected_mask_path.get().strip() or None

            # Create output directory
            output_dir = Path(self.output_directory.get())
            output_dir.mkdir(parents=True, exist_ok=True)

            # Create template
            template_image = self.template_maker.create_template_image(
                marker_ids=markers, image_path=image_path, mask_path=mask_path
            )

            # Save template
            template_path = output_dir / f"{template_name}.png"
            import cv2

            cv2.imwrite(str(template_path), template_image)

            self.progress_bar.stop()
            self.update_status(f"Template created: {template_name}")

            # Show success message
            messagebox.showinfo(
                "Success",
                f"Template created successfully!\n\nSaved to: {template_path}\n\nMarkers: {', '.join(map(str, markers))}",
            )

        except Exception as e:
            self.progress_bar.stop()
            self.update_status("Error creating template")
            messagebox.showerror("Creation Error", f"Could not create template: {e}")

    def update_status(self, message):
        """Update the status message."""
        self.status_message.set(message)
        self.root.update_idletasks()

    # Placeholder methods for advanced features
    def create_sequential_templates(self):
        """Create sequential templates (placeholder)."""
        messagebox.showinfo(
            "Coming Soon", "Sequential template creation feature is being developed!"
        )

    def create_from_config(self):
        """Create from config file (placeholder)."""
        messagebox.showinfo(
            "Coming Soon", "Config file creation feature is being developed!"
        )

    def create_sample_config(self):
        """Create sample config (placeholder)."""
        messagebox.showinfo(
            "Coming Soon", "Sample config creation feature is being developed!"
        )

    def list_templates(self):
        """List templates (placeholder)."""
        messagebox.showinfo(
            "Coming Soon", "Template listing feature is being developed!"
        )

    def find_templates(self):
        """Find templates (placeholder)."""
        messagebox.showinfo(
            "Coming Soon", "Template search feature is being developed!"
        )

    def clean_templates(self):
        """Clean old templates (placeholder)."""
        messagebox.showinfo(
            "Coming Soon", "Template cleanup feature is being developed!"
        )

    def open_output_folder(self):
        """Open the output folder."""
        try:
            output_dir = Path(self.output_directory.get())
            if output_dir.exists():
                os.startfile(str(output_dir))
            else:
                messagebox.showwarning(
                    "Folder Not Found", f"Output directory does not exist: {output_dir}"
                )
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")

    def show_specifications(self):
        """Show template specifications."""
        info = self.template_info
        specs = f"""🎯 Krathong Template Specifications

Template Size: {info['template_size'][0]} × {info['template_size'][1]} pixels
Drawing Area: {info['drawing_area_size'][0]} × {info['drawing_area_size'][1]} pixels
Drawing Position: ({info['drawing_area_position'][0]}, {info['drawing_area_position'][1]})
Marker Size: {info['marker_size']} × {info['marker_size']} pixels
ArUco Dictionary: {info['aruco_dictionary']}
Marker ID Range: {info['marker_id_range'][0]} - {info['marker_id_range'][1]}

Marker Positions:
• Top-Left: {info['marker_positions'][0]}
• Top-Right: {info['marker_positions'][1]}
• Bottom-Left: {info['marker_positions'][2]}
• Bottom-Right: {info['marker_positions'][3]}

Supported Image Formats: PNG, JPG, JPEG, BMP, TIFF"""

        messagebox.showinfo("Template Specifications", specs)

    def run(self):
        """Start the application."""
        print("🎯 Starting Clean Krathong Template Maker GUI...")
        self.root.mainloop()


def main():
    """Main entry point."""
    try:
        app = CleanTemplateGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Startup Error", f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
