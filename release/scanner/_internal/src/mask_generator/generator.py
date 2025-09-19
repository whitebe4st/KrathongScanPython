"""
Perfect Mask Generator for ArUco Detection System.

This module automatically generates optimized template masks based on:
- Universal cropping ratios (1.149 width, 1.225 height)
- Krathong shape parameters
- Content positioning and scaling
"""

import logging
import math
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np


class PerfectMaskGenerator:
    """
    Automated generator for perfect template masks optimized for universal cropping.

    Creates masks that are mathematically perfect for the universal ratio-based
    cropping system, ensuring consistent results across all image types.
    """

    def __init__(self):
        """Initialize the mask generator."""
        self.logger = self._setup_logger()

        # Universal cropping ratios from the detection system
        self.target_ratio_w = 1.149
        self.target_ratio_h = 1.225

        # Standard dimensions for universal cropping
        self.standard_crop_width = 773
        self.standard_crop_height = 462

        self.logger.info("Perfect Mask Generator initialized")

    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the mask generator."""
        logger = logging.getLogger("mask_generator.generator")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def generate_krathong_mask(
        self,
        width: int,
        height: int,
        content_scale: float = 0.7,
        base_width_ratio: float = 0.6,
        base_height_ratio: float = 0.25,
        lotus_layers: int = 3,
        candle_height_ratio: float = 0.4,
        output_path: Optional[str] = None,
    ) -> np.ndarray:
        """
        Generate a perfect krathong-shaped mask optimized for universal cropping.

        Args:
            width: Mask width in pixels
            height: Mask height in pixels
            content_scale: Overall scale of the krathong (0.5-0.9)
            base_width_ratio: Width of the base relative to content area (0.4-0.8)
            base_height_ratio: Height of the base relative to content area (0.2-0.4)
            lotus_layers: Number of lotus petal layers (2-4)
            candle_height_ratio: Height of candle relative to content area (0.3-0.5)
            output_path: Optional path to save the mask

        Returns:
            Generated mask as numpy array (grayscale)
        """
        try:
            self.logger.info(f"Generating krathong mask: {width}x{height}")

            # Create blank mask
            mask = np.zeros((height, width), dtype=np.uint8)

            # Calculate content area (centered)
            content_width = int(width * content_scale)
            content_height = int(height * content_scale)
            center_x = width // 2
            center_y = height // 2

            # Content bounds
            content_left = center_x - content_width // 2
            content_right = center_x + content_width // 2
            content_top = center_y - content_height // 2
            content_bottom = center_y + content_height // 2

            self.logger.info(
                f"Content area: {content_width}x{content_height} at ({center_x}, {center_y})"
            )

            # Generate krathong components
            self._draw_krathong_base(
                mask,
                center_x,
                center_y,
                content_width,
                content_height,
                base_width_ratio,
                base_height_ratio,
            )
            self._draw_lotus_petals(
                mask,
                center_x,
                center_y,
                content_width,
                content_height,
                base_width_ratio,
                lotus_layers,
            )
            self._draw_candle_and_flame(
                mask,
                center_x,
                center_y,
                content_width,
                content_height,
                candle_height_ratio,
            )

            # Apply smoothing for better edge quality
            mask = cv2.GaussianBlur(mask, (3, 3), 0.5)

            # Ensure binary mask (white = extract, black = ignore)
            _, mask = cv2.threshold(mask, 128, 255, cv2.THRESH_BINARY)

            # Save if path provided
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(output_path, mask)
                self.logger.info(f"Mask saved to: {output_path}")

            # Calculate mask statistics
            white_pixels = np.sum(mask == 255)
            total_pixels = mask.shape[0] * mask.shape[1]
            coverage = (white_pixels / total_pixels) * 100

            self.logger.info(
                f"Mask generated: {coverage:.1f}% coverage ({white_pixels:,}/{total_pixels:,} pixels)"
            )

            return mask

        except Exception as e:
            self.logger.error(f"Error generating krathong mask: {e}")
            raise

    def _draw_krathong_base(
        self,
        mask: np.ndarray,
        center_x: int,
        center_y: int,
        content_width: int,
        content_height: int,
        base_width_ratio: float,
        base_height_ratio: float,
    ):
        """Draw the base/bowl of the krathong."""
        base_width = int(content_width * base_width_ratio)
        base_height = int(content_height * base_height_ratio)

        # Position base in lower portion
        base_center_y = center_y + int(content_height * 0.1)

        # Draw elliptical base
        cv2.ellipse(
            mask,
            (center_x, base_center_y),
            (base_width // 2, base_height // 2),
            0,
            0,
            360,
            255,
            -1,
        )

        self.logger.debug(
            f"Drew krathong base: {base_width}x{base_height} at ({center_x}, {base_center_y})"
        )

    def _draw_lotus_petals(
        self,
        mask: np.ndarray,
        center_x: int,
        center_y: int,
        content_width: int,
        content_height: int,
        base_width_ratio: float,
        lotus_layers: int,
    ):
        """Draw lotus petals around the krathong."""
        base_radius = int(content_width * base_width_ratio * 0.6)

        for layer in range(lotus_layers):
            # Each layer is progressively larger and has more petals
            layer_radius = base_radius + (layer * 15)
            petals_in_layer = 8 + (layer * 2)
            petal_size = 12 + (layer * 3)

            for i in range(petals_in_layer):
                angle = (2 * math.pi * i) / petals_in_layer

                # Petal position
                petal_x = center_x + int(layer_radius * math.cos(angle))
                petal_y = center_y + int(layer_radius * math.sin(angle))

                # Draw petal as small ellipse
                petal_angle = math.degrees(angle)
                cv2.ellipse(
                    mask,
                    (petal_x, petal_y),
                    (petal_size, petal_size // 2),
                    petal_angle,
                    0,
                    360,
                    255,
                    -1,
                )

        self.logger.debug(
            f"Drew {lotus_layers} lotus layers with {petals_in_layer} petals each"
        )

    def _draw_candle_and_flame(
        self,
        mask: np.ndarray,
        center_x: int,
        center_y: int,
        content_width: int,
        content_height: int,
        candle_height_ratio: float,
    ):
        """Draw candle and flame on top of the krathong."""
        candle_height = int(content_height * candle_height_ratio)
        candle_width = max(8, candle_height // 6)

        # Position candle above center
        candle_bottom = center_y - int(content_height * 0.1)
        candle_top = candle_bottom - candle_height

        # Draw candle (rectangle)
        cv2.rectangle(
            mask,
            (center_x - candle_width // 2, candle_top),
            (center_x + candle_width // 2, candle_bottom),
            255,
            -1,
        )

        # Draw flame (teardrop shape)
        flame_height = candle_height // 3
        flame_width = candle_width
        flame_center_y = candle_top - flame_height // 2

        # Flame as ellipse
        cv2.ellipse(
            mask,
            (center_x, flame_center_y),
            (flame_width // 2, flame_height // 2),
            0,
            0,
            360,
            255,
            -1,
        )

        # Flame tip (smaller ellipse)
        tip_height = flame_height // 3
        tip_y = flame_center_y - flame_height // 3
        cv2.ellipse(
            mask,
            (center_x, tip_y),
            (flame_width // 4, tip_height // 2),
            0,
            0,
            360,
            255,
            -1,
        )

        self.logger.debug(f"Drew candle: {candle_width}x{candle_height} with flame")

    def generate_optimized_mask_for_universal_cropping(
        self, target_coverage: float = 22.8, output_path: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate a mask specifically optimized for the universal cropping system.

        This method analyzes the current universal cropping parameters and generates
        a mask with perfect dimensions and optimal content coverage.

        Args:
            target_coverage: Target coverage percentage (20-30% recommended)
            output_path: Optional path to save the mask

        Returns:
            Optimized mask as numpy array
        """
        try:
            # Use standard universal cropping dimensions
            width = self.standard_crop_width
            height = self.standard_crop_height

            self.logger.info(
                f"Generating optimized mask for universal cropping: {width}x{height}"
            )
            self.logger.info(f"Target coverage: {target_coverage:.1f}%")

            # Calculate optimal content scale to achieve target coverage
            # Krathong typically covers about 32% at scale 0.7, so adjust accordingly
            base_coverage_at_07 = 32.0
            optimal_scale = 0.7 * math.sqrt(target_coverage / base_coverage_at_07)
            optimal_scale = max(
                0.5, min(0.9, optimal_scale)
            )  # Clamp to reasonable range

            self.logger.info(f"Calculated optimal content scale: {optimal_scale:.3f}")

            # Generate mask with optimized parameters
            mask = self.generate_krathong_mask(
                width=width,
                height=height,
                content_scale=optimal_scale,
                base_width_ratio=0.6,
                base_height_ratio=0.25,
                lotus_layers=3,
                candle_height_ratio=0.4,
                output_path=output_path,
            )

            # Verify coverage
            actual_coverage = (
                np.sum(mask == 255) / (mask.shape[0] * mask.shape[1])
            ) * 100
            coverage_diff = abs(actual_coverage - target_coverage)

            self.logger.info(f"Generated optimized mask:")
            self.logger.info(f"  Dimensions: {width}x{height}")
            self.logger.info(f"  Target coverage: {target_coverage:.1f}%")
            self.logger.info(f"  Actual coverage: {actual_coverage:.1f}%")
            self.logger.info(f"  Coverage difference: {coverage_diff:.1f}%")

            if coverage_diff > 2.0:
                self.logger.warning(
                    f"Coverage difference is high ({coverage_diff:.1f}%). Consider adjusting parameters."
                )

            return mask

        except Exception as e:
            self.logger.error(f"Error generating optimized mask: {e}")
            raise

    def analyze_current_masks(self, mask_paths: List[str]) -> dict:
        """
        Analyze existing masks to understand their characteristics.

        Args:
            mask_paths: List of paths to existing mask files

        Returns:
            Dictionary with analysis results
        """
        try:
            analysis = {
                "masks": [],
                "average_coverage": 0.0,
                "coverage_variation": 0.0,
                "recommended_dimensions": None,
            }

            coverages = []

            for mask_path in mask_paths:
                if not Path(mask_path).exists():
                    self.logger.warning(f"Mask not found: {mask_path}")
                    continue

                mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
                if mask is None:
                    self.logger.warning(f"Could not load mask: {mask_path}")
                    continue

                white_pixels = np.sum(mask > 128)
                total_pixels = mask.shape[0] * mask.shape[1]
                coverage = (white_pixels / total_pixels) * 100

                mask_info = {
                    "path": mask_path,
                    "dimensions": mask.shape,
                    "coverage": coverage,
                    "white_pixels": white_pixels,
                    "total_pixels": total_pixels,
                }

                analysis["masks"].append(mask_info)
                coverages.append(coverage)

                self.logger.info(
                    f"Analyzed {Path(mask_path).name}: {mask.shape} - {coverage:.1f}% coverage"
                )

            if coverages:
                analysis["average_coverage"] = sum(coverages) / len(coverages)
                analysis["coverage_variation"] = max(coverages) - min(coverages)

                # Recommend dimensions based on universal cropping
                analysis["recommended_dimensions"] = (
                    self.standard_crop_width,
                    self.standard_crop_height,
                )

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing masks: {e}")
            return {"error": str(e)}
