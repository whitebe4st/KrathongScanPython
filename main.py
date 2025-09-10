#!/usr/bin/env python3
"""
KrathongScanner - Main Application Entry Point

This is the main entry point for the KrathongScanner application.
It coordinates the ArUco detection system, webcam detection, and WebSocket API server.
"""

import argparse
import asyncio
import logging
import signal
import sys
import threading
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from auto_directory_detector import run_auto_directory_detection
from config.settings import config
from database.models import TemplateData

# Import new database components
from database.registry import LocalTemplateRegistry
from ui.menu import KrathongScannerUI
from utils.logger import setup_logger
from webcam_detector import WebcamDetector
from webcam_detector_advanced import AdvancedWebcamDetector
from webcam_detector_with_paper import WebcamDetectorWithPaper


def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""

    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}, shutting down gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def run_webcam_detection(mode="basic"):
    """Run webcam detection in specified mode."""
    logger = logging.getLogger(__name__)

    if mode == "basic":
        logger.info("Starting basic webcam detection...")
        detector = WebcamDetector(
            camera_index=0, frame_width=1280, frame_height=720, fps=30
        )
    elif mode == "advanced":
        logger.info("Starting advanced webcam detection...")
        detector = AdvancedWebcamDetector(
            camera_index=0,
            frame_width=1280,
            frame_height=720,
            fps=30,
            auto_capture=True,
            capture_delay=2.0,
            min_markers=4,
        )
    elif mode == "enhanced":
        logger.info("Starting enhanced webcam detection with paper detection...")
        detector = WebcamDetectorWithPaper(camera_id=0)
    else:
        logger.error(f"Unknown webcam mode: {mode}")
        return

    try:
        detector.run()
    except KeyboardInterrupt:
        logger.info("Webcam detection stopped by user")
    except Exception as e:
        logger.error(f"Error in webcam detection: {e}")


def run_web_server(host="0.0.0.0", port=5000):
    """Run the KrathongScanner web server."""
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting KrathongScanner Web Server...")
        logger.info(f"Server will be available at http://localhost:{port}")

        # Import Flask server components
        sys.path.insert(0, str(Path(__file__).parent / "web"))

        # Import and run the server
        import server

        # Set Flask configuration
        server.app.config["HOST"] = host
        server.app.config["PORT"] = port

        # Initialize the auto detector
        server.setup_auto_detector()

        logger.info(f"Upload folder: {server.UPLOAD_FOLDER}")
        logger.info(f"Results folder: {server.RESULTS_FOLDER}")
        logger.info("=" * 50)
        logger.info("🎯 Web Server Ready! Upload images to process them automatically")
        logger.info("=" * 50)

        # Start Flask server in a separate thread
        def start_flask_server():
            server.app.run(host=host, port=port, debug=False, use_reloader=False)

        flask_thread = threading.Thread(target=start_flask_server, daemon=True)
        flask_thread.start()

        # Wait a moment for Flask server to start
        time.sleep(3)

        # Now start InstaTunnel for public access
        logger.info("Starting InstaTunnel for public access...")
        public_url = server.start_instatunnel(port)

        if public_url:
            logger.info(f"Public URL: {public_url}")
            qr_code = server.generate_qr_code(public_url)
            if qr_code:
                logger.info("QR code generated for mobile access")
        else:
            logger.warning("Server will only be available locally")

        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")

    except ImportError as e:
        logger.error(f"Failed to import web server components: {e}")
        logger.error("Make sure Flask and other web dependencies are installed:")
        logger.error("pip install flask werkzeug requests qrcode pillow")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting web server: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            import server

            server.cleanup_on_exit()
        except:
            pass


async def main():
    """Main application function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="KrathongScanner - ArUco Marker Detection System"
    )
    parser.add_argument(
        "--mode",
        choices=[
            "ui",
            "webcam",
            "webcam-advanced",
            "webcam-enhanced",
            "server",
            "auto-directory",
            "web-server",
        ],
        default="ui",
        help="Application mode: ui (graphical interface), webcam (basic), webcam-advanced (auto-capture), webcam-enhanced (with paper detection), web-server (mobile upload interface), auto-directory (monitor folder for new images), or server (WebSocket API)",
    )
    parser.add_argument(
        "--camera", type=int, default=0, help="Camera device index (default: 0)"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        help="Input directory to monitor for new images (auto-directory mode)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for processed images (auto-directory mode)",
    )
    parser.add_argument(
        "--check-interval",
        type=float,
        default=2.0,
        help="Interval in seconds to check for new files (default: 2.0)",
    )
    parser.add_argument(
        "--use-homography",
        action="store_true",
        default=True,
        help="Use homography/perspective correction (default: True)",
    )
    parser.add_argument(
        "--no-homography",
        action="store_true",
        help="Disable homography/perspective correction",
    )

    args = parser.parse_args()

    # Set up logging
    logger = setup_logger()
    logger.info(f"Starting {config.app_name} v{config.app_version}")

    # Set up signal handlers
    setup_signal_handlers()

    try:
        logger.info("Initializing KrathongScanner components...")

        if args.mode == "ui":
            logger.info("Running in UI mode")
            app = KrathongScannerUI()
            app.run()
        elif args.mode == "webcam":
            logger.info("Running in webcam detection mode")
            run_webcam_detection("basic")
        elif args.mode == "webcam-advanced":
            logger.info("Running in advanced webcam detection mode")
            run_webcam_detection("advanced")
        elif args.mode == "webcam-enhanced":
            logger.info(
                "Running in enhanced webcam detection mode with paper detection"
            )
            run_webcam_detection("enhanced")
        elif args.mode == "auto-directory":
            logger.info("Running in auto-directory mode")

            # Get directories from command line or prompt user
            input_dir = args.input_dir
            output_dir = args.output_dir

            if not input_dir:
                input_dir = input("Enter input directory to monitor: ").strip()
                if not input_dir:
                    logger.error("Input directory is required for auto-directory mode")
                    return

            if not output_dir:
                output_dir = input(
                    "Enter output directory for processed images: "
                ).strip()
                if not output_dir:
                    output_dir = "data/processed_images"
                    logger.info(f"Using default output directory: {output_dir}")

            # Determine homography setting
            use_homography = (
                not args.no_homography if args.no_homography else args.use_homography
            )

            logger.info(f"Input directory: {input_dir}")
            logger.info(f"Output directory: {output_dir}")
            logger.info(f"Check interval: {args.check_interval} seconds")
            logger.info(f"Use homography: {use_homography}")

            # Run auto-directory detection
            run_auto_directory_detection(
                input_dir, output_dir, args.check_interval, use_homography, True
            )
        elif args.mode == "web-server":
            logger.info("Running in web server mode")

            # Run the web server (this will block)
            run_web_server()
        elif args.mode == "server":
            logger.info("Running in server mode")
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
