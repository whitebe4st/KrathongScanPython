"""
Mask Converter for ArUco Detection System.

This module converts white-filled PNG/SVG images (with transparent backgrounds)
into optimized template masks for the universal cropping system.
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np


class MaskConverter:
    """
    Converts artwork (PNG/SVG) into optimized template masks.

    Takes white-filled images with transparent backgrounds and converts them
    into perfect binary masks optimized for the universal cropping system.
    """

    def __init__(self):
        """Initialize the mask converter."""
        self.logger = self._setup_logger()

        # Universal cropping dimensions
        self.target_width = 773
        self.target_height = 462

        self.logger.info("Mask Converter initialized")

    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the converter."""
        logger = logging.getLogger("mask_generator.converter")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def convert_png_to_mask(
        self,
        input_path: str,
        output_path: str,
        target_coverage: Optional[float] = None,
        content_scale: float = 0.8,
        center_offset: Tuple[int, int] = (0, 0),
        content_size: Optional[Tuple[int, int]] = None,
    ) -> np.ndarray:
        """
        Convert a white-filled PNG with transparent background to an optimized mask.

        Args:
            input_path: Path to input PNG file
            output_path: Path to save the output mask
            target_coverage: Target coverage percentage (auto-optimize if None)
            content_scale: Scale factor for the content (0.5-1.0)
            center_offset: Offset from center in pixels (x, y)

        Returns:
            Generated mask as numpy array
        """
        try:
            self.logger.info(f"Converting PNG to mask: {input_path}")

            # Load the input image
            input_img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
            if input_img is None:
                raise ValueError(f"Could not load image: {input_path}")

            # Handle different channel formats
            if input_img.shape[2] == 4:  # BGRA
                # Extract alpha channel as mask
                alpha = input_img[:, :, 3]
                # Use alpha channel to create white content on black background
                content_mask = np.where(alpha > 128, 255, 0).astype(np.uint8)
            elif input_img.shape[2] == 3:  # BGR
                # Convert to grayscale and threshold
                gray = cv2.cvtColor(input_img, cv2.COLOR_BGR2GRAY)
                # Assume white content on any background
                _, content_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            else:
                # Grayscale
                _, content_mask = cv2.threshold(input_img, 200, 255, cv2.THRESH_BINARY)

            self.logger.info(f"Input image: {input_img.shape}, extracted content mask")

            # Create output mask with target dimensions
            output_mask = np.zeros(
                (self.target_height, self.target_width), dtype=np.uint8
            )

            # Calculate scaling to fit content
            input_h, input_w = content_mask.shape

            if content_size is not None:
                # Use specified content dimensions
                new_w, new_h = content_size
                self.logger.info(f"Using specified content size: {new_w}x{new_h}")
            else:
                # Calculate scaling based on content_scale
                scale_w = (self.target_width * content_scale) / input_w
                scale_h = (self.target_height * content_scale) / input_h

                # Use the smaller scale to maintain aspect ratio
                scale = min(scale_w, scale_h)

                # Override with specified content_scale if it's meant to be the actual scale factor
                if content_scale < 1.0 and content_scale > 0.1:
                    # content_scale is likely the direct scale factor we want to use
                    scale = content_scale

                new_w = int(input_w * scale)
                new_h = int(input_h * scale)

            # Resize content mask
            resized_content = cv2.resize(
                content_mask, (new_w, new_h), interpolation=cv2.INTER_AREA
            )

            # Calculate position (center + offset)
            center_x = self.target_width // 2 + center_offset[0]
            center_y = self.target_height // 2 + center_offset[1]

            start_x = center_x - new_w // 2
            start_y = center_y - new_h // 2
            end_x = start_x + new_w
            end_y = start_y + new_h

            # Ensure bounds
            start_x = max(0, start_x)
            start_y = max(0, start_y)
            end_x = min(self.target_width, end_x)
            end_y = min(self.target_height, end_y)

            # Adjust resized content if needed
            actual_w = end_x - start_x
            actual_h = end_y - start_y

            if actual_w != new_w or actual_h != new_h:
                resized_content = cv2.resize(
                    resized_content, (actual_w, actual_h), interpolation=cv2.INTER_AREA
                )

            # Place content in output mask
            output_mask[start_y:end_y, start_x:end_x] = resized_content

            # Apply smoothing for better quality
            output_mask = cv2.GaussianBlur(output_mask, (3, 3), 0.5)

            # Ensure binary mask
            _, output_mask = cv2.threshold(output_mask, 128, 255, cv2.THRESH_BINARY)

            # Calculate coverage
            white_pixels = np.sum(output_mask == 255)
            total_pixels = output_mask.shape[0] * output_mask.shape[1]
            actual_coverage = (white_pixels / total_pixels) * 100

            # Save the mask
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(output_path, output_mask)

            self.logger.info(f"Mask converted successfully:")
            self.logger.info(f"  Input: {input_w}×{input_h}")
            self.logger.info(f"  Output: {self.target_width}×{self.target_height}")
            if content_size is not None:
                scale_w = new_w / input_w
                scale_h = new_h / input_h
                self.logger.info(f"  Scale: {scale_w:.3f}×{scale_h:.3f} (custom size)")
            else:
                self.logger.info(f"  Scale: {scale:.3f}")
            self.logger.info(f"  Content size: {new_w}×{new_h}")
            self.logger.info(f"  Coverage: {actual_coverage:.1f}%")
            self.logger.info(f"  Saved: {output_path}")

            return output_mask

        except Exception as e:
            self.logger.error(f"Error converting PNG to mask: {e}")
            raise

    def convert_svg_to_mask(
        self,
        input_path: str,
        output_path: str,
        target_coverage: Optional[float] = None,
        content_scale: float = 0.8,
        center_offset: Tuple[int, int] = (0, 0),
    ) -> np.ndarray:
        """
        Convert an SVG file to an optimized mask.

        First converts SVG to PNG, then processes as PNG.
        Requires Inkscape or similar SVG converter.

        Args:
            input_path: Path to input SVG file
            output_path: Path to save the output mask
            target_coverage: Target coverage percentage (auto-optimize if None)
            content_scale: Scale factor for the content (0.5-1.0)
            center_offset: Offset from center in pixels (x, y)

        Returns:
            Generated mask as numpy array
        """
        try:
            self.logger.info(f"Converting SVG to mask: {input_path}")

            # Create temporary PNG file
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_png_path = temp_file.name

            # Try to convert SVG to PNG using Inkscape
            try:
                # Try Inkscape command
                subprocess.run(
                    [
                        "inkscape",
                        "--export-type=png",
                        "--export-background-opacity=0",
                        f"--export-filename={temp_png_path}",
                        input_path,
                    ],
                    check=True,
                    capture_output=True,
                )

                self.logger.info("SVG converted to PNG using Inkscape")

            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.warning("Inkscape not found, trying alternative methods...")

                # Try using cairosvg (Python library)
                try:
                    import cairosvg

                    cairosvg.svg2png(url=input_path, write_to=temp_png_path)
                    self.logger.info("SVG converted to PNG using cairosvg")

                except ImportError:
                    self.logger.error(
                        "No SVG converter available. Install Inkscape or cairosvg."
                    )
                    raise ValueError("SVG conversion requires Inkscape or cairosvg")

            # Now convert the PNG to mask
            result_mask = self.convert_png_to_mask(
                temp_png_path,
                output_path,
                target_coverage,
                content_scale,
                center_offset,
            )

            # Clean up temporary file
            Path(temp_png_path).unlink()

            return result_mask

        except Exception as e:
            self.logger.error(f"Error converting SVG to mask: {e}")
            raise

    def optimize_coverage(
        self,
        input_path: str,
        output_path: str,
        target_coverage: float = 22.8,
        max_iterations: int = 10,
    ) -> np.ndarray:
        """
        Automatically optimize the mask to achieve target coverage.

        Args:
            input_path: Path to input image file
            output_path: Path to save the optimized mask
            target_coverage: Target coverage percentage
            max_iterations: Maximum optimization iterations

        Returns:
            Optimized mask
        """
        try:
            self.logger.info(f"Optimizing mask for {target_coverage:.1f}% coverage")

            best_mask = None
            best_diff = float("inf")
            best_scale = 0.8

            # Try different content scales to achieve target coverage
            for iteration in range(max_iterations):
                test_scale = 0.5 + (iteration * 0.05)  # 0.5 to 0.95

                # Create temporary output for testing
                with tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                ) as temp_file:
                    temp_output = temp_file.name

                try:
                    # Convert with test scale
                    test_mask = self.convert_png_to_mask(
                        input_path, temp_output, content_scale=test_scale
                    )

                    # Calculate coverage
                    white_pixels = np.sum(test_mask == 255)
                    total_pixels = test_mask.shape[0] * test_mask.shape[1]
                    actual_coverage = (white_pixels / total_pixels) * 100

                    # Check if this is better
                    diff = abs(actual_coverage - target_coverage)
                    if diff < best_diff:
                        best_diff = diff
                        best_mask = test_mask.copy()
                        best_scale = test_scale

                    self.logger.debug(
                        f"Scale {test_scale:.2f}: {actual_coverage:.1f}% (diff: {diff:.1f}%)"
                    )

                    # Clean up temp file
                    Path(temp_output).unlink()

                    # Early exit if we're close enough
                    if diff < 0.5:
                        break

                except Exception as e:
                    self.logger.warning(f"Failed test with scale {test_scale:.2f}: {e}")
                    continue

            if best_mask is not None:
                # Save the best mask
                cv2.imwrite(output_path, best_mask)

                best_coverage = (
                    np.sum(best_mask == 255) / (best_mask.shape[0] * best_mask.shape[1])
                ) * 100

                self.logger.info(f"Optimization completed:")
                self.logger.info(f"  Best scale: {best_scale:.3f}")
                self.logger.info(f"  Target coverage: {target_coverage:.1f}%")
                self.logger.info(f"  Achieved coverage: {best_coverage:.1f}%")
                self.logger.info(f"  Difference: {best_diff:.1f}%")

                return best_mask
            else:
                raise ValueError("Optimization failed - no valid masks generated")

        except Exception as e:
            self.logger.error(f"Error optimizing coverage: {e}")
            raise
