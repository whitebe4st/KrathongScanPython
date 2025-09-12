"""
Image cropping utilities for template maker.
"""

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk


class ImageCropperDialog:
    """Simplified image cropping dialog."""

    def __init__(self, parent, image_path, callback=None):
        """Initialize the cropper dialog."""
        self.parent = parent
        self.image_path = image_path
        self.callback = callback
        self.original_image = cv2.imread(image_path)
        self.cropped_image = None
        self.result_path = None
        self.mask_path = None

        if self.original_image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Crop Image")
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)
        self.dialog.grab_set()  # Make dialog modal

        # Crop variables
        self.crop_x1 = tk.IntVar(value=0)
        self.crop_y1 = tk.IntVar(value=0)
        self.crop_x2 = tk.IntVar(value=self.original_image.shape[1])
        self.crop_y2 = tk.IntVar(value=self.original_image.shape[0])

        # Selection state
        self.is_selecting = False
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.rect_id = None
        self.scale_factor = 1.0

        self.setup_ui()
        self.update_display()

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
        """Setup the cropping interface."""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(
            main_frame, text="🖼️ Image Cropper", font=("Segoe UI", 14, "bold")
        ).pack(pady=(0, 10))

        # Canvas for image display
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.canvas = tk.Canvas(canvas_frame, bg="gray90", cursor="crosshair")

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(
            canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        h_scrollbar = ttk.Scrollbar(
            canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview
        )

        self.canvas.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Bind mouse events
        self.canvas.bind("<Button-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.update_crop)
        self.canvas.bind("<ButtonRelease-1>", self.end_crop)

        # Controls frame
        controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # Coordinate inputs
        coords_frame = ttk.Frame(controls_frame)
        coords_frame.pack(fill=tk.X, pady=(0, 10))

        coord_labels = ["X1:", "Y1:", "X2:", "Y2:"]
        coord_vars = [self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2]

        for i, (label, var) in enumerate(zip(coord_labels, coord_vars)):
            ttk.Label(coords_frame, text=label).grid(row=0, column=i * 2, padx=(0, 5))
            entry = ttk.Entry(coords_frame, textvariable=var, width=8)
            entry.grid(row=0, column=i * 2 + 1, padx=(0, 15))
            var.trace_add("write", lambda *args: self.update_display())

        # Action buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Reset", command=self.reset_crop).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(button_frame, text="Auto Detect", command=self.auto_detect).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(
            button_frame, text="Remove Background", command=self.remove_background
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)

        ttk.Button(bottom_frame, text="Cancel", command=self.cancel).pack(
            side=tk.RIGHT, padx=(10, 0)
        )
        ttk.Button(
            bottom_frame, text="Apply", command=self.apply_crop, style="Accent.TButton"
        ).pack(side=tk.RIGHT)

    def update_display(self):
        """Update the image display with current crop selection."""
        if self.original_image is None:
            return

        # Calculate display size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            self.dialog.after(100, self.update_display)
            return

        img_height, img_width = self.original_image.shape[:2]

        # Calculate scale to fit canvas
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        self.scale_factor = min(scale_x, scale_y, 1.0)  # Don't upscale

        # Resize image for display
        display_width = int(img_width * self.scale_factor)
        display_height = int(img_height * self.scale_factor)

        display_image = cv2.resize(self.original_image, (display_width, display_height))

        # Convert to RGB for PIL
        display_image_rgb = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(display_image_rgb)
        self.photo_image = ImageTk.PhotoImage(pil_image)

        # Clear canvas and add image
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)

        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # Draw crop rectangle
        self.draw_crop_rectangle()

    def draw_crop_rectangle(self):
        """Draw the crop selection rectangle."""
        if self.scale_factor <= 0:
            return

        # Get crop coordinates in display space
        x1 = self.crop_x1.get() * self.scale_factor
        y1 = self.crop_y1.get() * self.scale_factor
        x2 = self.crop_x2.get() * self.scale_factor
        y2 = self.crop_y2.get() * self.scale_factor

        # Draw rectangle
        if self.rect_id:
            self.canvas.delete(self.rect_id)

        self.rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2, outline="red", width=2, dash=(5, 5)
        )

    def start_crop(self, event):
        """Start crop selection."""
        if self.scale_factor <= 0:
            return

        self.is_selecting = True
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)

        # Convert to image coordinates
        img_x = int(self.start_x / self.scale_factor)
        img_y = int(self.start_y / self.scale_factor)

        self.crop_x1.set(img_x)
        self.crop_y1.set(img_y)

    def update_crop(self, event):
        """Update crop selection."""
        if not self.is_selecting or self.scale_factor <= 0:
            return

        self.end_x = self.canvas.canvasx(event.x)
        self.end_y = self.canvas.canvasy(event.y)

        # Convert to image coordinates
        img_x = int(self.end_x / self.scale_factor)
        img_y = int(self.end_y / self.scale_factor)

        # Ensure valid coordinates
        img_height, img_width = self.original_image.shape[:2]
        img_x = max(0, min(img_x, img_width))
        img_y = max(0, min(img_y, img_height))

        self.crop_x2.set(img_x)
        self.crop_y2.set(img_y)

    def end_crop(self, event):
        """End crop selection."""
        self.is_selecting = False

    def reset_crop(self):
        """Reset crop to full image."""
        img_height, img_width = self.original_image.shape[:2]
        self.crop_x1.set(0)
        self.crop_y1.set(0)
        self.crop_x2.set(img_width)
        self.crop_y2.set(img_height)

    def auto_detect(self):
        """Auto-detect object bounds."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)

            # Apply threshold
            _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

            # Find contours
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if contours:
                # Find largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)

                # Add some padding
                padding = 10
                x = max(0, x - padding)
                y = max(0, y - padding)
                w = min(self.original_image.shape[1] - x, w + 2 * padding)
                h = min(self.original_image.shape[0] - y, h + 2 * padding)

                self.crop_x1.set(x)
                self.crop_y1.set(y)
                self.crop_x2.set(x + w)
                self.crop_y2.set(y + h)

        except Exception as e:
            messagebox.showerror(
                "Auto Detect Error", f"Could not auto-detect bounds: {e}"
            )

    def remove_background(self):
        """Remove white background from the image."""
        try:
            from .core import KrathongTemplateMaker

            template_maker = KrathongTemplateMaker()

            processed_image = template_maker.remove_white_background(
                self.original_image
            )
            self.original_image = processed_image
            self.update_display()

            messagebox.showinfo("Success", "Background removed!")

        except Exception as e:
            messagebox.showerror(
                "Background Removal Error", f"Could not remove background: {e}"
            )

    def apply_crop(self):
        """Apply the crop and close dialog."""
        try:
            # Get crop coordinates
            x1 = self.crop_x1.get()
            y1 = self.crop_y1.get()
            x2 = self.crop_x2.get()
            y2 = self.crop_y2.get()

            # Validate coordinates
            if x1 >= x2 or y1 >= y2:
                messagebox.showerror("Invalid Crop", "Please select a valid crop area")
                return

            # Crop image
            self.cropped_image = self.original_image[y1:y2, x1:x2]

            # Save cropped image
            input_path = Path(self.image_path)
            output_dir = input_path.parent

            cropped_filename = f"{input_path.stem}_cropped.png"
            self.result_path = str(output_dir / cropped_filename)
            cv2.imwrite(self.result_path, self.cropped_image)

            # Create mask from cropped image
            from .core import KrathongTemplateMaker

            template_maker = KrathongTemplateMaker()
            mask = template_maker.create_mask_from_image(self.cropped_image)

            mask_filename = f"{input_path.stem}_mask.png"
            self.mask_path = str(output_dir / mask_filename)
            cv2.imwrite(self.mask_path, mask)

            # Call callback if provided
            if self.callback:
                self.callback(self.result_path, self.mask_path)

            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("Crop Error", f"Could not apply crop: {e}")

    def cancel(self):
        """Cancel and close dialog."""
        self.result_path = None
        self.mask_path = None
        self.cropped_image = None
        self.dialog.destroy()


def crop_image(parent, image_path, callback=None):
    """Convenience function to crop an image."""
    dialog = ImageCropperDialog(parent, image_path, callback)
    parent.wait_window(dialog.dialog)
    return dialog.result_path, dialog.mask_path
