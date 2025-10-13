"""
ADRI Standards Parser.

YAML standard parsing and validation functionality, migrated from adri/standards/loader.py.
Provides offline-first loading of ADRI standards from bundled standards directory.
No network requests are made, ensuring enterprise-friendly operation and air-gap compatibility.
"""

import os
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Updated imports for new structure - with fallbacks during migration
try:
    from ..standards.exceptions import (
        InvalidStandardError,
        StandardNotFoundError,
        StandardsDirectoryNotFoundError,
    )
except ImportError:
    try:
        from adri.standards.exceptions import (
            InvalidStandardError,
            StandardNotFoundError,
            StandardsDirectoryNotFoundError,
        )
    except ImportError:
        # Fallback exception classes
        class StandardsDirectoryNotFoundError(Exception):
            """Exception raised when standards directory is not found."""

            pass

        class StandardNotFoundError(Exception):
            """Exception raised when a standard is not found."""

            pass

        class InvalidStandardError(Exception):
            """Exception raised when a standard is invalid."""

            pass


class StandardsParser:
    """
    Parses and loads ADRI standards from bundled standards directory.

    This parser provides fast, offline access to all standards
    without any network dependencies. All standards are validated on
    loading to ensure they conform to the ADRI standard format.
    """

    def __init__(self):
        """Initialize the standards parser."""

        self._lock = threading.RLock()
        self._standards_path = self._get_standards_path()
        self._validate_standards_directory()

    @property
    def standards_path(self) -> Path:
        """Get the path to the standards directory."""

        return self._standards_path

    def _get_standards_path(self) -> Path:
        """Resolve standards directory path from environment parameter only."""

        # Environment variable is required - no defaults or fallbacks
        env_path = os.getenv("ADRI_STANDARDS_PATH")
        if not env_path:
            raise StandardsDirectoryNotFoundError(
                "ADRI_STANDARDS_PATH environment variable must be set. "
                "Set it to point to your standards directory."
            )

        env_dir = Path(env_path)
        if not env_dir.exists():
            raise StandardsDirectoryNotFoundError(
                f"Standards directory does not exist: {env_path}"
            )

        if not env_dir.is_dir():
            raise StandardsDirectoryNotFoundError(
                f"Standards path is not a directory: {env_path}"
            )

        return env_dir.resolve()

    def _validate_standards_directory(self):
        """Validate that the standards directory exists."""

        if not self._standards_path.exists():
            raise StandardsDirectoryNotFoundError(str(self._standards_path))

        if not self._standards_path.is_dir():
            raise StandardsDirectoryNotFoundError(
                f"Standards path is not a directory: {self._standards_path}"
            )

    @lru_cache(maxsize=128)
    def parse_standard(self, standard_name: str) -> Dict[str, Any]:
        """
        Parse a standard by name.

        Args:
            standard_name: Name of the standard to parse (without .yaml extension)

        Returns:
            dict: The parsed and validated standard

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
        Validate that a standard has the required structure using StandardValidator.

        Args:
            standard: The standard dictionary to validate
            standard_name: Name of the standard for error messages

        Raises:
            InvalidStandardError: If the standard structure is invalid
        """
        try:
            from adri.standards.exceptions import SchemaValidationError
            from adri.standards.validator import get_validator

            validator = get_validator()
            result = validator.validate_standard(standard, use_cache=False)

            if not result.is_valid:
                # Collect all error messages
                error_messages = [err.message for err in result.errors]
                raise InvalidStandardError(
                    f"Standard validation failed: {'; '.join(error_messages)}",
                    standard_name,
                )
        except SchemaValidationError as e:
            raise InvalidStandardError(str(e), standard_name)
        except ImportError:
            # Fallback to basic validation if new validator not available
            if not isinstance(standard, dict):
                raise InvalidStandardError(
                    "Standard must be a dictionary", standard_name
                )

            # Check for required top-level sections
            required_sections = ["standards", "requirements"]
            for section in required_sections:
                if section not in standard:
                    raise InvalidStandardError(
                        f"Missing required section: {section}", standard_name
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

        # Parse the standard to get metadata
        standard = self.parse_standard(standard_name)
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
        """Clear the internal cache of parsed standards."""

        self.parse_standard.cache_clear()

    def get_cache_info(self):
        """Get information about the internal cache."""

        return self.parse_standard.cache_info()

    def validate_standard_file(self, standard_path: str) -> Dict[str, Any]:
        """
        Validate a YAML standard file and return detailed results.

        Args:
            standard_path: Path to YAML standard file

        Returns:
            Dict containing validation results
        """

        validation_result = {
            "file_path": standard_path,
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "passed_checks": [],
        }

        try:
            # Check if file exists
            if not os.path.exists(standard_path):
                validation_result["errors"].append(f"File not found: {standard_path}")
                validation_result["is_valid"] = False
                return validation_result

            # Load YAML content
            try:
                with open(standard_path, "r", encoding="utf-8") as f:
                    yaml_content = yaml.safe_load(f)
                validation_result["passed_checks"].append("Valid YAML syntax")
            except yaml.YAMLError as e:
                validation_result["errors"].append(f"Invalid YAML syntax: {e}")
                validation_result["is_valid"] = False
                return validation_result

            # Validate using existing structure validation
            try:
                self._validate_standard_structure(
                    yaml_content, os.path.basename(standard_path)
                )
                validation_result["passed_checks"].append(
                    "Valid ADRI standard structure"
                )
            except InvalidStandardError as e:
                validation_result["errors"].append(str(e))
                validation_result["is_valid"] = False

        except Exception as e:
            validation_result["errors"].append(
                f"Unexpected error during validation: {e}"
            )
            validation_result["is_valid"] = False

        return validation_result


# Convenience functions for backward compatibility
def load_bundled_standard(standard_name: str) -> Dict[str, Any]:
    """
    Load a standard using the default parser.

    Args:
        standard_name: Name of the standard to load

    Returns:
        dict: The loaded standard
    """

    parser = StandardsParser()
    return parser.parse_standard(standard_name)


def list_bundled_standards() -> List[str]:
    """
    List all available standards.

    Returns:
        list: List of standard names
    """

    parser = StandardsParser()
    return parser.list_available_standards()


# Backward compatibility aliases
StandardsLoader = StandardsParser
