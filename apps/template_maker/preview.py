"""
Template preview window for the template maker.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk


class TemplatePreviewDialog:
    """Template preview and adjustment dialog."""

    def __init__(
        self, parent, template_maker, marker_ids, image_path=None, mask_path=None
    ):
        """Initialize the preview dialog."""
        self.parent = parent
        self.template_maker = template_maker
        self.marker_ids = marker_ids
        self.image_path = image_path
        self.mask_path = mask_path

        # Adjustment variables
        self.image_scale = tk.DoubleVar(value=0.8)
        self.image_offset_x = tk.IntVar(value=0)
        self.image_offset_y = tk.IntVar(value=0)
        self.show_mask_overlay = tk.BooleanVar(value=False)

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Template Preview")
        self.dialog.geometry("900x700")
        self.dialog.resizable(True, True)
        self.dialog.grab_set()

        # Preview image
        self.preview_image = None
        self.photo_image = None

        self.setup_ui()
        self.update_preview()

        # Center dialog
        self.dialog.transient(parent)
        self.dialog.update_idletasks()
        x = (
            parent.winfo_rootx()
            + parent.winfo_width() // 2
            - self.dialog.winfo_width() // 2
        )
        y = (
            parent.winfo_rooty()
            + parent.winfo_height() // 2
            - self.dialog.winfo_height() // 2
        )
        self.dialog.geometry(f"+{x}+{y}")

    def setup_ui(self):
        """Setup the preview interface."""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(
            main_frame, text="👁️ Template Preview", font=("Segoe UI", 14, "bold")
        ).pack(pady=(0, 10))

        # Create paned window for layout
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Left panel - Preview
        preview_frame = ttk.LabelFrame(paned_window, text="Preview", padding="10")
        paned_window.add(preview_frame, weight=3)

        # Canvas for preview
        self.canvas = tk.Canvas(preview_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Right panel - Controls
        controls_frame = ttk.LabelFrame(paned_window, text="Adjustments", padding="10")
        paned_window.add(controls_frame, weight=1)

        # Image controls (only if image is provided)
        if self.image_path:
            self.create_image_controls(controls_frame)

        # Mask controls (only if mask is provided)
        if self.mask_path:
            self.create_mask_controls(controls_frame)

        # Action buttons
        action_frame = ttk.Frame(controls_frame)
        action_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(
            action_frame,
            text="Save Template",
            command=self.save_template,
            style="Accent.TButton",
        ).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(action_frame, text="Close", command=self.dialog.destroy).pack(
            fill=tk.X
        )

        # Info panel
        info_frame = ttk.LabelFrame(controls_frame, text="Info", padding="5")
        info_frame.pack(fill=tk.X, pady=(10, 0))

        info_text = f"""Markers: {', '.join(map(str, self.marker_ids))}
Template: 1270×720px
Drawing Area: 779×457px"""

        ttk.Label(info_frame, text=info_text, font=("Consolas", 9)).pack()

    def create_image_controls(self, parent):
        """Create image adjustment controls."""
        image_frame = ttk.LabelFrame(parent, text="🖼️ Image Adjustments", padding="10")
        image_frame.pack(fill=tk.X, pady=(0, 10))

        # Scale control
        ttk.Label(image_frame, text="Scale:").pack(anchor=tk.W)
        scale_frame = ttk.Frame(image_frame)
        scale_frame.pack(fill=tk.X, pady=(5, 10))

        self.scale_scale = ttk.Scale(
            scale_frame,
            from_=0.1,
            to=1.5,
            variable=self.image_scale,
            orient=tk.HORIZONTAL,
            command=self.on_scale_change,
        )
        self.scale_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.scale_label = ttk.Label(scale_frame, text="0.8")
        self.scale_label.pack(side=tk.RIGHT, padx=(10, 0))

        # Offset X control
        ttk.Label(image_frame, text="Offset X:").pack(anchor=tk.W)
        offset_x_frame = ttk.Frame(image_frame)
        offset_x_frame.pack(fill=tk.X, pady=(5, 10))

        self.offset_x_scale = ttk.Scale(
            offset_x_frame,
            from_=-200,
            to=200,
            variable=self.image_offset_x,
            orient=tk.HORIZONTAL,
            command=self.on_offset_change,
        )
        self.offset_x_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.offset_x_label = ttk.Label(offset_x_frame, text="0")
        self.offset_x_label.pack(side=tk.RIGHT, padx=(10, 0))

        # Offset Y control
        ttk.Label(image_frame, text="Offset Y:").pack(anchor=tk.W)
        offset_y_frame = ttk.Frame(image_frame)
        offset_y_frame.pack(fill=tk.X, pady=(5, 10))

        self.offset_y_scale = ttk.Scale(
            offset_y_frame,
            from_=-200,
            to=200,
            variable=self.image_offset_y,
            orient=tk.HORIZONTAL,
            command=self.on_offset_change,
        )
        self.offset_y_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.offset_y_label = ttk.Label(offset_y_frame, text="0")
        self.offset_y_label.pack(side=tk.RIGHT, padx=(10, 0))

        # Reset button
        ttk.Button(image_frame, text="Reset", command=self.reset_adjustments).pack(
            fill=tk.X
        )

    def create_mask_controls(self, parent):
        """Create mask adjustment controls."""
        mask_frame = ttk.LabelFrame(parent, text="🎭 Mask Options", padding="10")
        mask_frame.pack(fill=tk.X, pady=(0, 10))

        # Toggle mask overlay
        ttk.Checkbutton(
            mask_frame,
            text="Show Mask Overlay",
            variable=self.show_mask_overlay,
            command=self.update_preview,
        ).pack(anchor=tk.W)

    def on_scale_change(self, value=None):
        """Handle scale change."""
        self.scale_label.config(text=f"{self.image_scale.get():.2f}")
        self.update_preview()

    def on_offset_change(self, value=None):
        """Handle offset change."""
        self.offset_x_label.config(text=str(self.image_offset_x.get()))
        self.offset_y_label.config(text=str(self.image_offset_y.get()))
        self.update_preview()

    def reset_adjustments(self):
        """Reset all adjustments to defaults."""
        self.image_scale.set(0.8)
        self.image_offset_x.set(0)
        self.image_offset_y.set(0)

    def update_preview(self):
        """Update the preview image."""
        try:
            # Create template with current settings
            template_image = self.template_maker.create_template_image(
                marker_ids=self.marker_ids,
                image_path=self.image_path,
                mask_path=self.mask_path if not self.show_mask_overlay.get() else None,
                image_scale=self.image_scale.get(),
                image_offset_x=self.image_offset_x.get(),
                image_offset_y=self.image_offset_y.get(),
            )

            # Add mask overlay if requested
            if self.show_mask_overlay.get() and self.mask_path:
                template_image = self.add_mask_overlay(template_image)

            self.preview_image = template_image
            self.display_preview()

        except Exception as e:
            print(f"Preview error: {e}")

    def add_mask_overlay(self, template_image):
        """Add semi-transparent mask overlay to preview."""
        if not self.mask_path or not Path(self.mask_path).exists():
            return template_image

        try:
            # Load mask
            mask = cv2.imread(self.mask_path, cv2.IMREAD_GRAYSCALE)
            if mask is None:
                return template_image

            # Resize mask to match image scaling
            template_info = self.template_maker.get_template_info()
            drawing_area_width = int(
                template_info["drawing_area_size"][0] * self.image_scale.get()
            )
            drawing_area_height = int(
                template_info["drawing_area_size"][1] * self.image_scale.get()
            )

            # Maintain aspect ratio
            h, w = mask.shape[:2]
            aspect_ratio = w / h

            if drawing_area_width / drawing_area_height > aspect_ratio:
                new_height = drawing_area_height
                new_width = int(new_height * aspect_ratio)
            else:
                new_width = drawing_area_width
                new_height = int(new_width / aspect_ratio)

            resized_mask = cv2.resize(mask, (new_width, new_height))

            # Create colored overlay
            overlay = template_image.copy()

            # Calculate position
            drawing_x, drawing_y = template_info["drawing_area_position"]
            center_x = drawing_x + template_info["drawing_area_size"][0] // 2
            center_y = drawing_y + template_info["drawing_area_size"][1] // 2

            start_x = center_x - new_width // 2 + self.image_offset_x.get()
            start_y = center_y - new_height // 2 + self.image_offset_y.get()

            end_x = start_x + new_width
            end_y = start_y + new_height

            # Ensure bounds
            start_x = max(0, min(start_x, template_image.shape[1] - new_width))
            start_y = max(0, min(start_y, template_image.shape[0] - new_height))
            end_x = start_x + new_width
            end_y = start_y + new_height

            # Apply colored overlay where mask is active
            mask_area = resized_mask > 128
            overlay[start_y:end_y, start_x:end_x][mask_area] = [
                0,
                255,
                0,
            ]  # Green overlay

            # Blend with original
            result = cv2.addWeighted(template_image, 0.7, overlay, 0.3, 0)
            return result

        except Exception as e:
            print(f"Mask overlay error: {e}")
            return template_image

    def display_preview(self):
        """Display the preview image on canvas."""
        if self.preview_image is None:
            return

        # Calculate display size to fit canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            self.dialog.after(100, self.display_preview)
            return

        img_height, img_width = self.preview_image.shape[:2]

        # Calculate scale to fit canvas
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        scale = min(scale_x, scale_y, 1.0)  # Don't upscale

        # Resize for display
        display_width = int(img_width * scale)
        display_height = int(img_height * scale)

        display_image = cv2.resize(self.preview_image, (display_width, display_height))

        # Convert to RGB for PIL
        display_image_rgb = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(display_image_rgb)
        self.photo_image = ImageTk.PhotoImage(pil_image)

        # Clear canvas and add image
        self.canvas.delete("all")

        # Center image on canvas
        x = (canvas_width - display_width) // 2
        y = (canvas_height - display_height) // 2

        self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo_image)

    def save_template(self):
        """Save the current template."""
        if self.preview_image is None:
            messagebox.showerror("Error", "No template to save")
            return

        # Ask for save location
        filename = filedialog.asksaveasfilename(
            title="Save Template",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        )

        if filename:
            try:
                cv2.imwrite(filename, self.preview_image)
                messagebox.showinfo("Success", f"Template saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save template: {e}")


def preview_template(
    parent, template_maker, marker_ids, image_path=None, mask_path=None
):
    """Convenience function to show template preview."""
    dialog = TemplatePreviewDialog(
        parent, template_maker, marker_ids, image_path, mask_path
    )
    return dialog
