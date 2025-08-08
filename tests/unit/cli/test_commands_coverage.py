"""
Comprehensive tests to achieve 100% coverage for adri.cli.commands module.

This test file targets all uncovered lines and edge cases in the CLI commands.
"""

import csv
import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from adri.cli.commands import (
    _count_csv_rows,
    _format_file_size,
    _get_dimension_recommendations,
    _load_csv_data,
    _load_json_data,
    _load_parquet_data,
    _output_config_human,
    _output_config_json,
    _resolve_data_path,
    _resolve_standard_path,
    _show_assessment_settings,
    _show_generation_settings,
    _show_validation_results,
    _validate_dimension_requirements,
    _validate_field_requirements,
    _validate_requirements_section,
    _validate_standards_metadata,
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


class TestSetupCommandCoverage:
    """Test setup command edge cases and error paths."""

    def test_setup_permission_error(self):
        """Test setup command with permission error (lines 19-20)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.save_config.side_effect = PermissionError("Permission denied")

            result = setup_command(force=True, project_name="test")
            assert result == 1

    def test_setup_general_exception(self):
        """Test setup command with general exception."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_config_manager.side_effect = Exception("General error")

            result = setup_command()
            assert result == 1

    def test_setup_config_dir_creation(self):
        """Test setup with custom config path requiring directory creation (lines 103-105)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "subdir", "config.yaml")

            with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
                mock_manager = MagicMock()
                mock_config_manager.return_value = mock_manager
                mock_manager.create_default_config.return_value = {"test": "config"}

                result = setup_command(config_path=config_path)
                assert result == 0


class TestAssessCommandCoverage:
    """Test assess command edge cases and error paths."""

    def test_assess_no_config(self):
        """Test assess command with no configuration (lines 179-180)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = None

            result = assess_command("data.csv", "standard.yaml")
            assert result == 1

    def test_assess_invalid_environment(self):
        """Test assess command with invalid environment (lines 271-273)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {"test": "config"}
            mock_manager.get_environment_config.side_effect = ValueError(
                "Invalid environment"
            )

            result = assess_command("data.csv", "standard.yaml", environment="invalid")
            assert result == 1

    def test_assess_file_not_found(self):
        """Test assess command with file not found (lines 301-302)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {
                "adri": {"default_environment": "dev"}
            }
            mock_manager.get_environment_config.return_value = {
                "paths": {
                    "training_data": "/tmp",
                    "standards": "/tmp",
                    "assessments": "/tmp",
                }
            }

            with patch(
                "adri.cli.commands.load_data",
                side_effect=FileNotFoundError("File not found"),
            ):
                result = assess_command("nonexistent.csv", "standard.yaml")
                assert result == 1

    def test_assess_general_exception(self):
        """Test assess command with general exception."""
        with patch(
            "adri.cli.commands.ConfigManager", side_effect=Exception("General error")
        ):
            result = assess_command("data.csv", "standard.yaml")
            assert result == 1


class TestGenerateStandardCommandCoverage:
    """Test generate standard command edge cases and error paths."""

    def test_generate_no_config(self):
        """Test generate standard with no configuration (lines 564-565)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = None

            result = generate_adri_standard_command("data.csv")
            assert result == 1

    def test_generate_invalid_environment(self):
        """Test generate standard with invalid environment (lines 618-623)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {"test": "config"}
            mock_manager.get_environment_config.side_effect = ValueError(
                "Invalid environment"
            )

            result = generate_adri_standard_command("data.csv", environment="invalid")
            assert result == 1

    def test_generate_file_exists_no_force(self):
        """Test generate standard when file exists without force flag (lines 724-726)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            existing_file = os.path.join(temp_dir, "test_ADRI_standard.yaml")
            Path(existing_file).touch()

            with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
                mock_manager = MagicMock()
                mock_config_manager.return_value = mock_manager
                mock_manager.get_active_config.return_value = {
                    "adri": {"default_environment": "dev"}
                }
                mock_manager.get_environment_config.return_value = {
                    "paths": {"standards": temp_dir, "training_data": "/tmp"}
                }

                result = generate_adri_standard_command("test.csv", force=False)
                assert result == 1

    def test_generate_file_not_found(self):
        """Test generate standard with file not found (lines 1000)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {
                "adri": {"default_environment": "dev"}
            }
            mock_manager.get_environment_config.return_value = {
                "paths": {"standards": "/tmp", "training_data": "/tmp"}
            }

            with patch(
                "adri.cli.commands.load_data",
                side_effect=FileNotFoundError("File not found"),
            ):
                result = generate_adri_standard_command("nonexistent.csv")
                assert result == 1

    def test_generate_general_exception(self):
        """Test generate standard with general exception (lines 1057)."""
        with patch(
            "adri.cli.commands.ConfigManager", side_effect=Exception("General error")
        ):
            result = generate_adri_standard_command("data.csv")
            assert result == 1


class TestValidateStandardCommandCoverage:
    """Test validate standard command edge cases."""

    def test_validate_file_not_found(self):
        """Test validate standard with file not found (lines 1200-1202)."""
        with patch(
            "adri.cli.commands.validate_yaml_standard",
            side_effect=FileNotFoundError("File not found"),
        ):
            result = validate_standard_command("nonexistent.yaml")
            assert result == 1

    def test_validate_general_exception(self):
        """Test validate standard with general exception."""
        with patch(
            "adri.cli.commands.validate_yaml_standard",
            side_effect=Exception("General error"),
        ):
            result = validate_standard_command("standard.yaml")
            assert result == 1


class TestValidateYamlStandardCoverage:
    """Test YAML standard validation edge cases."""

    def test_validate_yaml_error(self):
        """Test YAML validation with YAML error (lines 1253-1269)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_file = f.name

        try:
            result = validate_yaml_standard(temp_file)
            assert not result["is_valid"]
            assert any("Invalid YAML syntax" in error for error in result["errors"])
        finally:
            os.unlink(temp_file)

    def test_validate_non_dict_root(self):
        """Test YAML validation with non-dictionary root (lines 1284-1286)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("- this is a list, not a dict")
            temp_file = f.name

        try:
            result = validate_yaml_standard(temp_file)
            assert not result["is_valid"]
            assert any(
                "dictionary at the root level" in error for error in result["errors"]
            )
        finally:
            os.unlink(temp_file)

    def test_validate_missing_sections(self):
        """Test YAML validation with missing required sections (lines 1311-1313)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"incomplete": "config"}, f)
            temp_file = f.name

        try:
            result = validate_yaml_standard(temp_file)
            assert not result["is_valid"]
            assert any(
                "Missing required section: 'standards'" in error
                for error in result["errors"]
            )
            assert any(
                "Missing required section: 'requirements'" in error
                for error in result["errors"]
            )
        finally:
            os.unlink(temp_file)

    def test_validate_yaml_valid_standard(self):
        """Test YAML validation with a valid standard."""
        valid_yaml = {
            "standards": {
                "id": "test",
                "name": "test",
                "version": "1.0.0",
                "authority": "test",
            },
            "requirements": {"overall_minimum": 80},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(valid_yaml, f)
            temp_file = f.name

        try:
            result = validate_yaml_standard(temp_file)
            # Should extract metadata successfully
            assert result["standard_name"] == "test"
            assert result["standard_version"] == "1.0.0"
            assert result["authority"] == "test"
            assert result["is_valid"] == True
            assert len(result["errors"]) == 0
        finally:
            os.unlink(temp_file)

    def test_validate_unexpected_exception(self):
        """Test YAML validation with unexpected exception (lines 1383-1384)."""
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", side_effect=Exception("Unexpected error")):
                result = validate_yaml_standard("any_file.yaml")
                assert not result["is_valid"]
                assert any(
                    "Unexpected error during validation" in error
                    for error in result["errors"]
                )


class TestValidationHelpersCoverage:
    """Test validation helper functions."""

    def test_validate_standards_metadata_empty_fields(self):
        """Test standards metadata validation with empty fields (lines 1386-1391)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        standards_section = {
            "id": "",
            "name": "   ",
            "version": "1.0.0",
            "authority": None,
        }

        _validate_standards_metadata(standards_section, result)

        assert not result["is_valid"]
        assert any(
            "Empty value for required field: 'id'" in error
            for error in result["errors"]
        )
        assert any(
            "Empty value for required field: 'name'" in error
            for error in result["errors"]
        )

    def test_validate_standards_metadata_invalid_version(self):
        """Test standards metadata validation with invalid version format (lines 1397, 1401)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        standards_section = {
            "id": "test",
            "name": "test",
            "version": "invalid-version",
            "authority": "test",
        }

        _validate_standards_metadata(standards_section, result)

        assert any(
            "does not follow semantic versioning" in warning
            for warning in result["warnings"]
        )

    def test_validate_standards_metadata_invalid_date(self):
        """Test standards metadata validation with invalid effective_date (lines 1417-1419)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        standards_section = {
            "id": "test",
            "name": "test",
            "version": "1.0.0",
            "authority": "test",
            "effective_date": "invalid-date",
        }

        _validate_standards_metadata(standards_section, result)

        assert not result["is_valid"]
        assert any(
            "Invalid effective_date format" in error for error in result["errors"]
        )

    def test_validate_requirements_non_dict(self):
        """Test requirements validation with non-dictionary (lines 1446-1448)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        _validate_requirements_section("not a dict", result)

        assert not result["is_valid"]
        assert any(
            "Requirements section must be a dictionary" in error
            for error in result["errors"]
        )

    def test_validate_requirements_invalid_overall_minimum(self):
        """Test requirements validation with invalid overall_minimum (lines 1456-1458, 1464-1466)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        requirements_section = {"overall_minimum": "not a number"}

        _validate_requirements_section(requirements_section, result)

        assert not result["is_valid"]
        assert any(
            "overall_minimum must be a number" in error for error in result["errors"]
        )

        # Test out of range
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        requirements_section = {"overall_minimum": 150}

        _validate_requirements_section(requirements_section, result)

        assert not result["is_valid"]
        assert any(
            "overall_minimum must be between 0 and 100" in error
            for error in result["errors"]
        )

    def test_validate_dimension_requirements_non_dict(self):
        """Test dimension requirements validation with non-dictionary (lines 1475-1480)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        _validate_dimension_requirements("not a dict", result)

        assert not result["is_valid"]
        assert any(
            "dimension_requirements must be a dictionary" in error
            for error in result["errors"]
        )

    def test_validate_dimension_requirements_invalid_dimension(self):
        """Test dimension requirements validation with invalid dimension (lines 1506-1534)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        dim_requirements = {
            "invalid_dimension": {"minimum_score": 15},
            "validity": {"minimum_score": "not a number"},
        }

        _validate_dimension_requirements(dim_requirements, result)

        assert not result["is_valid"]
        assert any(
            "Unknown dimension: 'invalid_dimension'" in error
            for error in result["errors"]
        )
        assert any(
            "minimum_score for validity must be a number" in error
            for error in result["errors"]
        )

    def test_validate_field_requirements_non_dict(self):
        """Test field requirements validation with non-dictionary (lines 1582-1584)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        _validate_field_requirements("not a dict", result)

        assert not result["is_valid"]
        assert any(
            "field_requirements must be a dictionary" in error
            for error in result["errors"]
        )

    def test_validate_field_requirements_invalid_config(self):
        """Test field requirements validation with invalid field config (lines 1592-1594)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        field_requirements = {
            "field1": "not a dict",
            "field2": {
                "type": "invalid_type",
                "nullable": "not a boolean",
                "min_value": 10,
                "max_value": 5,
                "pattern": "[invalid regex",
            },
        }

        _validate_field_requirements(field_requirements, result)

        assert not result["is_valid"]
        assert any(
            "Field 'field1' configuration must be a dictionary" in error
            for error in result["errors"]
        )
        assert any("Invalid type 'invalid_type'" in error for error in result["errors"])
        assert any(
            "nullable for field 'field2' must be true or false" in error
            for error in result["errors"]
        )
        assert any(
            "min_value must be less than max_value" in error
            for error in result["errors"]
        )
        assert any("Invalid regex pattern" in error for error in result["errors"])


class TestShowConfigCommandCoverage:
    """Test show config command edge cases."""

    def test_show_config_no_config(self):
        """Test show config with no configuration (lines 1659-1661)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = None

            result = show_config_command()
            assert result == 1

    def test_show_config_invalid_structure(self):
        """Test show config with invalid configuration structure (lines 1701)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {"invalid": "config"}
            mock_manager.validate_config.return_value = False

            result = show_config_command()
            assert result == 1

    def test_show_config_general_exception(self):
        """Test show config with general exception (lines 1713)."""
        with patch(
            "adri.cli.commands.ConfigManager", side_effect=Exception("General error")
        ):
            result = show_config_command()
            assert result == 1

    def test_show_config_json_format(self):
        """Test show config with JSON format (lines 1730-1732)."""
        config = {
            "adri": {
                "project_name": "test",
                "version": "1.0.0",
                "default_environment": "development",
                "environments": {"development": {"paths": {"standards": "/tmp"}}},
            }
        }

        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = config
            mock_manager.validate_config.return_value = True

            result = show_config_command(format_type="json")
            assert result == 0

    def test_show_config_environment_not_found(self):
        """Test show config with environment not found (lines 1798-1800)."""
        config = {
            "adri": {
                "project_name": "test",
                "version": "1.0.0",
                "default_environment": "development",
                "environments": {"development": {"paths": {"standards": "/tmp"}}},
            }
        }

        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = config
            mock_manager.validate_config.return_value = True

            result = show_config_command(environment="nonexistent")
            assert result == 0  # Should continue and show message


class TestListCommandsCoverage:
    """Test list commands edge cases."""

    def test_list_standards_no_config(self):
        """Test list standards with no configuration (lines 1815-1816)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = None

            result = list_standards_command()
            # Should return 0 because bundled standards are always available
            assert result == 0

    def test_list_standards_invalid_environment(self):
        """Test list standards with invalid environment (lines 1822)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {"test": "config"}
            mock_manager.get_environment_config.side_effect = ValueError(
                "Invalid environment"
            )

            result = list_standards_command(environment="invalid")
            # Should return 0 because bundled standards are still shown
            assert result == 0

    def test_list_standards_directory_not_found(self):
        """Test list standards with directory not found (lines 1825-1826)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {
                "adri": {"default_environment": "dev"}
            }
            mock_manager.get_environment_config.return_value = {
                "paths": {"standards": "/nonexistent"}
            }

            result = list_standards_command()
            assert result == 0

    def test_list_standards_no_files(self):
        """Test list standards with no standard files (lines 1845-1855)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
                mock_manager = MagicMock()
                mock_config_manager.return_value = mock_manager
                mock_manager.get_active_config.return_value = {
                    "adri": {"default_environment": "dev"}
                }
                mock_manager.get_environment_config.return_value = {
                    "paths": {"standards": temp_dir}
                }

                result = list_standards_command()
                assert result == 0

    def test_list_standards_general_exception(self):
        """Test list standards with general exception."""
        with patch(
            "adri.cli.commands.ConfigManager", side_effect=Exception("General error")
        ):
            result = list_standards_command()
            assert result == 1

    def test_list_training_data_no_config(self):
        """Test list training data with no configuration (lines 1913-1915)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = None

            result = list_training_data_command()
            assert result == 1

    def test_list_training_data_invalid_environment(self):
        """Test list training data with invalid environment (lines 1942-1944)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {"test": "config"}
            mock_manager.get_environment_config.side_effect = ValueError(
                "Invalid environment"
            )

            result = list_training_data_command(environment="invalid")
            assert result == 1

    def test_list_training_data_directory_not_found(self):
        """Test list training data with directory not found (lines 1952-1954)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {
                "adri": {"default_environment": "dev"}
            }
            mock_manager.get_environment_config.return_value = {
                "paths": {"training_data": "/nonexistent"}
            }

            result = list_training_data_command()
            assert result == 0

    def test_list_training_data_no_files(self):
        """Test list training data with no data files (lines 1960-1963)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
                mock_manager = MagicMock()
                mock_config_manager.return_value = mock_manager
                mock_manager.get_active_config.return_value = {
                    "adri": {"default_environment": "dev"}
                }
                mock_manager.get_environment_config.return_value = {
                    "paths": {"training_data": temp_dir}
                }

                result = list_training_data_command()
                assert result == 0

    def test_list_training_data_general_exception(self):
        """Test list training data with general exception (lines 1969-1971)."""
        with patch(
            "adri.cli.commands.ConfigManager", side_effect=Exception("General error")
        ):
            result = list_training_data_command()
            assert result == 1

    def test_list_assessments_no_config(self):
        """Test list assessments with no configuration (lines 2036-2039)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = None

            result = list_assessments_command()
            assert result == 1

    def test_list_assessments_invalid_environment(self):
        """Test list assessments with invalid environment (lines 2068-2070)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {"test": "config"}
            mock_manager.get_environment_config.side_effect = ValueError(
                "Invalid environment"
            )

            result = list_assessments_command(environment="invalid")
            assert result == 1

    def test_list_assessments_directory_not_found(self):
        """Test list assessments with directory not found (lines 2097-2099)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {
                "adri": {"default_environment": "dev"}
            }
            mock_manager.get_environment_config.return_value = {
                "paths": {"assessments": "/nonexistent"}
            }

            result = list_assessments_command()
            assert result == 0

    def test_list_assessments_no_files(self):
        """Test list assessments with no assessment files (lines 2107-2109)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
                mock_manager = MagicMock()
                mock_config_manager.return_value = mock_manager
                mock_manager.get_active_config.return_value = {
                    "adri": {"default_environment": "dev"}
                }
                mock_manager.get_environment_config.return_value = {
                    "paths": {"assessments": temp_dir}
                }

                result = list_assessments_command()
                assert result == 0

    def test_list_assessments_general_exception(self):
        """Test list assessments with general exception (lines 2116-2125)."""
        with patch(
            "adri.cli.commands.ConfigManager", side_effect=Exception("General error")
        ):
            result = list_assessments_command()
            assert result == 1


class TestCleanCacheCommandCoverage:
    """Test clean cache command edge cases."""

    def test_clean_cache_no_config(self):
        """Test clean cache with no configuration (lines 2131)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = None

            result = clean_cache_command()
            assert result == 1

    def test_clean_cache_invalid_environment(self):
        """Test clean cache with invalid environment (lines 2134-2141)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {"test": "config"}
            mock_manager.get_environment_config.side_effect = ValueError(
                "Invalid environment"
            )

            result = clean_cache_command(environment="invalid")
            assert result == 1

    def test_clean_cache_general_exception(self):
        """Test clean cache with general exception."""
        with patch(
            "adri.cli.commands.ConfigManager", side_effect=Exception("General error")
        ):
            result = clean_cache_command()
            assert result == 1


class TestExportReportCommandCoverage:
    """Test export report command edge cases."""

    def test_export_report_no_config(self):
        """Test export report with no configuration (lines 2228-2230)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = None

            result = export_report_command(latest=True)
            assert result == 1

    def test_export_report_invalid_environment(self):
        """Test export report with invalid environment (lines 2260)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {"test": "config"}
            mock_manager.get_environment_config.side_effect = ValueError(
                "Invalid environment"
            )

            result = export_report_command(latest=True, environment="invalid")
            assert result == 1

    def test_export_report_no_assessments(self):
        """Test export report with no assessments found (lines 2270)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
                mock_manager = MagicMock()
                mock_config_manager.return_value = mock_manager
                mock_manager.get_active_config.return_value = {
                    "adri": {"default_environment": "dev"}
                }
                mock_manager.get_environment_config.return_value = {
                    "paths": {"assessments": temp_dir}
                }

                result = export_report_command(latest=True)
                assert result == 1

    def test_export_report_file_not_found(self):
        """Test export report with assessment file not found (lines 2280)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {
                "adri": {"default_environment": "dev"}
            }
            mock_manager.get_environment_config.return_value = {
                "paths": {"assessments": "/tmp"}
            }

            result = export_report_command(assessment_file="nonexistent.json")
            assert result == 1

    def test_export_report_no_parameters(self):
        """Test export report with no latest or file specified (lines 2312)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {
                "adri": {"default_environment": "dev"}
            }
            mock_manager.get_environment_config.return_value = {
                "paths": {"assessments": "/tmp"}
            }

            result = export_report_command()
            assert result == 1

    def test_export_report_unsupported_format(self):
        """Test export report with unsupported format (lines 2320)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a dummy assessment file
            assessment_file = os.path.join(temp_dir, "test_assessment.json")
            with open(assessment_file, "w") as f:
                json.dump({"overall_score": 85, "passed": True}, f)

            with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
                mock_manager = MagicMock()
                mock_config_manager.return_value = mock_manager
                mock_manager.get_active_config.return_value = {
                    "adri": {"default_environment": "dev"}
                }
                mock_manager.get_environment_config.return_value = {
                    "paths": {"assessments": temp_dir}
                }

                result = export_report_command(latest=True, format_type="pdf")
                assert result == 1

    def test_export_report_general_exception(self):
        """Test export report with general exception (lines 2335)."""
        with patch(
            "adri.cli.commands.ConfigManager", side_effect=Exception("General error")
        ):
            result = export_report_command(latest=True)
            assert result == 1


class TestShowStandardCommandCoverage:
    """Test show standard command edge cases."""

    def test_show_standard_no_config(self):
        """Test show standard with no configuration (lines 2347)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = None

            result = show_standard_command("test.yaml")
            assert result == 1

    def test_show_standard_invalid_environment(self):
        """Test show standard with invalid environment (lines 2357)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {"test": "config"}
            mock_manager.get_environment_config.side_effect = ValueError(
                "Invalid environment"
            )

            result = show_standard_command("test.yaml", environment="invalid")
            assert result == 1

    def test_show_standard_file_not_found(self):
        """Test show standard with file not found (lines 2365)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {
                "adri": {"default_environment": "dev"}
            }
            mock_manager.get_environment_config.return_value = {
                "paths": {"standards": "/tmp"}
            }

            with patch(
                "adri.cli.commands._resolve_standard_path",
                return_value="/nonexistent/file.yaml",
            ):
                result = show_standard_command("nonexistent.yaml")
                assert result == 1

    def test_show_standard_general_exception(self):
        """Test show standard with general exception."""
        with patch(
            "adri.cli.commands.ConfigManager", side_effect=Exception("General error")
        ):
            result = show_standard_command("test.yaml")
            assert result == 1


class TestExplainFailureCommandCoverage:
    """Test explain failure command edge cases."""

    def test_explain_failure_no_config(self):
        """Test explain failure with no configuration."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = None

            result = explain_failure_command(latest=True)
            assert result == 1

    def test_explain_failure_invalid_environment(self):
        """Test explain failure with invalid environment."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {"test": "config"}
            mock_manager.get_environment_config.side_effect = ValueError(
                "Invalid environment"
            )

            result = explain_failure_command(latest=True, environment="invalid")
            assert result == 1

    def test_explain_failure_no_assessments(self):
        """Test explain failure with no assessments found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
                mock_manager = MagicMock()
                mock_config_manager.return_value = mock_manager
                mock_manager.get_active_config.return_value = {
                    "adri": {"default_environment": "dev"}
                }
                mock_manager.get_environment_config.return_value = {
                    "paths": {"assessments": temp_dir}
                }

                result = explain_failure_command(latest=True)
                assert result == 1

    def test_explain_failure_file_not_found(self):
        """Test explain failure with assessment file not found."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {
                "adri": {"default_environment": "dev"}
            }
            mock_manager.get_environment_config.return_value = {
                "paths": {"assessments": "/tmp"}
            }

            result = explain_failure_command(assessment_file="nonexistent.json")
            assert result == 1

    def test_explain_failure_no_parameters(self):
        """Test explain failure with no latest or file specified."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.get_active_config.return_value = {
                "adri": {"default_environment": "dev"}
            }
            mock_manager.get_environment_config.return_value = {
                "paths": {"assessments": "/tmp"}
            }

            result = explain_failure_command()
            assert result == 1

    def test_explain_failure_general_exception(self):
        """Test explain failure with general exception."""
        with patch(
            "adri.cli.commands.ConfigManager", side_effect=Exception("General error")
        ):
            result = explain_failure_command(latest=True)
            assert result == 1


class TestDataLoadingFunctionsCoverage:
    """Test data loading functions edge cases."""

    def test_load_csv_data_empty_file(self):
        """Test loading empty CSV file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("")  # Empty file
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="CSV file is empty"):
                _load_csv_data(Path(temp_file))
        finally:
            os.unlink(temp_file)

    def test_load_json_data_non_list(self):
        """Test loading JSON file that's not a list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"not": "a list"}, f)
            temp_file = f.name

        try:
            with pytest.raises(
                ValueError, match="JSON file must contain a list of objects"
            ):
                _load_json_data(Path(temp_file))
        finally:
            os.unlink(temp_file)

    def test_load_parquet_data_pandas_not_available(self):
        """Test loading Parquet file when pandas is not available."""
        with patch("adri.cli.commands.pd", None):
            with pytest.raises(ImportError, match="pandas is required"):
                _load_parquet_data(Path("test.parquet"))

    def test_load_parquet_data_empty_file(self):
        """Test loading empty Parquet file."""
        with patch("adri.cli.commands.pd") as mock_pd:
            mock_df = MagicMock()
            mock_df.empty = True
            mock_pd.read_parquet.return_value = mock_df

            with pytest.raises(ValueError, match="Parquet file is empty"):
                _load_parquet_data(Path("test.parquet"))

    def test_load_parquet_data_read_error(self):
        """Test loading Parquet file with read error."""
        with patch("adri.cli.commands.pd") as mock_pd:
            mock_pd.read_parquet.side_effect = Exception("Parquet read error")

            with pytest.raises(ValueError, match="Failed to read Parquet file"):
                _load_parquet_data(Path("test.parquet"))

    def test_load_data_unsupported_format(self):
        """Test loading data with unsupported file format."""
        with pytest.raises(FileNotFoundError, match="Data file not found"):
            load_data("test.txt")

    def test_load_standard_yaml_error(self):
        """Test loading standard with YAML error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_file = f.name

        try:
            with pytest.raises(Exception, match="Invalid YAML format"):
                load_standard(temp_file)
        finally:
            os.unlink(temp_file)

    def test_load_standard_general_error(self):
        """Test loading standard with general error."""
        with pytest.raises(FileNotFoundError, match="Standard file not found"):
            load_standard("test.yaml")


class TestUtilityFunctionsCoverage:
    """Test utility functions edge cases."""

    def test_format_file_size_zero(self):
        """Test formatting zero file size."""
        result = _format_file_size(0)
        assert result == "0 B"

    def test_format_file_size_various_sizes(self):
        """Test formatting various file sizes."""
        assert "KB" in _format_file_size(1024)
        assert "MB" in _format_file_size(1024 * 1024)
        assert "GB" in _format_file_size(1024 * 1024 * 1024)

    def test_count_csv_rows_exception(self):
        """Test counting CSV rows with exception."""
        with patch("builtins.open", side_effect=Exception("Read error")):
            result = _count_csv_rows(Path("test.csv"))
            assert result == 0

    def test_get_dimension_recommendations_all_dimensions(self):
        """Test getting recommendations for all dimension types."""
        # Test each dimension type
        dimensions = [
            "validity",
            "completeness",
            "consistency",
            "freshness",
            "plausibility",
        ]

        for dim in dimensions:
            recommendations = _get_dimension_recommendations(dim, 5.0, {})
            assert len(recommendations) > 0
            # Check for severity indicators
            assert any(
                any(severity in rec for severity in ["CRITICAL", "MAJOR", "MINOR"])
                for rec in recommendations
            )

        # Test different score ranges
        recommendations = _get_dimension_recommendations("validity", 8.0, {})
        assert len(recommendations) > 0
        assert any("MAJOR" in rec for rec in recommendations)

        recommendations = _get_dimension_recommendations("validity", 12.0, {})
        assert len(recommendations) > 0
        assert any("MINOR" in rec for rec in recommendations)


class TestPathResolutionCoverage:
    """Test path resolution functions."""

    def test_resolve_data_path_absolute(self):
        """Test resolving absolute data path."""
        result = _resolve_data_path(
            "/absolute/path/data.csv", {"paths": {"training_data": "/tmp"}}
        )
        assert result == "/absolute/path/data.csv"

    def test_resolve_data_path_existing_relative(self):
        """Test resolving existing relative data path."""
        with tempfile.NamedTemporaryFile(suffix=".csv") as temp_file:
            result = _resolve_data_path(
                temp_file.name, {"paths": {"training_data": "/tmp"}}
            )
            assert result == temp_file.name

    def test_resolve_data_path_training_data_dir(self):
        """Test resolving data path in training data directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file = os.path.join(temp_dir, "data.csv")
            Path(data_file).touch()

            result = _resolve_data_path(
                "data.csv", {"paths": {"training_data": temp_dir}}
            )
            assert result == data_file

    def test_resolve_data_path_not_found(self):
        """Test resolving non-existent data path."""
        result = _resolve_data_path(
            "nonexistent.csv", {"paths": {"training_data": "/tmp"}}
        )
        assert result == "nonexistent.csv"

    def test_resolve_standard_path_with_extension(self):
        """Test resolving standard path with automatic extension."""
        with tempfile.TemporaryDirectory() as temp_dir:
            standard_file = os.path.join(temp_dir, "standard.yaml")
            Path(standard_file).touch()

            result = _resolve_standard_path(
                "standard", {"paths": {"standards": temp_dir}}
            )
            assert result == standard_file


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
