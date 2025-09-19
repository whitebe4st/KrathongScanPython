"""
Automated Mask Generator Module.

This module provides functionality for generating perfect template masks
optimized for the universal cropping system.
"""

from .converter import MaskConverter
from .generator import PerfectMaskGenerator

__all__ = ["PerfectMaskGenerator", "MaskConverter"]
