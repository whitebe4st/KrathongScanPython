"""
Launcher for Unified Template Creator

Simple launcher script that handles path setup and starts the application.
Use this script to run the unified template creator.

Usage:
    python launch.py

Author: KrathongScanner Team
"""

import os
import sys
from pathlib import Path


def setup_paths():
    """Set up Python paths for module imports."""
    # Get the directory containing this script
    script_dir = Path(__file__).parent.absolute()

    # Add current directory and modules directory to Python path
    sys.path.insert(0, str(script_dir))
    sys.path.insert(0, str(script_dir / "modules"))

    # Add parent directories for core imports
    parent_dir = script_dir.parent.parent
    sys.path.insert(0, str(parent_dir / "core"))
    sys.path.insert(0, str(parent_dir))

    print(f"Script directory: {script_dir}")
    print(f"Python path setup complete")


def main():
    """Main launcher function."""
    print("=" * 60)
    print("🎯 Unified Template Creator")
    print("🔧 Modular template creation system")
    print("📁 Extracted from template_maker_gui.py (3537 lines)")
    print("=" * 60)

    try:
        # Setup paths first
        setup_paths()

        # Import and run the application
        from unified_template_creator import UnifiedTemplateCreator

        print("✅ Starting Unified Template Creator...")
        app = UnifiedTemplateCreator()
        app.run()

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📝 Make sure all required modules are available")
        return 1
    except Exception as e:
        print(f"❌ Application error: {e}")
        return 1

    print("👋 Application closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
