# Tools Directory

This directory contains various utility tools and scripts for KrathongScanner development and usage.

## Directory Structure

### template_makers/

Tools for creating and managing custom templates.

**Files:**

- `enhanced_template_maker.py` - Enhanced template creation with advanced features
- `interactive_template_maker.py` - Interactive template creation interface
- `template_maker_clean.py` - Clean/simple template maker implementation
- `template_maker_gui.py` - GUI-based template maker
- `template_maker_gui_improved.py` - Improved GUI template maker with better UX
- `batch_template_creator.py` - Batch processing for multiple template creation

**Usage:** These tools help create custom krathong templates with masks for the scanner system.

### image_processing/

Image processing and cropping utilities.

**Files:**

- `a4_cropper.py` - A4 paper format cropping
- `image_cropper.py` - General image cropping utility
- `krathong_processor.py` - Krathong-specific image processing
- `generate_improved_mask.py` - Generate improved template masks
- `generate_perfect_mask.py` - Generate optimized template masks
- `mask_maker.py` - Template mask creation utility
- `rectzoom.py` - Rectangle detection and zooming
- `rectzoom_clean.py` - Clean version of rectangle zoom utility

**Usage:** Tools for processing images, creating masks, and handling various image cropping scenarios.

### qr_generation/

QR code generation utilities.

**Files:**

- `auto_qr_generator.py` - Automatic QR code generation
- `generate_qr.py` - Manual QR code generation

**Usage:** Generate QR codes for web server access and template sharing.

### database/

Database management and template registry tools.

**Files:**

- `migrate_templates.py` - Template migration utility
- `template_registry.py` - Template registry management
- `registry_template_gui.py` - GUI for template registry
- `minimal_registry_gui.py` - Simplified registry interface
- `run_template_crud.py` - CRUD operations for templates

**Usage:** Manage template database, migrate templates, and perform CRUD operations.

### webcam/

Webcam-related utilities.

**Files:**

- `run_webcam.py` - Basic webcam interface
- `run_webcam_advanced.py` - Advanced webcam functionality

**Usage:** Webcam capture and processing tools.

## Root Level Tools

**Files:**

- `build_with_bundled.py` - Build script with bundled dependencies
- `run_auto_directory.py` - Automatic directory processing

## Usage Guidelines

### For End Users

Most users should focus on:

- `template_makers/` - Create custom templates
- `qr_generation/` - Generate QR codes for sharing

### For Developers

Development tools:

- `image_processing/` - Image processing utilities
- `database/` - Database management
- `build_with_bundled.py` - Building executable

### For System Integration

- `webcam/` - Webcam integration
- `run_auto_directory.py` - Automated processing

## Installation

Most tools require the same dependencies as the main KrathongScanner application. Ensure your Python environment is properly configured with all required packages.

## Notes

- Run tools from the project root directory for proper path resolution
- Some tools may require specific data directory structure
- GUI tools may have additional dependencies
- Check individual script documentation for specific usage instructions
