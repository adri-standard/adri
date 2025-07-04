"""
Tests to improve coverage for adri.decorators.guard module.

These tests target specific uncovered lines to reach 90%+ coverage.
"""

import pytest
from unittest.mock import patch, MagicMock
from adri.decorators.guard import adri_strict, adri_permissive, adri_financial


class TestGuardCoverage:
    """Tests targeting specific uncovered lines in guard.py."""

    def test_adri_strict_convenience_function(self):
        """Test the adri_strict convenience function (line 161)."""
        # Test that adri_strict sets the correct defaults
        decorator = adri_strict(data_param="test_data")
        
        # The decorator should be a function
        assert callable(decorator)
        
        # Test with custom parameters
        decorator_custom = adri_strict(
            data_param="custom_data",
            min_score=95,
            on_failure="continue"
        )
        assert callable(decorator_custom)

    def test_adri_permissive_convenience_function(self):
        """Test the adri_permissive convenience function (line 175)."""
        # Test that adri_permissive sets the correct defaults
        decorator = adri_permissive(data_param="test_data")
        
        # The decorator should be a function
        assert callable(decorator)
        
        # Test with custom parameters
        decorator_custom = adri_permissive(
            data_param="custom_data",
            min_score=60,
            on_failure="continue",
            verbose=False
        )
        assert callable(decorator_custom)

    def test_adri_financial_convenience_function(self):
        """Test the adri_financial convenience function (line 190)."""
        # Test that adri_financial sets the correct defaults
        decorator = adri_financial(data_param="financial_data")
        
        # The decorator should be a function
        assert callable(decorator)
        
        # Test with custom parameters
        decorator_custom = adri_financial(
            data_param="custom_data",
            min_score=98,
            dimensions={"validity": 20, "completeness": 20},
            on_failure="continue"
        )
        assert callable(decorator_custom)

    def test_convenience_functions_with_kwargs(self):
        """Test convenience functions with various kwargs."""
        # Test adri_strict with additional kwargs
        strict_decorator = adri_strict(
            data_param="strict_data",
            standard_file="strict.yaml",
            cache_assessments=True
        )
        assert callable(strict_decorator)
        
        # Test adri_permissive with additional kwargs
        permissive_decorator = adri_permissive(
            data_param="permissive_data",
            standard_name="permissive_standard",
            auto_generate=False
        )
        assert callable(permissive_decorator)
        
        # Test adri_financial with additional kwargs
        financial_decorator = adri_financial(
            data_param="financial_data",
            standard_id="financial_v2",
            cache_assessments=True
        )
        assert callable(financial_decorator)

    def test_convenience_functions_parameter_overrides(self):
        """Test that convenience functions properly override default parameters."""
        # Test adri_strict parameter overrides
        strict_decorator = adri_strict(
            data_param="test_data",
            min_score=85,  # Override default 90
            on_failure="warn"  # Override default "raise"
        )
        assert callable(strict_decorator)
        
        # Test adri_permissive parameter overrides
        permissive_decorator = adri_permissive(
            data_param="test_data",
            min_score=80,  # Override default 70
            on_failure="raise",  # Override default "warn"
            verbose=False  # Override default True
        )
        assert callable(permissive_decorator)
        
        # Test adri_financial parameter overrides
        financial_decorator = adri_financial(
            data_param="test_data",
            min_score=90,  # Override default 95
            dimensions={"validity": 15},  # Override default dimensions
            on_failure="warn"  # Override default "raise"
        )
        assert callable(financial_decorator)

    @patch('adri.decorators.guard.DataProtectionEngine')
    def test_convenience_functions_applied_to_real_function(self, mock_engine_class):
        """Test convenience functions when applied to actual functions."""
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        mock_engine.protect_function_call.return_value = "protected_result"
        
        # Test adri_strict applied to function
        @adri_strict(data_param="data")
        def strict_function(data):
            return "strict_result"
        
        result = strict_function({"test": "data"})
        assert result == "protected_result"
        mock_engine.protect_function_call.assert_called()
        
        # Test adri_permissive applied to function
        @adri_permissive(data_param="data")
        def permissive_function(data):
            return "permissive_result"
        
        result = permissive_function({"test": "data"})
        assert result == "protected_result"
        
        # Test adri_financial applied to function
        @adri_financial(data_param="data")
        def financial_function(data):
            return "financial_result"
        
        result = financial_function({"test": "data"})
        assert result == "protected_result"
