"""
ArUco Detection Module.

This module provides functionality for:
- ArUco marker detection and pose estimation
- Perspective correction using homography
- Template masking for drawing extraction
- Metadata generation and result saving
"""

from .detector import ArUcoDetector, MarkerData, MarkerPose

__all__ = ["ArUcoDetector", "MarkerData", "MarkerPose"]
