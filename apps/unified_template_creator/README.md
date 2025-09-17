# 🎯 Unified Template Creator

The **Unified Template Creator** is a streamlined application that combines template creation and database management into a single, intuitive workflow. No more switching between separate tools!

## ✨ Key Features

- **🖼️ Interactive Template Creation**: Load images, crop regions, generate masks
- **💾 Integrated Database Storage**: Save directly to scanner.db (no manual import needed)
- **📁 File Export**: Export template packages for distribution/backup
- **🎯 Smart Marker Management**: Auto-assign ArUco marker IDs with conflict detection
- **👁️ Real-time Preview**: See your template before saving
- **🔄 Simple Workflow**: One application, one process, one click to complete

## 🚀 Quick Start

### Method 1: Batch Script (Recommended)

```bash
# Navigate to project root
cd G:\MotionSix\KrathongScanner

# Run the launcher
scripts\run_unified_template_creator.bat
```

### Method 2: Direct Python

```bash
# Navigate to project root
cd G:\MotionSix\KrathongScanner

# Run directly
python apps\unified_template_creator\main.py
```

## 📋 Workflow Overview

1. **Load Image** 📂

   - Click "Load Image" to select your template image
   - Supports PNG, JPG, JPEG, BMP, TIFF formats

2. **Define Template Area** ✂️

   - Click "Start Cropping" to enable selection mode
   - Click and drag on the image to select the template region
   - This defines where the krathong will be placed

3. **Generate Mask** 🎭

   - Click "Generate Mask" to create the template mask
   - Mask defines the exact shape for krathong detection

4. **Configure Template** ⚙️

   - Enter a unique template name
   - Choose auto-assign markers (recommended) or manually set marker IDs
   - Adjust template dimensions if needed

5. **Preview & Create** 🎯
   - Click "Preview Template" to see the final result
   - Click "Create Template" to save to database + export files
   - ✅ Done! Template is ready for scanner use

## 🎯 Marker Management

- **Auto-Assignment**: System automatically assigns available marker IDs (20-49)
- **Conflict Detection**: Prevents duplicate marker assignments
- **Real-time Availability**: Shows remaining marker slots
- **Manual Override**: Option to manually specify marker IDs if needed

## 💾 Output Options

### Database Storage (Primary)

- **Target**: `data/db/scanner.db`
- **Purpose**: Templates immediately available to scanner
- **Automatic**: Mask files copied to correct scanner locations

### File Export (Secondary)

- **Target**: `output/` directory
- **Contents**:
  - Template image with markers
  - Individual marker files
  - Mask file
  - Metadata JSON
- **Purpose**: Distribution, backup, or manual deployment

## 🔧 Configuration

### Template Dimensions

- **Default**: 1270x720 pixels (HD ready)
- **Customizable**: Adjust width/height as needed
- **Scanner Compatible**: Dimensions optimized for detection performance

### Export Settings

- **Save to Database**: ✅ Enabled by default (recommended)
- **Export Files**: ✅ Enabled by default (creates backup)
- **Flexible**: Can disable either option if not needed

## 🚨 Troubleshooting

### Database Connection Issues

- **Symptom**: "❌ Database error" in status panel
- **Solution**: Ensure `data/db/scanner.db` exists and is writable
- **Check**: Database permissions and disk space

### Marker Availability

- **Symptom**: "⚠️ No markers available"
- **Explanation**: All marker IDs (20-49) are already assigned
- **Solution**: Delete unused templates or use manual assignment

### Import Errors

- **Symptom**: Import resolution errors
- **Solution**: Ensure you're running from project root directory
- **Check**: Python path includes project root

### Image Loading Issues

- **Symptom**: "Could not load image"
- **Solution**:
  - Ensure file format is supported (PNG, JPG, JPEG, BMP, TIFF)
  - Check file permissions and corruption
  - Try converting to PNG format

## 🎨 UI Guide

### Left Panel: Template Creation

- **Image Preview**: Large canvas showing your template image
- **Cropping Tools**: Interactive selection and mask generation
- **Scrollable View**: Handle large images with scroll bars

### Right Panel: Configuration

- **Template Name**: Unique identifier for your template
- **Marker Settings**: Auto or manual marker ID assignment
- **Dimensions**: Template size configuration
- **Export Options**: Database and file export settings
- **Action Buttons**: Create, preview, manage, reset

### Bottom Panel: Status

- **Status Messages**: Real-time feedback on operations
- **Progress Bar**: Shows creation progress
- **Database Status**: Connection and template count

## 🔗 Integration

### Scanner Integration

- Templates saved to database are **immediately available** to scanner
- No manual import or configuration required
- Mask files automatically copied to scanner's expected locations

### Template Management

- **View Templates**: Click "Manage Templates" to see existing templates
- **Update Templates**: Create new version with same name (overwrites)
- **Delete Templates**: Use template management interface

### File System

```
data/
├── db/
│   └── scanner.db          # Database storage
├── markers/
│   └── templates/          # Scanner mask files
└── exports/                # File export location
    └── [template_name]/
        ├── template.png
        ├── mask.png
        ├── markers/
        └── metadata.json
```

## 🎯 Best Practices

1. **Template Naming**: Use descriptive, unique names
2. **Image Quality**: Use high-resolution, clear images
3. **Crop Precision**: Select tight, accurate template regions
4. **Marker Conservation**: Use auto-assignment to prevent conflicts
5. **Regular Backups**: Export files for backup/distribution
6. **Test Templates**: Preview before finalizing

## 🔄 Comparison with Previous Workflow

### ❌ Old Workflow (Complex)

1. Open Template Maker GUI
2. Create template and export files
3. Close Template Maker GUI
4. Open Template CRUD GUI
5. Import files to database
6. Close Template CRUD GUI

### ✅ New Workflow (Unified)

1. Open Unified Template Creator
2. Create template + auto-save to database
3. ✅ Done!

**Result**:

- 🚀 **3x faster** template creation
- 🎯 **Zero manual imports** required
- 🧠 **No "airplane control"** complexity
- ✅ **Single workflow** for all operations

---

_The Unified Template Creator eliminates the complexity of managing separate template creation and database systems, providing a streamlined experience that gets you from image to scanner-ready template in just a few clicks._
