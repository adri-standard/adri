"""CLI command registry and discovery for ADRI.

This module provides command registration and discovery functionality
for the new modular CLI architecture.
"""

from typing import Dict

from ..core.protocols import Command
from ..core.registry import get_global_registry
from .commands import (
    AssessCommand,
    GenerateStandardCommand,
    ListAssessmentsCommand,
    ListStandardsCommand,
    ScoringExplainCommand,
    ScoringPresetApplyCommand,
    SetupCommand,
    ShowConfigCommand,
    ShowStandardCommand,
    ValidateStandardCommand,
    ViewLogsCommand,
)


def register_all_commands() -> None:
    """Register all CLI commands with the global registry."""
    registry = get_global_registry()

    # Core commands
    registry.commands.register("setup", SetupCommand)
    registry.commands.register("assess", AssessCommand)
    registry.commands.register("generate-standard", GenerateStandardCommand)

    # Information commands
    registry.commands.register("list-assessments", ListAssessmentsCommand)
    registry.commands.register("list-standards", ListStandardsCommand)
    registry.commands.register("view-logs", ViewLogsCommand)

    # Configuration commands
    registry.commands.register("show-config", ShowConfigCommand)
    registry.commands.register("validate-standard", ValidateStandardCommand)
    registry.commands.register("show-standard", ShowStandardCommand)

    # Scoring commands
    registry.commands.register("scoring-explain", ScoringExplainCommand)
    registry.commands.register("scoring-preset-apply", ScoringPresetApplyCommand)


def create_command_registry() -> Dict[str, Command]:
    """Create a dictionary of all registered commands.

    Returns:
        Dictionary mapping command names to command instances
    """
    # Ensure all commands are registered
    register_all_commands()

    # Get the global registry and create command instances
    registry = get_global_registry()
    commands = {}

    for command_name in registry.commands.list_components():
        commands[command_name] = registry.commands.get_command(command_name)

    return commands


def get_command(command_name: str) -> Command:
    """Get a specific command by name.

    Args:
        command_name: Name of the command to retrieve

    Returns:
        Command instance

    Raises:
        ComponentNotFoundError: If command is not found
    """
    # Ensure all commands are registered
    register_all_commands()

    registry = get_global_registry()
    return registry.commands.get_command(command_name)


def list_available_commands() -> list:
    """List all available command names.

    Returns:
        List of command names
    """
    # Ensure all commands are registered
    register_all_commands()

    registry = get_global_registry()
    return registry.commands.list_components()
