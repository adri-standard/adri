"""
Configuration loader for ADRI V2.

This module handles loading and parsing of ADRI configuration files.
"""

import os
from typing import Any, Dict, Optional

import yaml


class ConfigLoader:
    """Loads and validates ADRI configuration files."""

    def __init__(self):
        """Initialize the configuration loader with default search paths."""
        self.default_config_paths = [
            "adri-config.yaml",
            "ADRI/adri-config.yaml",
            ".adri/config.yaml",
        ]

    def load_config(
        self, config_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Load configuration from file.

        Args:
            config_path: Specific config file path, or None to search default locations

        Returns:
            Configuration dictionary or None if not found
        """
        if config_path:
            return self._load_config_file(config_path)

        # Search default locations
        for default_path in self.default_config_paths:
            if os.path.exists(default_path):
                return self._load_config_file(default_path)

        return None

    def _load_config_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load configuration from specific file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                return None

            return config
        except Exception:
            return None

    def validate_config_structure(self, config: Dict[str, Any]) -> bool:
        """Validate that config has required structure."""
        if "adri" not in config:
            return False

        adri_config = config["adri"]

        required_fields = ["project_name", "version", "environments"]
        for field in required_fields:
            if field not in adri_config:
                return False

        return True
