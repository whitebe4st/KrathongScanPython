"""
Auto-Directory Detector for KrathongScanner.

This module monitors a directory for new krathong images and automatically processes them
using the same pipeline as the Import and Webcam modes.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional, Set

import cv2
import numpy as np

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from aruco_detector import ArUcoDetector


class AutoDirectoryDetector:
    """Monitors a directory for new krathong images and processes them automatically."""

    def __init__(
        self,
        input_directory: str,
        output_directory: str,
        check_interval: float = 2.0,
        use_homography: bool = True,
        use_rectangle_detection: bool = False,
        supported_extensions: tuple = (
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".tiff",
            ".tif",
        ),
    ):
        """
        Initialize the auto-directory detector.

        Args:
            input_directory: Directory to monitor for new images
            output_directory: Directory to save processed images
            check_interval: Time in seconds between directory checks
            use_homography: Whether to use homography/perspective correction (default: True)
            use_rectangle_detection: Whether to use rectangle detection instead of ArUco markers (default: False)
            supported_extensions: Tuple of supported image file extensions
        """
        self.input_directory = Path(input_directory)
        self.output_directory = Path(output_directory)
        self.check_interval = check_interval
        self.use_homography = use_homography
        self.use_rectangle_detection = use_rectangle_detection
        self.supported_extensions = supported_extensions

        # Create directories if they don't exist
        self.input_directory.mkdir(parents=True, exist_ok=True)
        self.output_directory.mkdir(parents=True, exist_ok=True)

        # Initialize detector (only if not using rectangle detection)
        if not self.use_rectangle_detection:
            self.detector = ArUcoDetector()
        else:
            self.detector = None

        # Track processed files to avoid reprocessing
        self.processed_files: Set[str] = set()
        self.processed_files_cache = self.output_directory / ".processed_files.json"

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Load previously processed files on startup
        self._load_processed_files()

        # Statistics
        self.stats = {"files_processed": 0, "files_failed": 0, "start_time": None}

    def get_image_files(self) -> list:
        """Get all image files in the input directory."""
        image_files = []
        for ext in self.supported_extensions:
            image_files.extend(self.input_directory.glob(f"*{ext}"))
            image_files.extend(self.input_directory.glob(f"*{ext.upper()}"))
        return image_files

    def is_new_file(self, file_path: Path) -> bool:
        """Check if a file is new (not processed before)."""
        return str(file_path) not in self.processed_files

    def mark_as_processed(self, file_path: Path):
        """Mark a file as processed."""
        self.processed_files.add(str(file_path))
        self._save_processed_files()

    def _load_processed_files(self):
        """Load previously processed files from cache."""
        try:
            if self.processed_files_cache.exists():
                import json

                with open(self.processed_files_cache, "r", encoding="utf-8") as f:
                    cached_files = json.load(f)
                    # Only keep files that still exist in input directory
                    existing_files = {str(f) for f in self.get_image_files()}
                    self.processed_files = set(cached_files) & existing_files
                    self.logger.info(
                        f"Loaded {len(self.processed_files)} previously processed files from cache"
                    )
        except Exception as e:
            self.logger.warning(f"Could not load processed files cache: {e}")

    def _save_processed_files(self):
        """Save processed files to cache."""
        try:
            import json

            with open(self.processed_files_cache, "w", encoding="utf-8") as f:
                json.dump(list(self.processed_files), f, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not save processed files cache: {e}")

    def cleanup_on_exit(self):
        """Clean up processed files cache when exiting."""
        try:
            # Save final state
            self._save_processed_files()
            self.logger.info("Auto-directory detector cleanup completed")
        except Exception as e:
            self.logger.warning(f"Cleanup error: {e}")

    def get_mask_path(self, template_id: Optional[str] = None) -> Optional[str]:
        """Get the path to the template mask based on detected template."""
        # If using rectangle detection, no mask is needed
        if self.use_rectangle_detection:
            return None

        # If we have a template ID, get the specific mask for that template
        if template_id:
            template_mask_path = self.detector.get_template_mask_path_for_template(
                template_id
            )
            if template_mask_path and Path(template_mask_path).exists():
                return template_mask_path

        # Fallback to detector's automatic template detection
        template_mask_path = self.detector.get_template_mask_path()
        if template_mask_path and Path(template_mask_path).exists():
            return template_mask_path

        # Last resort: look for mask files in the standard location
        mask_paths = [
            "data/markers/templates/krathong1_mask_final.png",
            "data/markers/templates/krathong1_mask.png",
            "data/markers/templates/mask1_final.png",
        ]

        for mask_path in mask_paths:
            if Path(mask_path).exists():
                return mask_path

        self.logger.warning("No template mask found. Tried: " + ", ".join(mask_paths))
        return None

    def find_rectangle_contour(self, image):
        """Find any rectangular contour in the image (from scantest.py)"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Try multiple edge detection approaches
            threshold_pairs = [(50, 150), (75, 200), (30, 100), (100, 250)]

            for low, high in threshold_pairs:
                edged = cv2.Canny(blurred, low, high)

                # Find contours
                contours, _ = cv2.findContours(
                    edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
                )
                contours = sorted(contours, key=cv2.contourArea, reverse=True)

                # Look for rectangular contours
                for contour in contours:
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    # Check if it's a rectangle with reasonable area
                    if len(approx) == 4:
                        area = cv2.contourArea(approx)
                        if area > 5000:  # Minimum area threshold
                            self.logger.info(f"Found rectangle with area: {area}")
                            return approx

            # If no rectangles found with edge detection, try adaptive threshold
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            contours, _ = cv2.findContours(
                adaptive, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            for contour in contours:
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) == 4:
                    area = cv2.contourArea(approx)
                    if area > 5000:
                        self.logger.info(
                            f"Found rectangle (adaptive) with area: {area}"
                        )
                        return approx

            self.logger.warning("No rectangular contours found")
            return None

        except Exception as e:
            self.logger.error(f"Error finding rectangle: {e}")
            return None

    def order_points(self, pts):
        """Order points in the order: top-left, top-right, bottom-right, bottom-left (from scantest.py)"""
        rect = np.zeros((4, 2), dtype="float32")

        # Sum and difference to find corners
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)

        rect[0] = pts[np.argmin(s)]  # top-left
        rect[2] = pts[np.argmax(s)]  # bottom-right
        rect[1] = pts[np.argmin(diff)]  # top-right
        rect[3] = pts[np.argmax(diff)]  # bottom-left

        return rect

    def four_point_transform(self, image, pts):
        """Apply perspective transformation to zoom into the rectangle (from scantest.py)"""
        # Order the points
        rect = self.order_points(pts)
        (tl, tr, br, bl) = rect

        # Calculate the width and height of the new image
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))

        # Define the destination points
        dst = np.array(
            [
                [0, 0],
                [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1],
                [0, maxHeight - 1],
            ],
            dtype="float32",
        )

        # Calculate the perspective transform matrix and apply it
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

        return warped

    def process_with_rectangle_detection(
        self, image_path: Path, output_path: Path
    ) -> bool:
        """Process image using rectangle detection method from scantest.py"""
        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                self.logger.error(f"Could not load image from {image_path}")
                return False

            # Find rectangular contour
            contour = self.find_rectangle_contour(image)
            if contour is None:
                self.logger.warning(f"No rectangle found in {image_path.name}")
                return False

            # Apply perspective transformation to zoom into the rectangle
            pts = contour.reshape(4, 2)
            self.logger.info(f"Rectangle corners: {pts}")

            # Apply perspective transform
            warped = self.four_point_transform(image, pts)

            # Save the processed image
            success = cv2.imwrite(str(output_path), warped)
            if not success:
                self.logger.error(f"Failed to save processed image to {output_path}")
                return False

            # Calculate and log zoom info
            original_area = image.shape[0] * image.shape[1]
            rect_area = cv2.contourArea(contour)
            zoom_factor = original_area / rect_area if rect_area > 0 else 1

            self.logger.info(f"Rectangle processed! Zoom factor: {zoom_factor:.1f}x")

            # Create metadata
            metadata = {
                "input_file": str(image_path),
                "output_file": str(output_path),
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "input_size": {"width": image.shape[1], "height": image.shape[0]},
                "output_size": {"width": warped.shape[1], "height": warped.shape[0]},
                "zoom_factor": float(zoom_factor),
                "processing_mode": "rectangle-detection",
                "detector_version": "1.0",
            }

            # Save metadata
            metadata_path = output_path.with_suffix(".json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            return True

        except Exception as e:
            self.logger.error(f"Error processing {image_path.name}: {e}")
            return False

    def process_image(self, image_path: Path) -> bool:
        """
        Process a single image file using rectangle detection or ArUco markers.

        Args:
            image_path: Path to the image to process

        Returns:
            True if processing was successful, False otherwise
        """
        try:
            self.logger.info(f"Processing new image: {image_path.name}")

            # Generate output filename
            output_filename = f"processed_{image_path.stem}.png"
            output_path = self.output_directory / output_filename

            # Use rectangle detection if enabled
            if self.use_rectangle_detection:
                return self.process_with_rectangle_detection(image_path, output_path)

            # Use ArUco marker detection (original method)
            # Load and process the image (same as import mode)
            image = cv2.imread(str(image_path))
            if image is None:
                self.logger.error(f"Could not load image from {image_path}")
                return False

            # Detect markers (same as import mode)
            markers = self.detector.detect_markers(image)
            if not markers:
                self.logger.error("No markers detected")
                return False

            # Get template info (same as import mode)
            marker_ids = [marker.id for marker in markers]
            template_id = self.detector.detect_template(marker_ids)

            # Get corner markers (same as import mode)
            corner_markers = self.detector.get_corner_markers(markers)
            if corner_markers is None:
                self.logger.error("Could not find corner markers")
                return False

            # Apply cropping based on homography setting (same as import mode)
            if self.use_homography:
                # Apply homography for perspective correction, then crop
                cropped = self.detector._apply_homography_and_crop(
                    image, corner_markers
                )
            else:
                # Use simple cropping
                cropped = self.detector._crop_marker_area(image, corner_markers)

            # Get template mask path (same as import mode)
            template_mask_path = self.detector.get_template_mask_path()

            if template_mask_path:
                # Apply template mask (same as import mode)
                masked = self.detector.apply_template_mask(cropped, template_mask_path)
                processed_image = self.detector._crop_masked_area(masked)
            else:
                self.logger.warning("No template mask available, using cropped image")
                processed_image = cropped

            # Save the processed image
            success = cv2.imwrite(str(output_path), processed_image)

            if success:
                self.logger.info(
                    f"Successfully processed: {image_path.name} -> {output_filename}"
                )
                self.stats["files_processed"] += 1

                # Create a metadata file
                self.create_metadata_file(image_path, output_path)
                return True
            else:
                self.logger.error(f"Failed to save processed image: {output_path}")
                self.stats["files_failed"] += 1
                return False

        except Exception as e:
            self.logger.error(f"Error processing {image_path.name}: {e}")
            self.stats["files_failed"] += 1
            return False

    def create_metadata_file(self, input_path: Path, output_path: Path):
        """Create a metadata file with processing information."""
        try:
            metadata_path = output_path.with_suffix(".json")

            # Get basic image info
            image = cv2.imread(str(input_path))
            height, width = image.shape[:2] if image is not None else (0, 0)

            metadata = {
                "input_file": str(input_path),
                "output_file": str(output_path),
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "input_size": {"width": width, "height": height},
                "processing_mode": "auto-directory",
                "detector_version": "1.0",
            }

            import json

            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

        except Exception as e:
            self.logger.warning(f"Could not create metadata file: {e}")

    def scan_and_process(self):
        """Scan directory once and process any new files."""
        try:
            image_files = self.get_image_files()
            new_files = [f for f in image_files if self.is_new_file(f)]
            total_files = len(image_files)
            processed_count = len(self.processed_files)

            if new_files:
                self.logger.info(f"Found {len(new_files)} new image(s) to process")

                for image_file in new_files:
                    success = self.process_image(image_file)
                    self.mark_as_processed(image_file)

                    if success:
                        self.logger.info(f"✅ Processed: {image_file.name}")
                    else:
                        self.logger.error(f"❌ Failed: {image_file.name}")
            elif total_files > 0:
                # Only log this occasionally to avoid spam
                import time

                if int(time.time()) % 30 == 0:  # Every 30 seconds
                    self.logger.info(
                        f"📁 Directory status: {total_files} total files, {processed_count} already processed, {total_files - processed_count} new files found"
                    )

        except Exception as e:
            self.logger.error(f"Error during directory scan: {e}")

    def print_status(self):
        """Print current status and statistics."""
        elapsed = (
            time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
        )

        total_files = len(self.get_image_files())
        processed_count = len(self.processed_files)

        print(f"\n📊 Auto-Directory Detector Status")
        print(f"=" * 40)
        print(f"📁 Input Directory: {self.input_directory}")
        print(f"📁 Output Directory: {self.output_directory}")
        print(f"⏱️  Running time: {elapsed:.1f} seconds")
        print(f"📄 Total image files: {total_files}")
        print(f"✅ Files processed: {self.stats['files_processed']}")
        print(
            f"💾 Previously processed: {processed_count - self.stats['files_processed']}"
        )
        print(f"❌ Files failed: {self.stats['files_failed']}")
        print(f"🔍 Checking every {self.check_interval} seconds")
        print(f"=" * 40)

    def run(self):
        """
        Start monitoring the directory for new images.

        This will run continuously until interrupted.
        """
        self.logger.info(f"Starting Auto-Directory Detector")
        self.logger.info(f"Input directory: {self.input_directory}")
        self.logger.info(f"Output directory: {self.output_directory}")
        self.logger.info(f"Check interval: {self.check_interval} seconds")

        # Validate directories
        if not self.input_directory.exists():
            raise ValueError(f"Input directory does not exist: {self.input_directory}")

        # Check for mask only if not using rectangle detection
        if not self.use_rectangle_detection and not self.get_mask_path():
            raise ValueError(
                "No template mask found. Please ensure mask files are in data/markers/templates/"
            )

        self.stats["start_time"] = time.time()

        try:
            print(f"\n🚀 Auto-Directory Detector Started")
            print(f"📁 Monitoring: {self.input_directory}")
            print(f"📤 Output to: {self.output_directory}")
            print(f"⏱️  Check interval: {self.check_interval}s")
            print(
                f"\n💡 Drop krathong images into the input folder to process them automatically!"
            )
            print(f"📝 Press Ctrl+C to stop\n")

            # Initial scan to process any existing files
            self.logger.info("Performing initial directory scan...")
            self.scan_and_process()

            # Continuous monitoring loop
            while True:
                time.sleep(self.check_interval)
                self.scan_and_process()

                # Print status every 30 seconds
                if int(time.time()) % 30 == 0:
                    self.print_status()

        except KeyboardInterrupt:
            self.logger.info("Auto-directory monitoring stopped by user")
            self.cleanup_on_exit()
            self.print_status()
            print(f"\n👋 Auto-Directory Detector stopped gracefully")

        except Exception as e:
            self.logger.error(f"Error in auto-directory monitoring: {e}")
            self.cleanup_on_exit()
            raise


def run_auto_directory_detection(
    input_dir: str,
    output_dir: str,
    check_interval: float = 2.0,
    use_homography: bool = True,
    use_rectangle_detection: bool = False,
):
    """
    Convenience function to run auto-directory detection.

    Args:
        input_dir: Directory to monitor for new images
        output_dir: Directory to save processed images
        check_interval: Time in seconds between directory checks
        use_homography: Whether to use homography/perspective correction
        use_rectangle_detection: Whether to use rectangle detection instead of ArUco markers
    """
    detector = AutoDirectoryDetector(
        input_directory=input_dir,
        output_directory=output_dir,
        check_interval=check_interval,
        use_homography=use_homography,
        use_rectangle_detection=use_rectangle_detection,
    )

    detector.run()


if __name__ == "__main__":
    # Example usage for testing
    import argparse

    parser = argparse.ArgumentParser(description="Auto-Directory Krathong Detector")
    parser.add_argument("input_dir", help="Directory to monitor for new images")
    parser.add_argument("output_dir", help="Directory to save processed images")
    parser.add_argument(
        "--interval", type=float, default=2.0, help="Check interval in seconds"
    )

    args = parser.parse_args()

    run_auto_directory_detection(args.input_dir, args.output_dir, args.interval)
