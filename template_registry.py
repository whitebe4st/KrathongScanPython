#!/usr/bin/env python3
"""
Template Registry System

Manages ArUco marker ID allocation and template tracking to prevent conflicts
and ensure unique marker combinations for each client template.

Features:
- Automatic unique ID assignment
- Conflict prevention
- Template tracking and management
- Client template organization
- Registry persistence
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """
    Manages template registration and ArUco marker ID allocation.

    Prevents conflicts by ensuring each template has a unique combination
    of marker IDs and tracks all created templates.
    """

    def __init__(self, registry_file: str = "data/template_registry.json"):
        """
        Initialize the template registry.

        Args:
            registry_file: Path to the registry JSON file
        """
        self.registry_file = Path(registry_file)
        self.registry_data = {}
        self.load_registry()

    def load_registry(self):
        """Load registry from file or create new if doesn't exist."""
        try:
            if self.registry_file.exists():
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    self.registry_data = json.load(f)
                logger.info(
                    f"Registry loaded: {len(self.registry_data.get('templates', {}))} templates"
                )
            else:
                self.create_empty_registry()
                logger.info("Created new template registry")
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            self.create_empty_registry()

    def create_empty_registry(self):
        """Create an empty registry structure."""
        self.registry_data = {
            "registry_info": {
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_templates": 0,
                "next_available_id_set": [0, 1, 2, 3],
            },
            "templates": {},
            "id_allocation": {"used_combinations": [], "next_id_sequence": 0},
        }

    def save_registry(self):
        """Save registry to file."""
        try:
            # Ensure directory exists
            self.registry_file.parent.mkdir(parents=True, exist_ok=True)

            # Update metadata
            self.registry_data["registry_info"][
                "last_updated"
            ] = datetime.now().isoformat()
            self.registry_data["registry_info"]["total_templates"] = len(
                self.registry_data["templates"]
            )

            # Save to file
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(self.registry_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Registry saved: {self.registry_file}")

        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
            raise

    def get_next_unique_ids(self) -> List[int]:
        """
        Get the next available unique set of 4 ArUco marker IDs.

        Returns:
            List of 4 unique marker IDs

        Raises:
            ValueError: If no more valid combinations are available
        """
        # ArUco 4x4_50 dictionary supports markers 0-49
        MAX_MARKER_ID = 49

        # Get next sequence number
        next_seq = self.registry_data["id_allocation"]["next_id_sequence"]

        # Check if we can fit 4 consecutive IDs within the limit
        if next_seq + 3 > MAX_MARKER_ID:
            # Try to find gaps in used combinations or reset to a lower sequence
            available_start = self._find_available_sequence_start()
            if available_start is None:
                raise ValueError(
                    f"No more unique 4-marker combinations available within ArUco 4x4_50 range (0-{MAX_MARKER_ID}). "
                    f"Consider using overlapping combinations or a larger ArUco dictionary."
                )
            next_seq = available_start

        # Generate 4 consecutive IDs starting from next_seq
        marker_ids = [next_seq, next_seq + 1, next_seq + 2, next_seq + 3]

        # Ensure all IDs are within valid range
        if max(marker_ids) > MAX_MARKER_ID:
            raise ValueError(
                f"Cannot assign marker IDs {marker_ids}: exceeds ArUco 4x4_50 limit (0-{MAX_MARKER_ID})"
            )

        # Update sequence for next allocation (reserve some gaps for safety)
        # But don't go beyond the limit
        next_increment = min(next_seq + 10, MAX_MARKER_ID - 3)
        self.registry_data["id_allocation"]["next_id_sequence"] = next_increment

        # Update next available info
        if next_increment + 3 <= MAX_MARKER_ID:
            self.registry_data["registry_info"]["next_available_id_set"] = [
                next_increment,
                next_increment + 1,
                next_increment + 2,
                next_increment + 3,
            ]
        else:
            # No more sequences available
            self.registry_data["registry_info"]["next_available_id_set"] = [
                -1,
                -1,
                -1,
                -1,
            ]

        logger.info(f"Allocated unique marker IDs: {marker_ids}")
        return marker_ids

    def _find_available_sequence_start(self) -> Optional[int]:
        """
        Find the next available starting position for a 4-marker sequence.

        Returns:
            Starting position or None if no sequence available
        """
        MAX_MARKER_ID = 49
        used_combinations = self.registry_data["id_allocation"]["used_combinations"]

        # Convert used combinations to a set of individual used IDs
        used_ids = set()
        for combo in used_combinations:
            used_ids.update(combo)

        # Look for 4 consecutive available IDs
        for start in range(0, MAX_MARKER_ID - 2, 10):  # Check every 10 positions
            sequence = [start, start + 1, start + 2, start + 3]
            if (
                all(id not in used_ids for id in sequence)
                and max(sequence) <= MAX_MARKER_ID
            ):
                return start

        return None

    def is_id_combination_available(self, marker_ids: List[int]) -> bool:
        """
        Check if a combination of marker IDs is available.

        Args:
            marker_ids: List of marker IDs to check

        Returns:
            True if combination is available, False if already used
        """
        used_combinations = self.registry_data["id_allocation"]["used_combinations"]

        # Sort both lists for comparison
        sorted_ids = sorted(marker_ids)

        for used_combo in used_combinations:
            if sorted(used_combo) == sorted_ids:
                return False

        return True

    def register_template(
        self,
        template_name: str,
        marker_ids: List[int],
        client_name: str = "",
        template_file_path: str = "",
        mask_file_path: str = "",
        image_settings: Optional[Dict] = None,
    ) -> bool:
        """
        Register a new template in the registry.

        Args:
            template_name: Name of the template
            marker_ids: List of ArUco marker IDs used
            client_name: Name of the client (optional)
            template_file_path: Path to template PNG file
            mask_file_path: Path to mask file (optional)
            image_settings: Image settings used (scale, offset, etc.)

        Returns:
            True if registration successful, False if IDs already used
        """
        # Check if IDs are available
        if not self.is_id_combination_available(marker_ids):
            logger.warning(f"Marker IDs {marker_ids} already in use")
            return False

        # Check if template name already exists
        if template_name in self.registry_data["templates"]:
            logger.warning(f"Template name '{template_name}' already exists")
            return False

        # Register the template
        template_entry = {
            "marker_ids": sorted(marker_ids),
            "created_date": datetime.now().isoformat(),
            "client": client_name,
            "status": "active",
            "template_file_path": template_file_path,
            "mask_file_path": mask_file_path,
            "image_settings": image_settings or {},
        }

        # Add to registry
        self.registry_data["templates"][template_name] = template_entry
        self.registry_data["id_allocation"]["used_combinations"].append(
            sorted(marker_ids)
        )

        # Save registry
        self.save_registry()

        logger.info(f"Template '{template_name}' registered with IDs {marker_ids}")
        return True

    def unregister_template(self, template_name: str) -> bool:
        """
        Remove a template from the registry (delete, not archive).

        Args:
            template_name: Name of template to remove

        Returns:
            True if removal successful, False if template not found
        """
        if template_name not in self.registry_data["templates"]:
            logger.warning(f"Template '{template_name}' not found in registry")
            return False

        # Get marker IDs before removal
        template_data = self.registry_data["templates"][template_name]
        marker_ids = template_data["marker_ids"]

        # Remove template
        del self.registry_data["templates"][template_name]

        # Remove from used combinations
        used_combinations = self.registry_data["id_allocation"]["used_combinations"]
        self.registry_data["id_allocation"]["used_combinations"] = [
            combo for combo in used_combinations if sorted(combo) != sorted(marker_ids)
        ]

        # Save registry
        self.save_registry()

        logger.info(f"Template '{template_name}' removed from registry")
        return True

    def get_template_by_marker_ids(self, detected_ids: List[int]) -> Optional[str]:
        """
        Find template name by detected marker IDs.

        Args:
            detected_ids: List of detected ArUco marker IDs

        Returns:
            Template name if found, None if no match
        """
        sorted_detected = sorted(detected_ids)

        for template_name, template_data in self.registry_data["templates"].items():
            if template_data["status"] == "active":
                template_ids = sorted(template_data["marker_ids"])
                if template_ids == sorted_detected:
                    logger.info(
                        f"Template matched: '{template_name}' for IDs {detected_ids}"
                    )
                    return template_name

        logger.info(f"No template found for marker IDs: {detected_ids}")
        return None

    def get_template_info(self, template_name: str) -> Optional[Dict]:
        """
        Get full information about a template.

        Args:
            template_name: Name of the template

        Returns:
            Template data dictionary or None if not found
        """
        return self.registry_data["templates"].get(template_name)

    def list_all_templates(self) -> Dict[str, Dict]:
        """
        Get all registered templates.

        Returns:
            Dictionary of template_name -> template_data
        """
        return self.registry_data["templates"].copy()

    def list_active_templates(self) -> Dict[str, Dict]:
        """
        Get only active templates.

        Returns:
            Dictionary of active template_name -> template_data
        """
        return {
            name: data
            for name, data in self.registry_data["templates"].items()
            if data["status"] == "active"
        }

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry statistics
        """
        templates = self.registry_data["templates"]
        active_count = sum(1 for t in templates.values() if t["status"] == "active")

        return {
            "total_templates": len(templates),
            "active_templates": active_count,
            "next_available_ids": self.registry_data["registry_info"][
                "next_available_id_set"
            ],
            "total_id_combinations_used": len(
                self.registry_data["id_allocation"]["used_combinations"]
            ),
            "last_updated": self.registry_data["registry_info"]["last_updated"],
        }

    def suggest_template_name(self, client_name: str = "") -> str:
        """
        Suggest a template name based on client and date.

        Args:
            client_name: Name of the client

        Returns:
            Suggested template name
        """
        # Clean client name
        clean_client = "".join(
            c for c in client_name if c.isalnum() or c in "_-"
        ).lower()
        if not clean_client:
            clean_client = "template"

        # Add date
        date_str = datetime.now().strftime("%Y%m%d")
        base_name = f"{clean_client}_{date_str}"

        # Ensure uniqueness
        counter = 1
        suggested_name = base_name
        while suggested_name in self.registry_data["templates"]:
            suggested_name = f"{base_name}_{counter:02d}"
            counter += 1

        return suggested_name

    def export_template_list(self, output_file: str = "template_list.json") -> bool:
        """
        Export template list for external use.

        Args:
            output_file: Path to output file

        Returns:
            True if export successful
        """
        try:
            export_data = {
                "export_date": datetime.now().isoformat(),
                "total_templates": len(self.registry_data["templates"]),
                "templates": [],
            }

            for name, data in self.registry_data["templates"].items():
                if data["status"] == "active":
                    export_data["templates"].append(
                        {
                            "name": name,
                            "marker_ids": data["marker_ids"],
                            "client": data["client"],
                            "created_date": data["created_date"],
                            "template_file": data["template_file_path"],
                        }
                    )

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Template list exported to: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False


# Convenience functions for global registry instance
_global_registry = None


def get_registry() -> TemplateRegistry:
    """Get the global template registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = TemplateRegistry()
    return _global_registry


def register_template(template_name: str, marker_ids: List[int], **kwargs) -> bool:
    """Convenience function to register a template."""
    return get_registry().register_template(template_name, marker_ids, **kwargs)


def get_next_unique_ids() -> List[int]:
    """Convenience function to get next unique marker IDs."""
    return get_registry().get_next_unique_ids()


def find_template_by_markers(marker_ids: List[int]) -> Optional[str]:
    """Convenience function to find template by marker IDs."""
    return get_registry().get_template_by_marker_ids(marker_ids)


if __name__ == "__main__":
    # Test the registry
    registry = TemplateRegistry("test_registry.json")

    # Test auto-allocation
    print("🎯 Testing Template Registry")

    # Get unique IDs
    ids1 = registry.get_next_unique_ids()
    print(f"First allocation: {ids1}")

    ids2 = registry.get_next_unique_ids()
    print(f"Second allocation: {ids2}")

    # Register templates
    registry.register_template("festival_2025", ids1, client_name="Festival Committee")
    registry.register_template("corporate_event", ids2, client_name="Corp Ltd")

    # Test lookup
    found = registry.get_template_by_marker_ids(ids1)
    print(f"Template found for {ids1}: {found}")

    # Show stats
    stats = registry.get_registry_stats()
    print(f"Registry stats: {stats}")

    print("✅ Registry tests completed")
