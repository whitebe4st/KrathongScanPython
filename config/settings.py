"""
Configuration settings for KrathongScanner.

This module provides centralized configuration management
for all components of the system.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class ArUcoConfig:
    """ArUco detection configuration."""

    dict_type: str = os.getenv("ARUCO_DICT_TYPE", "4X4_50")
    marker_size: float = float(os.getenv("ARUCO_MARKER_SIZE", "0.04"))
    marker_separation: float = float(os.getenv("ARUCO_MARKER_SEPARATION", "0.01"))
    camera_index: int = int(os.getenv("CAMERA_INDEX", "0"))
    camera_width: int = int(os.getenv("CAMERA_WIDTH", "640"))
    camera_height: int = int(os.getenv("CAMERA_HEIGHT", "480"))
    camera_fps: int = int(os.getenv("CAMERA_FPS", "30"))


@dataclass
class WebSocketConfig:
    """WebSocket API configuration."""

    host: str = os.getenv("WEBSOCKET_HOST", "localhost")
    port: int = int(os.getenv("WEBSOCKET_PORT", "8765"))
    max_connections: int = int(os.getenv("WEBSOCKET_MAX_CONNECTIONS", "10"))
    heartbeat_interval: int = int(os.getenv("WEBSOCKET_HEARTBEAT_INTERVAL", "30"))


@dataclass
class UnityConfig:
    """Unity integration configuration."""

    client_timeout: int = int(os.getenv("UNITY_CLIENT_TIMEOUT", "60"))
    max_reconnect_attempts: int = int(os.getenv("UNITY_MAX_RECONNECT_ATTEMPTS", "5"))


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = os.getenv("LOG_LEVEL", "INFO")
    file: str = os.getenv("LOG_FILE", "logs/krathong_scanner.log")
    max_size: str = os.getenv("LOG_MAX_SIZE", "10MB")
    backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))


@dataclass
class PerformanceConfig:
    """Performance configuration."""

    detection_interval: float = float(os.getenv("DETECTION_INTERVAL", "0.033"))
    pose_estimation_enabled: bool = (
        os.getenv("POSE_ESTIMATION_ENABLED", "true").lower() == "true"
    )
    multi_marker_detection: bool = (
        os.getenv("MULTI_MARKER_DETECTION", "true").lower() == "true"
    )


@dataclass
class Config:
    """Main configuration class."""

    app_name: str = os.getenv("APP_NAME", "KrathongScanner")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    aruco: ArUcoConfig = ArUcoConfig()
    websocket: WebSocketConfig = WebSocketConfig()
    unity: UnityConfig = UnityConfig()
    logging: LoggingConfig = LoggingConfig()
    performance: PerformanceConfig = PerformanceConfig()

    def __post_init__(self):
        """Post-initialization setup."""
        # Ensure log directory exists
        log_dir = Path(self.logging.file).parent
        log_dir.mkdir(parents=True, exist_ok=True)


# Global configuration instance
config = Config()
