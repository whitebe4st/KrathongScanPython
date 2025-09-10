#!/usr/bin/env python3
"""
Template Management Launcher

Launch the template CRUD GUI for managing custom templates.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    try:
        from apps.scanner.template_crud_gui import TemplateManagementGUI

        print("🎯 Starting Template Management System...")
        app = TemplateManagementGUI()
        app.run()

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
