"""
Additional tests to improve coverage for adri.analysis.data_profiler module.

These tests target specific uncovered lines and edge cases using ONLY real data
and NO mocking to prevent pandas state pollution - BEST PRACTICE APPROACH.
"""

import numpy as np
import pandas as pd
import pytest

from adri.analysis.data_profiler import DataProfiler


class TestDataProfilerCoverage:
    """Tests targeting specific uncovered lines in DataProfiler - NO MOCKING."""

    def test_empty_series_handling_in_profile_methods(self):
        """Test handling of empty series in various profile methods."""
        profiler = DataProfiler()

        # Test empty integer series
        empty_int_series = pd.Series([], dtype="int64")
        int_profile = profiler._profile_integer_field(empty_int_series)
        assert int_profile["min_value"] == 0
        assert int_profile["max_value"] == 0
        assert int_profile["avg_value"] == 0.0

        # Test empty float series
        empty_float_series = pd.Series([], dtype="float64")
        float_profile = profiler._profile_float_field(empty_float_series)
        assert float_profile["min_value"] == 0.0
        assert float_profile["max_value"] == 0.0
        assert float_profile["avg_value"] == 0.0

        # Test empty string series
        empty_string_series = pd.Series([], dtype="object")
        string_profile = profiler._profile_string_field(empty_string_series)
        assert string_profile["min_length"] == 0
        assert string_profile["max_length"] == 0
        assert string_profile["avg_length"] == 0.0

    def test_exception_handling_with_real_problematic_data(self):
        """Test exception handling using real problematic data - NO MOCKING."""
        profiler = DataProfiler()

        # Test integer field with inf/nan values
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            problematic_int_series = pd.Series([float("inf"), float("-inf"), float("nan")])
            int_profile = profiler._profile_integer_field(problematic_int_series)
            assert int_profile["min_value"] == 0
            assert int_profile["max_value"] == 0
            assert int_profile["avg_value"] == 0.0

        # Test float field with inf/nan values
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            problematic_float_series = pd.Series([float("inf"), float("-inf"), float("nan")])
            float_profile = profiler._profile_float_field(problematic_float_series)
            assert float_profile["min_value"] == 0.0
            assert float_profile["max_value"] == 0.0
            assert float_profile["avg_value"] == 0.0

    def test_string_field_edge_cases_real_data(self):
        """Test string field with edge case data."""
        profiler = DataProfiler()

        # Test with data that could cause string length calculation issues
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            edge_case_series = pd.Series([None, "", np.nan, "test"])
            string_profile = profiler._profile_string_field(edge_case_series)

            # Should handle edge cases gracefully
            assert "min_length" in string_profile
            assert "max_length" in string_profile
            assert "avg_length" in string_profile
            assert isinstance(string_profile["min_length"], int)
            assert isinstance(string_profile["max_length"], int)
            assert isinstance(string_profile["avg_length"], float)

    def test_all_null_column_handling(self):
        """Test handling of columns with all null values."""
        profiler = DataProfiler()

        # Create DataFrame with all-null column
        df_with_nulls = pd.DataFrame(
            {"all_nulls": [None, None, None, None], "some_data": [1, 2, 3, 4]}
        )

        profile = profiler.profile_data(df_with_nulls)

        # All-null column should default to string type
        all_nulls_profile = profile["fields"]["all_nulls"]
        assert all_nulls_profile["type"] == "string"
        assert all_nulls_profile["nullable"] is True
        assert all_nulls_profile["null_count"] == 4
        assert all_nulls_profile["null_percentage"] == 100.0

    def test_string_length_calculation_edge_cases(self):
        """Test string length calculation with edge cases using real data."""
        profiler = DataProfiler()

        # Test with very long strings
        long_string_df = pd.DataFrame(
            {"long_strings": ["a" * 1000, "b" * 2000, "c" * 500]}
        )

        profile = profiler.profile_data(long_string_df)
        string_profile = profile["fields"]["long_strings"]

        assert string_profile["min_length"] == 500
        assert string_profile["max_length"] == 2000
        assert string_profile["avg_length"] == (1000 + 2000 + 500) / 3

    def test_email_pattern_comprehensive_real_data(self):
        """Test email pattern detection using real email data."""
        profiler = DataProfiler()

        # Test with all valid emails
        valid_emails_df = pd.DataFrame(
            {
                "emails": [
                    "test@example.com",
                    "user.name@domain.org",
                    "user+tag@example.co.uk",
                ]
            }
        )

        profile = profiler.profile_data(valid_emails_df)
        email_profile = profile["fields"]["emails"]

        assert email_profile["type"] == "string"
        assert "pattern" in email_profile
        assert "@" in email_profile["pattern"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
