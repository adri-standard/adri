"""
Comprehensive tests for CLI commands in adri.cli.commands module.
Adapted from ADRI folder tests and enhanced for coverage improvement.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest
import yaml

from adri.cli.commands import (
    _load_csv_data,
    _load_json_data,
    _load_parquet_data,
    _resolve_data_path,
    _resolve_standard_path,
    assess_command,
    clean_cache_command,
    explain_failure_command,
    export_report_command,
    generate_adri_standard_command,
    list_assessments_command,
    list_standards_command,
    list_training_data_command,
    load_data,
    load_standard,
    setup_command,
    show_config_command,
    show_standard_command,
    validate_standard_command,
    validate_yaml_standard,
)


class TestSetupCommandComprehensive:
    """Comprehensive tests for setup_command function."""

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.Path")
    @patch("adri.cli.commands.os.path.exists")
    def test_setup_command_success(self, mock_exists, mock_path, mock_config_manager):
        """Test successful setup command."""
        mock_exists.return_value = False
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.create_default_config.return_value = {
            "test": "config"
        }
        mock_path.cwd.return_value.name = "test_project"

        result = setup_command()

        assert result == 0
        mock_config_manager_instance.create_default_config.assert_called_once_with(
            "test_project"
        )
        mock_config_manager_instance.save_config.assert_called_once()
        mock_config_manager_instance.create_directory_structure.assert_called_once()

    @patch("adri.cli.commands.os.path.exists")
    def test_setup_command_existing_config_no_force(self, mock_exists):
        """Test setup command with existing config and no force flag."""
        mock_exists.return_value = True

        result = setup_command(force=False)

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.Path")
    @patch("adri.cli.commands.os.path.exists")
    def test_setup_command_with_custom_params(
        self, mock_exists, mock_path, mock_config_manager
    ):
        """Test setup command with custom parameters."""
        mock_exists.return_value = False
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.create_default_config.return_value = {
            "test": "config"
        }

        result = setup_command(
            force=True,
            project_name="custom_project",
            config_path="custom/path/config.yaml",
        )

        assert result == 0
        mock_config_manager_instance.create_default_config.assert_called_once_with(
            "custom_project"
        )

    @patch("adri.cli.commands.ConfigManager")
    def test_setup_command_permission_error(self, mock_config_manager):
        """Test setup command with permission error."""
        mock_config_manager.side_effect = PermissionError("Permission denied")

        result = setup_command()

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    def test_setup_command_general_exception(self, mock_config_manager):
        """Test setup command with general exception."""
        mock_config_manager.side_effect = Exception("General error")

        result = setup_command()

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.Path")
    @patch("adri.cli.commands.os.path.exists")
    def test_setup_command_creates_parent_directory(
        self, mock_exists, mock_path, mock_config_manager
    ):
        """Test setup command creates parent directory when needed."""
        mock_exists.return_value = False
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.create_default_config.return_value = {
            "test": "config"
        }

        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent = MagicMock()
        mock_path.cwd.return_value.name = "test_project"

        result = setup_command(config_path="subdir/config.yaml")

        assert result == 0
        mock_path_instance.parent.mkdir.assert_called_once_with(
            parents=True, exist_ok=True
        )


class TestAssessCommandComprehensive:
    """Comprehensive tests for assess_command function."""

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.load_data")
    @patch("adri.cli.commands.load_standard")
    @patch("adri.cli.commands.AssessmentEngine")
    @patch("adri.cli.commands.Path")
    @patch("adri.cli.commands.datetime")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.json.dump")
    @patch("pandas.DataFrame")
    def test_assess_command_success(
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
        """Test successful assess command."""
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

        # Mock assessment result
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

        result = assess_command("test_data.csv", "test_standard.yaml")

        assert result == 0
        mock_load_data.assert_called_once()
        mock_load_standard.assert_called_once()
        mock_engine_instance.assess.assert_called_once()

    @patch("adri.cli.commands.ConfigManager")
    def test_assess_command_no_config(self, mock_config_manager):
        """Test assess command with no configuration."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = None

        result = assess_command("test_data.csv", "test_standard.yaml")

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    def test_assess_command_invalid_environment(self, mock_config_manager):
        """Test assess command with invalid environment."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {"test": "config"}
        mock_config_manager_instance.get_environment_config.side_effect = ValueError(
            "Invalid environment"
        )

        result = assess_command(
            "test_data.csv", "test_standard.yaml", environment="invalid"
        )

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.load_data")
    def test_assess_command_no_data(self, mock_load_data, mock_config_manager):
        """Test assess command with no data loaded."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {
                "training_data": "/test",
                "standards": "/test",
                "assessments": "/test",
            }
        }

        mock_load_data.return_value = []  # Empty data

        result = assess_command("test_data.csv", "test_standard.yaml")

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.load_data")
    @patch("adri.cli.commands.load_standard")
    @patch("adri.cli.commands.AssessmentEngine")
    @patch("pandas.DataFrame")
    def test_assess_command_with_performance_limits(
        self,
        mock_df,
        mock_engine,
        mock_load_standard,
        mock_load_data,
        mock_config_manager,
    ):
        """Test assess command with performance limits applied."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {
                "default_environment": "development",
                "assessment": {"performance": {"max_rows": 100}},
            }
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {
                "training_data": "/test",
                "standards": "/test",
                "assessments": "/test",
            }
        }

        # Create large dataset
        large_data = [{"col1": f"value{i}"} for i in range(200)]
        mock_load_data.return_value = large_data
        mock_load_standard.return_value = {"test": "standard"}

        # Mock DataFrame with length
        mock_df_instance = MagicMock()
        mock_df.return_value = mock_df_instance
        mock_df_instance.__len__.return_value = 200
        mock_df_instance.head.return_value = mock_df_instance

        # Mock assessment
        mock_assessment = MagicMock()
        mock_assessment.overall_score = 85.0
        mock_assessment.passed = True
        mock_assessment.dimension_scores = {}
        mock_assessment.to_standard_dict.return_value = {"assessment": "data"}

        mock_engine_instance = MagicMock()
        mock_engine.return_value = mock_engine_instance
        mock_engine_instance.assess.return_value = mock_assessment

        with (
            patch("adri.cli.commands.Path"),
            patch("adri.cli.commands.datetime"),
            patch("builtins.open", mock_open()),
            patch("adri.cli.commands.json.dump"),
        ):
            result = assess_command("test_data.csv", "test_standard.yaml", verbose=True)

        assert result == 0
        # Verify that head() was called to limit rows
        mock_df_instance.head.assert_called_once_with(100)


class TestGenerateStandardCommandComprehensive:
    """Comprehensive tests for generate_adri_standard_command function."""

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.load_data")
    @patch("adri.cli.commands.DataProfiler")
    @patch("adri.cli.commands.StandardGenerator")
    @patch("adri.cli.commands.Path")
    @patch("adri.cli.commands.os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.yaml.dump")
    @patch("pandas.DataFrame")
    def test_generate_standard_success(
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
        """Test successful standard generation."""
        # Setup mocks
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {
                "default_environment": "development",
                "assessment": {"performance": {"max_rows": 1000}},
                "generation": {"test": "config"},
            }
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"training_data": "/test/training", "standards": "/test/standards"}
        }

        mock_exists.return_value = False  # No existing standard
        mock_load_data.return_value = [{"col1": "value1", "col2": "value2"}]

        # Mock profiler
        mock_profiler_instance = MagicMock()
        mock_profiler.return_value = mock_profiler_instance
        mock_profiler_instance.profile_data.return_value = {
            "summary": {
                "total_rows": 100,
                "total_columns": 2,
                "data_types": {"string": 2},
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

        result = generate_adri_standard_command("test_data.csv")

        assert result == 0
        mock_profiler_instance.profile_data.assert_called_once()
        mock_generator_instance.generate_standard.assert_called_once()

    @patch("adri.cli.commands.ConfigManager")
    def test_generate_standard_no_config(self, mock_config_manager):
        """Test generate standard with no configuration."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = None

        result = generate_adri_standard_command("test_data.csv")

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.os.path.exists")
    def test_generate_standard_existing_file_no_force(
        self, mock_exists, mock_config_manager
    ):
        """Test generate standard with existing file and no force flag."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"standards": "/test/standards"}
        }

        mock_exists.return_value = True  # Existing standard file

        result = generate_adri_standard_command("test_data.csv", force=False)

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.load_data")
    def test_generate_standard_file_not_found(
        self, mock_load_data, mock_config_manager
    ):
        """Test generate standard with file not found error."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"training_data": "/test", "standards": "/test"}
        }

        mock_load_data.side_effect = FileNotFoundError("File not found")

        result = generate_adri_standard_command("nonexistent.csv")

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.load_data")
    @patch("adri.cli.commands.DataProfiler")
    def test_generate_standard_general_exception(
        self, mock_profiler, mock_load_data, mock_config_manager
    ):
        """Test generate standard with general exception."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"training_data": "/test", "standards": "/test"}
        }

        mock_load_data.return_value = [{"col1": "value1"}]
        mock_profiler.side_effect = Exception("Profiling error")

        with (
            patch("adri.cli.commands.os.path.exists", return_value=False),
            patch("pandas.DataFrame"),
        ):
            result = generate_adri_standard_command("test_data.csv")

        assert result == 1


class TestDataLoadingComprehensive:
    """Comprehensive tests for data loading functions."""

    @patch("adri.cli.commands.os.path.exists")
    @patch("adri.cli.commands._load_csv_data")
    def test_load_csv_data(self, mock_load_csv, mock_exists):
        """Test loading CSV data."""
        mock_exists.return_value = True
        mock_load_csv.return_value = [{"col1": "value1", "col2": "value2"}]

        result = load_data("test.csv")

        assert result == [{"col1": "value1", "col2": "value2"}]
        mock_load_csv.assert_called_once()

    @patch("adri.cli.commands.os.path.exists")
    @patch("adri.cli.commands._load_json_data")
    def test_load_json_data(self, mock_load_json, mock_exists):
        """Test loading JSON data."""
        mock_exists.return_value = True
        mock_load_json.return_value = [{"col1": "value1", "col2": "value2"}]

        result = load_data("test.json")

        assert result == [{"col1": "value1", "col2": "value2"}]
        mock_load_json.assert_called_once()

    @patch("adri.cli.commands.os.path.exists")
    @patch("adri.cli.commands._load_parquet_data")
    def test_load_parquet_data(self, mock_load_parquet, mock_exists):
        """Test loading Parquet data."""
        mock_exists.return_value = True
        mock_load_parquet.return_value = [{"col1": "value1", "col2": "value2"}]

        result = load_data("test.parquet")

        assert result == [{"col1": "value1", "col2": "value2"}]
        mock_load_parquet.assert_called_once()

    @patch("adri.cli.commands.os.path.exists")
    def test_load_data_file_not_found(self, mock_exists):
        """Test loading data with file not found."""
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError):
            load_data("nonexistent.csv")

    @patch("adri.cli.commands.os.path.exists")
    def test_load_data_unsupported_format(self, mock_exists):
        """Test loading data with unsupported format."""
        mock_exists.return_value = True

        with pytest.raises(ValueError, match="Unsupported file format"):
            load_data("test.txt")

    def test_load_csv_data_success(self):
        """Test successful CSV loading."""
        csv_content = "col1,col2\nvalue1,value2\nvalue3,value4"

        with patch("builtins.open", mock_open(read_data=csv_content)):
            result = _load_csv_data(Path("test.csv"))

        expected = [
            {"col1": "value1", "col2": "value2"},
            {"col1": "value3", "col2": "value4"},
        ]
        assert result == expected

    def test_load_csv_data_empty_file(self):
        """Test loading empty CSV file."""
        with patch("builtins.open", mock_open(read_data="")):
            with pytest.raises(ValueError, match="CSV file is empty"):
                _load_csv_data(Path("empty.csv"))

    def test_load_json_data_success(self):
        """Test successful JSON loading."""
        json_content = '[{"col1": "value1", "col2": "value2"}]'

        with patch("builtins.open", mock_open(read_data=json_content)):
            result = _load_json_data(Path("test.json"))

        expected = [{"col1": "value1", "col2": "value2"}]
        assert result == expected

    def test_load_json_data_not_list(self):
        """Test loading JSON that's not a list."""
        json_content = '{"col1": "value1", "col2": "value2"}'

        with patch("builtins.open", mock_open(read_data=json_content)):
            with pytest.raises(ValueError, match="JSON file must contain a list"):
                _load_json_data(Path("test.json"))

    @patch("pandas.read_parquet")
    def test_load_parquet_data_success(self, mock_read_parquet):
        """Test successful Parquet loading."""
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.to_dict.return_value = [{"col1": "value1", "col2": "value2"}]
        mock_read_parquet.return_value = mock_df

        result = _load_parquet_data(Path("test.parquet"))

        assert result == [{"col1": "value1", "col2": "value2"}]
        mock_df.to_dict.assert_called_once_with("records")

    @patch("pandas.read_parquet")
    def test_load_parquet_data_empty(self, mock_read_parquet):
        """Test loading empty Parquet file."""
        mock_df = MagicMock()
        mock_df.empty = True
        mock_read_parquet.return_value = mock_df

        with pytest.raises(ValueError, match="Parquet file is empty"):
            _load_parquet_data(Path("empty.parquet"))

    def test_load_parquet_data_pandas_not_available(self):
        """Test loading Parquet when pandas is not available."""
        with patch("adri.cli.commands.pd", None):
            with pytest.raises(ImportError, match="pandas is required"):
                _load_parquet_data(Path("test.parquet"))


class TestPathResolutionComprehensive:
    """Comprehensive tests for path resolution functions."""

    def test_resolve_data_path_absolute(self):
        """Test resolving absolute data path."""
        env_config = {"paths": {"training_data": "/test/training"}}

        with patch("adri.cli.commands.os.path.isabs", return_value=True):
            result = _resolve_data_path("/absolute/path/data.csv", env_config)

        assert result == "/absolute/path/data.csv"

    def test_resolve_data_path_exists_as_is(self):
        """Test resolving data path that exists as-is."""
        env_config = {"paths": {"training_data": "/test/training"}}

        with (
            patch("adri.cli.commands.os.path.isabs", return_value=False),
            patch("adri.cli.commands.os.path.exists", return_value=True),
        ):
            result = _resolve_data_path("data.csv", env_config)

        assert result == "data.csv"

    def test_resolve_data_path_in_training_dir(self):
        """Test resolving data path in training directory."""
        env_config = {"paths": {"training_data": "/test/training"}}

        with (
            patch("adri.cli.commands.os.path.isabs", return_value=False),
            patch("adri.cli.commands.os.path.exists", side_effect=[False, True]),
        ):
            result = _resolve_data_path("data.csv", env_config)

        assert result == "/test/training/data.csv"

    def test_resolve_data_path_not_found(self):
        """Test resolving data path that doesn't exist anywhere."""
        env_config = {"paths": {"training_data": "/test/training"}}

        with (
            patch("adri.cli.commands.os.path.isabs", return_value=False),
            patch("adri.cli.commands.os.path.exists", return_value=False),
        ):
            result = _resolve_data_path("nonexistent.csv", env_config)

        assert result == "nonexistent.csv"  # Returns original path

    def test_resolve_standard_path_with_extension(self):
        """Test resolving standard path with automatic extension."""
        env_config = {"paths": {"standards": "/test/standards"}}

        with (
            patch("adri.cli.commands.os.path.isabs", return_value=False),
            patch("adri.cli.commands.os.path.exists", side_effect=[False, False, True]),
        ):
            result = _resolve_standard_path("standard", env_config)

        assert result == "/test/standards/standard.yaml"

    def test_resolve_standard_path_already_has_extension(self):
        """Test resolving standard path that already has extension."""
        env_config = {"paths": {"standards": "/test/standards"}}

        with (
            patch("adri.cli.commands.os.path.isabs", return_value=False),
            patch("adri.cli.commands.os.path.exists", side_effect=[False, True]),
        ):
            result = _resolve_standard_path("standard.yaml", env_config)

        assert result == "/test/standards/standard.yaml"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
