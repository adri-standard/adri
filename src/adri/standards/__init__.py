"""
ADRI Standards Module.

Standard parsing and validation functionality.
Handles YAML standard loading and validation logic.

Components:
- StandardsParser: Parses and validates YAML standards
- Standard loading utilities

This module provides standard management for the ADRI framework.
"""

# Import standards components
from .parser import StandardsParser

# Export all components
__all__ = ["StandardsParser"]
