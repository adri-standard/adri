"""
Configuration management for ADRI.

This module provides configuration management for the ADRI framework,
including loading configurations from files and managing defaults.
"""

from .config import Configuration, get_config, set_config

__all__ = ["Configuration", "get_config", "set_config"]
