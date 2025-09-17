#!/usr/bin/env python3
"""
Unified Template Creator - Main Entry Point

This application combines template creation and database management
into a single, streamlined workflow that eliminates the complexity
of separate systems.

Author: KrathongScanner Team
Created: 2024
"""

import logging
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.unified_template_creator.gui.unified_template_creator_gui import (
    UnifiedTemplateCreatorGUI,
)


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/unified_template_creator.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    """Main entry point for Unified Template Creator."""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)

        logger.info("🚀 Starting Unified Template Creator...")

        # Create and run the GUI application
        app = UnifiedTemplateCreatorGUI()
        app.run()

        logger.info("✅ Unified Template Creator closed successfully")

    except KeyboardInterrupt:
        print("\n⚠️ Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.exception("Fatal error in main application")
        sys.exit(1)


if __name__ == "__main__":
    main()
