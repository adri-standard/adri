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
    show_config_command,
    list_assessments_command,
    view_logs_command,
    show_standard_command,
    show_help_guide,
    create_sample_files,
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
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Create ADRI project structure for path resolution
        setup_command(force=True, project_name="test_project")

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
    @patch('adri.cli.load_standard')
    @patch('adri.cli.DataQualityAssessor')
    def test_assess_command_success(self, mock_assessor_class, mock_load_standard, mock_load_data):
        """Test successful assess command execution."""
        # Create test files in absolute paths to bypass path resolution
        import tempfile
        data_file = Path(tempfile.mktemp(suffix=".csv"))
        standard_file = Path(tempfile.mktemp(suffix=".yaml"))

        try:
            # Create test data file
            with open(data_file, 'w') as f:
                f.write("name,age,email\nAlice,25,alice@test.com\nBob,30,bob@test.com")

            # Create test standard file
            with open(standard_file, 'w') as f:
                yaml.dump({"standards": {"name": "Test"}, "requirements": {}}, f)

            # Setup mocks
            mock_load_data.return_value = self.sample_data
            mock_load_standard.return_value = {"standards": {"name": "Test"}, "requirements": {}}
            mock_assessor = Mock()
            mock_result = Mock()
            mock_result.overall_score = 85.0
            mock_result.passed = True
            mock_result.to_standard_dict.return_value = {"score": 85.0}
            mock_assessor.assess.return_value = mock_result
            mock_assessor.audit_logger = None
            mock_assessor_class.return_value = mock_assessor

            # Use absolute paths to bypass path resolution
            result = assess_command(str(data_file), str(standard_file))

            self.assertEqual(result, 0)
            mock_load_data.assert_called_once()
            mock_assessor.assess.assert_called_once()

        finally:
            # Clean up temporary files
            if data_file.exists():
                data_file.unlink()
            if standard_file.exists():
                standard_file.unlink()

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

        # Create ADRI directory structure that enhanced CLI expects
        os.makedirs("ADRI/dev/standards", exist_ok=True)

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

        # Create test data file using absolute path to bypass path resolution
        import tempfile
        data_file = Path(tempfile.mktemp(suffix=".csv"))

        try:
            # Create test data file
            with open(data_file, 'w') as f:
                f.write("name,age,email\nAlice,25,alice@test.com\nBob,30,bob@test.com")

            # Use absolute path to bypass path resolution issues
            result = generate_standard_command(str(data_file))

            self.assertEqual(result, 0)
            # Enhanced CLI saves to ADRI/dev/standards/ directory
            standard_path = f"ADRI/dev/standards/{data_file.stem}_ADRI_standard.yaml"
            self.assertTrue(os.path.exists(standard_path))

            # Check generated standard
            with open(standard_path, 'r') as f:
                standard = yaml.safe_load(f)

            self.assertIn("standards", standard)
            self.assertIn("requirements", standard)
            # Verify enhanced CLI added record identification
            self.assertIn("record_identification", standard)

        finally:
            # Clean up temporary file
            if data_file.exists():
                data_file.unlink()

    @patch('adri.cli.load_data')
    def test_generate_standard_existing_file_no_force(self, mock_load_data):
        """Test generate command fails when file exists and no force."""
        mock_load_data.return_value = self.sample_data

        # Create test data file using absolute path
        import tempfile
        data_file = Path(tempfile.mktemp(suffix=".csv"))

        try:
            # Create test data file
            with open(data_file, 'w') as f:
                f.write("name,age,email\nAlice,25,alice@test.com\nBob,30,bob@test.com")

            # Create existing standard in the correct location
            standard_path = f"ADRI/dev/standards/{data_file.stem}_ADRI_standard.yaml"
            with open(standard_path, 'w') as f:
                f.write("existing: standard")

            # Use absolute path
            result = generate_standard_command(str(data_file))

            self.assertEqual(result, 1)  # Should fail

        finally:
            # Clean up temporary file
            if data_file.exists():
                data_file.unlink()

    @patch('adri.cli.load_data')
    def test_generate_standard_force_overwrite(self, mock_load_data):
        """Test generate command with force overwrite."""
        mock_load_data.return_value = self.sample_data

        # Create test data file using absolute path
        import tempfile
        data_file = Path(tempfile.mktemp(suffix=".csv"))

        try:
            # Create test data file
            with open(data_file, 'w') as f:
                f.write("name,age,email\nAlice,25,alice@test.com\nBob,30,bob@test.com")

            # Create existing standard in the correct location
            standard_path = f"ADRI/dev/standards/{data_file.stem}_ADRI_standard.yaml"
            with open(standard_path, 'w') as f:
                f.write("existing: standard")

            # Use absolute path with force=True
            result = generate_standard_command(str(data_file), force=True)

            self.assertEqual(result, 0)

            # Check standard was overwritten in the correct location
            with open(standard_path, 'r') as f:
                standard = yaml.safe_load(f)

            self.assertIn("standards", standard)
            self.assertIn("requirements", standard)
            # Verify enhanced CLI added record identification
            self.assertIn("record_identification", standard)

        finally:
            # Clean up temporary file
            if data_file.exists():
                data_file.unlink()


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

    def test_list_standards_local_only(self):
        """Test list standards shows local dev/prod standards without remote catalog."""
        # Create project standards directories and files
        dev_dir = Path("ADRI/dev/standards")
        prod_dir = Path("ADRI/prod/standards")
        dev_dir.mkdir(parents=True, exist_ok=True)
        prod_dir.mkdir(parents=True, exist_ok=True)

        (dev_dir / "project_standard1.yaml").touch()
        (prod_dir / "project_standard2.yaml").touch()

        result = list_standards_command()

        self.assertEqual(result, 0)

    def test_list_standards_with_project_standards(self):
        """Test list standards with project standards."""
        # Create project standards directory and files
        standards_dir = Path("ADRI/dev/standards")
        standards_dir.mkdir(parents=True, exist_ok=True)

        (standards_dir / "project_standard1.yaml").touch()
        (standards_dir / "project_standard2.yaml").touch()

        result = list_standards_command()

        self.assertEqual(result, 0)

    def test_list_standards_no_standards(self):
        """Test list standards when no local standards are found."""
        result = list_standards_command()
        self.assertEqual(result, 0)  # Should still succeed but show message


class TestShowConfigCommand(unittest.TestCase):
    """Test the show-config command functionality."""

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

    @patch('adri.cli.ConfigurationLoader')
    def test_show_config_success(self, mock_config_class):
        """Test successful config display."""
        # Setup mock
        mock_loader = Mock()
        mock_config = {
            "adri": {
                "project_name": "test_project",
                "version": "4.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "ADRI/dev/standards",
                            "assessments": "ADRI/dev/assessments"
                        }
                    }
                }
            }
        }
        mock_loader.get_active_config.return_value = mock_config
        mock_config_class.return_value = mock_loader

        result = show_config_command()

        self.assertEqual(result, 0)
        mock_loader.get_active_config.assert_called_once()

    @patch('adri.cli.ConfigurationLoader')
    def test_show_config_no_config(self, mock_config_class):
        """Test show config when no config exists."""
        mock_loader = Mock()
        mock_loader.get_active_config.return_value = None
        mock_config_class.return_value = mock_loader

        result = show_config_command()

        self.assertEqual(result, 1)


class TestListAssessmentsCommand(unittest.TestCase):
    """Test the list-assessments command functionality."""

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

    def test_list_assessments_no_directory(self):
        """Test list assessments when no assessments directory exists."""
        result = list_assessments_command()
        self.assertEqual(result, 0)

    def test_list_assessments_empty_directory(self):
        """Test list assessments with empty assessments directory."""
        assessments_dir = Path("ADRI/dev/assessments")
        assessments_dir.mkdir(parents=True, exist_ok=True)

        result = list_assessments_command()
        self.assertEqual(result, 0)

    def test_list_assessments_with_reports(self):
        """Test list assessments with existing assessment reports."""
        assessments_dir = Path("ADRI/dev/assessments")
        assessments_dir.mkdir(parents=True, exist_ok=True)

        # Create sample assessment report
        sample_report = {
            "adri_assessment_report": {
                "summary": {
                    "overall_score": 85.0,
                    "overall_passed": True
                }
            }
        }

        with open(assessments_dir / "test_assessment_20240101_120000.json", "w") as f:
            json.dump(sample_report, f)

        result = list_assessments_command()
        self.assertEqual(result, 0)


class TestViewLogsCommand(unittest.TestCase):
    """Test the view-logs command functionality."""

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

    def test_view_logs_no_directory(self):
        """Test view logs when no logs directory exists."""
        result = view_logs_command()
        self.assertEqual(result, 0)

    def test_view_logs_no_files(self):
        """Test view logs when logs directory exists but no files."""
        logs_dir = Path("ADRI/dev/audit-logs")
        logs_dir.mkdir(parents=True, exist_ok=True)

        result = view_logs_command()
        self.assertEqual(result, 0)

    def test_view_logs_with_data(self):
        """Test view logs with actual log data."""
        logs_dir = Path("ADRI/dev/audit-logs")
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Create sample audit log
        import csv
        with open(logs_dir / "adri_assessment_logs.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "assessment_id", "overall_score", "passed", "data_row_count", "function_name", "standard_id", "assessment_duration_ms", "execution_decision"])
            writer.writerow(["2024-01-01 12:00:00", "test_001", "85.0", "TRUE", "100", "assess", "test_standard", "150", "ALLOW"])

        result = view_logs_command()
        self.assertEqual(result, 0)


class TestShowStandardCommand(unittest.TestCase):
    """Test the show-standard command functionality."""

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
    def test_show_standard_success(self, mock_load_standard):
        """Test successful standard display."""
        # Create a real file for the existence check
        with open("test_standard.yaml", "w") as f:
            f.write("test: standard")

        mock_standard = {
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
        mock_load_standard.return_value = mock_standard

        result = show_standard_command("test_standard.yaml")
        self.assertEqual(result, 0)
        mock_load_standard.assert_called_once_with("test_standard.yaml")

    def test_show_standard_file_not_found(self):
        """Test show standard when file not found."""
        result = show_standard_command("nonexistent.yaml")
        self.assertEqual(result, 1)


class TestHelpGuideCommand(unittest.TestCase):
    """Test the help-guide command functionality."""

    def test_help_guide_execution(self):
        """Test help guide executes successfully."""
        result = show_help_guide()
        self.assertEqual(result, 0)


class TestSampleFilesCreation(unittest.TestCase):
    """Test the create_sample_files function."""

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

    def test_create_sample_files(self):
        """Test sample files creation."""
        create_sample_files()

        # Check files were created in new tutorial structure
        self.assertTrue(Path("ADRI/tutorials/invoice_processing/invoice_data.csv").exists())
        self.assertTrue(Path("ADRI/tutorials/invoice_processing/test_invoice_data.csv").exists())

        # Check content is not empty
        with open("ADRI/tutorials/invoice_processing/invoice_data.csv") as f:
            content = f.read()
            self.assertIn("invoice_id", content)
            self.assertIn("INV-001", content)


class TestEnhancedCommandFeatures(unittest.TestCase):
    """Test enhanced features of existing commands."""

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

    def test_setup_command_with_guide(self):
        """Test setup command with guide mode."""
        result = setup_command(guide=True, project_name="test_project")

        # Should create directories and sample files in new tutorial structure
        self.assertEqual(result, 0)
        self.assertTrue(Path("ADRI/config.yaml").exists())
        self.assertTrue(Path("ADRI/tutorials/invoice_processing/invoice_data.csv").exists())
        self.assertTrue(Path("ADRI/tutorials/invoice_processing/test_invoice_data.csv").exists())

    @patch('adri.cli.load_data')
    def test_generate_standard_with_guide(self, mock_load_data):
        """Test generate standard with guide mode."""
        mock_load_data.return_value = [
            {"name": "Alice", "age": 25, "email": "alice@test.com"},
            {"name": "Bob", "age": 30, "email": "bob@test.com"}
        ]

        # Create directory structure
        Path("ADRI/dev/standards").mkdir(parents=True, exist_ok=True)

        # Create test data file using absolute path
        import tempfile
        data_file = Path(tempfile.mktemp(suffix=".csv"))

        try:
            # Create test data file
            with open(data_file, 'w') as f:
                f.write("name,age,email\nAlice,25,alice@test.com\nBob,30,bob@test.com")

            # Use absolute path for guide mode test
            result = generate_standard_command(str(data_file), guide=True)

            self.assertEqual(result, 0)
            self.assertTrue(Path(f"ADRI/dev/standards/{data_file.stem}_ADRI_standard.yaml").exists())

        finally:
            # Clean up temporary file
            if data_file.exists():
                data_file.unlink()


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

        # Check enhanced commands exist
        self.assertTrue(hasattr(cli_module, 'show_config_command'))
        self.assertTrue(hasattr(cli_module, 'list_assessments_command'))
        self.assertTrue(hasattr(cli_module, 'view_logs_command'))
        self.assertTrue(hasattr(cli_module, 'show_standard_command'))
        self.assertTrue(hasattr(cli_module, 'show_help_guide'))
        self.assertTrue(hasattr(cli_module, 'create_sample_files'))


if __name__ == '__main__':
    unittest.main()
