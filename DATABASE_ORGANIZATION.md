# Database Organization

## Overview

The KrathongScanner database has been reorganized for better project structure and maintainability.

## Database Location

**New Location**: `data/db/scanner.db`

### Why This Location?

1. **Organization**: Databases belong in a dedicated directory structure
2. **Clarity**: Easy to find and understand the purpose
3. **Separation**: Keeps the project root clean
4. **Scalability**: Room for future database files (backups, versions, etc.)

## Components Using the Database

### 1. Scanner (ArUco Detector)

- **File**: `src/aruco_detector/detector.py`
- **Path**: `Path(__file__).parent.parent.parent / "data" / "db" / "scanner.db"`
- **Usage**: Loads custom templates with hardcoded fallback

### 2. Template Manager (CRUD System)

- **File**: `apps/scanner/template_manager.py`
- **Path**: `project_root / "data" / "db" / "scanner.db"`
- **Usage**: Creates, reads, updates, deletes templates

### 3. CRUD Interface

- **File**: `run_template_crud.py`
- **Description**: "data/db/scanner.db" template database editor
- **Usage**: GUI for managing scanner templates

## Migration Completed

✅ **Old locations removed:**

- `scanner.db` (project root)
- `data/scanner.db`
- `apps/admin/data/scanner.db`

✅ **New organized location:**

- `data/db/scanner.db`

✅ **All components updated:**

- Scanner detector
- Template manager
- CRUD interface
- Documentation
- Test scripts

## Benefits

1. **Clean Structure**: Database files are properly organized
2. **No Confusion**: Single source of truth for template database
3. **Better Maintenance**: Clear location for backups and management
4. **Professionalism**: Follows standard project organization practices

## Future Enhancements

The new structure allows for:

- Database versioning (`scanner_v1.db`, `scanner_v2.db`)
- Backup files (`scanner_backup.db`)
- Multiple databases for different purposes
- Better deployment and distribution
