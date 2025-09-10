"""
Main entry point for Admin application.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.admin.gui import AdminGUI
from utils.config import Config


def main():
    """Main function for Admin application."""
    # Ensure required directories exist
    Config.ensure_directories()

    # Create and run the GUI
    app = AdminGUI()
    app.run()


if __name__ == "__main__":
    main()
