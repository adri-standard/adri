"""CLI package for ADRI framework.

This package contains the command-line interface components including
individual command implementations and registry functionality.
"""

from .registry import create_command_registry, get_command, register_all_commands

__all__ = ["register_all_commands", "get_command", "create_command_registry"]
