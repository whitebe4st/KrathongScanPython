#!/usr/bin/env python3
"""
Krathong Processor

Advanced image processing tool for krathong images with automatic detection and cropping.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk


class KrathongProcessor:
    """Advanced krathong image processor with automatic detection."""

    def __init__(self, image_path):
        """Initialize the krathong processor."""
        self.image_path = image_path
        self.original_image = None
        self.processed_image = None
        self.processed_path = None

        # Load image
        try:
            self.original_image = cv2.imread(image_path)
            if self.original_image is None:
                raise Exception("Could not load image")

            # Start with original as processed
            self.processed_image = self.original_image.copy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            return

        self.setup_ui()

    def setup_ui(self):
        """Set up the processing interface."""
        self.root = tk.Toplevel()
        self.root.title("Krathong Processor")
        self.root.geometry("1000x700")

        # Main frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = tk.Label(
            main_frame, text="🎯 Krathong Image Processor", font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Controls frame
        controls_frame = tk.LabelFrame(
            main_frame, text="Processing Controls", font=("Arial", 12, "bold")
        )
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # Processing buttons
        btn_frame = tk.Frame(controls_frame)
        btn_frame.pack(pady=10)

        auto_btn = tk.Button(
            btn_frame, text="🤖 Auto Detect Krathong", command=self.auto_detect
        )
        auto_btn.pack(side=tk.LEFT, padx=(0, 10))

        enhance_btn = tk.Button(
            btn_frame, text="✨ Enhance Image", command=self.enhance_image
        )
        enhance_btn.pack(side=tk.LEFT, padx=(0, 10))

        reset_btn = tk.Button(btn_frame, text="🔄 Reset", command=self.reset_image)
        reset_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Image display frame
        display_frame = tk.Frame(main_frame)
        display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Original image
        orig_frame = tk.LabelFrame(
            display_frame, text="Original", font=("Arial", 10, "bold")
        )
        orig_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.orig_canvas = tk.Canvas(orig_frame, bg="white", width=400, height=300)
        self.orig_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Processed image
        proc_frame = tk.LabelFrame(
            display_frame, text="Processed", font=("Arial", 10, "bold")
        )
        proc_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.proc_canvas = tk.Canvas(proc_frame, bg="white", width=400, height=300)
        self.proc_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Action buttons
        action_frame = tk.Frame(main_frame)
        action_frame.pack(pady=10)

        save_btn = tk.Button(
            action_frame, text="💾 Save Processed Image", command=self.save_processed
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 10))

        cancel_btn = tk.Button(action_frame, text="❌ Cancel", command=self.root.destroy)
        cancel_btn.pack(side=tk.LEFT)

        # Display initial images
        self.update_display()

    def auto_detect(self):
        """Automatically detect and crop krathong from image."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)

            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (15, 15), 0)

            # Apply threshold to get binary image
            _, thresh = cv2.threshold(
                blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            # Find contours
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if contours:
                # Find the largest contour (assuming it's the krathong)
                largest_contour = max(contours, key=cv2.contourArea)

                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(largest_contour)

                # Add some padding
                padding = 20
                x = max(0, x - padding)
                y = max(0, y - padding)
                w = min(self.original_image.shape[1] - x, w + 2 * padding)
                h = min(self.original_image.shape[0] - y, h + 2 * padding)

                # Crop the image
                self.processed_image = self.original_image[y : y + h, x : x + w]

                self.update_display()
                messagebox.showinfo(
                    "Success", "Krathong detected and cropped automatically!"
                )

            else:
                messagebox.showwarning(
                    "Detection Failed",
                    "Could not detect krathong automatically. Try manual cropping.",
                )

        except Exception as e:
            messagebox.showerror("Error", f"Auto detection failed: {e}")

    def enhance_image(self):
        """Enhance the processed image quality."""
        try:
            # Apply various enhancement techniques
            enhanced = self.processed_image.copy()

            # Increase contrast and brightness
            alpha = 1.2  # Contrast control
            beta = 10  # Brightness control
            enhanced = cv2.convertScaleAbs(enhanced, alpha=alpha, beta=beta)

            # Apply slight sharpening
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            enhanced = cv2.filter2D(enhanced, -1, kernel)

            # Reduce noise
            enhanced = cv2.bilateralFilter(enhanced, 9, 75, 75)

            self.processed_image = enhanced
            self.update_display()

            messagebox.showinfo("Success", "Image enhanced successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Enhancement failed: {e}")

    def reset_image(self):
        """Reset processed image to original."""
        self.processed_image = self.original_image.copy()
        self.update_display()

    def update_display(self):
        """Update the image displays."""
        try:
            # Display original image
            self.display_image_on_canvas(self.original_image, self.orig_canvas)

            # Display processed image
            self.display_image_on_canvas(self.processed_image, self.proc_canvas)

        except Exception as e:
            print(f"Display update error: {e}")

    def display_image_on_canvas(self, image, canvas):
        """Display an image on a canvas."""
        try:
            # Get canvas size
            canvas.update()
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                # Canvas not ready yet
                return

            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Calculate scale to fit image in canvas
            img_height, img_width = rgb_image.shape[:2]
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            scale = min(scale_x, scale_y, 1.0)

            # Resize image
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)

            resized_image = cv2.resize(rgb_image, (new_width, new_height))

            # Convert to PIL Image for tkinter
            pil_image = Image.fromarray(resized_image)
            photo = ImageTk.PhotoImage(pil_image)

            # Clear canvas and display image
            canvas.delete("all")

            # Center image on canvas
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2

            canvas.create_image(x, y, anchor=tk.NW, image=photo)

            # Keep a reference to prevent garbage collection
            canvas.image = photo

        except Exception as e:
            print(f"Canvas display error: {e}")

    def save_processed(self):
        """Save the processed image."""
        try:
            # Generate output filename
            input_path = Path(self.image_path)
            output_path = (
                input_path.parent / f"{input_path.stem}_processed{input_path.suffix}"
            )

            # Save processed image
            success = cv2.imwrite(str(output_path), self.processed_image)

            if success:
                self.processed_path = str(output_path)
                messagebox.showinfo(
                    "Success", f"Processed image saved to: {output_path}"
                )
                self.root.destroy()
            else:
                messagebox.showerror("Error", "Failed to save processed image.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {e}")


def open_krathong_processor(image_path):
    """Open the krathong processor and return the path to the processed image."""
    if not Path(image_path).exists():
        messagebox.showerror("Error", f"Image file not found: {image_path}")
        return None

    processor = KrathongProcessor(image_path)

    # Wait for processor window to close
    if hasattr(processor, "root"):
        processor.root.wait_window()
        return processor.processed_path

    return None


if __name__ == "__main__":
    # Test the processor
    import sys

    if len(sys.argv) > 1:
        result = open_krathong_processor(sys.argv[1])
        if result:
            print(f"Processed image saved to: {result}")
    else:
        print("Usage: python krathong_processor.py <image_path>")
