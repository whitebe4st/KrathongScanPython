"""
Configuration utilities for KrathongScanner.

This module provides:
- Configuration validation
- Environment variable helpers
- Configuration file management
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    """Configuration management utility class."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_file: Optional path to configuration file
        """
        self.config_file = config_file
        self._config_data: Dict[str, Any] = {}

        if config_file:
            self.load_config()

    def load_config(self) -> None:
        """Load configuration from file."""
        if not self.config_file:
            return

        config_path = Path(self.config_file)
        if not config_path.exists():
            return

        try:
            if config_path.suffix.lower() in [".yaml", ".yml"]:
                with open(config_path, encoding="utf-8") as f:
                    self._config_data = yaml.safe_load(f) or {}
            elif config_path.suffix.lower() == ".json":
                with open(config_path, encoding="utf-8") as f:
                    self._config_data = json.load(f)
            else:
                # Try to load as JSON by default
                with open(config_path, encoding="utf-8") as f:
                    self._config_data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
            self._config_data = {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config_data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config_data[key] = value

    def save_config(self) -> None:
        """Save configuration to file."""
        if not self.config_file:
            return

        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if config_path.suffix.lower() in [".yaml", ".yml"]:
                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.dump(self._config_data, f, default_flow_style=False)
            elif config_path.suffix.lower() == ".json":
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(self._config_data, f, indent=2)
            else:
                # Save as JSON by default
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(self._config_data, f, indent=2)
        except Exception as e:
            print(f"Error: Could not save config file {config_file}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Get configuration as dictionary.

        Returns:
            Configuration dictionary
        """
        return self._config_data.copy()
