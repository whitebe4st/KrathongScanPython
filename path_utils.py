"""
Path Utilities for KrathongScanner Applications

Handles path resolution for executables and development environments.
Ensures both Scanner and Template Management can find shared resources.
"""

import os
import sys
from pathlib import Path
from typing import Optional


def get_executable_dir() -> Path:
    """Get the directory containing the executable or script."""
    if hasattr(sys, "_MEIPASS"):
        # Running as PyInstaller executable
        return Path(sys.executable).parent
    else:
        # Running as script
        return Path(__file__).parent


def get_resource_dir() -> Path:
    """Get the directory containing shared resources."""
    exe_dir = get_executable_dir()

    # Try to find resources relative to executable
    possible_paths = [
        exe_dir / "resources",  # Packaged resources
        exe_dir / ".." / "resources",  # One level up
        exe_dir,  # Same directory as executable
        Path.cwd(),  # Current working directory
    ]

    for path in possible_paths:
        if path.exists():
            return path.resolve()

    # Default to executable directory
    return exe_dir


def get_database_path() -> Path:
    """Get the path to scanner.db database - Scanner-centric approach."""
    exe_dir = get_executable_dir()

    # For scanner application - store database in scanner directory
    if is_scanner_app():
        scanner_db_path = exe_dir / "scanner.db"
        scanner_db_path.parent.mkdir(parents=True, exist_ok=True)
        return scanner_db_path

    # For template management - search for scanner database first
    scanner_locations = find_scanner_database_locations()
    if scanner_locations:
        return scanner_locations[0]  # Use first found scanner database

    # Fallback to local database if no scanner database found
    fallback_path = exe_dir / "scanner.db"
    fallback_path.parent.mkdir(parents=True, exist_ok=True)
    return fallback_path


def is_scanner_app() -> bool:
    """Check if current executable is the scanner application."""
    exe_path = Path(sys.executable) if hasattr(sys, "_MEIPASS") else Path(__file__)
    return "scanner" in exe_path.name.lower() or "Scanner" in exe_path.name


def find_scanner_database_locations() -> list[Path]:
    """Find all possible scanner database locations for template management."""
    exe_dir = get_executable_dir()

    possible_paths = [
        # Look for scanner directory relative to current location
        exe_dir / ".." / "scanner" / "scanner.db",  # ../scanner/scanner.db
        exe_dir
        / ".."
        / "scanner"
        / "_internal"
        / "scanner.db",  # ../scanner/_internal/scanner.db
        exe_dir / "scanner" / "scanner.db",  # scanner/scanner.db
        exe_dir
        / "scanner"
        / "_internal"
        / "scanner.db",  # scanner/_internal/scanner.db
        # Look in release structure
        exe_dir / ".." / ".." / "scanner" / "scanner.db",  # ../../scanner/scanner.db
        exe_dir
        / ".."
        / ".."
        / "scanner"
        / "_internal"
        / "scanner.db",  # ../../scanner/_internal/scanner.db
        # Development paths
        Path.cwd() / "release" / "scanner" / "scanner.db",
        Path.cwd() / "release" / "scanner" / "_internal" / "scanner.db",
        # Common installation paths
        Path.cwd() / "scanner.db",
        exe_dir / "scanner.db",
    ]

    existing_paths = []
    for path in possible_paths:
        try:
            if path.exists():
                existing_paths.append(path.resolve())
        except (OSError, PermissionError):
            continue

    return existing_paths


def get_custom_database_path(custom_path: str) -> Path:
    """Validate and return custom database path."""
    path = Path(custom_path)
    if not path.exists():
        raise FileNotFoundError(f"Database file not found: {custom_path}")
    if not path.suffix.lower() == ".db":
        raise ValueError(f"Invalid database file extension: {path.suffix}")
    return path.resolve()


def get_data_dir() -> Path:
    """Get the data directory for storing outputs."""
    exe_dir = get_executable_dir()
    data_dir = exe_dir / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_config_dir() -> Path:
    """Get the configuration directory."""
    exe_dir = get_executable_dir()
    config_dir = exe_dir / "config"
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_templates_dir() -> Path:
    """Get the templates directory for storing template files."""
    data_dir = get_data_dir()
    templates_dir = data_dir / "templates"
    templates_dir.mkdir(exist_ok=True)
    return templates_dir


def get_masks_dir() -> Path:
    """Get the masks directory for storing mask files."""
    data_dir = get_data_dir()
    masks_dir = data_dir / "masks"
    masks_dir.mkdir(exist_ok=True)
    return masks_dir


def ensure_directories() -> None:
    """Ensure all necessary directories exist."""
    get_data_dir()
    get_config_dir()
    get_templates_dir()
    get_masks_dir()


def get_log_path() -> Path:
    """Get the path for log files."""
    exe_dir = get_executable_dir()
    return exe_dir / "krathong_scanner.log"


def print_paths_info():
    """Print information about resolved paths (for debugging)."""
    print("=== KrathongScanner Path Information ===")
    print(f"Executable directory: {get_executable_dir()}")
    print(f"Resource directory: {get_resource_dir()}")
    print(f"Database path: {get_database_path()}")
    print(f"Data directory: {get_data_dir()}")
    print(f"Config directory: {get_config_dir()}")
    print(f"Templates directory: {get_templates_dir()}")
    print(f"Masks directory: {get_masks_dir()}")
    print(f"Log path: {get_log_path()}")
    print("========================================")


if __name__ == "__main__":
    # Print path information when run directly
    ensure_directories()
    print_paths_info()
