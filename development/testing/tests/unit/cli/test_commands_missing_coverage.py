"""
Tests specifically targeting missing coverage lines in CLI commands.
Focuses on covering the uncovered lines identified in coverage analysis.
"""

import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from adri.cli.commands import (
    assess_command,
    clean_cache_command,
    explain_failure_command,
    export_report_command,
    generate_adri_standard_command,
    list_assessments_command,
    list_standards_command,
    list_training_data_command,
    main,
    setup_command,
    show_config_command,
    show_standard_command,
    validate_standard_command,
)


class TestSetupCommandMissingCoverage:
    """Test missing coverage in setup_command."""

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.Path")
    @patch("adri.cli.commands.os.path.exists")
    def test_setup_command_with_subdirectory_config(
        self, mock_exists, mock_path, mock_config_manager
    ):
        """Test setup command with config in subdirectory."""
        mock_exists.return_value = False
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.create_default_config.return_value = {
            "test": "config"
        }

        # Mock Path for subdirectory creation
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent = MagicMock()
        mock_path.cwd.return_value.name = "test_project"

        result = setup_command(config_path="subdir/config.yaml")

        assert result == 0
        # Verify parent directory creation was called
        mock_path_instance.parent.mkdir.assert_called_once_with(
            parents=True, exist_ok=True
        )


class TestAssessCommandMissingCoverage:
    """Test missing coverage in assess_command."""

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.load_data")
    @patch("adri.cli.commands.load_standard")
    @patch("adri.cli.commands.AssessmentEngine")
    @patch("adri.cli.commands.Path")
    @patch("adri.cli.commands.datetime")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.json.dump")
    @patch("pandas.DataFrame")
    def test_assess_command_with_verbose_output(
        self,
        mock_df,
        mock_json_dump,
        mock_file,
        mock_datetime,
        mock_path,
        mock_engine,
        mock_load_standard,
        mock_load_data,
        mock_config_manager,
    ):
        """Test assess command with verbose output enabled."""
        # Setup mocks
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {
                "default_environment": "development",
                "assessment": {"performance": {"max_rows": 1000}},
            }
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {
                "training_data": "/test/training",
                "standards": "/test/standards",
                "assessments": "/test/assessments",
            }
        }

        mock_load_data.return_value = [{"col1": "value1", "col2": "value2"}]
        mock_load_standard.return_value = {"test": "standard"}

        # Mock assessment result with dimension scores
        mock_assessment = MagicMock()
        mock_assessment.overall_score = 85.0
        mock_assessment.passed = True
        mock_assessment.dimension_scores = {
            "validity": MagicMock(score=18.0, percentage=lambda: 90.0),
            "completeness": MagicMock(score=17.0, percentage=lambda: 85.0),
        }
        mock_assessment.to_standard_dict.return_value = {"assessment": "data"}

        mock_engine_instance = MagicMock()
        mock_engine.return_value = mock_engine_instance
        mock_engine_instance.assess.return_value = mock_assessment

        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
        mock_path.return_value.parent.mkdir = MagicMock()

        result = assess_command("test_data.csv", "test_standard.yaml", verbose=True)

        assert result == 0

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.load_data")
    @patch("adri.cli.commands.load_standard")
    @patch("adri.cli.commands.AssessmentEngine")
    @patch("adri.cli.commands.Path")
    @patch("adri.cli.commands.datetime")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.json.dump")
    @patch("pandas.DataFrame")
    def test_assess_command_non_verbose_output(
        self,
        mock_df,
        mock_json_dump,
        mock_file,
        mock_datetime,
        mock_path,
        mock_engine,
        mock_load_standard,
        mock_load_data,
        mock_config_manager,
    ):
        """Test assess command with non-verbose output (default)."""
        # Setup mocks
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {
                "training_data": "/test/training",
                "standards": "/test/standards",
                "assessments": "/test/assessments",
            }
        }

        mock_load_data.return_value = [{"col1": "value1"}]
        mock_load_standard.return_value = {"test": "standard"}

        # Mock assessment result
        mock_assessment = MagicMock()
        mock_assessment.overall_score = 75.0
        mock_assessment.passed = False
        mock_assessment.dimension_scores = {}
        mock_assessment.to_standard_dict.return_value = {"assessment": "data"}

        mock_engine_instance = MagicMock()
        mock_engine.return_value = mock_engine_instance
        mock_engine_instance.assess.return_value = mock_assessment

        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
        mock_path.return_value.parent.mkdir = MagicMock()

        result = assess_command("test_data.csv", "test_standard.yaml", verbose=False)

        assert result == 0


class TestGenerateStandardMissingCoverage:
    """Test missing coverage in generate_adri_standard_command."""

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.load_data")
    @patch("adri.cli.commands.DataProfiler")
    @patch("adri.cli.commands.StandardGenerator")
    @patch("adri.cli.commands.Path")
    @patch("adri.cli.commands.os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.yaml.dump")
    @patch("pandas.DataFrame")
    def test_generate_standard_with_verbose_debug_info(
        self,
        mock_df,
        mock_yaml_dump,
        mock_file,
        mock_exists,
        mock_path,
        mock_generator,
        mock_profiler,
        mock_load_data,
        mock_config_manager,
    ):
        """Test generate standard with verbose output and exception handling."""
        # Setup mocks
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"training_data": "/test", "standards": "/test"}
        }

        mock_exists.return_value = False
        mock_load_data.side_effect = Exception("Test exception")

        with patch("traceback.format_exc") as mock_traceback:
            mock_traceback.return_value = "Traceback details..."
            result = generate_adri_standard_command("test_data.csv", verbose=True)

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.load_data")
    @patch("adri.cli.commands.DataProfiler")
    @patch("adri.cli.commands.StandardGenerator")
    @patch("adri.cli.commands.Path")
    @patch("adri.cli.commands.os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.yaml.dump")
    @patch("pandas.DataFrame")
    def test_generate_standard_with_large_dataset_verbose(
        self,
        mock_df,
        mock_yaml_dump,
        mock_file,
        mock_exists,
        mock_path,
        mock_generator,
        mock_profiler,
        mock_load_data,
        mock_config_manager,
    ):
        """Test generate standard with large dataset and verbose warnings."""
        # Setup mocks
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {
                "default_environment": "development",
                "assessment": {"performance": {"max_rows": 100}},
                "generation": {"test": "config"},
            }
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"training_data": "/test", "standards": "/test"}
        }

        mock_exists.return_value = False
        mock_load_data.return_value = [{"col1": f"value{i}"} for i in range(200)]

        # Mock DataFrame with large size
        mock_df_instance = MagicMock()
        mock_df.return_value = mock_df_instance
        mock_df_instance.__len__.return_value = 200
        mock_df_instance.head.return_value = mock_df_instance

        # Mock profiler
        mock_profiler_instance = MagicMock()
        mock_profiler.return_value = mock_profiler_instance
        mock_profiler_instance.profile_data.return_value = {
            "summary": {
                "total_rows": 200,
                "total_columns": 1,
                "data_types": {"string": 1},
            }
        }

        # Mock generator
        mock_generator_instance = MagicMock()
        mock_generator.return_value = mock_generator_instance
        mock_generator_instance.generate_standard.return_value = {
            "standards": {
                "name": "Test Standard",
                "id": "test_std",
                "version": "1.0.0",
            },
            "requirements": {
                "overall_minimum": 80.0,
                "field_requirements": {},
                "dimension_requirements": {},
            },
        }

        mock_path.return_value.parent.mkdir = MagicMock()
        mock_path.return_value.stem = "test_data"

        result = generate_adri_standard_command("test_data.csv", verbose=True)

        assert result == 0
        # Verify that head() was called to limit rows
        mock_df_instance.head.assert_called_once_with(100)


class TestValidateStandardMissingCoverage:
    """Test missing coverage in validate_standard_command."""

    @patch("adri.cli.commands.validate_yaml_standard")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.json.dump")
    def test_validate_standard_with_output_file(
        self, mock_json_dump, mock_file, mock_validate
    ):
        """Test validate standard with output file specified."""
        mock_validate.return_value = {
            "is_valid": True,
            "standard_name": "Test Standard",
            "standard_version": "1.0.0",
            "authority": "Test Authority",
            "passed_checks": ["Check 1", "Check 2"],
            "errors": [],
            "warnings": [],
        }

        result = validate_standard_command(
            "test.yaml", output_path="validation_report.json"
        )

        assert result == 0
        mock_json_dump.assert_called_once()

    @patch("adri.cli.commands.validate_yaml_standard")
    def test_validate_standard_with_warnings(self, mock_validate):
        """Test validate standard with warnings."""
        mock_validate.return_value = {
            "is_valid": False,
            "standard_name": "Test Standard",
            "standard_version": "1.0.0",
            "authority": "Test Authority",
            "passed_checks": [],
            "errors": ["Error 1", "Error 2"],
            "warnings": ["Warning 1", "Warning 2"],
        }

        result = validate_standard_command("test.yaml")

        assert result == 1


class TestListCommandsMissingCoverage:
    """Test missing coverage in list commands."""

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.os.path.exists")
    @patch("adri.cli.commands.Path")
    def test_list_standards_with_verbose_yaml_error(
        self, mock_path, mock_exists, mock_config_manager
    ):
        """Test list standards with YAML loading error in verbose mode."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"standards": "/test/standards"}
        }
        mock_exists.return_value = True

        # Mock file path with stat
        mock_file_path = MagicMock()
        mock_file_path.name = "test_standard.yaml"
        mock_file_path.stat.return_value.st_mtime = 1640995200  # 2022-01-01
        mock_file_path.stat.return_value.st_size = 1024
        mock_file_path.is_file.return_value = True

        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.glob.return_value = [mock_file_path]

        # Mock YAML loading to fail
        with (
            patch("builtins.open", mock_open()),
            patch(
                "adri.cli.commands.yaml.safe_load", side_effect=Exception("YAML error")
            ),
        ):
            result = list_standards_command(verbose=True)

        assert result == 0

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.os.path.exists")
    @patch("adri.cli.commands.Path")
    def test_list_training_data_with_parquet_no_pandas(
        self, mock_path, mock_exists, mock_config_manager
    ):
        """Test list training data with parquet file but no pandas."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"training_data": "/test/training"}
        }
        mock_exists.return_value = True

        # Mock parquet file
        mock_file_path = MagicMock()
        mock_file_path.name = "test_data.parquet"
        mock_file_path.suffix.lower.return_value = ".parquet"
        mock_file_path.stat.return_value.st_mtime = 1640995200
        mock_file_path.stat.return_value.st_size = 2048
        mock_file_path.is_file.return_value = True

        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.glob.side_effect = [
            [],
            [],
            [mock_file_path],
        ]  # csv, json, parquet

        # Mock pandas import error
        with patch("adri.cli.commands.pd", None):
            result = list_training_data_command(verbose=True)

        assert result == 0

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.os.path.exists")
    @patch("adri.cli.commands.Path")
    def test_list_assessments_with_recent_limit(
        self, mock_path, mock_exists, mock_config_manager
    ):
        """Test list assessments with recent limit showing partial results."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"assessments": "/test/assessments"}
        }
        mock_exists.return_value = True

        # Mock multiple assessment files
        mock_files = []
        for i in range(5):
            mock_file = MagicMock()
            mock_file.name = f"assessment_{i}.json"
            mock_file.stat.return_value.st_mtime = 1640995200 + i
            mock_file.stat.return_value.st_size = 1024
            mock_file.is_file.return_value = True
            mock_files.append(mock_file)

        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.glob.return_value = mock_files

        result = list_assessments_command(recent=3)

        assert result == 0


class TestCleanCacheMissingCoverage:
    """Test missing coverage in clean_cache_command."""

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.os.path.exists")
    @patch("adri.cli.commands.Path")
    def test_clean_cache_with_errors(self, mock_path, mock_exists, mock_config_manager):
        """Test clean cache with file deletion errors."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {
                "assessments": "/test",
                "standards": "/test",
                "training_data": "/test",
            }
        }
        mock_exists.return_value = True

        # Mock file that will fail to delete
        mock_file = MagicMock()
        mock_file.stat.return_value.st_size = 100
        mock_file.unlink.side_effect = PermissionError("Permission denied")

        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.rglob.return_value = [mock_file]

        result = clean_cache_command()

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.os.path.exists")
    @patch("adri.cli.commands.Path")
    def test_clean_cache_with_directory_deletion_error(
        self, mock_path, mock_exists, mock_config_manager
    ):
        """Test clean cache with directory deletion error."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {
                "assessments": "/test",
                "standards": "/test",
                "training_data": "/test",
            }
        }
        mock_exists.return_value = True

        # Mock __pycache__ directory that will fail to delete
        mock_dir = MagicMock()
        mock_dir.is_dir.return_value = True
        mock_file_in_dir = MagicMock()
        mock_file_in_dir.is_file.return_value = True
        mock_file_in_dir.stat.return_value.st_size = 50
        mock_dir.rglob.return_value = [mock_file_in_dir]

        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.rglob.side_effect = lambda pattern: (
            [mock_dir] if pattern == "__pycache__" else []
        )

        with patch("shutil.rmtree", side_effect=OSError("Cannot delete")):
            result = clean_cache_command()

        assert result == 1


class TestExportReportMissingCoverage:
    """Test missing coverage in export_report_command."""

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.Path")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.json.load")
    @patch("adri.cli.commands.datetime")
    @patch("adri.cli.commands.csv.writer")
    def test_export_report_csv_format(
        self,
        mock_csv_writer,
        mock_datetime,
        mock_json_load,
        mock_file,
        mock_path,
        mock_config_manager,
    ):
        """Test export report in CSV format."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"assessments": "/test/assessments"}
        }

        # Mock assessment file exists
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        mock_json_load.return_value = {
            "overall_score": 85.5,
            "passed": True,
            "timestamp": "2024-01-01T12:00:00",
            "dimension_scores": {
                "validity": {"score": 18.0},
                "completeness": {"score": 17.0},
            },
        }
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"

        # Mock CSV writer
        mock_writer_instance = MagicMock()
        mock_csv_writer.return_value = mock_writer_instance

        result = export_report_command(assessment_file="test.json", format_type="csv")

        assert result == 0
        mock_writer_instance.writerows.assert_called_once()


class TestShowStandardMissingCoverage:
    """Test missing coverage in show_standard_command."""

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands._resolve_standard_path")
    @patch("adri.cli.commands.os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.yaml.safe_load")
    def test_show_standard_with_verbose_field_details(
        self,
        mock_yaml_load,
        mock_file,
        mock_exists,
        mock_resolve_path,
        mock_config_manager,
    ):
        """Test show standard with verbose field details."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"standards": "/test/standards"}
        }

        mock_resolve_path.return_value = "/test/standards/test.yaml"
        mock_exists.return_value = True

        mock_yaml_load.return_value = {
            "standards": {
                "name": "Test Standard",
                "id": "test_std",
                "version": "1.0.0",
                "authority": "Test Authority",
                "effective_date": "2024-01-01",
                "description": "Test description",
            },
            "requirements": {
                "overall_minimum": 80.0,
                "dimension_requirements": {
                    "validity": {"minimum_score": 15.0},
                    "completeness": {},
                },
                "field_requirements": {
                    "field1": {
                        "type": "string",
                        "nullable": False,
                        "min_value": 1,
                        "max_value": 100,
                        "pattern": "^[A-Z]+$",
                        "allowed_values": ["A", "B", "C"],
                    },
                    "field2": {
                        "type": "integer",
                        "nullable": True,
                        "allowed_values": list(range(20)),  # More than 5 values
                    },
                },
            },
        }

        result = show_standard_command("test", verbose=True)

        assert result == 0


class TestExplainFailureMissingCoverage:
    """Test missing coverage in explain_failure_command."""

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.Path")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.json.load")
    def test_explain_failure_with_passed_assessment(
        self, mock_json_load, mock_file, mock_path, mock_config_manager
    ):
        """Test explain failure with assessment that actually passed."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"assessments": "/test/assessments"}
        }

        # Mock assessment file exists
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        mock_json_load.return_value = {
            "overall_score": 95.0,
            "passed": True,
            "timestamp": "2024-01-01T12:00:00",
            "dimension_scores": {
                "validity": {"score": 19.0},
                "completeness": {"score": 18.0},
            },
            "metadata": {
                "data_source": "test_data.csv",
                "standard_name": "test_standard.yaml",
            },
        }

        result = explain_failure_command(assessment_file="test.json")

        assert result == 0

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.Path")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.json.load")
    def test_explain_failure_with_issues_in_dimensions(
        self, mock_json_load, mock_file, mock_path, mock_config_manager
    ):
        """Test explain failure with specific issues in dimension data."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"assessments": "/test/assessments"}
        }

        # Mock assessment file exists
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True

        mock_json_load.return_value = {
            "overall_score": 45.0,
            "passed": False,
            "timestamp": "2024-01-01T12:00:00",
            "dimension_scores": {
                "validity": {
                    "score": 8.0,
                    "issues": ["Issue 1", "Issue 2", "Issue 3", "Issue 4", "Issue 5"],
                },
                "completeness": {
                    "score": 12.0,
                    "issues": ["Missing data in field X", "Empty values found"],
                },
            },
            "metadata": {
                "data_source": "test_data.csv",
                "standard_name": "test_standard.yaml",
            },
        }

        result = explain_failure_command(assessment_file="test.json")

        assert result == 0


class TestMainFunctionCoverage:
    """Test main function and CLI setup."""

    def test_main_function_returns_cli(self):
        """Test main function creates CLI structure."""
        # Test that main() can be imported and contains the CLI setup
        # We'll test this by checking that the function exists and can be called
        # without actually executing the CLI

        from adri.cli.commands import main

        # Test that main function exists and is callable
        assert callable(main)

        # Test that we can patch the click execution to prevent actual CLI run
        with patch("click.Group.main") as mock_click_main:
            # This will prevent the actual CLI from running
            mock_click_main.return_value = None

            # Call main() - it should create the CLI structure
            # The function doesn't return anything, it just sets up and calls the CLI
            result = main()

            # main() doesn't return anything, it just calls the CLI
            assert result is None


class TestDataLoadingMissingCoverage:
    """Test data loading functions missing coverage."""

    @patch("adri.cli.commands.csv.DictReader")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_csv_data_empty_file_with_content_check(
        self, mock_file, mock_csv_reader
    ):
        """Test loading CSV with empty file but content check."""
        from adri.cli.commands import _load_csv_data

        # First call returns empty data
        mock_csv_reader.return_value = []

        # Second call for content check returns empty string
        mock_file.return_value.read.return_value = ""

        with pytest.raises(ValueError, match="CSV file is empty"):
            _load_csv_data(Path("empty.csv"))

    @patch("adri.cli.commands.json.load")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_json_data_not_list(self, mock_file, mock_json_load):
        """Test loading JSON that's not a list."""
        from adri.cli.commands import _load_json_data

        mock_json_load.return_value = {"not": "a list"}

        with pytest.raises(
            ValueError, match="JSON file must contain a list of objects"
        ):
            _load_json_data(Path("invalid.json"))

    @patch("adri.cli.commands.pd")
    def test_load_parquet_data_empty_dataframe(self, mock_pd):
        """Test loading parquet with empty DataFrame."""
        from adri.cli.commands import _load_parquet_data

        mock_df = MagicMock()
        mock_df.empty = True
        mock_pd.read_parquet.return_value = mock_df

        with pytest.raises(ValueError, match="Parquet file is empty"):
            _load_parquet_data(Path("empty.parquet"))

    @patch("adri.cli.commands.pd")
    def test_load_parquet_data_parquet_specific_error(self, mock_pd):
        """Test loading parquet with parquet-specific error."""
        from adri.cli.commands import _load_parquet_data

        mock_pd.read_parquet.side_effect = Exception("parquet format error")

        with pytest.raises(ValueError, match="Failed to read Parquet file"):
            _load_parquet_data(Path("error.parquet"))

    @patch("adri.cli.commands.pd")
    def test_load_parquet_data_generic_error(self, mock_pd):
        """Test loading parquet with generic error."""
        from adri.cli.commands import _load_parquet_data

        mock_pd.read_parquet.side_effect = Exception("generic error")

        with pytest.raises(Exception, match="generic error"):
            _load_parquet_data(Path("error.parquet"))


class TestConfigOutputMissingCoverage:
    """Test config output functions missing coverage."""

    def test_output_config_human_with_validation_errors(self):
        """Test human config output with validation errors."""
        from adri.cli.commands import _output_config_human

        config = {
            "adri": {
                "project_name": "Test Project",
                "version": "1.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": "/test/standards",
                            "assessments": "/test/assessments",
                        }
                    }
                },
                "assessment": {
                    "caching": {"enabled": True, "ttl": "24h"},
                    "performance": {"max_rows": 1000000, "timeout": "5m"},
                    "output": {"format": "json"},
                },
                "generation": {
                    "default_thresholds": {
                        "completeness_min": 85,
                        "validity_min": 90,
                        "consistency_min": 80,
                        "freshness_max_age": "7d",
                        "plausibility_outlier_threshold": 3.0,
                    }
                },
            }
        }

        validation_results = {
            "valid": False,
            "errors": ["Error 1", "Error 2"],
            "warnings": ["Warning 1"],
            "path_status": {
                "development.standards": {"exists": True, "file_count": 5},
                "development.assessments": {"exists": False, "file_count": -1},
            },
        }

        mock_config_manager = MagicMock()

        result = _output_config_human(
            config, None, False, True, validation_results, mock_config_manager
        )

        assert result == 0

    def test_show_assessment_settings_caching_disabled(self):
        """Test showing assessment settings with caching disabled."""
        from adri.cli.commands import _show_assessment_settings

        adri_config = {
            "assessment": {
                "caching": {"enabled": False},
                "performance": {"max_rows": 500000, "timeout": "10m"},
                "output": {"format": "csv"},
            }
        }

        # This should not raise an exception
        _show_assessment_settings(adri_config)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
