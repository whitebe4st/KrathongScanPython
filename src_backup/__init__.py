"""
KrathongScanner - ArUco marker detection with WebSocket API for Unity.

This package provides:
- ArUco marker detection and pose estimation
- ArUco marker generation and validation
- WebSocket API server for real-time communication
- Utilities for computer vision and networking
"""

__version__ = "1.0.0"
__author__ = "Your Team"
__email__ = "your.email@example.com"

from . import aruco_detector, aruco_generator, utils

__all__ = ["aruco_detector", "aruco_generator", "utils"]
