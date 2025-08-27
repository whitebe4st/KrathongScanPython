#!/usr/bin/env python3
"""
KrathongScanner - Main Application Entry Point

This is the main entry point for the KrathongScanner application.
It coordinates the ArUco detection system and WebSocket API server.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.settings import config
from utils.logger import setup_logger


def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""

    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}, shutting down gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main application function."""
    # Set up logging
    logger = setup_logger()
    logger.info(f"Starting {config.app_name} v{config.app_version}")

    # Set up signal handlers
    setup_signal_handlers()

    try:
        logger.info("Initializing KrathongScanner components...")

        # TODO: Initialize ArUco detector
        # TODO: Initialize WebSocket API server

        logger.info("All components initialized successfully")
        logger.info(
            f"WebSocket server listening on {config.websocket.host}:{config.websocket.port}"
        )

        # Keep the application running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
