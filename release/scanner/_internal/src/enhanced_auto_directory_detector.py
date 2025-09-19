"""
Enhanced Auto-Directory Detector for KrathongScanner.

This module monitors a directory for new krathong images and automatically processes them
using the enhanced pipeline: detect paper -> detect aruco -> apply mask

Based on the robust document scanning approach from scantest.py.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Optional, Set

import cv2

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from aruco_detector import ArUcoDetector
from enhanced_document_scanner import EnhancedDocumentScanner


class EnhancedAutoDirectoryDetector:
    """Enhanced auto-directory detector with robust document scanning pipeline."""

    def __init__(
        self,
        input_directory: str,
        output_directory: str,
        check_interval: float = 2.0,
        use_document_detection: bool = True,
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
        Initialize the enhanced auto-directory detector.

        Args:
            input_directory: Directory to monitor for new images
            output_directory: Directory to save processed images
            check_interval: Time in seconds between directory checks
            use_document_detection: Whether to use document detection first (default: True)
            supported_extensions: Tuple of supported image file extensions
        """
        self.input_directory = Path(input_directory)
        self.output_directory = Path(output_directory)
        self.check_interval = check_interval
        self.use_document_detection = use_document_detection
        self.supported_extensions = supported_extensions

        # Create directories if they don't exist
        self.input_directory.mkdir(parents=True, exist_ok=True)
        self.output_directory.mkdir(parents=True, exist_ok=True)

        # Initialize detectors
        self.detector = ArUcoDetector()
        self.document_scanner = EnhancedDocumentScanner()

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
                    self.processed_files = set(cached_files)
                    self.logger.info(
                        f"Loaded {len(self.processed_files)} previously processed files"
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

    def get_template_mask_path(self, template_id: str) -> Optional[str]:
        """Get the mask path for a template ID (expects mask1-4_final.png)."""
        try:
            # Extract numeric suffix from template id like 'krathong2' -> '2'
            import re

            match = re.search(r"(\d+)$", template_id)
            num = match.group(1) if match else None

            candidates = []
            if num:
                candidates.extend(
                    [
                        f"data/markers/templates/mask{num}_final.png",
                        f"data/markers/templates/mask{num}.png",
                        f"data/templates/mask{num}_final.png",
                        f"data/templates/mask{num}.png",
                    ]
                )

            # Fallbacks using full id just in case
            candidates.extend(
                [
                    f"data/markers/templates/{template_id}_mask.png",
                    f"data/templates/{template_id}_mask.png",
                ]
            )

            for path in candidates:
                if Path(path).exists():
                    return path

            self.logger.warning(
                "No template mask found. Tried: " + ", ".join(candidates)
            )
            return None
        except Exception:
            return None

    def process_image(self, image_path: Path) -> bool:
        """
        Process a single image file using the enhanced pipeline:
        detect paper -> detect aruco -> apply mask

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

            # Load the image
            image = cv2.imread(str(image_path))
            if image is None:
                self.logger.error(f"Could not load image from {image_path}")
                return False

            # Step 1: Document Detection (if enabled)
            if self.use_document_detection:
                self.logger.info("Step 1: Detecting document boundaries...")
                processed_image, doc_success = self.document_scanner.process_image(
                    image
                )

                if doc_success:
                    self.logger.info("✓ Document detected and perspective corrected")
                    # Use the document-corrected image for ArUco detection
                    image_for_aruco = processed_image
                else:
                    self.logger.warning(
                        "⚠ Document detection failed, using original image"
                    )
                    image_for_aruco = image
            else:
                self.logger.info("Step 1: Skipping document detection (disabled)")
                image_for_aruco = image

            # Step 2: ArUco Detection
            self.logger.info("Step 2: Detecting ArUco markers...")
            markers = self.detector.detect_markers(image_for_aruco)
            if not markers:
                self.logger.error("❌ No ArUco markers detected")
                return False

            self.logger.info(f"✓ Found {len(markers)} ArUco markers")

            # Get template info
            marker_ids = [marker.id for marker in markers]
            template_id = self.detector.detect_template(marker_ids)

            # Get corner markers
            corner_markers = self.detector.get_corner_markers(markers)
            if corner_markers is None:
                self.logger.error("❌ Could not find corner markers")
                return False

            self.logger.info("✓ Corner markers found")

            # Step 3: Apply cropping based on ArUco markers
            self.logger.info("Step 3: Applying ArUco-based cropping...")
            if self.use_document_detection and doc_success:
                # If we already have document-corrected image, use simple cropping
                cropped = self.detector._crop_marker_area(
                    image_for_aruco, corner_markers
                )
            else:
                # Use homography for perspective correction, then crop
                cropped = self.detector._apply_homography_and_crop(
                    image_for_aruco, corner_markers
                )

            self.logger.info("✓ ArUco-based cropping applied")

            # Step 4: Apply template mask
            self.logger.info("Step 4: Applying template mask...")
            # Prefer detector's built-in resolution if available
            try:
                template_mask_path = self.detector.get_template_mask_path()
            except Exception:
                template_mask_path = self.get_template_mask_path(template_id)

            if template_mask_path:
                # Apply template mask
                masked = self.detector.apply_template_mask(cropped, template_mask_path)
                processed_image = self.detector._crop_masked_area(masked)
                self.logger.info("✓ Template mask applied")
            else:
                self.logger.warning("⚠ No template mask available, using cropped image")
                processed_image = cropped

            # Save the processed image
            success = cv2.imwrite(str(output_path), processed_image)

            if success:
                self.logger.info(
                    f"✅ Successfully processed: {image_path.name} -> {output_filename}"
                )
                self.logger.info(
                    f"   Final size: {processed_image.shape[1]}x{processed_image.shape[0]}"
                )
                self.stats["files_processed"] += 1

                # Create a metadata file
                self.create_metadata_file(
                    image_path, output_path, template_id, doc_success
                )
                return True
            else:
                self.logger.error(f"❌ Failed to save processed image: {output_path}")
                self.stats["files_failed"] += 1
                return False

        except Exception as e:
            self.logger.error(f"❌ Error processing {image_path.name}: {e}")
            self.stats["files_failed"] += 1
            return False

    def create_metadata_file(
        self,
        input_path: Path,
        output_path: Path,
        template_id: str,
        doc_detection_used: bool,
    ):
        """Create a metadata file with processing information."""
        try:
            metadata_path = output_path.with_suffix(".json")

            # Get basic image info
            image = cv2.imread(str(input_path))
            height, width = image.shape[:2] if image is not None else (0, 0)

            # Get processed image info
            processed_image = cv2.imread(str(output_path))
            proc_height, proc_width = (
                processed_image.shape[:2] if processed_image is not None else (0, 0)
            )

            metadata = {
                "input_file": str(input_path),
                "output_file": str(output_path),
                "template_id": template_id,
                "processing_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "original_size": {"width": width, "height": height},
                "processed_size": {"width": proc_width, "height": proc_height},
                "document_detection_used": doc_detection_used,
                "pipeline": "enhanced_auto_directory",
                "processing_steps": [
                    "document_detection"
                    if doc_detection_used
                    else "skip_document_detection",
                    "aruco_detection",
                    "aruco_cropping",
                    "template_masking",
                ],
            }

            import json

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

        except Exception as e:
            self.logger.warning(f"Could not create metadata file: {e}")

    def run(self):
        """Run the auto-directory detector continuously."""
        self.logger.info(f"Starting enhanced auto-directory detector...")
        self.logger.info(f"Monitoring: {self.input_directory}")
        self.logger.info(f"Output: {self.output_directory}")
        self.logger.info(
            f"Document detection: {'enabled' if self.use_document_detection else 'disabled'}"
        )
        self.logger.info(f"Check interval: {self.check_interval}s")
        self.logger.info("Press Ctrl+C to stop")

        self.stats["start_time"] = time.time()

        try:
            while True:
                # Get all image files
                image_files = self.get_image_files()

                # Process new files
                new_files = [f for f in image_files if self.is_new_file(f)]

                if new_files:
                    self.logger.info(f"Found {len(new_files)} new image(s) to process")

                    for image_file in new_files:
                        self.logger.info(f"Processing: {image_file.name}")
                        success = self.process_image(image_file)

                        if success:
                            self.mark_as_processed(image_file)
                            self.logger.info(f"✅ Completed: {image_file.name}")
                        else:
                            self.logger.error(f"❌ Failed: {image_file.name}")

                # Wait before next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Stopping auto-directory detector...")
            self._print_stats()

    # Compatibility with legacy server monitor loop
    def scan_and_process(self):
        """Scan the input directory once and process any new files (compat layer)."""
        image_files = self.get_image_files()
        new_files = [f for f in image_files if self.is_new_file(f)]
        for image_file in new_files:
            try:
                success = self.process_image(image_file)
                if success:
                    self.mark_as_processed(image_file)
            except Exception as e:
                self.logger.error(f"Error processing {image_file.name}: {e}")

    def _print_stats(self):
        """Print processing statistics."""
        if self.stats["start_time"]:
            runtime = time.time() - self.stats["start_time"]
            self.logger.info(f"Runtime: {runtime:.1f} seconds")

        self.logger.info(f"Files processed: {self.stats['files_processed']}")
        self.logger.info(f"Files failed: {self.stats['files_failed']}")

        if self.stats["files_processed"] > 0:
            success_rate = (
                self.stats["files_processed"]
                / (self.stats["files_processed"] + self.stats["files_failed"])
            ) * 100
            self.logger.info(f"Success rate: {success_rate:.1f}%")

    def process_single_file(self, file_path: str) -> bool:
        """Process a single file (for testing)."""
        return self.process_image(Path(file_path))
