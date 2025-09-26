"""CLI package for ADRI framework.

This package contains the command-line interface components including
individual command implementations and registry functionality.
"""

from .registry import create_command_registry, get_command, register_all_commands


# Import functions that are still needed for backward compatibility
def _get_cli_functions():
    """Get CLI functions lazily to avoid circular imports."""
    import importlib.util
    from pathlib import Path

    # Get the path to the cli.py module
    cli_path = Path(__file__).parent / ".." / "cli.py"

    # Load the module dynamically
    spec = importlib.util.spec_from_file_location("adri_cli", cli_path)
    cli_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli_module)

    return cli_module


def _find_adri_project_root(*args, **kwargs):
    """Find ADRI project root - backward compatibility wrapper."""
    cli_module = _get_cli_functions()
    return cli_module._find_adri_project_root(*args, **kwargs)


def setup_command(*args, **kwargs):
    """Provide setup command - backward compatibility wrapper."""
    from .commands.setup import SetupCommand

    command = SetupCommand()
    return command.execute(*args, **kwargs)


def scoring_explain_command(*args, **kwargs):
    """Scoring explain command - backward compatibility wrapper."""
    from .commands.scoring import ScoringCommand

    command = ScoringCommand()
    # This might need to be adapted based on the actual command structure
    return command.explain(*args, **kwargs)


# Import main function from the CLI module
def main():
    """Import and run the CLI main function."""
    import importlib.util
    import sys
    from pathlib import Path

    # Get the path to the cli.py module
    cli_path = Path(__file__).parent / ".." / "cli.py"

    # Load the module dynamically
    spec = importlib.util.spec_from_file_location("adri_cli", cli_path)
    cli_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli_module)

    # Call the main function
    return cli_module.main()


def _get_catalog_functions():
    """Get catalog functions lazily to avoid circular imports."""
    import importlib.util
    from pathlib import Path

    # Get the path to the cli.py module
    cli_path = Path(__file__).parent / ".." / "cli.py"

    # Load the module dynamically
    spec = importlib.util.spec_from_file_location("adri_cli", cli_path)
    cli_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli_module)

    return (
        cli_module.standards_catalog_list_command,
        cli_module.standards_catalog_fetch_command,
    )


# Lazy imports for catalog functions to avoid circular imports
def standards_catalog_list_command(*args, **kwargs):
    """List available standards from the remote catalog."""
    list_cmd, _ = _get_catalog_functions()
    return list_cmd(*args, **kwargs)


def standards_catalog_fetch_command(*args, **kwargs):
    """Fetch a standard from the remote catalog and save it locally."""
    _, fetch_cmd = _get_catalog_functions()
    return fetch_cmd(*args, **kwargs)


__all__ = [
    "register_all_commands",
    "get_command",
    "create_command_registry",
    "main",
    "standards_catalog_list_command",
    "standards_catalog_fetch_command",
    "_find_adri_project_root",
    "setup_command",
    "scoring_explain_command",
]
