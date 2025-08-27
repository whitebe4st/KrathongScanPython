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
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


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

        # Expected corner marker IDs (for perspective correction)
        self.corner_marker_ids = [
            0,
            1,
            2,
            3,
        ]  # Top-left, top-right, bottom-right, bottom-left

        self.logger.info(f"ArUco Detector initialized with {dict_type} dictionary")

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

        # Optimize detection parameters
        detector_params.adaptiveThreshWinSizeMin = 3
        detector_params.adaptiveThreshWinSizeMax = 23
        detector_params.adaptiveThreshWinSizeStep = 10
        detector_params.adaptiveThreshConstant = 7
        detector_params.minMarkerPerimeterRate = 0.03
        detector_params.maxMarkerPerimeterRate = 4.0
        detector_params.polygonalApproxAccuracyRate = 0.03
        detector_params.cornerRefinementWinSize = 5
        detector_params.cornerRefinementMaxIterations = 30
        detector_params.cornerRefinementMinAccuracy = 0.001
        detector_params.markerBorderBits = 1
        detector_params.perspectiveRemovePixelPerCell = 4
        detector_params.perspectiveRemoveIgnoredMarginPerCell = 0.13
        detector_params.maxErroneousBitsInBorderRate = 0.35
        detector_params.minOtsuStdDev = 5.0
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
        corner_markers = {}

        for marker in markers:
            if marker.id in self.corner_marker_ids:
                corner_markers[marker.id] = marker

        # Check if we have all four corner markers
        if len(corner_markers) == 4:
            self.logger.info("All four corner markers detected")
            return corner_markers
        else:
            missing_ids = set(self.corner_marker_ids) - set(corner_markers.keys())
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
            # Define the order: top-left, top-right, bottom-right, bottom-left
            marker_order = [0, 1, 2, 3]

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
            width = max(
                np.linalg.norm(src_points[1] - src_points[0]),
                np.linalg.norm(src_points[2] - src_points[3]),
            )
            height = max(
                np.linalg.norm(src_points[3] - src_points[0]),
                np.linalg.norm(src_points[2] - src_points[1]),
            )

            dst_points = np.array(
                [[0, 0], [width, 0], [width, height], [0, height]], dtype=np.float32
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
            # Get the size from the homography matrix
            h, w = image.shape[:2]

            # Apply perspective transform
            corrected = cv2.warpPerspective(image, homography, (int(w), int(h)))

            self.logger.info("Perspective correction applied")
            return corrected

        except Exception as e:
            self.logger.error(f"Error applying perspective correction: {e}")
            return image

    def apply_template_mask(self, image: np.ndarray, mask_path: str) -> np.ndarray:
        """
        Apply template mask to extract only the drawing area with transparent background.

        Args:
            image: Input image
            mask_path: Path to the template mask

        Returns:
            Masked image with alpha channel (BGRA)
        """
        try:
            # Load the mask
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            if mask is None:
                self.logger.error(f"Could not load mask from {mask_path}")
                return image

            # Resize mask to match image size
            mask = cv2.resize(mask, (image.shape[1], image.shape[0]))

            # Create a binary mask: treat gray pixels (above threshold) as white areas to extract
            # Threshold: treat pixels with value > 128 as "white" areas to keep
            _, binary_mask = cv2.threshold(mask, 128, 255, cv2.THRESH_BINARY)

            # Convert image to BGRA (add alpha channel)
            if image.shape[2] == 3:
                bgra_image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            else:
                bgra_image = image.copy()

            # Create alpha channel from binary mask
            # White areas in mask (255) = fully opaque (255)
            # Black areas in mask (0) = fully transparent (0)
            alpha_channel = binary_mask

            # Apply the alpha channel
            bgra_image[:, :, 3] = alpha_channel

            # Apply the binary mask to the BGR channels
            # Keep original colors where mask is white, make black where mask is black
            masked_bgr = cv2.bitwise_and(
                bgra_image[:, :, :3], bgra_image[:, :, :3], mask=binary_mask
            )
            bgra_image[:, :, :3] = masked_bgr

            self.logger.info("Template mask applied with transparent background")
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

    def process_image(self, image_path: str, mask_path: str, output_path: str) -> bool:
        """
        Complete image processing pipeline.

        Args:
            image_path: Path to input image
            mask_path: Path to template mask
            output_path: Path for output image

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

            # Step 2: Get corner markers
            corner_markers = self.get_corner_markers(markers)
            if corner_markers is None:
                self.logger.error("Could not find all corner markers")
                return False

            # Step 3: Extract the area using simple cropping (no homography)
            corrected = self._crop_marker_area(image, corner_markers)
            self.logger.info("Used simple cropping (no homography)")

            # Step 5: Apply template mask
            masked = self.apply_template_mask(corrected, mask_path)

            # Step 6: Crop to only the masked content area
            final_result = self._crop_masked_area(masked)

            # Step 7: Prepare metadata
            metadata = {
                "input_image": image_path,
                "mask_path": mask_path,
                "output_image": output_path,
                "detected_markers": len(markers),
                "corner_markers": {
                    str(k): {"id": v.id, "center": v.center}
                    for k, v in corner_markers.items()
                },
                "processing_timestamp": str(Path(image_path).stat().st_mtime),
                "detector_config": {
                    "dict_type": self.dict_type,
                    "marker_size": self.marker_size,
                },
            }

            # Step 8: Save result
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
            # Get all marker centers
            centers = []
            for marker_id in [
                0,
                1,
                2,
                3,
            ]:  # Top-left, top-right, bottom-right, bottom-left
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
