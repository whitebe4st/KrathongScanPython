# Scripts Directory

This directory contains various utility scripts and batch files for KrathongScanner.

## Batch Files (.bat)

### Application Launchers

- **run_KrathongScanner.bat** - Main application launcher
- **run_KrathongScanner_with_data.bat** - Launch with specific data directory
- **run_admin.bat** - Run application with administrator privileges

### Web Server

- **run_web_server.bat** - Start the web server component
- **start_web_server.bat** - Alternative web server launcher
- **start_mall_deployment.bat** - Start for mall deployment scenario

### Template Management

- **run_template_maker.bat** - CLI template maker
- **run_template_maker_gui.bat** - GUI template maker

### Utilities

- **auto_qr_generator.bat** - Automatic QR code generation
- **qr_generator.bat** - Manual QR code generation
- **run_auto_directory.bat** - Auto directory processing

## Python Scripts (.py)

### Development Tools

- **setup_dev.py** - Development environment setup
- **debug_process_image.py** - Image processing debugging
- **test_detector_mask_lookup.py** - Test mask detection
- **check_mask_paths.py** - Verify mask file paths

## Usage

### For Users

Most users should use:

- `run_KrathongScanner.bat` - Standard application launch
- `run_template_maker_gui.bat` - Create custom templates
- `start_web_server.bat` - Web interface

### For Developers

Development and debugging:

- `setup_dev.py` - Set up development environment
- `debug_*.py` - Various debugging utilities
- `test_*.py` - Testing utilities

### For Deployment

Special deployment scenarios:

- `start_mall_deployment.bat` - Mall/kiosk deployment
- `run_admin.bat` - When administrator privileges needed

## Notes

- All batch files should be run from the project root directory
- Ensure Python environment is properly configured before running Python scripts
- Web server scripts may require network configuration
- Template maker scripts need access to the data directory
