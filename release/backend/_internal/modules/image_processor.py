"""
Image Processing Module

Handles background removal, mask generation, and image enhancement for template creation.
Extracted and modularized from core/template_maker.py and template_maker_gui.py.

Key Features:
- Multiple background removal algorithms
- Mask generation from cropped images
- Image enhancement and filtering
- Color space conversions and analysis
- Morphological operations for cleanup

Author: KrathongScanner Team
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


class BackgroundRemovalMethod(Enum):
    """Background removal methods."""

    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    SMART = "smart"
    HSV_BASED = "hsv_based"
    LAB_BASED = "lab_based"
    THRESHOLD = "threshold"


class MaskGenerationMethod(Enum):
    """Mask generation methods."""

    CONTOUR = "contour"
    THRESHOLD = "threshold"
    EDGE_DETECTION = "edge_detection"
    COLOR_SEGMENTATION = "color_segmentation"


class ImageProcessor:
    """
    Advanced image processing for template creation.

    Handles background removal, mask generation, and image enhancement
    with multiple algorithms and methods.
    """

    def __init__(self):
        """Initialize the image processor."""
        self.logger = logging.getLogger(__name__)

        # Processing parameters
        self.bg_threshold = 200
        self.edge_low_threshold = 50
        self.edge_high_threshold = 150
        self.morphology_kernel_size = 3

        # Template drawing area dimensions (from Config)
        self.drawing_width = 779
        self.drawing_height = 457

        self.logger.info("ImageProcessor initialized")

    def remove_background(
        self,
        image: np.ndarray,
        method: BackgroundRemovalMethod = BackgroundRemovalMethod.STANDARD,
    ) -> np.ndarray:
        """
        Remove background from image using specified method.

        Args:
            image: Input image (BGR format)
            method: Background removal method

        Returns:
            Processed image with background removed
        """
        try:
            if method == BackgroundRemovalMethod.STANDARD:
                return self._remove_white_background_standard(image)
            elif method == BackgroundRemovalMethod.AGGRESSIVE:
                return self._remove_white_background_aggressive(image)
            elif method == BackgroundRemovalMethod.SMART:
                return self._remove_white_background_smart(image)
            elif method == BackgroundRemovalMethod.HSV_BASED:
                return self._remove_background_hsv(image)
            elif method == BackgroundRemovalMethod.LAB_BASED:
                return self._remove_background_lab(image)
            elif method == BackgroundRemovalMethod.THRESHOLD:
                return self._remove_background_threshold(image)
            else:
                self.logger.warning(f"Unknown background removal method: {method}")
                return image.copy()

        except Exception as e:
            self.logger.error(f"Background removal failed: {e}")
            return image.copy()

    def _remove_white_background_standard(self, image: np.ndarray) -> np.ndarray:
        """Standard white background removal."""
        if len(image.shape) == 3:
            # Convert to grayscale for thresholding
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Create mask for non-white areas
        _, mask = cv2.threshold(gray, self.bg_threshold, 255, cv2.THRESH_BINARY_INV)

        # Apply morphological operations to clean up
        kernel = np.ones(
            (self.morphology_kernel_size, self.morphology_kernel_size), np.uint8
        )
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

    def _remove_white_background_aggressive(self, image: np.ndarray) -> np.ndarray:
        """
        Aggressive white background removal using multiple color spaces.
        Removes ALL white colors from krathong image.
        """
        if len(image.shape) == 3:
            # Convert to different color spaces for better white detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            hsv = cv2.cvtColor(
                cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2HSV
            )
            lab = cv2.cvtColor(
                cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2LAB
            )

        # Method 1: HSV-based white detection
        # White has low saturation and high value
        lower_white_hsv = np.array([0, 0, 200])
        upper_white_hsv = np.array([180, 30, 255])
        mask_hsv = cv2.inRange(hsv, lower_white_hsv, upper_white_hsv)

        # Method 2: LAB-based white detection
        # White has high L (lightness) and neutral a, b
        lower_white_lab = np.array([200, 120, 120])
        upper_white_lab = np.array([255, 135, 135])
        mask_lab = cv2.inRange(lab, lower_white_lab, upper_white_lab)

        # Method 3: Grayscale threshold
        _, mask_gray = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)

        # Method 4: RGB-based white detection
        if len(image.shape) == 3:
            b, g, r = cv2.split(image)
            mask_b = (b > 200).astype(np.uint8) * 255
            mask_g = (g > 200).astype(np.uint8) * 255
            mask_r = (r > 200).astype(np.uint8) * 255
            mask_rgb = cv2.bitwise_and(cv2.bitwise_and(mask_b, mask_g), mask_r)
        else:
            mask_rgb = np.zeros_like(gray)

        # Combine all masks (OR operation)
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

    def _remove_white_background_smart(self, image: np.ndarray) -> np.ndarray:
        """Smart background removal that preserves important details."""
        # Use adaptive threshold to better handle varying lighting
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply adaptive threshold
        mask = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        # Find contours and keep only significant ones
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours by area (remove small noise)
        min_area = image.shape[0] * image.shape[1] * 0.001  # 0.1% of image area
        filtered_contours = [c for c in contours if cv2.contourArea(c) > min_area]

        # Create final mask from filtered contours
        final_mask = np.zeros_like(gray)
        cv2.drawContours(final_mask, filtered_contours, -1, 255, thickness=cv2.FILLED)

        # Apply morphological operations
        kernel = np.ones((5, 5), np.uint8)
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel)

        # Create result
        if len(image.shape) == 3:
            result = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            result[:, :, 3] = final_mask
        else:
            result = image.copy()
            result[final_mask == 0] = 255

        return result

    def _remove_background_hsv(self, image: np.ndarray) -> np.ndarray:
        """HSV-based background removal."""
        if len(image.shape) == 3:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        else:
            hsv = cv2.cvtColor(
                cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2HSV
            )

        # Define range for white colors in HSV
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 25, 255])

        # Create mask
        white_mask = cv2.inRange(hsv, lower_white, upper_white)
        mask = cv2.bitwise_not(white_mask)

        # Apply morphological operations
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Create result
        if len(image.shape) == 3:
            result = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            result[:, :, 3] = mask
        else:
            result = image.copy()
            result[mask == 0] = 255

        return result

    def _remove_background_lab(self, image: np.ndarray) -> np.ndarray:
        """LAB color space based background removal."""
        if len(image.shape) == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        else:
            lab = cv2.cvtColor(
                cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2LAB
            )

        # Define range for white colors in LAB
        lower_white = np.array([200, 120, 120])
        upper_white = np.array([255, 135, 135])

        # Create mask
        white_mask = cv2.inRange(lab, lower_white, upper_white)
        mask = cv2.bitwise_not(white_mask)

        # Apply morphological operations
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Create result
        if len(image.shape) == 3:
            result = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            result[:, :, 3] = mask
        else:
            result = image.copy()
            result[mask == 0] = 255

        return result

    def _remove_background_threshold(self, image: np.ndarray) -> np.ndarray:
        """Simple threshold-based background removal."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply threshold
        _, mask = cv2.threshold(gray, self.bg_threshold, 255, cv2.THRESH_BINARY_INV)

        # Apply morphological operations
        kernel = np.ones(
            (self.morphology_kernel_size, self.morphology_kernel_size), np.uint8
        )
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Create result
        if len(image.shape) == 3:
            result = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            result[:, :, 3] = mask
        else:
            result = image.copy()
            result[mask == 0] = 255

        return result

    def generate_mask(
        self,
        image: np.ndarray,
        method: MaskGenerationMethod = MaskGenerationMethod.CONTOUR,
    ) -> np.ndarray:
        """
        Generate mask from image using specified method.

        Args:
            image: Input image (BGR format)
            method: Mask generation method

        Returns:
            Binary mask (0=background, 255=foreground)
        """
        try:
            if method == MaskGenerationMethod.CONTOUR:
                return self._generate_mask_contour(image)
            elif method == MaskGenerationMethod.THRESHOLD:
                return self._generate_mask_threshold(image)
            elif method == MaskGenerationMethod.EDGE_DETECTION:
                return self._generate_mask_edges(image)
            elif method == MaskGenerationMethod.COLOR_SEGMENTATION:
                return self._generate_mask_color_segmentation(image)
            else:
                self.logger.warning(f"Unknown mask generation method: {method}")
                return self._generate_mask_contour(image)

        except Exception as e:
            self.logger.error(f"Mask generation failed: {e}")
            # Return empty mask on failure
            return np.zeros((self.drawing_height, self.drawing_width), dtype=np.uint8)

    def _generate_mask_contour(self, image: np.ndarray) -> np.ndarray:
        """
        Generate mask using contour detection.
        Creates a mask with the exact size of the template drawing area.
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Threshold to create binary mask (inverted - white background becomes 0)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Create mask with template drawing area size
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
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        return mask

    def _generate_mask_threshold(self, image: np.ndarray) -> np.ndarray:
        """Generate mask using simple thresholding."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply threshold
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

        # Resize to template drawing area
        mask = cv2.resize(binary, (self.drawing_width, self.drawing_height))

        # Apply morphological operations
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        return mask

    def _generate_mask_edges(self, image: np.ndarray) -> np.ndarray:
        """Generate mask using edge detection."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply edge detection
        edges = cv2.Canny(gray, self.edge_low_threshold, self.edge_high_threshold)

        # Dilate edges to create thicker lines
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=2)

        # Fill enclosed areas
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        mask = np.zeros_like(edges)
        cv2.drawContours(mask, contours, -1, 255, thickness=cv2.FILLED)

        # Resize to template drawing area
        mask = cv2.resize(mask, (self.drawing_width, self.drawing_height))

        return mask

    def _generate_mask_color_segmentation(self, image: np.ndarray) -> np.ndarray:
        """Generate mask using color segmentation."""
        if len(image.shape) == 3:
            # Convert to HSV for better color segmentation
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Define range for non-white colors
            lower_color = np.array([0, 30, 30])
            upper_color = np.array([180, 255, 200])

            # Create mask
            mask = cv2.inRange(hsv, lower_color, upper_color)
        else:
            # For grayscale, use threshold
            _, mask = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY_INV)

        # Apply morphological operations
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Resize to template drawing area
        mask = cv2.resize(mask, (self.drawing_width, self.drawing_height))

        return mask

    def enhance_image(
        self,
        image: np.ndarray,
        enhance_contrast: bool = True,
        enhance_sharpness: bool = True,
    ) -> np.ndarray:
        """
        Enhance image quality for better processing.

        Args:
            image: Input image
            enhance_contrast: Whether to enhance contrast
            enhance_sharpness: Whether to enhance sharpness

        Returns:
            Enhanced image
        """
        result = image.copy()

        try:
            if enhance_contrast:
                # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
                if len(result.shape) == 3:
                    lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
                    result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                else:
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    result = clahe.apply(result)

            if enhance_sharpness:
                # Apply unsharp mask
                kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                result = cv2.filter2D(result, -1, kernel)

            return result

        except Exception as e:
            self.logger.error(f"Image enhancement failed: {e}")
            return image.copy()

    def get_processing_info(self) -> Dict[str, Any]:
        """Get information about processing parameters."""
        return {
            "bg_threshold": self.bg_threshold,
            "edge_low_threshold": self.edge_low_threshold,
            "edge_high_threshold": self.edge_high_threshold,
            "morphology_kernel_size": self.morphology_kernel_size,
            "drawing_width": self.drawing_width,
            "drawing_height": self.drawing_height,
            "available_bg_methods": [
                method.value for method in BackgroundRemovalMethod
            ],
            "available_mask_methods": [method.value for method in MaskGenerationMethod],
        }

    def set_parameters(self, **kwargs):
        """Set processing parameters."""
        if "bg_threshold" in kwargs:
            self.bg_threshold = kwargs["bg_threshold"]
        if "edge_low_threshold" in kwargs:
            self.edge_low_threshold = kwargs["edge_low_threshold"]
        if "edge_high_threshold" in kwargs:
            self.edge_high_threshold = kwargs["edge_high_threshold"]
        if "morphology_kernel_size" in kwargs:
            self.morphology_kernel_size = kwargs["morphology_kernel_size"]

        self.logger.debug(f"Parameters updated: {kwargs}")


if __name__ == "__main__":
    # Test the image processor
    import tkinter as tk
    from tkinter import filedialog

    # Load test image
    root = tk.Tk()
    root.withdraw()

    image_path = filedialog.askopenfilename(title="Select test image")
    if image_path:
        image = cv2.imread(image_path)
        if image is not None:
            processor = ImageProcessor()

            # Test background removal
            print("Testing background removal methods...")
            for method in BackgroundRemovalMethod:
                result = processor.remove_background(image, method)
                print(f"  {method.value}: {result.shape}")

            # Test mask generation
            print("Testing mask generation methods...")
            for method in MaskGenerationMethod:
                mask = processor.generate_mask(image, method)
                print(f"  {method.value}: {mask.shape}")

            print("Testing completed successfully!")
        else:
            print("Failed to load image")
    else:
        print("No image selected")

    root.destroy()
