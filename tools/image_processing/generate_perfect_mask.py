#!/usr/bin/env python3
"""
Perfect Mask Generator Script.

This script generates mathematically perfect template masks optimized
for the universal cropping system.
"""
import sys

sys.path.insert(0, "src")

from pathlib import Path

from mask_generator import PerfectMaskGenerator


def generate_perfect_masks():
    """Generate perfect masks for the ArUco detection system."""
    print("🎭 Perfect Mask Generator")
    print("=" * 40)

    # Initialize generator
    generator = PerfectMaskGenerator()

    # Output directory
    output_dir = Path("data/markers/templates")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📁 Output directory: {output_dir}")

    # Analyze existing masks first
    print(f"\n🔍 ANALYZING EXISTING MASKS:")
    print("-" * 30)

    existing_masks = [
        "data/markers/templates/krathong1_mask2.png",
        "data/markers/templates/krathong1_mask_final.png",
    ]

    analysis = generator.analyze_current_masks(existing_masks)

    if "error" not in analysis and analysis["masks"]:
        print(f"Found {len(analysis['masks'])} existing masks:")
        for mask_info in analysis["masks"]:
            name = Path(mask_info["path"]).name
            dims = mask_info["dimensions"]
            coverage = mask_info["coverage"]
            print(f"  • {name}: {dims[1]}×{dims[0]} - {coverage:.1f}% coverage")

        print(f"\nAnalysis results:")
        print(f"  Average coverage: {analysis['average_coverage']:.1f}%")
        print(f"  Coverage variation: {analysis['coverage_variation']:.1f}%")
        print(f"  Recommended dimensions: {analysis['recommended_dimensions']}")

    else:
        print("No existing masks found or analysis failed")

    # Generate perfect masks
    print(f"\n🎯 GENERATING PERFECT MASKS:")
    print("-" * 35)

    # Generate masks with different target coverages for comparison
    mask_configs = [
        {
            "name": "krathong_perfect_22.8.png",
            "target_coverage": 22.8,
            "description": "Optimized for current system (22.8% coverage)",
        },
        {
            "name": "krathong_perfect_20.0.png",
            "target_coverage": 20.0,
            "description": "Conservative coverage (20.0%)",
        },
        {
            "name": "krathong_perfect_25.0.png",
            "target_coverage": 25.0,
            "description": "Higher coverage (25.0%)",
        },
    ]

    generated_masks = []

    for config in mask_configs:
        print(f"\n🔄 Generating {config['name']}...")
        print(f"   {config['description']}")

        output_path = output_dir / config["name"]

        try:
            mask = generator.generate_optimized_mask_for_universal_cropping(
                target_coverage=config["target_coverage"], output_path=str(output_path)
            )

            generated_masks.append(
                {
                    "name": config["name"],
                    "path": output_path,
                    "mask": mask,
                    "target_coverage": config["target_coverage"],
                }
            )

            print(f"   ✅ Generated: {output_path}")

        except Exception as e:
            print(f"   ❌ Failed: {e}")

    # Generate comparison image
    if generated_masks:
        print(f"\n📊 CREATING COMPARISON IMAGE:")
        print("-" * 32)

        try:
            import cv2
            import numpy as np

            # Create comparison image showing all generated masks
            mask_height = 200
            mask_width = 300
            masks_per_row = 3

            comparison_height = mask_height * (
                (len(generated_masks) + masks_per_row - 1) // masks_per_row
            )
            comparison_width = mask_width * masks_per_row
            comparison = np.zeros((comparison_height, comparison_width), dtype=np.uint8)

            for i, mask_info in enumerate(generated_masks):
                row = i // masks_per_row
                col = i % masks_per_row

                # Resize mask for comparison
                resized_mask = cv2.resize(mask_info["mask"], (mask_width, mask_height))

                # Position in comparison image
                y_start = row * mask_height
                y_end = y_start + mask_height
                x_start = col * mask_width
                x_end = x_start + mask_width

                comparison[y_start:y_end, x_start:x_end] = resized_mask

                # Add text label
                label = f"{mask_info['target_coverage']:.1f}%"
                cv2.putText(
                    comparison,
                    label,
                    (x_start + 10, y_start + 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    255,
                    2,
                )

            comparison_path = output_dir / "mask_comparison_generated.png"
            cv2.imwrite(str(comparison_path), comparison)
            print(f"✅ Comparison saved: {comparison_path}")

        except Exception as e:
            print(f"❌ Failed to create comparison: {e}")

    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 20)

    if analysis.get("average_coverage"):
        current_avg = analysis["average_coverage"]
        print(f"Current average coverage: {current_avg:.1f}%")

        if current_avg < 20:
            print("✅ Recommend: krathong_perfect_20.0.png (more conservative)")
        elif current_avg > 25:
            print(
                "✅ Recommend: krathong_perfect_25.0.png (matches current high coverage)"
            )
        else:
            print(
                "✅ Recommend: krathong_perfect_22.8.png (optimized for current system)"
            )
    else:
        print(
            "✅ Recommend: krathong_perfect_22.8.png (optimized for universal cropping)"
        )

    print(f"\n🎯 NEXT STEPS:")
    print("-" * 15)
    print("1. Review the generated masks visually")
    print("2. Test the recommended mask with your detection system")
    print("3. Compare results with hand-optimized masks")
    print("4. Replace the current mask if results are better")

    print(f"\n📁 All masks saved in: {output_dir}/")
    print("🚀 Perfect mask generation completed!")


if __name__ == "__main__":
    generate_perfect_masks()
