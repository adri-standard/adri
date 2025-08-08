"""
Ultimate coverage test for CLI commands module.

This test file targets the exact remaining missing lines with surgical precision.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, MagicMock, Mock, mock_open, patch

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


class TestCommandsUltimateCoverage(unittest.TestCase):
    """Ultimate coverage test for CLI commands."""

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

    def test_import_error_simulation_lines_19_20(self):
        """Test import error handling for pandas (lines 19-20)."""
        # This tests the try/except ImportError block for pandas
        # We can't easily test this directly, but we can test the pd = None path

        # Test _load_parquet_data when pd is None
        with patch("adri.cli.commands.pd", None):
            with self.assertRaises(ImportError) as context:
                _load_parquet_data(Path("test.parquet"))
            self.assertIn("pandas is required", str(context.exception))

    def test_setup_command_environment_error_lines_179_180(self):
        """Test setup command with environment configuration error."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = Mock()
            mock_manager.create_default_config.side_effect = ValueError(
                "Environment error"
            )
            mock_config_manager.return_value = mock_manager

            result = setup_command(
                force=False, project_name="test", config_path="test.yaml"
            )
            self.assertEqual(result, 1)

    def test_assess_command_file_not_found_lines_301_302(self):
        """Test assess command FileNotFoundError handling."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            with patch("adri.cli.commands.load_data") as mock_load_data:
                mock_manager = Mock()
                mock_manager.get_active_config.return_value = self.config
                mock_manager.get_environment_config.return_value = self.config["adri"][
                    "environments"
                ]["development"]
                mock_config_manager.return_value = mock_manager

                # Simulate FileNotFoundError
                mock_load_data.side_effect = FileNotFoundError("Data file not found")

                result = assess_command(
                    data_path="missing.csv", standard_path="test_standard.yaml"
                )
                self.assertEqual(result, 1)

    def test_assess_command_generic_exception_lines_564_565(self):
        """Test assess command generic exception handling."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            with patch("adri.cli.commands.load_data") as mock_load_data:
                with patch("adri.cli.commands.load_standard") as mock_load_standard:
                    with patch("adri.cli.commands.AssessmentEngine") as mock_engine:
                        mock_manager = Mock()
                        mock_manager.get_active_config.return_value = self.config
                        mock_manager.get_environment_config.return_value = self.config[
                            "adri"
                        ]["environments"]["development"]
                        mock_config_manager.return_value = mock_manager

                        mock_load_data.return_value = [{"test": "data"}]
                        mock_load_standard.return_value = {"test": "standard"}

                        # Mock pandas DataFrame
                        with patch("adri.cli.commands.pd") as mock_pd:
                            mock_df = Mock()
                            mock_pd.DataFrame.return_value = mock_df

                            # Make the assessment engine fail
                            mock_engine_instance = Mock()
                            mock_engine_instance.assess.side_effect = Exception(
                                "Assessment failed"
                            )
                            mock_engine.return_value = mock_engine_instance

                            result = assess_command(
                                data_path="test.csv", standard_path="test_standard.yaml"
                            )
                            self.assertEqual(result, 1)

    def test_generate_standard_file_not_found_lines_595_597(self):
        """Test generate standard FileNotFoundError handling."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            with patch("adri.cli.commands.load_data") as mock_load_data:
                mock_manager = Mock()
                mock_manager.get_active_config.return_value = self.config
                mock_manager.get_environment_config.return_value = self.config["adri"][
                    "environments"
                ]["development"]
                mock_config_manager.return_value = mock_manager

                mock_load_data.side_effect = FileNotFoundError("Data file not found")

                result = generate_adri_standard_command(data_path="missing.csv")
                self.assertEqual(result, 1)

    def test_generate_standard_exception_verbose_lines_724_726(self):
        """Test generate standard exception with verbose output."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            with patch("adri.cli.commands.load_data") as mock_load_data:
                with patch("adri.cli.commands.DataProfiler") as mock_profiler:
                    with patch("adri.cli.commands.StandardGenerator") as mock_generator:
                        with patch("adri.cli.commands.pd") as mock_pd:
                            mock_manager = Mock()
                            mock_manager.get_active_config.return_value = self.config
                            mock_manager.get_environment_config.return_value = (
                                self.config["adri"]["environments"]["development"]
                            )
                            mock_config_manager.return_value = mock_manager

                            mock_load_data.return_value = [{"test": "data"}]

                            # Mock DataFrame
                            mock_df = Mock()
                            mock_df.head.return_value = mock_df
                            mock_pd.DataFrame.return_value = mock_df

                            # Mock profiler
                            mock_profiler_instance = Mock()
                            mock_profiler_instance.profile_data.return_value = {
                                "summary": {"total_rows": 100}
                            }
                            mock_profiler.return_value = mock_profiler_instance

                            # Mock generator to fail
                            mock_generator_instance = Mock()
                            mock_generator_instance.generate_standard.side_effect = (
                                Exception("Generation failed")
                            )
                            mock_generator.return_value = mock_generator_instance

                            # Test with verbose=True to trigger the verbose exception path
                            result = generate_adri_standard_command(
                                data_path="test.csv", verbose=True
                            )
                            self.assertEqual(result, 1)

    def test_load_csv_data_empty_file_line_1000(self):
        """Test _load_csv_data with empty file (line 1000)."""
        # Create a CSV file with only headers
        csv_file = os.path.join(self.temp_dir, "headers_only.csv")
        with open(csv_file, "w") as f:
            f.write("header1,header2\n")  # Only headers, no data

        result = _load_csv_data(Path(csv_file))
        self.assertEqual(result, [])

    def test_load_parquet_data_empty_dataframe_line_1057(self):
        """Test _load_parquet_data with empty DataFrame (line 1057)."""
        with patch("adri.cli.commands.pd") as mock_pd:
            mock_df = Mock()
            mock_df.empty = True
            mock_pd.read_parquet.return_value = mock_df

            with self.assertRaises(ValueError) as context:
                _load_parquet_data(Path("empty.parquet"))
            self.assertIn("empty", str(context.exception))

    def test_validate_yaml_standard_file_not_found_lines_1253_1269(self):
        """Test validate_yaml_standard file not found (lines 1253-1269)."""
        result = validate_yaml_standard("nonexistent_file.yaml")

        self.assertFalse(result["is_valid"])
        self.assertIn("File not found", result["errors"][0])
        self.assertEqual(result["file_path"], "nonexistent_file.yaml")

    def test_validate_yaml_standard_yaml_error_lines_1383_1384(self):
        """Test validate_yaml_standard YAML error (lines 1383-1384)."""
        invalid_yaml = os.path.join(self.temp_dir, "invalid.yaml")
        with open(invalid_yaml, "w") as f:
            f.write("invalid: yaml: [unclosed")

        result = validate_yaml_standard(invalid_yaml)

        self.assertFalse(result["is_valid"])
        self.assertIn("Invalid YAML syntax", result["errors"][0])

    def test_validate_yaml_standard_non_dict_lines_1386_1391(self):
        """Test validate_yaml_standard non-dict root (lines 1386-1391)."""
        list_yaml = os.path.join(self.temp_dir, "list.yaml")
        with open(list_yaml, "w") as f:
            yaml.dump(["item1", "item2"], f)

        result = validate_yaml_standard(list_yaml)

        self.assertFalse(result["is_valid"])
        self.assertIn("dictionary at the root level", result["errors"][0])

    def test_validate_yaml_standard_missing_sections_lines_1397_1401(self):
        """Test validate_yaml_standard missing sections (lines 1397, 1401)."""
        # Missing 'standards' section
        missing_standards = os.path.join(self.temp_dir, "missing_standards.yaml")
        with open(missing_standards, "w") as f:
            yaml.dump({"requirements": {"overall_minimum": 80}}, f)

        result = validate_yaml_standard(missing_standards)

        self.assertFalse(result["is_valid"])
        self.assertIn("Missing required section: 'standards'", result["errors"][0])

    def test_validate_yaml_standard_valid_standard_lines_1506_1534(self):
        """Test validate_yaml_standard with valid standard (lines 1506-1534)."""
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

    def test_validate_standards_metadata_empty_field_lines_1659_1661(self):
        """Test _validate_standards_metadata empty field (lines 1659-1661)."""
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

    def test_validate_standards_metadata_version_warning_line_1701(self):
        """Test _validate_standards_metadata version warning (line 1701)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        standards_section = {
            "id": "test-v1",
            "name": "Test",
            "version": "invalid-version",
            "authority": "Test",
        }

        _validate_standards_metadata(standards_section, result)

        self.assertIn("does not follow semantic versioning", result["warnings"][0])

    def test_validate_standards_metadata_invalid_date_line_1713(self):
        """Test _validate_standards_metadata invalid date (line 1713)."""
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

    def test_validate_requirements_section_not_dict_line_1822(self):
        """Test _validate_requirements_section not dict (line 1822)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        _validate_requirements_section("not a dict", result)

        self.assertFalse(result["is_valid"])
        self.assertIn("Requirements section must be a dictionary", result["errors"][0])

    def test_validate_requirements_section_invalid_overall_minimum_lines_1845_1855(
        self,
    ):
        """Test _validate_requirements_section invalid overall_minimum (lines 1845-1855)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        # Test non-numeric
        requirements = {"overall_minimum": "not a number"}
        _validate_requirements_section(requirements, result)
        self.assertFalse(result["is_valid"])
        self.assertIn("overall_minimum must be a number", result["errors"][0])

        # Reset and test out of range
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        requirements = {"overall_minimum": 150}
        _validate_requirements_section(requirements, result)
        self.assertFalse(result["is_valid"])
        self.assertIn("overall_minimum must be between 0 and 100", result["errors"][0])

    def test_validate_dimension_requirements_not_dict_lines_1969_1971(self):
        """Test _validate_dimension_requirements not dict (lines 1969-1971)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        _validate_dimension_requirements("not a dict", result)

        self.assertFalse(result["is_valid"])
        self.assertIn(
            "dimension_requirements must be a dictionary", result["errors"][0]
        )

    def test_validate_dimension_requirements_unknown_dimension_lines_2036_2039(self):
        """Test _validate_dimension_requirements unknown dimension (lines 2036-2039)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        dim_requirements = {"unknown_dimension": {"minimum_score": 15}}

        _validate_dimension_requirements(dim_requirements, result)

        self.assertFalse(result["is_valid"])
        self.assertIn("Unknown dimension: 'unknown_dimension'", result["errors"][0])

    def test_validate_dimension_requirements_invalid_score_lines_2124_2125_2131(self):
        """Test _validate_dimension_requirements invalid score (lines 2124-2125, 2131)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        # Test non-numeric
        dim_requirements = {"validity": {"minimum_score": "not a number"}}
        _validate_dimension_requirements(dim_requirements, result)
        self.assertFalse(result["is_valid"])
        self.assertIn(
            "minimum_score for validity must be a number", result["errors"][0]
        )

        # Reset and test out of range
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        dim_requirements = {"validity": {"minimum_score": 25}}
        _validate_dimension_requirements(dim_requirements, result)
        self.assertFalse(result["is_valid"])
        self.assertIn(
            "minimum_score for validity must be between 0 and 20", result["errors"][0]
        )

    def test_validate_field_requirements_not_dict_line_2312(self):
        """Test _validate_field_requirements not dict (line 2312)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        _validate_field_requirements("not a dict", result)

        self.assertFalse(result["is_valid"])
        self.assertIn("field_requirements must be a dictionary", result["errors"][0])

    def test_validate_field_requirements_field_config_not_dict_line_2320(self):
        """Test _validate_field_requirements field config not dict (line 2320)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        field_requirements = {"field1": "not a dict"}

        _validate_field_requirements(field_requirements, result)

        self.assertFalse(result["is_valid"])
        self.assertIn(
            "Field 'field1' configuration must be a dictionary", result["errors"][0]
        )

    def test_validate_field_requirements_invalid_type_line_2335(self):
        """Test _validate_field_requirements invalid type (line 2335)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        field_requirements = {"field1": {"type": "invalid_type"}}

        _validate_field_requirements(field_requirements, result)

        self.assertFalse(result["is_valid"])
        self.assertIn(
            "Invalid type 'invalid_type' for field 'field1'", result["errors"][0]
        )

    def test_validate_field_requirements_invalid_nullable_line_2347(self):
        """Test _validate_field_requirements invalid nullable (line 2347)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        field_requirements = {"field1": {"nullable": "not a boolean"}}

        _validate_field_requirements(field_requirements, result)

        self.assertFalse(result["is_valid"])
        self.assertIn(
            "nullable for field 'field1' must be true or false", result["errors"][0]
        )

    def test_validate_field_requirements_min_max_range_line_2357(self):
        """Test _validate_field_requirements min >= max (line 2357)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        field_requirements = {
            "field1": {"min_value": 100, "max_value": 50}  # min > max
        }

        _validate_field_requirements(field_requirements, result)

        self.assertFalse(result["is_valid"])
        self.assertIn("min_value must be less than max_value", result["errors"][0])

    def test_validate_field_requirements_invalid_regex_line_2365(self):
        """Test _validate_field_requirements invalid regex (line 2365)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}

        field_requirements = {"field1": {"pattern": "[invalid"}}

        _validate_field_requirements(field_requirements, result)

        self.assertFalse(result["is_valid"])
        self.assertIn("Invalid regex pattern for field 'field1'", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
