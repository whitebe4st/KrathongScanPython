"""
Image utility functions for KrathongScanner.
"""

from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageTk


class ImageUtils:
    """Utility functions for image operations."""

    @staticmethod
    def load_image(path: Path) -> Optional[np.ndarray]:
        """Load image from file path."""
        try:
            image = cv2.imread(str(path))
            if image is None:
                print(f"Error loading image: {path}")
                return None
            return image
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            return None

    @staticmethod
    def save_image(image: np.ndarray, path: Path) -> bool:
        """Save image to file path."""
        try:
            cv2.imwrite(str(path), image)
            return True
        except Exception as e:
            print(f"Error saving image to {path}: {e}")
            return False

    @staticmethod
    def resize_image(
        image: np.ndarray, width: int, height: int, keep_aspect: bool = True
    ) -> np.ndarray:
        """Resize image with optional aspect ratio preservation."""
        if keep_aspect:
            h, w = image.shape[:2]
            aspect_ratio = w / h

            if width / height > aspect_ratio:
                new_width = int(height * aspect_ratio)
                new_height = height
            else:
                new_width = width
                new_height = int(width / aspect_ratio)

            resized = cv2.resize(image, (new_width, new_height))

            # Create canvas with target size
            canvas = np.zeros((height, width, 3), dtype=np.uint8)

            # Center the resized image
            y_offset = (height - new_height) // 2
            x_offset = (width - new_width) // 2
            canvas[
                y_offset : y_offset + new_height, x_offset : x_offset + new_width
            ] = resized

            return canvas
        else:
            return cv2.resize(image, (width, height))

    @staticmethod
    def crop_image(
        image: np.ndarray, x: int, y: int, width: int, height: int
    ) -> np.ndarray:
        """Crop image to specified rectangle."""
        try:
            h, w = image.shape[:2]

            # Ensure coordinates are within bounds
            x = max(0, min(x, w))
            y = max(0, min(y, h))
            width = min(width, w - x)
            height = min(height, h - y)

            return image[y : y + height, x : x + width]
        except Exception as e:
            print(f"Error cropping image: {e}")
            return image

    @staticmethod
    def convert_bgr_to_rgb(image: np.ndarray) -> np.ndarray:
        """Convert BGR image to RGB."""
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    @staticmethod
    def convert_rgb_to_bgr(image: np.ndarray) -> np.ndarray:
        """Convert RGB image to BGR."""
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    @staticmethod
    def convert_to_pil(image: np.ndarray) -> Image.Image:
        """Convert OpenCV image to PIL Image."""
        if len(image.shape) == 3:
            rgb_image = ImageUtils.convert_bgr_to_rgb(image)
            return Image.fromarray(rgb_image)
        else:
            return Image.fromarray(image)

    @staticmethod
    def convert_to_tkinter(
        image: np.ndarray, max_width: int = 800, max_height: int = 600
    ) -> ImageTk.PhotoImage:
        """Convert OpenCV image to Tkinter PhotoImage."""
        pil_image = ImageUtils.convert_to_pil(image)

        # Resize if too large
        if pil_image.width > max_width or pil_image.height > max_height:
            pil_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        return ImageTk.PhotoImage(pil_image)

    @staticmethod
    def remove_white_background(image: np.ndarray, threshold: int = 240) -> np.ndarray:
        """Remove white background from image."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Create mask for white pixels
            mask = gray > threshold

            # Convert to 3-channel mask
            mask_3ch = cv2.cvtColor(mask.astype(np.uint8) * 255, cv2.COLOR_GRAY2BGR)

            # Apply mask
            result = cv2.bitwise_and(image, mask_3ch)

            # Make background transparent
            result = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)
            result[:, :, 3] = mask.astype(np.uint8) * 255

            return result
        except Exception as e:
            print(f"Error removing white background: {e}")
            return image

    @staticmethod
    def add_border(
        image: np.ndarray, border_size: int, color: Tuple[int, int, int] = (0, 0, 0)
    ) -> np.ndarray:
        """Add border to image."""
        return cv2.copyMakeBorder(
            image,
            border_size,
            border_size,
            border_size,
            border_size,
            cv2.BORDER_CONSTANT,
            value=color,
        )

    @staticmethod
    def get_image_info(image: np.ndarray) -> dict:
        """Get image information."""
        if image is None:
            return {}

        h, w = image.shape[:2]
        channels = image.shape[2] if len(image.shape) > 2 else 1

        return {
            "width": w,
            "height": h,
            "channels": channels,
            "dtype": str(image.dtype),
            "size": image.size,
        }

    @staticmethod
    def create_thumbnail(
        image: np.ndarray, size: Tuple[int, int] = (150, 150)
    ) -> np.ndarray:
        """Create thumbnail of image."""
        return cv2.resize(image, size)

    @staticmethod
    def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by specified angle."""
        h, w = image.shape[:2]
        center = (w // 2, h // 2)

        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, rotation_matrix, (w, h))

        return rotated

    @staticmethod
    def flip_image(image: np.ndarray, direction: str = "horizontal") -> np.ndarray:
        """Flip image horizontally or vertically."""
        if direction == "horizontal":
            return cv2.flip(image, 1)
        elif direction == "vertical":
            return cv2.flip(image, 0)
        else:
            return image
