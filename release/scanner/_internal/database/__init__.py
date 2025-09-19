"""
Database management for KrathongScanner applications.
"""

from .marker_manager import MarkerIDManager
from .models import MarkerData, TemplateData
from .registry import LocalTemplateRegistry

__all__ = ["LocalTemplateRegistry", "MarkerIDManager", "TemplateData", "MarkerData"]
