"""
Tests for @adri_protected decorator.

Following TDD approach - comprehensive test coverage for the data protection decorator.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, MagicMock, patch

import pandas as pd

from adri.core.protection import DataProtectionEngine, ProtectionError
from adri.decorators.guard import adri_protected


class TestAdriProtectedDecorator(unittest.TestCase):
    """Test the @adri_protected decorator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.standards_dir = os.path.join(self.temp_dir, "standards")
        self.assessments_dir = os.path.join(self.temp_dir, "assessments")
        os.makedirs(self.standards_dir)
        os.makedirs(self.assessments_dir)

        # Mock config
        self.mock_config = {
            "adri": {
                "project_name": "test-project",
                "version": "2.0.0",
                "default_environment": "development",
                "protection": {
                    "default_failure_mode": "raise",
                    "default_min_score": 80,
                    "cache_duration_hours": 1,
                    "auto_generate_standards": True,
                    "data_sampling_limit": 1000,
                    "standard_naming_pattern": "{function_name}_{data_param}_standard.yaml",
                    "verbose_protection": False,
                },
                "environments": {
                    "development": {
                        "paths": {
                            "standards": self.standards_dir,
                            "assessments": self.assessments_dir,
                        }
                    }
                },
            }
        }

        # Sample data for testing
        self.sample_data = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "name": ["Alice", "Bob", "Charlie"],
                "email": ["alice@test.com", "bob@test.com", "charlie@test.com"],
                "age": [25, 30, 35],
            }
        )

        # Sample assessment result
        self.good_assessment = {
            "overall_score": 85.0,
            "passed": True,
            "dimension_scores": {
                "validity": {"score": 18.0},
                "completeness": {"score": 17.0},
                "consistency": {"score": 16.5},
                "freshness": {"score": 19.0},
                "plausibility": {"score": 14.5},
            },
        }

        self.bad_assessment = {
            "overall_score": 65.0,
            "passed": False,
            "dimension_scores": {
                "validity": {"score": 15.0},
                "completeness": {"score": 10.0},
                "consistency": {"score": 12.0},
                "freshness": {"score": 14.0},
                "plausibility": {"score": 14.0},
            },
        }

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("adri.decorators.guard.ConfigManager")
    @patch("adri.decorators.guard.DataProtectionEngine")
    def test_basic_decorator_usage(self, mock_engine_class, mock_config_manager):
        """Test basic decorator usage with default parameters."""
        # Setup mocks
        mock_manager = MagicMock()
        mock_manager.get_protection_config.return_value = self.mock_config["adri"][
            "protection"
        ]
        mock_config_manager.return_value = mock_manager

        mock_engine = MagicMock()
        mock_engine.protect_function_call.return_value = "processed_result"
        mock_engine_class.return_value = mock_engine

        # Define test function
        @adri_protected(data_param="data")
        def test_function(data):
            return "processed_result"

        # Call function
        result = test_function(self.sample_data)

        # Verify results
        self.assertEqual(result, "processed_result")
        mock_engine.protect_function_call.assert_called_once()

        # Verify call arguments
        call_args = mock_engine.protect_function_call.call_args
        self.assertEqual(call_args[1]["data_param"], "data")
        self.assertEqual(call_args[1]["function_name"], "test_function")

    @patch("adri.decorators.guard.ConfigManager")
    @patch("adri.decorators.guard.DataProtectionEngine")
    def test_decorator_with_explicit_standard_file(
        self, mock_engine_class, mock_config_manager
    ):
        """Test decorator with explicit standard file specification."""
        # Setup mocks
        mock_manager = MagicMock()
        mock_manager.get_protection_config.return_value = self.mock_config["adri"][
            "protection"
        ]
        mock_config_manager.return_value = mock_manager

        mock_engine = MagicMock()
        mock_engine.protect_function_call.return_value = "processed_result"
        mock_engine_class.return_value = mock_engine

        # Define test function with explicit standard
        @adri_protected(
            data_param="customer_data", standard_file="custom_standard.yaml"
        )
        def process_customers(customer_data):
            return "processed_result"

        # Call function
        result = process_customers(self.sample_data)

        # Verify results
        self.assertEqual(result, "processed_result")

        # Verify standard file was passed correctly
        call_args = mock_engine.protect_function_call.call_args
        self.assertEqual(call_args[1]["standard_file"], "custom_standard.yaml")

    @patch("adri.decorators.guard.ConfigManager")
    @patch("adri.decorators.guard.DataProtectionEngine")
    def test_decorator_with_custom_parameters(
        self, mock_engine_class, mock_config_manager
    ):
        """Test decorator with custom parameters overriding config defaults."""
        # Setup mocks
        mock_manager = MagicMock()
        mock_manager.get_protection_config.return_value = self.mock_config["adri"][
            "protection"
        ]
        mock_config_manager.return_value = mock_manager

        mock_engine = MagicMock()
        mock_engine.protect_function_call.return_value = "processed_result"
        mock_engine_class.return_value = mock_engine

        # Define test function with custom parameters
        @adri_protected(
            data_param="financial_data",
            min_score=90,
            on_failure="warn",
            dimensions={"validity": 19, "completeness": 18},
        )
        def process_financial_data(financial_data):
            return "processed_result"

        # Call function
        result = process_financial_data(self.sample_data)

        # Verify results
        self.assertEqual(result, "processed_result")

        # Verify custom parameters were passed
        call_args = mock_engine.protect_function_call.call_args
        self.assertEqual(call_args[1]["min_score"], 90)
        self.assertEqual(call_args[1]["on_failure"], "warn")
        self.assertEqual(
            call_args[1]["dimensions"], {"validity": 19, "completeness": 18}
        )

    @patch("adri.decorators.guard.ConfigManager")
    @patch("adri.decorators.guard.DataProtectionEngine")
    def test_decorator_quality_failure_raises_exception(
        self, mock_engine_class, mock_config_manager
    ):
        """Test decorator raises exception when data quality fails."""
        # Setup mocks
        mock_manager = MagicMock()
        mock_manager.get_protection_config.return_value = self.mock_config["adri"][
            "protection"
        ]
        mock_config_manager.return_value = mock_manager

        mock_engine = MagicMock()
        mock_engine.protect_function_call.side_effect = ProtectionError(
            "Data quality insufficient"
        )
        mock_engine_class.return_value = mock_engine

        # Define test function
        @adri_protected(data_param="data")
        def test_function(data):
            return "should_not_reach_here"

        # Verify exception is raised
        with self.assertRaises(ProtectionError) as context:
            test_function(self.sample_data)

        self.assertIn("Data quality insufficient", str(context.exception))

    @patch("adri.decorators.guard.ConfigManager")
    @patch("adri.decorators.guard.DataProtectionEngine")
    def test_decorator_missing_data_parameter(
        self, mock_engine_class, mock_config_manager
    ):
        """Test decorator handles missing data parameter gracefully."""
        # Setup mocks
        mock_manager = MagicMock()
        mock_manager.get_protection_config.return_value = self.mock_config["adri"][
            "protection"
        ]
        mock_config_manager.return_value = mock_manager

        mock_engine = MagicMock()
        mock_engine.protect_function_call.side_effect = ValueError(
            "Could not find data parameter 'missing_param'"
        )
        mock_engine_class.return_value = mock_engine

        # Define test function
        @adri_protected(data_param="missing_param")
        def test_function(data):
            return "result"

        # Verify exception is raised for missing parameter
        with self.assertRaises(ProtectionError) as context:
            test_function(self.sample_data)

        self.assertIn("missing_param", str(context.exception))

    def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves original function metadata."""

        @adri_protected(data_param="data")
        def test_function(data):
            """Test function docstring."""
            return "result"

        # Verify function metadata is preserved
        self.assertEqual(test_function.__name__, "test_function")
        self.assertEqual(test_function.__doc__, "Test function docstring.")


class TestDataProtectionEngine(unittest.TestCase):
    """Test the DataProtectionEngine core functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.standards_dir = os.path.join(self.temp_dir, "standards")
        self.assessments_dir = os.path.join(self.temp_dir, "assessments")
        os.makedirs(self.standards_dir)
        os.makedirs(self.assessments_dir)

        # Mock config
        self.mock_config = {
            "adri": {
                "protection": {
                    "default_failure_mode": "raise",
                    "default_min_score": 80,
                    "cache_duration_hours": 1,
                    "auto_generate_standards": True,
                    "data_sampling_limit": 1000,
                    "standard_naming_pattern": "{function_name}_{data_param}_standard.yaml",
                    "verbose_protection": False,
                },
                "environments": {
                    "development": {
                        "paths": {
                            "standards": self.standards_dir,
                            "assessments": self.assessments_dir,
                        }
                    }
                },
            }
        }

        self.sample_data = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "name": ["Alice", "Bob", "Charlie"],
                "email": ["alice@test.com", "bob@test.com", "charlie@test.com"],
            }
        )

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("adri.core.protection.ConfigManager")
    def test_engine_initialization(self, mock_config_manager):
        """Test DataProtectionEngine initialization."""
        mock_manager = MagicMock()
        mock_manager.get_protection_config.return_value = self.mock_config["adri"][
            "protection"
        ]
        mock_config_manager.return_value = mock_manager

        engine = DataProtectionEngine()

        self.assertIsNotNone(engine.config_manager)
        self.assertEqual(engine.protection_config["default_min_score"], 80)

    @patch("adri.core.protection.ConfigManager")
    @patch("adri.core.protection.StandardsLoader")
    def test_resolve_standard_with_explicit_file(
        self, mock_loader_class, mock_config_manager
    ):
        """Test standard resolution with explicit file."""
        mock_manager = MagicMock()
        mock_manager.get_protection_config.return_value = self.mock_config["adri"][
            "protection"
        ]
        mock_manager.resolve_standard_path_simple.return_value = (
            "/path/to/custom_standard.yaml"
        )
        mock_config_manager.return_value = mock_manager

        # Mock standards loader to return None (no bundled standard found)
        mock_loader = MagicMock()
        mock_loader.standard_exists.return_value = False
        mock_loader_class.return_value = mock_loader

        engine = DataProtectionEngine()

        result = engine.resolve_standard(
            function_name="test_func",
            data_param="data",
            standard_file="custom_standard.yaml",
            standard_name=None,
        )

        self.assertEqual(result, "/path/to/custom_standard.yaml")
        mock_manager.resolve_standard_path_simple.assert_called_once_with(
            "custom_standard.yaml"
        )

    @patch("adri.core.protection.ConfigManager")
    @patch("adri.core.protection.StandardsLoader")
    def test_resolve_standard_with_auto_generation(
        self, mock_loader_class, mock_config_manager
    ):
        """Test standard resolution with auto-generated name."""
        mock_manager = MagicMock()
        mock_manager.get_protection_config.return_value = self.mock_config["adri"][
            "protection"
        ]
        mock_manager.resolve_standard_path_simple.return_value = (
            "/path/to/test_func_data_standard.yaml"
        )
        mock_config_manager.return_value = mock_manager

        # Mock standards loader to return None (no bundled standard found)
        mock_loader = MagicMock()
        mock_loader.standard_exists.return_value = False
        mock_loader_class.return_value = mock_loader

        engine = DataProtectionEngine()

        result = engine.resolve_standard(
            function_name="test_func",
            data_param="data",
            standard_file=None,
            standard_name=None,
        )

        self.assertEqual(result, "/path/to/test_func_data_standard.yaml")
        mock_manager.resolve_standard_path_simple.assert_called_once_with(
            "test_func_data_standard.yaml"
        )

    @patch("adri.core.protection.ConfigManager")
    @patch("adri.core.protection.StandardGenerator")
    @patch("adri.analysis.data_profiler.DataProfiler")
    def test_ensure_standard_exists_generates_when_missing(
        self, mock_profiler_class, mock_generator_class, mock_config_manager
    ):
        """Test standard generation when file doesn't exist."""
        mock_manager = MagicMock()
        mock_manager.get_protection_config.return_value = self.mock_config["adri"][
            "protection"
        ]
        mock_config_manager.return_value = mock_manager

        # Mock the data profiler
        mock_profiler = MagicMock()
        mock_profile = {"field_analysis": {"overall": {"field_count": 3}}}
        mock_profiler.profile_data.return_value = mock_profile
        mock_profiler_class.return_value = mock_profiler

        # Mock the standard generator
        mock_generator = MagicMock()
        mock_standard_dict = {"standards": {"id": "test"}, "requirements": {}}
        mock_generator.generate_standard.return_value = mock_standard_dict
        mock_generator_class.return_value = mock_generator

        engine = DataProtectionEngine()

        standard_path = os.path.join(self.standards_dir, "test_standard.yaml")

        # File doesn't exist, should generate
        engine.ensure_standard_exists(standard_path, self.sample_data)

        # Verify the correct methods were called
        mock_profiler.profile_data.assert_called_once()
        mock_generator.generate_standard.assert_called_once()

    @patch("adri.core.protection.ConfigManager")
    def test_ensure_standard_exists_skips_when_exists(self, mock_config_manager):
        """Test standard generation is skipped when file exists."""
        mock_manager = MagicMock()
        mock_manager.get_protection_config.return_value = self.mock_config["adri"][
            "protection"
        ]
        mock_config_manager.return_value = mock_manager

        engine = DataProtectionEngine()

        # Create existing standard file
        standard_path = os.path.join(self.standards_dir, "existing_standard.yaml")
        with open(standard_path, "w") as f:
            f.write("standards:\n  id: test\n")

        # Should not generate when file exists
        result = engine.ensure_standard_exists(standard_path, self.sample_data)

        self.assertTrue(result)  # Should return True for existing file

    @patch("adri.core.protection.ConfigManager")
    @patch("adri.core.protection.AssessmentEngine")
    def test_assess_data_quality_success(
        self, mock_assessor_class, mock_config_manager
    ):
        """Test successful data quality assessment."""
        mock_manager = MagicMock()
        mock_manager.get_protection_config.return_value = self.mock_config["adri"][
            "protection"
        ]
        mock_config_manager.return_value = mock_manager

        mock_assessor = MagicMock()
        mock_assessment_result = MagicMock()
        mock_assessment_result.overall_score = 85.0
        mock_assessment_result.passed = True
        mock_assessor.assess.return_value = mock_assessment_result
        mock_assessor_class.return_value = mock_assessor

        engine = DataProtectionEngine()

        # Create standard file
        standard_path = os.path.join(self.standards_dir, "test_standard.yaml")
        with open(standard_path, "w") as f:
            f.write("standards:\n  id: test\n")

        result = engine.assess_data_quality(self.sample_data, standard_path)

        self.assertEqual(result.overall_score, 85.0)
        self.assertTrue(result.passed)

    @patch("adri.core.protection.ConfigManager")
    def test_handle_quality_failure_raise_mode(self, mock_config_manager):
        """Test quality failure handling in raise mode."""
        mock_manager = MagicMock()
        mock_manager.get_protection_config.return_value = self.mock_config["adri"][
            "protection"
        ]
        mock_config_manager.return_value = mock_manager

        engine = DataProtectionEngine()

        mock_assessment = MagicMock()
        mock_assessment.overall_score = 65.0
        mock_assessment.passed = False

        with self.assertRaises(ProtectionError) as context:
            engine.handle_quality_failure(mock_assessment, "raise", 80)

        # Check for the new error message format
        error_message = str(context.exception)
        self.assertIn("🛡️ ADRI Protection: BLOCKED ❌", error_message)
        self.assertIn("65.0", error_message)
        self.assertIn("80.0", error_message)

    @patch("adri.core.protection.ConfigManager")
    @patch("adri.core.protection.logger")
    def test_handle_quality_failure_warn_mode(self, mock_logger, mock_config_manager):
        """Test quality failure handling in warn mode."""
        mock_manager = MagicMock()
        mock_manager.get_protection_config.return_value = self.mock_config["adri"][
            "protection"
        ]
        mock_config_manager.return_value = mock_manager

        engine = DataProtectionEngine()

        mock_assessment = MagicMock()
        mock_assessment.overall_score = 65.0
        mock_assessment.passed = False

        # Should not raise exception in warn mode
        engine.handle_quality_failure(mock_assessment, "warn", 80)

        # Should log warning
        mock_logger.warning.assert_called()

    @patch("adri.core.protection.ConfigManager")
    @patch("adri.core.protection.StandardsLoader")
    @patch("adri.core.protection.AssessmentEngine")
    def test_protect_function_call_full_workflow(
        self, mock_assessor_class, mock_loader_class, mock_config_manager
    ):
        """Test complete protection workflow."""
        # Setup mocks
        mock_manager = MagicMock()
        mock_manager.get_protection_config.return_value = self.mock_config["adri"][
            "protection"
        ]
        standard_path = os.path.join(self.standards_dir, "test_standard.yaml")
        mock_manager.resolve_standard_path_simple.return_value = standard_path
        mock_config_manager.return_value = mock_manager

        # Mock standards loader to return None (no bundled standard found)
        mock_loader = MagicMock()
        mock_loader.standard_exists.return_value = False
        mock_loader_class.return_value = mock_loader

        # Create a real standard file to avoid generation
        with open(standard_path, "w") as f:
            f.write(
                """
standards:
  id: "test-standard"
  name: "Test Standard"
  version: "1.0.0"
  authority: "Test Authority"

requirements:
  overall_minimum: 80.0
"""
            )

        mock_assessor = MagicMock()
        mock_assessment_result = MagicMock()
        # Make sure overall_score is a real number, not a MagicMock
        mock_assessment_result.overall_score = 85.0
        mock_assessment_result.passed = True
        mock_assessor.assess.return_value = mock_assessment_result
        mock_assessor_class.return_value = mock_assessor

        engine = DataProtectionEngine()

        # Define test function
        def test_function(data):
            return "success"

        # Call protection
        result = engine.protect_function_call(
            func=test_function,
            args=(self.sample_data,),
            kwargs={},
            data_param="data",
            function_name="test_function",
            standard_file=None,
            min_score=80,
            on_failure="raise",
        )

        self.assertEqual(result, "success")


if __name__ == "__main__":
    unittest.main()
