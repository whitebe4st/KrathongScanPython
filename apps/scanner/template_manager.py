"""
Template Manager for KrathongScanner CRUD System.

This module provides CRUD operations for managing custom templates
with ArUco marker support and SQLite database integration.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from database.models import MarkerData, TemplateData
from database.registry import LocalTemplateRegistry


class TemplateManager:
    """
    Manages custom templates with CRUD operations.

    Features:
    - Template CRUD operations
    - ArUco marker ID management
    - Conflict detection and resolution
    - Database integration
    - File system management
    """

    def __init__(self, db_path: str = None):
        """
        Initialize template manager.

        Args:
            db_path: Path to SQLite database (defaults to data/db/scanner.db)
        """
        self.logger = logging.getLogger(__name__)

        # Default to scanner.db in data/db/ directory
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = str(project_root / "data" / "db" / "scanner.db")

        self.db_path = db_path
        self.registry = LocalTemplateRegistry(db_path)
        self.template_dir = Path("data/markers/templates")
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # Hardcoded template ranges (to avoid conflicts)
        self.reserved_marker_ranges = {
            "krathong1": [0, 1, 2, 3],
            "krathong2": [4, 5, 6, 7],
            "krathong3": [8, 9, 10, 11],
            "krathong4": [12, 13, 14, 15],
            "krathong5": [16, 17, 18, 19],
        }
        self.reserved_markers = set()
        for markers in self.reserved_marker_ranges.values():
            self.reserved_markers.update(markers)

        # Available range for custom templates (20-49 for 4X4_50 dictionary)
        self.custom_marker_range = list(range(20, 50))

        self.logger.info(f"Template Manager initialized with database: {db_path}")

    def create_template(
        self,
        name: str,
        template_file: str,
        mask_file: str,
        marker_ids: Optional[List[int]] = None,
        template_width: int = 1270,
        template_height: int = 720,
    ) -> bool:
        """
        Create a new custom template.

        Args:
            name: Template name
            template_file: Path to template image file
            mask_file: Path to mask file
            marker_ids: Optional list of 4 marker IDs (auto-assigned if None)
            template_width: Template width in pixels
            template_height: Template height in pixels

        Returns:
            bool: Success status
        """
        try:
            # Validate inputs
            if not name or not name.strip():
                raise ValueError("Template name cannot be empty")

            if not Path(template_file).exists():
                raise FileNotFoundError(f"Template file not found: {template_file}")

            if not Path(mask_file).exists():
                raise FileNotFoundError(f"Mask file not found: {mask_file}")

            # Check if template already exists
            if self.template_exists(name):
                raise ValueError(f"Template '{name}' already exists")

            # Assign marker IDs if not provided
            if marker_ids is None:
                marker_ids = self.get_next_available_markers()
                if not marker_ids:
                    raise ValueError("No available marker IDs for new template")
            else:
                # Validate provided marker IDs
                if len(marker_ids) != 4:
                    raise ValueError("Template must have exactly 4 marker IDs")

                if not self.validate_marker_ids(marker_ids):
                    raise ValueError("Invalid or conflicting marker IDs")

            # 🎯 Copy mask file to scanner's expected location
            scanner_mask_dir = Path("data/markers/templates")
            scanner_mask_dir.mkdir(parents=True, exist_ok=True)

            # Generate unique mask filename to avoid conflicts
            mask_filename = f"{name}_mask.png"
            scanner_mask_path = scanner_mask_dir / mask_filename

            # Copy mask file to scanner location
            import shutil

            shutil.copy2(mask_file, scanner_mask_path)
            self.logger.info(
                f"📁 Copied mask file to scanner location: {scanner_mask_path}"
            )

            # Update mask path to point to scanner location
            final_mask_path = str(scanner_mask_path)

            # Create template data
            template_data = TemplateData(
                name=name,
                marker_ids=marker_ids,
                image_path=template_file,
                mask_path=final_mask_path,  # Use scanner location
                template_width=template_width,
                template_height=template_height,
                is_active=True,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )

            # Save to database
            success = self.registry.save_template(template_data)
            if not success:
                raise RuntimeError("Failed to save template to database")

            self.logger.info(
                f"✅ Created template '{name}' with marker IDs: {marker_ids}"
            )
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to create template '{name}': {e}")
            return False

    def read_template(self, name: str) -> Optional[TemplateData]:
        """
        Read a template by name.

        Args:
            name: Template name

        Returns:
            TemplateData or None if not found
        """
        return self.registry.get_template(name)

    def read_all_templates(self, include_inactive: bool = False) -> List[TemplateData]:
        """
        Read all templates.

        Args:
            include_inactive: Whether to include inactive templates

        Returns:
            List of TemplateData
        """
        return self.registry.get_all_templates(include_inactive)

    def update_template(self, name: str, **kwargs) -> bool:
        """
        Update an existing template.

        Args:
            name: Template name
            **kwargs: Fields to update

        Returns:
            bool: Success status
        """
        try:
            template = self.read_template(name)
            if not template:
                raise ValueError(f"Template '{name}' not found")

            # Update fields
            for key, value in kwargs.items():
                if hasattr(template, key):
                    setattr(template, key, value)

            template.updated_at = datetime.now().isoformat()

            # Save updated template
            success = self.registry.save_template(template)
            if not success:
                raise RuntimeError("Failed to update template in database")

            self.logger.info(f"✅ Updated template '{name}'")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to update template '{name}': {e}")
            return False

    def delete_template(self, name: str, delete_files: bool = False) -> bool:
        """
        Delete a template.

        Args:
            name: Template name
            delete_files: Whether to delete associated files

        Returns:
            bool: Success status
        """
        try:
            template = self.read_template(name)
            if not template:
                raise ValueError(f"Template '{name}' not found")

            # Delete from database
            success = self.registry.delete_template(name)
            if not success:
                raise RuntimeError("Failed to delete template from database")

            # Optionally delete files
            if delete_files:
                try:
                    if Path(template.image_path).exists():
                        Path(template.image_path).unlink()
                    if Path(template.mask_path).exists():
                        Path(template.mask_path).unlink()
                    self.logger.info(f"🗑️ Deleted files for template '{name}'")
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to delete files for '{name}': {e}")

            self.logger.info(f"✅ Deleted template '{name}'")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to delete template '{name}': {e}")
            return False

    def template_exists(self, name: str) -> bool:
        """Check if template exists."""
        return self.read_template(name) is not None

    def validate_marker_ids(self, marker_ids: List[int]) -> bool:
        """
        Validate marker IDs for conflicts.

        Args:
            marker_ids: List of marker IDs to validate

        Returns:
            bool: True if valid
        """
        # Check for reserved markers
        for marker_id in marker_ids:
            if marker_id in self.reserved_markers:
                self.logger.error(
                    f"❌ Marker ID {marker_id} is reserved for hardcoded templates"
                )
                return False

        # Check for existing usage
        used_markers = self.get_used_marker_ids()
        for marker_id in marker_ids:
            if marker_id in used_markers:
                self.logger.error(f"❌ Marker ID {marker_id} is already in use")
                return False

        # Check range
        for marker_id in marker_ids:
            if marker_id not in self.custom_marker_range:
                self.logger.error(
                    f"❌ Marker ID {marker_id} is outside custom range (20-49)"
                )
                return False

        # Check for duplicates
        if len(marker_ids) != len(set(marker_ids)):
            self.logger.error("❌ Duplicate marker IDs found")
            return False

        return True

    def get_used_marker_ids(self) -> set:
        """Get all currently used marker IDs."""
        used_markers = set(self.reserved_markers)

        templates = self.read_all_templates(include_inactive=True)
        for template in templates:
            used_markers.update(template.marker_ids)

        return used_markers

    def get_available_marker_ids(self) -> List[int]:
        """Get available marker IDs for new templates."""
        used_markers = self.get_used_marker_ids()
        available = [mid for mid in self.custom_marker_range if mid not in used_markers]
        return sorted(available)

    def get_next_available_markers(self) -> Optional[List[int]]:
        """Get next 4 available marker IDs."""
        available = self.get_available_marker_ids()
        if len(available) >= 4:
            return available[:4]
        return None

    def import_template_from_metadata(self, metadata_file: str) -> bool:
        """
        Import template from metadata file created by template maker.

        Args:
            metadata_file: Path to metadata JSON file

        Returns:
            bool: Success status
        """
        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)

            name = metadata.get("template_name")
            marker_ids = metadata.get("aruco_ids", [])
            template_file = metadata.get("template_file")
            mask_file = metadata.get("mask_file")
            template_width = metadata.get("template_width", 1270)
            template_height = metadata.get("template_height", 720)

            return self.create_template(
                name=name,
                template_file=template_file,
                mask_file=mask_file,
                marker_ids=marker_ids,
                template_width=template_width,
                template_height=template_height,
            )

        except Exception as e:
            self.logger.error(f"❌ Failed to import template from {metadata_file}: {e}")
            return False

    def get_template_config_dict(self) -> Dict:
        """
        Get template configuration dictionary for scanner integration.

        Returns:
            Dict compatible with ArUco detector template_config.py
        """
        config = {}

        # Add hardcoded templates
        config.update(
            {
                "krathong1": {
                    "name": "Traditional Krathong (Original)",
                    "description": "Classic traditional design",
                    "markers": [0, 1, 2, 3],
                    "mask_file": "mask1_final.png",
                },
                "krathong2": {
                    "name": "Modern Krathong",
                    "description": "Contemporary modern design",
                    "markers": [4, 5, 6, 7],
                    "mask_file": "mask2_final.png",
                },
                "krathong3": {
                    "name": "Lotus Krathong",
                    "description": "Lotus flower inspired design",
                    "markers": [8, 9, 10, 11],
                    "mask_file": "mask3_final.png",
                },
                "krathong4": {
                    "name": "Royal Krathong",
                    "description": "Elegant royal design",
                    "markers": [12, 13, 14, 15],
                    "mask_file": "mask4_final.png",
                },
                "krathong5": {
                    "name": "Children Krathong",
                    "description": "Kid-friendly simple design",
                    "markers": [16, 17, 18, 19],
                    "mask_file": "krathong5_mask.png",
                },
            }
        )

        # Add custom templates
        custom_templates = self.read_all_templates()
        for template in custom_templates:
            config[f"custom_{template.name}"] = {
                "name": template.name,
                "description": f"Custom template: {template.name}",
                "markers": template.marker_ids,
                "mask_file": Path(template.mask_path).name,
            }

        return config

    def get_marker_to_template_dict(self) -> Dict[int, str]:
        """
        Get marker ID to template mapping.

        Returns:
            Dict mapping marker IDs to template names
        """
        marker_to_template = {}

        # Add hardcoded mappings
        for template_id, markers in self.reserved_marker_ranges.items():
            for marker_id in markers:
                marker_to_template[marker_id] = template_id

        # Add custom mappings
        custom_templates = self.read_all_templates()
        for template in custom_templates:
            template_key = f"custom_{template.name}"
            for marker_id in template.marker_ids:
                marker_to_template[marker_id] = template_key

        return marker_to_template

    def get_statistics(self) -> Dict:
        """Get template system statistics."""
        templates = self.read_all_templates(include_inactive=True)
        used_markers = self.get_used_marker_ids()
        available_markers = self.get_available_marker_ids()

        return {
            "total_templates": len(templates),
            "active_templates": len([t for t in templates if t.is_active]),
            "custom_templates": len(templates),
            "hardcoded_templates": len(self.reserved_marker_ranges),
            "used_markers": len(used_markers),
            "available_markers": len(available_markers),
            "reserved_markers": len(self.reserved_markers),
            "custom_marker_range": f"{min(self.custom_marker_range)}-{max(self.custom_marker_range)}",
        }


# Convenience functions for direct usage
def create_template_manager() -> TemplateManager:
    """Create a template manager instance."""
    return TemplateManager()


def import_template_from_gui(metadata_file: str) -> bool:
    """Import template created by template maker GUI."""
    manager = create_template_manager()
    return manager.import_template_from_metadata(metadata_file)


if __name__ == "__main__":
    # Test the template manager
    manager = create_template_manager()

    print("📊 Template System Statistics:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n🎯 Available Marker IDs:", manager.get_available_marker_ids()[:10])
    print("🔒 Reserved Marker IDs:", sorted(manager.reserved_markers))
