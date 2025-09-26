"""
Edge case tests for ADRI Protection Modes to achieve 85%+ coverage.

Targets specific missing lines identified in coverage analysis:
- Import fallback logic (lines 23-34)
- Configuration loading exceptions (lines 204-205)
- Protection mode overrides (lines 264-269)
- Parameter extraction edge cases (lines 331-332)
- Standard generation edge cases (lines 372, 376-382, 389-390, 401, 442)
- Assessment data conversion (lines 446-452)
- Dimension requirements edge cases (line 463)
"""

import unittest
import pandas as pd
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Test the actual imports
from src.adri.guard.modes import (
    DataProtectionEngine,
    FailFastMode,
    SelectiveMode,
    WarnOnlyMode,
    ProtectionError,
    fail_fast_mode,
    selective_mode,
    warn_only_mode
)


class TestProtectionModesEdgeCases(unittest.TestCase):
    """Test edge cases and error paths to achieve complete coverage."""

    def setUp(self):
        """Set up test environment."""
        self.test_data = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
            "value": [10.5, 20.3, 30.1]
        })

    def test_import_fallback_scenarios(self):
        """Test import fallback logic (lines 23-34)."""
        # This is tricky to test directly since imports happen at module load
        # But we can verify the fallback values are set correctly
        from adri.guard.modes import ValidationEngine, ConfigurationLoader, LocalLogger, EnterpriseLogger

        # These should be loaded successfully in our test environment
        self.assertIsNotNone(ValidationEngine)
        self.assertIsNotNone(ConfigurationLoader)
        self.assertIsNotNone(LocalLogger)
        self.assertIsNotNone(EnterpriseLogger)

    @patch('adri.guard.modes.ConfigurationLoader')
    def test_config_loading_exception_handling(self, mock_config_class):
        """Test configuration loading exception handling (lines 204-205)."""
        # Setup mock to raise exception during get_protection_config
        mock_config_instance = Mock()
        mock_config_instance.get_protection_config.side_effect = Exception("Config error")
        mock_config_class.return_value = mock_config_instance

        # Should fall back to default config when exception occurs
        engine = DataProtectionEngine()

        # Verify default config is used
        self.assertEqual(engine.protection_config["default_min_score"], 80)
        self.assertTrue(engine.protection_config["auto_generate_standards"])

    @patch('adri.guard.modes.ConfigurationLoader')
    @patch('adri.guard.modes.LocalLogger')
    @patch('adri.guard.modes.EnterpriseLogger')
    @patch('adri.guard.modes.ValidationEngine')
    @patch('os.path.exists')
    def test_on_failure_parameter_overrides(self, mock_exists, mock_engine_class, mock_enterprise, mock_local, mock_config):
        """Test on_failure parameter override logic (lines 264-269)."""
        mock_config.return_value = None
        mock_local.return_value = None
        mock_enterprise.return_value = None
        mock_exists.return_value = True

        # Setup mock assessment
        mock_engine = Mock()
        mock_result = Mock()
        mock_result.overall_score = 90.0
        mock_engine.assess.return_value = mock_result
        mock_engine_class.return_value = mock_engine

        engine = DataProtectionEngine(SelectiveMode())  # Default mode

        def test_function(data):
            return {"result": "success"}

        # Test each on_failure override
        with patch('builtins.print'):  # Suppress output
            for on_failure_value in ["raise", "warn", "continue"]:
                result = engine.protect_function_call(
                    func=test_function,
                    args=(self.test_data,),
                    kwargs={},
                    data_param="data",
                    function_name="test_function",
                    on_failure=on_failure_value,
                    verbose=True  # Also test verbose logging path
                )
                self.assertEqual(result["result"], "success")

    @patch('adri.guard.modes.ConfigurationLoader')
    @patch('adri.guard.modes.LocalLogger')
    @patch('adri.guard.modes.EnterpriseLogger')
    def test_data_parameter_extraction_edge_cases(self, mock_enterprise, mock_local, mock_config):
        """Test data parameter extraction edge cases (lines 331-332)."""
        mock_config.return_value = None
        mock_local.return_value = None
        mock_enterprise.return_value = None

        engine = DataProtectionEngine()

        # Test function with no signature inspection capability
        def unparseable_function(*args, **kwargs):
            return "result"

        # Mock inspect.signature to raise exception
        with patch('inspect.signature', side_effect=Exception("Signature error")):
            # Should still work if parameter is in kwargs
            data = engine._extract_data_parameter(
                unparseable_function, (), {"data": self.test_data}, "data"
            )
            pd.testing.assert_frame_equal(data, self.test_data)

            # Should raise ValueError if parameter not found
            with self.assertRaises(ValueError) as context:
                engine._extract_data_parameter(
                    unparseable_function, ("arg1",), {}, "missing_param"
                )

            self.assertIn("Could not find data parameter 'missing_param'", str(context.exception))

    @patch('adri.guard.modes.ConfigurationLoader')
    @patch('adri.guard.modes.LocalLogger')
    @patch('adri.guard.modes.EnterpriseLogger')
    def test_standard_generation_edge_cases(self, mock_enterprise, mock_local, mock_config):
        """Test standard generation edge cases (lines 372, 376-382, 389-390, 401, 442)."""
        mock_config.return_value = None
        mock_local.return_value = None
        mock_enterprise.return_value = None

        engine = DataProtectionEngine()

        # Test with auto_generate_standards disabled (line 372)
        engine.protection_config["auto_generate_standards"] = False

        with tempfile.TemporaryDirectory() as temp_dir:
            standard_path = os.path.join(temp_dir, "nonexistent_standard.yaml")

            with self.assertRaises(ProtectionError) as context:
                engine._ensure_standard_exists(standard_path, self.test_data)

            self.assertIn("Standard file not found", str(context.exception))

        # Re-enable auto generation for further tests
        engine.protection_config["auto_generate_standards"] = True

        # Test with different data types (lines 376-382)
        test_cases = [
            # List data
            [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}],
            # Dict data (single record)
            {"id": 1, "name": "A", "value": 10.5},
            # Invalid data type
            "invalid_data_type"
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for i, test_data in enumerate(test_cases):
                standard_path = os.path.join(temp_dir, f"test_standard_{i}.yaml")

                if i == len(test_cases) - 1:  # Last case is invalid
                    with self.assertRaises(ProtectionError) as context:
                        engine._ensure_standard_exists(standard_path, test_data)
                    self.assertIn("Cannot generate standard from data type", str(context.exception))
                else:
                    # Should generate successfully
                    engine._ensure_standard_exists(standard_path, test_data)
                    self.assertTrue(os.path.exists(standard_path))

    @patch('adri.guard.modes.ConfigurationLoader')
    @patch('adri.guard.modes.LocalLogger')
    @patch('adri.guard.modes.EnterpriseLogger')
    def test_field_type_detection_edge_cases(self, mock_enterprise, mock_local, mock_config):
        """Test field type detection in standard generation (line 401)."""
        mock_config.return_value = None
        mock_local.return_value = None
        mock_enterprise.return_value = None

        engine = DataProtectionEngine()

        # Create DataFrame with all null column to test edge case
        # Use Python native types to avoid numpy serialization issues
        df_with_nulls = pd.DataFrame({
            "all_null_column": [None, None, None],
            "int_column": [int(1), int(2), int(3)],
            "float_column": [float(1.5), float(2.5), float(3.5)],
            "string_column": ["a", "b", "c"]
        })

        with tempfile.TemporaryDirectory() as temp_dir:
            standard_path = os.path.join(temp_dir, "null_test_standard.yaml")
            engine._generate_basic_standard(df_with_nulls, standard_path)

            # Verify standard was created successfully
            self.assertTrue(os.path.exists(standard_path))

            # Verify the file has content (non-empty YAML was generated)
            with open(standard_path, 'r') as f:
                content = f.read()
                self.assertGreater(len(content), 100)  # Should contain substantial YAML content
                self.assertIn("all_null_column", content)  # Should include our test column
                self.assertIn("requirements", content)  # Should have requirements section

    @patch('adri.guard.modes.ConfigurationLoader')
    @patch('adri.guard.modes.LocalLogger')
    @patch('adri.guard.modes.EnterpriseLogger')
    def test_assessment_data_conversion_edge_cases(self, mock_enterprise, mock_local, mock_config):
        """Test assessment data conversion edge cases (lines 446-452)."""
        mock_config.return_value = None
        mock_local.return_value = None
        mock_enterprise.return_value = None

        engine = DataProtectionEngine()

        # Test with ValidationEngine not available
        with patch('adri.guard.modes.ValidationEngine', None):
            with self.assertRaises(ProtectionError) as context:
                engine._assess_data_quality(self.test_data, "test_standard.yaml")

            self.assertIn("Validation engine not available", str(context.exception))

        # Test with different data types
        test_cases = [
            # List data
            [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}],
            # Dict data (single record)
            {"id": 1, "name": "A", "value": 10.5},
            # Invalid data type
            42  # Number that can't be converted
        ]

        with patch('adri.guard.modes.ValidationEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_result = Mock()
            mock_result.overall_score = 85.0
            mock_engine.assess.return_value = mock_result
            mock_engine_class.return_value = mock_engine

            for i, test_data in enumerate(test_cases):
                if i == len(test_cases) - 1:  # Last case is invalid
                    with self.assertRaises(ProtectionError) as context:
                        engine._assess_data_quality(test_data, "test_standard.yaml")
                    self.assertIn("Cannot assess data type", str(context.exception))
                else:
                    # Should assess successfully
                    result = engine._assess_data_quality(test_data, "test_standard.yaml")
                    self.assertEqual(result.overall_score, 85.0)

    @patch('adri.guard.modes.ConfigurationLoader')
    @patch('adri.guard.modes.LocalLogger')
    @patch('adri.guard.modes.EnterpriseLogger')
    def test_dimension_requirements_edge_cases(self, mock_enterprise, mock_local, mock_config):
        """Test dimension requirements edge cases (line 463)."""
        mock_config.return_value = None
        mock_local.return_value = None
        mock_enterprise.return_value = None

        engine = DataProtectionEngine()

        # Test with assessment result that has no dimension_scores attribute
        mock_result_no_dims = Mock()
        del mock_result_no_dims.dimension_scores  # Ensure attribute doesn't exist

        # Should return True when no dimension_scores attribute
        result = engine._check_dimension_requirements(
            mock_result_no_dims,
            {"validity": 15.0, "completeness": 16.0}
        )
        self.assertTrue(result)

        # Test with dimension score object that has no score attribute
        mock_result_no_score = Mock()
        mock_dim_obj = Mock()
        del mock_dim_obj.score  # Ensure score attribute doesn't exist
        mock_result_no_score.dimension_scores = {"validity": mock_dim_obj}

        # Should handle missing score attribute gracefully (default to 0)
        result = engine._check_dimension_requirements(
            mock_result_no_score,
            {"validity": 15.0}  # Requirement higher than default 0
        )
        self.assertFalse(result)  # Should fail since 0 < 15.0

    def test_protection_mode_base_class_coverage(self):
        """Test base ProtectionMode class coverage (line 89)."""
        # Test the base get_description method
        mode = FailFastMode()
        base_description = super(FailFastMode, mode).get_description()
        self.assertEqual(base_description, "fail-fast protection mode")

        # Test with custom config
        custom_config = {"test_setting": "value"}
        mode_with_config = SelectiveMode(custom_config)
        self.assertEqual(mode_with_config.config["test_setting"], "value")

    @patch('adri.guard.modes.ConfigurationLoader')
    @patch('adri.guard.modes.LocalLogger')
    @patch('adri.guard.modes.EnterpriseLogger')
    def test_directory_creation_edge_case(self, mock_enterprise, mock_local, mock_config):
        """Test directory creation with empty path (edge case)."""
        mock_config.return_value = None
        mock_local.return_value = None
        mock_enterprise.return_value = None

        engine = DataProtectionEngine()

        # Test with standard path that has no directory component
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()  # Save original directory
            try:
                os.chdir(temp_dir)  # Change to temp directory

                standard_path = "no_directory_standard.yaml"  # No directory component

                # Should handle this case without trying to create empty directory
                engine._ensure_standard_exists(standard_path, self.test_data)
                self.assertTrue(os.path.exists(standard_path))
            finally:
                # Always change back to original directory before cleanup
                os.chdir(original_cwd)

    @patch('adri.guard.modes.ConfigurationLoader')
    @patch('adri.guard.modes.LocalLogger')
    @patch('adri.guard.modes.EnterpriseLogger')
    def test_standard_generation_failure_handling(self, mock_enterprise, mock_local, mock_config):
        """Test standard generation failure handling."""
        mock_config.return_value = None
        mock_local.return_value = None
        mock_enterprise.return_value = None

        engine = DataProtectionEngine()

        # Test failure during standard generation
        with patch('builtins.open', side_effect=PermissionError("Cannot write file")):
            with self.assertRaises(ProtectionError) as context:
                engine._ensure_standard_exists("test_standard.yaml", self.test_data)

            self.assertIn("Failed to generate standard", str(context.exception))


if __name__ == '__main__':
    unittest.main()
