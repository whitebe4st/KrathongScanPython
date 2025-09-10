# ArUco Marker Generator Module

This module provides comprehensive functionality for generating, validating, and exporting ArUco markers.

## Features

- **Marker Generation**: Create individual ArUco markers with customizable parameters
- **Batch Generation**: Generate multiple markers at once with consistent styling
- **Marker Sheets**: Create printable sheets with multiple markers arranged in grids
- **Validation**: Quality checking and detection testing for generated markers
- **Multi-format Export**: Support for PNG, JPEG, BMP, TIFF, SVG, and PDF formats
- **Customization**: Adjustable marker size, border, and styling options

## Components

### 1. ArUcoMarkerGenerator

The main class for generating ArUco markers.

```python
from aruco_generator import ArUcoMarkerGenerator

# Initialize generator
generator = ArUcoMarkerGenerator(
    dict_type="4X4_50",      # ArUco dictionary type
    marker_size=300,          # Marker size in pixels
    border_bits=1,            # Border bits around marker
    output_dir="data/markers" # Output directory
)

# Generate a single marker
marker_img = generator.generate_marker(
    marker_id=0,
    filename="marker_000.png",
    add_border=True
)

# Generate multiple markers
markers = generator.generate_markers_batch(
    marker_ids=[0, 1, 2, 3, 4],
    filename_pattern="marker_{id:03d}.png"
)

# Generate a marker sheet
sheet = generator.generate_marker_sheet(
    marker_ids=[0, 1, 2, 3, 4],
    cols=3,
    filename="marker_sheet.png"
)
```

### 2. MarkerValidator

Validates generated markers for quality and detection reliability.

```python
from aruco_generator import MarkerValidator

# Initialize validator
validator = MarkerValidator(dict_type="4X4_50")

# Validate a marker image
result = validator.validate_marker_image(marker_img, expected_id=0)

# Validate a marker file
result = validator.validate_marker_file("marker_000.png", expected_id=0)

# Batch validate multiple markers
results = validator.batch_validate_markers(marker_files)

# Generate validation report
report = validator.generate_validation_report(results)
print(report)
```

### 3. MarkerExporter

Exports markers in various formats and configurations.

```python
from aruco_generator import MarkerExporter

# Initialize exporter
exporter = MarkerExporter(output_dir="data/markers")

# Export in different formats
exporter.export_marker(marker_img, "marker_000", format="png")
exporter.export_marker(marker_img, "marker_000", format="jpg", quality=95)
exporter.export_marker(marker_img, "marker_000", format="svg")

# Export marker sheet
exporter.export_marker_sheet(
    marker_images,
    filename="marker_sheet",
    format="png",
    cols=5,
    add_labels=True
)

# Export marker catalog
exporter.export_marker_catalog(
    marker_images,
    filename="marker_catalog",
    format="pdf"
)
```

## Supported ArUco Dictionaries

- **4X4**: 4x4 bit markers (50, 100, 250, 1000 variants)
- **5X5**: 5x5 bit markers (50, 100, 250, 1000 variants)
- **6X6**: 6x6 bit markers (50, 100, 250, 1000 variants)
- **7X7**: 7x7 bit markers (50, 100, 250, 1000 variants)

## Output Formats

- **PNG**: Lossless compression, best for quality
- **JPEG**: Lossy compression, smaller file sizes
- **BMP**: Uncompressed, large file sizes
- **TIFF**: High quality with compression options
- **SVG**: Vector format, scalable
- **PDF**: Document format, good for printing

## Directory Structure

```
data/markers/
├── generated/     # Newly generated markers
├── templates/     # Template markers
└── custom/        # Custom marker designs
```

## Example Usage

See `examples/generate_markers.py` for a complete demonstration of all features.

## Configuration

The module uses the same configuration system as the main project. Key settings:

- `ARUCO_DICT_TYPE`: Default dictionary type
- `MARKER_SIZE`: Default marker size in pixels
- `BORDER_BITS`: Default border bits

## Dependencies

- OpenCV (cv2) for ArUco functionality
- NumPy for image processing
- PIL (Pillow) for advanced image format support

## Error Handling

All methods include comprehensive error handling and logging. Check the logs for detailed information about any issues during generation, validation, or export.

## Performance Notes

- **Generation**: Very fast, suitable for real-time applications
- **Validation**: Moderate speed, depends on image size and complexity
- **Export**: Varies by format, PNG/JPEG are fastest, SVG/PDF are slower

## Best Practices

1. **Use appropriate dictionary size**: 4X4 for simple applications, 6X6+ for complex scenarios
2. **Validate markers**: Always validate generated markers before use
3. **Choose export format**: PNG for quality, JPEG for size, SVG for scalability
4. **Monitor output directory**: Ensure sufficient disk space for generated markers
5. **Test detection**: Verify markers work with your detection system
