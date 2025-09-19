"""
Tests for ADRI CLI functionality.

Tests the streamlined CLI commands and functionality.
Consolidated from tests/unit/cli/test_*.py with updated imports for src/ layout.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path
import yaml
import json

# Updated imports for new src/ layout
from adri.cli import (
    setup_command,
    assess_command,
    generate_standard_command,
    validate_standard_command,
    list_standards_command,
    main
)


class TestSetupCommand(unittest.TestCase):
    """Test the setup command functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_setup_command_success(self):
        """Test successful setup command execution."""
        result = setup_command(project_name="test_project")

        self.assertEqual(result, 0)
        self.assertTrue(os.path.exists("ADRI/config.yaml"))

        # Check config content
        with open("ADRI/config.yaml", 'r') as f:
            config = yaml.safe_load(f)

        self.assertEqual(config["adri"]["project_name"], "test_project")
        self.assertIn("environments", config["adri"])

    def test_setup_command_force_overwrite(self):
        """Test setup command with force overwrite."""
        # Create ADRI directory and existing config
        os.makedirs("ADRI", exist_ok=True)
        with open("ADRI/config.yaml", 'w') as f:
            f.write("existing: config")

        result = setup_command(force=True, project_name="new_project")

        self.assertEqual(result, 0)

        # Check config was overwritten
        with open("ADRI/config.yaml", 'r') as f:
            config = yaml.safe_load(f)

        self.assertEqual(config["adri"]["project_name"], "new_project")

    def test_setup_command_existing_config_no_force(self):
        """Test setup command fails when config exists and no force."""
        # Create ADRI directory and existing config
        os.makedirs("ADRI", exist_ok=True)
        with open("ADRI/config.yaml", 'w') as f:
            f.write("existing: config")

        result = setup_command(project_name="test_project")

        self.assertEqual(result, 1)  # Should fail


class TestAssessCommand(unittest.TestCase):
    """Test the assess command functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_data = [
            {"name": "Alice", "age": 25, "email": "alice@test.com"},
            {"name": "Bob", "age": 30, "email": "bob@test.com"}
        ]

    @patch('adri.cli.load_data')
    @patch('adri.cli.DataQualityAssessor')
    def test_assess_command_success(self, mock_assessor_class, mock_load_data):
        """Test successful assess command execution."""
        # Setup mocks
        mock_load_data.return_value = self.sample_data
        mock_assessor = Mock()
        mock_result = Mock()
        mock_result.overall_score = 85.0
        mock_result.passed = True
        mock_result.to_standard_dict.return_value = {"score": 85.0}
        mock_assessor.assess.return_value = mock_result
        mock_assessor_class.return_value = mock_assessor

        result = assess_command("data.csv", "standard.yaml")

        self.assertEqual(result, 0)
        mock_load_data.assert_called_once_with("data.csv")
        mock_assessor.assess.assert_called_once()

    @patch('adri.cli.load_data')
    def test_assess_command_file_not_found(self, mock_load_data):
        """Test assess command with file not found."""
        mock_load_data.side_effect = FileNotFoundError("File not found")

        result = assess_command("missing.csv", "standard.yaml")

        self.assertEqual(result, 1)  # Should fail

    @patch('adri.cli.load_data')
    def test_assess_command_no_data(self, mock_load_data):
        """Test assess command with no data loaded."""
        mock_load_data.return_value = []

        result = assess_command("empty.csv", "standard.yaml")

        self.assertEqual(result, 1)  # Should fail


class TestGenerateStandardCommand(unittest.TestCase):
    """Test the generate-standard command functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        self.sample_data = [
            {"name": "Alice", "age": 25, "email": "alice@test.com"},
            {"name": "Bob", "age": 30, "email": "bob@test.com"}
        ]

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('adri.cli.load_data')
    def test_generate_standard_success(self, mock_load_data):
        """Test successful standard generation."""
        mock_load_data.return_value = self.sample_data

        result = generate_standard_command("data.csv")

        self.assertEqual(result, 0)
        self.assertTrue(os.path.exists("data_ADRI_standard.yaml"))

        # Check generated standard
        with open("data_ADRI_standard.yaml", 'r') as f:
            standard = yaml.safe_load(f)

        self.assertIn("standards", standard)
        self.assertIn("requirements", standard)

    @patch('adri.cli.load_data')
    def test_generate_standard_existing_file_no_force(self, mock_load_data):
        """Test generate command fails when file exists and no force."""
        mock_load_data.return_value = self.sample_data

        # Create existing standard
        with open("data_ADRI_standard.yaml", 'w') as f:
            f.write("existing: standard")

        result = generate_standard_command("data.csv")

        self.assertEqual(result, 1)  # Should fail

    @patch('adri.cli.load_data')
    def test_generate_standard_force_overwrite(self, mock_load_data):
        """Test generate command with force overwrite."""
        mock_load_data.return_value = self.sample_data

        # Create existing standard
        with open("data_ADRI_standard.yaml", 'w') as f:
            f.write("existing: standard")

        result = generate_standard_command("data.csv", force=True)

        self.assertEqual(result, 0)

        # Check standard was overwritten
        with open("data_ADRI_standard.yaml", 'r') as f:
            standard = yaml.safe_load(f)

        self.assertIn("standards", standard)
        self.assertIn("requirements", standard)


class TestValidateStandardCommand(unittest.TestCase):
    """Test the validate-standard command functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('adri.cli.load_standard')
    def test_validate_standard_success(self, mock_load_standard):
        """Test successful standard validation."""
        mock_load_standard.return_value = {
            "standards": {
                "id": "test_standard",
                "name": "Test Standard",
                "version": "1.0.0",
                "authority": "ADRI Framework"
            },
            "requirements": {
                "overall_minimum": 75.0
            }
        }

        result = validate_standard_command("test_standard.yaml")

        self.assertEqual(result, 0)

    @patch('adri.cli.load_standard')
    def test_validate_standard_missing_sections(self, mock_load_standard):
        """Test standard validation with missing sections."""
        mock_load_standard.return_value = {
            "standards": {
                "id": "test_standard",
                "name": "Test Standard"
                # Missing version and authority
            }
            # Missing requirements section
        }

        result = validate_standard_command("test_standard.yaml")

        self.assertEqual(result, 1)  # Should fail

    @patch('adri.cli.load_standard')
    def test_validate_standard_file_error(self, mock_load_standard):
        """Test standard validation with file loading error."""
        mock_load_standard.side_effect = FileNotFoundError("File not found")

        result = validate_standard_command("missing_standard.yaml")

        self.assertEqual(result, 1)  # Should fail


class TestListStandardsCommand(unittest.TestCase):
    """Test the list-standards command functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('adri.cli.StandardsParser')
    def test_list_standards_with_bundled(self, mock_parser_class):
        """Test list standards with bundled standards available."""
        mock_parser = Mock()
        mock_parser.list_available_standards.return_value = ["standard1", "standard2"]
        mock_parser_class.return_value = mock_parser

        result = list_standards_command()

        self.assertEqual(result, 0)
        mock_parser.list_available_standards.assert_called_once()

    def test_list_standards_with_project_standards(self):
        """Test list standards with project standards."""
        # Create project standards directory and files
        standards_dir = Path("ADRI/dev/standards")
        standards_dir.mkdir(parents=True)

        (standards_dir / "project_standard1.yaml").touch()
        (standards_dir / "project_standard2.yaml").touch()

        result = list_standards_command()

        self.assertEqual(result, 0)

    @patch('adri.cli.StandardsParser')
    def test_list_standards_no_standards(self, mock_parser_class):
        """Test list standards when no standards are found."""
        mock_parser = Mock()
        mock_parser.list_available_standards.return_value = []
        mock_parser_class.return_value = mock_parser

        result = list_standards_command()

        self.assertEqual(result, 0)  # Should still succeed but show message


class TestCLIUtilities(unittest.TestCase):
    """Test CLI utility functions and edge cases."""

    @patch('adri.cli.cli')
    def test_main_function(self, mock_cli):
        """Test main CLI entry point."""
        main()
        mock_cli.assert_called_once()

    def test_import_availability(self):
        """Test that all required imports are available."""
        # This test ensures the CLI can import all its dependencies
        import adri.cli as cli_module

        # Check that key functions exist
        self.assertTrue(hasattr(cli_module, 'setup_command'))
        self.assertTrue(hasattr(cli_module, 'assess_command'))
        self.assertTrue(hasattr(cli_module, 'generate_standard_command'))
        self.assertTrue(hasattr(cli_module, 'validate_standard_command'))
        self.assertTrue(hasattr(cli_module, 'list_standards_command'))
        self.assertTrue(hasattr(cli_module, 'main'))


if __name__ == '__main__':
    unittest.main()
