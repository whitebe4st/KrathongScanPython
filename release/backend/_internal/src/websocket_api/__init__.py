"""
WebSocket API Module for Unity Integration.

This module provides:
- WebSocket server for real-time communication
- API endpoints for marker data
- Client connection management
- Data serialization and validation
"""

from .client import WebSocketClient
from .handlers import MessageHandler
from .server import WebSocketServer

__all__ = ["WebSocketServer", "WebSocketClient", "MessageHandler"]
