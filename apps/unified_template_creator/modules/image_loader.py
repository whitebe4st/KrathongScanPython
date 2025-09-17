"""
Image Loader Module

Handles loading, displaying, and managing krathong images for template creation.
Extracted and modularized from template_maker_gui.py ImageCropper class.

Key Features:
- Load images from file system with format validation
- Scale and resize images for display
- Canvas integration with scrollbars
- Image coordinate system management
- Display optimization and memory management

Author: KrathongScanner Team
"""

import logging
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageTk


class ImageLoader:
    """
    Handles loading and displaying krathong images for template creation.

    Manages image loading, format validation, scaling, and canvas display
    with proper coordinate system management.
    """

    def __init__(self):
        """Initialize the image loader."""
        self.logger = logging.getLogger(__name__)

        # Image state
        self.original_image: Optional[np.ndarray] = None
        self.display_image: Optional[np.ndarray] = None
        self.photo_image: Optional[ImageTk.PhotoImage] = None
        self.current_image_path: Optional[str] = None

        # Display properties
        self.scale_factor: float = 1.0
        self.display_width: int = 0
        self.display_height: int = 0
        self.canvas_image_id: Optional[int] = None

        # Canvas reference (set externally)
        self.canvas: Optional[tk.Canvas] = None

        # Supported image formats
        self.supported_formats = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"]

        self.logger.info("ImageLoader initialized")

    def set_canvas(self, canvas: tk.Canvas):
        """Set the canvas for image display."""
        self.canvas = canvas
        self.logger.debug("Canvas set for image display")

    def load_image(self, file_path: str) -> bool:
        """
        Load an image from a file path.

        Args:
            file_path: Path to the image file

        Returns:
            True if image loaded successfully, False otherwise
        """
        try:
            if not file_path or not os.path.exists(file_path):
                self.logger.error(f"File path does not exist: {file_path}")
                return False

            # Validate format
            if not self.validate_format(file_path):
                self.logger.error(f"Unsupported image format: {file_path}")
                return False

            # Load image using OpenCV
            image = cv2.imread(file_path)
            if image is None:
                self.logger.error(f"Failed to load image with OpenCV: {file_path}")
                return False

            # Store the image and path
            self.original_image = image.copy()
            self.current_image_path = file_path

            # Update display
            self._update_display_image()

            self.logger.info(f"Image loaded successfully: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error loading image {file_path}: {e}")
            return False

    def load_image_from_file(self, initial_dir: str = None) -> bool:
        """
        Load an image from file using file dialog.

        Args:
            initial_dir: Initial directory for file dialog

        Returns:
            True if image loaded successfully, False otherwise
        """
        try:
            # Prepare file dialog
            filetypes = [
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*"),
            ]

            file_path = filedialog.askopenfilename(
                title="Select Krathong Image",
                filetypes=filetypes,
                initialdir=initial_dir,
            )

            if not file_path:
                return False

            return self.load_image_from_path(file_path)

        except Exception as e:
            self.logger.error(f"Error in file dialog: {e}")
            messagebox.showerror("File Dialog Error", f"Error opening file dialog: {e}")
            return False

    def load_image_from_path(self, image_path: str) -> bool:
        """
        Load an image from specified path.

        Args:
            image_path: Path to the image file

        Returns:
            True if image loaded successfully, False otherwise
        """
        try:
            # Validate file existence
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")

            # Validate file format
            file_ext = Path(image_path).suffix.lower()
            if file_ext not in self.supported_formats:
                raise ValueError(f"Unsupported image format: {file_ext}")

            # Load image with OpenCV
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image file: {image_path}")

            # Store image data
            self.original_image = image.copy()
            self.current_image_path = image_path

            # Log image information
            height, width, channels = image.shape
            file_size = Path(image_path).stat().st_size / (1024 * 1024)  # MB

            self.logger.info(f"Image loaded successfully:")
            self.logger.info(f"  Path: {image_path}")
            self.logger.info(f"  Dimensions: {width}x{height}")
            self.logger.info(f"  Channels: {channels}")
            self.logger.info(f"  File size: {file_size:.2f} MB")

            return True

        except Exception as e:
            self.logger.error(f"Failed to load image from {image_path}: {e}")
            messagebox.showerror("Image Load Error", f"Failed to load image: {e}")
            return False

    def get_image(self) -> Optional[np.ndarray]:
        """
        Get the currently loaded original image.

        Returns:
            Original image as numpy array, or None if no image loaded
        """
        return self.original_image.copy() if self.original_image is not None else None

    def get_display_image(self) -> Optional[np.ndarray]:
        """
        Get the display-ready image.

        Returns:
            Display image as numpy array, or None if no image prepared
        """
        return self.display_image.copy() if self.display_image is not None else None

    def get_image_path(self) -> Optional[str]:
        """
        Get the path of the currently loaded image.

        Returns:
            Image file path, or None if no image loaded
        """
        return self.current_image_path

    def validate_format(self, file_path: str) -> bool:
        """
        Validate if the file format is supported.

        Args:
            file_path: Path to the image file

        Returns:
            True if format is supported, False otherwise
        """
        if not file_path:
            return False

        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.supported_formats

    def _update_display_image(self):
        """Update the display image after loading."""
        if self.original_image is not None:
            # Prepare display image with default canvas size
            self.prepare_display_image()

            # Update canvas if available
            if self.canvas is not None:
                self.update_canvas_display()

    def prepare_display_image(
        self, max_width: int = 800, max_height: int = 600
    ) -> bool:
        """
        Prepare image for display by scaling to fit canvas.

        Args:
            max_width: Maximum display width
            max_height: Maximum display height

        Returns:
            True if image prepared successfully, False otherwise
        """
        try:
            if self.original_image is None:
                raise ValueError("No image loaded")

            # Get original dimensions
            original_height, original_width = self.original_image.shape[:2]

            # Calculate scale factor to fit within max dimensions
            scale_x = max_width / original_width
            scale_y = max_height / original_height
            self.scale_factor = min(scale_x, scale_y, 1.0)  # Don't scale up

            # Calculate display dimensions
            self.display_width = int(original_width * self.scale_factor)
            self.display_height = int(original_height * self.scale_factor)

            # Resize image for display
            if self.scale_factor < 1.0:
                self.display_image = cv2.resize(
                    self.original_image,
                    (self.display_width, self.display_height),
                    interpolation=cv2.INTER_AREA,
                )
            else:
                self.display_image = self.original_image.copy()

            # Convert BGR to RGB for PIL
            display_rgb = cv2.cvtColor(self.display_image, cv2.COLOR_BGR2RGB)

            # Convert to PIL Image and then to PhotoImage
            pil_image = Image.fromarray(display_rgb)
            self.photo_image = ImageTk.PhotoImage(pil_image)

            self.logger.debug(
                f"Display image prepared: {self.display_width}x{self.display_height} (scale: {self.scale_factor:.3f})"
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to prepare display image: {e}")
            return False

    def display_on_canvas(self) -> bool:
        """
        Display the prepared image on the canvas.

        Returns:
            True if image displayed successfully, False otherwise
        """
        try:
            if self.canvas is None:
                raise ValueError("Canvas not set")

            if self.photo_image is None:
                raise ValueError("No display image prepared")

            # Clear existing image
            if self.canvas_image_id is not None:
                self.canvas.delete(self.canvas_image_id)

            # Display image at top-left of canvas
            self.canvas_image_id = self.canvas.create_image(
                0, 0, anchor=tk.NW, image=self.photo_image
            )

            # Update canvas scroll region to match image size
            self.canvas.configure(
                scrollregion=(0, 0, self.display_width, self.display_height)
            )

            self.logger.debug("Image displayed on canvas successfully")

            return True

        except Exception as e:
            self.logger.error(f"Failed to display image on canvas: {e}")
            return False

    def convert_canvas_to_image_coords(
        self, canvas_x: float, canvas_y: float
    ) -> Tuple[int, int]:
        """
        Convert canvas coordinates to original image coordinates.

        Args:
            canvas_x: X coordinate on canvas
            canvas_y: Y coordinate on canvas

        Returns:
            Tuple of (image_x, image_y) in original image coordinates
        """
        if self.original_image is None or self.scale_factor == 0:
            return int(canvas_x), int(canvas_y)

        # Convert to original image coordinates
        image_x = int(canvas_x / self.scale_factor)
        image_y = int(canvas_y / self.scale_factor)

        # Clamp to image bounds
        height, width = self.original_image.shape[:2]
        image_x = max(0, min(image_x, width - 1))
        image_y = max(0, min(image_y, height - 1))

        return image_x, image_y

    def convert_image_to_canvas_coords(
        self, image_x: int, image_y: int
    ) -> Tuple[float, float]:
        """
        Convert original image coordinates to canvas coordinates.

        Args:
            image_x: X coordinate in original image
            image_y: Y coordinate in original image

        Returns:
            Tuple of (canvas_x, canvas_y) in canvas coordinates
        """
        canvas_x = image_x * self.scale_factor
        canvas_y = image_y * self.scale_factor

        return canvas_x, canvas_y

    def get_image_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded image.

        Returns:
            Dictionary with image information
        """
        if self.original_image is None:
            return {}

        height, width, channels = self.original_image.shape
        file_size = 0

        if self.current_image_path:
            try:
                file_size = Path(self.current_image_path).stat().st_size / (
                    1024 * 1024
                )  # MB
            except:
                pass

        return {
            "path": self.current_image_path,
            "filename": Path(self.current_image_path).name
            if self.current_image_path
            else "Unknown",
            "width": width,
            "height": height,
            "channels": channels,
            "file_size_mb": file_size,
            "scale_factor": self.scale_factor,
            "display_width": self.display_width,
            "display_height": self.display_height,
        }

    def clear_image(self):
        """Clear the loaded image and reset state."""
        # Clear canvas
        if self.canvas and self.canvas_image_id:
            self.canvas.delete(self.canvas_image_id)
            self.canvas_image_id = None

        # Clear image data
        self.original_image = None
        self.display_image = None
        self.photo_image = None
        self.current_image_path = None

        # Reset properties
        self.scale_factor = 1.0
        self.display_width = 0
        self.display_height = 0

        self.logger.debug("Image cleared and state reset")

    def has_image(self) -> bool:
        """Check if an image is currently loaded."""
        return self.original_image is not None

    def get_original_image(self) -> Optional[np.ndarray]:
        """Get the original image data."""
        return self.original_image.copy() if self.original_image is not None else None

    def get_display_image(self) -> Optional[np.ndarray]:
        """Get the display image data."""
        return self.display_image.copy() if self.display_image is not None else None

    def refresh_display(self) -> bool:
        """Refresh the image display on canvas."""
        if not self.has_image():
            return False

        # Prepare and display image
        if self.prepare_display_image():
            return self.display_on_canvas()

        return False


# Convenience functions for standalone usage
def load_and_display_image(
    canvas: tk.Canvas, initial_dir: str = None
) -> Optional[ImageLoader]:
    """
    Convenience function to load and display an image on a canvas.

    Args:
        canvas: Tkinter canvas for display
        initial_dir: Initial directory for file dialog

    Returns:
        ImageLoader instance if successful, None otherwise
    """
    loader = ImageLoader()
    loader.set_canvas(canvas)

    if loader.load_image_from_file(initial_dir):
        if loader.prepare_display_image():
            if loader.display_on_canvas():
                return loader

    return None


if __name__ == "__main__":
    # Test the image loader
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Image Loader Test")
    root.geometry("800x600")

    # Create canvas
    canvas = tk.Canvas(root, bg="white")
    canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Load button
    def test_load():
        loader = load_and_display_image(canvas)
        if loader:
            info = loader.get_image_info()
            print("Image loaded:", info)

    ttk.Button(root, text="Load Image", command=test_load).pack(pady=5)

    root.mainloop()
