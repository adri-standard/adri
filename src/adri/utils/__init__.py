"""Utility modules for the ADRI framework.

This module contains shared utility functions and classes that are used
throughout the ADRI system for common operations like path resolution,
validation helpers, serialization, and JSON Schema validation.
"""

from adri.utils.json_schema_validator import validate_json_against_schema

__all__ = ["validate_json_against_schema"]
