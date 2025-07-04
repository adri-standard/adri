"""
Tests to cover exception handling paths in DataProfiler.

These tests specifically target the uncovered exception handling blocks
to achieve 99%+ coverage.
"""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from adri.analysis.data_profiler import DataProfiler


class TestDataProfilerExceptionCoverage(unittest.TestCase):
    """Test exception handling paths in DataProfiler."""

    def setUp(self):
        """Set up test fixtures."""
        self.profiler = DataProfiler()

    def test_profile_integer_field_value_error(self):
        """Test ValueError handling in _profile_integer_field."""
        # Create a series that will trigger ValueError in conversion
        problematic_series = pd.Series([1, 2, 3, 4, 5])
        
        # Mock int() to raise ValueError during the conversion inside try block
        with patch('builtins.int', side_effect=ValueError("Conversion failed")):
            result = self.profiler._profile_integer_field(problematic_series)
            
            # Should return safe defaults
            self.assertEqual(result["min_value"], 0)
            self.assertEqual(result["max_value"], 0)
            self.assertEqual(result["avg_value"], 0.0)

    def test_profile_integer_field_type_error(self):
        """Test TypeError handling in _profile_integer_field."""
        # Create a series that will trigger TypeError
        problematic_series = pd.Series([1, 2, 3, 4, 5])
        
        # Mock min() to raise TypeError
        with patch.object(pd.Series, 'min', side_effect=TypeError("Type error")):
            result = self.profiler._profile_integer_field(problematic_series)
            
            # Should return safe defaults
            self.assertEqual(result["min_value"], 0)
            self.assertEqual(result["max_value"], 0)
            self.assertEqual(result["avg_value"], 0.0)

    def test_profile_integer_field_overflow_error(self):
        """Test OverflowError handling in _profile_integer_field."""
        # Create a series that will trigger OverflowError
        problematic_series = pd.Series([1, 2, 3, 4, 5])
        
        # Mock int() to raise OverflowError
        with patch('builtins.int', side_effect=OverflowError("Overflow error")):
            result = self.profiler._profile_integer_field(problematic_series)
            
            # Should return safe defaults
            self.assertEqual(result["min_value"], 0)
            self.assertEqual(result["max_value"], 0)
            self.assertEqual(result["avg_value"], 0.0)

    def test_profile_float_field_value_error(self):
        """Test ValueError handling in _profile_float_field."""
        # Create a series that will trigger ValueError
        problematic_series = pd.Series([1.5, 2.5, 3.5, 4.5, 5.5])
        
        # Mock float() to raise ValueError during the conversion inside try block
        with patch('builtins.float', side_effect=ValueError("Conversion failed")):
            result = self.profiler._profile_float_field(problematic_series)
            
            # Should return safe defaults
            self.assertEqual(result["min_value"], 0.0)
            self.assertEqual(result["max_value"], 0.0)
            self.assertEqual(result["avg_value"], 0.0)

    def test_profile_float_field_type_error(self):
        """Test TypeError handling in _profile_float_field."""
        # Create a series that will trigger TypeError
        problematic_series = pd.Series([1.5, 2.5, 3.5, 4.5, 5.5])
        
        # Mock float() to raise TypeError
        with patch('builtins.float', side_effect=TypeError("Type error")):
            result = self.profiler._profile_float_field(problematic_series)
            
            # Should return safe defaults
            self.assertEqual(result["min_value"], 0.0)
            self.assertEqual(result["max_value"], 0.0)
            self.assertEqual(result["avg_value"], 0.0)

    def test_profile_float_field_overflow_error(self):
        """Test OverflowError handling in _profile_float_field."""
        # Create a series that will trigger OverflowError
        problematic_series = pd.Series([1.5, 2.5, 3.5, 4.5, 5.5])
        
        # Mock max() to raise OverflowError
        with patch.object(pd.Series, 'max', side_effect=OverflowError("Overflow error")):
            result = self.profiler._profile_float_field(problematic_series)
            
            # Should return safe defaults
            self.assertEqual(result["min_value"], 0.0)
            self.assertEqual(result["max_value"], 0.0)
            self.assertEqual(result["avg_value"], 0.0)

    def test_profile_string_field_special_values_handling(self):
        """Test special values handling in _profile_string_field that returns defaults."""
        # Create a series that will have special values after processing
        problematic_series = pd.Series(["test1", "test2", "test3"])
        
        # Mock str.len() to return series with NaN values
        mock_lengths = pd.Series([np.nan, np.nan, np.nan])
        with patch.object(pd.core.strings.accessor.StringMethods, 'len', return_value=mock_lengths):
            result = self.profiler._profile_string_field(problematic_series)
            
            # Should return safe defaults when all lengths are NaN
            self.assertEqual(result["min_length"], 0)
            self.assertEqual(result["max_length"], 0)
            self.assertEqual(result["avg_length"], 0.0)

    def test_profile_string_field_value_error(self):
        """Test ValueError handling in _profile_string_field."""
        # Create a series that will trigger ValueError
        problematic_series = pd.Series(["test1", "test2", "test3"])
        
        # Mock the min() method to raise ValueError after lengths are calculated
        with patch.object(pd.Series, 'min', side_effect=ValueError("Conversion failed")):
            result = self.profiler._profile_string_field(problematic_series)
            
            # Should return safe defaults
            self.assertEqual(result["min_length"], 0)
            self.assertEqual(result["max_length"], 0)
            self.assertEqual(result["avg_length"], 0.0)

    def test_profile_string_field_type_error(self):
        """Test TypeError handling in _profile_string_field."""
        # Create a series that will trigger TypeError
        problematic_series = pd.Series(["test1", "test2", "test3"])
        
        # Mock float() to raise TypeError
        with patch('builtins.float', side_effect=TypeError("Type error")):
            result = self.profiler._profile_string_field(problematic_series)
            
            # Should return safe defaults
            self.assertEqual(result["min_length"], 0)
            self.assertEqual(result["max_length"], 0)
            self.assertEqual(result["avg_length"], 0.0)

    def test_profile_string_field_overflow_error(self):
        """Test OverflowError handling in _profile_string_field."""
        # Create a series that will trigger OverflowError
        problematic_series = pd.Series(["test1", "test2", "test3"])
        
        # Mock mean() to raise OverflowError
        with patch.object(pd.Series, 'mean', side_effect=OverflowError("Overflow error")):
            result = self.profiler._profile_string_field(problematic_series)
            
            # Should return safe defaults
            self.assertEqual(result["min_length"], 0)
            self.assertEqual(result["max_length"], 0)
            self.assertEqual(result["avg_length"], 0.0)

    def test_profile_date_field_exception_handling(self):
        """Test exception handling in _profile_date_field."""
        # Create a series that will trigger exception in date parsing
        problematic_series = pd.Series(["2023-01-01", "2023-02-01", "2023-03-01"])
        
        # Mock pd.to_datetime to raise exception
        with patch('pandas.to_datetime', side_effect=Exception("Date parsing failed")):
            result = self.profiler._profile_date_field(problematic_series)
            
            # Should return safe defaults
            self.assertEqual(result["date_format"], "unknown")

    def test_comprehensive_exception_scenarios(self):
        """Test comprehensive exception scenarios across multiple methods."""
        # Create test data that could trigger various exceptions
        test_data = pd.DataFrame({
            "integers": [1, 2, 3, 4, 5],
            "floats": [1.1, 2.2, 3.3, 4.4, 5.5],
            "strings": ["a", "b", "c", "d", "e"],
            "dates": ["2023-01-01", "2023-02-01", "2023-03-01", "2023-04-01", "2023-05-01"]
        })
        
        # Mock various pandas operations to raise exceptions
        with patch('pandas.to_numeric', side_effect=ValueError("Numeric conversion failed")):
            with patch.object(pd.core.strings.accessor.StringMethods, 'len', side_effect=TypeError("String length failed")):
                with patch('pandas.to_datetime', side_effect=Exception("Date parsing failed")):
                    profile = self.profiler.profile_data(test_data)
                    
                    # Should still return a valid profile structure
                    self.assertIn("summary", profile)
                    self.assertIn("fields", profile)
                    
                    # All fields should have safe default values
                    for field_name, field_info in profile["fields"].items():
                        self.assertIn("type", field_info)
                        self.assertIn("nullable", field_info)


if __name__ == "__main__":
    unittest.main()
