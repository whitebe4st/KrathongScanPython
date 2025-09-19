"""
Rectangle cropper extracted from scantest.py logic.

Find a rectangular contour and warp the image to that rectangle area.
"""

from typing import Optional, Tuple

import cv2
import numpy as np


def _largest_quad_from_contours(
    contours: list, min_area: float
) -> Optional[np.ndarray]:
    best_quad = None
    best_area = 0.0
    for contour in contours:
        if cv2.contourArea(contour) < min_area:
            continue
        peri = cv2.arcLength(contour, True)
        # Sweep epsilon multipliers to be tolerant
        for eps_mul in (0.01, 0.015, 0.02, 0.03, 0.05):
            approx = cv2.approxPolyDP(contour, eps_mul * peri, True)
            if len(approx) == 4:
                area = cv2.contourArea(approx)
                if area > best_area:
                    best_area = area
                    best_quad = approx
                break
        # Fallback: use minAreaRect to get a quad from non-4-vertex contours
        if best_quad is None:
            rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            area = cv2.contourArea(box)
            if area >= min_area and area > best_area:
                best_area = area
                best_quad = box.reshape(-1, 1, 2)
    return best_quad


def find_rectangle_contour(image: np.ndarray) -> Optional[np.ndarray]:
    """Robustly find a large rectangular contour in the image (BGR)."""
    try:
        h, w = image.shape[:2]
        min_area = 0.08 * (h * w)  # at least 8% of image area

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Illumination normalize
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_eq = clahe.apply(gray)

        # 1) Multi-threshold Canny + morphology closing
        threshold_pairs = [(30, 100), (50, 150), (75, 200), (100, 250)]
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        for low, high in threshold_pairs:
            edged = cv2.Canny(gray_eq, low, high)
            closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel, iterations=2)
            contours, _ = cv2.findContours(
                closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            quad = _largest_quad_from_contours(contours, min_area)
            if quad is not None:
                return quad

        # 2) Adaptive threshold + morphology
        adaptive = cv2.adaptiveThreshold(
            gray_eq, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 2
        )
        adaptive = cv2.bitwise_not(adaptive)
        adaptive = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(
            adaptive, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        quad = _largest_quad_from_contours(contours, min_area)
        if quad is not None:
            return quad

        # 3) Otsu threshold + morphology
        _, otsu = cv2.threshold(gray_eq, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        otsu = cv2.bitwise_not(otsu)
        otsu = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(otsu, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        quad = _largest_quad_from_contours(contours, min_area)
        if quad is not None:
            return quad

        return None
    except Exception:
        return None


def _order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    rect[0] = pts[np.argmin(s)]  # top-left
    rect[2] = pts[np.argmax(s)]  # bottom-right
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left
    return rect


def warp_rectangle(image: np.ndarray, contour: np.ndarray) -> np.ndarray:
    """Warp perspective to the rectangular contour area."""
    pts = contour.reshape(4, 2).astype("float32")
    rect = _order_points(pts)
    (tl, tr, br, bl) = rect

    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = int(max(widthA, widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = int(max(heightA, heightB))

    dst = np.array(
        [[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]],
        dtype="float32",
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped


def detect_and_crop_rectangle(
    image: np.ndarray,
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """Return warped rectangle image and the contour used, if any."""
    contour = find_rectangle_contour(image)
    if contour is None:
        return None, None
    return warp_rectangle(image, contour), contour
