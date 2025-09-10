"""Tests specifically targeting missing coverage lines in core/protection.py.

Focuses on covering the uncovered lines identified in coverage analysis.
"""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest
import yaml

from adri.core.protection import DataProtectionEngine, ProtectionError
from adri.standards.exceptions import StandardNotFoundError


class TestDataProtectionEngineInit:
    """Test DataProtectionEngine initialization and configuration."""

    @patch("adri.core.protection.ConfigManager")
    @patch("adri.core.protection.StandardsLoader")
    def test_init_with_config_manager_setup(
        self, mock_standards_loader, mock_config_manager
    ):
        """Test initialization with proper config manager setup."""
        mock_config_instance = MagicMock()
        mock_config_manager.return_value = mock_config_instance
        mock_config_instance.get_protection_config.return_value = {
            "default_min_score": 85,
            "cache_duration_hours": 2,
        }

        mock_standards_instance = MagicMock()
        mock_standards_loader.return_value = mock_standards_instance

        engine = DataProtectionEngine()

        assert engine.config_manager == mock_config_instance
        assert engine.standards_loader == mock_standards_instance
        assert engine._assessment_cache == {}
        mock_config_instance.get_protection_config.assert_called_once()


class TestResolveStandardMissingCoverage:
    """Test resolve_standard method missing coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("adri.core.protection.ConfigManager"),
            patch("adri.core.protection.StandardsLoader"),
        ):
            self.engine = DataProtectionEngine()

    @patch("adri.core.protection.ConfigManager")
    @patch("adri.core.protection.StandardsLoader")
    def test_resolve_standard_with_custom_pattern(
        self, mock_standards_loader, mock_config_manager
    ):
        """Test resolve_standard with custom naming pattern."""
        mock_config_instance = MagicMock()
        mock_config_manager.return_value = mock_config_instance
        mock_config_instance.get_protection_config.return_value = {
            "standard_naming_pattern": "custom_{function_name}_{data_param}.yaml"
        }
        mock_config_instance.resolve_standard_path_simple.return_value = (
            "/test/custom_func_data.yaml"
        )

        mock_standards_instance = MagicMock()
        mock_standards_loader.return_value = mock_standards_instance
        mock_standards_instance.standard_exists.return_value = False

        engine = DataProtectionEngine()

        # Mock the _try_bundled_standard to return None (no bundled standard found)
        with patch.object(engine, "_try_bundled_standard", return_value=None):
            result = engine.resolve_standard("func", "data")

        expected_filename = "custom_func_data.yaml"
        mock_config_instance.resolve_standard_path_simple.assert_called_with(
            expected_filename
        )
        assert result == "/test/custom_func_data.yaml"

    def test_resolve_standard_with_standard_name(self):
        """Test resolve_standard with explicit standard_name parameter."""
        self.engine.config_manager.resolve_standard_path_simple.return_value = (
            "/test/custom_standard.yaml"
        )

        with patch.object(self.engine, "_try_bundled_standard", return_value=None):
            result = self.engine.resolve_standard(
                "func", "data", standard_name="custom_standard"
            )

        self.engine.config_manager.resolve_standard_path_simple.assert_called_with(
            "custom_standard.yaml"
        )
        assert result == "/test/custom_standard.yaml"


class TestTryBundledStandardMissingCoverage:
    """Test _try_bundled_standard method missing coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("adri.core.protection.ConfigManager"),
            patch("adri.core.protection.StandardsLoader"),
        ):
            self.engine = DataProtectionEngine()

    def test_try_bundled_standard_with_explicit_file_base_name_extraction(self):
        """Test bundled standard lookup with explicit file and base name extraction."""
        self.engine.standards_loader.standard_exists.return_value = True
        self.engine.standards_loader.load_standard.return_value = {"test": "standard"}

        # Test with _standard suffix removal
        result = self.engine._try_bundled_standard(
            "func", "data", standard_file="/path/to/test_data_standard.yaml"
        )

        # Should extract "test_data" from "test_data_standard.yaml"
        self.engine.standards_loader.standard_exists.assert_called_with("test_data")
        assert result == {"test": "standard"}

    def test_try_bundled_standard_with_custom_standard_name(self):
        """Test bundled standard lookup with custom standard name."""
        self.engine.standards_loader.standard_exists.return_value = True
        self.engine.standards_loader.load_standard.return_value = {"custom": "standard"}

        result = self.engine._try_bundled_standard(
            "func", "data", standard_name="custom_standard"
        )

        self.engine.standards_loader.standard_exists.assert_called_with(
            "custom_standard"
        )
        self.engine.standards_loader.load_standard.assert_called_with("custom_standard")
        assert result == {"custom": "standard"}

    def test_try_bundled_standard_pattern_matching_fallbacks(self):
        """Test bundled standard pattern matching with various fallbacks."""

        # Mock to return True only for the "customer_data_standard" pattern
        def mock_exists(name):
            return name == "customer_data_standard"

        self.engine.standards_loader.standard_exists.side_effect = mock_exists
        self.engine.standards_loader.load_standard.return_value = {
            "fallback": "standard"
        }

        result = self.engine._try_bundled_standard("process_user", "user_data")

        # Should try multiple patterns and find customer_data_standard
        expected_calls = [
            "process_user_user_data_standard",
            "user_data_standard",
            "process_user_standard",
            "customer_data_standard",
        ]

        actual_calls = [
            call[0][0]
            for call in self.engine.standards_loader.standard_exists.call_args_list
        ]
        for expected in expected_calls:
            assert expected in actual_calls

        assert result == {"fallback": "standard"}

    def test_try_bundled_standard_with_standard_not_found_error(self):
        """Test bundled standard with StandardNotFoundError exception."""
        self.engine.standards_loader.standard_exists.side_effect = (
            StandardNotFoundError("Not found")
        )

        result = self.engine._try_bundled_standard("func", "data")

        assert result is None

    def test_try_bundled_standard_with_generic_exception(self):
        """Test bundled standard with generic exception handling."""
        self.engine.standards_loader.standard_exists.side_effect = Exception(
            "Generic error"
        )

        result = self.engine._try_bundled_standard("func", "data")

        assert result is None


class TestEnsureStandardExistsMissingCoverage:
    """Test ensure_standard_exists method missing coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("adri.core.protection.ConfigManager"),
            patch("adri.core.protection.StandardsLoader"),
        ):
            self.engine = DataProtectionEngine()

    def test_ensure_standard_exists_bundled_standard(self):
        """Test ensure_standard_exists with bundled standard (dict)."""
        bundled_standard = {"standards": {"id": "test_standard"}}
        sample_data = pd.DataFrame({"col1": [1, 2, 3]})

        result = self.engine.ensure_standard_exists(bundled_standard, sample_data)

        assert result is True

    def test_ensure_standard_exists_file_already_exists(self):
        """Test ensure_standard_exists with existing file."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp:
            tmp.write(b"test: standard")
            tmp.flush()

            try:
                result = self.engine.ensure_standard_exists(
                    tmp.name, pd.DataFrame({"col1": [1]})
                )
                assert result is True
            finally:
                os.unlink(tmp.name)

    def test_ensure_standard_exists_auto_generate_disabled(self):
        """Test ensure_standard_exists with auto-generation disabled."""
        self.engine.protection_config = {"auto_generate_standards": False}

        with pytest.raises(ProtectionError, match="Standard file not found"):
            self.engine.ensure_standard_exists(
                "/nonexistent/standard.yaml", pd.DataFrame({"col1": [1]})
            )

    @patch("adri.core.protection.os.makedirs")
    @patch("adri.analysis.data_profiler.DataProfiler")
    @patch("adri.analysis.standard_generator.StandardGenerator")
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.dump")
    def test_ensure_standard_exists_generation_with_sampling(
        self,
        mock_yaml_dump,
        mock_file,
        mock_generator_class,
        mock_profiler_class,
        mock_makedirs,
    ):
        """Test standard generation with data sampling."""
        self.engine.protection_config = {
            "auto_generate_standards": True,
            "data_sampling_limit": 5,
            "generation": {
                "default_thresholds": {"completeness_min": 90, "validity_min": 95}
            },
        }

        # Create large dataset that will be sampled
        large_data = pd.DataFrame({"col1": range(100), "col2": range(100, 200)})

        # Mock profiler
        mock_profiler = MagicMock()
        mock_profiler_class.return_value = mock_profiler
        mock_profiler.profile_data.return_value = {"summary": {"total_rows": 5}}

        # Mock generator
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_standard.return_value = {
            "standards": {"name": "Test", "version": "1.0.0"},
            "requirements": {},
        }

        result = self.engine.ensure_standard_exists(
            "/test/new_standard.yaml", large_data
        )

        assert result is True
        # Verify sampling was applied (should call head(5))
        mock_profiler.profile_data.assert_called_once()
        # Verify the data passed to profiler was sampled
        profiler_call_args = mock_profiler.profile_data.call_args[0]
        sampled_df = profiler_call_args[0]
        assert len(sampled_df) == 5  # Should be sampled to 5 rows

    @patch("adri.core.protection.os.makedirs")
    def test_ensure_standard_exists_unsupported_data_type(self, mock_makedirs):
        """Test ensure_standard_exists with unsupported data type."""
        self.engine.protection_config = {"auto_generate_standards": True}

        # Use a data type that can't be converted to DataFrame
        unsupported_data = object()

        with pytest.raises(
            ProtectionError, match="Cannot generate standard from data type"
        ):
            self.engine.ensure_standard_exists("/test/standard.yaml", unsupported_data)

    @patch("adri.analysis.data_profiler.DataProfiler")
    def test_ensure_standard_exists_generation_failure(self, mock_profiler_class):
        """Test ensure_standard_exists with generation failure."""
        self.engine.protection_config = {"auto_generate_standards": True}

        # Mock profiler to raise exception
        mock_profiler_class.side_effect = Exception("Profiling failed")

        with pytest.raises(ProtectionError, match="Failed to generate standard"):
            self.engine.ensure_standard_exists(
                "/test/standard.yaml", pd.DataFrame({"col1": [1]})
            )

    @patch("adri.core.protection.os.makedirs")
    @patch("adri.analysis.data_profiler.DataProfiler")
    @patch("adri.analysis.standard_generator.StandardGenerator")
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.dump")
    def test_ensure_standard_exists_with_list_data(
        self,
        mock_yaml_dump,
        mock_file,
        mock_generator_class,
        mock_profiler_class,
        mock_makedirs,
    ):
        """Test standard generation with list data input."""
        self.engine.protection_config = {"auto_generate_standards": True}

        # Mock profiler and generator
        mock_profiler = MagicMock()
        mock_profiler_class.return_value = mock_profiler
        mock_profiler.profile_data.return_value = {"summary": {"total_rows": 2}}

        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_standard.return_value = {
            "standards": {"name": "Test", "version": "1.0.0"},
            "requirements": {},
        }

        # Test with list data
        list_data = [{"col1": 1, "col2": "a"}, {"col1": 2, "col2": "b"}]

        result = self.engine.ensure_standard_exists("/test/standard.yaml", list_data)

        assert result is True
        mock_profiler.profile_data.assert_called_once()

    @patch("adri.core.protection.os.makedirs")
    @patch("adri.analysis.data_profiler.DataProfiler")
    @patch("adri.analysis.standard_generator.StandardGenerator")
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.dump")
    def test_ensure_standard_exists_with_dict_data(
        self,
        mock_yaml_dump,
        mock_file,
        mock_generator_class,
        mock_profiler_class,
        mock_makedirs,
    ):
        """Test standard generation with dict data input."""
        self.engine.protection_config = {"auto_generate_standards": True}

        # Mock profiler and generator
        mock_profiler = MagicMock()
        mock_profiler_class.return_value = mock_profiler
        mock_profiler.profile_data.return_value = {"summary": {"total_rows": 1}}

        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_standard.return_value = {
            "standards": {"name": "Test", "version": "1.0.0"},
            "requirements": {},
        }

        # Test with dict data
        dict_data = {"col1": [1, 2], "col2": ["a", "b"]}

        result = self.engine.ensure_standard_exists("/test/standard.yaml", dict_data)

        assert result is True
        mock_profiler.profile_data.assert_called_once()

    @patch("adri.core.protection.os.makedirs")
    @patch("adri.analysis.data_profiler.DataProfiler")
    @patch("adri.analysis.standard_generator.StandardGenerator")
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.dump")
    def test_ensure_standard_exists_with_to_pandas_method(
        self,
        mock_yaml_dump,
        mock_file,
        mock_generator_class,
        mock_profiler_class,
        mock_makedirs,
    ):
        """Test standard generation with data that has to_pandas method."""
        self.engine.protection_config = {"auto_generate_standards": True}

        # Mock profiler and generator
        mock_profiler = MagicMock()
        mock_profiler_class.return_value = mock_profiler
        mock_profiler.profile_data.return_value = {"summary": {"total_rows": 1}}

        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_standard.return_value = {
            "standards": {"name": "Test", "version": "1.0.0"},
            "requirements": {},
        }

        # Create mock data with to_pandas method
        mock_data = MagicMock()
        mock_data.to_pandas.return_value = pd.DataFrame({"col1": [1, 2]})

        result = self.engine.ensure_standard_exists("/test/standard.yaml", mock_data)

        assert result is True
        mock_data.to_pandas.assert_called_once()
        mock_profiler.profile_data.assert_called_once()


class TestAssessDataQualityMissingCoverage:
    """Test assess_data_quality method missing coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("adri.core.protection.ConfigManager"),
            patch("adri.core.protection.StandardsLoader"),
        ):
            self.engine = DataProtectionEngine()
            self.engine.protection_config = {"cache_duration_hours": 1}

    def test_assess_data_quality_bundled_standard_caching(self):
        """Test assessment with bundled standard and caching."""
        bundled_standard = {
            "standards": {"id": "test_standard", "name": "Test Standard"}
        }
        test_data = pd.DataFrame({"col1": [1, 2, 3]})

        # Mock assessment result
        mock_result = MagicMock()
        mock_result.overall_score = 85.0

        with (
            patch.object(self.engine, "_generate_data_hash", return_value="hash123"),
            patch("adri.core.protection.AssessmentEngine") as mock_assessor_class,
        ):
            mock_assessor = MagicMock()
            mock_assessor_class.return_value = mock_assessor
            mock_assessor.assess_with_standard_dict.return_value = mock_result

            # First call - should run assessment and cache result
            result1 = self.engine.assess_data_quality(test_data, bundled_standard)

            # Second call - should use cached result
            result2 = self.engine.assess_data_quality(test_data, bundled_standard)

            # Assessment should only be called once (first time)
            mock_assessor.assess_with_standard_dict.assert_called_once()
            assert result1 == mock_result
            assert result2 == mock_result

    def test_assess_data_quality_file_standard_caching(self):
        """Test assessment with file-based standard and caching."""
        standard_path = "/test/standard.yaml"
        test_data = pd.DataFrame({"col1": [1, 2, 3]})

        # Mock assessment result
        mock_result = MagicMock()
        mock_result.overall_score = 90.0

        with (
            patch.object(self.engine, "_generate_data_hash", return_value="hash456"),
            patch("adri.core.protection.AssessmentEngine") as mock_assessor_class,
        ):
            mock_assessor = MagicMock()
            mock_assessor_class.return_value = mock_assessor
            mock_assessor.assess.return_value = mock_result

            # First call
            result1 = self.engine.assess_data_quality(test_data, standard_path)

            # Second call - should use cache
            result2 = self.engine.assess_data_quality(test_data, standard_path)

            # Assessment should only be called once
            mock_assessor.assess.assert_called_once_with(test_data, standard_path)
            assert result1 == mock_result
            assert result2 == mock_result

    def test_assess_data_quality_cache_disabled(self):
        """Test assessment with caching disabled."""
        self.engine.protection_config = {"cache_duration_hours": 0}

        bundled_standard = {"standards": {"id": "test_standard"}}
        test_data = pd.DataFrame({"col1": [1, 2, 3]})

        mock_result = MagicMock()

        with (
            patch.object(self.engine, "_generate_data_hash", return_value="hash789"),
            patch("adri.core.protection.AssessmentEngine") as mock_assessor_class,
        ):
            mock_assessor = MagicMock()
            mock_assessor_class.return_value = mock_assessor
            mock_assessor.assess_with_standard_dict.return_value = mock_result

            # Multiple calls should each run assessment (no caching)
            self.engine.assess_data_quality(test_data, bundled_standard)
            self.engine.assess_data_quality(test_data, bundled_standard)

            # Should be called twice since caching is disabled
            assert mock_assessor.assess_with_standard_dict.call_count == 2

    def test_assess_data_quality_with_list_data(self):
        """Test assessment with list data conversion."""
        standard_path = "/test/standard.yaml"
        list_data = [{"col1": 1, "col2": "a"}, {"col1": 2, "col2": "b"}]

        mock_result = MagicMock()

        with patch("adri.core.protection.AssessmentEngine") as mock_assessor_class:
            mock_assessor = MagicMock()
            mock_assessor_class.return_value = mock_assessor
            mock_assessor.assess.return_value = mock_result

            result = self.engine.assess_data_quality(list_data, standard_path)

            # Should convert list to DataFrame and assess
            mock_assessor.assess.assert_called_once()
            call_args = mock_assessor.assess.call_args[0]
            assert isinstance(call_args[0], pd.DataFrame)
            assert result == mock_result

    def test_assess_data_quality_with_to_pandas_data(self):
        """Test assessment with data that has to_pandas method."""
        bundled_standard = {"standards": {"id": "test_standard"}}

        # Mock data with to_pandas method
        mock_data = MagicMock()
        mock_data.to_pandas.return_value = pd.DataFrame({"col1": [1, 2]})

        mock_result = MagicMock()

        with patch("adri.core.protection.AssessmentEngine") as mock_assessor_class:
            mock_assessor = MagicMock()
            mock_assessor_class.return_value = mock_assessor
            mock_assessor.assess_with_standard_dict.return_value = mock_result

            result = self.engine.assess_data_quality(mock_data, bundled_standard)

            mock_data.to_pandas.assert_called_once()
            mock_assessor.assess_with_standard_dict.assert_called_once()
            assert result == mock_result

    def test_assess_data_quality_unsupported_data_type(self):
        """Test assessment with unsupported data type."""
        standard_path = "/test/standard.yaml"
        unsupported_data = object()

        with pytest.raises(ProtectionError, match="Cannot assess data type"):
            self.engine.assess_data_quality(unsupported_data, standard_path)

    def test_assess_data_quality_assessment_failure(self):
        """Test assessment with assessment engine failure."""
        standard_path = "/test/standard.yaml"
        test_data = pd.DataFrame({"col1": [1, 2, 3]})

        with patch("adri.core.protection.AssessmentEngine") as mock_assessor_class:
            mock_assessor = MagicMock()
            mock_assessor_class.return_value = mock_assessor
            mock_assessor.assess.side_effect = Exception("Assessment failed")

            with pytest.raises(ProtectionError, match="Assessment failed"):
                self.engine.assess_data_quality(test_data, standard_path)


class TestHandleQualityFailureMissingCoverage:
    """Test handle_quality_failure method missing coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("adri.core.protection.ConfigManager"),
            patch("adri.core.protection.StandardsLoader"),
        ):
            self.engine = DataProtectionEngine()

    def test_handle_quality_failure_warn_mode(self):
        """Test quality failure handling in warn mode."""
        mock_result = MagicMock()
        mock_result.overall_score = 60.0

        with (
            patch.object(
                self.engine, "_format_quality_error", return_value="Test error message"
            ),
            patch("adri.core.protection.logger") as mock_logger,
        ):
            # Should not raise exception, just log warning
            self.engine.handle_quality_failure(
                mock_result, "warn", 80.0, "/test/standard.yaml"
            )

            mock_logger.warning.assert_called_once_with(
                "Data quality warning: Test error message"
            )

    def test_handle_quality_failure_continue_mode(self):
        """Test quality failure handling in continue mode."""
        mock_result = MagicMock()
        mock_result.overall_score = 60.0

        with (
            patch.object(
                self.engine, "_format_quality_error", return_value="Test error message"
            ),
            patch("adri.core.protection.logger") as mock_logger,
        ):
            # Should not raise exception, just log debug
            self.engine.handle_quality_failure(
                mock_result, "continue", 80.0, "/test/standard.yaml"
            )

            mock_logger.debug.assert_called_once_with(
                "Data quality failure (continuing): Test error message"
            )

    def test_handle_quality_failure_invalid_mode(self):
        """Test quality failure handling with invalid mode."""
        mock_result = MagicMock()
        mock_result.overall_score = 60.0

        with (
            patch.object(
                self.engine, "_format_quality_error", return_value="Test error message"
            ),
            patch("adri.core.protection.logger") as mock_logger,
        ):
            # Should default to raise mode and log error
            with pytest.raises(ProtectionError, match="Test error message"):
                self.engine.handle_quality_failure(mock_result, "invalid_mode", 80.0)

            mock_logger.error.assert_called_once_with(
                "Invalid failure mode 'invalid_mode', defaulting to 'raise'"
            )


class TestProtectFunctionCallMissingCoverage:
    """Test protect_function_call method missing coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("adri.core.protection.ConfigManager"),
            patch("adri.core.protection.StandardsLoader"),
        ):
            self.engine = DataProtectionEngine()
            self.engine.protection_config = {
                "default_min_score": 75,
                "default_failure_mode": "warn",
                "verbose_protection": True,
            }

    def test_protect_function_call_with_dimension_requirements(self):
        """Test function protection with dimension-specific requirements that fail."""

        def test_func(data):
            return "success"

        test_data = pd.DataFrame({"col1": [1, 2, 3]})
        mock_result = MagicMock()
        mock_result.overall_score = 85.0
        mock_result.dimension_scores = {
            "validity": MagicMock(score=12.0),  # Failing score
            "completeness": MagicMock(score=16.0),
        }

        dimensions = {"validity": 15.0, "completeness": 15.0}

        with (
            patch.object(
                self.engine, "_extract_data_parameter", return_value=test_data
            ),
            patch.object(
                self.engine, "resolve_standard", return_value="/test/standard.yaml"
            ),
            patch.object(self.engine, "ensure_standard_exists", return_value=True),
            patch.object(self.engine, "assess_data_quality", return_value=mock_result),
            patch.object(
                self.engine, "_check_dimension_requirements"
            ) as mock_check_dims,
            patch.object(
                self.engine, "_format_quality_success", return_value="Success message"
            ),
            patch.object(self.engine.audit_logger, "log_assessment"),
        ):
            result = self.engine.protect_function_call(
                test_func,
                (test_data,),
                {},
                "data",
                "test_func",
                dimensions=dimensions,
                verbose=True,
            )

            assert result == "success"
            mock_check_dims.assert_called_once_with(mock_result, dimensions, "warn")

    def test_protect_function_call_with_bundled_standard_verbose(self):
        """Test function protection with bundled standard and verbose output."""

        def test_func(data):
            return "success"

        test_data = pd.DataFrame({"col1": [1, 2, 3]})
        bundled_standard = {
            "standards": {"id": "test_standard", "name": "Test Standard"}
        }
        mock_result = MagicMock()
        mock_result.overall_score = 85.0

        with (
            patch.object(
                self.engine, "_extract_data_parameter", return_value=test_data
            ),
            patch.object(
                self.engine, "resolve_standard", return_value=bundled_standard
            ),
            patch.object(self.engine, "ensure_standard_exists", return_value=True),
            patch.object(self.engine, "assess_data_quality", return_value=mock_result),
            patch.object(
                self.engine, "_format_quality_success", return_value="Success message"
            ),
            patch("adri.core.protection.logger") as mock_logger,
        ):
            result = self.engine.protect_function_call(
                test_func, (test_data,), {}, "data", "test_func", verbose=True
            )

            assert result == "success"
            # Should log bundled standard info
            mock_logger.info.assert_any_call("Using bundled standard: test_standard")

    def test_protect_function_call_non_verbose_success_print(self):
        """Test function protection with non-verbose mode success print."""

        def test_func(data):
            return "success"

        test_data = pd.DataFrame({"col1": [1, 2, 3]})
        mock_result = MagicMock()
        mock_result.overall_score = 85.0

        with (
            patch.object(
                self.engine, "_extract_data_parameter", return_value=test_data
            ),
            patch.object(
                self.engine, "resolve_standard", return_value="/test/standard.yaml"
            ),
            patch.object(self.engine, "ensure_standard_exists", return_value=True),
            patch.object(self.engine, "assess_data_quality", return_value=mock_result),
            patch.object(
                self.engine, "_format_quality_success", return_value="Success message"
            ),
            patch("builtins.print") as mock_print,
        ):
            result = self.engine.protect_function_call(
                test_func, (test_data,), {}, "data", "test_func", verbose=False
            )

            assert result == "success"
            # Should print success message in non-verbose mode
            mock_print.assert_called_once_with("Success message")


class TestExtractDataParameterMissingCoverage:
    """Test _extract_data_parameter method missing coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("adri.core.protection.ConfigManager"),
            patch("adri.core.protection.StandardsLoader"),
        ):
            self.engine = DataProtectionEngine()

    def test_extract_data_parameter_from_kwargs(self):
        """Test extracting data parameter from kwargs."""

        def test_func(data, other_param):
            pass

        test_data = pd.DataFrame({"col1": [1, 2, 3]})
        kwargs = {"data": test_data, "other_param": "value"}

        result = self.engine._extract_data_parameter(test_func, (), kwargs, "data")

        assert result is test_data

    def test_extract_data_parameter_from_positional_args(self):
        """Test extracting data parameter from positional arguments."""

        def test_func(data, other_param):
            pass

        test_data = pd.DataFrame({"col1": [1, 2, 3]})
        args = (test_data, "other_value")

        result = self.engine._extract_data_parameter(test_func, args, {}, "data")

        assert result is test_data

    def test_extract_data_parameter_inspection_failure(self):
        """Test data parameter extraction with function inspection failure."""

        # Create a function that can't be inspected easily
        def test_func():
            return None  # Functions can be tricky to inspect

        # Don't provide the parameter in kwargs, so it has to use inspection
        kwargs = {"other_param": "other_value"}
        args = ("test_data",)  # Provide data as positional arg

        with (
            patch("inspect.signature", side_effect=Exception("Inspection failed")),
            patch("adri.core.protection.logger") as mock_logger,
        ):
            # This should trigger the inspection failure and raise ValueError
            with pytest.raises(
                ValueError, match="Could not find data parameter 'data'"
            ):
                self.engine._extract_data_parameter(test_func, args, kwargs, "data")

            mock_logger.warning.assert_called_once_with(
                "Could not inspect function signature: Inspection failed"
            )

    def test_extract_data_parameter_not_found(self):
        """Test data parameter extraction when parameter is not found."""

        def test_func(other_param):
            pass

        args = ("other_value",)
        kwargs = {"other_param": "value"}

        with pytest.raises(
            ValueError, match="Could not find data parameter 'missing_param'"
        ):
            self.engine._extract_data_parameter(
                test_func, args, kwargs, "missing_param"
            )


class TestGenerateDataHashMissingCoverage:
    """Test _generate_data_hash method missing coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("adri.core.protection.ConfigManager"),
            patch("adri.core.protection.StandardsLoader"),
        ):
            self.engine = DataProtectionEngine()

    def test_generate_data_hash_dataframe(self):
        """Test data hash generation for DataFrame."""
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

        hash_result = self.engine._generate_data_hash(df)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 16  # MD5 hash truncated to 16 chars

    def test_generate_data_hash_non_dataframe(self):
        """Test data hash generation for non-DataFrame data."""
        test_data = {"key": "value", "number": 123}

        hash_result = self.engine._generate_data_hash(test_data)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 16

    def test_generate_data_hash_exception_fallback(self):
        """Test data hash generation with exception fallback."""
        # Create data that will cause an exception during hashing
        problematic_data = MagicMock()
        problematic_data.__str__.side_effect = Exception("String conversion failed")

        with patch("time.time", return_value=1234567890):
            hash_result = self.engine._generate_data_hash(problematic_data)

        assert hash_result == "1234567890"  # Should fallback to timestamp


class TestFormatQualityErrorMissingCoverage:
    """Test _format_quality_error method missing coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("adri.core.protection.ConfigManager"),
            patch("adri.core.protection.StandardsLoader"),
        ):
            self.engine = DataProtectionEngine()

    def test_format_quality_error_with_bundled_standard(self):
        """Test error formatting with bundled standard."""
        mock_result = MagicMock()
        mock_result.overall_score = 65.0
        mock_result.dimension_scores = {
            "validity": MagicMock(score=12.0),
            "completeness": MagicMock(score=14.0),
        }

        bundled_standard = {
            "standards": {"id": "test_standard", "name": "Test Standard"}
        }

        with patch.object(
            self.engine,
            "_identify_main_issues",
            return_value="invalid data formats detected",
        ):
            error_msg = self.engine._format_quality_error(
                mock_result, 80.0, bundled_standard
            )

        assert "test_standard (bundled)" in error_msg
        assert "65.0/100" in error_msg
        assert "invalid data formats detected" in error_msg

    def test_format_quality_error_with_file_standard(self):
        """Test error formatting with file-based standard."""
        mock_result = MagicMock()
        mock_result.overall_score = 70.0
        mock_result.dimension_scores = {}

        standard_path = "/test/path/customer_data_standard.yaml"

        with patch.object(
            self.engine,
            "_identify_main_issues",
            return_value="quality threshold not met",
        ):
            error_msg = self.engine._format_quality_error(
                mock_result, 85.0, standard_path
            )

        assert standard_path in error_msg
        assert "70.0/100" in error_msg
        assert "adri show-standard customer_data" in error_msg


class TestIdentifyMainIssuesMissingCoverage:
    """Test _identify_main_issues method missing coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("adri.core.protection.ConfigManager"),
            patch("adri.core.protection.StandardsLoader"),
        ):
            self.engine = DataProtectionEngine()

    def test_identify_main_issues_no_problems(self):
        """Test issue identification with no problem dimensions."""
        mock_result = MagicMock()

        result = self.engine._identify_main_issues(mock_result, [])

        assert result == "quality threshold not met"

    def test_identify_main_issues_single_problem(self):
        """Test issue identification with single problem dimension."""
        mock_result = MagicMock()
        problem_dimensions = ["validity"]

        result = self.engine._identify_main_issues(mock_result, problem_dimensions)

        assert (
            result == "invalid data formats detected (e.g., bad emails, invalid dates)"
        )

    def test_identify_main_issues_two_problems(self):
        """Test issue identification with two problem dimensions."""
        mock_result = MagicMock()
        problem_dimensions = ["completeness", "consistency"]

        result = self.engine._identify_main_issues(mock_result, problem_dimensions)

        assert "missing required data fields and inconsistent data formats" in result

    def test_identify_main_issues_many_problems(self):
        """Test issue identification with many problem dimensions."""
        mock_result = MagicMock()
        problem_dimensions = ["validity", "completeness", "consistency", "freshness"]

        result = self.engine._identify_main_issues(mock_result, problem_dimensions)

        # The method returns the first two issues joined, not a count
        assert (
            "invalid data formats detected" in result
            and "missing required data fields" in result
        )

    def test_identify_main_issues_unknown_dimension(self):
        """Test issue identification with unknown dimension."""
        mock_result = MagicMock()
        problem_dimensions = ["unknown_dimension"]

        result = self.engine._identify_main_issues(mock_result, problem_dimensions)

        assert result == "1 data quality issues"


class TestFormatQualitySuccessMissingCoverage:
    """Test _format_quality_success method missing coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("adri.core.protection.ConfigManager"),
            patch("adri.core.protection.StandardsLoader"),
        ):
            self.engine = DataProtectionEngine()

    def test_format_quality_success_bundled_standard_verbose(self):
        """Test success formatting with bundled standard in verbose mode."""
        mock_result = MagicMock()
        mock_result.overall_score = 92.0
        mock_result.dimension_scores = {
            "validity": MagicMock(score=18.0),
            "completeness": MagicMock(score=17.0),
        }

        bundled_standard = {
            "standards": {
                "id": "test_standard",
                "name": "Test Standard",
                "version": "2.0.0",
            }
        }

        with patch.object(
            self.engine, "_was_standard_just_created", return_value=False
        ):
            result = self.engine._format_quality_success(
                mock_result, 80.0, bundled_standard, "test_func", verbose=True
            )

        assert "Test Standard v2.0.0" in result
        assert "92.0/100" in result
        assert "Validity: 18.0/20" in result
        assert "adri show-standard Test Standard" in result

    def test_format_quality_success_new_standard_verbose(self):
        """Test success formatting with newly created standard in verbose mode."""
        mock_result = MagicMock()
        mock_result.overall_score = 88.0
        mock_result.dimension_scores = {}

        standard_path = "/test/new_standard.yaml"

        with (
            patch.object(self.engine, "_was_standard_just_created", return_value=True),
            patch("os.path.exists", return_value=True),
            patch(
                "builtins.open", mock_open(read_data='standards:\n  version: "1.5.0"')
            ),
            patch("yaml.safe_load", return_value={"standards": {"version": "1.5.0"}}),
        ):
            result = self.engine._format_quality_success(
                mock_result, 80.0, standard_path, "test_func", verbose=True
            )

        assert "(NEW)" in result
        assert "v1.5.0" in result
        assert "Since this is a NEW standard:" in result
        assert "Customize Your Standard:" in result

    def test_format_quality_success_minimal_mode(self):
        """Test success formatting in minimal (non-verbose) mode."""
        mock_result = MagicMock()
        mock_result.overall_score = 85.0

        standard_path = "/test/standard.yaml"

        with patch.object(
            self.engine, "_was_standard_just_created", return_value=False
        ):
            result = self.engine._format_quality_success(
                mock_result, 80.0, standard_path, "test_func", verbose=False
            )

        assert "ADRI Protection: ALLOWED ✅" in result
        assert "85.0/100" in result
        assert "standard v1.0.0" in result
        # Should not contain verbose details
        assert "Learn More:" not in result


class TestWasStandardJustCreatedMissingCoverage:
    """Test _was_standard_just_created method missing coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("adri.core.protection.ConfigManager"),
            patch("adri.core.protection.StandardsLoader"),
        ):
            self.engine = DataProtectionEngine()

    def test_was_standard_just_created_nonexistent_file(self):
        """Test with nonexistent file."""
        result = self.engine._was_standard_just_created("/nonexistent/file.yaml")

        assert result is False

    def test_was_standard_just_created_none_path(self):
        """Test with None path."""
        result = self.engine._was_standard_just_created(None)

        assert result is False

    def test_was_standard_just_created_old_file(self):
        """Test with old file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp.flush()

            try:
                # Mock file creation time to be old
                with patch("os.path.getctime", return_value=time.time() - 100):
                    result = self.engine._was_standard_just_created(tmp.name)

                assert result is False
            finally:
                os.unlink(tmp.name)

    def test_was_standard_just_created_recent_file(self):
        """Test with recently created file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp.flush()

            try:
                # Mock file creation time to be very recent
                with patch("os.path.getctime", return_value=time.time() - 2):
                    result = self.engine._was_standard_just_created(tmp.name)

                assert result is True
            finally:
                os.unlink(tmp.name)

    def test_was_standard_just_created_exception(self):
        """Test with exception during file stat."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp.flush()

            try:
                with patch(
                    "os.path.getctime", side_effect=OSError("Permission denied")
                ):
                    result = self.engine._was_standard_just_created(tmp.name)

                assert result is False
            finally:
                os.unlink(tmp.name)


class TestCheckDimensionRequirementsMissingCoverage:
    """Test _check_dimension_requirements method missing coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("adri.core.protection.ConfigManager"),
            patch("adri.core.protection.StandardsLoader"),
        ):
            self.engine = DataProtectionEngine()

    def test_check_dimension_requirements_no_dimension_scores(self):
        """Test dimension checking with assessment result lacking dimension scores."""
        mock_result = MagicMock()
        del mock_result.dimension_scores  # Remove dimension_scores attribute

        dimensions = {"validity": 15.0}

        with patch("adri.core.protection.logger") as mock_logger:
            # Should not raise exception, just log warning
            self.engine._check_dimension_requirements(mock_result, dimensions, "raise")

            mock_logger.warning.assert_called_once_with(
                "Assessment result does not contain dimension scores"
            )

    def test_check_dimension_requirements_missing_dimension_raise(self):
        """Test dimension checking with missing required dimension in raise mode."""
        mock_result = MagicMock()
        mock_result.dimension_scores = {"validity": MagicMock(score=18.0)}

        dimensions = {"missing_dimension": 15.0}

        with pytest.raises(
            ProtectionError, match="Required dimension 'missing_dimension' not found"
        ):
            self.engine._check_dimension_requirements(mock_result, dimensions, "raise")

    def test_check_dimension_requirements_missing_dimension_warn(self):
        """Test dimension checking with missing required dimension in warn mode."""
        mock_result = MagicMock()
        mock_result.dimension_scores = {"validity": MagicMock(score=18.0)}

        dimensions = {"missing_dimension": 15.0}

        with patch("adri.core.protection.logger") as mock_logger:
            self.engine._check_dimension_requirements(mock_result, dimensions, "warn")

            mock_logger.warning.assert_called_once_with(
                "Data quality warning: Required dimension 'missing_dimension' not found in assessment"
            )

    def test_check_dimension_requirements_insufficient_score_raise(self):
        """Test dimension checking with insufficient score in raise mode."""
        mock_result = MagicMock()
        mock_result.dimension_scores = {"validity": MagicMock(score=12.0)}

        dimensions = {"validity": 15.0}

        with pytest.raises(
            ProtectionError, match="Dimension 'validity' score insufficient"
        ):
            self.engine._check_dimension_requirements(mock_result, dimensions, "raise")

    def test_check_dimension_requirements_insufficient_score_warn(self):
        """Test dimension checking with insufficient score in warn mode."""
        mock_result = MagicMock()
        mock_result.dimension_scores = {"completeness": MagicMock(score=10.0)}

        dimensions = {"completeness": 15.0}

        with patch("adri.core.protection.logger") as mock_logger:
            self.engine._check_dimension_requirements(mock_result, dimensions, "warn")

            mock_logger.warning.assert_called_once_with(
                "Data quality warning: Dimension 'completeness' score insufficient: 10.0/20 (required: 15.0/20)"
            )

    def test_check_dimension_requirements_continue_mode_silent(self):
        """Test dimension checking in continue mode (should be silent)."""
        mock_result = MagicMock()
        mock_result.dimension_scores = {"validity": MagicMock(score=8.0)}

        dimensions = {"validity": 15.0}

        with patch("adri.core.protection.logger") as mock_logger:
            # Should not raise exception or log anything
            self.engine._check_dimension_requirements(
                mock_result, dimensions, "continue"
            )

            # No warnings or errors should be logged in continue mode
            mock_logger.warning.assert_not_called()
            mock_logger.error.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
