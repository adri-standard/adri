"""
Edge case and error handling tests for CLI commands.
Focuses on covering the missing lines identified in coverage analysis.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from adri.cli.commands import (
    _count_csv_rows,
    _format_file_size,
    _get_dimension_recommendations,
    _output_config_human,
    _output_config_json,
    _show_assessment_settings,
    _show_generation_settings,
    _show_validation_results,
    _validate_dimension_requirements,
    _validate_field_requirements,
    _validate_requirements_section,
    _validate_standards_metadata,
    clean_cache_command,
    explain_failure_command,
    export_report_command,
    list_assessments_command,
    list_standards_command,
    list_training_data_command,
    show_config_command,
    show_standard_command,
    validate_yaml_standard,
)


class TestValidateYamlStandardEdgeCases:
    """Test edge cases in YAML standard validation."""

    @patch("adri.cli.commands.os.path.exists")
    def test_validate_yaml_standard_file_not_found(self, mock_exists):
        """Test validation with file not found."""
        mock_exists.return_value = False

        result = validate_yaml_standard("nonexistent.yaml")

        assert result["is_valid"] is False
        assert "File not found" in result["errors"][0]

    @patch("adri.cli.commands.os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.yaml.safe_load")
    def test_validate_yaml_standard_invalid_yaml(
        self, mock_yaml_load, mock_file, mock_exists
    ):
        """Test validation with invalid YAML."""
        mock_exists.return_value = True
        mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")

        result = validate_yaml_standard("invalid.yaml")

        assert result["is_valid"] is False
        assert "Invalid YAML syntax" in result["errors"][0]

    @patch("adri.cli.commands.os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.yaml.safe_load")
    def test_validate_yaml_standard_not_dict(
        self, mock_yaml_load, mock_file, mock_exists
    ):
        """Test validation with non-dictionary root."""
        mock_exists.return_value = True
        mock_yaml_load.return_value = ["not", "a", "dict"]

        result = validate_yaml_standard("invalid.yaml")

        assert result["is_valid"] is False
        assert "dictionary at the root level" in result["errors"][0]

    @patch("adri.cli.commands.os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.yaml.safe_load")
    def test_validate_yaml_standard_missing_sections(
        self, mock_yaml_load, mock_file, mock_exists
    ):
        """Test validation with missing required sections."""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"incomplete": "standard"}

        result = validate_yaml_standard("incomplete.yaml")

        assert result["is_valid"] is False
        assert any(
            "Missing required section: 'standards'" in error
            for error in result["errors"]
        )
        assert any(
            "Missing required section: 'requirements'" in error
            for error in result["errors"]
        )

    @patch("adri.cli.commands.os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.yaml.safe_load")
    @patch("adri.cli.commands.YAMLStandards")
    def test_validate_yaml_standard_yaml_standards_failure(
        self, mock_yaml_standards, mock_yaml_load, mock_file, mock_exists
    ):
        """Test validation when YAMLStandards instantiation fails."""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            "standards": {
                "id": "test_std",
                "name": "Test Standard",
                "version": "1.0.0",
                "authority": "Test Authority",
            },
            "requirements": {},
        }

        # Mock YAMLStandards to fail
        mock_yaml_standards.side_effect = Exception("YAMLStandards error")

        result = validate_yaml_standard("test.yaml")

        # Should still extract metadata even if YAMLStandards fails
        assert result["standard_name"] == "Test Standard"
        assert result["standard_version"] == "1.0.0"
        assert result["authority"] == "Test Authority"

    @patch("adri.cli.commands.os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.yaml.safe_load")
    def test_validate_yaml_standard_unexpected_error(
        self, mock_yaml_load, mock_file, mock_exists
    ):
        """Test validation with unexpected error."""
        mock_exists.return_value = True
        mock_yaml_load.side_effect = Exception("Unexpected error")

        result = validate_yaml_standard("error.yaml")

        assert result["is_valid"] is False
        assert "Unexpected error during validation" in result["errors"][0]


class TestValidationHelperFunctions:
    """Test validation helper functions."""

    def test_validate_standards_metadata_missing_fields(self):
        """Test standards metadata validation with missing fields."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        standards_section = {
            "name": "Test",
            "version": "1.0.0",
        }  # Missing id and authority

        _validate_standards_metadata(standards_section, result)

        assert result["is_valid"] is False
        assert any("Missing required field" in error for error in result["errors"])

    def test_validate_standards_metadata_empty_values(self):
        """Test standards metadata validation with empty values."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        standards_section = {
            "id": "",
            "name": "Test",
            "version": "1.0.0",
            "authority": "   ",  # Whitespace only
        }

        _validate_standards_metadata(standards_section, result)

        assert result["is_valid"] is False
        assert any(
            "Empty value for required field" in error for error in result["errors"]
        )

    def test_validate_standards_metadata_invalid_version(self):
        """Test standards metadata validation with invalid version format."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        standards_section = {
            "id": "test",
            "name": "Test",
            "version": "invalid-version",
            "authority": "Test Authority",
        }

        _validate_standards_metadata(standards_section, result)

        assert any(
            "does not follow semantic versioning" in warning
            for warning in result["warnings"]
        )

    def test_validate_standards_metadata_invalid_effective_date(self):
        """Test standards metadata validation with invalid effective date."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        standards_section = {
            "id": "test",
            "name": "Test",
            "version": "1.0.0",
            "authority": "Test Authority",
            "effective_date": "invalid-date",
        }

        _validate_standards_metadata(standards_section, result)

        assert result["is_valid"] is False
        assert any(
            "Invalid effective_date format" in error for error in result["errors"]
        )

    def test_validate_requirements_section_not_dict(self):
        """Test requirements section validation when not a dictionary."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        requirements_section = ["not", "a", "dict"]

        _validate_requirements_section(requirements_section, result)

        assert result["is_valid"] is False
        assert "Requirements section must be a dictionary" in result["errors"][0]

    def test_validate_requirements_section_invalid_overall_minimum(self):
        """Test requirements section validation with invalid overall_minimum."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        requirements_section = {"overall_minimum": "not_a_number"}

        _validate_requirements_section(requirements_section, result)

        assert result["is_valid"] is False
        assert "overall_minimum must be a number" in result["errors"][0]

    def test_validate_requirements_section_out_of_range_overall_minimum(self):
        """Test requirements section validation with out-of-range overall_minimum."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        requirements_section = {"overall_minimum": 150}  # > 100

        _validate_requirements_section(requirements_section, result)

        assert result["is_valid"] is False
        assert "overall_minimum must be between 0 and 100" in result["errors"][0]

    def test_validate_dimension_requirements_not_dict(self):
        """Test dimension requirements validation when not a dictionary."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        dim_requirements = ["not", "a", "dict"]

        _validate_dimension_requirements(dim_requirements, result)

        assert result["is_valid"] is False
        assert "dimension_requirements must be a dictionary" in result["errors"][0]

    def test_validate_dimension_requirements_unknown_dimension(self):
        """Test dimension requirements validation with unknown dimension."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        dim_requirements = {"unknown_dimension": {"minimum_score": 15}}

        _validate_dimension_requirements(dim_requirements, result)

        assert result["is_valid"] is False
        assert "Unknown dimension: 'unknown_dimension'" in result["errors"][0]

    def test_validate_dimension_requirements_invalid_minimum_score(self):
        """Test dimension requirements validation with invalid minimum_score."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        dim_requirements = {"validity": {"minimum_score": "not_a_number"}}

        _validate_dimension_requirements(dim_requirements, result)

        assert result["is_valid"] is False
        assert "minimum_score for validity must be a number" in result["errors"][0]

    def test_validate_dimension_requirements_out_of_range_minimum_score(self):
        """Test dimension requirements validation with out-of-range minimum_score."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        dim_requirements = {"validity": {"minimum_score": 25}}  # > 20

        _validate_dimension_requirements(dim_requirements, result)

        assert result["is_valid"] is False
        assert (
            "minimum_score for validity must be between 0 and 20" in result["errors"][0]
        )

    def test_validate_field_requirements_not_dict(self):
        """Test field requirements validation when not a dictionary."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        field_requirements = ["not", "a", "dict"]

        _validate_field_requirements(field_requirements, result)

        assert result["is_valid"] is False
        assert "field_requirements must be a dictionary" in result["errors"][0]

    def test_validate_field_requirements_field_config_not_dict(self):
        """Test field requirements validation when field config is not a dictionary."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        field_requirements = {"field1": "not_a_dict"}

        _validate_field_requirements(field_requirements, result)

        assert result["is_valid"] is False
        assert (
            "Field 'field1' configuration must be a dictionary" in result["errors"][0]
        )

    def test_validate_field_requirements_invalid_type(self):
        """Test field requirements validation with invalid type."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        field_requirements = {"field1": {"type": "invalid_type"}}

        _validate_field_requirements(field_requirements, result)

        assert result["is_valid"] is False
        assert "Invalid type 'invalid_type' for field 'field1'" in result["errors"][0]

    def test_validate_field_requirements_invalid_nullable(self):
        """Test field requirements validation with invalid nullable."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        field_requirements = {"field1": {"nullable": "not_boolean"}}

        _validate_field_requirements(field_requirements, result)

        assert result["is_valid"] is False
        assert (
            "nullable for field 'field1' must be true or false" in result["errors"][0]
        )

    def test_validate_field_requirements_invalid_min_max_range(self):
        """Test field requirements validation with invalid min/max range."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        field_requirements = {"field1": {"min_value": 10, "max_value": 5}}  # min > max

        _validate_field_requirements(field_requirements, result)

        assert result["is_valid"] is False
        assert (
            "min_value must be less than max_value for field 'field1'"
            in result["errors"][0]
        )

    def test_validate_field_requirements_invalid_regex_pattern(self):
        """Test field requirements validation with invalid regex pattern."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        field_requirements = {"field1": {"pattern": "[invalid_regex"}}

        _validate_field_requirements(field_requirements, result)

        assert result["is_valid"] is False
        assert "Invalid regex pattern for field 'field1'" in result["errors"][0]


class TestShowConfigCommandEdgeCases:
    """Test edge cases in show_config_command."""

    @patch("adri.cli.commands.ConfigManager")
    def test_show_config_no_config(self, mock_config_manager):
        """Test show config with no configuration."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = None

        result = show_config_command()

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    def test_show_config_invalid_config(self, mock_config_manager):
        """Test show config with invalid configuration."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "invalid": "config"
        }
        mock_config_manager_instance.validate_config.return_value = False

        result = show_config_command()

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    def test_show_config_json_format(self, mock_config_manager):
        """Test show config with JSON format."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {"test": "config"}
        mock_config_manager_instance.validate_config.return_value = True

        with patch("adri.cli.commands._output_config_json") as mock_output:
            mock_output.return_value = 0
            result = show_config_command(format_type="json")

        assert result == 0
        mock_output.assert_called_once()

    @patch("adri.cli.commands.ConfigManager")
    def test_show_config_with_validation(self, mock_config_manager):
        """Test show config with validation enabled."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {"test": "config"}
        mock_config_manager_instance.validate_config.return_value = True
        mock_config_manager_instance.validate_paths.return_value = {"valid": True}

        with patch("adri.cli.commands._output_config_human") as mock_output:
            mock_output.return_value = 0
            result = show_config_command(validate=True)

        assert result == 0
        mock_config_manager_instance.validate_paths.assert_called_once()

    @patch("adri.cli.commands.ConfigManager")
    def test_show_config_exception(self, mock_config_manager):
        """Test show config with exception."""
        mock_config_manager.side_effect = Exception("Config error")

        result = show_config_command()

        assert result == 1


class TestListCommandsEdgeCases:
    """Test edge cases in list commands."""

    @patch("adri.cli.commands.ConfigManager")
    def test_list_standards_no_config(self, mock_config_manager):
        """Test list standards with no configuration."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = None

        result = list_standards_command()

        # Should return 0 because bundled standards are always available
        assert result == 0

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.os.path.exists")
    def test_list_standards_directory_not_found(self, mock_exists, mock_config_manager):
        """Test list standards with directory not found."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"standards": "/nonexistent/standards"}
        }
        mock_exists.return_value = False

        result = list_standards_command()

        assert result == 0  # Should return 0 but show message about missing directory

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.os.path.exists")
    @patch("adri.cli.commands.Path")
    def test_list_standards_no_files(self, mock_path, mock_exists, mock_config_manager):
        """Test list standards with no standard files."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"standards": "/test/standards"}
        }
        mock_exists.return_value = True

        # Mock Path.glob to return empty list
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.glob.return_value = []

        result = list_standards_command()

        assert result == 0

    @patch("adri.cli.commands.ConfigManager")
    def test_list_training_data_invalid_environment(self, mock_config_manager):
        """Test list training data with invalid environment."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {"test": "config"}
        mock_config_manager_instance.get_environment_config.side_effect = ValueError(
            "Invalid environment"
        )

        result = list_training_data_command(environment="invalid")

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    def test_list_assessments_exception(self, mock_config_manager):
        """Test list assessments with exception."""
        mock_config_manager.side_effect = Exception("Unexpected error")

        result = list_assessments_command()

        assert result == 1


class TestUtilityFunctions:
    """Test utility functions."""

    def test_format_file_size_zero(self):
        """Test formatting zero file size."""
        result = _format_file_size(0)
        assert result == "0 B"

    def test_format_file_size_bytes(self):
        """Test formatting file size in bytes."""
        result = _format_file_size(512)
        assert result == "512.0 B"

    def test_format_file_size_kilobytes(self):
        """Test formatting file size in kilobytes."""
        result = _format_file_size(1536)  # 1.5 KB
        assert result == "1.5 KB"

    def test_format_file_size_megabytes(self):
        """Test formatting file size in megabytes."""
        result = _format_file_size(1572864)  # 1.5 MB
        assert result == "1.5 MB"

    def test_count_csv_rows_empty_file(self):
        """Test counting rows in empty CSV file."""
        with patch("builtins.open", mock_open(read_data="")):
            result = _count_csv_rows(Path("empty.csv"))

        assert result == 0

    def test_count_csv_rows_small_file(self):
        """Test counting rows in small CSV file."""
        csv_content = "header1,header2\nrow1,data1\nrow2,data2"

        with patch("builtins.open", mock_open(read_data=csv_content)):
            result = _count_csv_rows(Path("small.csv"))

        assert result == 2  # 3 lines - 1 header = 2 rows

    def test_count_csv_rows_exception(self):
        """Test counting rows with exception."""
        with patch("builtins.open", side_effect=Exception("File error")):
            result = _count_csv_rows(Path("error.csv"))

        assert result == 0

    def test_get_dimension_recommendations_validity(self):
        """Test getting recommendations for validity dimension."""
        recommendations = _get_dimension_recommendations("validity", 4.0, {})

        assert len(recommendations) <= 4
        assert any("CRITICAL" in rec for rec in recommendations)
        assert any("email formats" in rec for rec in recommendations)

    def test_get_dimension_recommendations_completeness(self):
        """Test getting recommendations for completeness dimension."""
        recommendations = _get_dimension_recommendations("completeness", 12.0, {})

        assert len(recommendations) <= 4
        assert any("MINOR" in rec for rec in recommendations)
        assert any("missing required fields" in rec for rec in recommendations)

    def test_get_dimension_recommendations_unknown_dimension(self):
        """Test getting recommendations for unknown dimension."""
        recommendations = _get_dimension_recommendations("unknown", 8.0, {})

        assert len(recommendations) <= 4
        assert any("MAJOR" in rec for rec in recommendations)


class TestExportReportEdgeCases:
    """Test edge cases in export_report_command."""

    @patch("adri.cli.commands.ConfigManager")
    def test_export_report_no_config(self, mock_config_manager):
        """Test export report with no configuration."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = None

        result = export_report_command(latest=True)

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.Path")
    def test_export_report_no_assessments(self, mock_path, mock_config_manager):
        """Test export report with no assessment files."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }
        mock_config_manager_instance.get_environment_config.return_value = {
            "paths": {"assessments": "/test/assessments"}
        }

        # Mock Path.glob to return empty list
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.glob.return_value = []

        result = export_report_command(latest=True)

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    def test_export_report_missing_parameters(self, mock_config_manager):
        """Test export report with missing parameters."""
        mock_config_manager_instance = MagicMock()
        mock_config_manager.return_value = mock_config_manager_instance
        mock_config_manager_instance.get_active_config.return_value = {
            "adri": {"default_environment": "development"}
        }

        result = export_report_command()  # No latest=True and no assessment_file

        assert result == 1

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.Path")
    @patch("builtins.open", new_callable=mock_open)
    @patch("adri.cli.commands.json.load")
    @patch("adri.cli.commands.datetime")
    def test_export_report_unsupported_format(
        self, mock_datetime, mock_json_load, mock_file, mock_path, mock_config_manager
    ):
        """Test export report with unsupported format."""
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

        mock_json_load.return_value = {"test": "assessment"}
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"

        result = export_report_command(assessment_file="test.json", format_type="xml")

        assert result == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
