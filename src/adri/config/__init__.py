"""
ADRI Configuration Module.

Handles configuration loading and management functionality.
Consolidates configuration components from the original config/manager.py.

Components:
- ConfigurationLoader: Streamlined configuration loading (simplified from ConfigManager)
- Configuration management utilities

This module provides configuration management for the ADRI framework.
"""

# Import configuration loader
from .loader import (
    ConfigurationLoader,
    get_protection_settings,
    load_adri_config,
    resolve_contract_file,
)

# Export all components
__all__ = [
    "ConfigurationLoader",
    "load_adri_config",
    "get_protection_settings",
    "resolve_contract_file",
]
