"""
ADRI Standards Module.

This module provides standards loading functionality for the ADRI validator.
Standards are loaded from the adri-standards submodule to ensure offline-first
operation and eliminate network dependencies.
"""

from .exceptions import InvalidStandardError, StandardNotFoundError
from .loader import StandardsLoader

__all__ = ["StandardsLoader", "StandardNotFoundError", "InvalidStandardError"]

# Default loader instance for convenience
default_loader = StandardsLoader()


def load_standard(standard_name: str):
    """
    Load a standard using the default loader.

    Args:
        standard_name: Name of the standard to load

    Returns:
        dict: The loaded standard

    Raises:
        StandardNotFoundError: If the standard is not found
        InvalidStandardError: If the standard is invalid
    """
    return default_loader.load_standard(standard_name)


def list_available_standards():
    """
    List available standards.

    Returns:
        list: List of available standard names
    """
    return default_loader.list_available_standards()


def standard_exists(standard_name: str) -> bool:
    """
    Check if a standard exists.

    Args:
        standard_name: Name of the standard to check

    Returns:
        bool: True if the standard exists, False otherwise
    """
    return default_loader.standard_exists(standard_name)
