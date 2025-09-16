# Test Outputs Directory

This directory contains test outputs, debug images, and temporary files generated during development and testing of KrathongScanner.

## Directory Structure

### images/

Test images and debug visualizations including:

- Test cropping results
- Debug images showing processing steps
- Notification test images
- Template test images
- QR code images

### json/

Test JSON output files including:

- Processing result metadata
- Template registry test files
- ArUco detection results

### Subdirectories

- `debug_aruco_mask/` - ArUco mask debugging outputs
- `debug_inner_detection/` - Inner detection debugging
- `test_enhanced_output/` - Enhanced processing test outputs

## File Types

### PNG Images

- `test_*.png` - Various test result images
- `debug_*.png` - Debug visualization images
- `enhanced_*.png` - Enhanced processing results
- `mall_*.png` - Mall deployment QR codes
- `qr_*.png` - QR code generation tests

### JSON Files

- `test_*.json` - Test result metadata and configurations

### Text Files

- `test_*.txt` - Test logs and output text

## Usage

This directory is primarily for:

1. **Development** - Debugging image processing pipeline
2. **Testing** - Verifying algorithm improvements
3. **Validation** - Comparing before/after results
4. **Documentation** - Visual examples of processing steps

## Maintenance

- Files in this directory can be safely deleted if disk space is needed
- Automated tests may regenerate some of these files
- Keep representative examples for documentation purposes
- Clean up old test outputs periodically

## Notes

- This directory is typically excluded from production builds
- Test outputs help track development progress
- Images show various stages of the krathong detection and processing pipeline
