#!/usr/bin/env python3
"""
Example script demonstrating ArUco marker generation.

This script shows how to use the ArUcoMarkerGenerator class
to create and export ArUco markers.
"""

import sys
from pathlib import Path

import cv2

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aruco_generator import ArUcoMarkerGenerator, MarkerExporter, MarkerValidator


def main():
    """Main function demonstrating marker generation."""
    print("🎯 ArUco Marker Generator Example")
    print("=" * 50)

    # Initialize the generator
    generator = ArUcoMarkerGenerator(
        dict_type="4X4_50",
        marker_size=300,
        border_bits=1,
        output_dir="data/markers/generated",
    )

    # Get dictionary information
    dict_info = generator.get_dictionary_info()
    print(f"📚 Dictionary: {dict_info['dict_type']}")
    print(f"🔢 Total markers available: {dict_info['total_markers']}")
    print(f"📏 Marker size: {dict_info['marker_size']} pixels")
    print()

    # Generate individual markers
    print("🖼️  Generating individual markers...")
    marker_ids = [0, 1, 2, 3, 4]

    for marker_id in marker_ids:
        try:
            marker_img = generator.generate_marker(
                marker_id=marker_id,
                filename=f"marker_{marker_id:03d}.png",
                add_border=True,
            )
            print(f"  ✓ Generated marker ID {marker_id}")
        except Exception as e:
            print(f"  ✗ Failed to generate marker ID {marker_id}: {e}")

    print()

    # Generate batch markers
    print("📦 Generating batch markers...")
    try:
        batch_markers = generator.generate_markers_batch(
            marker_ids=[5, 6, 7, 8, 9], filename_pattern="batch_marker_{id:03d}.png"
        )
        print(f"  ✓ Generated {len(batch_markers)} markers in batch")
    except Exception as e:
        print(f"  ✗ Batch generation failed: {e}")

    print()

    # Generate marker sheet
    print("📄 Generating marker sheet...")
    try:
        sheet = generator.generate_marker_sheet(
            marker_ids=[10, 11, 12, 13, 14],
            cols=3,
            filename="marker_sheet_3x2.png",
            spacing=30,
        )
        print("  ✓ Generated marker sheet")
    except Exception as e:
        print(f"  ✗ Sheet generation failed: {e}")

    print()

    # Validate generated markers
    print("🔍 Validating generated markers...")
    validator = MarkerValidator(dict_type="4X4_50")

    # Get list of generated marker files
    output_dir = Path("data/markers/generated")
    marker_files = list(output_dir.glob("*.png"))

    if marker_files:
        # Validate each marker
        validation_results = {}
        for marker_file in marker_files[:5]:  # Validate first 5 markers
            result = validator.validate_marker_file(str(marker_file))
            validation_results[marker_file.name] = result

        # Generate validation report
        report = validator.generate_validation_report(validation_results)
        print(report)
    else:
        print("  No marker files found for validation")

    print()

    # Export markers in different formats
    print("📤 Exporting markers in different formats...")
    exporter = MarkerExporter(output_dir="data/markers/generated")

    # Get export information
    export_info = exporter.get_export_info()
    print(f"  Supported formats: {', '.join(export_info['supported_formats'])}")

    # Export a marker in multiple formats
    if marker_files:
        sample_marker = cv2.imread(str(marker_files[0]))

        formats_to_test = ["png", "jpg", "bmp", "tiff"]
        for fmt in formats_to_test:
            try:
                success = exporter.export_marker(
                    sample_marker, f"sample_marker.{fmt}", format=fmt
                )
                if success:
                    print(f"  ✓ Exported sample marker as {fmt.upper()}")
                else:
                    print(f"  ✗ Failed to export as {fmt.upper()}")
            except Exception as e:
                print(f"  ✗ Export to {fmt.upper()} failed: {e}")

    print()
    print("🎉 Marker generation example completed!")
    print(f"📁 Check the 'data/markers/generated' folder for your markers!")


if __name__ == "__main__":
    main()
