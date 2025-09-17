"""
ADRI Standards Module

Handles YAML standard parsing and validation functionality.
Consolidates standards components from the original standards/loader.py.

Components:
- StandardsParser: YAML parsing functionality (renamed from StandardsLoader)
- Schema validation: Standards schema validation
- Standards loading utilities

This module provides standards parsing and validation for the ADRI framework.
"""

# Import standards parser
from .parser import list_bundled_standards, load_bundled_standard, StandardsParser

# Import exceptions
try:
    from .exceptions import (
        InvalidStandardError,
        StandardNotFoundError,
        StandardsDirectoryNotFoundError,
    )
except ImportError:
    # Handle missing exceptions gracefully
    StandardNotFoundError = Exception
    InvalidStandardError = Exception
    StandardsDirectoryNotFoundError = Exception

# Export all components
__all__ = [
    "StandardsParser",
    "load_bundled_standard",
    "list_bundled_standards",
    "StandardNotFoundError",
    "InvalidStandardError",
    "StandardsDirectoryNotFoundError",
]
