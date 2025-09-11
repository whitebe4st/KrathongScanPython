#!/usr/bin/env python3
"""
Scanner Database Editor

This is the CRUD interface for editing the scanner's template database (scanner.db).
The scanner will automatically load templates from this database, with fallback to hardcoded templates.

Architecture:
- scanner.db: Primary template storage for the scanner
- Hardcoded templates: Fallback when database is empty
- This tool: Database editor for scanner.db
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    try:
        from apps.scanner.template_crud_gui import TemplateManagementGUI

        print("🗃️  Starting Scanner Database Editor...")
        print("📊 This tool edits the scanner's template database (scanner.db)")
        print("🎯 The scanner will automatically load templates from this database")
        print("📋 Fallback to hardcoded templates if database is empty")
        print("-" * 60)

        app = TemplateManagementGUI()
        app.run()

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
