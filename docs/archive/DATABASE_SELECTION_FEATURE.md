# Database Selection Feature - CRUD System

## Overview

The KrathongScanner CRUD system now includes robust database selection functionality, allowing users to select and manage different database files for template storage.

## Features

### 🎯 **Automatic Default Connection**

- **Auto-detects**: `data/db/scanner.db` on startup
- **Fallback**: Shows selection dialog if default database not found
- **User-friendly**: No manual configuration required for standard setup

### 🗃️ **Database Selection Dialog**

When the default database is not found, users get three options:

- **Yes**: Select existing database file
- **No**: Create new database file
- **Cancel**: Exit program

### 🔧 **GUI Database Controls**

The CRUD interface now includes:

- **Database Status**: Shows current connected database name
- **Select Database**: Browse and select existing database files
- **Create New**: Create new database files with custom names/locations
- **Real-time Switching**: Change databases without restarting the program

## How It Works

### 1. **Startup Process**

```
1. Check if custom database path provided
2. If not, try default location: data/db/scanner.db
3. If default not found, show selection dialog
4. Connect to selected/created database
5. Launch GUI with database information
```

### 2. **Database Selection**

- **File Browser**: Navigate to any location
- **File Validation**: Ensures selected files are valid SQLite databases
- **Error Handling**: Clear error messages for invalid files
- **Directory Creation**: Auto-creates directories for new databases

### 3. **GUI Integration**

- **Status Display**: Current database name shown in GUI header
- **Control Buttons**: Easy access to database management
- **Template Refresh**: Automatically refreshes template list when database changes
- **Error Recovery**: Graceful handling of database connection issues

## Usage Examples

### **Basic Usage (Default Database)**

```bash
python run_template_crud.py
```

- Automatically connects to `data/db/scanner.db`
- If found: Launches directly with templates loaded
- If not found: Shows database selection dialog

### **Custom Database Path**

```python
from apps.scanner.template_crud_gui import TemplateManagementGUI

# Connect to specific database
app = TemplateManagementGUI(db_path="path/to/custom/scanner.db")
app.run()
```

### **Database Selection in GUI**

1. **Select Existing Database**: Click "Select Database" → Browse → Choose file
2. **Create New Database**: Click "Create New" → Choose location → Enter filename
3. **Switch Databases**: Use controls to change database without restart

## File Structure

```
data/
  db/
    scanner.db          # Default database location
    scanner_backup.db   # Backup databases
    custom_templates.db # Custom database files
    projects/
      project1.db       # Project-specific databases
      project2.db
```

## Benefits

### 🎯 **For Users**

- **No Configuration**: Works out-of-the-box with default setup
- **Flexibility**: Easy switching between different template collections
- **Project Management**: Separate databases for different projects
- **Backup Support**: Easy database backup and restore

### 🔧 **For Developers**

- **Error Resilience**: Robust error handling and recovery
- **User Experience**: Clear feedback and intuitive controls
- **Extensibility**: Easy to add more database management features
- **Testing**: Simple to test with different database configurations

## Error Handling

### **Database Connection Errors**

- **Invalid Files**: Clear error messages for corrupted databases
- **Permission Issues**: Helpful messages for file access problems
- **Missing Directories**: Auto-creation of required directories
- **Recovery Options**: Always provides alternative actions

### **User Experience**

- **Progress Feedback**: Visual confirmation of database operations
- **Cancel Options**: Users can cancel operations safely
- **Persistent State**: Remembers last successful database connection
- **Help Information**: Clear descriptions of each option

## Future Enhancements

### **Planned Features**

- **Recent Databases**: Quick access to recently used databases
- **Database Import/Export**: Transfer templates between databases
- **Database Backup**: Automated backup functionality
- **Multi-Database View**: Compare templates across databases
- **Database Validation**: Check database integrity

### **Configuration Options**

- **Default Path Setting**: User-configurable default database location
- **Auto-Backup**: Automatic database backup on changes
- **Database Encryption**: Optional database encryption support
- **Cloud Sync**: Integration with cloud storage services

## Technical Implementation

### **Database Manager Integration**

- Uses existing `TemplateManager` class
- Maintains compatibility with all CRUD operations
- Supports both default and custom database paths
- Handles database initialization and validation

### **GUI Integration**

- Added database status section to main interface
- Real-time database information display
- Integrated database selection controls
- Automatic template list refresh on database change

### **Error Recovery**

- Fallback mechanisms for database connection failures
- User-friendly error messages with actionable solutions
- Graceful degradation when database operations fail
- Comprehensive logging for troubleshooting

## Conclusion

The database selection feature makes the KrathongScanner CRUD system more robust, user-friendly, and flexible. Users can easily manage multiple template databases, switch between projects, and handle database-related issues with confidence.

The implementation maintains backward compatibility while adding powerful new capabilities for database management and project organization.
