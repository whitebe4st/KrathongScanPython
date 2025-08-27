"""
Pytest configuration and common fixtures.

This file provides shared test fixtures and configuration
for all test modules.
"""

import asyncio

# Add src to Python path for imports
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_camera():
    """Mock camera for testing."""
    camera = Mock()
    camera.read.return_value = (True, Mock())  # (success, frame)
    camera.isOpened.return_value = True
    return camera


@pytest.fixture
def mock_websocket_connection():
    """Mock WebSocket connection for testing."""
    connection = Mock()
    connection.send = Mock()
    connection.close = Mock()
    return connection


@pytest.fixture
def sample_marker_data():
    """Sample marker data for testing."""
    return {
        "id": 1,
        "corners": [[100, 100], [200, 100], [200, 200], [100, 200]],
        "center": [150, 150],
        "pose": {"translation": [0.1, 0.2, 0.5], "rotation": [0, 0, 0]},
    }


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
