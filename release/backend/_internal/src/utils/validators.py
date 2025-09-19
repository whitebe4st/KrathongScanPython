"""
Data validation utilities for KrathongScanner.

This module provides:
- Marker data validation
- Input sanitization
- Data type checking
"""

import re
from typing import Any, Dict, List, Optional, Union


def validate_marker_data(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate ArUco marker data.

    Args:
        data: Dictionary containing marker data

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check required fields
    required_fields = ["id", "dict_type"]
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Validate marker ID
    if "id" in data:
        marker_id = data["id"]
        if not isinstance(marker_id, int) or marker_id < 0:
            errors.append("Marker ID must be a non-negative integer")

    # Validate dictionary type
    if "dict_type" in data:
        dict_type = data["dict_type"]
        if not isinstance(dict_type, str):
            errors.append("Dictionary type must be a string")
        elif not re.match(r"^\d+X\d+_\d+$", dict_type):
            errors.append("Dictionary type must be in format: NXN_M (e.g., 4X4_50)")

    # Validate marker size (if present)
    if "marker_size" in data:
        marker_size = data["marker_size"]
        if not isinstance(marker_size, (int, float)) or marker_size <= 0:
            errors.append("Marker size must be a positive number")

    # Validate border bits (if present)
    if "border_bits" in data:
        border_bits = data["border_bits"]
        if not isinstance(border_bits, int) or border_bits < 0:
            errors.append("Border bits must be a non-negative integer")

    return len(errors) == 0, errors


def validate_websocket_message(
    message: Union[str, bytes]
) -> tuple[bool, Optional[str]]:
    """
    Validate WebSocket message format.

    Args:
        message: WebSocket message to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if isinstance(message, bytes):
        try:
            message = message.decode("utf-8")
        except UnicodeDecodeError:
            return False, "Message could not be decoded as UTF-8"

    if not isinstance(message, str):
        return False, "Message must be a string or bytes"

    if len(message.strip()) == 0:
        return False, "Message cannot be empty"

    # Check if it's valid JSON (basic check)
    try:
        import json

        json.loads(message)
        return True, None
    except json.JSONDecodeError:
        return False, "Message must be valid JSON"

    return True, None


def validate_camera_settings(settings: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate camera settings.

    Args:
        settings: Dictionary containing camera settings

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Validate camera index
    if "camera_index" in settings:
        camera_index = settings["camera_index"]
        if not isinstance(camera_index, int) or camera_index < 0:
            errors.append("Camera index must be a non-negative integer")

    # Validate resolution
    if "width" in settings:
        width = settings["width"]
        if not isinstance(width, int) or width <= 0:
            errors.append("Camera width must be a positive integer")

    if "height" in settings:
        height = settings["height"]
        if not isinstance(height, int) or height <= 0:
            errors.append("Camera height must be a positive integer")

    # Validate FPS
    if "fps" in settings:
        fps = settings["fps"]
        if not isinstance(fps, (int, float)) or fps <= 0:
            errors.append("Camera FPS must be a positive number")

    return len(errors) == 0, errors


def sanitize_string(input_string: str, max_length: int = 1000) -> str:
    """
    Sanitize input string.

    Args:
        input_string: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not isinstance(input_string, str):
        return ""

    # Remove null bytes and control characters
    sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", input_string)

    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized.strip()
