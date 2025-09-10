#!/usr/bin/env python3
"""
GUI Krathong Template Maker

A user-friendly graphical interface for creating krathong templates
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


class ImageCropper:
    """Interactive image cropping interface."""

    def __init__(self, parent, image_path, template_maker=None):
        self.parent = parent
        self.template_maker = template_maker
        self.image_path = image_path
        self.original_image = cv2.imread(image_path)
        self.cropped_image = None

        # Create cropping window
        self.window = tk.Toplevel(parent)
        self.window.title("Crop Krathong Image")
        self.window.geometry("1000x700")
        self.window.resizable(True, True)

        # Variables
        self.crop_x1 = tk.IntVar(value=0)
        self.crop_y1 = tk.IntVar(value=0)
        self.crop_x2 = tk.IntVar(value=self.original_image.shape[1])
        self.crop_y2 = tk.IntVar(value=self.original_image.shape[0])
        self.is_selecting = False
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.rect_id = None
        self.scale_factor = 1.0
        self.display_image = None
        self.photo_image = None
        self.canvas_image_id = None

        self.setup_ui()
        self.update_preview()

    def setup_ui(self):
        """Set up the cropping interface."""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Image preview canvas with scrollbars - copied from Testtest.py
        self.canvas_frame = ttk.Frame(main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.canvas = tk.Canvas(self.canvas_frame, bg="gray90", cursor="crosshair")

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(
            self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        h_scrollbar = ttk.Scrollbar(
            self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview
        )

        self.canvas.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Grid layout for canvas and scrollbars
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        # Bind mouse events for interactive cropping
        self.canvas.bind("<Button-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.update_crop)
        self.canvas.bind("<ButtonRelease-1>", self.end_crop)

        # Controls frame
        controls_frame = ttk.LabelFrame(main_frame, text="Crop Controls", padding="10")
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # Crop coordinates
        coords_frame = ttk.Frame(controls_frame)
        coords_frame.pack(fill=tk.X, pady=5)

        ttk.Label(coords_frame, text="X1:").grid(row=0, column=0, padx=(0, 5))
        ttk.Entry(coords_frame, textvariable=self.crop_x1, width=8).grid(
            row=0, column=1, padx=(0, 10)
        )

        ttk.Label(coords_frame, text="Y1:").grid(row=0, column=2, padx=(0, 5))
        ttk.Entry(coords_frame, textvariable=self.crop_y1, width=8).grid(
            row=0, column=3, padx=(0, 10)
        )

        ttk.Label(coords_frame, text="X2:").grid(row=0, column=4, padx=(0, 5))
        ttk.Entry(coords_frame, textvariable=self.crop_x2, width=8).grid(
            row=0, column=5, padx=(0, 10)
        )

        ttk.Label(coords_frame, text="Y2:").grid(row=0, column=6, padx=(0, 5))
        ttk.Entry(coords_frame, textvariable=self.crop_y2, width=8).grid(
            row=0, column=7, padx=(0, 10)
        )

        # Bind coordinate changes to preview update
        for var in [self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2]:
            var.trace_add("write", lambda *args: self.update_preview())

        # Buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="Reset", command=self.reset_crop).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(button_frame, text="Quick Crop", command=self.quick_crop).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(button_frame, text="Free Draw", command=self.enable_free_draw).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(button_frame, text="Preview Crop", command=self.preview_crop).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(
            button_frame, text="Back to Selection", command=self.update_preview
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            button_frame, text="Test BG Removal", command=self.test_background_removal
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            button_frame, text="Smart BG Removal", command=self.smart_background_removal
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            button_frame, text="Remove White BG", command=self.remove_background
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Apply Crop", command=self.apply_crop).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(
            side=tk.RIGHT
        )

    def start_crop(self, event):
        """Start cropping selection - exact copy from Testtest.py."""
        if self.original_image is None:
            return

        self.is_selecting = True
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.end_x = self.start_x
        self.end_y = self.start_y

        # Clear previous selection
        if self.rect_id:
            self.canvas.delete(self.rect_id)

        print(
            f"Debug: Start crop at canvas coords ({self.start_x:.1f}, {self.start_y:.1f})"
        )

    def update_crop(self, event):
        """Update cropping selection - exact copy from Testtest.py."""
        if not self.is_selecting or self.original_image is None:
            return

        self.end_x = self.canvas.canvasx(event.x)
        self.end_y = self.canvas.canvasy(event.y)

        # Update selection rectangle
        if self.rect_id:
            self.canvas.delete(self.rect_id)

        self.rect_id = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.end_x,
            self.end_y,
            outline="blue",
            width=10,
            fill="",
            dash=(20, 10),
            tags="crop_rect",
        )
        # Bring rectangle to front
        self.canvas.tag_raise("crop_rect")
        # Force canvas update
        self.canvas.update_idletasks()

        print(
            f"Debug: Drawing rectangle from ({self.start_x:.1f}, {self.start_y:.1f}) to ({self.end_x:.1f}, {self.end_y:.1f})"
        )

    def end_crop(self, event):
        """End cropping selection - exact copy from Testtest.py."""
        self.is_selecting = False

        if self.original_image is None:
            return

        # Final update of selection
        self.end_x = self.canvas.canvasx(event.x)
        self.end_y = self.canvas.canvasy(event.y)

        # Ensure we have a valid selection
        if abs(self.end_x - self.start_x) < 5 or abs(self.end_y - self.start_y) < 5:
            self.clear_selection()
            return

        # Delete old rectangle and create new one (exact copy from Testtest.py)
        if self.rect_id:
            self.canvas.delete(self.rect_id)

        self.rect_id = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.end_x,
            self.end_y,
            outline="blue",
            width=10,
            fill="",
            dash=(20, 10),
            tags="crop_rect",
        )
        # Bring rectangle to front
        self.canvas.tag_raise("crop_rect")
        # Force canvas update
        self.canvas.update_idletasks()

        print(
            f"Debug: Final rectangle from ({self.start_x:.1f}, {self.start_y:.1f}) to ({self.end_x:.1f}, {self.end_y:.1f})"
        )
        print(f"Debug: Rectangle ID: {self.rect_id}")
        # Debug: Check if rectangle is actually visible
        try:
            coords = self.canvas.coords(self.rect_id)
            print(f"Debug: Rectangle {self.rect_id} coords: {coords}")
        except:
            print(f"Debug: Could not get coords for rectangle {self.rect_id}")

        # Debug: Create a test rectangle to see if canvas is working
        test_rect = self.canvas.create_rectangle(
            10, 10, 50, 50, outline="green", width=5, fill="", dash=(5, 5)
        )
        print(f"Debug: Test rectangle created with ID: {test_rect}")

        # Convert canvas coordinates to image coordinates (exact copy from Testtest.py)
        img_height, img_width = self.original_image.shape[:2]

        # Convert canvas coordinates to image coordinates
        left = min(self.start_x, self.end_x) / self.scale_factor
        top = min(self.start_y, self.end_y) / self.scale_factor
        right = max(self.start_x, self.end_x) / self.scale_factor
        bottom = max(self.start_y, self.end_y) / self.scale_factor

        # Ensure coordinates are within image bounds
        left = max(0, min(left, img_width))
        top = max(0, min(top, img_height))
        right = max(0, min(right, img_width))
        bottom = max(0, min(bottom, img_height))

        # Set crop coordinates
        self.crop_x1.set(int(left))
        self.crop_y1.set(int(top))
        self.crop_x2.set(int(right))
        self.crop_y2.set(int(bottom))

        print(f"Debug: Scale factor: {self.scale_factor:.3f}")
        print(
            f"Debug: Canvas coords: ({self.start_x:.1f}, {self.start_y:.1f}) to ({self.end_x:.1f}, {self.end_y:.1f})"
        )
        print(
            f"Debug: Image coords: ({int(left)}, {int(top)}) to ({int(right)}, {int(bottom)})"
        )

    def clear_selection(self):
        """Clear selection - exact copy from Testtest.py."""
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None

    def quick_crop(self):
        """Quick crop using a simple percentage-based approach."""
        try:
            # Get image dimensions
            img_height, img_width = self.original_image.shape[:2]

            # Simple crop: remove 10% from each side
            margin_x = int(img_width * 0.1)
            margin_y = int(img_height * 0.1)

            x1 = margin_x
            y1 = margin_y
            x2 = img_width - margin_x
            y2 = img_height - margin_y

            self.crop_x1.set(x1)
            self.crop_y1.set(y1)
            self.crop_x2.set(x2)
            self.crop_y2.set(y2)

            self.update_preview()

        except Exception as e:
            print(f"Quick crop error: {e}")

    def enable_free_draw(self):
        """Enable free drawing mode for more flexible cropping."""
        try:
            # Get image dimensions
            img_height, img_width = self.original_image.shape[:2]

            # Set crop to a smaller area in the center for free drawing
            center_x = img_width // 2
            center_y = img_height // 2

            # Create a smaller crop area (20% of image size)
            crop_width = int(img_width * 0.2)
            crop_height = int(img_height * 0.2)

            x1 = center_x - crop_width // 2
            y1 = center_y - crop_height // 2
            x2 = center_x + crop_width // 2
            y2 = center_y + crop_height // 2

            # Ensure coordinates are within image bounds
            x1 = max(0, min(x1, img_width))
            y1 = max(0, min(y1, img_height))
            x2 = max(x1, min(x2, img_width))
            y2 = max(y1, min(y2, img_height))

            self.crop_x1.set(x1)
            self.crop_y1.set(y1)
            self.crop_x2.set(x2)
            self.crop_y2.set(y2)

            self.update_preview()

            print(f"Free draw mode: Set crop to ({x1}, {y1}) to ({x2}, {y2})")

        except Exception as e:
            print(f"Free draw error: {e}")

    def reset_crop(self):
        """Reset crop to full image."""
        self.crop_x1.set(0)
        self.crop_y1.set(0)
        self.crop_x2.set(self.original_image.shape[1])
        self.crop_y2.set(self.original_image.shape[0])

    def preview_crop(self):
        """Show preview of the cropped image."""
        try:
            # Get crop coordinates
            x1, y1 = self.crop_x1.get(), self.crop_y1.get()
            x2, y2 = self.crop_x2.get(), self.crop_y2.get()

            # Ensure valid coordinates
            x1 = max(0, min(x1, self.original_image.shape[1]))
            y1 = max(0, min(y1, self.original_image.shape[0]))
            x2 = max(x1, min(x2, self.original_image.shape[1]))
            y2 = max(y1, min(y2, self.original_image.shape[0]))

            # Crop the image
            cropped = self.original_image[y1:y2, x1:x2]

            if cropped.size == 0:
                return

            # Display the cropped image
            canvas_width = 800
            canvas_height = 500

            # Calculate aspect ratio
            img_height, img_width = cropped.shape[:2]
            aspect_ratio = img_width / img_height

            # Calculate display dimensions
            if aspect_ratio > canvas_width / canvas_height:
                display_width = canvas_width
                display_height = int(canvas_width / aspect_ratio)
            else:
                display_height = canvas_height
                display_width = int(canvas_height * aspect_ratio)

            # Resize image maintaining aspect ratio
            display_image = cv2.resize(cropped, (display_width, display_height))
            display_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)

            pil_image = Image.fromarray(display_image)
            self.photo = ImageTk.PhotoImage(pil_image)

            self.canvas.delete("all")
            # Center the image on canvas
            x_pos = canvas_width // 2
            y_pos = canvas_height // 2
            self.canvas.create_image(x_pos, y_pos, image=self.photo)

        except Exception as e:
            print(f"Preview crop error: {e}")

    def test_background_removal(self):
        """Test background removal on the original image."""
        try:
            # Create template maker instance for background removal
            template_maker = KrathongTemplateMaker()
            # Apply aggressive background removal to original image
            processed = template_maker.remove_white_background_aggressive(
                self.original_image
            )

            # Save test result
            test_path = str(
                Path(self.image_path).parent
                / f"{Path(self.image_path).stem}_bg_removed_aggressive.png"
            )
            cv2.imwrite(test_path, processed)

            print(f"Aggressive background removal test saved to: {test_path}")

        except Exception as e:
            print(f"Test background removal error: {e}")

    def smart_background_removal(self):
        """Apply smart background removal that preserves important details like outlines."""
        if self.cropped_image is not None:
            # Create template maker instance for background removal
            template_maker = KrathongTemplateMaker()
            # Apply smart background removal
            processed = template_maker.remove_white_background_aggressive(
                self.cropped_image
            )
            self.cropped_image = processed
            self.update_preview()

    def remove_background(self):
        """Remove white background from the cropped image."""
        if self.cropped_image is not None:
            # Create template maker instance for background removal
            template_maker = KrathongTemplateMaker()
            # Apply background removal
            processed = template_maker.remove_white_background(self.cropped_image)
            self.cropped_image = processed
            self.update_preview()

    def display_image_on_canvas(self):
        """Display image on canvas - preserve rectangle when redrawing."""
        if self.original_image is None:
            return

        print(f"Debug: display_image_on_canvas called, rect_id: {self.rect_id}")

        # Store rectangle coordinates before clearing if rectangle exists
        rect_coords = None
        if self.rect_id:
            try:
                rect_coords = self.canvas.coords(self.rect_id)
                print(
                    f"Debug: Preserving rectangle {self.rect_id} with coords: {rect_coords}"
                )
            except:
                print(f"Debug: Could not get coords for rectangle {self.rect_id}")
                rect_coords = None

        # Convert OpenCV image to PIL Image
        img_height, img_width = self.original_image.shape[:2]
        display_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(display_image)

        # Calculate scale to fit image in canvas while maintaining aspect ratio
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:  # Canvas not yet initialized
            self.window.after(100, self.display_image_on_canvas)
            return

        # Calculate scale factor to fit image in canvas
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        self.scale_factor = min(scale_x, scale_y, 1.0)  # Don't scale up

        # Resize image for display
        display_width = int(img_width * self.scale_factor)
        display_height = int(img_height * self.scale_factor)

        self.display_image = pil_image.resize(
            (display_width, display_height), Image.Resampling.LANCZOS
        )
        self.photo_image = ImageTk.PhotoImage(self.display_image)

        # Clear canvas and add image
        self.canvas.delete("all")

        self.canvas_image_id = self.canvas.create_image(
            0, 0, anchor=tk.NW, image=self.photo_image
        )

        # Recreate rectangle if it existed
        if rect_coords and len(rect_coords) == 4:
            self.rect_id = self.canvas.create_rectangle(
                rect_coords[0],
                rect_coords[1],
                rect_coords[2],
                rect_coords[3],
                outline="blue",
                width=10,
                fill="",
                dash=(20, 10),
                tags="crop_rect",
            )
            # Bring rectangle to front
            self.canvas.tag_raise("crop_rect")
            print(
                f"Debug: Recreated rectangle {self.rect_id} at {rect_coords} and brought to front"
            )

        # Update canvas scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def update_preview(self):
        """Update the preview - simplified version."""
        self.display_image_on_canvas()

    def draw_image_boundary(self):
        """Draw a boundary around the image area for reference."""
        try:
            # Get original image dimensions
            img_height, img_width = self.original_image.shape[:2]

            # Calculate display dimensions
            canvas_width = 800
            canvas_height = 500
            aspect_ratio = img_width / img_height

            if aspect_ratio > canvas_width / canvas_height:
                display_width = canvas_width
                display_height = int(canvas_width / aspect_ratio)
            else:
                display_height = canvas_height
                display_width = int(canvas_height * aspect_ratio)

            # Calculate offsets for centering
            offset_x = (canvas_width - display_width) // 2
            offset_y = (canvas_height - display_height) // 2

            # Draw boundary rectangle
            self.canvas.create_rectangle(
                offset_x,
                offset_y,
                offset_x + display_width,
                offset_y + display_height,
                outline="blue",
                width=1,
                tags="image_boundary",
            )

        except Exception as e:
            print(f"Image boundary error: {e}")

    def draw_crop_overlay(self):
        """Draw crop overlay on the canvas."""
        try:
            # Get crop coordinates
            x1, y1 = self.crop_x1.get(), self.crop_y1.get()
            x2, y2 = self.crop_x2.get(), self.crop_y2.get()

            # Get original image dimensions
            img_height, img_width = self.original_image.shape[:2]

            # Calculate display dimensions (same as update_preview)
            canvas_width = 800
            canvas_height = 500
            aspect_ratio = img_width / img_height

            if aspect_ratio > canvas_width / canvas_height:
                # Image is wider than canvas
                display_width = canvas_width
                display_height = int(canvas_width / aspect_ratio)
            else:
                # Image is taller than canvas
                display_height = canvas_height
                display_width = int(canvas_height * aspect_ratio)

            # Calculate image position on canvas (centered)
            image_x = (canvas_width - display_width) // 2
            image_y = (canvas_height - display_height) // 2

            # Convert image coordinates to percentages within the image
            x1_pct = x1 / img_width
            y1_pct = y1 / img_height
            x2_pct = x2 / img_width
            y2_pct = y2 / img_height

            # Convert percentages to display coordinates
            display_x1 = x1_pct * display_width
            display_y1 = y1_pct * display_height
            display_x2 = x2_pct * display_width
            display_y2 = y2_pct * display_height

            # Convert to canvas coordinates
            canvas_x1 = image_x + display_x1
            canvas_y1 = image_y + display_y1
            canvas_x2 = image_x + display_x2
            canvas_y2 = image_y + display_y2

            # Draw crop rectangle
            self.canvas.create_rectangle(
                canvas_x1,
                canvas_y1,
                canvas_x2,
                canvas_y2,
                outline="red",
                width=2,
                tags="crop_overlay",
            )

        except Exception as e:
            print(f"Crop overlay error: {e}")

    def apply_crop(self):
        """Apply the crop and return the cropped image path - copied from Testtest.py."""
        if self.original_image is None or not self.rect_id:
            messagebox.showwarning(
                "No Selection",
                "Please make a selection first by dragging on the image.",
            )
            return None

        try:
            # Convert canvas coordinates to image coordinates (exact copy from Testtest.py)
            img_height, img_width = self.original_image.shape[:2]

            # Convert canvas coordinates to image coordinates
            left = min(self.start_x, self.end_x) / self.scale_factor
            top = min(self.start_y, self.end_y) / self.scale_factor
            right = max(self.start_x, self.end_x) / self.scale_factor
            bottom = max(self.start_y, self.end_y) / self.scale_factor

            # Ensure coordinates are within image bounds
            left = max(0, min(left, img_width))
            top = max(0, min(top, img_height))
            right = max(0, min(right, img_width))
            bottom = max(0, min(bottom, img_height))

            # Crop the original image
            crop_box = (int(left), int(top), int(right), int(bottom))

            # Convert OpenCV image to PIL for cropping
            display_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(display_image)
            cropped_pil = pil_image.crop(crop_box)

            # Convert back to OpenCV
            cropped_array = np.array(cropped_pil)
            self.cropped_image = cv2.cvtColor(cropped_array, cv2.COLOR_RGB2BGR)

            # Save cropped image
            cropped_path = str(
                Path(self.image_path).parent
                / f"{Path(self.image_path).stem}_cropped.png"
            )
            cv2.imwrite(cropped_path, self.cropped_image)

            # Generate mask from cropped image
            mask = self.template_maker.generate_mask_from_cropped_image(
                self.cropped_image
            )

            # Save mask in output directory
            output_dir = Path("data/templates")
            output_dir.mkdir(parents=True, exist_ok=True)
            mask_filename = f"{Path(self.image_path).stem}_mask.png"
            mask_path = str(output_dir / mask_filename)
            cv2.imwrite(mask_path, mask)

            crop_width = int(right - left)
            crop_height = int(bottom - top)
            print(f"Image cropped to {crop_width}x{crop_height} pixels")
            print(f"Mask generated and saved to: {mask_path}")

            messagebox.showinfo(
                "Success",
                f"Image cropped and mask generated!\nNew size: {crop_width}x{crop_height} pixels\nMask saved to: {Path(mask_path).name}",
            )

            # Close window and return both paths
            self.window.destroy()
            return cropped_path, mask_path

        except Exception as e:
            messagebox.showerror("Error", f"Could not crop image: {str(e)}")
            return None


class KrathongTemplateMaker:
    """Core template maker for creating krathong templates with ArUco markers."""

    def __init__(self):
        """Initialize the template maker."""
        # Template specifications
        self.template_width = 1270
        self.template_height = 720
        self.drawing_width = 779
        self.drawing_height = 457
        self.drawing_offset_x = (
            self.template_width - self.drawing_width
        ) // 2  # Center the drawing area
        self.drawing_offset_y = (
            self.template_height - self.drawing_height
        ) // 2  # Center the drawing area
        self.marker_size = 100
        self.outline_thickness = 4

        # ArUco dictionary
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    def create_template_image(
        self,
        marker_ids: List[int],
        krathong_image: Optional[np.ndarray] = None,
        scale: float = 0.8,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> np.ndarray:
        """
        Create a template image with ArUco markers and optional krathong image.

        Args:
            marker_ids: List of 4 ArUco marker IDs [top_left, top_right, bottom_left, bottom_right]
            krathong_image: Optional krathong image to place in the template
            scale: Scale factor for the krathong image (0.1 to 1.5)
            offset_x: X offset for krathong image placement
            offset_y: Y offset for krathong image placement

        Returns:
            Template image as numpy array
        """
        # Create white template (BGR format)
        template = (
            np.ones((self.template_height, self.template_width, 3), dtype=np.uint8)
            * 255
        )

        # Generate ArUco markers
        markers = []
        for marker_id in marker_ids:
            marker = cv2.aruco.generateImageMarker(
                self.aruco_dict, marker_id, self.marker_size
            )
            markers.append(marker)

        # Place markers at the corners of the drawing area box (outside the box)
        marker_positions = [
            (
                self.drawing_offset_x - self.marker_size,
                self.drawing_offset_y - self.marker_size,
            ),  # Top-left corner (outside box)
            (
                self.drawing_offset_x + self.drawing_width,
                self.drawing_offset_y - self.marker_size,
            ),  # Top-right corner (outside box)
            (
                self.drawing_offset_x - self.marker_size,
                self.drawing_offset_y + self.drawing_height,
            ),  # Bottom-left corner (outside box)
            (
                self.drawing_offset_x + self.drawing_width,
                self.drawing_offset_y + self.drawing_height,
            ),  # Bottom-right corner (outside box)
        ]

        # Place markers on template
        for i, (marker, pos) in enumerate(zip(markers, marker_positions)):
            x, y = pos
            # Convert grayscale marker to 3-channel BGR if needed
            if len(marker.shape) == 2:
                marker_3ch = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)
            else:
                marker_3ch = marker
            template[y : y + self.marker_size, x : x + self.marker_size] = marker_3ch

        # Draw black outlined box in the center for drawing area
        cv2.rectangle(
            template,
            (self.drawing_offset_x, self.drawing_offset_y),
            (
                self.drawing_offset_x + self.drawing_width,
                self.drawing_offset_y + self.drawing_height,
            ),
            (0, 0, 0),
            self.outline_thickness,
        )

        # Place krathong image if provided
        if krathong_image is not None:
            self._place_krathong_image(
                template, krathong_image, scale, offset_x, offset_y
            )

        return template

    def _place_krathong_image(
        self,
        template: np.ndarray,
        krathong_image: np.ndarray,
        scale: float,
        offset_x: int,
        offset_y: int,
    ):
        """Place krathong image in the drawing area of the template."""
        # Resize krathong image
        height, width = krathong_image.shape[:2]
        new_width = int(width * scale)
        new_height = int(height * scale)

        if new_width > 0 and new_height > 0:
            # Only auto-scale if the image is way too big (more than 2x the drawing area)
            # This allows the user's scale setting to work for reasonable sizes
            if (
                new_width > self.drawing_width * 2
                or new_height > self.drawing_height * 2
            ):
                # Calculate scale to fit within drawing area
                scale_x = self.drawing_width / new_width
                scale_y = self.drawing_height / new_height
                fit_scale = min(scale_x, scale_y) * 0.9  # 90% to leave some margin

                new_width = int(new_width * fit_scale)
                new_height = int(new_height * fit_scale)
                print(
                    f"Debug: Auto-scaled down to fit (image was too large): {new_width}x{new_height}"
                )
            else:
                print(f"Debug: Using user scale setting: {new_width}x{new_height}")

            resized_krathong = cv2.resize(krathong_image, (new_width, new_height))

            # Calculate placement position (center of drawing area + offsets)
            center_x = self.drawing_offset_x + self.drawing_width // 2
            center_y = self.drawing_offset_y + self.drawing_height // 2

            start_x = center_x - new_width // 2 + offset_x
            start_y = center_y - new_height // 2 + offset_y

            # Ensure the image fits within the drawing area
            start_x = max(
                self.drawing_offset_x,
                min(start_x, self.drawing_offset_x + self.drawing_width - new_width),
            )
            start_y = max(
                self.drawing_offset_y,
                min(start_y, self.drawing_offset_y + self.drawing_height - new_height),
            )

            # Place the image
            if (
                start_x >= 0
                and start_y >= 0
                and start_x + new_width <= self.template_width
                and start_y + new_height <= self.template_height
            ):
                if len(resized_krathong.shape) == 3:
                    # Color image - handle transparency properly
                    if resized_krathong.shape[2] == 4:
                        # RGBA image - blend with template background
                        alpha = resized_krathong[:, :, 3] / 255.0
                        alpha = np.stack([alpha, alpha, alpha], axis=2)

                        # Convert RGBA to BGR for blending
                        krathong_bgr = cv2.cvtColor(
                            resized_krathong, cv2.COLOR_RGBA2BGR
                        )

                        # Blend with template background
                        template_roi = template[
                            start_y : start_y + new_height,
                            start_x : start_x + new_width,
                        ]
                        blended = (
                            krathong_bgr * alpha + template_roi * (1 - alpha)
                        ).astype(np.uint8)
                        template[
                            start_y : start_y + new_height,
                            start_x : start_x + new_width,
                        ] = blended
                    else:
                        # BGR image - place directly
                        template[
                            start_y : start_y + new_height,
                            start_x : start_x + new_width,
                        ] = resized_krathong
                else:
                    # Grayscale image - convert to BGR
                    template[
                        start_y : start_y + new_height, start_x : start_x + new_width
                    ] = cv2.cvtColor(resized_krathong, cv2.COLOR_GRAY2BGR)

    def remove_white_background(self, image: np.ndarray) -> np.ndarray:
        """
        Remove ALL white colors from krathong image.
        Aggressive approach to remove white backgrounds.
        """
        if len(image.shape) == 3:
            # Convert to different color spaces for better white detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            hsv = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            lab = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        # Method 1: HSV-based white detection
        # White has low saturation and high value
        lower_white_hsv = np.array([0, 0, 200])  # Low saturation, high value
        upper_white_hsv = np.array([180, 30, 255])
        mask_hsv = cv2.inRange(hsv, lower_white_hsv, upper_white_hsv)

        # Method 2: LAB-based white detection
        # White has high L (lightness) and neutral a, b
        lower_white_lab = np.array([200, 120, 120])  # High L, neutral a, b
        upper_white_lab = np.array([255, 135, 135])
        mask_lab = cv2.inRange(lab, lower_white_lab, upper_white_lab)

        # Method 3: Grayscale threshold
        _, mask_gray = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)

        # Method 4: RGB-based white detection
        if len(image.shape) == 3:
            # White has high values in all RGB channels
            b, g, r = cv2.split(image)
            mask_b = (b > 200).astype(np.uint8) * 255
            mask_g = (g > 200).astype(np.uint8) * 255
            mask_r = (r > 200).astype(np.uint8) * 255
            mask_rgb = cv2.bitwise_and(cv2.bitwise_and(mask_b, mask_g), mask_r)
        else:
            mask_rgb = np.zeros_like(gray)

        # Combine all masks (OR operation - if any method detects white, remove it)
        combined_mask = cv2.bitwise_or(mask_hsv, mask_lab)
        combined_mask = cv2.bitwise_or(combined_mask, mask_gray)
        if len(image.shape) == 3:
            combined_mask = cv2.bitwise_or(combined_mask, mask_rgb)

        # Invert mask so white areas become transparent
        mask = cv2.bitwise_not(combined_mask)

        # Apply morphological operations to clean up the mask
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Create result with alpha channel
        if len(image.shape) == 3:
            result = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            result[:, :, 3] = mask
        else:
            result = image.copy()
            result[mask == 0] = 255

        return result

    def generate_mask_from_cropped_image(self, cropped_image: np.ndarray) -> np.ndarray:
        """
        Generate a mask from a cropped krathong image using mask_maker.py logic.
        Creates a mask with the exact size of the template drawing area (779x457).

        Args:
            cropped_image: The cropped krathong image (BGR format)

        Returns:
            Binary mask as numpy array (0=background, 255=foreground) with size 779x457
        """
        # Convert to grayscale
        gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)

        # Threshold to create binary mask (inverted - white background becomes 0)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Create mask with template drawing area size (779x457)
        mask = np.zeros((self.drawing_height, self.drawing_width), dtype=np.uint8)

        if contours:
            # Find the largest contour (assumed to be the krathong)
            largest_contour = max(contours, key=cv2.contourArea)

            # Get bounding rectangle of the largest contour
            x, y, w, h = cv2.boundingRect(largest_contour)

            # Calculate center position in the template drawing area
            center_x = self.drawing_width // 2
            center_y = self.drawing_height // 2

            # Calculate the position to place the contour in the center
            # Scale the contour to fit within the drawing area if needed
            scale_factor = (
                min(self.drawing_width / w, self.drawing_height / h) * 0.8
            )  # 80% to leave margin

            if scale_factor < 1.0:
                # Scale down the contour
                scaled_contour = largest_contour * scale_factor
            else:
                scaled_contour = largest_contour

            # Get new bounding rectangle after scaling
            x_new, y_new, w_new, h_new = cv2.boundingRect(
                scaled_contour.astype(np.int32)
            )

            # Center the contour in the drawing area
            offset_x = center_x - (x_new + w_new // 2)
            offset_y = center_y - (y_new + h_new // 2)

            # Translate the contour to the center position
            translated_contour = scaled_contour + [offset_x, offset_y]

            # Draw the translated contour onto the mask
            cv2.drawContours(
                mask,
                [translated_contour.astype(np.int32)],
                -1,
                255,
                thickness=cv2.FILLED,
            )

            # Apply morphological operations to clean up the mask
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        return mask

    def remove_white_background_aggressive(self, image: np.ndarray) -> np.ndarray:
        """
        Remove white backgrounds while preserving important details like outlines.
        Balanced approach that removes backgrounds but keeps krathong details.
        """
        if len(image.shape) == 3:
            # Convert to different color spaces for better white detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            hsv = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            lab = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        # Method 1: HSV-based white detection (balanced)
        # White has low saturation and high value
        lower_white_hsv = np.array([0, 0, 220])  # Higher threshold to preserve details
        upper_white_hsv = np.array([180, 30, 255])  # Lower saturation tolerance
        mask_hsv = cv2.inRange(hsv, lower_white_hsv, upper_white_hsv)

        # Method 2: LAB-based white detection (balanced)
        # White has high L (lightness) and neutral a, b
        lower_white_lab = np.array([220, 120, 120])  # Higher L threshold
        upper_white_lab = np.array([255, 135, 135])  # Narrower a, b range
        mask_lab = cv2.inRange(lab, lower_white_lab, upper_white_lab)

        # Method 3: Grayscale threshold (balanced)
        _, mask_gray = cv2.threshold(
            gray, 230, 255, cv2.THRESH_BINARY
        )  # Higher threshold

        # Method 4: RGB-based white detection (balanced)
        if len(image.shape) == 3:
            # White has high values in all RGB channels
            b, g, r = cv2.split(image)
            mask_b = (b > 220).astype(np.uint8) * 255  # Higher threshold
            mask_g = (g > 220).astype(np.uint8) * 255
            mask_r = (r > 220).astype(np.uint8) * 255
            mask_rgb = cv2.bitwise_and(cv2.bitwise_and(mask_b, mask_g), mask_r)
        else:
            mask_rgb = np.zeros_like(gray)

        # Method 5: Edge preservation - don't remove areas near edges
        edges = cv2.Canny(gray, 50, 150)
        edges_dilated = cv2.dilate(edges, np.ones((5, 5), np.uint8), iterations=2)

        # Combine masks but exclude areas near edges
        combined_mask = cv2.bitwise_or(mask_hsv, mask_lab)
        combined_mask = cv2.bitwise_or(combined_mask, mask_gray)
        if len(image.shape) == 3:
            combined_mask = cv2.bitwise_or(combined_mask, mask_rgb)

        # Remove edge areas from the mask to preserve outlines
        combined_mask = cv2.bitwise_and(combined_mask, cv2.bitwise_not(edges_dilated))

        # Invert mask so white areas become transparent
        mask = cv2.bitwise_not(combined_mask)

        # Apply gentle morphological operations to preserve details
        kernel = np.ones((3, 3), np.uint8)  # Smaller kernel
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Create result with alpha channel
        if len(image.shape) == 3:
            result = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            result[:, :, 3] = mask
        else:
            result = image.copy()
            result[mask == 0] = 255

        return result

    def create_mask(self, krathong_image: np.ndarray) -> np.ndarray:
        """
        Create mask from krathong image.
        Based on mask_maker.py logic.
        """
        if len(krathong_image.shape) == 3:
            gray = cv2.cvtColor(krathong_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = krathong_image.copy()

        # Threshold
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Create mask
        mask = np.zeros_like(gray)
        cv2.drawContours(mask, contours, -1, 255, thickness=cv2.FILLED)

        return mask


class TemplatePreviewWindow:
    """Preview window for template visualization."""

    def __init__(
        self,
        parent,
        template_maker,
        marker_ids,
        image_path=None,
        image_scale=0.8,
        image_offset_x=0,
        image_offset_y=0,
        mask_path=None,
    ):
        """Initialize preview window."""
        self.parent = parent
        self.template_maker = template_maker
        self.marker_ids = marker_ids
        self.image_path = image_path
        self.image_scale = image_scale
        self.image_offset_x = image_offset_x
        self.image_offset_y = image_offset_y
        self.mask_path = mask_path

        # Load krathong image if provided
        self.krathong_image = None
        if image_path and os.path.exists(image_path):
            self.krathong_image = cv2.imread(image_path)
            if self.krathong_image is not None:
                # Remove white background using smart method
                self.krathong_image = (
                    self.template_maker.remove_white_background_aggressive(
                        self.krathong_image
                    )
                )

        # Load mask if provided
        self.mask_image = None
        self.mask_path_var = tk.StringVar(value=mask_path or "")
        if mask_path and os.path.exists(mask_path):
            self.mask_image = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

        # Create preview window
        self.window = tk.Toplevel(parent)
        self.window.title("Template Preview")
        self.window.geometry("1000x700")
        self.window.resizable(True, True)

        # Variables for interactive adjustment
        self.final_scale = image_scale
        self.final_offset_x = image_offset_x
        self.final_offset_y = image_offset_y

        self.setup_preview_ui()
        self.update_preview()

    def setup_preview_ui(self):
        """Set up the preview interface."""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Preview canvas
        self.canvas_frame = ttk.Frame(main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.canvas = tk.Canvas(self.canvas_frame, bg="white", width=640, height=480)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Controls frame
        controls_frame = ttk.LabelFrame(main_frame, text="Adjust Image", padding="10")
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # Scale control
        scale_frame = ttk.Frame(controls_frame)
        scale_frame.pack(fill=tk.X, pady=5)

        ttk.Label(scale_frame, text="Scale:").pack(side=tk.LEFT)
        self.scale_var = tk.DoubleVar(value=self.image_scale)
        scale_scale = ttk.Scale(
            scale_frame,
            from_=0.1,
            to=1.5,
            variable=self.scale_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.on_scale_change,
        )
        scale_scale.pack(side=tk.LEFT, padx=(10, 0))
        self.scale_label = ttk.Label(scale_frame, text=f"{self.image_scale:.2f}")
        self.scale_label.pack(side=tk.LEFT, padx=(10, 0))

        # Offset controls
        offset_frame = ttk.Frame(controls_frame)
        offset_frame.pack(fill=tk.X, pady=5)

        # X offset
        ttk.Label(offset_frame, text="X Offset:").pack(side=tk.LEFT)
        self.offset_x_var = tk.IntVar(value=self.image_offset_x)
        x_scale = ttk.Scale(
            offset_frame,
            from_=-200,
            to=200,
            variable=self.offset_x_var,
            orient=tk.HORIZONTAL,
            length=150,
            command=self.on_offset_change,
        )
        x_scale.pack(side=tk.LEFT, padx=(10, 0))
        self.offset_x_label = ttk.Label(offset_frame, text=str(self.image_offset_x))
        self.offset_x_label.pack(side=tk.LEFT, padx=(10, 0))

        # Y offset
        ttk.Label(offset_frame, text="Y Offset:").pack(side=tk.LEFT, padx=(20, 0))
        self.offset_y_var = tk.IntVar(value=self.image_offset_y)
        y_scale = ttk.Scale(
            offset_frame,
            from_=-200,
            to=200,
            variable=self.offset_y_var,
            orient=tk.HORIZONTAL,
            length=150,
            command=self.on_offset_change,
        )
        y_scale.pack(side=tk.LEFT, padx=(10, 0))
        self.offset_y_label = ttk.Label(offset_frame, text=str(self.image_offset_y))
        self.offset_y_label.pack(side=tk.LEFT, padx=(10, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        # Mask overlay toggle
        self.show_mask_var = tk.BooleanVar(value=False)
        mask_toggle = ttk.Checkbutton(
            button_frame,
            text="Show Mask Overlay",
            variable=self.show_mask_var,
            command=self.toggle_mask_overlay,
        )
        mask_toggle.pack(side=tk.LEFT, padx=(0, 10))

        # Mask path selection button
        mask_path_btn = ttk.Button(
            button_frame, text="Select Mask", command=self.select_mask_path
        )
        mask_path_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Mask controls frame
        mask_controls_frame = ttk.Frame(button_frame)
        mask_controls_frame.pack(side=tk.LEFT, padx=(0, 10))

        # Mask scale adjustment
        mask_scale_frame = ttk.Frame(mask_controls_frame)
        mask_scale_frame.pack(side=tk.TOP, pady=(0, 5))

        ttk.Label(mask_scale_frame, text="Scale:").pack(side=tk.LEFT)

        # Scale decrease button
        scale_dec_btn = ttk.Button(
            mask_scale_frame,
            text="◀",
            width=2,
            command=lambda: self.adjust_mask_scale(-0.05),
        )
        scale_dec_btn.pack(side=tk.LEFT, padx=(5, 2))

        self.mask_scale_var = tk.DoubleVar(value=1.0)
        mask_scale_scale = ttk.Scale(
            mask_scale_frame,
            from_=0.1,
            to=3.0,
            variable=self.mask_scale_var,
            orient=tk.HORIZONTAL,
            length=60,
            command=self.on_mask_scale_change,
        )
        mask_scale_scale.pack(side=tk.LEFT, padx=(2, 2))

        # Scale increase button
        scale_inc_btn = ttk.Button(
            mask_scale_frame,
            text="▶",
            width=2,
            command=lambda: self.adjust_mask_scale(0.05),
        )
        scale_inc_btn.pack(side=tk.LEFT, padx=(2, 5))

        self.mask_scale_label = ttk.Label(mask_scale_frame, text="1.0x")
        self.mask_scale_label.pack(side=tk.LEFT)

        # Mask offset controls
        mask_offset_frame = ttk.Frame(mask_controls_frame)
        mask_offset_frame.pack(side=tk.TOP)

        # X offset controls
        ttk.Label(mask_offset_frame, text="X:").pack(side=tk.LEFT)

        # X decrease button
        x_dec_btn = ttk.Button(
            mask_offset_frame,
            text="◀",
            width=2,
            command=lambda: self.adjust_mask_offset_x(-1),
        )
        x_dec_btn.pack(side=tk.LEFT, padx=(2, 1))

        self.mask_offset_x_var = tk.IntVar(value=0)
        mask_x_scale = ttk.Scale(
            mask_offset_frame,
            from_=-200,
            to=200,
            variable=self.mask_offset_x_var,
            orient=tk.HORIZONTAL,
            length=40,
            command=self.on_mask_offset_change,
        )
        mask_x_scale.pack(side=tk.LEFT, padx=(1, 1))

        # X increase button
        x_inc_btn = ttk.Button(
            mask_offset_frame,
            text="▶",
            width=2,
            command=lambda: self.adjust_mask_offset_x(1),
        )
        x_inc_btn.pack(side=tk.LEFT, padx=(1, 5))

        # Y offset controls
        ttk.Label(mask_offset_frame, text="Y:").pack(side=tk.LEFT)

        # Y decrease button
        y_dec_btn = ttk.Button(
            mask_offset_frame,
            text="◀",
            width=2,
            command=lambda: self.adjust_mask_offset_y(-1),
        )
        y_dec_btn.pack(side=tk.LEFT, padx=(2, 1))

        self.mask_offset_y_var = tk.IntVar(value=0)
        mask_y_scale = ttk.Scale(
            mask_offset_frame,
            from_=-200,
            to=200,
            variable=self.mask_offset_y_var,
            orient=tk.HORIZONTAL,
            length=40,
            command=self.on_mask_offset_change,
        )
        mask_y_scale.pack(side=tk.LEFT, padx=(1, 1))

        # Y increase button
        y_inc_btn = ttk.Button(
            mask_offset_frame,
            text="▶",
            width=2,
            command=lambda: self.adjust_mask_offset_y(1),
        )
        y_inc_btn.pack(side=tk.LEFT, padx=(1, 5))

        ttk.Button(
            button_frame, text="Create Template", command=self.create_template
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(
            side=tk.RIGHT
        )

    def on_scale_change(self, value):
        """Handle scale changes."""
        self.final_scale = float(value)
        self.scale_label.config(text=f"{self.final_scale:.2f}")
        self.update_preview()

    def on_offset_change(self, value):
        """Handle offset changes."""
        self.final_offset_x = self.offset_x_var.get()
        self.final_offset_y = self.offset_y_var.get()
        self.offset_x_label.config(text=str(self.final_offset_x))
        self.offset_y_label.config(text=str(self.final_offset_y))
        self.update_preview()

    def update_preview(self):
        """Update the preview image."""
        try:
            # Generate preview using template maker
            preview_image = self.template_maker.create_template_image(
                marker_ids=self.marker_ids,
                krathong_image=self.krathong_image,
                scale=self.final_scale,
                offset_x=self.final_offset_x,
                offset_y=self.final_offset_y,
            )

            # Add mask overlay if enabled and mask is available
            if (
                self.show_mask_var.get()
                and self.mask_image is not None
                and self.krathong_image is not None
            ):
                preview_image = self.add_mask_overlay(preview_image)

            # Convert to PhotoImage and display
            if preview_image is not None and preview_image.size > 0:
                # Resize for display (maintain aspect ratio)
                display_width = 800
                display_height = int(
                    display_width * preview_image.shape[0] / preview_image.shape[1]
                )
                preview_image = cv2.resize(
                    preview_image, (display_width, display_height)
                )

                # Convert BGR to RGB for PIL
                preview_image = cv2.cvtColor(preview_image, cv2.COLOR_BGR2RGB)

                pil_image = Image.fromarray(preview_image)
                self.photo = ImageTk.PhotoImage(pil_image)

                self.canvas.delete("all")
                self.canvas.create_image(400, display_height // 2, image=self.photo)
            else:
                # Show placeholder if no image generated
                self.canvas.delete("all")
                self.canvas.create_text(
                    400, 200, text="No preview available", fill="gray"
                )

        except Exception as e:
            print(f"Preview update error: {e}")
            import traceback

            traceback.print_exc()
            # Show a placeholder if preview fails
            self.canvas.delete("all")
            self.canvas.create_text(
                400, 200, text=f"Preview Error: {str(e)[:50]}...", fill="red"
            )

    def add_mask_overlay(self, template_image):
        """
        Add mask overlay to the template image.
        The mask is already the correct size (779x457) and positioned correctly.

        Args:
            template_image: The template image (BGR format)

        Returns:
            Template image with mask overlay (BGR format)
        """
        if self.mask_image is None:
            return template_image

        # Create a copy of the template
        result = template_image.copy()

        # Apply mask scale
        mask_scale = self.mask_scale_var.get()
        original_mask_height, original_mask_width = self.mask_image.shape[:2]
        scaled_mask_width = int(original_mask_width * mask_scale)
        scaled_mask_height = int(original_mask_height * mask_scale)

        # Resize mask to the scaled size
        scaled_mask = cv2.resize(
            self.mask_image,
            (scaled_mask_width, scaled_mask_height),
            interpolation=cv2.INTER_NEAREST,
        )

        # Center the scaled mask in the drawing area and apply user offsets
        drawing_x = self.template_maker.drawing_offset_x
        drawing_y = self.template_maker.drawing_offset_y
        drawing_center_x = drawing_x + self.template_maker.drawing_width // 2
        drawing_center_y = drawing_y + self.template_maker.drawing_height // 2

        # Get user-defined offsets
        offset_x = self.mask_offset_x_var.get()
        offset_y = self.mask_offset_y_var.get()

        # Calculate the top-left corner of the scaled mask with offsets
        mask_start_x = drawing_center_x - scaled_mask_width // 2 + offset_x
        mask_start_y = drawing_center_y - scaled_mask_height // 2 + offset_y

        # Ensure the mask fits within the template bounds
        template_height, template_width = template_image.shape[:2]

        # Calculate the actual area to overlay
        end_x = min(mask_start_x + scaled_mask_width, template_width)
        end_y = min(mask_start_y + scaled_mask_height, template_height)
        actual_start_x = max(0, mask_start_x)
        actual_start_y = max(0, mask_start_y)
        actual_width = end_x - actual_start_x
        actual_height = end_y - actual_start_y

        if actual_width > 0 and actual_height > 0:
            # Create a colored overlay (green with transparency)
            overlay = result.copy()
            overlay[actual_start_y:end_y, actual_start_x:end_x] = [
                0,
                255,
                0,
            ]  # Green overlay

            # Calculate the corresponding region in the scaled mask
            mask_offset_x = actual_start_x - mask_start_x
            mask_offset_y = actual_start_y - mask_start_y
            mask_region = scaled_mask[
                mask_offset_y : mask_offset_y + actual_height,
                mask_offset_x : mask_offset_x + actual_width,
            ]

            # Apply mask to create semi-transparent overlay
            mask_3ch = cv2.cvtColor(mask_region, cv2.COLOR_GRAY2BGR)
            mask_normalized = mask_3ch.astype(np.float32) / 255.0

            # Blend the overlay with the template
            template_region = result[actual_start_y:end_y, actual_start_x:end_x].astype(
                np.float32
            )
            overlay_region = overlay[actual_start_y:end_y, actual_start_x:end_x].astype(
                np.float32
            )

            blended = template_region * (1 - mask_normalized * 0.5) + overlay_region * (
                mask_normalized * 0.5
            )
            result[actual_start_y:end_y, actual_start_x:end_x] = blended.astype(
                np.uint8
            )

        return result

    def toggle_mask_overlay(self):
        """Toggle mask overlay on/off."""
        self.update_preview()

    def select_mask_path(self):
        """Open file dialog to select a mask image."""
        from tkinter import filedialog

        file_path = filedialog.askopenfilename(
            title="Select Mask Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("PNG files", "*.png"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            try:
                # Load the new mask
                self.mask_image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
                if self.mask_image is not None:
                    self.mask_path_var.set(file_path)
                    self.mask_path = file_path
                    print(f"Mask loaded: {file_path}")
                    print(f"Mask size: {self.mask_image.shape}")

                    # Update preview if mask overlay is enabled
                    if self.show_mask_var.get():
                        self.update_preview()
                else:
                    messagebox.showerror("Error", "Could not load the mask image file.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load mask: {e}")

    def on_mask_scale_change(self, value=None):
        """Handle mask scale change."""
        scale_value = self.mask_scale_var.get()
        self.mask_scale_label.config(text=f"{scale_value:.1f}x")
        if self.show_mask_var.get():
            self.update_preview()

    def on_mask_offset_change(self, value=None):
        """Handle mask offset change."""
        if self.show_mask_var.get():
            self.update_preview()

    def adjust_mask_scale(self, delta):
        """Adjust mask scale by a small amount."""
        current_scale = self.mask_scale_var.get()
        new_scale = max(0.1, min(3.0, current_scale + delta))
        self.mask_scale_var.set(new_scale)
        self.on_mask_scale_change()

    def adjust_mask_offset_x(self, delta):
        """Adjust mask X offset by a small amount."""
        current_x = self.mask_offset_x_var.get()
        new_x = max(-200, min(200, current_x + delta))
        self.mask_offset_x_var.set(new_x)
        self.on_mask_offset_change()

    def adjust_mask_offset_y(self, delta):
        """Adjust mask Y offset by a small amount."""
        current_y = self.mask_offset_y_var.get()
        new_y = max(-200, min(200, current_y + delta))
        self.mask_offset_y_var.set(new_y)
        self.on_mask_offset_change()

    def save_adjusted_mask(self):
        """Save the adjusted mask with current scale and offset settings."""
        if self.mask_image is None:
            return

        # Apply the same scaling and positioning logic as in add_mask_overlay
        mask_scale = self.mask_scale_var.get()
        original_mask_height, original_mask_width = self.mask_image.shape[:2]
        scaled_mask_width = int(original_mask_width * mask_scale)
        scaled_mask_height = int(original_mask_height * mask_scale)

        # Resize mask to the scaled size
        scaled_mask = cv2.resize(
            self.mask_image,
            (scaled_mask_width, scaled_mask_height),
            interpolation=cv2.INTER_NEAREST,
        )

        # Create a new mask with the exact template drawing area size (779x457)
        final_mask = np.zeros(
            (self.template_maker.drawing_height, self.template_maker.drawing_width),
            dtype=np.uint8,
        )

        # Center the scaled mask in the drawing area and apply user offsets
        drawing_center_x = self.template_maker.drawing_width // 2
        drawing_center_y = self.template_maker.drawing_height // 2

        # Get user-defined offsets
        offset_x = self.mask_offset_x_var.get()
        offset_y = self.mask_offset_y_var.get()

        # Calculate the top-left corner of the scaled mask with offsets
        mask_start_x = drawing_center_x - scaled_mask_width // 2 + offset_x
        mask_start_y = drawing_center_y - scaled_mask_height // 2 + offset_y

        # Calculate the actual area to place the mask
        end_x = min(mask_start_x + scaled_mask_width, self.template_maker.drawing_width)
        end_y = min(
            mask_start_y + scaled_mask_height, self.template_maker.drawing_height
        )
        actual_start_x = max(0, mask_start_x)
        actual_start_y = max(0, mask_start_y)
        actual_width = end_x - actual_start_x
        actual_height = end_y - actual_start_y

        if actual_width > 0 and actual_height > 0:
            # Calculate the corresponding region in the scaled mask
            mask_offset_x = actual_start_x - mask_start_x
            mask_offset_y = actual_start_y - mask_start_y
            mask_region = scaled_mask[
                mask_offset_y : mask_offset_y + actual_height,
                mask_offset_x : mask_offset_x + actual_width,
            ]

            # Place the mask region in the final mask
            final_mask[actual_start_y:end_y, actual_start_x:end_x] = mask_region

        # Save the adjusted mask in the output directory with template name
        # Get the template name from the parent window
        template_name = ""
        if hasattr(self.parent, "template_name_var"):
            template_name = self.parent.template_name_var.get().strip()

        if template_name:
            # Create output directory path (same as template output)
            output_dir = Path("data/templates")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Create mask filename with template name and adjusted suffix
            mask_filename = f"{template_name}_mask_adjusted.png"
            mask_path = output_dir / mask_filename

            cv2.imwrite(str(mask_path), final_mask)

            # Update the mask path to point to the new location
            self.mask_path_var.set(str(mask_path))

            print(f"Adjusted mask saved to: {mask_path}")
            messagebox.showinfo("Success", f"Adjusted mask saved to:\n{mask_filename}")
        else:
            # Fallback to original behavior if no template name
            mask_path = self.mask_path_var.get().strip()
            if mask_path and os.path.exists(mask_path):
                original_path = Path(mask_path)
                adjusted_path = (
                    original_path.parent
                    / f"{original_path.stem}_adjusted{original_path.suffix}"
                )
                cv2.imwrite(str(adjusted_path), final_mask)
                self.mask_path_var.set(str(adjusted_path))
                print(f"Adjusted mask saved to: {adjusted_path}")
                messagebox.showinfo(
                    "Success", f"Adjusted mask saved to:\n{adjusted_path.name}"
                )

    def create_template(self):
        """Create template with current settings and save adjusted mask."""
        try:
            # Save the adjusted mask if mask overlay is enabled and mask exists
            if self.show_mask_var.get() and self.mask_image is not None:
                self.save_adjusted_mask()

            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save adjusted mask: {e}")
        self.window.destroy()


class TemplateMarkerGUI:
    """GUI application for creating krathong templates."""

    def __init__(self):
        """Initialize the GUI application."""
        self.root = tk.Tk()
        self.root.title("Krathong Template Maker")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Initialize template maker
        try:
            self.template_maker = KrathongTemplateMaker()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize template maker: {e}")
            sys.exit(1)

        # Variables
        self.template_name_var = tk.StringVar(value="my_template")
        self.output_dir_var = tk.StringVar(value="data/templates")
        self.marker_vars = [tk.StringVar(value=str(i)) for i in range(4)]
        self.progress_var = tk.StringVar(value="Ready")
        self.status_var = tk.StringVar(value="Ready to create templates")

        # Image placement variables
        self.image_path_var = tk.StringVar(value="")
        self.mask_path_var = tk.StringVar(value="")

        # Adjusted values from preview window
        self.adjusted_scale = 0.8
        self.adjusted_offset_x = 0
        self.adjusted_offset_y = 0

        # Mask generation variables
        self.last_generated_mask = None

        # Setup UI
        self.setup_styles()
        self.create_widgets()
        self.center_window()

    def setup_styles(self):
        """Setup modern styles for the GUI."""
        style = ttk.Style()

        # Configure styles
        style.configure("Title.TLabel", font=("Arial", 16, "bold"))
        style.configure("Heading.TLabel", font=("Arial", 12, "bold"))
        style.configure("Info.TLabel", font=("Arial", 10))

    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        """Create all GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame, text="🎯 Krathong Template Maker", style="Title.TLabel"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Template specifications info
        self.create_info_section(main_frame, 1)

        # Template creation section
        self.create_template_section(main_frame, 2)

        # Batch creation section
        self.create_batch_section(main_frame, 3)

        # Output section
        self.create_output_section(main_frame, 4)

        # Status bar
        self.create_status_bar(main_frame, 5)

    def create_info_section(self, parent, row):
        """Create the information section."""
        info_frame = ttk.LabelFrame(
            parent, text="📋 Template Specifications", padding="10"
        )
        info_frame.grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        info_text = (
            "Template Size: 1270×720 pixels | "
            "Drawing Area: 779×457 pixels (centered) | "
            "Marker Size: 100×100 pixels\n"
            "ArUco Dictionary: 4X4_50 | "
            "Supported Formats: PNG, JPG | "
            "Max Image Scale: 150%"
        )

        info_label = ttk.Label(info_frame, text=info_text, style="Info.TLabel")
        info_label.grid(row=0, column=0, sticky=(tk.W, tk.E))

    def create_template_section(self, parent, row):
        """Create the single template creation section."""
        template_frame = ttk.LabelFrame(
            parent, text="🎨 Single Template Creation", padding="10"
        )
        template_frame.grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        template_frame.columnconfigure(1, weight=1)

        # Template name
        ttk.Label(template_frame, text="Template Name:", style="Heading.TLabel").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 5)
        )
        name_entry = ttk.Entry(
            template_frame, textvariable=self.template_name_var, width=30
        )
        name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))

        # Output directory
        ttk.Label(
            template_frame, text="Output Directory:", style="Heading.TLabel"
        ).grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        output_frame = ttk.Frame(template_frame)
        output_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(5, 0))
        output_frame.columnconfigure(0, weight=1)

        output_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var)
        output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        browse_btn = ttk.Button(
            output_frame, text="Browse", command=self.browse_output_directory
        )
        browse_btn.grid(row=0, column=1)

        # Marker IDs
        markers_frame = ttk.LabelFrame(
            template_frame, text="ArUco Marker IDs (0-49)", padding="5"
        )
        markers_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0)
        )

        marker_labels = ["Top-left:", "Top-right:", "Bottom-left:", "Bottom-right:"]
        for i, label in enumerate(marker_labels):
            ttk.Label(markers_frame, text=label).grid(
                row=i // 2, column=(i % 2) * 2, sticky=tk.W, padx=(0, 5), pady=2
            )
            marker_entry = ttk.Entry(
                markers_frame, textvariable=self.marker_vars[i], width=10
            )
            marker_entry.grid(row=i // 2, column=(i % 2) * 2 + 1, padx=(0, 20), pady=2)

        # Quick preset buttons
        preset_frame = ttk.Frame(template_frame)
        preset_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))

        ttk.Label(preset_frame, text="Quick Presets:").grid(
            row=0, column=0, padx=(0, 10)
        )

        preset_configs = [
            ("0,1,2,3", [0, 1, 2, 3]),
            ("4,5,6,7", [4, 5, 6, 7]),
            ("8,9,10,11", [8, 9, 10, 11]),
            ("Random", None),
        ]

        for i, (label, markers) in enumerate(preset_configs):
            btn = ttk.Button(
                preset_frame,
                text=label,
                command=lambda m=markers: self.set_marker_preset(m),
            )
            btn.grid(row=0, column=i + 1, padx=5)

        # Image file selection
        image_frame = ttk.LabelFrame(
            template_frame, text="🖼️ Optional Image", padding="5"
        )
        image_frame.grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0)
        )
        image_frame.columnconfigure(0, weight=1)

        image_file_frame = ttk.Frame(image_frame)
        image_file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        image_file_frame.columnconfigure(0, weight=1)

        image_entry = ttk.Entry(image_file_frame, textvariable=self.image_path_var)
        image_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        browse_image_btn = ttk.Button(
            image_file_frame, text="Browse & Crop Image", command=self.browse_image_file
        )
        browse_image_btn.grid(row=0, column=1)

        crop_image_btn = ttk.Button(
            image_file_frame, text="Remove White BG", command=self.crop_current_image
        )
        crop_image_btn.grid(row=0, column=2, padx=(5, 0))

        clear_image_btn = ttk.Button(
            image_file_frame, text="Clear", command=lambda: self.image_path_var.set("")
        )
        clear_image_btn.grid(row=0, column=3, padx=(5, 0))

        # Image controls
        controls_frame = ttk.Frame(image_frame)
        controls_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0)
        )

        # Buttons frame
        buttons_frame = ttk.Frame(template_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=(15, 0))

        # Main action buttons
        ttk.Button(
            buttons_frame, text="🎯 Create Template", command=self.create_single_template
        ).grid(row=0, column=0, padx=(0, 10))

        ttk.Button(
            buttons_frame, text="👁️ Preview Template", command=self.preview_template
        ).grid(row=0, column=1, padx=(0, 10))

        ttk.Button(
            buttons_frame,
            text="🔄 Update Live Preview",
            command=self.update_live_preview,
        ).grid(row=0, column=2)

    def create_batch_section(self, parent, row):
        """Create the batch creation section."""
        batch_frame = ttk.LabelFrame(parent, text="🏭 Batch Creation", padding="10")
        batch_frame.grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        batch_frame.columnconfigure(0, weight=1)

        # Buttons frame
        buttons_frame = ttk.Frame(batch_frame)
        buttons_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Sequential templates
        sequential_btn = ttk.Button(
            buttons_frame,
            text="📊 Create Sequential Templates",
            command=self.create_sequential_templates,
        )
        sequential_btn.grid(row=0, column=0, padx=(0, 10), pady=5)

        # From config file
        config_btn = ttk.Button(
            buttons_frame,
            text="📄 Create from Config File",
            command=self.create_from_config,
        )
        config_btn.grid(row=0, column=1, padx=(0, 10), pady=5)

        # Create sample config
        sample_btn = ttk.Button(
            buttons_frame,
            text="📝 Create Sample Config",
            command=self.create_sample_config,
        )
        sample_btn.grid(row=0, column=2, pady=5)

    def create_output_section(self, parent, row):
        """Create the output and management section."""
        output_frame = ttk.LabelFrame(
            parent, text="📁 Template Management", padding="10"
        )
        output_frame.grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        # Buttons frame
        mgmt_frame = ttk.Frame(output_frame)
        mgmt_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # List templates
        list_btn = ttk.Button(
            mgmt_frame, text="📋 List Templates", command=self.list_templates
        )
        list_btn.grid(row=0, column=0, padx=(0, 10), pady=5)

        # Open output folder
        folder_btn = ttk.Button(
            mgmt_frame, text="📂 Open Output Folder", command=self.open_output_folder
        )
        folder_btn.grid(row=0, column=1, padx=(0, 10), pady=5)

        # View specifications
        specs_btn = ttk.Button(
            mgmt_frame, text="📐 View Specifications", command=self.show_specifications
        )
        specs_btn.grid(row=0, column=2, pady=5)

    def create_status_bar(self, parent, row):
        """Create the status bar."""
        status_frame = ttk.Frame(parent)
        status_frame.grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0)
        )
        status_frame.columnconfigure(0, weight=1)

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            status_frame, mode="indeterminate", length=200
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))

        # Status label
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=1)

    def set_marker_preset(self, markers):
        """Set marker IDs from preset."""
        if markers is None:
            # Generate random markers
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
        """Browse for krathong image file with processing options."""
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
            # Open cropping interface immediately after selection
            self.open_image_cropper(filename)

    def open_image_cropper(self, image_path):
        """Open the image cropping interface."""
        try:
            cropper = ImageCropper(self.root, image_path, self.template_maker)
            # Wait for cropping to complete
            self.root.wait_window(cropper.window)

            # Check if user applied crop
            if hasattr(cropper, "cropped_image") and cropper.cropped_image is not None:
                # The cropper now returns both cropped_path and mask_path
                result = cropper.apply_crop()
                if result and len(result) == 2:
                    cropped_path, mask_path = result
                    # Set the cropped image as the selected image
                    self.image_path_var.set(cropped_path)
                    # Store mask path for later use
                    self.mask_path_var.set(mask_path)
                    self.update_status(
                        f"Cropped image: {Path(cropped_path).name}, Mask: {Path(mask_path).name}"
                    )
                else:
                    # Fallback to old method if apply_crop wasn't called
                    cropped_path = str(
                        Path(image_path).parent / f"{Path(image_path).stem}_cropped.png"
                    )
                    cv2.imwrite(cropped_path, cropper.cropped_image)
                    self.image_path_var.set(cropped_path)
                    self.update_status(f"Cropped image: {Path(cropped_path).name}")
            else:
                # User cancelled, use original image
                self.image_path_var.set(image_path)
                self.update_status(f"Selected image: {Path(image_path).name}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image cropper: {e}")
            # Fallback to original image
            self.image_path_var.set(image_path)
            self.update_status(f"Selected image: {Path(image_path).name}")

    def crop_current_image(self):
        """Process the currently selected image to remove white background."""
        image_path = self.image_path_var.get().strip()
        if not image_path:
            messagebox.showwarning("No Image", "Please select an image first.")
            return

        if not Path(image_path).exists():
            messagebox.showerror(
                "File Not Found", f"Image file not found: {image_path}"
            )
            return

        try:
            # Load the image
            image = cv2.imread(image_path)
            if image is None:
                messagebox.showerror("Error", "Could not load the image file.")
                return

            # Remove white background
            processed_image = self.template_maker.remove_white_background(image)

            # Save processed image
            processed_path = str(
                Path(image_path).parent / f"{Path(image_path).stem}_processed.png"
            )
            cv2.imwrite(processed_path, processed_image)

            # Update the image path
            self.image_path_var.set(processed_path)
            self.update_status(f"Processed image: {Path(processed_path).name}")

            messagebox.showinfo(
                "Success", f"White background removed!\nSaved to: {processed_path}"
            )

        except Exception as e:
            messagebox.showerror("Processing Error", f"Failed to process image: {e}")

    def preview_template(self):
        """Show template preview."""
        try:
            # Validate inputs
            template_name = self.template_name_var.get().strip()
            if not template_name:
                messagebox.showerror("Error", "Please enter a template name")
                return

            markers = self.validate_markers()
            if markers is None:
                return

            # Show preview window
            preview_window = TemplatePreviewWindow(
                self.root,
                self.template_maker,
                markers,
                image_path=self.image_path_var.get().strip() or None,
                image_scale=0.8,  # Default scale
                image_offset_x=0,  # Default X offset
                image_offset_y=0,  # Default Y offset
                mask_path=self.mask_path_var.get().strip() or None,
            )

            # Wait for window to close, then check if user created template
            self.root.wait_window(preview_window.window)

            # Check if preview window has updated values and save them
            if hasattr(preview_window, "final_scale"):
                self.adjusted_scale = preview_window.final_scale
            if hasattr(preview_window, "final_offset_x"):
                self.adjusted_offset_x = preview_window.final_offset_x
            if hasattr(preview_window, "final_offset_y"):
                self.adjusted_offset_y = preview_window.final_offset_y

        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to show preview: {e}")

    def update_live_preview(self):
        """Update a small live preview when settings change."""
        # This would show a small preview in the main window
        # Implementation depends on having a preview canvas in the main UI
        pass

    def validate_markers(self) -> Optional[List[int]]:
        """Validate marker IDs."""
        try:
            markers = []
            for var in self.marker_vars:
                value = var.get().strip()
                if not value:
                    messagebox.showerror("Error", "All marker ID fields must be filled")
                    return None

                marker_id = int(value)
                if marker_id < 0 or marker_id > 49:
                    messagebox.showerror(
                        "Error", f"Marker ID {marker_id} must be between 0 and 49"
                    )
                    return None

                if marker_id in markers:
                    messagebox.showerror("Error", f"Duplicate marker ID: {marker_id}")
                    return None

                markers.append(marker_id)

            return markers
        except ValueError:
            messagebox.showerror("Error", "Marker IDs must be valid integers")
            return None

    def update_status(self, message: str, show_progress: bool = False):
        """Update status message and progress bar."""
        self.status_var.set(message)
        if show_progress:
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
        self.root.update()

    def create_single_template(self):
        """Create a single template."""
        # Validate inputs
        template_name = self.template_name_var.get().strip()
        if not template_name:
            messagebox.showerror("Error", "Please enter a template name")
            return

        markers = self.validate_markers()
        if markers is None:
            return

        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            messagebox.showerror("Error", "Please select an output directory")
            return

        # Create template in background thread
        def create_template():
            try:
                self.update_status(f"Creating template '{template_name}'...", True)

                # Check if image is provided
                image_path = self.image_path_var.get().strip()
                krathong_image = None

                if image_path and os.path.exists(image_path):
                    # Load and process krathong image
                    krathong_image = cv2.imread(image_path)
                    if krathong_image is not None:
                        # Remove white background using smart method
                        krathong_image = (
                            self.template_maker.remove_white_background_aggressive(
                                krathong_image
                            )
                        )

                # Create template image using adjusted values from preview
                template_image = self.template_maker.create_template_image(
                    marker_ids=markers,
                    krathong_image=krathong_image,
                    scale=self.adjusted_scale,
                    offset_x=self.adjusted_offset_x,
                    offset_y=self.adjusted_offset_y,
                )

                # Ensure output directory exists
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                # Save template
                template_file = output_path / f"{template_name}.png"
                cv2.imwrite(str(template_file), template_image)

                # Handle mask file - rename existing mask or create new one
                mask_file = None
                if krathong_image is not None:
                    # Check if there's an existing mask from cropping
                    existing_mask_path = self.mask_path_var.get().strip()
                    if existing_mask_path and os.path.exists(existing_mask_path):
                        # Copy the existing mask to use template name
                        mask_file = output_path / f"{template_name}_mask.png"
                        shutil.copy2(existing_mask_path, mask_file)
                        # Delete the old mask file with original image name
                        os.remove(existing_mask_path)
                        print(f"Renamed mask from {existing_mask_path} to {mask_file}")
                    else:
                        # Create new mask if no existing mask
                        mask = self.template_maker.create_mask(krathong_image)
                        mask_file = output_path / f"{template_name}_mask.png"
                        cv2.imwrite(str(mask_file), mask)

                # 🎯 Save ArUco metadata for CRUD system
                metadata = {
                    "template_name": template_name,
                    "aruco_ids": markers,
                    "template_file": str(template_file),
                    "mask_file": str(mask_file) if mask_file else None,
                    "template_width": self.template_maker.template_width,
                    "template_height": self.template_maker.template_height,
                    "created_at": datetime.now().isoformat(),
                    "marker_positions": {
                        "top_left": markers[0],
                        "top_right": markers[1],
                        "bottom_left": markers[2],
                        "bottom_right": markers[3],
                    },
                    "dictionary_type": "4X4_50",
                }

                # Save metadata file
                metadata_file = output_path / f"{template_name}_metadata.json"
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                print(f"✅ Template metadata saved: {metadata_file}")
                print(f"🎯 ArUco IDs: {markers}")

                self.update_status("Template created successfully!", False)
                messagebox.showinfo(
                    "Success",
                    f"Template created successfully!\n\nFiles:\n- Template: {template_file}\n- Metadata: {metadata_file}",
                )

            except Exception as e:
                self.update_status("Error creating template", False)
                messagebox.showerror("Error", f"Failed to create template: {e}")

        thread = threading.Thread(target=create_template)
        thread.daemon = True
        thread.start()

    def create_sequential_templates(self):
        """Create sequential templates."""
        try:
            # Get number of templates to create
            num_templates = tk.simpledialog.askinteger(
                "Sequential Templates",
                "How many templates do you want to create?",
                minvalue=1,
                maxvalue=50,
                initialvalue=5,
            )

            if not num_templates:
                return

            # Get starting marker ID
            start_id = tk.simpledialog.askinteger(
                "Starting Marker ID",
                "Starting marker ID (0-46):",
                minvalue=0,
                maxvalue=46,
                initialvalue=0,
            )

            if start_id is None:
                return

            base_name = self.template_name_var.get().strip()
            if not base_name:
                messagebox.showerror("Error", "Please enter a base template name")
                return

            output_dir = self.output_dir_var.get().strip()
            if not output_dir:
                messagebox.showerror("Error", "Please select an output directory")
                return

            def create_templates():
                try:
                    self.update_status("Creating sequential templates...", True)

                    for i in range(num_templates):
                        # Calculate marker IDs for this template
                        base_marker = start_id + (i * 4)
                        if base_marker + 3 > 49:
                            messagebox.showwarning(
                                "Warning",
                                f"Stopping at template {i + 1}: would exceed marker ID 49",
                            )
                            break

                        markers = [base_marker + j for j in range(4)]
                        template_name = f"{base_name}_{i + 1:02d}"

                        self.update_status(
                            f"Creating template {i + 1}/{num_templates}: {template_name}",
                            True,
                        )

                        # Create template
                        image_path = self.image_path_var.get().strip()
                        if image_path:
                            (
                                success,
                                message,
                            ) = self.template_maker.create_template_with_registry(
                                template_name=template_name,
                                client_name="GUI_Sequential",
                                marker_ids=markers,
                                output_dir=output_dir,
                                image_path=image_path,
                                image_scale=self.adjusted_scale,
                                image_offset_x=self.adjusted_offset_x,
                                image_offset_y=self.adjusted_offset_y,
                            )
                        else:
                            (
                                success,
                                message,
                            ) = self.template_maker.create_template_with_registry(
                                template_name=template_name,
                                client_name="GUI_Sequential",
                                marker_ids=markers,
                                output_dir=output_dir,
                            )

                        if not success:
                            raise Exception(message)

                    self.update_status(
                        f"Created {num_templates} sequential templates successfully!",
                        False,
                    )
                    messagebox.showinfo(
                        "Success",
                        f"Created {num_templates} sequential templates successfully!",
                    )

                except Exception as e:
                    self.update_status("Error creating templates", False)
                    messagebox.showerror("Error", f"Failed to create templates: {e}")

            thread = threading.Thread(target=create_templates)
            thread.daemon = True
            thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create sequential templates: {e}")

    def create_from_config(self):
        """Create templates from configuration file."""
        config_file = filedialog.askopenfilename(
            title="Select Configuration File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=os.getcwd(),
        )

        if not config_file:
            return

        try:
            with open(config_file, "r") as f:
                config = json.load(f)

            templates = config.get("templates", [])
            if not templates:
                messagebox.showerror(
                    "Error", "No templates found in configuration file"
                )
                return

            def create_from_config_thread():
                try:
                    self.update_status("Creating templates from config...", True)

                    for i, template_config in enumerate(templates):
                        template_name = template_config.get("name", f"template_{i+1}")
                        markers = template_config.get(
                            "markers", [i * 4, i * 4 + 1, i * 4 + 2, i * 4 + 3]
                        )

                        self.update_status(
                            f"Creating template {i+1}/{len(templates)}: {template_name}",
                            True,
                        )

                        # Create template
                        (
                            success,
                            message,
                        ) = self.template_maker.create_template_with_registry(
                            template_name=template_name,
                            client_name="GUI_Config",
                            marker_ids=markers,
                            output_dir=self.output_dir_var.get(),
                        )

                        if not success:
                            raise Exception(message)

                    self.update_status(
                        f"Created {len(templates)} templates from config!", False
                    )
                    messagebox.showinfo(
                        "Success",
                        f"Created {len(templates)} templates from configuration!",
                    )

                except Exception as e:
                    self.update_status("Error creating templates", False)
                    messagebox.showerror("Error", f"Failed to create templates: {e}")

            thread = threading.Thread(target=create_from_config_thread)
            thread.daemon = True
            thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read configuration file: {e}")

    def create_sample_config(self):
        """Create a sample configuration file."""
        sample_config = {
            "templates": [
                {"name": "template_01", "markers": [0, 1, 2, 3]},
                {"name": "template_02", "markers": [4, 5, 6, 7]},
                {"name": "template_03", "markers": [8, 9, 10, 11]},
                {"name": "template_04", "markers": [12, 13, 14, 15]},
                {"name": "template_05", "markers": [16, 17, 18, 19]},
            ]
        }

        config_file = filedialog.asksaveasfilename(
            title="Save Sample Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfilename="template_config.json",
        )

        if config_file:
            try:
                with open(config_file, "w") as f:
                    json.dump(sample_config, f, indent=2)
                messagebox.showinfo(
                    "Success", f"Sample configuration saved to: {config_file}"
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {e}")

    def list_templates(self):
        """List existing templates."""
        templates_dir = Path(self.output_dir_var.get())

        if not templates_dir.exists():
            messagebox.showinfo("Templates", "Output directory does not exist")
            return

        template_files = list(templates_dir.glob("*.png"))

        if not template_files:
            messagebox.showinfo("Templates", "No templates found in output directory")
            return

        # Create a new window to show templates
        list_window = tk.Toplevel(self.root)
        list_window.title("Template List")
        list_window.geometry("600x400")

        # Create listbox with scrollbar
        frame = ttk.Frame(list_window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        list_window.columnconfigure(0, weight=1)
        list_window.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, text="Template Files:", style="Heading.TLabel").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 10)
        )

        # Listbox with scrollbar
        listbox_frame = ttk.Frame(frame)
        listbox_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)

        listbox = tk.Listbox(listbox_frame)
        listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(
            listbox_frame, orient=tk.VERTICAL, command=listbox.yview
        )
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        listbox.configure(yscrollcommand=scrollbar.set)

        for template_file in sorted(template_files):
            file_size = template_file.stat().st_size
            listbox.insert(tk.END, f"{template_file.name} ({file_size:,} bytes)")

        # Close button
        ttk.Button(frame, text="Close", command=list_window.destroy).grid(
            row=2, column=0, pady=(10, 0)
        )

    def open_output_folder(self):
        """Open the output folder in file explorer."""
        output_dir = Path(self.output_dir_var.get())

        if not output_dir.exists():
            messagebox.showerror("Error", "Output directory does not exist")
            return

        try:
            import platform

            if platform.system() == "Windows":
                os.startfile(output_dir)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open '{output_dir}'")
            else:  # Linux
                os.system(f"xdg-open '{output_dir}'")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")

    def show_specifications(self):
        """Show detailed template specifications."""
        specs = {
            "Template Dimensions": "1270 × 720 pixels",
            "Drawing Area": "779 × 457 pixels (centered)",
            "Drawing Area Position": "Centered on canvas",
            "ArUco Marker Size": "100 × 100 pixels",
            "ArUco Dictionary": "4X4_50 (IDs 0-49)",
            "Marker Positions": "Drawing area box corners (outside the box)",
            "Drawing Area Outline": "4px black border",
            "Supported Image Formats": "PNG, JPG, JPEG, BMP, TIFF",
            "Image Scale Range": "10% - 150%",
            "Image Offset Range": "-200px to +200px (X and Y)",
            "Output Format": "PNG with transparency",
        }

        specs_window = tk.Toplevel(self.root)
        specs_window.title("Template Specifications")
        specs_window.geometry("500x400")
        specs_window.resizable(False, False)

        # Main frame
        main_frame = ttk.Frame(specs_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(
            main_frame, text="Template Specifications", style="Title.TLabel"
        ).pack(pady=(0, 20))

        # Specifications
        for key, value in specs.items():
            spec_frame = ttk.Frame(main_frame)
            spec_frame.pack(fill=tk.X, pady=2)

            ttk.Label(spec_frame, text=f"{key}:", style="Heading.TLabel").pack(
                side=tk.LEFT
            )
            ttk.Label(spec_frame, text=value).pack(side=tk.RIGHT)

        # Close button
        ttk.Button(main_frame, text="Close", command=specs_window.destroy).pack(
            pady=(20, 0)
        )

    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


def main():
    """Main function to run the GUI application."""
    print("🎯 Starting Krathong Template Maker GUI...")

    try:
        app = TemplateMarkerGUI()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")


if __name__ == "__main__":
    main()
