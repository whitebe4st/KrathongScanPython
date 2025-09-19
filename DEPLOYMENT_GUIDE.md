# KrathongScanner Deployment Structure Guide

## 🏗️ **Required Folder Structure for Executables**

Both `Scanner_1-0.exe` and `template_management_1-0.exe` need specific files and directories to function properly.

### 📁 **Scanner_1-0.exe Deployment Structure**

```
release/scanner/
├── Scanner_1-0.exe              # Main scanner executable
├── scanner.db                   # SQLite database (shared with template management)
├── path_utils.py               # Path resolution utilities
├── krathong.ico                # Application icon (optional)
├── _internal/                  # PyInstaller dependencies (auto-generated)
├── data/                       # Data directories (auto-created)
│   ├── webcam_captures/        # Webcam output storage
│   ├── auto_input/             # Auto processing input
│   ├── auto_output/            # Auto processing output
│   ├── templates/              # Template image files
│   └── masks/                  # Mask files
├── config/                     # Configuration files (auto-created)
└── krathong_scanner.log        # Application log file (auto-created)
```

### 📁 **template_management_1-0.exe Deployment Structure**

```
release/backend/
├── template_management_1-0.exe # Template creator executable
├── scanner.db                  # SQLite database (shared with scanner)
├── path_utils.py              # Path resolution utilities
├── krathong.ico               # Application icon (optional)
├── _internal/                 # PyInstaller dependencies (auto-generated)
├── modules/                   # Template creator modules (auto-included)
├── data/                      # Data directories (auto-created)
│   ├── templates/             # Template output storage
│   ├── masks/                 # Generated mask files
│   └── processed_images/      # Processed image cache
├── config/                    # Configuration files (auto-created)
└── krathong_scanner.log       # Application log file (auto-created)
```

## 🔗 **Shared Database (scanner.db)**

**Critical**: Both applications must share the same `scanner.db` file for proper integration.

### Option 1: Shared Database (Recommended)

```
release/
├── scanner.db                  # Shared database file
├── scanner/
│   └── Scanner_1-0.exe        # Links to ../scanner.db
└── backend/
    └── template_management_1-0.exe # Links to ../scanner.db
```

### Option 2: Separate Copies (Manual Sync Required)

```
release/
├── scanner/
│   ├── Scanner_1-0.exe
│   └── scanner.db             # Copy 1
└── backend/
    ├── template_management_1-0.exe
    └── scanner.db             # Copy 2 (must sync manually)
```

## 🚀 **Deployment Steps**

### 1. **Build Applications**

```bash
# Run the build script
python build_applications.py
```

### 2. **Copy Database**

```bash
# Copy existing database to both locations
copy database\scanner.db release\scanner\
copy database\scanner.db release\backend\
```

### 3. **Optional: Create Shared Database Setup**

```batch
# Create shared database launcher
echo Creating shared database structure...
move release\scanner\scanner.db release\
move release\backend\scanner.db release\
```

### 4. **Test Deployment**

- Launch both applications
- Create a template in `template_management_1-0.exe`
- Verify it appears in `Scanner_1-0.exe`

## 🛠️ **Path Resolution**

The applications use intelligent path resolution:

1. **Database Location Priority**:

   - Same directory as executable
   - Parent directory
   - Current working directory
   - Creates new if not found

2. **Auto-Created Directories**:
   - `data/` - All data storage
   - `config/` - Configuration files
   - `data/templates/` - Template files
   - `data/masks/` - Mask files

## 🔧 **Troubleshooting**

### **Database Not Found**

- Ensure `scanner.db` exists in executable directory
- Check application logs for path resolution details
- Verify both apps point to same database file

### **Missing Dependencies**

- Ensure `_internal/` folder is complete
- Include `path_utils.py` in executable directory
- Verify all PyInstaller data files are included

### **Path Issues**

- Run applications from their respective directories
- Avoid spaces in directory names
- Ensure write permissions for data directories

## 📋 **Deployment Checklist**

- [ ] Both executables built successfully
- [ ] `scanner.db` accessible to both applications
- [ ] `path_utils.py` included with both executables
- [ ] `_internal/` directories complete
- [ ] Write permissions for data directories
- [ ] Applications launch without errors
- [ ] Template creation works in backend
- [ ] Scanner detects templates from database
- [ ] Database synchronization verified

## 🎯 **Production Deployment**

For production deployment:

1. **Single Installation Package**:

   ```
   KrathongScanner_v1.0/
   ├── scanner.db
   ├── scanner/
   │   └── Scanner_1-0.exe
   └── backend/
       └── template_management_1-0.exe
   ```

2. **Installation Script** (optional):

   - Copy database to shared location
   - Create desktop shortcuts
   - Set up file associations

3. **User Documentation**:
   - Workflow guide (template creation → scanning)
   - Troubleshooting common issues
   - Path and database management

Both applications are now properly configured for standalone deployment! 🎉
