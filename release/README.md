# KrathongScanner Release v1.0

## 📦 Applications Included

### 1. Scanner_1-0.exe

**Location**: `scanner/Scanner_1-0.exe`
**Purpose**: Main scanning application for detecting ArUco markers and processing templates
**Features**:

- Real-time webcam scanning
- Image file processing
- Template detection and analysis
- Results export and management

### 2. template_management_1-0.exe

**Location**: `backend/template_management_1-0.exe`
**Purpose**: Template creation and database management
**Features**:

- Interactive template creation workflow
- Krathong image import and cropping
- Background removal and mask generation
- ArUco marker assignment and validation
- Database template management
- Template preview and editing

## 🚀 Quick Start

### Option 1: Use the Launcher

1. Double-click `launcher.bat`
2. Choose the application you want to run

### Option 2: Direct Launch

- **Scanner**: Double-click `scanner/Scanner_1-0.exe`
- **Template Management**: Double-click `backend/template_management_1-0.exe`

## 📋 System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space
- **Camera**: USB webcam for scanning (optional)

## 🎯 Workflow

1. **Create Templates** using `template_management_1-0.exe`:

   - Import krathong images
   - Crop and process images
   - Assign unique ArUco marker IDs
   - Save to database

2. **Scan Templates** using `Scanner_1-0.exe`:
   - Load created templates from database
   - Use webcam or image files for scanning
   - Detect and identify templates
   - Export results

## 📁 Directory Structure

```
release/
├── launcher.bat              # Application launcher
├── README.md                 # This file
├── scanner/
│   ├── Scanner_1-0.exe      # Main scanner application
│   └── _internal/           # Required dependencies
└── backend/
    ├── template_management_1-0.exe  # Template creator
    └── _internal/           # Required dependencies
```

## 🔧 Configuration

Both applications will automatically create necessary configuration files and databases in the same directory where they are run.

## 🐛 Troubleshooting

### Common Issues:

1. **Application won't start**: Ensure all files in `_internal/` folders are present
2. **Database errors**: Run as administrator if file permission issues occur
3. **Camera not detected**: Check webcam drivers and permissions

### Support:

- Check log files created in the application directory
- Ensure Windows Defender/antivirus isn't blocking the executables

## 📝 Version Information

- **Version**: 1.0
- **Build Date**: September 2025
- **Branch**: indexing-ids
- **Compatibility**: ArUco 4x4_50 markers (IDs 20-49 available for templates)

## 🎉 Features

### Scanner_1-0 Features:

- ✅ Multi-template detection
- ✅ Real-time webcam processing
- ✅ Batch image processing
- ✅ Results export (JSON, CSV)
- ✅ Template database integration

### template_management_1-0 Features:

- ✅ Interactive image cropping
- ✅ Multiple background removal algorithms
- ✅ Mask generation and preview
- ✅ Available ID suggestions
- ✅ Template conflict detection
- ✅ Database template viewer
- ✅ Real-time preview with adjustments

Enjoy using KrathongScanner! 🎊
