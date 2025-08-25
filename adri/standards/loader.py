"""
ADRI Standards Loader.

This module provides offline-first loading of ADRI standards from bundled
standards. No network requests are made, ensuring enterprise-friendly
operation and air-gap compatibility.
"""

import os
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import yaml

from .exceptions import (
    InvalidStandardError,
    StandardNotFoundError,
    StandardsDirectoryNotFoundError,
)


class StandardsLoader:
    """
    Loads ADRI standards from bundled standards directory.

    This loader provides fast, offline access to all standards
    without any network dependencies. All standards are validated on
    loading to ensure they conform to the ADRI standard format.
    """

    def __init__(self):
        """Initialize the standards loader."""
        self._lock = threading.RLock()
        self._standards_path = self._get_standards_path()
        self._validate_standards_directory()

    @property
    def standards_path(self) -> Path:
        """Get the path to the standards directory."""
        return self._standards_path

    def _get_standards_path(self) -> Path:
        """Resolve standards directory path, using bundled standards or environment override."""
        # Environment override first (for testing or custom standards)
        env_path = os.getenv("ADRI_STANDARDS_PATH")
        if env_path:
            env_dir = Path(env_path)
            if env_dir.exists() and env_dir.is_dir():
                return env_dir.resolve()

        # Use bundled standards (default for all installations)
        bundled_standards_path = Path(__file__).parent / "bundled"
        if bundled_standards_path.exists() and bundled_standards_path.is_dir():
            return bundled_standards_path.resolve()

        # No fallback - bundled standards are required for standalone operation
        raise StandardsDirectoryNotFoundError(
            f"Bundled standards directory not found at {bundled_standards_path}"
        )

    def _validate_standards_directory(self):
        """Validate that the standards directory exists."""
        if not self._standards_path.exists():
            raise StandardsDirectoryNotFoundError(str(self._standards_path))

        if not self._standards_path.is_dir():
            raise StandardsDirectoryNotFoundError(
                f"Standards path is not a directory: {self._standards_path}"
            )

    @lru_cache(maxsize=128)
    def load_standard(self, standard_name: str) -> Dict[str, Any]:
        """
        Load a standard by name.

        Args:
            standard_name: Name of the standard to load (without .yaml extension)

        Returns:
            dict: The loaded and validated standard

        Raises:
            StandardNotFoundError: If the standard is not found
            InvalidStandardError: If the standard is invalid
        """
        with self._lock:
            # Construct the file path
            standard_file = self._standards_path / f"{standard_name}.yaml"

            # Check if the file exists
            if not standard_file.exists():
                raise StandardNotFoundError(standard_name)

            try:
                # Load and parse the YAML file
                with open(standard_file, "r", encoding="utf-8") as f:
                    standard_content = yaml.safe_load(f)

                # Validate the standard structure
                self._validate_standard_structure(standard_content, standard_name)

                # Ensure we return the correct type
                if isinstance(standard_content, dict):
                    return standard_content
                else:
                    raise InvalidStandardError(
                        "Standard content must be a dictionary", standard_name
                    )

            except yaml.YAMLError as e:
                raise InvalidStandardError(f"YAML parsing error: {e}", standard_name)
            except Exception as e:
                raise InvalidStandardError(
                    f"Error loading standard: {e}", standard_name
                )

    def _validate_standard_structure(
        self, standard: Dict[str, Any], standard_name: str
    ):
        """
        Validate that a standard has the required structure.

        Args:
            standard: The standard dictionary to validate
            standard_name: Name of the standard for error messages

        Raises:
            InvalidStandardError: If the standard structure is invalid
        """
        if not isinstance(standard, dict):
            raise InvalidStandardError("Standard must be a dictionary", standard_name)

        # Check for required top-level sections
        required_sections = ["standards", "requirements"]
        for section in required_sections:
            if section not in standard:
                raise InvalidStandardError(
                    f"Missing required section: {section}", standard_name
                )

        # Validate standards section
        standards_section = standard["standards"]
        if not isinstance(standards_section, dict):
            raise InvalidStandardError(
                "'standards' section must be a dictionary", standard_name
            )

        required_standards_fields = ["id", "name", "version"]
        for field in required_standards_fields:
            if field not in standards_section:
                raise InvalidStandardError(
                    f"Missing required field in standards section: {field}",
                    standard_name,
                )

        # Validate requirements section
        requirements_section = standard["requirements"]
        if not isinstance(requirements_section, dict):
            raise InvalidStandardError(
                "'requirements' section must be a dictionary", standard_name
            )

        if "overall_minimum" not in requirements_section:
            raise InvalidStandardError(
                "Missing 'overall_minimum' in requirements section", standard_name
            )

    def list_available_standards(self) -> List[str]:
        """
        List all available standards.

        Returns:
            list: List of standard names (without .yaml extension)
        """
        with self._lock:
            standards = []

            # Find all .yaml files in the standards directory
            for yaml_file in self._standards_path.glob("*.yaml"):
                # Remove the .yaml extension to get the standard name
                standard_name = yaml_file.stem
                standards.append(standard_name)

            return sorted(standards)

    def standard_exists(self, standard_name: str) -> bool:
        """
        Check if a standard exists in the standards directory.

        Args:
            standard_name: Name of the standard to check

        Returns:
            bool: True if the standard exists, False otherwise
        """
        standard_file = self._standards_path / f"{standard_name}.yaml"
        return standard_file.exists()

    def get_standard_metadata(self, standard_name: str) -> Dict[str, Any]:
        """
        Get metadata for a standard without loading the full content.

        Args:
            standard_name: Name of the standard

        Returns:
            dict: Standard metadata including name, version, description, file_path

        Raises:
            StandardNotFoundError: If the standard is not found
        """
        if not self.standard_exists(standard_name):
            raise StandardNotFoundError(standard_name)

        # Load the standard to get metadata
        standard = self.load_standard(standard_name)
        standards_section = standard["standards"]

        metadata = {
            "name": standards_section.get("name", standard_name),
            "version": standards_section.get("version", "unknown"),
            "description": standards_section.get(
                "description", "No description available"
            ),
            "file_path": str(self._standards_path / f"{standard_name}.yaml"),
            "id": standards_section.get("id", standard_name),
        }

        return metadata

    def clear_cache(self):
        """Clear the internal cache of loaded standards."""
        self.load_standard.cache_clear()

    def get_cache_info(self):
        """Get information about the internal cache."""
        return self.load_standard.cache_info()


# Convenience functions for backward compatibility
def load_bundled_standard(standard_name: str) -> Dict[str, Any]:
    """
    Load a standard using the default loader.

    Args:
        standard_name: Name of the standard to load

    Returns:
        dict: The loaded standard
    """
    loader = StandardsLoader()
    return loader.load_standard(standard_name)


def list_bundled_standards() -> List[str]:
    """
    List all available standards.

    Returns:
        list: List of standard names
    """
    loader = StandardsLoader()
    return loader.list_available_standards()
