"""
Tests to cover specific missing lines in CLI commands module.

This test file targets the exact missing lines to achieve 99% coverage.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

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


class TestCommandsMissingLinesCoverage(unittest.TestCase):
    """Test CLI commands missing lines coverage."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            "adri": {
                "project_name": "test_project",
                "version": "2.0.0",
                "default_environment": "development",
                "environments": {
                    "development": {
                        "paths": {
                            "standards": os.path.join(self.temp_dir, "standards"),
                            "assessments": os.path.join(self.temp_dir, "assessments"),
                            "training_data": os.path.join(
                                self.temp_dir, "training_data"
                            ),
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

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("adri.cli.commands.ConfigManager")
    def test_setup_command_permission_error(self, mock_config_manager):
        """Test setup command with permission error (lines 103-105)."""
        mock_manager = Mock()
        mock_manager.create_default_config.side_effect = PermissionError(
            "Permission denied"
        )
        mock_config_manager.return_value = mock_manager

        result = setup_command(
            force=False, project_name="test", config_path="test.yaml"
        )
        self.assertEqual(result, 1)

    @patch("adri.cli.commands.ConfigManager")
    def test_setup_command_generic_exception(self, mock_config_manager):
        """Test setup command with generic exception (lines 179-180)."""
        mock_manager = Mock()
        mock_manager.create_default_config.side_effect = Exception("Generic error")
        mock_config_manager.return_value = mock_manager

        result = setup_command(
            force=False, project_name="test", config_path="test.yaml"
        )
        self.assertEqual(result, 1)

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.load_data")
    def test_assess_command_file_not_found(self, mock_load_data, mock_config_manager):
        """Test assess command with FileNotFoundError (lines 301-302)."""
        mock_manager = Mock()
        mock_manager.get_active_config.return_value = self.config
        mock_manager.get_environment_config.return_value = self.config["adri"][
            "environments"
        ]["development"]
        mock_config_manager.return_value = mock_manager

        mock_load_data.side_effect = FileNotFoundError("File not found")

        result = assess_command(
            data_path="nonexistent.csv",
            standard_path="test_standard.yaml",
            verbose=False,
        )
        self.assertEqual(result, 1)

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.load_data")
    def test_assess_command_generic_exception(
        self, mock_load_data, mock_config_manager
    ):
        """Test assess command with generic exception (lines 564-565)."""
        mock_manager = Mock()
        mock_manager.get_active_config.return_value = self.config
        mock_manager.get_environment_config.return_value = self.config["adri"][
            "environments"
        ]["development"]
        mock_config_manager.return_value = mock_manager

        mock_load_data.side_effect = Exception("Generic error")

        result = assess_command(
            data_path="test.csv", standard_path="test_standard.yaml", verbose=False
        )
        self.assertEqual(result, 1)

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.load_data")
    def test_generate_standard_file_not_found(
        self, mock_load_data, mock_config_manager
    ):
        """Test generate standard command with FileNotFoundError (lines 595-597)."""
        mock_manager = Mock()
        mock_manager.get_active_config.return_value = self.config
        mock_manager.get_environment_config.return_value = self.config["adri"][
            "environments"
        ]["development"]
        mock_config_manager.return_value = mock_manager

        mock_load_data.side_effect = FileNotFoundError("File not found")

        result = generate_adri_standard_command(
            data_path="nonexistent.csv", force=False, verbose=False
        )
        self.assertEqual(result, 1)

    @patch("adri.cli.commands.ConfigManager")
    @patch("adri.cli.commands.load_data")
    @patch("adri.cli.commands.DataProfiler")
    def test_generate_standard_generic_exception(
        self, mock_profiler, mock_load_data, mock_config_manager
    ):
        """Test generate standard command with generic exception (lines 724-726)."""
        mock_manager = Mock()
        mock_manager.get_active_config.return_value = self.config
        mock_manager.get_environment_config.return_value = self.config["adri"][
            "environments"
        ]["development"]
        mock_config_manager.return_value = mock_manager

        mock_load_data.return_value = [{"test": "data"}]
        mock_profiler_instance = Mock()
        mock_profiler_instance.profile_data.side_effect = Exception("Profiling error")
        mock_profiler.return_value = mock_profiler_instance

        result = generate_adri_standard_command(
            data_path="test.csv", force=False, verbose=True  # Test verbose path
        )
        self.assertEqual(result, 1)

    def test_load_csv_data_empty_file(self):
        """Test loading empty CSV file (lines 1000)."""
        # Create empty CSV file
        empty_csv = os.path.join(self.temp_dir, "empty.csv")
        with open(empty_csv, "w") as f:
            f.write("")

        with self.assertRaises(ValueError) as context:
            _load_csv_data(Path(empty_csv))
        self.assertIn("empty", str(context.exception))

    def test_load_parquet_data_empty_file(self):
        """Test loading empty Parquet file (lines 1057)."""
        with patch("adri.cli.commands.pd") as mock_pd:
            mock_df = Mock()
            mock_df.empty = True
            mock_pd.read_parquet.return_value = mock_df

            with self.assertRaises(ValueError) as context:
                _load_parquet_data(Path("test.parquet"))
            self.assertIn("empty", str(context.exception))

    def test_validate_yaml_standard_file_not_found(self):
        """Test validate YAML standard with file not found (lines 1253-1269)."""
        result = validate_yaml_standard("nonexistent.yaml")

        self.assertFalse(result["is_valid"])
        self.assertIn("File not found", result["errors"][0])

    def test_validate_yaml_standard_invalid_yaml(self):
        """Test validate YAML standard with invalid YAML (lines 1383-1384)."""
        invalid_yaml = os.path.join(self.temp_dir, "invalid.yaml")
        with open(invalid_yaml, "w") as f:
            f.write("invalid: yaml: content: [")

        result = validate_yaml_standard(invalid_yaml)

        self.assertFalse(result["is_valid"])
        self.assertIn("Invalid YAML syntax", result["errors"][0])

    def test_validate_yaml_standard_not_dict(self):
        """Test validate YAML standard with non-dict content (lines 1386-1391)."""
        non_dict_yaml = os.path.join(self.temp_dir, "non_dict.yaml")
        with open(non_dict_yaml, "w") as f:
            yaml.dump(["not", "a", "dict"], f)

        result = validate_yaml_standard(non_dict_yaml)

        self.assertFalse(result["is_valid"])
        self.assertIn("dictionary at the root level", result["errors"][0])

    def test_validate_yaml_standard_missing_sections(self):
        """Test validate YAML standard with missing sections (lines 1397, 1401)."""
        incomplete_yaml = os.path.join(self.temp_dir, "incomplete.yaml")
        with open(incomplete_yaml, "w") as f:
            yaml.dump({"standards": {"name": "test"}}, f)  # Missing requirements

        result = validate_yaml_standard(incomplete_yaml)

        self.assertFalse(result["is_valid"])
        self.assertIn("Missing required section: 'requirements'", result["errors"][0])

    def test_validate_yaml_standard_valid_standard(self):
        """Test validate YAML standard with valid standard (lines 1506-1534)."""
        valid_yaml = os.path.join(self.temp_dir, "valid.yaml")
        yaml_content = {
            "standards": {
                "id": "test-v1",
                "name": "Test Standard",
                "version": "1.0.0",
                "authority": "Test Authority",
            },
            "requirements": {"overall_minimum": 80},
        }
        with open(valid_yaml, "w") as f:
            yaml.dump(yaml_content, f)

        result = validate_yaml_standard(valid_yaml)

        # Should extract metadata successfully
        self.assertEqual(result["standard_name"], "Test Standard")
        self.assertEqual(result["standard_version"], "1.0.0")
        self.assertEqual(result["authority"], "Test Authority")
        self.assertTrue(result["is_valid"])

    def test_validate_standards_metadata_empty_fields(self):
        """Test validate standards metadata with empty fields (lines 1659-1661)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        standards_section = {
            "id": "",  # Empty field
            "name": "Test",
            "version": "1.0.0",
            "authority": "Test",
        }

        _validate_standards_metadata(standards_section, result)

        self.assertFalse(result["is_valid"])
        self.assertIn("Empty value for required field: 'id'", result["errors"][0])

    def test_validate_standards_metadata_invalid_version(self):
        """Test validate standards metadata with invalid version format (lines 1701)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        standards_section = {
            "id": "test-v1",
            "name": "Test",
            "version": "invalid-version",  # Invalid semver
            "authority": "Test",
        }

        _validate_standards_metadata(standards_section, result)

        self.assertIn("does not follow semantic versioning", result["warnings"][0])

    def test_validate_standards_metadata_invalid_date(self):
        """Test validate standards metadata with invalid effective_date (lines 1713)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        standards_section = {
            "id": "test-v1",
            "name": "Test",
            "version": "1.0.0",
            "authority": "Test",
            "effective_date": "invalid-date",
        }

        _validate_standards_metadata(standards_section, result)

        self.assertFalse(result["is_valid"])
        self.assertIn("Invalid effective_date format", result["errors"][0])

    def test_validate_requirements_section_not_dict(self):
        """Test validate requirements section with non-dict (lines 1822)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        _validate_requirements_section("not a dict", result)

        self.assertFalse(result["is_valid"])
        self.assertIn("Requirements section must be a dictionary", result["errors"][0])

    def test_validate_requirements_section_invalid_overall_minimum(self):
        """Test validate requirements section with invalid overall_minimum (lines 1845-1855)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        # Test non-numeric overall_minimum
        requirements = {"overall_minimum": "not a number"}
        _validate_requirements_section(requirements, result)
        self.assertFalse(result["is_valid"])
        self.assertIn("overall_minimum must be a number", result["errors"][0])

        # Reset result
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        # Test out of range overall_minimum
        requirements = {"overall_minimum": 150}  # > 100
        _validate_requirements_section(requirements, result)
        self.assertFalse(result["is_valid"])
        self.assertIn("overall_minimum must be between 0 and 100", result["errors"][0])

    def test_validate_dimension_requirements_not_dict(self):
        """Test validate dimension requirements with non-dict (lines 1969-1971)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        _validate_dimension_requirements("not a dict", result)

        self.assertFalse(result["is_valid"])
        self.assertIn(
            "dimension_requirements must be a dictionary", result["errors"][0]
        )

    def test_validate_dimension_requirements_invalid_dimension(self):
        """Test validate dimension requirements with invalid dimension (lines 2036-2039)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        dim_requirements = {"invalid_dimension": {"minimum_score": 15}}

        _validate_dimension_requirements(dim_requirements, result)

        self.assertFalse(result["is_valid"])
        self.assertIn("Unknown dimension: 'invalid_dimension'", result["errors"][0])

    def test_validate_dimension_requirements_invalid_score(self):
        """Test validate dimension requirements with invalid minimum_score (lines 2124-2125, 2131)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        # Test non-numeric minimum_score
        dim_requirements = {"validity": {"minimum_score": "not a number"}}
        _validate_dimension_requirements(dim_requirements, result)
        self.assertFalse(result["is_valid"])
        self.assertIn(
            "minimum_score for validity must be a number", result["errors"][0]
        )

        # Reset result
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        # Test out of range minimum_score
        dim_requirements = {"validity": {"minimum_score": 25}}  # > 20
        _validate_dimension_requirements(dim_requirements, result)
        self.assertFalse(result["is_valid"])
        self.assertIn(
            "minimum_score for validity must be between 0 and 20", result["errors"][0]
        )

    def test_validate_field_requirements_not_dict(self):
        """Test validate field requirements with non-dict (lines 2312)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        _validate_field_requirements("not a dict", result)

        self.assertFalse(result["is_valid"])
        self.assertIn("field_requirements must be a dictionary", result["errors"][0])

    def test_validate_field_requirements_field_config_not_dict(self):
        """Test validate field requirements with field config not dict (lines 2320)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        field_requirements = {"test_field": "not a dict"}

        _validate_field_requirements(field_requirements, result)

        self.assertFalse(result["is_valid"])
        self.assertIn(
            "Field 'test_field' configuration must be a dictionary", result["errors"][0]
        )

    def test_validate_field_requirements_invalid_type(self):
        """Test validate field requirements with invalid type (lines 2335)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        field_requirements = {"test_field": {"type": "invalid_type"}}

        _validate_field_requirements(field_requirements, result)

        self.assertFalse(result["is_valid"])
        self.assertIn(
            "Invalid type 'invalid_type' for field 'test_field'", result["errors"][0]
        )

    def test_validate_field_requirements_invalid_nullable(self):
        """Test validate field requirements with invalid nullable (lines 2347)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        field_requirements = {"test_field": {"nullable": "not a boolean"}}

        _validate_field_requirements(field_requirements, result)

        self.assertFalse(result["is_valid"])
        self.assertIn(
            "nullable for field 'test_field' must be true or false", result["errors"][0]
        )

    def test_validate_field_requirements_invalid_min_max_range(self):
        """Test validate field requirements with invalid min/max range (lines 2357)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        field_requirements = {
            "test_field": {"min_value": 100, "max_value": 50}  # min > max
        }

        _validate_field_requirements(field_requirements, result)

        self.assertFalse(result["is_valid"])
        self.assertIn("min_value must be less than max_value", result["errors"][0])

    def test_validate_field_requirements_invalid_regex(self):
        """Test validate field requirements with invalid regex pattern (lines 2365)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        field_requirements = {"test_field": {"pattern": "[invalid regex"}}

        _validate_field_requirements(field_requirements, result)

        self.assertFalse(result["is_valid"])
        self.assertIn(
            "Invalid regex pattern for field 'test_field'", result["errors"][0]
        )

    @patch("adri.cli.commands.ConfigManager")
    def test_validate_standard_command_file_not_found(self, mock_config_manager):
        """Test validate standard command with file not found."""
        result = validate_standard_command("nonexistent.yaml", verbose=False)
        self.assertEqual(result, 1)

    @patch("adri.cli.commands.ConfigManager")
    def test_validate_standard_command_generic_exception(self, mock_config_manager):
        """Test validate standard command with generic exception."""
        with patch("adri.cli.commands.validate_yaml_standard") as mock_validate:
            mock_validate.side_effect = Exception("Validation error")

            result = validate_standard_command("test.yaml", verbose=False)
            self.assertEqual(result, 1)

    @patch("adri.cli.commands.ConfigManager")
    def test_show_config_command_no_config(self, mock_config_manager):
        """Test show config command with no configuration."""
        mock_manager = Mock()
        mock_manager.get_active_config.return_value = None
        mock_config_manager.return_value = mock_manager

        result = show_config_command()
        self.assertEqual(result, 1)

    @patch("adri.cli.commands.ConfigManager")
    def test_show_config_command_invalid_config(self, mock_config_manager):
        """Test show config command with invalid configuration."""
        mock_manager = Mock()
        mock_manager.get_active_config.return_value = {"invalid": "config"}
        mock_manager.validate_config.return_value = False
        mock_config_manager.return_value = mock_manager

        result = show_config_command()
        self.assertEqual(result, 1)

    @patch("adri.cli.commands.ConfigManager")
    def test_show_config_command_generic_exception(self, mock_config_manager):
        """Test show config command with generic exception."""
        mock_manager = Mock()
        mock_manager.get_active_config.side_effect = Exception("Config error")
        mock_config_manager.return_value = mock_manager

        result = show_config_command()
        self.assertEqual(result, 1)

    def test_output_config_json(self):
        """Test output config in JSON format."""
        result = _output_config_json(self.config, "development", None)
        self.assertEqual(result, 0)

    def test_output_config_human_with_validation(self):
        """Test output config in human format with validation."""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": ["Test warning"],
            "path_status": {
                "development.standards": {"exists": True, "file_count": 5},
                "development.assessments": {"exists": False, "file_count": -1},
            },
        }

        mock_config_manager = Mock()

        result = _output_config_human(
            self.config,
            "development",
            False,  # paths_only
            True,  # validate
            validation_results,
            mock_config_manager,
        )
        self.assertEqual(result, 0)

    def test_show_assessment_settings(self):
        """Test show assessment settings."""
        # This should not raise any exceptions
        _show_assessment_settings(self.config["adri"])

    def test_show_generation_settings(self):
        """Test show generation settings."""
        # This should not raise any exceptions
        _show_generation_settings(self.config["adri"])

    def test_show_validation_results(self):
        """Test show validation results."""
        validation_results = {
            "valid": False,
            "errors": ["Test error"],
            "warnings": ["Test warning"],
            "path_status": {
                "development.standards": {"exists": True, "file_count": 5},
                "development.assessments": {"exists": False, "file_count": 0},
            },
        }

        # This should not raise any exceptions
        _show_validation_results(validation_results)

    @patch("adri.cli.commands.ConfigManager")
    def test_list_standards_command_no_config(self, mock_config_manager):
        """Test list standards command with no configuration."""
        mock_manager = Mock()
        mock_manager.get_active_config.return_value = None
        mock_config_manager.return_value = mock_manager

        result = list_standards_command()
        # Should return 0 because bundled standards are always available
        self.assertEqual(result, 0)

    @patch("adri.cli.commands.ConfigManager")
    def test_list_standards_command_invalid_environment(self, mock_config_manager):
        """Test list standards command with invalid environment."""
        mock_manager = Mock()
        mock_manager.get_active_config.return_value = self.config
        mock_manager.get_environment_config.side_effect = ValueError(
            "Invalid environment"
        )
        mock_config_manager.return_value = mock_manager

        result = list_standards_command(environment="invalid")
        # Should return 0 because bundled standards are still shown
        self.assertEqual(result, 0)

    @patch("adri.cli.commands.ConfigManager")
    def test_list_standards_command_generic_exception(self, mock_config_manager):
        """Test list standards command with generic exception."""
        mock_manager = Mock()
        mock_manager.get_active_config.side_effect = Exception("List error")
        mock_config_manager.return_value = mock_manager

        result = list_standards_command()
        self.assertEqual(result, 1)

    def test_format_file_size(self):
        """Test file size formatting."""
        self.assertEqual(_format_file_size(0), "0 B")
        self.assertEqual(_format_file_size(1024), "1.0 KB")
        self.assertEqual(_format_file_size(1024 * 1024), "1.0 MB")

    def test_count_csv_rows_exception(self):
        """Test CSV row counting with exception."""
        # Test with non-existent file
        result = _count_csv_rows(Path("nonexistent.csv"))
        self.assertEqual(result, 0)

    def test_get_dimension_recommendations(self):
        """Test dimension recommendations for different dimensions and scores."""
        # Test validity dimension
        recs = _get_dimension_recommendations("validity", 3.0, {})
        self.assertIn("CRITICAL", recs[0])
        self.assertIn("email formats", recs[1])

        # Test completeness dimension
        recs = _get_dimension_recommendations("completeness", 8.0, {})
        self.assertIn("MAJOR", recs[0])
        self.assertIn("missing required fields", recs[1])

        # Test consistency dimension
        recs = _get_dimension_recommendations("consistency", 12.0, {})
        self.assertIn("MINOR", recs[0])
        self.assertIn("date formats", recs[1])

        # Test freshness dimension
        recs = _get_dimension_recommendations("freshness", 5.0, {})
        self.assertIn("Update old records", recs[1])

        # Test plausibility dimension
        recs = _get_dimension_recommendations("plausibility", 15.0, {})
        self.assertIn("outlier values", recs[1])

    @patch("adri.cli.commands.ConfigManager")
    def test_list_training_data_command_no_config(self, mock_config_manager):
        """Test list training data command with no configuration."""
        mock_manager = Mock()
        mock_manager.get_active_config.return_value = None
        mock_config_manager.return_value = mock_manager

        result = list_training_data_command()
        self.assertEqual(result, 1)

    @patch("adri.cli.commands.ConfigManager")
    def test_list_assessments_command_no_config(self, mock_config_manager):
        """Test list assessments command with no configuration."""
        mock_manager = Mock()
        mock_manager.get_active_config.return_value = None
        mock_config_manager.return_value = mock_manager

        result = list_assessments_command()
        self.assertEqual(result, 1)

    @patch("adri.cli.commands.ConfigManager")
    def test_clean_cache_command_no_config(self, mock_config_manager):
        """Test clean cache command with no configuration."""
        mock_manager = Mock()
        mock_manager.get_active_config.return_value = None
        mock_config_manager.return_value = mock_manager

        result = clean_cache_command()
        self.assertEqual(result, 1)

    @patch("adri.cli.commands.ConfigManager")
    def test_export_report_command_no_config(self, mock_config_manager):
        """Test export report command with no configuration."""
        mock_manager = Mock()
        mock_manager.get_active_config.return_value = None
        mock_config_manager.return_value = mock_manager

        result = export_report_command(latest=True)
        self.assertEqual(result, 1)

    @patch("adri.cli.commands.ConfigManager")
    def test_show_standard_command_no_config(self, mock_config_manager):
        """Test show standard command with no configuration."""
        mock_manager = Mock()
        mock_manager.get_active_config.return_value = None
        mock_config_manager.return_value = mock_manager

        result = show_standard_command("test_standard.yaml")
        self.assertEqual(result, 1)

    @patch("adri.cli.commands.ConfigManager")
    def test_explain_failure_command_no_config(self, mock_config_manager):
        """Test explain failure command with no configuration."""
        mock_manager = Mock()
        mock_manager.get_active_config.return_value = None
        mock_config_manager.return_value = mock_manager

        result = explain_failure_command(latest=True)
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
