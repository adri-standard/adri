"""Tests for the guide command implementation.

This module tests the new unified guide command that replaces
the scattered --guide flags across individual commands.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.adri.cli.commands.guide import GuideCommand


class TestGuideCommand:
    """Test suite for the GuideCommand class."""

    def test_guide_command_instantiation(self):
        """Test that GuideCommand can be instantiated."""
        cmd = GuideCommand()
        assert cmd is not None
        assert cmd.tutorial_path == Path("ADRI/tutorials/invoice_processing")
        assert cmd.steps_completed == []

    def test_guide_command_name(self):
        """Test that command returns correct name."""
        cmd = GuideCommand()
        assert cmd.get_name() == "guide"

    def test_guide_command_description(self):
        """Test that command returns a description."""
        cmd = GuideCommand()
        description = cmd.get_description()
        assert description is not None
        assert len(description) > 0
        assert "guide" in description.lower() or "first" in description.lower()

    @patch('src.adri.cli.commands.guide.click.echo')
    def test_welcome_step_displays_content(self, mock_echo):
        """Test that welcome step displays expected content."""
        cmd = GuideCommand()
        result = cmd._welcome_step()

        assert result is True
        assert mock_echo.call_count > 0

        # Check that welcome messages were displayed
        calls = [str(call) for call in mock_echo.call_args_list]
        all_output = ' '.join(calls)

        assert 'ADRI' in all_output or 'Welcome' in all_output

    @patch('src.adri.cli.commands.guide.Path.exists')
    @patch('src.adri.cli.commands.guide.click.echo')
    def test_setup_step_when_already_configured(self, mock_echo, mock_exists):
        """Test setup step when project is already configured."""
        mock_exists.return_value = True

        cmd = GuideCommand()
        result = cmd._setup_step()

        assert result is True
        assert mock_echo.call_count > 0

    @patch('src.adri.cli.commands.guide.click.echo')
    def test_decorator_example_step(self, mock_echo):
        """Test that decorator example step displays code."""
        cmd = GuideCommand()
        result = cmd._decorator_example_step()

        assert result is True
        assert mock_echo.call_count > 0

        # Check that code example was shown
        calls = [str(call) for call in mock_echo.call_args_list]
        all_output = ' '.join(calls)

        assert 'adri_assess' in all_output or 'decorator' in all_output.lower()

    @patch('src.adri.cli.commands.guide.Path.exists')
    @patch('src.adri.cli.commands.guide.click.echo')
    def test_generate_standard_step_missing_data(self, mock_echo, mock_exists):
        """Test generate standard step when training data is missing."""
        mock_exists.return_value = False

        cmd = GuideCommand()
        result = cmd._generate_standard_step()

        assert result is False
        assert mock_echo.call_count > 0

    @patch('src.adri.cli.commands.guide.Path.exists')
    @patch('src.adri.cli.commands.guide.click.echo')
    def test_assess_data_step_missing_files(self, mock_echo, mock_exists):
        """Test assess step when files are missing."""
        mock_exists.return_value = False

        cmd = GuideCommand()
        result = cmd._assess_data_step()

        assert result is False
        assert mock_echo.call_count > 0

    @patch('src.adri.cli.commands.view_logs.ViewLogsCommand')
    @patch('src.adri.cli.commands.guide.click.echo')
    def test_view_results_step(self, mock_echo, mock_view_logs_cmd):
        """Test view results step."""
        mock_instance = Mock()
        mock_instance.execute.return_value = 0
        mock_view_logs_cmd.return_value = mock_instance

        cmd = GuideCommand()
        result = cmd._view_results_step()

        assert result is True
        assert mock_echo.call_count > 0

    @patch('src.adri.cli.commands.guide.click.echo')
    def test_next_steps_conclusion(self, mock_echo):
        """Test next steps conclusion displays guidance."""
        cmd = GuideCommand()
        result = cmd._next_steps_conclusion()

        assert result is True
        assert mock_echo.call_count > 0

        # Check that completion message and next steps were shown
        calls = [str(call) for call in mock_echo.call_args_list]
        all_output = ' '.join(calls)

        assert 'complete' in all_output.lower() or 'next' in all_output.lower()

    def test_execute_returns_integer(self):
        """Test that execute returns an integer exit code."""
        cmd = GuideCommand()
        args = {}

        # Mock all the step methods to return True quickly
        with patch.object(cmd, '_welcome_step', return_value=True), \
             patch.object(cmd, '_setup_step', return_value=True), \
             patch.object(cmd, '_decorator_example_step', return_value=True), \
             patch.object(cmd, '_generate_standard_step', return_value=True), \
             patch.object(cmd, '_assess_data_step', return_value=True), \
             patch.object(cmd, '_view_results_step', return_value=True), \
             patch.object(cmd, '_next_steps_conclusion', return_value=True):

            result = cmd.execute(args)
            assert isinstance(result, int)
            assert result == 0

    def test_execute_handles_keyboard_interrupt(self):
        """Test that execute handles KeyboardInterrupt gracefully."""
        cmd = GuideCommand()
        args = {}

        with patch.object(cmd, '_welcome_step', side_effect=KeyboardInterrupt):
            result = cmd.execute(args)
            assert isinstance(result, int)
            assert result == 130  # Standard exit code for SIGINT

    def test_execute_handles_exceptions(self):
        """Test that execute handles general exceptions."""
        cmd = GuideCommand()
        args = {}

        with patch.object(cmd, '_welcome_step', side_effect=Exception("Test error")):
            result = cmd.execute(args)
            assert isinstance(result, int)
            assert result != 0

    def test_guide_step_failure_stops_execution(self):
        """Test that if a step fails, execution stops."""
        cmd = GuideCommand()
        args = {}

        # Make the setup step fail
        with patch.object(cmd, '_welcome_step', return_value=True), \
             patch.object(cmd, '_setup_step', return_value=False), \
             patch.object(cmd, '_decorator_example_step') as mock_decorator:

            result = cmd.execute(args)

            # Should stop after setup fails, so decorator step should not be called
            mock_decorator.assert_not_called()
            assert result == 1


class TestGuideCommandIntegration:
    """Integration tests for guide command with other commands."""

    @patch('src.adri.cli.commands.setup.SetupCommand')
    @patch('src.adri.cli.commands.guide.Path.exists')
    def test_guide_calls_setup_command(self, mock_exists, mock_setup_cmd):
        """Test that guide properly calls setup command."""
        mock_exists.return_value = False
        mock_instance = Mock()
        mock_instance.execute.return_value = 0
        mock_setup_cmd.return_value = mock_instance

        cmd = GuideCommand()
        result = cmd._setup_step()

        assert mock_instance.execute.called

    @patch('src.adri.cli.commands.generate_contract.GenerateContractCommand')
    @patch('src.adri.cli.commands.guide.Path.exists')
    def test_guide_calls_generate_standard_command(self, mock_exists, mock_gen_cmd):
        """Test that guide properly calls generate-standard command."""
        mock_exists.return_value = True
        mock_instance = Mock()
        mock_instance.execute.return_value = 0
        mock_gen_cmd.return_value = mock_instance

        cmd = GuideCommand()
        result = cmd._generate_standard_step()

        assert mock_instance.execute.called

    @patch('src.adri.cli.commands.assess.AssessCommand')
    @patch('src.adri.cli.commands.guide.Path.exists')
    def test_guide_calls_assess_command(self, mock_exists, mock_assess_cmd):
        """Test that guide properly calls assess command."""
        mock_exists.return_value = True
        mock_instance = Mock()
        mock_instance.execute.return_value = 0
        mock_assess_cmd.return_value = mock_instance

        cmd = GuideCommand()
        result = cmd._assess_data_step()

        assert mock_instance.execute.called

    @patch('src.adri.cli.commands.view_logs.ViewLogsCommand')
    def test_guide_calls_view_logs_command(self, mock_logs_cmd):
        """Test that guide properly calls view-logs command."""
        mock_instance = Mock()
        mock_instance.execute.return_value = 0
        mock_logs_cmd.return_value = mock_instance

        cmd = GuideCommand()
        result = cmd._view_results_step()

        assert mock_instance.execute.called


class TestGuideCommandCLIIntegration:
    """Test guide command integration with CLI."""

    def test_guide_command_registered(self):
        """Test that guide command is registered in the registry."""
        from src.adri.cli.registry import list_available_commands

        commands = list_available_commands()
        assert 'guide' in commands

    def test_guide_command_can_be_retrieved(self):
        """Test that guide command can be retrieved from registry."""
        from src.adri.cli.registry import get_command

        cmd = get_command('guide')
        assert cmd is not None
        assert isinstance(cmd, GuideCommand)

    def test_guide_command_in_cli_exports(self):
        """Test that GuideCommand is exported from commands module."""
        from src.adri.cli.commands import GuideCommand as ExportedGuideCommand

        assert ExportedGuideCommand is not None
        assert ExportedGuideCommand == GuideCommand
