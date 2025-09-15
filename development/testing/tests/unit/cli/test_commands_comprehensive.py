"""
Comprehensive tests for CLI commands module to achieve 85%+ coverage.
Tests all major functions, error handling, and edge cases.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import yaml

from adri.cli.commands import (
    setup_command,
    assess_command,
    generate_adri_standard_command,
    validate_standard_command,
    show_config_command,
    list_standards_command,
    load_data,
    load_standard,
    validate_yaml_standard,
    _resolve_data_path,
    _resolve_standard_path,
    _load_csv_data,
    _load_json_data,
    _format_file_size,
    _count_csv_rows,
    list_training_data_command,
    list_assessments_command,
    clean_cache_command,
    export_report_command,
    show_standard_command,
    explain_failure_command
)


class TestSetupCommand(unittest.TestCase):
    """Test setup command functionality."""

    @patch('adri.cli.commands.ConfigManager')
    @patch('adri.cli.commands.Path')
    @patch('adri.cli.commands.os.path.exists')
    def test_setup_command_success(self, mock_exists, mock_path, mock_config_manager):
        """Test successful setup."""
        # Mock no existing config
        mock_exists.return_value = False
        
        # Mock config manager
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.create_default_config.return_value = {"test": "config"}
        
        # Mock path operations
        mock_path.cwd.return_value.name = "test_project"
        mock_path.return_value.parent = mock_path.return_value
        mock_path.return_value.__eq__.return_value = False
        
        result = setup_command()
        
        self.assertEqual(result, 0)
        mock_manager.create_default_config.assert_called_once_with("test_project")
        mock_manager.save_config.assert_called_once()
        mock_manager.create_directory_structure.assert_called_once()

    @patch('adri.cli.commands.os.path.exists')
    def test_setup_command_existing_config_no_force(self, mock_exists):
        """Test setup with existing config and no force flag."""
        mock_exists.return_value = True
        
        result = setup_command(force=False)
        
        self.assertEqual(result, 1)

    @patch('adri.cli.commands.ConfigManager')
    def test_setup_command_permission_error(self, mock_config_manager):
        """Test setup with permission error."""
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.save_config.side_effect = PermissionError("Access denied")
        
        result = setup_command()
        
        self.assertEqual(result, 1)

    @patch('adri.cli.commands.ConfigManager')
    def test_setup_command_generic_error(self, mock_config_manager):
        """Test setup with generic error."""
        mock_config_manager.side_effect = Exception("Generic error")
        
        result = setup_command()
        
        self.assertEqual(result, 1)


class TestAssessCommand(unittest.TestCase):
    """Test assess command functionality."""

    @patch('adri.cli.commands.ConfigManager')
    @patch('adri.cli.commands.load_data')
    @patch('adri.cli.commands.load_standard')
    @patch('adri.cli.commands.AssessmentEngine')
    @patch('adri.cli.commands.Path')
    @patch('pandas.DataFrame')
    def test_assess_command_success(self, mock_df, mock_path, mock_engine, 
                                   mock_load_standard, mock_load_data, mock_config_manager):
        """Test successful assessment."""
        # Mock config manager
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = {
            "adri": {
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "training_data": "/path/to/data",
                            "standards": "/path/to/standards",
                            "assessments": "/path/to/assessments"
                        }
                    }
                },
                "assessment": {"performance": {"max_rows": 1000}}
            }
        }
        mock_manager.get_environment_config.return_value = {
            "paths": {
                "training_data": "/path/to/data",
                "standards": "/path/to/standards", 
                "assessments": "/path/to/assessments"
            }
        }
        
        # Mock data loading
        mock_load_data.return_value = [{"field1": "value1", "field2": "value2"}]
        mock_load_standard.return_value = {"standards": {"name": "test"}}
        
        # Mock assessment engine
        mock_assessment = MagicMock()
        mock_assessment.overall_score = 85.0
        mock_assessment.passed = True
        mock_assessment.dimension_scores = {}
        mock_assessment.to_standard_dict.return_value = {"test": "result"}
        mock_engine.return_value.assess.return_value = mock_assessment
        
        # Mock path operations
        mock_path.return_value.parent.mkdir.return_value = None
        mock_path.return_value.stem = "test_data"
        
        with patch('builtins.open', mock_open()):
            result = assess_command("data.csv", "standard.yaml")
        
        self.assertEqual(result, 0)

    @patch('adri.cli.commands.ConfigManager')
    def test_assess_command_no_config(self, mock_config_manager):
        """Test assess command with no configuration."""
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = None
        
        result = assess_command("data.csv", "standard.yaml")
        
        self.assertEqual(result, 1)

    @patch('adri.cli.commands.ConfigManager')
    @patch('adri.cli.commands.load_data')
    def test_assess_command_no_data(self, mock_load_data, mock_config_manager):
        """Test assess command with no data loaded."""
        # Mock config
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = {"adri": {"environments": {"development": {"paths": {}}}}}
        mock_manager.get_environment_config.return_value = {"paths": {}}
        
        # No data loaded
        mock_load_data.return_value = []
        
        result = assess_command("data.csv", "standard.yaml")
        
        self.assertEqual(result, 1)

    @patch('adri.cli.commands.ConfigManager')
    def test_assess_command_file_not_found(self, mock_config_manager):
        """Test assess command with file not found."""
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = {"adri": {"environments": {"development": {"paths": {}}}}}
        mock_manager.get_environment_config.side_effect = FileNotFoundError("File not found")
        
        result = assess_command("data.csv", "standard.yaml")
        
        self.assertEqual(result, 1)


class TestDataLoading(unittest.TestCase):
    """Test data loading functions."""

    def test_load_data_file_not_found(self):
        """Test loading non-existent file."""
        with self.assertRaises(FileNotFoundError):
            load_data("nonexistent.csv")

    @patch('adri.cli.commands.os.path.exists')
    def test_load_data_unsupported_format(self, mock_exists):
        """Test loading unsupported file format."""
        mock_exists.return_value = True
        
        with self.assertRaises(ValueError):
            load_data("data.txt")

    @patch('adri.cli.commands._load_csv_data')
    @patch('adri.cli.commands.os.path.exists')
    def test_load_csv_data_success(self, mock_exists, mock_load_csv):
        """Test successful CSV loading."""
        mock_exists.return_value = True
        mock_load_csv.return_value = [{"field1": "value1"}]
        
        result = load_data("data.csv")
        
        self.assertEqual(result, [{"field1": "value1"}])

    @patch('adri.cli.commands._load_json_data') 
    @patch('adri.cli.commands.os.path.exists')
    def test_load_json_data_success(self, mock_exists, mock_load_json):
        """Test successful JSON loading."""
        mock_exists.return_value = True
        mock_load_json.return_value = [{"field1": "value1"}]
        
        result = load_data("data.json")
        
        self.assertEqual(result, [{"field1": "value1"}])

    def test_load_csv_data_with_content(self):
        """Test loading CSV data with actual content."""
        csv_content = "field1,field2\nvalue1,value2\nvalue3,value4"
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            from pathlib import Path
            result = _load_csv_data(Path("test.csv"))
        
        expected = [
            {"field1": "value1", "field2": "value2"},
            {"field1": "value3", "field2": "value4"}
        ]
        self.assertEqual(result, expected)

    def test_load_csv_data_empty_file(self):
        """Test loading empty CSV file."""
        with patch('builtins.open', mock_open(read_data="")):
            from pathlib import Path
            with self.assertRaises(ValueError):
                _load_csv_data(Path("empty.csv"))

    def test_load_json_data_with_content(self):
        """Test loading JSON data with actual content."""
        json_content = '[{"field1": "value1"}, {"field1": "value2"}]'
        
        with patch('builtins.open', mock_open(read_data=json_content)):
            from pathlib import Path
            result = _load_json_data(Path("test.json"))
        
        expected = [{"field1": "value1"}, {"field1": "value2"}]
        self.assertEqual(result, expected)

    def test_load_json_data_invalid_format(self):
        """Test loading JSON with invalid format."""
        json_content = '{"not": "a list"}'
        
        with patch('builtins.open', mock_open(read_data=json_content)):
            from pathlib import Path
            with self.assertRaises(ValueError):
                _load_json_data(Path("test.json"))


class TestStandardLoading(unittest.TestCase):
    """Test standard loading and validation."""

    def test_load_standard_file_not_found(self):
        """Test loading non-existent standard."""
        with self.assertRaises(FileNotFoundError):
            load_standard("nonexistent.yaml")

    @patch('adri.cli.commands.os.path.exists')
    def test_load_standard_success(self, mock_exists):
        """Test successful standard loading."""
        mock_exists.return_value = True
        yaml_content = """
        standards:
          name: "Test Standard"
          version: "1.0.0"
        """
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            result = load_standard("test.yaml")
        
        self.assertIn("standards", result)
        self.assertEqual(result["standards"]["name"], "Test Standard")

    @patch('adri.cli.commands.os.path.exists')
    def test_load_standard_invalid_yaml(self, mock_exists):
        """Test loading standard with invalid YAML."""
        mock_exists.return_value = True
        
        with patch('builtins.open', mock_open(read_data="invalid: yaml: content: [")):
            with self.assertRaises(Exception):
                load_standard("invalid.yaml")


class TestStandardValidation(unittest.TestCase):
    """Test YAML standard validation."""

    def test_validate_yaml_standard_file_not_found(self):
        """Test validation of non-existent file."""
        result = validate_yaml_standard("nonexistent.yaml")
        
        self.assertFalse(result["is_valid"])
        self.assertIn("File not found", result["errors"][0])

    @patch('adri.cli.commands.os.path.exists')
    def test_validate_yaml_standard_invalid_yaml(self, mock_exists):
        """Test validation of invalid YAML."""
        mock_exists.return_value = True
        
        with patch('builtins.open', mock_open(read_data="invalid: yaml: [")):
            result = validate_yaml_standard("test.yaml")
        
        self.assertFalse(result["is_valid"])
        self.assertIn("Invalid YAML syntax", result["errors"][0])

    @patch('adri.cli.commands.os.path.exists')
    def test_validate_yaml_standard_success(self, mock_exists):
        """Test validation of valid standard."""
        mock_exists.return_value = True
        valid_yaml = """
        standards:
          id: "test-standard"
          name: "Test Standard"
          version: "1.0.0"
          authority: "Test Authority"
        requirements:
          overall_minimum: 85
        """
        
        with patch('builtins.open', mock_open(read_data=valid_yaml)):
            result = validate_yaml_standard("test.yaml")
        
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["standard_name"], "Test Standard")

    @patch('adri.cli.commands.os.path.exists')
    def test_validate_yaml_standard_missing_sections(self, mock_exists):
        """Test validation with missing required sections."""
        mock_exists.return_value = True
        incomplete_yaml = """
        standards:
          name: "Test Standard"
        """
        
        with patch('builtins.open', mock_open(read_data=incomplete_yaml)):
            result = validate_yaml_standard("test.yaml")
        
        self.assertFalse(result["is_valid"])
        self.assertTrue(any("Missing required section" in error for error in result["errors"]))


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""

    def test_resolve_data_path_absolute(self):
        """Test resolving absolute data path."""
        env_config = {"paths": {"training_data": "/path/to/data"}}
        
        with patch('adri.cli.commands.os.path.isabs', return_value=True):
            result = _resolve_data_path("/abs/path/data.csv", env_config)
        
        self.assertEqual(result, "/abs/path/data.csv")

    def test_resolve_data_path_exists_as_is(self):
        """Test resolving data path that exists as-is."""
        env_config = {"paths": {"training_data": "/path/to/data"}}
        
        with patch('adri.cli.commands.os.path.isabs', return_value=False):
            with patch('adri.cli.commands.os.path.exists', return_value=True):
                result = _resolve_data_path("data.csv", env_config)
        
        self.assertEqual(result, "data.csv")

    def test_resolve_data_path_relative_to_training_data(self):
        """Test resolving path relative to training data directory."""
        env_config = {"paths": {"training_data": "/path/to/data"}}
        
        def mock_exists(path):
            return path == "/path/to/data/data.csv"
        
        with patch('adri.cli.commands.os.path.isabs', return_value=False):
            with patch('adri.cli.commands.os.path.exists', side_effect=mock_exists):
                result = _resolve_data_path("data.csv", env_config)
        
        self.assertEqual(result, "/path/to/data/data.csv")

    def test_resolve_standard_path_with_yaml_extension(self):
        """Test resolving standard path by adding .yaml extension."""
        env_config = {"paths": {"standards": "/path/to/standards"}}
        
        def mock_exists(path):
            return path == "/path/to/standards/standard.yaml"
        
        with patch('adri.cli.commands.os.path.isabs', return_value=False):
            with patch('adri.cli.commands.os.path.exists', side_effect=mock_exists):
                result = _resolve_standard_path("standard", env_config)
        
        self.assertEqual(result, "/path/to/standards/standard.yaml")

    def test_format_file_size(self):
        """Test file size formatting."""
        self.assertEqual(_format_file_size(0), "0 B")
        self.assertEqual(_format_file_size(1024), "1.0 KB")
        self.assertEqual(_format_file_size(1024 * 1024), "1.0 MB")
        self.assertEqual(_format_file_size(1024 * 1024 * 1024), "1.0 GB")

    def test_count_csv_rows(self):
        """Test CSV row counting."""
        csv_content = "header1,header2\nrow1,data1\nrow2,data2\n"
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            from pathlib import Path
            result = _count_csv_rows(Path("test.csv"))
        
        self.assertEqual(result, 2)  # Two data rows (excluding header)

    def test_count_csv_rows_error(self):
        """Test CSV row counting with error."""
        with patch('builtins.open', side_effect=IOError("File error")):
            from pathlib import Path
            result = _count_csv_rows(Path("test.csv"))
        
        self.assertEqual(result, 0)


class TestGenerateStandardCommand(unittest.TestCase):
    """Test generate standard command."""

    @patch('adri.cli.commands.ConfigManager')
    @patch('adri.cli.commands.load_data')
    @patch('adri.cli.commands.DataProfiler')
    @patch('adri.cli.commands.StandardGenerator')
    @patch('adri.cli.commands.Path')
    def test_generate_standard_success(self, mock_path, mock_generator, 
                                     mock_profiler, mock_load_data, mock_config_manager):
        """Test successful standard generation."""
        # Mock config manager
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = {
            "adri": {
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "training_data": "/path/to/data",
                            "standards": "/path/to/standards"
                        }
                    }
                },
                "assessment": {"performance": {"max_rows": 1000}},
                "generation": {}
            }
        }
        mock_manager.get_environment_config.return_value = {
            "paths": {
                "training_data": "/path/to/data",
                "standards": "/path/to/standards"
            }
        }
        
        # Mock data loading and profiling
        mock_load_data.return_value = [{"field1": "value1"}]
        mock_profiler_instance = MagicMock()
        mock_profiler.return_value = mock_profiler_instance
        mock_profiler_instance.profile_data.return_value = {"summary": {"total_rows": 1}}
        
        # Mock standard generation
        mock_generator_instance = MagicMock()
        mock_generator.return_value = mock_generator_instance
        mock_generator_instance.generate_standard.return_value = {
            "standards": {"name": "Test", "id": "test"},
            "requirements": {"overall_minimum": 85}
        }
        
        # Mock path operations
        mock_path.return_value.stem = "test_data"
        mock_path.return_value.parent.mkdir.return_value = None
        
        with patch('builtins.open', mock_open()):
            with patch('adri.cli.commands.yaml.dump'):
                result = generate_adri_standard_command("data.csv")
        
        self.assertEqual(result, 0)

    @patch('adri.cli.commands.ConfigManager')
    def test_generate_standard_no_config(self, mock_config_manager):
        """Test generate standard with no configuration."""
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = None
        
        result = generate_adri_standard_command("data.csv")
        
        self.assertEqual(result, 1)

    @patch('adri.cli.commands.ConfigManager')
    @patch('adri.cli.commands.os.path.exists')
    def test_generate_standard_file_exists_no_force(self, mock_exists, mock_config_manager):
        """Test generate standard with existing file and no force."""
        # Mock config
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = {
            "adri": {"environments": {"development": {"paths": {"standards": "/path"}}}}
        }
        mock_manager.get_environment_config.return_value = {"paths": {"standards": "/path"}}
        
        # File already exists
        mock_exists.return_value = True
        
        result = generate_adri_standard_command("data.csv", force=False)
        
        self.assertEqual(result, 1)


class TestListCommands(unittest.TestCase):
    """Test list commands."""

    @patch('adri.cli.commands.ConfigManager')
    @patch('adri.standards.loader.StandardsLoader')
    def test_list_standards_command_success(self, mock_loader_class, mock_config_manager):
        """Test successful list standards command."""
        # Mock standards loader
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader
        mock_loader.list_available_standards.return_value = ["standard1", "standard2"]
        mock_loader.standards_path = "/path/to/standards"
        
        # Mock config manager
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = None
        
        result = list_standards_command()
        
        self.assertEqual(result, 0)

    @patch('adri.cli.commands.ConfigManager')
    def test_list_training_data_command_no_config(self, mock_config_manager):
        """Test list training data with no configuration."""
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = None
        
        result = list_training_data_command()
        
        self.assertEqual(result, 1)

    @patch('adri.cli.commands.ConfigManager')
    def test_list_assessments_command_no_config(self, mock_config_manager):
        """Test list assessments with no configuration."""
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = None
        
        result = list_assessments_command()
        
        self.assertEqual(result, 1)


class TestCleanCacheCommand(unittest.TestCase):
    """Test clean cache command."""

    @patch('adri.cli.commands.ConfigManager')
    def test_clean_cache_command_no_config(self, mock_config_manager):
        """Test clean cache with no configuration."""
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = None
        
        result = clean_cache_command()
        
        self.assertEqual(result, 1)

    @patch('adri.cli.commands.ConfigManager')
    @patch('adri.cli.commands._find_cache_files')
    def test_clean_cache_command_no_files(self, mock_find_files, mock_config_manager):
        """Test clean cache with no files to clean."""
        # Mock config
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = {"adri": {"default_environment": "dev"}}
        mock_manager.get_environment_config.return_value = {"paths": {}}
        
        # No files to clean
        mock_find_files.return_value = ([], [], 0)
        
        result = clean_cache_command()
        
        self.assertEqual(result, 0)


class TestExportReportCommand(unittest.TestCase):
    """Test export report command."""

    @patch('adri.cli.commands.ConfigManager')
    def test_export_report_command_no_config(self, mock_config_manager):
        """Test export report with no configuration."""
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = None
        
        result = export_report_command()
        
        self.assertEqual(result, 1)

    @patch('adri.cli.commands.ConfigManager')
    @patch('adri.cli.commands.Path')
    def test_export_report_command_no_assessments(self, mock_path, mock_config_manager):
        """Test export report with no assessments found."""
        # Mock config
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = {"adri": {}}
        mock_manager.get_environment_config.return_value = {"paths": {"assessments": "/path"}}
        
        # No assessment files
        mock_path.return_value.glob.return_value = []
        
        result = export_report_command(latest=True)
        
        self.assertEqual(result, 1)

    def test_export_report_command_no_options(self):
        """Test export report with no latest flag or file specified."""
        result = export_report_command(latest=False, assessment_file=None)
        
        self.assertEqual(result, 1)


class TestShowStandardCommand(unittest.TestCase):
    """Test show standard command."""

    @patch('adri.cli.commands.ConfigManager')
    def test_show_standard_command_no_config(self, mock_config_manager):
        """Test show standard with no configuration."""
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = None
        
        result = show_standard_command("test_standard")
        
        self.assertEqual(result, 1)

    @patch('adri.cli.commands.ConfigManager')
    @patch('adri.cli.commands._load_standard_data')
    def test_show_standard_command_standard_not_found(self, mock_load_standard, mock_config_manager):
        """Test show standard with standard not found."""
        # Mock config
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = {"adri": {}}
        mock_manager.get_environment_config.return_value = {"paths": {}}
        
        # Standard not found
        mock_load_standard.return_value = None
        
        result = show_standard_command("test_standard")
        
        self.assertEqual(result, 1)


class TestExplainFailureCommand(unittest.TestCase):
    """Test explain failure command."""

    @patch('adri.cli.commands.ConfigManager')
    def test_explain_failure_command_no_config(self, mock_config_manager):
        """Test explain failure with no configuration."""
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = None
        
        result = explain_failure_command()
        
        self.assertEqual(result, 1)

    def test_explain_failure_command_no_options(self):
        """Test explain failure with no latest flag or file specified."""
        result = explain_failure_command(latest=False, assessment_file=None)
        
        self.assertEqual(result, 1)

    @patch('adri.cli.commands.ConfigManager')
    @patch('adri.cli.commands.Path')
    def test_explain_failure_command_no_assessments(self, mock_path, mock_config_manager):
        """Test explain failure with no assessments found."""
        # Mock config
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = {"adri": {}}
        mock_manager.get_environment_config.return_value = {"paths": {"assessments": "/path"}}
        
        # No assessment files
        mock_path.return_value.glob.return_value = []
        
        result = explain_failure_command(latest=True)
        
        self.assertEqual(result, 1)


class TestShowConfigCommand(unittest.TestCase):
    """Test show config command."""

    @patch('adri.cli.commands.ConfigManager')
    def test_show_config_command_no_config(self, mock_config_manager):
        """Test show config with no configuration."""
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = None
        
        result = show_config_command()
        
        self.assertEqual(result, 1)

    @patch('adri.cli.commands.ConfigManager')
    def test_show_config_command_success(self, mock_config_manager):
        """Test successful show config command."""
        # Mock config manager
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = {
            "adri": {
                "project_name": "test_project",
                "version": "2.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "/path/to/standards",
                            "assessments": "/path/to/assessments"
                        }
                    }
                }
            }
        }
        mock_manager.validate_config.return_value = True
        
        result = show_config_command()
        
        self.assertEqual(result, 0)

    @patch('adri.cli.commands.ConfigManager')
    def test_show_config_command_invalid_config(self, mock_config_manager):
        """Test show config with invalid configuration."""
        mock_manager = MagicMock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_active_config.return_value = {"invalid": "config"}
        mock_manager.validate_config.return_value = False
        
        result = show_config_command()
        
        self.assertEqual(result, 1)


class TestValidateStandardCommand(unittest.TestCase):
    """Test validate standard command."""

    @patch('adri.cli.commands._resolve_standard_for_validation')
    @patch('adri.cli.commands.validate_yaml_standard')
    def test_validate_standard_command_success(self, mock_validate, mock_resolve):
        """Test successful standard validation."""
        mock_resolve.return_value = "/path/to/standard.yaml"
        mock_validate.return_value = {
            "is_valid": True,
            "standard_name": "Test Standard",
            "standard_version": "1.0.0",
            "authority": "Test Authority",
            "passed_checks": ["check1", "check2"]
        }
        
        result = validate_standard_command("test_standard.yaml")
        
        self.assertEqual(result, 0)

    @patch('adri.cli.commands._resolve_standard_for_validation')
    @patch('adri.cli.commands.validate_yaml_standard')
    def test_validate_standard_command_failure(self, mock_validate, mock_resolve):
        """Test standard validation failure."""
        mock_resolve.return_value = "/path/to/standard.yaml"
        mock_validate.return_value = {
            "is_valid": False,
            "errors": ["Error 1", "Error 2"],
            "warnings": ["Warning 1"]
        }
        
        result = validate_standard_command("test_standard.yaml")
        
        self.assertEqual(result, 1)

    def test_validate_standard_command_file_not_found(self):
        """Test validate standard with file not found."""
        with patch('adri.cli.commands._resolve_standard_for_validation', 
                  side_effect=FileNotFoundError("File not found")):
            result = validate_standard_command("nonexistent.yaml")
        
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
