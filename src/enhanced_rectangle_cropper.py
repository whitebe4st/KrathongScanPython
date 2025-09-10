"""
Enhanced rectangle cropper that looks for inner rectangles (like black-lined boundaries)
instead of just the outer paper boundary.
"""

from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np


def _create_aruco_mask(image: np.ndarray) -> np.ndarray:
    """Create a mask to exclude ArUco marker regions from rectangle detection."""
    try:
        # Import ArUco detector
        import cv2.aruco as aruco

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # Create empty mask (white = keep, black = exclude)
        mask = np.ones((h, w), dtype=np.uint8) * 255

        # Detect ArUco markers - use newer API
        try:
            # Try newer OpenCV 4.7+ API first
            aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
            detector = cv2.aruco.ArucoDetector(aruco_dict)
            corners, ids, _ = detector.detectMarkers(gray)
        except AttributeError:
            # Fallback to older API
            aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
            parameters = cv2.aruco.DetectorParameters_create()
            corners, ids, _ = cv2.aruco.detectMarkers(
                gray, aruco_dict, parameters=parameters
            )

        if ids is not None and len(corners) > 0:
            print(f"🎯 Detected {len(corners)} ArUco markers to exclude")

            # Create exclusion zones around each marker
            for corner_set in corners:
                corner_points = corner_set[0].astype(int)

                # Expand the exclusion zone around the marker
                x_min = max(0, np.min(corner_points[:, 0]) - 50)
                x_max = min(w, np.max(corner_points[:, 0]) + 50)
                y_min = max(0, np.min(corner_points[:, 1]) - 50)
                y_max = min(h, np.max(corner_points[:, 1]) + 50)

                # Black out this region in the mask
                mask[y_min:y_max, x_min:x_max] = 0
        else:
            print("🔍 No ArUco markers detected for masking")

        return mask

    except Exception as e:
        print(f"Error creating ArUco mask: {e}")
        # Return all-white mask if error
        return np.ones((image.shape[0], image.shape[1]), dtype=np.uint8) * 255


def _get_rectangle_from_aruco_markers(
    image: np.ndarray, debug_dir: Path
) -> Optional[np.ndarray]:
    """Get rectangle boundaries using ArUco marker positions."""
    try:
        # Import ArUco detector
        import cv2.aruco as aruco

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # Detect ArUco markers
        try:
            # Try newer OpenCV 4.7+ API first
            aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
            detector = cv2.aruco.ArucoDetector(aruco_dict)
            corners, ids, _ = detector.detectMarkers(gray)
        except AttributeError:
            # Fallback to older API
            aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
            parameters = cv2.aruco.DetectorParameters_create()
            corners, ids, _ = cv2.aruco.detectMarkers(
                gray, aruco_dict, parameters=parameters
            )

        if ids is None or len(corners) < 4:
            print(
                f"❌ Need 4 ArUco markers for rectangle boundaries, found {len(corners) if ids is not None else 0}"
            )
            return None

        print(f"🎯 Found {len(corners)} ArUco markers, calculating rectangle boundaries")

        # Create visualization
        debug_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        # Dictionary to store marker positions by ID
        marker_positions = {}

        for i, (corner_set, marker_id) in enumerate(zip(corners, ids.flatten())):
            corner_points = corner_set[0].astype(int)

            # Draw marker outline
            cv2.drawContours(debug_img, [corner_points], -1, (0, 255, 0), 2)

            # Calculate marker center
            center_x = int(np.mean(corner_points[:, 0]))
            center_y = int(np.mean(corner_points[:, 1]))

            # Store marker position and corners
            marker_positions[marker_id] = {
                "center": (center_x, center_y),
                "corners": corner_points,
            }

            # Label marker
            cv2.putText(
                debug_img,
                str(marker_id),
                (center_x - 10, center_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),
                2,
            )

        cv2.imwrite(str(debug_dir / "02_aruco_markers.png"), debug_img)

        # Now calculate the inner rectangle using marker positions
        # The inner corners of the markers define the rectangle boundary

        # We need to find which markers are in which corners
        # Sort markers by position to identify corners
        marker_list = list(marker_positions.items())

        if len(marker_list) < 4:
            print(f"❌ Need exactly 4 markers, found {len(marker_list)}")
            return None

        # Sort by y-coordinate first, then x-coordinate to identify corners
        marker_list.sort(key=lambda x: (x[1]["center"][1], x[1]["center"][0]))

        # Split into top and bottom rows
        top_markers = marker_list[:2]
        bottom_markers = marker_list[2:]

        # Sort each row by x-coordinate
        top_markers.sort(key=lambda x: x[1]["center"][0])
        bottom_markers.sort(key=lambda x: x[1]["center"][0])

        # Now we have: top_left, top_right, bottom_left, bottom_right
        top_left_id, top_left_data = top_markers[0]
        top_right_id, top_right_data = top_markers[1]
        bottom_left_id, bottom_left_data = bottom_markers[0]
        bottom_right_id, bottom_right_data = bottom_markers[1]

        print(
            f"📍 Corner markers - TL:{top_left_id}, TR:{top_right_id}, BL:{bottom_left_id}, BR:{bottom_right_id}"
        )

        # Calculate the inner rectangle boundaries using the inner corners of markers
        # For each marker, find the corner point that's closest to the center of the image
        image_center = (w // 2, h // 2)

        def get_inner_corner(marker_corners, image_center):
            """Get the corner of the marker that's closest to the image center."""
            distances = [
                np.linalg.norm(np.array(corner) - np.array(image_center))
                for corner in marker_corners
            ]
            return marker_corners[np.argmin(distances)]

        # Get inner corners for each marker
        tl_inner = get_inner_corner(top_left_data["corners"], image_center)
        tr_inner = get_inner_corner(top_right_data["corners"], image_center)
        bl_inner = get_inner_corner(bottom_left_data["corners"], image_center)
        br_inner = get_inner_corner(bottom_right_data["corners"], image_center)

        # Create rectangle from these points
        rectangle_points = np.array(
            [tl_inner, tr_inner, br_inner, bl_inner], dtype=np.int32
        )

        # Draw the calculated rectangle
        debug_rect = debug_img.copy()
        cv2.drawContours(debug_rect, [rectangle_points], -1, (0, 0, 255), 3)
        cv2.imwrite(str(debug_dir / "03_aruco_rectangle.png"), debug_rect)

        print(f"✅ ArUco rectangle calculated: {rectangle_points.shape}")

        # Reshape to match expected format
        return rectangle_points.reshape(-1, 1, 2)

    except Exception as e:
        print(f"Error getting rectangle from ArUco markers: {e}")
        import traceback

        traceback.print_exc()
        return None


def _find_center_rectangle(
    gray: np.ndarray, min_area: float, max_area: float, debug_dir: Path
) -> Optional[np.ndarray]:
    """Find rectangle in the center region, excluding corners where ArUco markers typically are."""
    h, w = gray.shape

    # Create a mask that excludes corner regions where ArUco markers typically appear
    center_mask = np.ones((h, w), dtype=np.uint8) * 255

    # Size of corner exclusion zones (typically 15-20% of image dimension)
    corner_size_h = int(h * 0.18)
    corner_size_w = int(w * 0.18)

    # Black out corners
    center_mask[0:corner_size_h, 0:corner_size_w] = 0  # Top-left
    center_mask[0:corner_size_h, w - corner_size_w : w] = 0  # Top-right
    center_mask[h - corner_size_h : h, 0:corner_size_w] = 0  # Bottom-left
    center_mask[h - corner_size_h : h, w - corner_size_w : w] = 0  # Bottom-right

    cv2.imwrite(str(debug_dir / "08_center_mask.png"), center_mask)

    # Apply center mask to gray image
    gray_center = cv2.bitwise_and(gray, gray, mask=center_mask)
    cv2.imwrite(str(debug_dir / "09_gray_center.png"), gray_center)

    # Look for dark regions in the center area
    _, thresh_center = cv2.threshold(gray_center, 120, 255, cv2.THRESH_BINARY_INV)
    cv2.imwrite(str(debug_dir / "10_thresh_center.png"), thresh_center)

    # Morphological operations to connect lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    morph_center = cv2.morphologyEx(
        thresh_center, cv2.MORPH_CLOSE, kernel, iterations=3
    )
    cv2.imwrite(str(debug_dir / "11_morph_center.png"), morph_center)

    # Find contours
    contours, _ = cv2.findContours(
        morph_center, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    print(f"🔍 Found {len(contours)} center contours")

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        print(f"   Center contour {i}: area={area}")

        if min_area <= area <= max_area:
            # Check if contour center is reasonably in the image center
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                # Should be in middle 60% of image
                center_zone_x = (w * 0.2, w * 0.8)
                center_zone_y = (h * 0.2, h * 0.8)

                if (
                    center_zone_x[0] <= cx <= center_zone_x[1]
                    and center_zone_y[0] <= cy <= center_zone_y[1]
                ):
                    peri = cv2.arcLength(contour, True)
                    for eps_mul in (0.01, 0.015, 0.02, 0.03, 0.05, 0.08):
                        approx = cv2.approxPolyDP(contour, eps_mul * peri, True)
                        if len(approx) == 4:
                            if _is_good_rectangle(approx, min_area):
                                print(f"✅ Found good center rectangle with area {area}")

                                # Draw the selected rectangle
                                debug_rect = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                                cv2.drawContours(
                                    debug_rect, [approx], -1, (255, 0, 255), 3
                                )
                                cv2.imwrite(
                                    str(debug_dir / f"12_center_rectangle_{i}.png"),
                                    debug_rect,
                                )

                                return approx

    return None


def find_inner_rectangle_contour(image: np.ndarray) -> Optional[np.ndarray]:
    """Find inner rectangular contour using ArUco marker positions as cropping boundaries."""
    try:
        h, w = image.shape[:2]

        # Save debug images to see what we're detecting
        debug_dir = Path("debug_inner_detection")
        debug_dir.mkdir(exist_ok=True)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(str(debug_dir / "01_original_gray.png"), gray)

        # First, try to use ArUco markers as cropping boundaries
        aruco_rect = _get_rectangle_from_aruco_markers(image, debug_dir)
        if aruco_rect is not None:
            print("🎯 Using ArUco markers as cropping boundaries")
            return aruco_rect

        print("🔍 No ArUco markers found, falling back to line detection...")

        # Fallback to original detection methods
        min_area = 0.02 * (h * w)  # Even smaller min area for inner rectangles
        max_area = 0.7 * (h * w)  # Maximum area to exclude paper boundary

        # First, try to detect and mask out ArUco markers to avoid confusing them with the drawing border
        aruco_mask = _create_aruco_mask(image)
        cv2.imwrite(str(debug_dir / "01b_aruco_mask.png"), aruco_mask)

        # Apply the ArUco mask to the grayscale image
        gray_masked = cv2.bitwise_and(gray, gray, mask=aruco_mask)
        cv2.imwrite(str(debug_dir / "01c_gray_masked.png"), gray_masked)

        # Strategy 1: Look for dark lines (black rectangle borders) excluding ArUco areas
        # Use threshold to isolate dark regions
        _, thresh_dark = cv2.threshold(gray_masked, 100, 255, cv2.THRESH_BINARY_INV)
        cv2.imwrite(str(debug_dir / "02_threshold_dark.png"), thresh_dark)

        # Apply the ArUco mask to the threshold result to exclude ArUco regions
        thresh_dark_masked = cv2.bitwise_and(thresh_dark, thresh_dark, mask=aruco_mask)
        cv2.imwrite(str(debug_dir / "02b_threshold_masked.png"), thresh_dark_masked)

        # Use morphological operations to connect line segments
        kernel_line = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        morph_dark = cv2.morphologyEx(
            thresh_dark_masked, cv2.MORPH_CLOSE, kernel_line, iterations=3
        )
        cv2.imwrite(str(debug_dir / "03_morph_dark.png"), morph_dark)

        # Find contours on the morphologically processed image
        contours, _ = cv2.findContours(
            morph_dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Draw all contours for debugging
        debug_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(debug_img, contours, -1, (0, 255, 0), 2)
        cv2.imwrite(str(debug_dir / "04_all_contours.png"), debug_img)

        # Look for rectangular contours in the right size range
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        print(f"🔍 Found {len(contours)} contours, looking for inner rectangle...")

        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            print(f"   Contour {i}: area={area}, min={min_area}, max={max_area}")

            # Skip contours that are too large (paper boundary) or too small
            if area < min_area or area > max_area:
                continue

            # Try to approximate to a rectangle
            peri = cv2.arcLength(contour, True)
            for eps_mul in (0.01, 0.015, 0.02, 0.03, 0.05, 0.08):
                approx = cv2.approxPolyDP(contour, eps_mul * peri, True)
                if len(approx) == 4:
                    # Check if it's reasonably rectangular
                    if _is_good_rectangle(approx, min_area):
                        print(f"✅ Found good inner rectangle with area {area}")

                        # Draw the selected rectangle
                        debug_rect = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                        cv2.drawContours(debug_rect, [approx], -1, (0, 0, 255), 3)
                        cv2.imwrite(
                            str(debug_dir / f"05_selected_rectangle_{i}.png"),
                            debug_rect,
                        )

                        return approx

        # Strategy 2: Enhanced edge detection for drawn lines
        print("🔍 Trying enhanced edge detection...")

        # Gaussian blur to reduce noise - use masked gray image
        blurred = cv2.GaussianBlur(gray_masked, (3, 3), 0)

        # Edge detection with multiple parameters
        for low_thresh, high_thresh in [(20, 60), (30, 90), (50, 150)]:
            edges = cv2.Canny(blurred, low_thresh, high_thresh)
            cv2.imwrite(
                str(debug_dir / f"06_edges_{low_thresh}_{high_thresh}.png"), edges
            )

            # Apply ArUco mask to edges to exclude marker regions
            edges_masked = cv2.bitwise_and(edges, edges, mask=aruco_mask)
            cv2.imwrite(
                str(debug_dir / f"06b_edges_masked_{low_thresh}_{high_thresh}.png"),
                edges_masked,
            )

            # Dilate to connect broken lines
            kernel_edge = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            edges_dilated = cv2.dilate(edges_masked, kernel_edge, iterations=2)
            cv2.imwrite(
                str(debug_dir / f"07_edges_dilated_{low_thresh}_{high_thresh}.png"),
                edges_dilated,
            )

            contours, _ = cv2.findContours(
                edges_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            for contour in contours:
                area = cv2.contourArea(contour)
                if min_area <= area <= max_area:
                    peri = cv2.arcLength(contour, True)
                    for eps_mul in (0.01, 0.015, 0.02, 0.03, 0.05, 0.08):
                        approx = cv2.approxPolyDP(contour, eps_mul * peri, True)
                        if len(approx) == 4:
                            if _is_good_rectangle(approx, min_area):
                                print(f"✅ Found good rectangle with edges, area {area}")
                                return approx

        # Strategy 3: Look for center rectangle by excluding corner regions
        print("🔍 Trying center rectangle detection...")
        center_rect = _find_center_rectangle(gray, min_area, max_area, debug_dir)
        if center_rect is not None:
            return center_rect

        print("❌ No inner rectangle found")
        return None

    except Exception as e:
        print(f"Error in find_inner_rectangle_contour: {e}")
        import traceback

        traceback.print_exc()
        return None


def _is_good_rectangle(approx: np.ndarray, min_area: float) -> bool:
    """Check if the approximated contour is a good rectangle."""
    if len(approx) != 4:
        return False

    area = cv2.contourArea(approx)
    if area < min_area:
        return False

    # Check if the angles are roughly 90 degrees
    pts = approx.reshape(4, 2)

    # Calculate angles between consecutive sides
    angles = []
    for i in range(4):
        p1 = pts[i]
        p2 = pts[(i + 1) % 4]
        p3 = pts[(i + 2) % 4]

        # Vectors
        v1 = p1 - p2
        v2 = p3 - p2

        # Angle between vectors
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cos_angle = np.clip(cos_angle, -1, 1)
        angle = np.arccos(cos_angle) * 180 / np.pi
        angles.append(angle)

    # Check if angles are close to 90 degrees (allow some tolerance)
    for angle in angles:
        if not (70 <= angle <= 110):  # Allow 20 degree tolerance
            return False

    # Check aspect ratio (not too extreme)
    rect = cv2.boundingRect(approx)
    aspect_ratio = max(rect[2], rect[3]) / min(rect[2], rect[3])
    if aspect_ratio > 5:  # Too elongated
        return False

    return True


def detect_and_crop_inner_rectangle(
    image: np.ndarray,
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """Detect and crop to inner rectangle (like black-lined boundaries)."""
    contour = find_inner_rectangle_contour(image)
    if contour is None:
        return None, None

    # Use the same perspective transformation as the original
    from src.rectangle_cropper import warp_rectangle

    return warp_rectangle(image, contour), contour


def detect_and_crop_rectangle_enhanced(
    image: np.ndarray,
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Enhanced rectangle detection that tries inner rectangle first,
    then falls back to outer rectangle.
    """
    # Try inner rectangle first (for drawings with black borders)
    inner_cropped, inner_contour = detect_and_crop_inner_rectangle(image)
    if inner_cropped is not None:
        print("🎯 Inner rectangle detected (black border)")
        return inner_cropped, inner_contour

    # Fallback to original outer rectangle detection
    from src.rectangle_cropper import detect_and_crop_rectangle

    outer_cropped, outer_contour = detect_and_crop_rectangle(image)
    if outer_cropped is not None:
        print("📄 Outer rectangle detected (paper boundary)")
        return outer_cropped, outer_contour

    return None, None
