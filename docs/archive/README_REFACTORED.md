# KrathongScanner - Refactored Architecture

## Overview

KrathongScanner has been refactored into a clean, modular architecture with three separate applications:

1. **Template Maker** - Create krathong templates with ArUco markers
2. **Admin App** - Manage templates and transfer them to scanner database
3. **Scanner App** - End-user application for processing krathong images

## Project Structure

```
KrathongScanner/
├── apps/                          # Application modules
│   ├── template_maker/            # Template creation app
│   │   ├── __init__.py
│   │   ├── main.py               # Entry point
│   │   ├── gui.py                # GUI interface
│   │   └── export.py             # Export functionality
│   ├── admin/                    # Template management app
│   │   ├── __init__.py
│   │   ├── main.py               # Entry point
│   │   └── gui.py                # Admin interface
│   └── scanner/                  # End-user scanner app
│       ├── __init__.py
│       ├── main.py               # Entry point
│       └── gui.py                # Scanner interface
├── core/                         # Core functionality
│   ├── __init__.py
│   ├── template_maker.py         # Template creation logic
│   ├── krathong_processor.py     # Image processing
│   ├── mask_maker.py             # Mask generation
│   ├── image_cropper.py          # Image cropping
│   └── aruco_utils.py            # ArUco marker utilities
├── database/                     # Database management
│   ├── __init__.py
│   ├── registry.py               # Template registry
│   ├── marker_manager.py         # Marker ID management
│   └── models.py                 # Data models
├── utils/                        # Utility functions
│   ├── __init__.py
│   ├── file_utils.py             # File operations
│   ├── image_utils.py            # Image utilities
│   └── config.py                 # Configuration
├── data/                         # Data directories
│   ├── templates/                # Template maker data
│   ├── scanner_templates/        # Scanner templates
│   ├── exports/                  # Exported packages
│   └── processed/                # Processed images
├── requirements.txt              # Dependencies
├── requirements-dev.txt          # Development dependencies
├── run_template_maker.bat        # Template maker launcher
├── run_admin.bat                 # Admin app launcher
├── run_scanner.bat               # Scanner app launcher
└── README_REFACTORED.md          # This file
```

## Applications

### 1. Template Maker (`apps/template_maker/`)

**Purpose**: Create krathong templates with ArUco markers

**Features**:

- Interactive image cropping
- Automatic mask generation
- Template preview with adjustable parameters
- Marker ID management
- Template package export

**Usage**:

```bash
python apps/template_maker/main.py
# or
run_template_maker.bat
```

**Workflow**:

1. Import krathong image
2. Crop image to desired area
3. Generate mask automatically
4. Preview template with adjustments
5. Export template package

### 2. Admin App (`apps/admin/`)

**Purpose**: Manage templates and transfer them to scanner database

**Features**:

- Browse template packages
- View template information
- Add templates to scanner database
- Manage scanner templates (view, delete, toggle active)
- Template validation

**Usage**:

```bash
python apps/admin/main.py
# or
run_admin.bat
```

**Workflow**:

1. Browse exported template package
2. Review template information
3. Add template to scanner database
4. Manage existing templates

### 3. Scanner App (`apps/scanner/`)

**Purpose**: End-user application for processing krathong images

**Features**:

- Image selection and loading
- Template selection from database
- ArUco marker detection
- Image processing with templates
- Processed image display and saving

**Usage**:

```bash
python apps/scanner/main.py
# or
run_scanner.bat
```

**Workflow**:

1. Select image to process
2. Choose template from database
3. Process image automatically
4. View and save results

## Database Architecture

### Two-Database System

1. **Templates Database** (`data/templates.db`)

   - Used by Template Maker
   - Stores template creation data
   - Manages marker ID assignments

2. **Scanner Database** (`data/scanner.db`)
   - Used by Scanner App
   - Stores active templates for processing
   - Managed by Admin App

### Template Package Export

Template Maker exports complete packages containing:

- Template image (1270x720 with ArUco markers)
- Mask image (779x457 binary mask)
- Individual marker images (for printing)
- Metadata file (JSON with all information)

## Core Modules

### Template Maker (`core/template_maker.py`)

- Creates template images with ArUco markers
- Handles krathong image placement
- Background removal
- Mask generation

### ArUco Utils (`core/aruco_utils.py`)

- Marker generation and detection
- Marker validation
- Marker sheet creation
- ID management

### Krathong Processor (`core/krathong_processor.py`)

- Image processing with templates
- Homography calculation
- Marker detection and matching
- Image enhancement

### Database Registry (`database/registry.py`)

- SQLite database operations
- Template CRUD operations
- Marker ID tracking

## Configuration

All configuration is centralized in `utils/config.py`:

- Template dimensions
- ArUco settings
- Database paths
- Directory structure
- UI settings

## Installation

1. **Install Python dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **For development**:

   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Run applications**:
   - Use the provided `.bat` files on Windows
   - Or run Python scripts directly

## Usage Examples

### Creating a New Template

1. **Start Template Maker**:

   ```bash
   run_template_maker.bat
   ```

2. **Import krathong image** and crop to desired area

3. **Preview template** with adjustments

4. **Export template package** to `data/exports/`

### Adding Template to Scanner

1. **Start Admin App**:

   ```bash
   run_admin.bat
   ```

2. **Browse template package** from exports directory

3. **Review template information**

4. **Add to scanner database**

### Processing Images

1. **Start Scanner App**:

   ```bash
   run_scanner.bat
   ```

2. **Select image** to process

3. **Choose template** from database

4. **Process image** automatically

## Benefits of Refactored Architecture

1. **Separation of Concerns**: Each app has a specific purpose
2. **Modularity**: Core functionality is reusable
3. **Maintainability**: Clean code structure
4. **Scalability**: Easy to add new features
5. **User Experience**: Simplified workflows
6. **Database Management**: Clear data flow
7. **Template Packages**: Complete export/import system

## Migration from Old Structure

The old `template_maker_gui.py` has been refactored into:

- Core functionality → `core/` modules
- GUI → `apps/template_maker/gui.py`
- Database → `database/` modules
- Utilities → `utils/` modules

## Future Enhancements

1. **Web Interface**: Web-based admin panel
2. **Cloud Storage**: Remote template storage
3. **Batch Processing**: Multiple image processing
4. **Advanced Analytics**: Processing statistics
5. **API Integration**: REST API for external access

## Support

For issues or questions:

1. Check the application logs
2. Verify database connections
3. Ensure all dependencies are installed
4. Check file permissions for data directories
