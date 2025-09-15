"""
Comprehensive tests for DataProfiler to achieve 85%+ coverage.
Tests edge cases, error handling, and additional functionality.
"""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import re
from adri.analysis.data_profiler import DataProfiler


class TestDataProfilerComprehensive(unittest.TestCase):
    """Comprehensive test cases for DataProfiler edge cases and full coverage."""

    def setUp(self):
        """Set up test fixtures."""
        self.profiler = DataProfiler()

    def test_email_pattern_compilation(self):
        """Test that email pattern is properly compiled."""
        # Test the email pattern directly
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test+tag@example.org"
        ]
        
        for email in valid_emails:
            self.assertTrue(self.profiler.email_pattern.match(email))
        
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@"
        ]
        
        for email in invalid_emails:
            self.assertIsNone(self.profiler.email_pattern.match(email))

    def test_date_patterns_compilation(self):
        """Test that date patterns are properly compiled."""
        # Test date patterns
        valid_dates = [
            ("2023-12-31", 0),  # YYYY-MM-DD
            ("12/31/2023", 1),  # MM/DD/YYYY  
            ("12-31-2023", 2)   # MM-DD-YYYY
        ]
        
        for date_str, pattern_idx in valid_dates:
            self.assertTrue(self.profiler.date_patterns[pattern_idx].match(date_str))

    def test_is_boolean_series_edge_cases(self):
        """Test boolean series detection with various edge cases."""
        # Test with mixed boolean representations
        bool_series = pd.Series(["true", "false", "True", "False"])
        self.assertTrue(self.profiler._is_boolean_series(bool_series))
        
        # Test with numeric boolean
        numeric_bool = pd.Series([1, 0, 1, 0])
        self.assertTrue(self.profiler._is_boolean_series(numeric_bool))
        
        # Test with yes/no
        yes_no_series = pd.Series(["yes", "no", "y", "n"])
        self.assertTrue(self.profiler._is_boolean_series(yes_no_series))
        
        # Test with invalid boolean
        invalid_bool = pd.Series(["maybe", "perhaps"])
        self.assertFalse(self.profiler._is_boolean_series(invalid_bool))
        
        # Test exception handling
        with patch.object(pd.Series, 'unique', side_effect=Exception("Test error")):
            result = self.profiler._is_boolean_series(pd.Series([True, False]))
            self.assertFalse(result)

    def test_is_integer_series_edge_cases(self):
        """Test integer series detection with edge cases."""
        # Test with valid integers as strings
        int_strings = pd.Series(["1", "2", "3", "4"])
        self.assertTrue(self.profiler._is_integer_series(int_strings))
        
        # Test with floats that are actually integers
        float_ints = pd.Series([1.0, 2.0, 3.0])
        self.assertTrue(self.profiler._is_integer_series(float_ints))
        
        # Test with mixed valid/invalid
        mixed_series = pd.Series(["1", "not_a_number"])
        self.assertFalse(self.profiler._is_integer_series(mixed_series))
        
        # Test exception handling
        with patch('pandas.to_numeric', side_effect=Exception("Test error")):
            result = self.profiler._is_integer_series(pd.Series([1, 2, 3]))
            self.assertFalse(result)

    def test_is_float_series_edge_cases(self):
        """Test float series detection with edge cases."""
        # Test with string floats
        float_strings = pd.Series(["1.5", "2.7", "3.14"])
        self.assertTrue(self.profiler._is_float_series(float_strings))
        
        # Test with integers (should still be considered numeric)
        int_series = pd.Series([1, 2, 3])
        self.assertTrue(self.profiler._is_float_series(int_series))
        
        # Test with mixed valid/invalid
        mixed_series = pd.Series(["1.5", "not_a_number"])
        self.assertFalse(self.profiler._is_float_series(mixed_series))
        
        # Test exception handling
        with patch('pandas.to_numeric', side_effect=Exception("Test error")):
            result = self.profiler._is_float_series(pd.Series([1.1, 2.2]))
            self.assertFalse(result)

    def test_is_date_series_edge_cases(self):
        """Test date series detection with edge cases."""
        # Test with various date formats
        date_series = pd.Series(["2023-01-01", "2023-02-15", "2023-12-31"])
        self.assertTrue(self.profiler._is_date_series(date_series))
        
        # Test with US format dates
        us_dates = pd.Series(["01/15/2023", "12/31/2023"])
        self.assertTrue(self.profiler._is_date_series(us_dates))
        
        # Test with non-date strings
        non_dates = pd.Series(["hello", "world", "test"])
        self.assertFalse(self.profiler._is_date_series(non_dates))
        
        # Test exception handling
        with patch.object(pd.Series, 'head', side_effect=Exception("Test error")):
            result = self.profiler._is_date_series(pd.Series(["2023-01-01"]))
            self.assertFalse(result)

    def test_profile_integer_field_edge_cases(self):
        """Test integer field profiling edge cases."""
        # Test with empty series
        empty_series = pd.Series([], dtype='int64')
        result = self.profiler._profile_integer_field(empty_series)
        expected = {"min_value": 0, "max_value": 0, "avg_value": 0.0}
        self.assertEqual(result, expected)
        
        # Test with all-null series
        null_series = pd.Series([None, None, None])
        result = self.profiler._profile_integer_field(null_series)
        self.assertEqual(result, expected)
        
        # Test with string integers
        string_ints = pd.Series(["10", "20", "30"])
        result = self.profiler._profile_integer_field(string_ints)
        self.assertEqual(result["min_value"], 10)
        self.assertEqual(result["max_value"], 30)
        self.assertEqual(result["avg_value"], 20.0)

    def test_profile_float_field_edge_cases(self):
        """Test float field profiling edge cases."""
        # Test with empty series
        empty_series = pd.Series([], dtype='float64')
        result = self.profiler._profile_float_field(empty_series)
        expected = {"min_value": 0.0, "max_value": 0.0, "avg_value": 0.0}
        self.assertEqual(result, expected)
        
        # Test with string floats
        string_floats = pd.Series(["1.5", "2.5", "3.5"])
        result = self.profiler._profile_float_field(string_floats)
        self.assertEqual(result["min_value"], 1.5)
        self.assertEqual(result["max_value"], 3.5)
        self.assertEqual(result["avg_value"], 2.5)

    def test_profile_string_field_edge_cases(self):
        """Test string field profiling edge cases."""
        # Test with empty series
        empty_series = pd.Series([], dtype='string')
        result = self.profiler._profile_string_field(empty_series)
        expected = {"min_length": 0, "max_length": 0, "avg_length": 0.0}
        self.assertEqual(result, expected)
        
        # Test with numbers converted to strings
        number_strings = pd.Series([123, 45, 6789])
        result = self.profiler._profile_string_field(number_strings)
        self.assertEqual(result["min_length"], 1)  # "6"
        self.assertEqual(result["max_length"], 4)  # "6789"
        
        # Test pattern detection with emails
        email_series = pd.Series(["test@example.com", "user@domain.org"])
        result = self.profiler._profile_string_field(email_series)
        self.assertIn("pattern", result)
        self.assertIn("@", result["pattern"])

    def test_profile_boolean_field_edge_cases(self):
        """Test boolean field profiling edge cases."""
        # Test with mixed boolean representations
        mixed_bool = pd.Series([True, False, 1, 0, "true", "false"])
        result = self.profiler._profile_boolean_field(mixed_bool)
        self.assertIn("true_count", result)
        self.assertIn("false_count", result)
        
        # Test with only True values
        true_only = pd.Series([True, True, True])
        result = self.profiler._profile_boolean_field(true_only)
        self.assertEqual(result["true_count"], 3)
        self.assertEqual(result["false_count"], 0)

    def test_profile_date_field_edge_cases(self):
        """Test date field profiling edge cases."""
        # Test with valid date strings
        date_strings = pd.Series(["2023-01-01", "2023-12-31", "2023-06-15"])
        result = self.profiler._profile_date_field(date_strings)
        self.assertIn("min_date", result)
        self.assertIn("max_date", result)
        self.assertIn("date_format", result)
        
        # Test with unparseable dates
        bad_dates = pd.Series(["not-a-date", "invalid"])
        result = self.profiler._profile_date_field(bad_dates)
        self.assertEqual(result["date_format"], "unknown")

    def test_detect_string_pattern_edge_cases(self):
        """Test string pattern detection edge cases."""
        # Test with empty series
        empty_series = pd.Series([])
        result = self.profiler._detect_string_pattern(empty_series)
        self.assertIsNone(result)
        
        # Test with non-email strings
        non_email = pd.Series(["hello", "world"])
        result = self.profiler._detect_string_pattern(non_email)
        self.assertIsNone(result)
        
        # Test with mixed email/non-email
        mixed = pd.Series(["test@example.com", "not-an-email"])
        result = self.profiler._detect_string_pattern(mixed)
        self.assertIsNone(result)

    def test_detect_date_format_edge_cases(self):
        """Test date format detection edge cases."""
        # Test various date formats
        formats = [
            ("2023-01-01", "YYYY-MM-DD"),
            ("01/15/2023", "MM/DD/YYYY"),
            ("01-15-2023", "MM-DD-YYYY"),
            ("invalid-date", "unknown")
        ]
        
        for date_str, expected_format in formats:
            result = self.profiler._detect_date_format(date_str)
            self.assertEqual(result, expected_format)

    def test_create_summary_with_analyzed_rows(self):
        """Test summary creation with analyzed_rows parameter."""
        data = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"]
        })
        
        summary = self.profiler._create_summary(data, 100, 3)
        self.assertEqual(summary["total_rows"], 100)
        self.assertEqual(summary["analyzed_rows"], 3)
        self.assertEqual(summary["total_columns"], 2)
        self.assertIn("data_types", summary)

    def test_profile_data_with_max_rows_larger_dataset(self):
        """Test profiling with max_rows on a larger dataset."""
        # Create a larger dataset
        large_data = pd.DataFrame({
            "numbers": range(1000),
            "strings": [f"value_{i}" for i in range(1000)]
        })
        
        # Profile with max_rows limit
        profile = self.profiler.profile_data(large_data, max_rows=10)
        
        # Check that summary reflects both original and analyzed sizes
        summary = profile["summary"]
        self.assertEqual(summary["total_rows"], 1000)
        self.assertEqual(summary["analyzed_rows"], 10)

    def test_infer_field_type_priority(self):
        """Test field type inference priority order."""
        # Boolean should be detected before numeric
        bool_like_numbers = pd.Series([1, 0, 1, 0])
        field_type = self.profiler._infer_field_type(bool_like_numbers)
        self.assertEqual(field_type, "boolean")
        
        # Integer should be detected before float
        int_floats = pd.Series([1.0, 2.0, 3.0])
        field_type = self.profiler._infer_field_type(int_floats)
        self.assertEqual(field_type, "integer")

    def test_profile_field_type_specific_methods(self):
        """Test that profile_field calls the correct type-specific methods."""
        test_data = pd.Series([1, 2, 3])
        
        # Mock the type-specific method
        with patch.object(self.profiler, '_profile_integer_field', return_value={"test": "integer"}) as mock_int:
            with patch.object(self.profiler, '_infer_field_type', return_value="integer"):
                result = self.profiler._profile_field(test_data)
                mock_int.assert_called_once_with(test_data)
                self.assertIn("test", result)
                self.assertEqual(result["test"], "integer")


class TestDataProfilerErrorHandling(unittest.TestCase):
    """Test error handling and robustness of DataProfiler."""

    def setUp(self):
        """Set up test fixtures."""
        self.profiler = DataProfiler()

    def test_profile_integer_field_type_errors(self):
        """Test integer field profiling with type conversion errors."""
        # Create a series that will cause conversion issues
        problematic_series = pd.Series(["not_a_number", "also_not_a_number"])
        
        result = self.profiler._profile_integer_field(problematic_series)
        # Should return safe defaults
        expected = {"min_value": 0, "max_value": 0, "avg_value": 0.0}
        self.assertEqual(result, expected)

    def test_profile_float_field_type_errors(self):
        """Test float field profiling with type conversion errors."""
        problematic_series = pd.Series(["not_a_float", "also_not_a_float"])
        
        result = self.profiler._profile_float_field(problematic_series)
        expected = {"min_value": 0.0, "max_value": 0.0, "avg_value": 0.0}
        self.assertEqual(result, expected)

    def test_profile_string_field_type_errors(self):
        """Test string field profiling with type conversion errors."""
        # Test with None values that cause issues
        with patch.object(pd.Series, 'str', side_effect=Exception("String error")):
            problematic_series = pd.Series(["test"])
            result = self.profiler._profile_string_field(problematic_series)
            expected = {"min_length": 0, "max_length": 0, "avg_length": 0.0}
            self.assertEqual(result, expected)

    def test_profile_date_field_parse_errors(self):
        """Test date field profiling with parsing errors."""
        # Test with dates that cause parsing exceptions
        problematic_dates = pd.Series(["2023-99-99", "invalid-date"])
        
        result = self.profiler._profile_date_field(problematic_dates)
        self.assertEqual(result["date_format"], "unknown")

    def test_robustness_with_extreme_values(self):
        """Test profiler robustness with extreme values."""
        extreme_data = pd.DataFrame({
            "large_numbers": [1e20, 1e21, 1e22],
            "tiny_numbers": [1e-20, 1e-21, 1e-22],
            "empty_strings": ["", "", ""],
            "very_long_string": ["x" * 10000]
        })
        
        # Should not crash
        profile = self.profiler.profile_data(extreme_data)
        self.assertIn("summary", profile)
        self.assertIn("fields", profile)


if __name__ == "__main__":
    unittest.main()
