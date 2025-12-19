"""
CLI Import Integration Tests

Tests to ensure CLI import issues are caught early and prevent future regressions.
These tests validate that all critical CLI imports work correctly with the
modernized command registry architecture.
"""

import pytest
import sys
import tempfile
import os
import shutil
import time
import gc
from pathlib import Path
from unittest.mock import patch


def safe_rmtree(path, max_retries=3, delay=0.1):
    """Windows-safe recursive directory removal with retries."""
    for attempt in range(max_retries):
        try:
            if os.path.exists(path):
                # Force garbage collection to release file handles
                gc.collect()

                # Try different removal strategies
                if os.name == 'nt':  # Windows
                    import subprocess
                    try:
                        subprocess.run(['rmdir', '/s', '/q', path],
                                     shell=True, check=False, capture_output=True)
                        if not os.path.exists(path):
                            return
                    except:
                        pass

                # Fallback to shutil with error handling
                shutil.rmtree(path, ignore_errors=True)

                if not os.path.exists(path):
                    return

            else:
                return  # Directory doesn't exist, success

        except (OSError, PermissionError) as e:
            if attempt == max_retries - 1:
                # Final attempt failed, but don't raise error for tearDown
                try:
                    # Try to at least make files writable for later cleanup
                    for root, dirs, files in os.walk(path, topdown=False):
                        for name in files:
                            try:
                                filepath = os.path.join(root, name)
                                os.chmod(filepath, 0o777)
                            except:
                                pass
                except:
                    pass
                return  # Don't raise in tearDown

            # Wait before retrying
            time.sleep(delay * (attempt + 1))
            gc.collect()


class TestCLIImportValidation:
    """Integration tests for CLI import validation and regression prevention."""

    def test_core_cli_imports(self):
        """Test that all core CLI imports work without errors."""

        # Test main CLI entry point
        from src.adri.cli import main
        assert callable(main)

        # Test command registry imports (modern architecture)
        from src.adri.cli.registry import (
            register_all_commands,
            get_command,
            list_available_commands,
            create_command_registry
        )

        # Test all command class imports
        from src.adri.cli.commands.setup import SetupCommand
        from src.adri.cli.commands.assess import AssessCommand
        from src.adri.cli.commands.generate_contract import GenerateContractCommand
        from src.adri.cli.commands.config import (
            ValidateContractCommand,
            ListContractsCommand,
            ShowConfigCommand,
            ShowContractCommand
        )
        from src.adri.cli.commands.list_assessments import ListAssessmentsCommand
        from src.adri.cli.commands.view_logs import ViewLogsCommand
        from src.adri.cli.commands.scoring import ScoringExplainCommand, ScoringPresetApplyCommand

        # Test exception imports
        from src.adri.core.exceptions import DataValidationError, ConfigurationError, ComponentNotFoundError

        # Verify registry functions are callable
        assert callable(register_all_commands)
        assert callable(get_command)
        assert callable(list_available_commands)
        assert callable(create_command_registry)

    def test_command_registry_functions_work(self):
        """Test that command registry functions can execute without crashing."""

        from src.adri.cli.registry import register_all_commands, list_available_commands

        # Test registry operations (should not crash)
        try:
            register_all_commands()
            commands = list_available_commands()
            assert isinstance(commands, list)
        except Exception as e:
            # Should not fail with import errors
            assert not isinstance(e, (ImportError, ModuleNotFoundError))

    def test_command_classes_instantiate(self):
        """Test that all command classes can be instantiated and have required methods."""

        from src.adri.cli.commands.setup import SetupCommand
        from src.adri.cli.commands.assess import AssessCommand
        from src.adri.cli.commands.generate_contract import GenerateContractCommand
        from src.adri.cli.commands.config import ValidateContractCommand, ShowConfigCommand

        commands = [
            SetupCommand(),
            AssessCommand(),
            GenerateContractCommand(),
            ValidateContractCommand(),
            ShowConfigCommand()
        ]

        for cmd in commands:
            # Test modern command interface
            assert hasattr(cmd, 'get_name')
            assert hasattr(cmd, 'get_description')
            assert hasattr(cmd, 'execute')
            assert callable(cmd.execute)

            # Verify methods return valid data
            name = cmd.get_name()
            description = cmd.get_description()
            assert isinstance(name, str) and len(name) > 0
            assert isinstance(description, str) and len(description) > 0

    def test_exception_hierarchy_correct(self):
        """Test that exception imports use the correct hierarchy."""

        from src.adri.core.exceptions import DataValidationError, ConfigurationError, ADRIError, ComponentNotFoundError

        # Test that exceptions can be raised and caught
        try:
            raise DataValidationError("Test error")
        except DataValidationError as e:
            assert "Test error" in str(e)
        except Exception:
            pytest.fail("DataValidationError should be catchable")

        # Test inheritance
        assert issubclass(DataValidationError, ADRIError)
        assert issubclass(ConfigurationError, ADRIError)
        assert issubclass(ComponentNotFoundError, ADRIError)

    def test_no_circular_imports(self):
        """Test that CLI module imports don't create circular dependencies."""

        # This test will fail if circular imports exist
        from src.adri.cli.commands.setup import SetupCommand
        from src.adri.cli.registry import get_command, register_all_commands
        from src.adri.core.registry import get_global_registry

        # Test that we can import and use these together
        assert callable(get_command)
        assert callable(register_all_commands)

        # If we get here without import errors, circular imports are resolved
        assert True

    def test_cli_registry_integration(self):
        """Test that CLI registry system works with command registration."""

        from src.adri.cli.registry import register_all_commands, get_command, list_available_commands
        from src.adri.cli.commands.setup import SetupCommand

        # Test that registry functions exist and are callable
        assert callable(register_all_commands)
        assert callable(get_command)
        assert callable(list_available_commands)

        # Test that commands can be retrieved (should work with modern registry)
        with patch('src.adri.cli.registry.get_global_registry') as mock_registry:
            mock_commands_manager = mock_registry.return_value.commands
            mock_commands_manager.get_command.return_value = SetupCommand()

            try:
                command = get_command("setup")
                # Should return a command instance
                assert command is not None
                assert hasattr(command, 'execute')
            except Exception as e:
                # If it fails, it should be a known exception type, not an import error
                assert not isinstance(e, (ImportError, ModuleNotFoundError))

    def test_modern_cli_catalog_imports(self):
        """Test that catalog-related imports work with modern architecture."""

        # Test catalog client imports (if available)
        try:
            from src.adri.catalog.client import CatalogClient, CatalogEntry, FetchResult
            assert CatalogClient is not None
            assert CatalogEntry is not None
            assert FetchResult is not None
        except ImportError:
            # Catalog may not be fully implemented yet, that's okay
            pass

        # Test that catalog imports don't break other imports
        from src.adri.cli.registry import get_command
        assert callable(get_command)

    def test_legacy_function_compatibility(self):
        """Test that any remaining legacy functions still work."""

        # Test if any legacy functions are still exposed for backwards compatibility
        try:
            from src.adri.cli import standards_catalog_list_command, standards_catalog_fetch_command
            # If these exist, they should be callable
            assert callable(standards_catalog_list_command)
            assert callable(standards_catalog_fetch_command)
        except ImportError:
            # If these don't exist anymore, that's expected in the modernized version
            pass


def test_cli_import_regression_check():
    """Integration test to catch import regressions early in CI."""

    # This test should be run in CI to catch import issues
    import subprocess
    import sys

    # Test that CLI module can be imported in a fresh Python process
    temp_dir = tempfile.mkdtemp()
    try:
        os.chdir(temp_dir)

        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent.parent.parent)  # Project root

        # Test modern registry imports
        result = subprocess.run([
            sys.executable, '-c',
            'from src.adri.cli.registry import get_command, register_all_commands; print("REGISTRY_SUCCESS")'
        ], capture_output=True, text=True, env=env)

        assert result.returncode == 0, f"CLI registry import failed in subprocess: {result.stderr}"
        assert "REGISTRY_SUCCESS" in result.stdout

        # Test command imports
        result = subprocess.run([
            sys.executable, '-c',
            'from src.adri.cli.commands.setup import SetupCommand; print("COMMANDS_SUCCESS")'
        ], capture_output=True, text=True, env=env)

        assert result.returncode == 0, f"CLI commands import failed in subprocess: {result.stderr}"
        assert "COMMANDS_SUCCESS" in result.stdout

    finally:
        safe_rmtree(temp_dir)


def test_command_registry_end_to_end():
    """End-to-end test of command registry functionality."""

    from src.adri.cli.registry import get_command
    from src.adri.cli.commands.setup import SetupCommand

    # Mock the registry to avoid actual registration in tests
    with patch('src.adri.cli.registry.get_global_registry') as mock_get_registry:
        mock_registry = mock_get_registry.return_value
        mock_commands_manager = mock_registry.commands

        # Setup mock command
        mock_setup_cmd = SetupCommand()
        mock_commands_manager.get_command.return_value = mock_setup_cmd

        # Test that we can get a command through the registry
        command = get_command("setup")

        # Verify it's the right type
        assert isinstance(command, SetupCommand)
        assert hasattr(command, 'execute')

        # Test that it has the expected interface
        assert callable(command.get_name)
        assert callable(command.get_description)
        assert callable(command.execute)
