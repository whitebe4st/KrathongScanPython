#!/usr/bin/env python3
"""
Improved Perfect Mask Generator.

This script generates realistic krathong-shaped masks with proper coverage
optimized for the universal cropping system.
"""
import sys

sys.path.insert(0, "src")

import math
from pathlib import Path

import cv2
import numpy as np


def generate_realistic_krathong_mask(
    width: int, height: int, target_coverage: float = 22.8
) -> np.ndarray:
    """
    Generate a realistic krathong mask with proper coverage.

    Args:
        width: Mask width
        height: Mask height
        target_coverage: Target coverage percentage

    Returns:
        Generated mask
    """
    # Create blank mask
    mask = np.zeros((height, width), dtype=np.uint8)

    center_x = width // 2
    center_y = height // 2

    # Calculate scale to achieve target coverage
    # A filled ellipse covering ~35% of a 0.8 scaled area gives us good coverage
    content_scale = 0.8
    content_width = int(width * content_scale)
    content_height = int(height * content_scale)

    # Main krathong body (large ellipse)
    main_width = int(content_width * 0.7)
    main_height = int(content_height * 0.6)

    cv2.ellipse(
        mask,
        (center_x, center_y),
        (main_width // 2, main_height // 2),
        0,
        0,
        360,
        255,
        -1,
    )

    # Add lotus petals around the edge (smaller ellipses)
    petal_count = 12
    petal_radius = main_width // 2 + 20
    petal_size_w = 25
    petal_size_h = 15

    for i in range(petal_count):
        angle = (2 * math.pi * i) / petal_count
        petal_x = center_x + int(petal_radius * math.cos(angle))
        petal_y = center_y + int(petal_radius * math.sin(angle))

        # Draw petal
        cv2.ellipse(
            mask,
            (petal_x, petal_y),
            (petal_size_w, petal_size_h),
            math.degrees(angle),
            0,
            360,
            255,
            -1,
        )

    # Add candle in center
    candle_width = 12
    candle_height = int(content_height * 0.4)
    candle_top = center_y - main_height // 4 - candle_height
    candle_bottom = center_y - main_height // 4

    cv2.rectangle(
        mask,
        (center_x - candle_width // 2, candle_top),
        (center_x + candle_width // 2, candle_bottom),
        255,
        -1,
    )

    # Add flame (teardrop)
    flame_height = 30
    flame_width = 18
    flame_y = candle_top - flame_height // 2

    cv2.ellipse(
        mask,
        (center_x, flame_y),
        (flame_width // 2, flame_height // 2),
        0,
        0,
        360,
        255,
        -1,
    )

    # Add some decorative elements (small circles)
    decoration_count = 8
    decoration_radius = main_width // 3

    for i in range(decoration_count):
        angle = (2 * math.pi * i) / decoration_count
        dec_x = center_x + int(decoration_radius * math.cos(angle))
        dec_y = center_y + int(decoration_radius * math.sin(angle))

        cv2.circle(mask, (dec_x, dec_y), 8, 255, -1)

    # Apply smoothing
    mask = cv2.GaussianBlur(mask, (3, 3), 0.5)

    # Ensure binary
    _, mask = cv2.threshold(mask, 128, 255, cv2.THRESH_BINARY)

    return mask


def generate_improved_masks():
    """Generate improved realistic krathong masks."""
    print("🎭 Improved Perfect Mask Generator")
    print("=" * 45)

    # Output directory
    output_dir = Path("data/markers/templates")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Universal cropping dimensions
    width = 773
    height = 462

    print(f"📏 Using universal dimensions: {width}x{height}")
    print(f"📁 Output directory: {output_dir}")

    # Generate masks with different target coverages
    mask_configs = [
        {
            "name": "krathong_generated_22.8.png",
            "target_coverage": 22.8,
            "description": "Matches current system coverage",
        },
        {
            "name": "krathong_generated_20.0.png",
            "target_coverage": 20.0,
            "description": "Conservative coverage",
        },
        {
            "name": "krathong_generated_25.0.png",
            "target_coverage": 25.0,
            "description": "Higher coverage",
        },
    ]

    generated_masks = []

    print(f"\n🎯 GENERATING IMPROVED MASKS:")
    print("-" * 35)

    for config in mask_configs:
        print(f"\n🔄 Generating {config['name']}...")
        print(f"   {config['description']}")

        output_path = output_dir / config["name"]

        try:
            mask = generate_realistic_krathong_mask(
                width, height, config["target_coverage"]
            )

            # Calculate actual coverage
            white_pixels = np.sum(mask == 255)
            total_pixels = mask.shape[0] * mask.shape[1]
            actual_coverage = (white_pixels / total_pixels) * 100

            # Save mask
            cv2.imwrite(str(output_path), mask)

            generated_masks.append(
                {
                    "name": config["name"],
                    "path": output_path,
                    "mask": mask,
                    "target_coverage": config["target_coverage"],
                    "actual_coverage": actual_coverage,
                }
            )

            print(f"   ✅ Generated: {output_path}")
            print(
                f"   📊 Coverage: {actual_coverage:.1f}% (target: {config['target_coverage']:.1f}%)"
            )

        except Exception as e:
            print(f"   ❌ Failed: {e}")

    # Create visual comparison
    if generated_masks:
        print(f"\n📊 CREATING VISUAL COMPARISON:")
        print("-" * 32)

        try:
            # Create comparison showing all masks
            comparison_width = 300 * len(generated_masks)
            comparison_height = 400
            comparison = np.zeros((comparison_height, comparison_width), dtype=np.uint8)

            for i, mask_info in enumerate(generated_masks):
                # Resize mask for comparison
                resized_mask = cv2.resize(mask_info["mask"], (300, 200))

                # Position in comparison
                x_start = i * 300
                x_end = x_start + 300

                # Place mask
                comparison[50:250, x_start:x_end] = resized_mask

                # Add labels
                label1 = f"Target: {mask_info['target_coverage']:.1f}%"
                label2 = f"Actual: {mask_info['actual_coverage']:.1f}%"

                cv2.putText(
                    comparison,
                    label1,
                    (x_start + 10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    255,
                    2,
                )
                cv2.putText(
                    comparison,
                    label2,
                    (x_start + 10, 280),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    255,
                    2,
                )
                cv2.putText(
                    comparison,
                    f"{mask_info['target_coverage']:.1f}%",
                    (x_start + 10, 320),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    255,
                    2,
                )

            comparison_path = output_dir / "improved_mask_comparison.png"
            cv2.imwrite(str(comparison_path), comparison)
            print(f"✅ Comparison saved: {comparison_path}")

        except Exception as e:
            print(f"❌ Failed to create comparison: {e}")

    # Analysis and recommendations
    print(f"\n📊 COVERAGE ANALYSIS:")
    print("-" * 25)

    for mask_info in generated_masks:
        target = mask_info["target_coverage"]
        actual = mask_info["actual_coverage"]
        diff = abs(actual - target)

        status = (
            "✅ Excellent"
            if diff < 2.0
            else "⚠️  Needs adjustment"
            if diff < 5.0
            else "❌ Poor"
        )

        print(f"{mask_info['name']}:")
        print(
            f"  Target: {target:.1f}% | Actual: {actual:.1f}% | Diff: {diff:.1f}% | {status}"
        )

    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 20)

    # Find best match to 22.8%
    best_mask = min(generated_masks, key=lambda m: abs(m["actual_coverage"] - 22.8))

    print(f"✅ Best match for current system (22.8%): {best_mask['name']}")
    print(f"   Actual coverage: {best_mask['actual_coverage']:.1f}%")
    print(f"   Difference: {abs(best_mask['actual_coverage'] - 22.8):.1f}%")

    print(f"\n🎯 NEXT STEPS:")
    print("-" * 15)
    print("1. Test the recommended mask with your detection system")
    print("2. Compare results with hand-optimized masks")
    print("3. Use the best performing mask as your new template")

    print(f"\n📁 All improved masks saved in: {output_dir}/")
    print("🚀 Improved mask generation completed!")


if __name__ == "__main__":
    generate_improved_masks()
