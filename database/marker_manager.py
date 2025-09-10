"""
Marker ID management for ArUco markers.
"""

from typing import Any, Dict, List, Optional, Set

from .models import MarkerData
from .registry import LocalTemplateRegistry


class MarkerIDManager:
    """Manages ArUco marker ID assignment and tracking."""

    def __init__(self, db_path: str = "data/templates.db"):
        self.db_path = db_path
        self.registry = LocalTemplateRegistry(db_path)
        self.used_ids: Set[int] = set()
        self.load_used_ids()

    def load_used_ids(self):
        """Load used marker IDs from database."""
        self.used_ids = set(self.registry.get_used_marker_ids())

    def get_next_available_ids(self, count: int = 4) -> List[int]:
        """Get next available sequential marker IDs."""
        available_ids = []

        for marker_id in range(50):  # 4x4_50 dictionary has IDs 0-49
            if marker_id not in self.used_ids:
                available_ids.append(marker_id)
                if len(available_ids) >= count:
                    break

        return available_ids

    def reserve_ids(self, marker_ids: List[int], template_name: str) -> bool:
        """Reserve marker IDs for a template."""
        try:
            # Check if any IDs are already used
            conflicting_ids = [mid for mid in marker_ids if mid in self.used_ids]
            if conflicting_ids:
                print(f"Warning: Marker IDs {conflicting_ids} are already in use")
                return False

            # Add to used set
            self.used_ids.update(marker_ids)

            # Save to database
            for marker_id in marker_ids:
                marker_data = MarkerData(
                    marker_id=marker_id, template_name=template_name, is_used=True
                )
                # This will be handled by the registry when saving the template
                # We just update our local tracking here

            return True

        except Exception as e:
            print(f"Error reserving marker IDs: {e}")
            return False

    def release_ids(self, marker_ids: List[int], template_name: str) -> bool:
        """Release marker IDs from a template."""
        try:
            # Remove from used set
            for marker_id in marker_ids:
                self.used_ids.discard(marker_id)

            # Update database
            with self.registry.registry as conn:
                cursor = conn.cursor()
                for marker_id in marker_ids:
                    cursor.execute(
                        "UPDATE markers SET is_used = 0 WHERE marker_id = ? AND template_name = ?",
                        (marker_id, template_name),
                    )
                conn.commit()

            return True

        except Exception as e:
            print(f"Error releasing marker IDs: {e}")
            return False

    def get_template_assignments(self) -> Dict[str, List[int]]:
        """Get all template assignments with their marker IDs."""
        try:
            import sqlite3

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT template_name, marker_id
                    FROM markers
                    WHERE is_used = 1
                    ORDER BY template_name, marker_id
                """
                )

                assignments = {}
                for row in cursor.fetchall():
                    template_name, marker_id = row
                    if template_name not in assignments:
                        assignments[template_name] = []
                    assignments[template_name].append(marker_id)

                return assignments

        except Exception as e:
            print(f"Error getting template assignments: {e}")
            return {}

    def validate_marker_ids(self, marker_ids: List[int]) -> Dict[str, Any]:
        """Validate marker IDs for a template."""
        validation_result = {"is_valid": True, "errors": [], "warnings": []}

        # Check count
        if len(marker_ids) != 4:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                "Template must have exactly 4 marker IDs"
            )

        # Check range
        for marker_id in marker_ids:
            if not (0 <= marker_id <= 49):
                validation_result["is_valid"] = False
                validation_result["errors"].append(
                    f"Marker ID {marker_id} is out of range (0-49)"
                )

        # Check duplicates
        if len(marker_ids) != len(set(marker_ids)):
            validation_result["is_valid"] = False
            validation_result["errors"].append("Duplicate marker IDs found")

        # Check availability
        conflicting_ids = [mid for mid in marker_ids if mid in self.used_ids]
        if conflicting_ids:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"Marker IDs {conflicting_ids} are already in use"
            )

        return validation_result

    def get_availability_summary(self) -> Dict[str, Any]:
        """Get summary of marker ID availability."""
        used_count = len(self.used_ids)
        available_count = 50 - used_count
        used_templates = len(self.get_template_assignments())

        return {
            "total_markers": 50,
            "used_markers": used_count,
            "available_markers": available_count,
            "used_templates": used_templates,
            "used_ids": sorted(list(self.used_ids)),
            "available_ids": sorted([i for i in range(50) if i not in self.used_ids]),
        }
