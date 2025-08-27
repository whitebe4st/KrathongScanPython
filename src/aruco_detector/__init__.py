"""
ArUco Marker Detection Module.

This module provides functionality for:
- Real-time ArUco marker detection
- Pose estimation and tracking
- Camera calibration and management
- Marker data processing and validation
"""

from .camera import CameraManager
from .detector import ArUcoDetector
from .marker import MarkerData, MarkerPose

__all__ = ["ArUcoDetector", "CameraManager", "MarkerData", "MarkerPose"]
