"""
Export functionality for Template Maker application.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from core.aruco_utils import ArucoUtils
from core.template_maker import KrathongTemplateMaker
from database.models import TemplateData
from utils.config import Config
from utils.file_utils import FileUtils


class TemplateExporter:
    """Handles template package export for admin app."""

    def __init__(self):
        """Initialize template exporter."""
        self.template_maker = KrathongTemplateMaker()
        self.aruco_utils = ArucoUtils()
        self.file_utils = FileUtils()

    def export_template_package(
        self,
        template_data: TemplateData,
        krathong_image: Optional[np.ndarray] = None,
        mask_image: Optional[np.ndarray] = None,
    ) -> bool:
        """
        Export complete template package for admin app.

        Args:
            template_data: Template data including name, marker IDs, etc.
            krathong_image: Optional krathong image to include
            mask_image: Optional mask image to include

        Returns:
            True if export successful, False otherwise
        """
        try:
            # Create export directory
            export_dir = Config.EXPORTS_DIR / template_data.name
            export_dir.mkdir(parents=True, exist_ok=True)

            # Export template image
            template_image = self.template_maker.create_template_image(
                template_data.marker_ids, krathong_image
            )
            template_path = export_dir / f"{template_data.name}_template.png"
            cv2.imwrite(str(template_path), template_image)

            # Export mask if provided
            if mask_image is not None:
                mask_path = export_dir / f"{template_data.name}_mask.png"
                cv2.imwrite(str(mask_path), mask_image)

            # Export individual markers
            self._export_individual_markers(template_data.marker_ids, export_dir)

            # Create metadata file
            self._create_metadata_file(template_data, export_dir, template_path)

            return True

        except Exception as e:
            print(f"Error exporting template package: {e}")
            return False

    def _export_individual_markers(self, marker_ids: List[int], export_dir: Path):
        """Export each marker as separate image."""
        for i, marker_id in enumerate(marker_ids):
            # Generate marker image
            marker = self.aruco_utils.generate_marker(marker_id, Config.MARKER_SIZE)

            # Add border and ID label
            labeled_marker = self.aruco_utils.add_marker_label(marker, marker_id)

            # Save marker
            marker_path = export_dir / f"marker_{i+1}_id_{marker_id}.png"
            cv2.imwrite(str(marker_path), labeled_marker)

    def _create_metadata_file(
        self, template_data: TemplateData, export_dir: Path, template_path: Path
    ):
        """Create metadata file for admin app."""
        metadata = {
            "template_name": template_data.name,
            "marker_ids": template_data.marker_ids,
            "marker_files": [
                f"marker_1_id_{template_data.marker_ids[0]}.png",
                f"marker_2_id_{template_data.marker_ids[1]}.png",
                f"marker_3_id_{template_data.marker_ids[2]}.png",
                f"marker_4_id_{template_data.marker_ids[3]}.png",
            ],
            "template_file": f"{template_data.name}_template.png",
            "mask_file": f"{template_data.name}_mask.png",
            "template_width": template_data.template_width,
            "template_height": template_data.template_height,
            "created_at": datetime.now().isoformat(),
            "created_by": "Template Maker",
            "version": Config.VERSION,
        }

        metadata_path = export_dir / "metadata.json"
        self.file_utils.save_json(metadata, metadata_path)

    def export_marker_sheet(self, marker_ids: List[int], output_path: Path) -> bool:
        """Export markers as a printable sheet."""
        try:
            marker_sheet = self.aruco_utils.create_marker_sheet(marker_ids)
            cv2.imwrite(str(output_path), marker_sheet)
            return True
        except Exception as e:
            print(f"Error exporting marker sheet: {e}")
            return False

    def get_export_info(self, template_data: TemplateData) -> Dict[str, Any]:
        """Get information about what will be exported."""
        return {
            "template_name": template_data.name,
            "marker_count": len(template_data.marker_ids),
            "marker_ids": template_data.marker_ids,
            "export_directory": str(Config.EXPORTS_DIR / template_data.name),
            "files_to_create": [
                f"{template_data.name}_template.png",
                f"{template_data.name}_mask.png",
                "marker_1_id_{}.png".format(template_data.marker_ids[0]),
                "marker_2_id_{}.png".format(template_data.marker_ids[1]),
                "marker_3_id_{}.png".format(template_data.marker_ids[2]),
                "marker_4_id_{}.png".format(template_data.marker_ids[3]),
                "metadata.json",
            ],
        }
