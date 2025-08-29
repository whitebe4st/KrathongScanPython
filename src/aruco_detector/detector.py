"""
ArUco Marker Detection System.

This module provides comprehensive ArUco marker detection with:
- Marker detection and pose estimation
- Perspective correction using homography
- Template masking for drawing extraction
- Metadata generation
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from .template_config import (
    MARKER_TO_TEMPLATE,
    TEMPLATE_MARKER_SETS,
    detect_template_from_markers,
    detect_template_partial,
    get_template_config,
)


@dataclass
class MarkerData:
    """Data structure for detected marker information."""

    id: int
    corners: np.ndarray
    center: Tuple[float, float]
    pose: Optional[np.ndarray] = None


@dataclass
class MarkerPose:
    """Data structure for marker pose information."""

    rotation_matrix: np.ndarray
    translation_vector: np.ndarray
    euler_angles: Tuple[float, float, float]


class ArUcoDetector:
    """
    Comprehensive ArUco marker detection system.

    Handles marker detection, perspective correction, and template masking
    for drawing extraction from scanned images.
    """

    def __init__(
        self,
        dict_type: str = "4X4_50",
        marker_size: float = 0.04,
        camera_matrix: Optional[np.ndarray] = None,
        dist_coeffs: Optional[np.ndarray] = None,
    ):
        """
        Initialize the ArUco detector.

        Args:
            dict_type: ArUco dictionary type
            marker_size: Physical size of markers in meters
            camera_matrix: Camera intrinsic matrix (if available)
            dist_coeffs: Camera distortion coefficients (if available)
        """
        self.logger = self._setup_logger()
        self.dict_type = dict_type
        self.marker_size = marker_size

        # Initialize ArUco dictionary and detector
        self.aruco_dict = self._get_aruco_dict()
        self.detector = self._setup_detector()

        # Camera parameters (optional, for pose estimation)
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs

        # Template detection and configuration
        self.template_configs = TEMPLATE_MARKER_SETS
        self.marker_to_template = MARKER_TO_TEMPLATE
        self.current_template = None
        self.current_template_config = None

        # Expected corner marker IDs (for perspective correction)
        self.corner_marker_ids = [
            0,
            1,
            2,
            3,
        ]  # Top-left, top-right, bottom-left, bottom-right

        self.logger.info(f"ArUco Detector initialized with {dict_type} dictionary")

    def detect_template(
        self, marker_ids: List[int], use_partial: bool = False
    ) -> Optional[str]:
        """
        Detect which template is being used based on detected marker IDs.

        Args:
            marker_ids: List of detected ArUco marker IDs
            use_partial: Whether to use partial detection for display purposes

        Returns:
            Template ID string or None if no match found
        """
        template_id = detect_template_from_markers(marker_ids)

        # If no strict template detected and partial detection is enabled, try partial
        if not template_id and use_partial and len(marker_ids) >= 3:
            template_id = detect_template_partial(marker_ids, min_markers=3)

        if template_id:
            self.current_template = template_id
            self.current_template_config = get_template_config(template_id)
            self.logger.info(
                f"Detected template: {template_id} - {self.current_template_config['name']}"
            )
        else:
            self.logger.warning(f"No template detected for markers: {marker_ids}")
            self.current_template = None
            self.current_template_config = None

        return template_id

    def get_template_corner_markers(self) -> List[int]:
        """
        Get the corner marker IDs for the current template.

        Returns:
            List of corner marker IDs for the current template, or default if no template detected
        """
        if self.current_template_config:
            return self.current_template_config["markers"]
        else:
            return self.corner_marker_ids

    def get_template_mask_path(self) -> Optional[str]:
        """
        Get the mask file path for the current template.

        Returns:
            Path to the template mask file, or None if no template detected
        """
        if self.current_template_config:
            mask_filename = self.current_template_config["mask_file"]
            # Look for mask in the templates directory
            mask_path = Path("data/markers/templates") / mask_filename

            # Try different naming conventions
            if not mask_path.exists():
                # Try with "mask" prefix and "final" suffix
                alt_filename = f"mask{self.current_template[-1]}_final.png"
                mask_path = Path("data/markers/templates") / alt_filename

            if mask_path.exists():
                self.logger.info(f"Using template mask: {mask_path}")
                return str(mask_path)
            else:
                self.logger.warning(f"Template mask not found: {mask_path}")
                return None
        else:
            # Fallback to default mask
            default_mask = Path("data/markers/templates/mask1_final.png")
            if default_mask.exists():
                self.logger.info(f"Using default mask: {default_mask}")
                return str(default_mask)
            else:
                self.logger.error(
                    "No template mask found and no default mask available"
                )
                return None

    def _setup_logger(self):
        """Setup logger for the detector."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _get_aruco_dict(self) -> cv2.aruco.Dictionary:
        """Get the ArUco dictionary."""
        dict_mapping = {
            "4X4_50": cv2.aruco.DICT_4X4_50,
            "4X4_100": cv2.aruco.DICT_4X4_100,
            "5X5_50": cv2.aruco.DICT_5X5_50,
            "6X6_50": cv2.aruco.DICT_6X6_50,
        }

        if self.dict_type not in dict_mapping:
            self.logger.warning(
                f"Unknown dictionary type: {self.dict_type}. Using 4X4_50"
            )
            self.dict_type = "4X4_50"

        return cv2.aruco.getPredefinedDictionary(dict_mapping[self.dict_type])

    def _setup_detector(self) -> cv2.aruco.ArucoDetector:
        """Setup the ArUco detector with optimized parameters."""
        detector_params = cv2.aruco.DetectorParameters()

        # More sensitive parameters for webcam detection
        detector_params.adaptiveThreshWinSizeMin = 3
        detector_params.adaptiveThreshWinSizeMax = 23
        detector_params.adaptiveThreshWinSizeStep = 10
        detector_params.adaptiveThreshConstant = 7
        detector_params.minMarkerPerimeterRate = 0.02  # More sensitive (was 0.03)
        detector_params.maxMarkerPerimeterRate = 4.0
        detector_params.polygonalApproxAccuracyRate = 0.05  # More lenient (was 0.03)
        detector_params.cornerRefinementWinSize = 5
        detector_params.cornerRefinementMaxIterations = 30
        detector_params.cornerRefinementMinAccuracy = 0.001
        detector_params.markerBorderBits = 1
        detector_params.perspectiveRemovePixelPerCell = 4
        detector_params.perspectiveRemoveIgnoredMarginPerCell = 0.13
        detector_params.maxErroneousBitsInBorderRate = 0.4  # More lenient (was 0.35)
        detector_params.minOtsuStdDev = 3.0  # More sensitive (was 5.0)
        detector_params.errorCorrectionRate = 0.6

        return cv2.aruco.ArucoDetector(self.aruco_dict, detector_params)

    def detect_markers(self, image: np.ndarray) -> List[MarkerData]:
        """
        Detect ArUco markers in the image.

        Args:
            image: Input image (BGR format)

        Returns:
            List of detected marker data
        """
        try:
            # Convert to grayscale for detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Detect markers
            corners, ids, rejected = self.detector.detectMarkers(gray)

            markers = []
            if ids is not None:
                for i, marker_id in enumerate(ids.flatten()):
                    marker_corners = corners[i][0]
                    center = np.mean(marker_corners, axis=0)

                    # Estimate pose if camera parameters are available
                    pose = None
                    if self.camera_matrix is not None and self.dist_coeffs is not None:
                        pose = self._estimate_pose(marker_corners)

                    marker_data = MarkerData(
                        id=int(marker_id),
                        corners=marker_corners,
                        center=(float(center[0]), float(center[1])),
                        pose=pose,
                    )
                    markers.append(marker_data)

                    self.logger.info(
                        f"Detected marker ID {marker_id} at center {center}"
                    )

            self.logger.info(f"Detected {len(markers)} markers")
            return markers

        except Exception as e:
            self.logger.error(f"Error detecting markers: {e}")
            return []

    def _estimate_pose(self, corners: np.ndarray) -> Optional[MarkerPose]:
        """Estimate marker pose using camera parameters."""
        try:
            if self.camera_matrix is None or self.dist_coeffs is None:
                return None

            # Create marker points
            marker_points = np.array(
                [
                    [-self.marker_size / 2, self.marker_size / 2, 0],
                    [self.marker_size / 2, self.marker_size / 2, 0],
                    [self.marker_size / 2, -self.marker_size / 2, 0],
                    [-self.marker_size / 2, -self.marker_size / 2, 0],
                ],
                dtype=np.float32,
            )

            # Estimate pose
            success, rvec, tvec = cv2.solvePnP(
                marker_points, corners, self.camera_matrix, self.dist_coeffs
            )

            if success:
                # Convert rotation vector to rotation matrix
                rotation_matrix, _ = cv2.Rodrigues(rvec)

                # Convert to Euler angles
                euler_angles = self._rotation_matrix_to_euler_angles(rotation_matrix)

                return MarkerPose(
                    rotation_matrix=rotation_matrix,
                    translation_vector=tvec.flatten(),
                    euler_angles=euler_angles,
                )

            return None

        except Exception as e:
            self.logger.error(f"Error estimating pose: {e}")
            return None

    def _rotation_matrix_to_euler_angles(
        self, R: np.ndarray
    ) -> Tuple[float, float, float]:
        """Convert rotation matrix to Euler angles (roll, pitch, yaw)."""
        sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
        singular = sy < 1e-6

        if not singular:
            x = np.arctan2(R[2, 1], R[2, 2])
            y = np.arctan2(-R[2, 0], sy)
            z = np.arctan2(R[1, 0], R[0, 0])
        else:
            x = np.arctan2(-R[1, 2], R[1, 1])
            y = np.arctan2(-R[2, 0], sy)
            z = 0

        return (np.degrees(x), np.degrees(y), np.degrees(z))

    def get_corner_markers(
        self, markers: List[MarkerData]
    ) -> Optional[Dict[int, MarkerData]]:
        """
        Get the four corner markers for perspective correction.

        Args:
            markers: List of detected markers

        Returns:
            Dictionary mapping marker IDs to marker data, or None if not all corners found
        """
        # Get corner marker IDs for current template (or default)
        corner_marker_ids = self.get_template_corner_markers()

        corner_markers = {}

        for marker in markers:
            if marker.id in corner_marker_ids:
                corner_markers[marker.id] = marker

        # Check if we have all four corner markers
        if len(corner_markers) == 4:
            self.logger.info(
                f"All four corner markers detected: {list(corner_markers.keys())}"
            )
            return corner_markers
        else:
            missing_ids = set(corner_marker_ids) - set(corner_markers.keys())
            self.logger.warning(f"Missing corner markers: {missing_ids}")
            return None

    def create_perspective_transform(
        self, corner_markers: Dict[int, MarkerData]
    ) -> Optional[np.ndarray]:
        """
        Create perspective transform matrix from corner markers.

        Args:
            corner_markers: Dictionary of corner markers

        Returns:
            Homography matrix for perspective correction
        """
        try:
            # Define the order: top-left, top-right, bottom-left, bottom-right
            # For any template, we assume the markers are in the same relative positions
            marker_order = (
                self.get_template_corner_markers()
            )  # [0,1,2,3] or [4,5,6,7] etc.

            # Get corner points in the correct order
            src_points = []
            for marker_id in marker_order:
                if marker_id in corner_markers:
                    # Use the center of the marker
                    center = corner_markers[marker_id].center
                    src_points.append([center[0], center[1]])
                else:
                    self.logger.error(
                        f"Missing marker {marker_id} for perspective transform"
                    )
                    return None

            src_points = np.array(src_points, dtype=np.float32)

            # Define destination points (rectangular output)
            # Calculate the size based on the detected markers
            # For correct mapping: 0->(0,0), 1->(w,0), 2->(0,h), 3->(w,h)
            width = max(
                np.linalg.norm(src_points[1] - src_points[0]),  # top edge
                np.linalg.norm(src_points[3] - src_points[2]),  # bottom edge
            )
            height = max(
                np.linalg.norm(src_points[2] - src_points[0]),  # left edge
                np.linalg.norm(src_points[3] - src_points[1]),  # right edge
            )

            # Map markers to rectangle corners:
            # 0 (top-left) -> (0, 0)
            # 1 (top-right) -> (width, 0)
            # 2 (bottom-left) -> (0, height)
            # 3 (bottom-right) -> (width, height)
            dst_points = np.array(
                [[0, 0], [width, 0], [0, height], [width, height]], dtype=np.float32
            )

            # Calculate homography matrix
            homography = cv2.getPerspectiveTransform(src_points, dst_points)

            self.logger.info(f"Perspective transform created: {width:.1f}x{height:.1f}")
            return homography

        except Exception as e:
            self.logger.error(f"Error creating perspective transform: {e}")
            return None

    def apply_perspective_correction(
        self, image: np.ndarray, homography: np.ndarray
    ) -> np.ndarray:
        """
        Apply perspective correction to the image.

        Args:
            image: Input image
            homography: Homography matrix

        Returns:
            Perspective-corrected image
        """
        try:
            # Calculate the size from the homography matrix
            # Transform the corners of the original image to get the output size
            h, w = image.shape[:2]
            corners = np.array(
                [[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32
            ).reshape(-1, 1, 2)

            # Transform the corners
            transformed_corners = cv2.perspectiveTransform(corners, homography)

            # Find the bounding box of the transformed corners
            min_x = int(np.floor(np.min(transformed_corners[:, :, 0])))
            max_x = int(np.ceil(np.max(transformed_corners[:, :, 0])))
            min_y = int(np.floor(np.min(transformed_corners[:, :, 1])))
            max_y = int(np.ceil(np.max(transformed_corners[:, :, 1])))

            # Calculate output size
            output_width = max_x - min_x
            output_height = max_y - min_y

            # Create translation matrix to shift the result to positive coordinates
            translation_matrix = np.array(
                [[1, 0, -min_x], [0, 1, -min_y], [0, 0, 1]], dtype=np.float32
            )

            # Combine homography with translation
            final_homography = translation_matrix @ homography

            # Apply perspective transform with correct size using Lanczos interpolation for highest quality
            corrected = cv2.warpPerspective(
                image,
                final_homography,
                (output_width, output_height),
                flags=cv2.INTER_LANCZOS4,
            )

            self.logger.info(
                f"Perspective correction applied: {output_width}x{output_height}"
            )
            return corrected

        except Exception as e:
            self.logger.error(f"Error applying perspective correction: {e}")
            return image

    def apply_template_mask(self, image: np.ndarray, mask_path: str) -> np.ndarray:
        """
        Apply template mask to extract only the drawing area with transparent background.
        Uses reliable centered approach with proper scaling.

        Args:
            image: Input image
            mask_path: Path to the template mask

        Returns:
            Masked image with alpha channel (BGRA)
        """
        try:
            # Load the mask
            mask_template = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            if mask_template is None:
                self.logger.error(f"Could not load mask from {mask_path}")
                return image

            # Resize mask to match image size (centered approach)
            mask_resized = cv2.resize(mask_template, (image.shape[1], image.shape[0]))

            # Create a binary mask: treat gray pixels (above threshold) as white areas to extract
            _, binary_mask = cv2.threshold(mask_resized, 128, 255, cv2.THRESH_BINARY)

            # Convert image to BGRA (add alpha channel)
            if image.shape[2] == 3:
                bgra_image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            else:
                bgra_image = image.copy()

            # Apply the binary mask as alpha channel
            bgra_image[:, :, 3] = binary_mask

            # Apply the binary mask to the BGR channels
            masked_bgr = cv2.bitwise_and(
                bgra_image[:, :, :3], bgra_image[:, :, :3], mask=binary_mask
            )
            bgra_image[:, :, :3] = masked_bgr

            self.logger.info(
                "Template mask applied with transparent background (centered approach)"
            )
            return bgra_image

        except Exception as e:
            self.logger.error(f"Error applying template mask: {e}")
            return image

    def save_result(
        self, image: np.ndarray, output_path: str, metadata: Dict[str, Any]
    ) -> bool:
        """
        Save the processed image and metadata.

        Args:
            image: Processed image to save (can be BGR or BGRA)
            output_path: Output file path
            metadata: Metadata to save as JSON

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Save image with proper parameters for transparency
            if image.shape[2] == 4:  # BGRA image with alpha channel
                # Use PNG format to preserve transparency
                if not output_path.lower().endswith(".png"):
                    output_path = str(output_file.with_suffix(".png"))
                    output_file = Path(output_path)

                # Save with PNG compression parameters
                cv2.imwrite(str(output_file), image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
                self.logger.info(f"Saved BGRA image with transparency: {output_file}")
            else:
                # Regular BGR image
                cv2.imwrite(str(output_file), image)
                self.logger.info(f"Saved BGR image: {output_file}")

            # Save metadata
            metadata_file = output_file.with_suffix(".json")
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Metadata saved: {metadata_file}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving result: {e}")
            return False

    def save_debug_images(
        self,
        original: np.ndarray,
        corrected: np.ndarray,
        mask: np.ndarray,
        output_dir: str,
    ) -> None:
        """
        Save intermediate processing steps for debugging.

        Args:
            original: Original input image
            corrected: Perspective-corrected or cropped image
            mask: Template mask
            output_dir: Directory to save debug images
        """
        try:
            debug_dir = Path(output_dir) / "debug"
            debug_dir.mkdir(parents=True, exist_ok=True)

            # Save original image
            cv2.imwrite(str(debug_dir / "01_original.png"), original)

            # Save corrected/cropped image
            cv2.imwrite(str(debug_dir / "02_corrected.png"), corrected)

            # Save template mask
            cv2.imwrite(str(debug_dir / "03_template_mask.png"), mask)

            self.logger.info(f"Debug images saved to {debug_dir}")

        except Exception as e:
            self.logger.error(f"Error saving debug images: {e}")

    def process_frame(
        self, frame: np.ndarray, output_path: str, use_homography: bool = False
    ) -> bool:
        """
        Process a frame (numpy array) directly.

        Args:
            frame: Input frame as numpy array
            output_path: Path for output image
            use_homography: Whether to use homography correction instead of simple cropping

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Processing frame to: {output_path}")

            # Step 1: Detect ArUco markers
            markers = self.detect_markers(frame)
            if not markers:
                self.logger.error("No markers detected")
                return False

            # Step 1.5: Detect template from marker IDs
            marker_ids = [marker.id for marker in markers]
            template_id = self.detect_template(marker_ids)

            # Step 2: Get corner markers (now template-aware)
            corner_markers = self.get_corner_markers(markers)
            if corner_markers is None:
                self.logger.error("Could not find all corner markers")
                return False

            # Step 3: Extract the area using homography or simple cropping
            if use_homography:
                # Use homography for perspective correction
                homography = self.create_perspective_transform(corner_markers)
                if homography is None:
                    self.logger.error("Could not create perspective transform")
                    return False

                corrected = self.apply_perspective_correction(frame, homography)
                self.logger.info("Used homography perspective correction")

                # Step 3.5: Detect markers again in straightened image and crop
                straightened_markers = self.detect_markers(corrected)
                straightened_corner_markers = self.get_corner_markers(
                    straightened_markers
                )
                if straightened_corner_markers is None:
                    self.logger.error(
                        "Could not find corner markers in straightened image"
                    )
                    return False

                # Use the new perspective cropping method
                corrected = self._crop_perspective_corrected_area(
                    corrected, straightened_corner_markers
                )
                self.logger.info("Used perspective-corrected cropping")
            else:
                # Use simple cropping (no homography)
                corrected = self._crop_marker_area(frame, corner_markers)
                self.logger.info("Used simple cropping (no homography)")

            # Step 4: Apply template mask (template-aware)
            template_mask_path = self.get_template_mask_path()
            if template_mask_path:
                masked = self.apply_template_mask(corrected, template_mask_path)
            else:
                self.logger.error("No template mask found")
                return False

            # Step 5: Crop to only the masked content area
            final_result = self._crop_masked_area(masked)

            # Step 6: Prepare metadata
            metadata = {
                "input_image": "webcam_frame",
                "mask_path": str(template_mask_path) if template_mask_path else None,
                "output_image": str(output_path),
                "detected_markers": len(markers),
                "detected_marker_ids": marker_ids,
                "template_detected": template_id,
                "template_config": self.current_template_config
                if self.current_template_config
                else None,
                "corner_markers": {
                    str(k): {"id": v.id, "center": v.center}
                    for k, v in corner_markers.items()
                },
                "processing_timestamp": str(datetime.now().timestamp()),
                "detector_config": {
                    "dict_type": self.dict_type,
                    "marker_size": self.marker_size,
                },
                "processing_method": "homography"
                if use_homography
                else "simple_cropping",
            }

            # Step 7: Save result
            success = cv2.imwrite(output_path, final_result)
            if not success:
                self.logger.error(f"Failed to save image to {output_path}")
                return False

            # Step 8: Save metadata
            metadata_path = str(output_path).replace(".png", ".json")
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            self.logger.info(f"Successfully processed frame to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
            return False

    def process_image(
        self,
        image_path: str,
        mask_path: str,
        output_path: str,
        use_homography: bool = False,
    ) -> bool:
        """
        Complete image processing pipeline.

        Args:
            image_path: Path to input image
            mask_path: Path to template mask
            output_path: Path for output image
            use_homography: Whether to use homography correction instead of simple cropping

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Processing image: {image_path}")

            # Load image
            image = cv2.imread(image_path)
            if image is None:
                self.logger.error(f"Could not load image from {image_path}")
                return False

            # Step 1: Detect ArUco markers
            markers = self.detect_markers(image)
            if not markers:
                self.logger.error("No markers detected")
                return False

            # Step 1.5: Detect template from marker IDs
            marker_ids = [marker.id for marker in markers]
            template_id = self.detect_template(marker_ids)

            # Step 2: Get corner markers (now template-aware)
            corner_markers = self.get_corner_markers(markers)
            if corner_markers is None:
                self.logger.error("Could not find all corner markers")
                return False

            # Step 3: Extract the area using homography or simple cropping
            if use_homography:
                # Use homography for perspective correction
                homography = self.create_perspective_transform(corner_markers)
                if homography is None:
                    self.logger.error("Could not create perspective transform")
                    return False

                corrected = self.apply_perspective_correction(image, homography)
                self.logger.info("Used homography perspective correction")

                # Step 3.5: Detect markers again in straightened image and crop
                straightened_markers = self.detect_markers(corrected)
                straightened_corner_markers = self.get_corner_markers(
                    straightened_markers
                )
                if straightened_corner_markers is None:
                    self.logger.error(
                        "Could not find corner markers in straightened image"
                    )
                    return False

                # Use the new perspective cropping method
                corrected = self._crop_perspective_corrected_area(
                    corrected, straightened_corner_markers
                )
                self.logger.info("Used perspective-corrected cropping")
            else:
                # Use simple cropping (no homography)
                corrected = self._crop_marker_area(image, corner_markers)
                self.logger.info("Used simple cropping (no homography)")

            # Step 4: Apply template mask (template-aware)
            template_mask_path = self.get_template_mask_path()
            if template_mask_path:
                masked = self.apply_template_mask(corrected, template_mask_path)
            else:
                # Fallback to provided mask path
                masked = self.apply_template_mask(corrected, mask_path)

            # Step 5: Crop to only the masked content area
            final_result = self._crop_masked_area(masked)

            # Step 6: Prepare metadata
            metadata = {
                "input_image": image_path,
                "mask_path": template_mask_path if template_mask_path else mask_path,
                "output_image": output_path,
                "detected_markers": len(markers),
                "detected_marker_ids": marker_ids,
                "template_detected": template_id,
                "template_config": self.current_template_config
                if self.current_template_config
                else None,
                "corner_markers": {
                    str(k): {"id": v.id, "center": v.center}
                    for k, v in corner_markers.items()
                },
                "processing_timestamp": str(Path(image_path).stat().st_mtime),
                "detector_config": {
                    "dict_type": self.dict_type,
                    "marker_size": self.marker_size,
                },
                "processing_method": "homography"
                if use_homography
                else "simple_cropping",
            }

            # Step 7: Save result
            success = self.save_result(final_result, output_path, metadata)

            if success:
                self.logger.info("Image processing completed successfully")
            else:
                self.logger.error("Failed to save result")

            return success

        except Exception as e:
            self.logger.error(f"Error in image processing pipeline: {e}")
            return False

    def _crop_marker_area(
        self, image: np.ndarray, corner_markers: Dict[int, "MarkerData"]
    ) -> np.ndarray:
        """
        Crop the area within the marker bounds without homography.
        Extracts a rectangular area positioned at the marker tips.

        Args:
            image: Input image
            corner_markers: Dictionary of corner markers

        Returns:
            Cropped image
        """
        try:
            # Get all marker centers (template-aware)
            centers = []
            corner_marker_ids = self.get_template_corner_markers()
            for (
                marker_id
            ) in corner_marker_ids:  # Top-left, top-right, bottom-left, bottom-right
                if marker_id in corner_markers:
                    center = corner_markers[marker_id].center
                    centers.append([center[0], center[1]])

            centers = np.array(centers)

            # Calculate the bounding box of marker centers
            x_min = int(np.min(centers[:, 0]))
            y_min = int(np.min(centers[:, 1]))
            x_max = int(np.max(centers[:, 0]))
            y_max = int(np.max(centers[:, 1]))

            # Calculate the size of the marker area
            marker_width = x_max - x_min
            marker_height = y_max - y_min

            # Define the target crop size (779x457)
            target_width = 779
            target_height = 457

            # Calculate the offset to position the crop at the marker tips
            # We want the crop to be centered within the marker area
            offset_x = (marker_width - target_width) // 2
            offset_y = (marker_height - target_height) // 2

            # Calculate the crop coordinates
            crop_x_min = x_min + offset_x
            crop_y_min = y_min + offset_y
            crop_x_max = crop_x_min + target_width
            crop_y_max = crop_y_min + target_height

            # Ensure the crop is within image bounds
            img_height, img_width = image.shape[:2]
            crop_x_min = max(0, crop_x_min)
            crop_y_min = max(0, crop_y_min)
            crop_x_max = min(img_width, crop_x_max)
            crop_y_max = min(img_height, crop_y_max)

            # Adjust if the crop would be outside bounds
            if crop_x_max - crop_x_min < target_width:
                # Adjust to fit within image width
                if crop_x_min == 0:
                    crop_x_max = min(img_width, target_width)
                else:
                    crop_x_min = max(0, img_width - target_width)

            if crop_y_max - crop_y_min < target_height:
                # Adjust to fit within image height
                if crop_y_min == 0:
                    crop_y_max = min(img_height, target_height)
                else:
                    crop_y_min = max(0, img_height - target_height)

            # Crop the image
            cropped = image[crop_y_min:crop_y_max, crop_x_min:crop_x_max]

            self.logger.info(
                f"Marker area: {x_min},{y_min} to {x_max},{y_max} ({marker_width}x{marker_height})"
            )
            self.logger.info(
                f"Crop area: {crop_x_min},{crop_y_min} to {crop_x_max},{crop_y_max} ({crop_x_max-crop_x_min}x{crop_y_max-crop_y_min})"
            )
            return cropped

        except Exception as e:
            self.logger.error(f"Error cropping marker area: {e}")
            return image

    def _crop_perspective_corrected_area(
        self, image: np.ndarray, corner_markers: Dict[int, "MarkerData"]
    ) -> np.ndarray:
        """
        Crop the area within the marker bounds for perspective-corrected images.
        This method matches the scale and positioning of simple cropping by using
        the same offset calculation approach.

        Args:
            image: Perspective-corrected image
            corner_markers: Dictionary of corner markers

        Returns:
            Cropped image with same scale as simple cropping
        """
        try:
            # Get all marker centers (template-aware)
            centers = []
            corner_marker_ids = self.get_template_corner_markers()
            for (
                marker_id
            ) in corner_marker_ids:  # Top-left, top-right, bottom-left, bottom-right
                if marker_id in corner_markers:
                    center = corner_markers[marker_id].center
                    centers.append([center[0], center[1]])

            centers = np.array(centers)

            # Calculate the bounding box of marker centers
            x_min = int(np.min(centers[:, 0]))
            y_min = int(np.min(centers[:, 1]))
            x_max = int(np.max(centers[:, 0]))
            y_max = int(np.max(centers[:, 1]))

            # Calculate the size of the marker area in the perspective-corrected image
            marker_width = x_max - x_min
            marker_height = y_max - y_min

            # Define the target crop size (779x457)
            target_width = 779
            target_height = 457

            # Calculate the scale factor to match simple cropping behavior
            # In simple cropping, we use offset = (marker_size - target_size) // 2
            # But in perspective correction, the marker spacing might be different
            # We need to adjust the crop size to maintain the same visual scale

            # Calculate what the crop size should be to maintain the same marker-to-crop ratio as simple cropping
            # Target ratios from simple cropping: ~1.149 (width) and ~1.225 (height)
            target_ratio_w = 1.149  # Based on analysis of simple cropping
            target_ratio_h = 1.225

            # Calculate ideal crop size to match these ratios
            ideal_crop_width = int(marker_width / target_ratio_w)
            ideal_crop_height = int(marker_height / target_ratio_h)

            # Use the ideal crop size to match simple cropping ratios
            # Don't force it to be the target size - let it be what it needs to be for proper scaling
            adjusted_width = ideal_crop_width
            adjusted_height = ideal_crop_height

            # Calculate offset with the adjusted size
            offset_x = (marker_width - adjusted_width) // 2
            offset_y = (marker_height - adjusted_height) // 2

            # Calculate the crop coordinates using the offset approach
            crop_x_min = x_min + offset_x
            crop_y_min = y_min + offset_y
            crop_x_max = crop_x_min + adjusted_width
            crop_y_max = crop_y_min + adjusted_height

            # Ensure the crop is within image bounds
            img_height, img_width = image.shape[:2]
            crop_x_min = max(0, crop_x_min)
            crop_y_min = max(0, crop_y_min)
            crop_x_max = min(img_width, crop_x_max)
            crop_y_max = min(img_height, crop_y_max)

            # Adjust if the crop would be outside bounds
            actual_width = crop_x_max - crop_x_min
            actual_height = crop_y_max - crop_y_min

            if actual_width < adjusted_width:
                if crop_x_min == 0:
                    crop_x_max = min(img_width, crop_x_min + adjusted_width)
                else:
                    crop_x_min = max(0, img_width - adjusted_width)
                    crop_x_max = crop_x_min + adjusted_width

            if actual_height < adjusted_height:
                if crop_y_min == 0:
                    crop_y_max = min(img_height, crop_y_min + adjusted_height)
                else:
                    crop_y_min = max(0, img_height - adjusted_height)
                    crop_y_max = crop_y_min + adjusted_height

            # Crop the image
            cropped = image[crop_y_min:crop_y_max, crop_x_min:crop_x_max]

            self.logger.info(
                f"Perspective marker area: {x_min},{y_min} to {x_max},{y_max} ({marker_width}x{marker_height})"
            )
            self.logger.info(
                f"Ideal crop size: {ideal_crop_width}x{ideal_crop_height}, adjusted: {adjusted_width}x{adjusted_height}"
            )
            self.logger.info(
                f"Perspective crop area: {crop_x_min},{crop_y_min} to {crop_x_max},{crop_y_max} ({crop_x_max-crop_x_min}x{crop_y_max-crop_y_min})"
            )
            return cropped

        except Exception as e:
            self.logger.error(f"Error cropping perspective-corrected area: {e}")
            return image

    def _crop_masked_area(self, masked_image: np.ndarray) -> np.ndarray:
        """
        Crop the masked image to include only the area with actual content.
        Removes excess transparent background around the drawing.

        Args:
            masked_image: Image that has been masked (BGR or BGRA)

        Returns:
            Cropped image containing only the drawing area
        """
        try:
            # Handle both BGR and BGRA images
            if masked_image.shape[2] == 4:  # BGRA image
                # Use alpha channel to find non-transparent areas
                alpha_channel = masked_image[:, :, 3]

                # Find non-transparent pixels (alpha > 0)
                _, thresh = cv2.threshold(alpha_channel, 0, 255, cv2.THRESH_BINARY)
            else:  # BGR image
                # Convert to grayscale to find non-white areas
                gray = cv2.cvtColor(masked_image, cv2.COLOR_BGR2GRAY)

                # Find non-white pixels (drawing content)
                # Use threshold to find pixels that are not white (not 255)
                _, thresh = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)

            # Find contours of non-transparent/non-white areas
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if not contours:
                self.logger.warning("No drawing content found in masked image")
                return masked_image

            # Find the bounding rectangle of all contours
            x_min, y_min, w, h = cv2.boundingRect(np.vstack(contours))

            # Add some padding around the content
            padding = 10
            x_min = max(0, x_min - padding)
            y_min = max(0, y_min - padding)
            x_max = min(masked_image.shape[1], x_min + w + 2 * padding)
            y_max = min(masked_image.shape[0], y_min + h + 2 * padding)

            # Crop the image
            cropped = masked_image[y_min:y_max, x_min:x_max]

            self.logger.info(
                f"Masked area cropped: {x_min},{y_min} to {x_max},{y_max} ({x_max-x_min}x{y_max-y_min})"
            )
            return cropped

        except Exception as e:
            self.logger.error(f"Error cropping masked area: {e}")
            return masked_image
