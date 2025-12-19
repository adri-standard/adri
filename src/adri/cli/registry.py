"""CLI command registry and discovery for ADRI.

This module provides command registration and discovery functionality
for the new modular CLI architecture.
"""

from ..core.protocols import Command
from ..core.registry import get_global_registry
from .commands import (
    AssessCommand,
    GenerateContractCommand,
    GuideCommand,
    ListAssessmentsCommand,
    ListContractsCommand,
    ScoringExplainCommand,
    ScoringPresetApplyCommand,
    SetupCommand,
    ShowConfigCommand,
    ShowContractCommand,
    ValidateContractCommand,
    ViewLogsCommand,
)


def register_all_commands() -> None:
    """Register all CLI commands with the global registry."""
    registry = get_global_registry()

    # Define all commands to register
    commands_to_register = [
        # Core commands
        ("setup", SetupCommand),
        ("assess", AssessCommand),
        ("generate-contract", GenerateContractCommand),
        ("guide", GuideCommand),
        # Information commands
        ("list-assessments", ListAssessmentsCommand),
        ("list-contracts", ListContractsCommand),
        ("view-logs", ViewLogsCommand),
        # Configuration commands
        ("show-config", ShowConfigCommand),
        ("validate-contract", ValidateContractCommand),
        ("show-contract", ShowContractCommand),
        # Scoring commands
        ("scoring-explain", ScoringExplainCommand),
        ("scoring-preset-apply", ScoringPresetApplyCommand),
    ]

    # Register commands only if they're not already registered
    existing_commands = set(registry.commands.list_components())
    for command_name, command_class in commands_to_register:
        if command_name not in existing_commands:
            registry.commands.register(command_name, command_class)


def create_command_registry() -> dict[str, Command]:
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
