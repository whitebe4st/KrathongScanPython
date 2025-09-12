"""
Local template registry for managing templates in SQLite database.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import TemplateData


class LocalTemplateRegistry:
    """Manages template data in local SQLite database."""

    def __init__(self, db_path: str = "scanner.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database and create tables."""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create templates table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    marker_ids TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    mask_path TEXT NOT NULL,
                    template_width INTEGER DEFAULT 1270,
                    template_height INTEGER DEFAULT 720,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

            # Create markers table for tracking usage
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS markers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    marker_id INTEGER NOT NULL,
                    template_name TEXT NOT NULL,
                    is_used BOOLEAN DEFAULT 1,
                    created_at TEXT NOT NULL,
                    UNIQUE(marker_id, template_name)
                )
            """
            )

            conn.commit()

    def save_template(self, template_data: TemplateData) -> bool:
        """Save template to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Insert or replace template
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO templates
                    (name, marker_ids, image_path, mask_path, template_width,
                     template_height, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        template_data.name,
                        json.dumps(template_data.marker_ids),
                        template_data.image_path,
                        template_data.mask_path,
                        template_data.template_width,
                        template_data.template_height,
                        template_data.is_active,
                        template_data.created_at
                        or template_data.to_dict()["created_at"],
                        template_data.updated_at
                        or template_data.to_dict()["updated_at"],
                    ),
                )

                # Update marker usage
                for marker_id in template_data.marker_ids:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO markers
                        (marker_id, template_name, is_used, created_at)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            marker_id,
                            template_data.name,
                            True,
                            template_data.created_at
                            or template_data.to_dict()["created_at"],
                        ),
                    )

                conn.commit()
                return True

        except Exception as e:
            print(f"Error saving template: {e}")
            return False

    def get_templates(self) -> List[TemplateData]:
        """Get all templates from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM templates ORDER BY created_at DESC")

                templates = []
                for row in cursor.fetchall():
                    template_dict = {
                        "name": row[1],
                        "marker_ids": row[2],
                        "image_path": row[3],
                        "mask_path": row[4],
                        "template_width": row[5],
                        "template_height": row[6],
                        "is_active": row[7],
                        "created_at": row[8],
                        "updated_at": row[9],
                    }
                    templates.append(TemplateData.from_dict(template_dict))

                return templates

        except Exception as e:
            print(f"Error getting templates: {e}")
            return []

    def get_template_by_name(self, name: str) -> Optional[TemplateData]:
        """Get template by name."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM templates WHERE name = ?", (name,))
                row = cursor.fetchone()

                if row:
                    template_dict = {
                        "name": row[1],
                        "marker_ids": row[2],
                        "image_path": row[3],
                        "mask_path": row[4],
                        "template_width": row[5],
                        "template_height": row[6],
                        "is_active": row[7],
                        "created_at": row[8],
                        "updated_at": row[9],
                    }
                    return TemplateData.from_dict(template_dict)

                return None

        except Exception as e:
            print(f"Error getting template by name: {e}")
            return None

    def delete_template(self, name: str) -> bool:
        """Delete template from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Delete template
                cursor.execute("DELETE FROM templates WHERE name = ?", (name,))

                # Delete associated markers
                cursor.execute("DELETE FROM markers WHERE template_name = ?", (name,))

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            print(f"Error deleting template: {e}")
            return False

    def get_used_marker_ids(self) -> List[int]:
        """Get all used marker IDs."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT marker_id FROM markers WHERE is_used = 1"
                )

                return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            print(f"Error getting used marker IDs: {e}")
            return []

    def get_available_marker_ids(self, count: int = 4) -> List[int]:
        """Get available marker IDs (20-49 for 4x4_50 dictionary, 0-19 reserved for hardcoded templates)."""
        used_ids = set(self.get_used_marker_ids())
        available_ids = []

        # Start from 20 since 0-19 are reserved for hardcoded templates
        for marker_id in range(
            20, 50
        ):  # 4x4_50 dictionary has IDs 0-49, but 0-19 are reserved
            if marker_id not in used_ids:
                available_ids.append(marker_id)
                if len(available_ids) >= count:
                    break

        return available_ids

    def get_all_templates(self, include_inactive: bool = False) -> List[TemplateData]:
        """Get all templates from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if include_inactive:
                    cursor.execute("SELECT * FROM templates ORDER BY name")
                else:
                    cursor.execute(
                        "SELECT * FROM templates WHERE is_active = 1 ORDER BY name"
                    )

                templates = []
                for row in cursor.fetchall():
                    template_dict = {
                        "name": row[1],
                        "marker_ids": row[2],
                        "image_path": row[3],
                        "mask_path": row[4],
                        "template_width": row[5],
                        "template_height": row[6],
                        "is_active": row[7],
                        "created_at": row[8],
                        "updated_at": row[9],
                    }
                    templates.append(TemplateData.from_dict(template_dict))

                return templates

        except Exception as e:
            print(f"Error getting all templates: {e}")
            return []

    def get_template(self, name: str) -> Optional[TemplateData]:
        """Get template by name (alias for get_template_by_name)."""
        return self.get_template_by_name(name)

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics compatible with template_maker_gui."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get total templates count
                cursor.execute("SELECT COUNT(*) FROM templates")
                total_templates = cursor.fetchone()[0]

                # Get active templates count
                cursor.execute("SELECT COUNT(*) FROM templates WHERE is_active = 1")
                active_templates = cursor.fetchone()[0]

                # Get next available IDs
                available_ids = self.get_available_marker_ids(4)
                next_available_ids = (
                    available_ids[:4] if len(available_ids) >= 4 else available_ids
                )

                # Get used combinations count
                cursor.execute(
                    "SELECT COUNT(DISTINCT template_name) FROM markers WHERE is_used = 1"
                )
                used_combinations = cursor.fetchone()[0]

                return {
                    "total_templates": total_templates,
                    "active_templates": active_templates,
                    "next_available_ids": next_available_ids,
                    "total_id_combinations_used": used_combinations,
                    "last_updated": self._get_last_updated(),
                }

        except Exception as e:
            print(f"Error getting registry stats: {e}")
            return {
                "total_templates": 0,
                "active_templates": 0,
                "next_available_ids": [],
                "total_id_combinations_used": 0,
                "last_updated": "",
            }

    def get_next_unique_ids(self) -> List[int]:
        """Get next available unique marker IDs for template creation (excluding reserved range 0-19)."""
        available_ids = self.get_available_marker_ids(4)
        if len(available_ids) < 4:
            raise ValueError(
                f"Only {len(available_ids)} marker IDs available in range 20-49. "
                f"Need 4 for template creation. IDs 0-19 are reserved for hardcoded templates. "
                f"Consider using overlapping combinations or deactivating old templates to free up marker IDs."
            )
        return available_ids[:4]

    def is_id_combination_available(self, marker_ids: List[int]) -> bool:
        """Check if a combination of marker IDs is available (not used by any active template and not in reserved range)."""
        try:
            # Check if any marker ID is in the reserved range (0-19)
            reserved_ids = [id for id in marker_ids if 0 <= id <= 19]
            if reserved_ids:
                print(
                    f"⚠️ Marker IDs {reserved_ids} are in reserved range (0-19) for hardcoded templates"
                )
                return False

            # Check if any marker ID is outside the valid range (20-49)
            invalid_ids = [id for id in marker_ids if id < 20 or id > 49]
            if invalid_ids:
                print(f"⚠️ Marker IDs {invalid_ids} are outside valid range (20-49)")
                return False

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if any of these marker IDs are used by active templates
                placeholders = ",".join("?" * len(marker_ids))
                cursor.execute(
                    f"""
                    SELECT COUNT(*) FROM markers m
                    JOIN templates t ON m.template_name = t.name
                    WHERE m.marker_id IN ({placeholders})
                    AND m.is_used = 1
                    AND t.is_active = 1
                """,
                    marker_ids,
                )

                used_count = cursor.fetchone()[0]
                return used_count == 0

        except Exception as e:
            print(f"Error checking marker availability: {e}")
            return False

    def register_template(
        self,
        template_name: str,
        marker_ids: List[int],
        template_file: str = "",
        mask_file: str = "",
        metadata_file: str = "",
        **kwargs,
    ) -> bool:
        """Register a new template with the given marker IDs."""
        try:
            from datetime import datetime

            from .models import TemplateData

            # Create template data object
            template_data = TemplateData(
                name=template_name,
                marker_ids=marker_ids,
                image_path=template_file,
                mask_path=mask_file or "",
                template_width=kwargs.get("template_width", 1270),
                template_height=kwargs.get("template_height", 720),
                is_active=True,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )

            # Save to database
            success = self.save_template(template_data)
            if success:
                print(f"✅ Template '{template_name}' registered in SQLite database")
                return True
            else:
                print(f"❌ Failed to register template '{template_name}' in database")
                return False

        except Exception as e:
            print(f"❌ Error registering template: {e}")
            return False

    def _get_last_updated(self) -> str:
        """Get the last updated timestamp from templates."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(updated_at) FROM templates")
                result = cursor.fetchone()
                return result[0] if result and result[0] else ""
        except:
            return ""
