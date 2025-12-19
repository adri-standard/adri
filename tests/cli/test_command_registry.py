"""Tests for the CLI command registry functionality.

This module tests the command registry pattern that replaced the monolithic
CLI structure, ensuring proper command registration, retrieval, and execution.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.adri.cli.registry import (
    register_all_commands,
    create_command_registry,
    get_command,
    list_available_commands
)
from src.adri.core.exceptions import ComponentNotFoundError
from tests.cli.fixtures import ModernCLITestBase, create_test_workspace


class TestCommandRegistry:
    """Test command registry functionality."""

    def test_register_all_commands_success(self):
        """Test that all commands are properly registered."""
        with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
            mock_registry = Mock()
            mock_commands_manager = Mock()
            mock_registry.commands = mock_commands_manager
            mock_commands_manager.list_components.return_value = []  # No existing commands
            mock_registry_func.return_value = mock_registry

            register_all_commands()

            # Verify all expected commands were registered
            expected_commands = [
                "setup", "assess", "generate-contract", "list-assessments",
                "list-contracts", "view-logs", "show-config", "validate-contract",
                "show-contract", "scoring-explain", "scoring-preset-apply", "guide"
            ]

            # Should have attempted to register each command
            assert mock_commands_manager.register.call_count == len(expected_commands)

            # Check that each expected command was registered
            registered_names = [call[0][0] for call in mock_commands_manager.register.call_args_list]
            for command_name in expected_commands:
                assert command_name in registered_names, f"Command {command_name} was not registered"

    def test_register_all_commands_no_duplicates(self):
        """Test that commands are not re-registered if they already exist."""
        with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
            mock_registry = Mock()
            mock_commands_manager = Mock()
            mock_registry.commands = mock_commands_manager
            # Simulate some commands already registered
            mock_commands_manager.list_components.return_value = ["setup", "assess"]
            mock_registry_func.return_value = mock_registry

            register_all_commands()

            # Should only register commands that weren't already registered
            expected_new_commands = [
                "generate-contract", "list-assessments", "list-contracts",
                "view-logs", "show-config", "validate-contract", "show-contract",
                "scoring-explain", "scoring-preset-apply", "guide"
            ]

            assert mock_commands_manager.register.call_count == len(expected_new_commands)

            # Verify only new commands were registered
            registered_names = [call[0][0] for call in mock_commands_manager.register.call_args_list]
            for command_name in expected_new_commands:
                assert command_name in registered_names

            # Verify existing commands were not re-registered
            for existing_command in ["setup", "assess"]:
                assert existing_command not in registered_names

    def test_create_command_registry_success(self):
        """Test creating a command registry successfully."""
        with patch('src.adri.cli.registry.register_all_commands') as mock_register:
            with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
                mock_registry = Mock()
                mock_commands_manager = Mock()
                mock_registry.commands = mock_commands_manager

                # Mock command instances
                mock_setup_cmd = Mock()
                mock_assess_cmd = Mock()
                mock_commands_manager.list_components.return_value = ["setup", "assess"]
                mock_commands_manager.get_command.side_effect = lambda name: {
                    "setup": mock_setup_cmd,
                    "assess": mock_assess_cmd
                }[name]

                mock_registry_func.return_value = mock_registry

                result = create_command_registry()

                # Verify registration was called
                mock_register.assert_called_once()

                # Verify all commands are in the result
                assert "setup" in result
                assert "assess" in result
                assert result["setup"] == mock_setup_cmd
                assert result["assess"] == mock_assess_cmd

    def test_get_command_success(self):
        """Test successfully retrieving a command."""
        with patch('src.adri.cli.registry.register_all_commands') as mock_register:
            with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
                mock_registry = Mock()
                mock_commands_manager = Mock()
                mock_registry.commands = mock_commands_manager

                mock_setup_cmd = Mock()
                mock_commands_manager.get_command.return_value = mock_setup_cmd
                mock_registry_func.return_value = mock_registry

                result = get_command("setup")

                # Verify registration was called
                mock_register.assert_called_once()

                # Verify correct command was retrieved
                mock_commands_manager.get_command.assert_called_once_with("setup")
                assert result == mock_setup_cmd

    def test_get_command_not_found(self):
        """Test retrieving a non-existent command raises appropriate error."""
        with patch('src.adri.cli.registry.register_all_commands') as mock_register:
            with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
                mock_registry = Mock()
                mock_commands_manager = Mock()
                mock_registry.commands = mock_commands_manager

                # Simulate ComponentNotFoundError
                mock_commands_manager.get_command.side_effect = ComponentNotFoundError("nonexistent-command", "Command not found")
                mock_registry_func.return_value = mock_registry

                with pytest.raises(ComponentNotFoundError):
                    get_command("nonexistent-command")

    def test_list_available_commands_success(self):
        """Test listing all available commands."""
        with patch('src.adri.cli.registry.register_all_commands') as mock_register:
            with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
                mock_registry = Mock()
                mock_commands_manager = Mock()
                mock_registry.commands = mock_commands_manager

                expected_commands = ["setup", "assess", "generate-contract"]
                mock_commands_manager.list_components.return_value = expected_commands
                mock_registry_func.return_value = mock_registry

                result = list_available_commands()

                # Verify registration was called
                mock_register.assert_called_once()

                # Verify correct commands were listed
                assert result == expected_commands

    def test_list_available_commands_empty(self):
        """Test listing commands when none are registered."""
        with patch('src.adri.cli.registry.register_all_commands') as mock_register:
            with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
                mock_registry = Mock()
                mock_commands_manager = Mock()
                mock_registry.commands = mock_commands_manager

                mock_commands_manager.list_components.return_value = []
                mock_registry_func.return_value = mock_registry

                result = list_available_commands()

                # Verify registration was called
                mock_register.assert_called_once()

                # Verify empty list is returned
                assert result == []


class TestCommandRegistryIntegration(ModernCLITestBase):
    """Test command registry integration with real commands."""

    def test_registry_with_real_commands(self):
        """Test registry works with actual command classes."""
        # Import actual command classes
        from src.adri.cli.commands import SetupCommand, AssessCommand

        with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
            mock_registry = Mock()
            mock_commands_manager = Mock()
            mock_registry.commands = mock_commands_manager
            mock_commands_manager.list_components.return_value = []
            mock_registry_func.return_value = mock_registry

            register_all_commands()

            # Verify setup command was registered with correct class
            setup_call = None
            for call in mock_commands_manager.register.call_args_list:
                if call[0][0] == "setup":
                    setup_call = call
                    break

            assert setup_call is not None, "Setup command was not registered"
            assert setup_call[0][1] == SetupCommand, "Setup command registered with wrong class"

            # Verify assess command was registered with correct class
            assess_call = None
            for call in mock_commands_manager.register.call_args_list:
                if call[0][0] == "assess":
                    assess_call = call
                    break

            assert assess_call is not None, "Assess command was not registered"
            assert assess_call[0][1] == AssessCommand, "Assess command registered with wrong class"

    def test_command_execution_through_registry(self):
        """Test executing commands through the registry pattern."""
        mock_command = Mock()
        mock_command.execute.return_value = 0

        with patch('src.adri.cli.registry.get_command') as mock_get_command:
            mock_get_command.return_value = mock_command

            # Simulate getting and executing a command
            command = get_command("setup")
            result = command.execute({"force": True, "project_name": "test"})

            # Verify command was retrieved and executed
            mock_get_command.assert_called_once_with("setup")
            mock_command.execute.assert_called_once_with({"force": True, "project_name": "test"})
            assert result == 0

    def test_command_registry_error_handling(self):
        """Test error handling in command registry operations."""
        with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
            # Simulate registry failure
            mock_registry_func.side_effect = Exception("Registry initialization failed")

            with pytest.raises(Exception, match="Registry initialization failed"):
                register_all_commands()


class TestCommandRegistryPathResolution(ModernCLITestBase):
    """Test command registry with path resolution scenarios."""

    def test_registry_works_from_different_directories(self):
        """Test that registry works regardless of current working directory."""
        workspace = create_test_workspace()

        # Test from project root
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(workspace)

            with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
                mock_registry = Mock()
                mock_commands_manager = Mock()
                mock_registry.commands = mock_commands_manager
                mock_commands_manager.list_components.return_value = []
                mock_registry_func.return_value = mock_registry

                register_all_commands()

                # Should work from project root
                assert mock_commands_manager.register.called
                root_call_count = mock_commands_manager.register.call_count

                # Reset and test from subdirectory
                mock_commands_manager.reset_mock()

                # Test from subdirectory
                os.chdir(workspace / "ADRI" / "dev")
                register_all_commands()

                # Should work from subdirectory too
                assert mock_commands_manager.register.called
                subdir_call_count = mock_commands_manager.register.call_count

                # Should register same number of commands
                assert root_call_count == subdir_call_count

        finally:
            try:
                os.chdir(original_cwd)
            except (OSError, FileNotFoundError):
                os.chdir(Path.home())

    def test_command_registry_with_missing_project_structure(self):
        """Test registry behavior when ADRI project structure is missing."""
        # Test in a directory without ADRI structure
        temp_workspace = create_test_workspace()

        # Remove ADRI structure to simulate non-ADRI directory
        import shutil
        shutil.rmtree(temp_workspace / "ADRI")

        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_workspace)

            with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
                mock_registry = Mock()
                mock_commands_manager = Mock()
                mock_registry.commands = mock_commands_manager
                mock_commands_manager.list_components.return_value = []
                mock_registry_func.return_value = mock_registry

                # Should still work even without ADRI structure
                register_all_commands()

                # Commands should still be registered
                assert mock_commands_manager.register.called

        finally:
            try:
                os.chdir(original_cwd)
            except (OSError, FileNotFoundError):
                os.chdir(Path.home())


class TestCommandRegistryPerformance(ModernCLITestBase):
    """Test performance aspects of command registry."""

    def test_registry_caching_behavior(self):
        """Test that registry operations are properly cached."""
        with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
            mock_registry = Mock()
            mock_commands_manager = Mock()
            mock_registry.commands = mock_commands_manager
            mock_commands_manager.list_components.return_value = ["setup"]
            mock_registry_func.return_value = mock_registry

            # Call multiple times
            register_all_commands()
            register_all_commands()
            register_all_commands()

            # Global registry should be called each time (caching happens at registry level)
            assert mock_registry_func.call_count == 3

    def test_command_instantiation_performance(self):
        """Test that commands are instantiated efficiently."""
        with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
            mock_registry = Mock()
            mock_commands_manager = Mock()
            mock_registry.commands = mock_commands_manager

            # Mock multiple commands
            mock_commands = {
                "setup": Mock(),
                "assess": Mock(),
                "generate-contract": Mock()
            }

            mock_commands_manager.list_components.return_value = list(mock_commands.keys())
            mock_commands_manager.get_command.side_effect = lambda name: mock_commands[name]
            mock_registry_func.return_value = mock_registry

            # Create command registry
            result = create_command_registry()

            # Should have all commands
            assert len(result) == 3
            assert all(cmd_name in result for cmd_name in mock_commands.keys())

            # Each command should have been retrieved once
            assert mock_commands_manager.get_command.call_count == 3


class TestCommandRegistryErrorScenarios(ModernCLITestBase):
    """Test error scenarios in command registry."""

    def test_partial_command_registration_failure(self):
        """Test behavior when some commands fail to register."""
        with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
            mock_registry = Mock()
            mock_commands_manager = Mock()
            mock_registry.commands = mock_commands_manager
            mock_commands_manager.list_components.return_value = []

            # Simulate registration failure for some commands
            def register_side_effect(name, command_class):
                if name == "assess":
                    raise Exception("Failed to register assess command")

            mock_commands_manager.register.side_effect = register_side_effect
            mock_registry_func.return_value = mock_registry

            # Should raise exception when registration fails
            with pytest.raises(Exception, match="Failed to register assess command"):
                register_all_commands()

    def test_command_retrieval_with_corrupted_registry(self):
        """Test command retrieval when registry is in corrupted state."""
        with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
            mock_registry = Mock()
            mock_commands_manager = Mock()
            mock_registry.commands = mock_commands_manager

            # Simulate corrupted state
            mock_commands_manager.get_command.side_effect = Exception("Registry corrupted")
            mock_registry_func.return_value = mock_registry

            with pytest.raises(Exception, match="Registry corrupted"):
                get_command("setup")

    def test_empty_command_list_handling(self):
        """Test handling when no commands are available."""
        with patch('src.adri.cli.registry.get_global_registry') as mock_registry_func:
            mock_registry = Mock()
            mock_commands_manager = Mock()
            mock_registry.commands = mock_commands_manager
            mock_commands_manager.list_components.return_value = []
            mock_registry_func.return_value = mock_registry

            result = list_available_commands()

            # Should return empty list gracefully
            assert result == []

            # Creating registry with no commands should work
            registry = create_command_registry()
            assert registry == {}
