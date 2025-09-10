"""
File utility functions for KrathongScanner.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class FileUtils:
    """Utility functions for file operations."""

    @staticmethod
    def ensure_directory(path: Path) -> Path:
        """Ensure directory exists and return Path object."""
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def copy_file(src: Path, dst: Path) -> bool:
        """Copy file from source to destination."""
        try:
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            print(f"Error copying file {src} to {dst}: {e}")
            return False

    @staticmethod
    def move_file(src: Path, dst: Path) -> bool:
        """Move file from source to destination."""
        try:
            shutil.move(str(src), str(dst))
            return True
        except Exception as e:
            print(f"Error moving file {src} to {dst}: {e}")
            return False

    @staticmethod
    def delete_file(path: Path) -> bool:
        """Delete file if it exists."""
        try:
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {path}: {e}")
            return False

    @staticmethod
    def get_file_size(path: Path) -> int:
        """Get file size in bytes."""
        try:
            return path.stat().st_size
        except Exception as e:
            print(f"Error getting file size for {path}: {e}")
            return 0

    @staticmethod
    def get_file_modified_time(path: Path) -> Optional[datetime]:
        """Get file modification time."""
        try:
            timestamp = path.stat().st_mtime
            return datetime.fromtimestamp(timestamp)
        except Exception as e:
            print(f"Error getting file modification time for {path}: {e}")
            return None

    @staticmethod
    def find_files(
        directory: Path, pattern: str = "*", recursive: bool = True
    ) -> List[Path]:
        """Find files matching pattern in directory."""
        try:
            if recursive:
                return list(directory.rglob(pattern))
            else:
                return list(directory.glob(pattern))
        except Exception as e:
            print(f"Error finding files in {directory}: {e}")
            return []

    @staticmethod
    def find_image_files(directory: Path, recursive: bool = True) -> List[Path]:
        """Find image files in directory."""
        image_extensions = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".gif"]
        all_files = FileUtils.find_files(directory, "*", recursive)

        return [f for f in all_files if f.suffix.lower() in image_extensions]

    @staticmethod
    def save_json(data: Dict[str, Any], path: Path) -> bool:
        """Save data as JSON file."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving JSON to {path}: {e}")
            return False

    @staticmethod
    def load_json(path: Path) -> Optional[Dict[str, Any]]:
        """Load data from JSON file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON from {path}: {e}")
            return None

    @staticmethod
    def create_backup(path: Path, backup_suffix: str = ".backup") -> Optional[Path]:
        """Create backup of file."""
        try:
            if not path.exists():
                return None

            backup_path = path.with_suffix(path.suffix + backup_suffix)
            shutil.copy2(path, backup_path)
            return backup_path
        except Exception as e:
            print(f"Error creating backup for {path}: {e}")
            return None

    @staticmethod
    def get_unique_filename(directory: Path, base_name: str, extension: str) -> Path:
        """Get unique filename in directory."""
        counter = 1
        while True:
            if counter == 1:
                filename = f"{base_name}{extension}"
            else:
                filename = f"{base_name}_{counter}{extension}"

            file_path = directory / filename
            if not file_path.exists():
                return file_path

            counter += 1

    @staticmethod
    def clean_filename(filename: str) -> str:
        """Clean filename by removing invalid characters."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        return filename.strip()

    @staticmethod
    def get_file_info(path: Path) -> Dict[str, Any]:
        """Get comprehensive file information."""
        try:
            stat = path.stat()
            return {
                "name": path.name,
                "stem": path.stem,
                "suffix": path.suffix,
                "size": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
                "exists": path.exists(),
            }
        except Exception as e:
            print(f"Error getting file info for {path}: {e}")
            return {}
