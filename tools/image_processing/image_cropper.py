#!/usr/bin/env python3
"""
Simple Image Cropper for Krathong Template Maker

A basic image cropping tool that opens an image and allows the user to crop it.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import cv2
import numpy as np
from PIL import Image, ImageTk


class ImageCropper:
    """Simple image cropping tool."""

    def __init__(self, image_path):
        """Initialize the image cropper."""
        self.image_path = image_path
        self.original_image = None
        self.display_image = None
        self.cropped_path = None

        # Crop coordinates
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None

        # Load image
        try:
            self.original_image = cv2.imread(image_path)
            if self.original_image is None:
                raise Exception("Could not load image")

            # Convert BGR to RGB for display
            self.display_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            return

        self.setup_ui()

    def setup_ui(self):
        """Set up the cropping interface."""
        self.root = tk.Toplevel()
        self.root.title("Image Cropper")
        self.root.geometry("800x600")

        # Main frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Instructions
        instructions = tk.Label(
            main_frame,
            text="Click and drag to select crop area. Click 'Crop' to save the cropped image.",
            font=("Arial", 12),
        )
        instructions.pack(pady=(0, 10))

        # Canvas for image display
        self.canvas = tk.Canvas(main_frame, bg="white", width=760, height=500)
        self.canvas.pack(pady=(0, 10))

        # Display image
        self.display_image_on_canvas()

        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack()

        crop_btn = tk.Button(button_frame, text="Crop & Save", command=self.crop_image)
        crop_btn.pack(side=tk.LEFT, padx=(0, 10))

        cancel_btn = tk.Button(button_frame, text="Cancel", command=self.root.destroy)
        cancel_btn.pack(side=tk.LEFT)

    def display_image_on_canvas(self):
        """Display the image on the canvas."""
        # Resize image to fit canvas if necessary
        img_height, img_width = self.display_image.shape[:2]
        canvas_width = 760
        canvas_height = 500

        # Calculate scale to fit image in canvas
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        self.scale = min(scale_x, scale_y, 1.0)  # Don't upscale

        new_width = int(img_width * self.scale)
        new_height = int(img_height * self.scale)

        # Resize image
        resized_image = cv2.resize(self.display_image, (new_width, new_height))

        # Convert to PIL Image for tkinter
        pil_image = Image.fromarray(resized_image)
        self.photo = ImageTk.PhotoImage(pil_image)

        # Center image on canvas
        self.image_x = (canvas_width - new_width) // 2
        self.image_y = (canvas_height - new_height) // 2

        self.canvas.create_image(
            self.image_x, self.image_y, anchor=tk.NW, image=self.photo
        )

        # Store image dimensions for coordinate conversion
        self.display_width = new_width
        self.display_height = new_height

    def on_click(self, event):
        """Handle mouse click."""
        self.start_x = event.x
        self.start_y = event.y

        # Remove previous rectangle
        self.canvas.delete("crop_rect")

    def on_drag(self, event):
        """Handle mouse drag."""
        if self.start_x is not None and self.start_y is not None:
            # Remove previous rectangle
            self.canvas.delete("crop_rect")

            # Draw new rectangle
            self.canvas.create_rectangle(
                self.start_x,
                self.start_y,
                event.x,
                event.y,
                outline="red",
                width=2,
                tags="crop_rect",
            )

    def on_release(self, event):
        """Handle mouse release."""
        self.end_x = event.x
        self.end_y = event.y

    def crop_image(self):
        """Crop the image based on selection."""
        if self.start_x is None or self.end_x is None:
            messagebox.showwarning("No Selection", "Please select an area to crop.")
            return

        try:
            # Convert canvas coordinates to image coordinates
            # Adjust for image position on canvas
            img_start_x = max(0, self.start_x - self.image_x)
            img_start_y = max(0, self.start_y - self.image_y)
            img_end_x = min(self.display_width, self.end_x - self.image_x)
            img_end_y = min(self.display_height, self.end_y - self.image_y)

            # Scale coordinates back to original image size
            orig_start_x = int(img_start_x / self.scale)
            orig_start_y = int(img_start_y / self.scale)
            orig_end_x = int(img_end_x / self.scale)
            orig_end_y = int(img_end_y / self.scale)

            # Ensure coordinates are in correct order
            x1, x2 = min(orig_start_x, orig_end_x), max(orig_start_x, orig_end_x)
            y1, y2 = min(orig_start_y, orig_end_y), max(orig_start_y, orig_end_y)

            # Crop the original image
            cropped = self.original_image[y1:y2, x1:x2]

            if cropped.size == 0:
                messagebox.showerror("Error", "Invalid crop selection.")
                return

            # Generate output filename
            input_path = Path(self.image_path)
            output_path = (
                input_path.parent / f"{input_path.stem}_cropped{input_path.suffix}"
            )

            # Save cropped image
            success = cv2.imwrite(str(output_path), cropped)

            if success:
                self.cropped_path = str(output_path)
                messagebox.showinfo("Success", f"Cropped image saved to: {output_path}")
                self.root.destroy()
            else:
                messagebox.showerror("Error", "Failed to save cropped image.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to crop image: {e}")


def open_image_cropper(image_path):
    """Open the image cropper and return the path to the cropped image."""
    if not Path(image_path).exists():
        messagebox.showerror("Error", f"Image file not found: {image_path}")
        return None

    cropper = ImageCropper(image_path)

    # Wait for cropper window to close
    if hasattr(cropper, "root"):
        cropper.root.wait_window()
        return cropper.cropped_path

    return None


if __name__ == "__main__":
    # Test the cropper
    import sys

    if len(sys.argv) > 1:
        result = open_image_cropper(sys.argv[1])
        if result:
            print(f"Cropped image saved to: {result}")
    else:
        print("Usage: python image_cropper.py <image_path>")
