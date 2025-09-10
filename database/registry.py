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
        """Get available marker IDs (0-49 for 4x4_50 dictionary)."""
        used_ids = set(self.get_used_marker_ids())
        available_ids = []

        for marker_id in range(50):  # 4x4_50 dictionary has IDs 0-49
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
