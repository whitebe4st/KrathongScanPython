"""
Cropping System Module

Handles interactive cropping functionality for template creation.
Extracted and modularized from template_maker_gui.py ImageCropper class.

Key Features:
- Interactive click-and-drag cropping selection
- Visual feedback with selection rectangle
- Coordinate system management (canvas <-> image)
- Manual coordinate adjustment
- Multiple selection modes (rectangle, auto-detect, quick crop)
- Selection validation and boundary checking

Author: KrathongScanner Team
"""

import logging
import tkinter as tk
from typing import Any, Callable, Dict, Optional, Tuple

import cv2
import numpy as np


class CroppingSystem:
    """
    Interactive cropping system for template creation.

    Manages crop selection with visual feedback, coordinate conversion,
    and multiple selection modes.
    """

    def __init__(self):
        """Initialize the cropping system."""
        self.logger = logging.getLogger(__name__)

        # Canvas reference (set externally)
        self.canvas: Optional[tk.Canvas] = None

        # Current image being cropped
        self.current_image: Optional[np.ndarray] = None

        # Image properties (set externally)
        self.image_width: int = 0
        self.image_height: int = 0
        self.scale_factor: float = 1.0

        # Selection state
        self._is_selecting: bool = False
        self.start_x: float = 0
        self.start_y: float = 0
        self.end_x: float = 0
        self.end_y: float = 0
        self.rect_id: Optional[int] = None

        # Crop coordinates (in image space)
        self.crop_x1: int = 0
        self.crop_y1: int = 0
        self.crop_x2: int = 0
        self.crop_y2: int = 0

        # Visual styling
        self.selection_style = {
            "outline": "blue",
            "width": 3,
            "fill": "",
            "dash": (10, 5),
            "tags": "crop_rect",
        }

        # Callbacks for coordinate updates
        self.on_coords_changed: Optional[Callable] = None
        self.on_selection_changed: Optional[Callable] = None

        self.logger.info("CroppingSystem initialized")

    def set_canvas(self, canvas: tk.Canvas):
        """Set the canvas for cropping operations."""
        self.canvas = canvas
        self.setup_canvas_bindings()
        self.logger.debug("Canvas set for cropping system")

    def set_image(self, image: np.ndarray):
        """
        Set the image for cropping operations.

        Args:
            image: Input image as numpy array
        """
        if image is None:
            self.logger.warning("Received None image")
            return

        # Store image reference
        self.current_image = image.copy()

        # Get image properties
        height, width = image.shape[:2]
        self.image_width = width
        self.image_height = height

        # Reset crop selection
        self.clear_selection()

        self.logger.info(f"Image set for cropping: {width}x{height}")

    def set_image_properties(self, width: int, height: int, scale_factor: float):
        """
        Set image properties for coordinate conversion.

        Args:
            width: Image width in pixels
            height: Image height in pixels
            scale_factor: Display scale factor
        """
        self.image_width = width
        self.image_height = height
        self.scale_factor = scale_factor

        # Reset crop coordinates to full image
        self.crop_x1 = 0
        self.crop_y1 = 0
        self.crop_x2 = width
        self.crop_y2 = height

        self.logger.debug(
            f"Image properties set: {width}x{height}, scale: {scale_factor:.3f}"
        )

    def setup_canvas_bindings(self):
        """Setup mouse event bindings for the canvas."""
        if self.canvas is None:
            return

        self.canvas.bind("<Button-1>", self.start_crop_selection)
        self.canvas.bind("<B1-Motion>", self.update_crop_selection)
        self.canvas.bind("<ButtonRelease-1>", self.end_crop_selection)
        self.canvas.bind("<Double-Button-1>", self.clear_selection)

        self.logger.debug("Canvas bindings setup for cropping")

    def start_crop_selection(self, event):
        """
        Start interactive crop selection.

        Args:
            event: Tkinter mouse event
        """
        if self.image_width == 0 or self.image_height == 0:
            return

        self._is_selecting = True
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.end_x = self.start_x
        self.end_y = self.start_y

        # Clear previous selection
        self.clear_selection_visual()

        self.logger.debug(
            f"Started crop selection at canvas coords ({self.start_x:.1f}, {self.start_y:.1f})"
        )

    def update_crop_selection(self, event):
        """
        Update crop selection during drag.

        Args:
            event: Tkinter mouse event
        """
        if not self._is_selecting or self.canvas is None:
            return

        self.end_x = self.canvas.canvasx(event.x)
        self.end_y = self.canvas.canvasy(event.y)

        # Update visual selection rectangle
        self.update_selection_visual()

        # Notify of selection change
        if self.on_selection_changed:
            try:
                self.on_selection_changed()
            except Exception as e:
                self.logger.error(f"Error in selection changed callback: {e}")

    def end_crop_selection(self, event):
        """
        End crop selection and finalize coordinates.

        Args:
            event: Tkinter mouse event
        """
        if not self._is_selecting:
            return

        self._is_selecting = False

        # Final update of selection
        self.end_x = self.canvas.canvasx(event.x)
        self.end_y = self.canvas.canvasy(event.y)

        # Validate minimum selection size (5 pixels)
        if abs(self.end_x - self.start_x) < 5 or abs(self.end_y - self.start_y) < 5:
            self.clear_selection()
            self.logger.debug("Selection too small, cleared")
            return

        # Update visual selection
        self.update_selection_visual()

        # Convert canvas coordinates to image coordinates
        self.update_image_coordinates()

        # Notify of coordinate change
        if self.on_coords_changed:
            try:
                self.on_coords_changed(
                    self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2
                )
            except Exception as e:
                self.logger.error(f"Error in coords changed callback: {e}")

        self.logger.debug(
            f"Crop selection finalized: ({self.crop_x1}, {self.crop_y1}) to ({self.crop_x2}, {self.crop_y2})"
        )

    def update_selection_visual(self):
        """Update the visual selection rectangle on canvas."""
        if self.canvas is None:
            return

        # Remove existing rectangle
        if self.rect_id:
            self.canvas.delete(self.rect_id)

        # Create new rectangle
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.end_x, self.end_y, **self.selection_style
        )

        # Bring rectangle to front
        self.canvas.tag_raise("crop_rect")

        # Force canvas update for smooth visual feedback
        self.canvas.update_idletasks()

    def clear_selection_visual(self):
        """Clear the visual selection rectangle."""
        if self.canvas and self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None

    def clear_selection(self, event=None):
        """
        Clear the current selection.

        Args:
            event: Optional tkinter event (for double-click binding)
        """
        self.clear_selection_visual()
        self._is_selecting = False

        # Reset to full image
        self.crop_x1 = 0
        self.crop_y1 = 0
        self.crop_x2 = self.image_width
        self.crop_y2 = self.image_height

        # Notify of coordinate change
        if self.on_coords_changed:
            try:
                self.on_coords_changed(
                    self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2
                )
            except Exception as e:
                self.logger.error(f"Error in coords changed callback: {e}")

        self.logger.debug("Selection cleared")

    def update_image_coordinates(self):
        """Update image coordinates from canvas selection."""
        # Convert canvas coordinates to image coordinates
        left = min(self.start_x, self.end_x) / self.scale_factor
        top = min(self.start_y, self.end_y) / self.scale_factor
        right = max(self.start_x, self.end_x) / self.scale_factor
        bottom = max(self.start_y, self.end_y) / self.scale_factor

        # Clamp to image bounds
        left = max(0, min(left, self.image_width))
        top = max(0, min(top, self.image_height))
        right = max(left, min(right, self.image_width))
        bottom = max(top, min(bottom, self.image_height))

        # Update crop coordinates
        self.crop_x1 = int(left)
        self.crop_y1 = int(top)
        self.crop_x2 = int(right)
        self.crop_y2 = int(bottom)

    def set_crop_coordinates(
        self, x1: int, y1: int, x2: int, y2: int, update_visual: bool = True
    ):
        """
        Set crop coordinates programmatically.

        Args:
            x1, y1: Top-left corner in image coordinates
            x2, y2: Bottom-right corner in image coordinates
            update_visual: Whether to update visual selection
        """
        # Validate and clamp coordinates
        x1 = max(0, min(x1, self.image_width))
        y1 = max(0, min(y1, self.image_height))
        x2 = max(x1, min(x2, self.image_width))
        y2 = max(y1, min(y2, self.image_height))

        self.crop_x1 = x1
        self.crop_y1 = y1
        self.crop_x2 = x2
        self.crop_y2 = y2

        if update_visual:
            self.update_visual_from_coordinates()

        self.logger.debug(f"Crop coordinates set: ({x1}, {y1}) to ({x2}, {y2})")

    def update_visual_from_coordinates(self):
        """Update visual selection from current coordinates."""
        if self.canvas is None:
            return

        # Convert image coordinates to canvas coordinates
        self.start_x = self.crop_x1 * self.scale_factor
        self.start_y = self.crop_y1 * self.scale_factor
        self.end_x = self.crop_x2 * self.scale_factor
        self.end_y = self.crop_y2 * self.scale_factor

        # Update visual
        self.update_selection_visual()

    # Interface methods for main application compatibility
    def is_selecting(self) -> bool:
        """
        Check if currently in selection mode.

        Returns:
            True if currently selecting
        """
        return self._is_selecting

    def start_selection(self, img_x: float, img_y: float):
        """
        Start selection at image coordinates.

        Args:
            img_x: X coordinate in image space
            img_y: Y coordinate in image space
        """
        if self.canvas is None:
            return

        self._is_selecting = True

        # Convert image coordinates to canvas coordinates
        self.start_x = img_x * self.scale_factor
        self.start_y = img_y * self.scale_factor
        self.end_x = self.start_x
        self.end_y = self.start_y

        # Clear previous selection
        self.clear_selection_visual()

        self.logger.debug(
            f"Started selection at image coords ({img_x:.1f}, {img_y:.1f})"
        )

    def update_selection(self, img_x: float, img_y: float):
        """
        Update selection to new image coordinates.

        Args:
            img_x: X coordinate in image space
            img_y: Y coordinate in image space
        """
        if not self._is_selecting or self.canvas is None:
            return

        # Convert image coordinates to canvas coordinates
        self.end_x = img_x * self.scale_factor
        self.end_y = img_y * self.scale_factor

        # Update visual selection rectangle
        self.update_selection_visual()

        # Notify of selection change
        if self.on_selection_changed:
            try:
                self.on_selection_changed()
            except Exception as e:
                self.logger.error(f"Error in selection changed callback: {e}")

    def end_selection(
        self, img_x: float, img_y: float
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        End selection and return final coordinates.

        Args:
            img_x: X coordinate in image space
            img_y: Y coordinate in image space

        Returns:
            Tuple of (x1, y1, x2, y2) coordinates or None if invalid
        """
        if not self._is_selecting:
            return None

        self._is_selecting = False

        # Convert image coordinates to canvas coordinates
        self.end_x = img_x * self.scale_factor
        self.end_y = img_y * self.scale_factor

        # Calculate selection area in image coordinates
        img_x1 = min(self.start_x, self.end_x) / self.scale_factor
        img_y1 = min(self.start_y, self.end_y) / self.scale_factor
        img_x2 = max(self.start_x, self.end_x) / self.scale_factor
        img_y2 = max(self.start_y, self.end_y) / self.scale_factor

        # Validate minimum selection size (5 pixels in image space)
        if abs(img_x2 - img_x1) < 5 or abs(img_y2 - img_y1) < 5:
            self.clear_selection()
            self.logger.debug("Selection too small, cleared")
            return None

        # Clamp to image bounds
        img_x1 = max(0, min(img_x1, self.image_width))
        img_y1 = max(0, min(img_y1, self.image_height))
        img_x2 = max(img_x1, min(img_x2, self.image_width))
        img_y2 = max(img_y1, min(img_y2, self.image_height))

        # Update crop coordinates
        self.crop_x1 = int(img_x1)
        self.crop_y1 = int(img_y1)
        self.crop_x2 = int(img_x2)
        self.crop_y2 = int(img_y2)

        # Update visual selection
        self.update_selection_visual()

        # Notify of coordinate change
        if self.on_coords_changed:
            try:
                self.on_coords_changed(
                    self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2
                )
            except Exception as e:
                self.logger.error(f"Error in coords changed callback: {e}")

        self.logger.debug(
            f"Selection finalized: ({self.crop_x1}, {self.crop_y1}) to ({self.crop_x2}, {self.crop_y2})"
        )
        return (self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2)

    def get_selection(self) -> Tuple[int, int, int, int]:
        """
        Get current selection coordinates.

        Returns:
            Tuple of (x1, y1, x2, y2) coordinates
        """
        return (self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2)

    def set_selection(self, x1: int, y1: int, x2: int, y2: int):
        """
        Set selection coordinates and update visual.

        Args:
            x1, y1: Top-left corner in image coordinates
            x2, y2: Bottom-right corner in image coordinates
        """
        self.set_crop_coordinates(x1, y1, x2, y2, update_visual=True)

    def auto_detect_bounds(self) -> bool:
        """
        Auto-detect bounds using the current image.

        Returns:
            True if bounds detected successfully
        """
        if self.current_image is None:
            self.logger.warning("No image available for auto-detection")
            return False

        return self.auto_detect_crop(self.current_image, method="contour")

    def crop_image(self) -> Optional[np.ndarray]:
        """
        Crop the current image using current selection coordinates.

        Returns:
            Cropped image or None if no image/selection
        """
        if self.current_image is None:
            self.logger.warning("No image available for cropping")
            return None

        if self.crop_x1 == self.crop_x2 or self.crop_y1 == self.crop_y2:
            self.logger.warning("Invalid crop coordinates")
            return None

        try:
            # Ensure coordinates are valid
            x1 = max(0, min(self.crop_x1, self.image_width))
            y1 = max(0, min(self.crop_y1, self.image_height))
            x2 = max(x1, min(self.crop_x2, self.image_width))
            y2 = max(y1, min(self.crop_y2, self.image_height))

            # Crop the image
            cropped = self.current_image[y1:y2, x1:x2]

            self.logger.info(
                f"Image cropped: ({x1}, {y1}) to ({x2}, {y2}), size: {cropped.shape}"
            )
            return cropped

        except Exception as e:
            self.logger.error(f"Error cropping image: {e}")
            return None

    def get_preview(self) -> Optional[np.ndarray]:
        """
        Get a preview of the cropped area.

        Returns:
            Preview image or None if no image/selection
        """
        return self.crop_image()  # For now, preview is the same as crop

    def quick_crop(self, margin_percent: float = 0.1):
        """
        Perform quick crop by removing margins from all sides.

        Args:
            margin_percent: Percentage margin to remove (0.1 = 10%)
        """
        margin_x = int(self.image_width * margin_percent)
        margin_y = int(self.image_height * margin_percent)

        x1 = margin_x
        y1 = margin_y
        x2 = self.image_width - margin_x
        y2 = self.image_height - margin_y

        self.set_crop_coordinates(x1, y1, x2, y2)

        # Notify of coordinate change
        if self.on_coords_changed:
            try:
                self.on_coords_changed(
                    self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2
                )
            except Exception as e:
                self.logger.error(f"Error in coords changed callback: {e}")

        self.logger.debug(f"Quick crop applied with {margin_percent*100}% margin")

    def auto_detect_crop(self, image: np.ndarray, method: str = "contour") -> bool:
        """
        Auto-detect crop area based on image content.

        Args:
            image: Input image for analysis
            method: Detection method ("contour", "edge", "threshold")

        Returns:
            True if crop area detected successfully
        """
        try:
            if method == "contour":
                return self._auto_detect_contour(image)
            elif method == "edge":
                return self._auto_detect_edge(image)
            elif method == "threshold":
                return self._auto_detect_threshold(image)
            else:
                self.logger.warning(f"Unknown auto-detect method: {method}")
                return False

        except Exception as e:
            self.logger.error(f"Auto-detect failed: {e}")
            return False

    def _auto_detect_contour(self, image: np.ndarray) -> bool:
        """Auto-detect using contour analysis."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply threshold to get binary image
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return False

        # Find largest contour
        largest_contour = max(contours, key=cv2.contourArea)

        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(largest_contour)

        # Set crop coordinates with some padding
        padding = 10
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(self.image_width, x + w + padding)
        y2 = min(self.image_height, y + h + padding)

        self.set_crop_coordinates(x1, y1, x2, y2)

        # Notify of coordinate change
        if self.on_coords_changed:
            self.on_coords_changed(
                self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2
            )

        self.logger.debug(
            f"Auto-detect (contour) found crop area: ({x1}, {y1}) to ({x2}, {y2})"
        )
        return True

    def _auto_detect_edge(self, image: np.ndarray) -> bool:
        """Auto-detect using edge detection."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Find non-zero pixels
        coords = np.column_stack(np.where(edges > 0))

        if len(coords) == 0:
            return False

        # Get bounding box of edge pixels
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)

        # Set crop coordinates with padding
        padding = 20
        x1 = max(0, x_min - padding)
        y1 = max(0, y_min - padding)
        x2 = min(self.image_width, x_max + padding)
        y2 = min(self.image_height, y_max + padding)

        self.set_crop_coordinates(x1, y1, x2, y2)

        # Notify of coordinate change
        if self.on_coords_changed:
            self.on_coords_changed(
                self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2
            )

        self.logger.debug(
            f"Auto-detect (edge) found crop area: ({x1}, {y1}) to ({x2}, {y2})"
        )
        return True

    def _auto_detect_threshold(self, image: np.ndarray) -> bool:
        """Auto-detect using threshold analysis."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply adaptive threshold
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Find non-zero pixels
        coords = np.column_stack(np.where(binary == 0))  # Dark pixels

        if len(coords) == 0:
            return False

        # Get bounding box
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)

        # Set crop coordinates with padding
        padding = 15
        x1 = max(0, x_min - padding)
        y1 = max(0, y_min - padding)
        x2 = min(self.image_width, x_max + padding)
        y2 = min(self.image_height, y_max + padding)

        self.set_crop_coordinates(x1, y1, x2, y2)

        # Notify of coordinate change
        if self.on_coords_changed:
            self.on_coords_changed(
                self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2
            )

        self.logger.debug(
            f"Auto-detect (threshold) found crop area: ({x1}, {y1}) to ({x2}, {y2})"
        )
        return True

    def get_crop_coordinates(self) -> Tuple[int, int, int, int]:
        """
        Get current crop coordinates.

        Returns:
            Tuple of (x1, y1, x2, y2) in image coordinates
        """
        return self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2

    def get_crop_dimensions(self) -> Tuple[int, int]:
        """
        Get crop dimensions.

        Returns:
            Tuple of (width, height)
        """
        width = self.crop_x2 - self.crop_x1
        height = self.crop_y2 - self.crop_y1
        return width, height

    def is_valid_crop(self) -> bool:
        """
        Check if current crop selection is valid.

        Returns:
            True if crop is valid (has area > 0)
        """
        width, height = self.get_crop_dimensions()
        return width > 0 and height > 0

    def crop_image_with_input(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Apply current crop to an input image.

        Args:
            image: Input image to crop

        Returns:
            Cropped image or None if crop is invalid
        """
        if not self.is_valid_crop():
            return None

        try:
            cropped = image[self.crop_y1 : self.crop_y2, self.crop_x1 : self.crop_x2]
            return cropped.copy()
        except Exception as e:
            self.logger.error(f"Failed to crop image: {e}")
            return None

    def get_crop_info(self) -> Dict[str, Any]:
        """
        Get information about current crop selection.

        Returns:
            Dictionary with crop information
        """
        width, height = self.get_crop_dimensions()
        area = width * height

        return {
            "x1": self.crop_x1,
            "y1": self.crop_y1,
            "x2": self.crop_x2,
            "y2": self.crop_y2,
            "width": width,
            "height": height,
            "area": area,
            "is_valid": self.is_valid_crop(),
            "aspect_ratio": width / height if height > 0 else 0,
        }


if __name__ == "__main__":
    # Test the cropping system
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Cropping System Test")
    root.geometry("800x600")

    # Create canvas
    canvas = tk.Canvas(root, bg="lightgray", width=600, height=400)
    canvas.pack(padx=10, pady=10)

    # Create cropping system
    cropper = CroppingSystem()
    cropper.set_canvas(canvas)
    cropper.set_image_properties(600, 400, 1.0)  # Mock image properties

    # Callback for coordinate updates
    def on_coords_changed(x1, y1, x2, y2):
        print(f"Crop coordinates: ({x1}, {y1}) to ({x2}, {y2})")

    cropper.on_coords_changed = on_coords_changed

    # Test buttons
    button_frame = ttk.Frame(root)
    button_frame.pack(pady=5)

    ttk.Button(
        button_frame, text="Quick Crop", command=lambda: cropper.quick_crop(0.1)
    ).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="Clear", command=cropper.clear_selection).pack(
        side=tk.LEFT, padx=5
    )

    root.mainloop()
