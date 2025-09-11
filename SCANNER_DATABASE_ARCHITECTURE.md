# Scanner Database Architecture

## Overview

The KrathongScanner now uses a clean, simplified database architecture where the scanner has its own dedicated database file with fallback to hardcoded templates.

## Architecture Components

### 1. Scanner Database (`scanner.db`)

- **Location**: Project root (`G:\MotionSix\KrathongScanner\scanner.db`)
- **Purpose**: Primary storage for custom templates
- **Managed by**: CRUD interface (`run_template_crud.py`)
- **Used by**: Scanner's ArUco detector

### 2. Hardcoded Templates (Fallback)

- **Templates**: `krathong1`, `krathong2`, `krathong3`, `krathong4`, `krathong5`
- **Marker IDs**: 0-19 (4 markers per template)
- **Purpose**: Ensure scanner always has working templates
- **Location**: Defined in `src/aruco_detector/template_config.py`

### 3. Database Editor (CRUD Interface)

- **Tool**: `run_template_crud.py`
- **Purpose**: Edit scanner's template database
- **Features**: Add, edit, delete, import/export templates
- **Target**: Works directly with `scanner.db`

## How It Works

### Scanner Startup

1. Scanner loads ArUco detector
2. ArUco detector reads templates from `scanner.db`
3. If database has templates → loads them
4. If database is empty/missing → uses hardcoded templates
5. Both custom and hardcoded templates are available

### Template Management

1. Use `run_template_crud.py` to manage templates
2. Add/edit/delete templates in the database
3. Scanner automatically loads templates on next startup
4. Use `reload_custom_templates()` method for live reload

### Template Creation

1. Use `template_maker_gui.py` to create templates
2. Export template packages (template + mask + metadata)
3. Use CRUD interface to import into scanner database
4. Templates become available in scanner

## Template ID Ranges

### Reserved (Hardcoded)

- **IDs 0-19**: Hardcoded templates (krathong1-5)
- **Purpose**: Always available fallback

### Custom Templates

- **IDs 20-49**: Custom templates from database
- **Purpose**: User-created templates
- **Managed by**: CRUD interface

## Files and Components

### Core Files

- `scanner.db` - Primary template database
- `src/aruco_detector/detector.py` - Template loading logic
- `apps/scanner/template_manager.py` - Database operations
- `run_template_crud.py` - Database editor interface

### Template Creation

- `template_maker_gui.py` - Create new templates
- `apps/admin/main.py` - Admin interface for template packages

### Testing

- `test_scanner_db_architecture.py` - Architecture verification

## Usage Examples

### 1. Check Current Templates

```bash
python test_scanner_db_architecture.py
```

### 2. Edit Scanner Database

```bash
python run_template_crud.py
```

### 3. Create New Template

```bash
python template_maker_gui.py
```

### 4. Run Scanner

```bash
python main.py
```

## Benefits

1. **Clean Separation**: Scanner has its own database
2. **Reliable Fallback**: Always has working templates
3. **Simple Management**: CRUD tool directly edits scanner database
4. **No Dependencies**: Scanner doesn't need CRUD system to work
5. **Live Reload**: Templates can be reloaded without restart

## Database Schema

The `scanner.db` uses the following tables:

- `templates` - Template definitions
- `markers` - Marker associations

See `database/models.py` and `database/registry.py` for details.

## Testing Results

✅ **Database Editor**: Successfully manages scanner.db
✅ **Scanner Integration**: Loads templates from database
✅ **Hardcoded Fallback**: Available when database is empty
✅ **Template Reload**: Dynamic template reloading works
✅ **Architecture**: Clean separation of concerns

Current status:

- Custom templates in database: 1 (Test1: markers [20,21,22,23])
- Hardcoded templates: 5 (krathong1-5: markers [0-19])
- Total available: 6 templates with 24 marker mappings
