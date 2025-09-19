"""
Database models for KrathongScanner.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class TemplateData:
    """Template data structure."""

    name: str
    marker_ids: List[int]
    image_path: str
    mask_path: str
    template_width: int = 1270
    template_height: int = 720
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "name": self.name,
            "marker_ids": json.dumps(self.marker_ids),
            "image_path": self.image_path,
            "mask_path": self.mask_path,
            "template_width": self.template_width,
            "template_height": self.template_height,
            "is_active": self.is_active,
            "created_at": self.created_at or datetime.now().isoformat(),
            "updated_at": self.updated_at or datetime.now().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TemplateData":
        """Create from dictionary from database."""
        return cls(
            name=data["name"],
            marker_ids=json.loads(data["marker_ids"]),
            image_path=data["image_path"],
            mask_path=data["mask_path"],
            template_width=data["template_width"],
            template_height=data["template_height"],
            is_active=bool(data["is_active"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


@dataclass
class MarkerData:
    """Marker data structure."""

    marker_id: int
    template_name: str
    is_used: bool = True
    created_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "marker_id": self.marker_id,
            "template_name": self.template_name,
            "is_used": self.is_used,
            "created_at": self.created_at or datetime.now().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MarkerData":
        """Create from dictionary from database."""
        return cls(
            marker_id=data["marker_id"],
            template_name=data["template_name"],
            is_used=bool(data["is_used"]),
            created_at=data["created_at"],
        )
