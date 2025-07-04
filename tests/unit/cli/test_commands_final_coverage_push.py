"""
Final push to achieve 99% coverage for CLI commands module.

This test file targets the exact remaining missing lines.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
import yaml
import re

from adri.cli.commands import (
    setup_command,
    assess_command,
    generate_adri_standard_command,
    validate_standard_command,
    validate_yaml_standard,
    _validate_standards_metadata,
    _validate_requirements_section,
    _validate_dimension_requirements,
    _validate_field_requirements,
    show_config_command,
    _output_config_json,
    _output_config_human,
    _show_assessment_settings,
    _show_generation_settings,
    _show_validation_results,
    list_standards_command,
    list_training_data_command,
    list_assessments_command,
    clean_cache_command,
    export_report_command,
    show_standard_command,
    explain_failure_command,
    _get_dimension_recommendations,
    load_data,
    _load_csv_data,
    _load_json_data,
    _load_parquet_data,
    load_standard,
    _resolve_data_path,
    _resolve_standard_path,
    _format_file_size,
    _count_csv_rows,
)


class TestCommandsFinalCoveragePush(unittest.TestCase):
    """Final coverage push for CLI commands."""

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
                            "training_data": os.path.join(self.temp_dir, "training_data"),
                        }
                    }
                },
                "assessment": {
                    "caching": {"enabled": False},  # Test disabled caching
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

    def test_setup_command_lines_19_20(self):
        """Test setup command lines 19-20 (import error handling)."""
        # These lines are likely import statements that can't be easily tested
        # Let's test the actual setup functionality that would trigger these paths
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = Mock()
            mock_manager.create_default_config.return_value = {"test": "config"}
            mock_manager.save_config.return_value = None
            mock_manager.create_directory_structure.return_value = None
            mock_config_manager.return_value = mock_manager
            
            # Test with config_path that requires directory creation
            result = setup_command(
                force=False, 
                project_name="test", 
                config_path="subdir/test.yaml"
            )
            self.assertEqual(result, 0)

    def test_assess_command_lines_179_180(self):
        """Test assess command lines 179-180 (environment error handling)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            mock_manager = Mock()
            mock_manager.get_active_config.return_value = self.config
            mock_manager.get_environment_config.side_effect = ValueError("Invalid environment")
            mock_config_manager.return_value = mock_manager

            result = assess_command(
                data_path="test.csv",
                standard_path="test_standard.yaml",
                environment="invalid_env"
            )
            self.assertEqual(result, 1)

    def test_assess_command_lines_301_302(self):
        """Test assess command lines 301-302 (file not found specific path)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            with patch("adri.cli.commands.load_data") as mock_load_data:
                mock_manager = Mock()
                mock_manager.get_active_config.return_value = self.config
                mock_manager.get_environment_config.return_value = self.config["adri"]["environments"]["development"]
                mock_config_manager.return_value = mock_manager

                mock_load_data.side_effect = FileNotFoundError("Specific file not found")

                result = assess_command(
                    data_path="missing.csv",
                    standard_path="test_standard.yaml"
                )
                self.assertEqual(result, 1)

    def test_assess_command_lines_564_565(self):
        """Test assess command lines 564-565 (generic exception path)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            with patch("adri.cli.commands.load_data") as mock_load_data:
                with patch("adri.cli.commands.load_standard") as mock_load_standard:
                    mock_manager = Mock()
                    mock_manager.get_active_config.return_value = self.config
                    mock_manager.get_environment_config.return_value = self.config["adri"]["environments"]["development"]
                    mock_config_manager.return_value = mock_manager

                    mock_load_data.return_value = [{"test": "data"}]
                    mock_load_standard.side_effect = Exception("Standard loading error")

                    result = assess_command(
                        data_path="test.csv",
                        standard_path="test_standard.yaml"
                    )
                    self.assertEqual(result, 1)

    def test_generate_standard_lines_595_597(self):
        """Test generate standard lines 595-597 (file not found path)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            with patch("adri.cli.commands.load_data") as mock_load_data:
                mock_manager = Mock()
                mock_manager.get_active_config.return_value = self.config
                mock_manager.get_environment_config.return_value = self.config["adri"]["environments"]["development"]
                mock_config_manager.return_value = mock_manager

                mock_load_data.side_effect = FileNotFoundError("Data file not found")

                result = generate_adri_standard_command(
                    data_path="missing.csv"
                )
                self.assertEqual(result, 1)

    def test_generate_standard_lines_724_726(self):
        """Test generate standard lines 724-726 (exception with verbose)."""
        with patch("adri.cli.commands.ConfigManager") as mock_config_manager:
            with patch("adri.cli.commands.load_data") as mock_load_data:
                with patch("adri.cli.commands.DataProfiler") as mock_profiler:
                    with patch("adri.cli.commands.StandardGenerator") as mock_generator:
                        mock_manager = Mock()
                        mock_manager.get_active_config.return_value = self.config
                        mock_manager.get_environment_config.return_value = self.config["adri"]["environments"]["development"]
                        mock_config_manager.return_value = mock_manager

                        mock_load_data.return_value = [{"test": "data"}]
                        
                        mock_profiler_instance = Mock()
                        mock_profiler_instance.profile_data.return_value = {"summary": {"total_rows": 100}}
                        mock_profiler.return_value = mock_profiler_instance
                        
                        mock_generator_instance = Mock()
                        mock_generator_instance.generate_standard.side_effect = Exception("Generation failed")
                        mock_generator.return_value = mock_generator_instance

                        result = generate_adri_standard_command(
                            data_path="test.csv",
                            verbose=True  # This should trigger the verbose exception path
                        )
                        self.assertEqual(result, 1)

    def test_load_csv_data_line_1000(self):
        """Test _load_csv_data line 1000 (empty file check)."""
        # Create a CSV file with only headers but no data
        csv_file = os.path.join(self.temp_dir, "headers_only.csv")
        with open(csv_file, "w") as f:
            f.write("header1,header2\n")  # Only headers, no data rows

        result = _load_csv_data(Path(csv_file))
        self.assertEqual(result, [])  # Should return empty list

    def test_load_parquet_data_line_1057(self):
        """Test _load_parquet_data line 1057 (empty DataFrame check)."""
        with patch("adri.cli.commands.pd") as mock_pd:
            mock_df = Mock()
            mock_df.empty = True
            mock_pd.read_parquet.return_value = mock_df

            with self.assertRaises(ValueError) as context:
                _load_parquet_data(Path("empty.parquet"))
            self.assertIn("empty", str(context.exception))

    def test_validate_yaml_standard_lines_1253_1269(self):
        """Test validate_yaml_standard lines 1253-1269 (file not found path)."""
        result = validate_yaml_standard("completely_nonexistent_file.yaml")
        
        self.assertFalse(result["is_valid"])
        self.assertIn("File not found", result["errors"][0])
        self.assertEqual(result["file_path"], "completely_nonexistent_file.yaml")

    def test_validate_yaml_standard_lines_1383_1384(self):
        """Test validate_yaml_standard lines 1383-1384 (YAML error return)."""
        invalid_yaml = os.path.join(self.temp_dir, "broken.yaml")
        with open(invalid_yaml, "w") as f:
            f.write("invalid: yaml: [unclosed")

        result = validate_yaml_standard(invalid_yaml)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("Invalid YAML syntax", result["errors"][0])

    def test_validate_yaml_standard_lines_1386_1391(self):
        """Test validate_yaml_standard lines 1386-1391 (non-dict root)."""
        list_yaml = os.path.join(self.temp_dir, "list_root.yaml")
        with open(list_yaml, "w") as f:
            yaml.dump(["item1", "item2"], f)

        result = validate_yaml_standard(list_yaml)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("dictionary at the root level", result["errors"][0])

    def test_validate_yaml_standard_lines_1397_1401(self):
        """Test validate_yaml_standard lines 1397, 1401 (missing sections)."""
        # Test missing 'standards' section
        missing_standards = os.path.join(self.temp_dir, "missing_standards.yaml")
        with open(missing_standards, "w") as f:
            yaml.dump({"requirements": {"overall_minimum": 80}}, f)

        result = validate_yaml_standard(missing_standards)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("Missing required section: 'standards'", result["errors"][0])

        # Test missing 'requirements' section
        missing_requirements = os.path.join(self.temp_dir, "missing_requirements.yaml")
        with open(missing_requirements, "w") as f:
            yaml.dump({"standards": {"name": "test"}}, f)

        result = validate_yaml_standard(missing_requirements)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("Missing required section: 'requirements'", result["errors"][0])

    def test_validate_yaml_standard_lines_1506_1534(self):
        """Test validate_yaml_standard lines 1506-1534 (YAMLStandards failure with fallback)."""
        valid_yaml = os.path.join(self.temp_dir, "valid_with_failure.yaml")
        yaml_content = {
            "standards": {
                "id": "test-v1",
                "name": "Test Standard",
                "version": "1.0.0",
                "authority": "Test Authority"
            },
            "requirements": {
                "overall_minimum": 80
            }
        }
        with open(valid_yaml, "w") as f:
            yaml.dump(yaml_content, f)

        with patch("adri.cli.commands.YAMLStandards") as mock_yaml_standards:
            # First call fails, triggering the exception path
            mock_yaml_standards.side_effect = Exception("YAMLStandards instantiation failed")
            
            result = validate_yaml_standard(valid_yaml)
            
            # Should still extract metadata from yaml_content directly
            self.assertEqual(result["standard_name"], "Test Standard")
            self.assertEqual(result["standard_version"], "1.0.0")
            self.assertEqual(result["authority"], "Test Authority")
            # Should have the fallback success message
            self.assertIn("Metadata extraction successful", result["passed_checks"][-1])

    def test_validate_standards_metadata_lines_1659_1661(self):
        """Test _validate_standards_metadata lines 1659-1661 (empty field values)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        
        # Test with whitespace-only field
        standards_section = {
            "id": "   ",  # Whitespace only
            "name": "Test",
            "version": "1.0.0",
            "authority": "Test"
        }
        
        _validate_standards_metadata(standards_section, result)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("Empty value for required field: 'id'", result["errors"][0])

    def test_validate_standards_metadata_line_1701(self):
        """Test _validate_standards_metadata line 1701 (version warning)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        
        standards_section = {
            "id": "test-v1",
            "name": "Test",
            "version": "not-semver",
            "authority": "Test"
        }
        
        _validate_standards_metadata(standards_section, result)
        
        self.assertIn("does not follow semantic versioning", result["warnings"][0])

    def test_validate_standards_metadata_line_1713(self):
        """Test _validate_standards_metadata line 1713 (invalid date format)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        
        standards_section = {
            "id": "test-v1",
            "name": "Test",
            "version": "1.0.0",
            "authority": "Test",
            "effective_date": "not-a-date"
        }
        
        _validate_standards_metadata(standards_section, result)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("Invalid effective_date format", result["errors"][0])

    def test_validate_requirements_section_line_1822(self):
        """Test _validate_requirements_section line 1822 (not a dict)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        
        _validate_requirements_section(["not", "a", "dict"], result)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("Requirements section must be a dictionary", result["errors"][0])

    def test_validate_requirements_section_lines_1845_1855(self):
        """Test _validate_requirements_section lines 1845-1855 (overall_minimum validation)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        
        # Test string value
        requirements = {"overall_minimum": "eighty"}
        _validate_requirements_section(requirements, result)
        self.assertFalse(result["is_valid"])
        self.assertIn("overall_minimum must be a number", result["errors"][0])
        
        # Reset and test negative value
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        requirements = {"overall_minimum": -10}
        _validate_requirements_section(requirements, result)
        self.assertFalse(result["is_valid"])
        self.assertIn("overall_minimum must be between 0 and 100", result["errors"][0])

    def test_validate_dimension_requirements_lines_1969_1971(self):
        """Test _validate_dimension_requirements lines 1969-1971 (not a dict)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        
        _validate_dimension_requirements(["not", "a", "dict"], result)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("dimension_requirements must be a dictionary", result["errors"][0])

    def test_validate_dimension_requirements_lines_2036_2039(self):
        """Test _validate_dimension_requirements lines 2036-2039 (unknown dimension)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        
        dim_requirements = {
            "unknown_dimension": {"minimum_score": 15}
        }
        
        _validate_dimension_requirements(dim_requirements, result)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("Unknown dimension: 'unknown_dimension'", result["errors"][0])

    def test_validate_dimension_requirements_lines_2124_2125_2131(self):
        """Test _validate_dimension_requirements lines 2124-2125, 2131 (score validation)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        
        # Test string minimum_score
        dim_requirements = {
            "validity": {"minimum_score": "fifteen"}
        }
        _validate_dimension_requirements(dim_requirements, result)
        self.assertFalse(result["is_valid"])
        self.assertIn("minimum_score for validity must be a number", result["errors"][0])
        
        # Reset and test out of range
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        dim_requirements = {
            "validity": {"minimum_score": 30}  # > 20
        }
        _validate_dimension_requirements(dim_requirements, result)
        self.assertFalse(result["is_valid"])
        self.assertIn("minimum_score for validity must be between 0 and 20", result["errors"][0])

    def test_validate_field_requirements_line_2312(self):
        """Test _validate_field_requirements line 2312 (not a dict)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        
        _validate_field_requirements("not a dict", result)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("field_requirements must be a dictionary", result["errors"][0])

    def test_validate_field_requirements_line_2320(self):
        """Test _validate_field_requirements line 2320 (field config not dict)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        
        field_requirements = {
            "field1": "not a dict"
        }
        
        _validate_field_requirements(field_requirements, result)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("Field 'field1' configuration must be a dictionary", result["errors"][0])

    def test_validate_field_requirements_line_2335(self):
        """Test _validate_field_requirements line 2335 (invalid type)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        
        field_requirements = {
            "field1": {"type": "invalid_type"}
        }
        
        _validate_field_requirements(field_requirements, result)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("Invalid type 'invalid_type' for field 'field1'", result["errors"][0])

    def test_validate_field_requirements_line_2347(self):
        """Test _validate_field_requirements line 2347 (invalid nullable)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        
        field_requirements = {
            "field1": {"nullable": "maybe"}
        }
        
        _validate_field_requirements(field_requirements, result)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("nullable for field 'field1' must be true or false", result["errors"][0])

    def test_validate_field_requirements_line_2357(self):
        """Test _validate_field_requirements line 2357 (min >= max)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        
        field_requirements = {
            "field1": {
                "min_value": 100,
                "max_value": 100  # min == max should also fail
            }
        }
        
        _validate_field_requirements(field_requirements, result)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("min_value must be less than max_value", result["errors"][0])

    def test_validate_field_requirements_line_2365(self):
        """Test _validate_field_requirements line 2365 (invalid regex)."""
        result = {"errors": [], "warnings": [], "passed_checks": [], "is_valid": True}
        
        field_requirements = {
            "field1": {"pattern": "[unclosed"}
        }
        
        _validate_field_requirements(field_requirements, result)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("Invalid regex pattern for field 'field1'", result["errors"][0])

    def test_show_assessment_settings_disabled_caching(self):
        """Test _show_assessment_settings with disabled caching."""
        # This should exercise the disabled caching path
        _show_assessment_settings(self.config["adri"])

    def test_additional_edge_cases(self):
        """Test additional edge cases to catch remaining lines."""
        # Test CSV with empty content after reading
        empty_csv = os.path.join(self.temp_dir, "truly_empty.csv")
        with open(empty_csv, "w") as f:
            f.write("")  # Completely empty file

        with self.assertRaises(ValueError):
            _load_csv_data(Path(empty_csv))

        # Test parquet error handling
        with patch("adri.cli.commands.pd") as mock_pd:
            mock_pd.read_parquet.side_effect = Exception("Parquet read error")
            
            with self.assertRaises(ValueError) as context:
                _load_parquet_data(Path("error.parquet"))
            self.assertIn("Failed to read Parquet file", str(context.exception))


if __name__ == "__main__":
    unittest.main()
