"""
Comprehensive test coverage for adri.analysis.type_inference module.
Tests all methods and edge cases to achieve 85%+ coverage.
"""

import pytest
import pandas as pd
from unittest.mock import patch

from adri.analysis.type_inference import TypeInference


class TestTypeInference:
    """Test cases for TypeInference class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.inference = TypeInference()

    def test_init(self):
        """Test TypeInference initialization."""
        assert hasattr(self.inference, 'patterns')
        assert 'email' in self.inference.patterns
        assert 'phone' in self.inference.patterns
        assert 'url' in self.inference.patterns
        assert 'uuid' in self.inference.patterns
        assert 'date_iso' in self.inference.patterns
        assert 'date_us' in self.inference.patterns
        assert 'time' in self.inference.patterns

    def test_infer_type_empty_list(self):
        """Test type inference with empty list."""
        result = self.inference.infer_type([])
        assert result == "string"

    def test_infer_type_all_null_values(self):
        """Test type inference with all null values."""
        result = self.inference.infer_type([None, None, pd.NA])
        assert result == "string"

    def test_infer_type_boolean(self):
        """Test boolean type inference."""
        # Test with true/false strings
        result = self.inference.infer_type(["true", "false", "true"])
        assert result == "boolean"
        
        # Test with 1/0 values
        result = self.inference.infer_type([1, 0, 1, 0])
        assert result == "boolean"
        
        # Test with yes/no
        result = self.inference.infer_type(["yes", "no", "yes"])
        assert result == "boolean"
        
        # Test with t/f
        result = self.inference.infer_type(["t", "f", "t"])
        assert result == "boolean"

    def test_infer_type_integer(self):
        """Test integer type inference."""
        result = self.inference.infer_type([1, 2, 3, 4, 5])
        assert result == "integer"
        
        # Test with string integers
        result = self.inference.infer_type(["10", "20", "30"])
        assert result == "integer"
        
        # Test with float values that are actually integers
        result = self.inference.infer_type([1.0, 2.0, 3.0])
        assert result == "integer"

    def test_infer_type_float(self):
        """Test float type inference."""
        result = self.inference.infer_type([1.5, 2.7, 3.14])
        assert result == "float"
        
        # Test with string floats
        result = self.inference.infer_type(["1.5", "2.7", "3.14"])
        assert result == "float"

    def test_infer_type_date(self):
        """Test date type inference."""
        # Test ISO format
        result = self.inference.infer_type(["2023-01-01", "2023-02-15"])
        assert result == "date"
        
        # Test US format
        result = self.inference.infer_type(["01/15/2023", "02/20/2023"])
        assert result == "date"

    def test_infer_type_string_default(self):
        """Test that strings are returned as default."""
        result = self.inference.infer_type(["hello", "world", "test"])
        assert result == "string"
        
        # Test mixed types that don't fit other categories
        result = self.inference.infer_type(["hello", 123, "world"])
        assert result == "string"

    def test_infer_type_with_nulls_mixed(self):
        """Test type inference with null values mixed in."""
        result = self.inference.infer_type([1, 2, None, 3, pd.NA])
        assert result == "integer"
        
        result = self.inference.infer_type(["true", None, "false", pd.NA])
        assert result == "boolean"

    def test_infer_constraints_empty_values(self):
        """Test constraint inference with empty values."""
        result = self.inference.infer_constraints([], "string")
        assert result == {}
        
        result = self.inference.infer_constraints([None, pd.NA], "integer")
        assert result == {}

    def test_infer_constraints_integer(self):
        """Test constraint inference for integers."""
        values = [1, 5, 10, 15, 20]
        result = self.inference.infer_constraints(values, "integer")
        
        assert result["min_value"] == 1
        assert result["max_value"] == 20
        assert result["avg_value"] == 10.2

    def test_infer_constraints_float(self):
        """Test constraint inference for floats."""
        values = [1.5, 2.5, 3.5, 4.5]
        result = self.inference.infer_constraints(values, "float")
        
        assert result["min_value"] == 1.5
        assert result["max_value"] == 4.5
        assert result["avg_value"] == 3.0

    def test_infer_constraints_string(self):
        """Test constraint inference for strings."""
        values = ["hello", "world", "test"]
        result = self.inference.infer_constraints(values, "string")
        
        assert result["min_length"] == 4  # "test"
        assert result["max_length"] == 5  # "hello", "world"
        assert result["avg_length"] == 4.666666666666667

    def test_infer_constraints_string_with_pattern(self):
        """Test constraint inference for strings with detected pattern."""
        values = ["test@example.com", "user@domain.org"]
        result = self.inference.infer_constraints(values, "string")
        
        assert "pattern" in result
        assert result["pattern"] == "email"

    def test_infer_constraints_date(self):
        """Test constraint inference for dates."""
        # Test ISO format
        values = ["2023-01-01", "2023-02-15"]
        result = self.inference.infer_constraints(values, "date")
        assert result["format"] == "YYYY-MM-DD"
        
        # Test US format
        values = ["01/15/2023", "02/20/2023"]
        result = self.inference.infer_constraints(values, "date")
        assert result["format"] == "MM/DD/YYYY"
        
        # Test unknown format
        values = ["some-date-string"]
        result = self.inference.infer_constraints(values, "date")
        assert result["format"] == "unknown"

    def test_infer_constraints_date_empty(self):
        """Test date constraint inference with empty values."""
        result = self.inference.infer_constraints([], "date")
        assert result == {}

    def test_infer_constraints_unknown_type(self):
        """Test constraint inference for unknown data type."""
        values = ["test"]
        result = self.inference.infer_constraints(values, "unknown_type")
        assert result == {}

    def test_detect_pattern_empty_values(self):
        """Test pattern detection with empty values."""
        result = self.inference.detect_pattern([])
        assert result is None

    def test_detect_pattern_email(self):
        """Test email pattern detection."""
        values = ["test@example.com", "user@domain.org", "admin@site.net"]
        result = self.inference.detect_pattern(values)
        assert result == "email"

    def test_detect_pattern_phone(self):
        """Test phone pattern detection."""
        values = ["+1234567890", "9876543210"]
        result = self.inference.detect_pattern(values)
        assert result == "phone"

    def test_detect_pattern_url(self):
        """Test URL pattern detection."""
        values = ["https://example.com", "http://test.org"]
        result = self.inference.detect_pattern(values)
        assert result == "url"

    def test_detect_pattern_uuid(self):
        """Test UUID pattern detection."""
        values = ["123e4567-e89b-12d3-a456-426614174000", "550e8400-e29b-41d4-a716-446655440000"]
        result = self.inference.detect_pattern(values)
        assert result == "uuid"

    def test_detect_pattern_date_iso(self):
        """Test ISO date pattern detection."""
        values = ["2023-01-01", "2023-12-31"]
        result = self.inference.detect_pattern(values)
        assert result == "date_iso"

    def test_detect_pattern_date_us(self):
        """Test US date pattern detection."""
        values = ["01/01/2023", "12/31/2023"]
        result = self.inference.detect_pattern(values)
        assert result == "date_us"

    def test_detect_pattern_time(self):
        """Test time pattern detection."""
        values = ["12:30:45", "09:15:30"]
        result = self.inference.detect_pattern(values)
        assert result == "time"

    def test_detect_pattern_no_match(self):
        """Test pattern detection when no pattern matches."""
        values = ["random", "strings", "here"]
        result = self.inference.detect_pattern(values)
        assert result is None

    def test_detect_pattern_partial_match(self):
        """Test pattern detection when only some values match."""
        values = ["test@example.com", "not-an-email"]
        result = self.inference.detect_pattern(values)
        assert result is None

    def test_detect_pattern_with_empty_strings(self):
        """Test pattern detection with some empty strings."""
        values = ["test@example.com", "", "user@domain.org"]
        result = self.inference.detect_pattern(values)
        assert result == "email"

    def test_is_boolean_type_true_false(self):
        """Test boolean type detection with true/false."""
        assert self.inference._is_boolean_type(["true", "false"]) is True
        assert self.inference._is_boolean_type(["TRUE", "FALSE"]) is True

    def test_is_boolean_type_one_zero(self):
        """Test boolean type detection with 1/0."""
        assert self.inference._is_boolean_type([1, 0]) is True
        assert self.inference._is_boolean_type(["1", "0"]) is True

    def test_is_boolean_type_yes_no(self):
        """Test boolean type detection with yes/no."""
        assert self.inference._is_boolean_type(["yes", "no"]) is True
        assert self.inference._is_boolean_type(["y", "n"]) is True

    def test_is_boolean_type_single_value(self):
        """Test boolean type detection with single value."""
        assert self.inference._is_boolean_type(["true"]) is True
        assert self.inference._is_boolean_type(["1"]) is True

    def test_is_boolean_type_invalid(self):
        """Test boolean type detection with invalid values."""
        assert self.inference._is_boolean_type(["maybe", "perhaps"]) is False
        assert self.inference._is_boolean_type([1, 2, 3]) is False

    def test_is_boolean_type_exception(self):
        """Test boolean type detection with exception-causing values."""
        # Mock an exception in the try block
        with patch('builtins.set', side_effect=Exception("Test exception")):
            assert self.inference._is_boolean_type(["true", "false"]) is False

    def test_is_integer_type_valid(self):
        """Test integer type detection with valid integers."""
        assert self.inference._is_integer_type([1, 2, 3]) is True
        assert self.inference._is_integer_type(["1", "2", "3"]) is True
        assert self.inference._is_integer_type([1.0, 2.0, 3.0]) is True

    def test_is_integer_type_invalid(self):
        """Test integer type detection with non-integers."""
        assert self.inference._is_integer_type([1.5, 2.7, 3.14]) is False
        assert self.inference._is_integer_type(["hello", "world"]) is False

    def test_is_integer_type_exception(self):
        """Test integer type detection with exception-causing values."""
        assert self.inference._is_integer_type([object(), object()]) is False

    def test_is_float_type_valid(self):
        """Test float type detection with valid floats."""
        assert self.inference._is_float_type([1.5, 2.7, 3.14]) is True
        assert self.inference._is_float_type(["1.5", "2.7", "3.14"]) is True
        assert self.inference._is_float_type([1, 2, 3]) is True  # integers are also floats

    def test_is_float_type_invalid(self):
        """Test float type detection with non-floats."""
        assert self.inference._is_float_type(["hello", "world"]) is False

    def test_is_float_type_exception(self):
        """Test float type detection with exception-causing values."""
        assert self.inference._is_float_type([object(), object()]) is False

    def test_is_date_type_iso_format(self):
        """Test date type detection with ISO format."""
        assert self.inference._is_date_type(["2023-01-01", "2023-12-31"]) is True

    def test_is_date_type_us_format(self):
        """Test date type detection with US format."""
        assert self.inference._is_date_type(["01/01/2023", "12/31/2023"]) is True

    def test_is_date_type_mixed_valid_formats(self):
        """Test date type detection with mixed valid formats."""
        # Should return True if any of the first 5 values match date patterns
        assert self.inference._is_date_type(["2023-01-01", "not-a-date"]) is True

    def test_is_date_type_invalid(self):
        """Test date type detection with invalid dates."""
        assert self.inference._is_date_type(["not-a-date", "hello"]) is False

    def test_is_date_type_exception(self):
        """Test date type detection with exception-causing values."""
        with patch('builtins.str', side_effect=Exception("Test exception")):
            assert self.inference._is_date_type([object()]) is False

    def test_is_date_type_sample_size_limit(self):
        """Test that date type checking only samples first 5 values."""
        # Create a list where first value is a date, but 6th value would cause issues
        values = ["2023-01-01"] + ["not-date"] * 10
        assert self.inference._is_date_type(values) is True

    def test_infer_integer_constraints_calculation(self):
        """Test integer constraint calculation."""
        values = [10, 20, 30]
        result = self.inference._infer_integer_constraints(values)
        
        assert result["min_value"] == 10
        assert result["max_value"] == 30
        assert result["avg_value"] == 20.0

    def test_infer_float_constraints_calculation(self):
        """Test float constraint calculation."""
        values = [1.0, 2.0, 3.0]
        result = self.inference._infer_float_constraints(values)
        
        assert result["min_value"] == 1.0
        assert result["max_value"] == 3.0
        assert result["avg_value"] == 2.0

    def test_infer_string_constraints_without_pattern(self):
        """Test string constraint calculation without pattern."""
        values = ["short", "medium", "very long string"]
        result = self.inference._infer_string_constraints(values)
        
        assert result["min_length"] == 5  # "short"
        assert result["max_length"] == 16  # "very long string"
        assert result["avg_length"] == 9.0
        assert "pattern" not in result

    def test_infer_string_constraints_with_pattern(self):
        """Test string constraint calculation with detected pattern."""
        values = ["test@example.com", "user@domain.org"]
        result = self.inference._infer_string_constraints(values)
        
        assert "pattern" in result
        assert result["pattern"] == "email"
        assert result["min_length"] == 15  # "user@domain.org"
        assert result["max_length"] == 16  # "test@example.com"

    def test_integration_full_workflow(self):
        """Integration test for complete type inference workflow."""
        # Test integer workflow
        int_values = [1, 2, 3, 4, 5]
        data_type = self.inference.infer_type(int_values)
        constraints = self.inference.infer_constraints(int_values, data_type)
        
        assert data_type == "integer"
        assert constraints["min_value"] == 1
        assert constraints["max_value"] == 5
        
        # Test string with pattern workflow
        email_values = ["test@example.com", "user@domain.org"]
        data_type = self.inference.infer_type(email_values)
        constraints = self.inference.infer_constraints(email_values, data_type)
        pattern = self.inference.detect_pattern(email_values)
        
        assert data_type == "string"
        assert pattern == "email"
        assert constraints["pattern"] == "email"

    def test_edge_cases_mixed_data(self):
        """Test edge cases with mixed and complex data."""
        # Test with very mixed data types
        mixed_values = [1, "hello", 2.5, None, pd.NA, "true"]
        result = self.inference.infer_type(mixed_values)
        assert result == "string"  # Should default to string
        
        # Test constraints with mixed data
        constraints = self.inference.infer_constraints(mixed_values, "string")
        assert "min_length" in constraints
        assert "max_length" in constraints

    def test_pattern_matching_edge_cases(self):
        """Test pattern matching with edge cases."""
        # Test email with special characters
        emails = ["test+tag@example-domain.co.uk", "user.name@sub.domain.org"]
        result = self.inference.detect_pattern(emails)
        assert result == "email"
        
        # Test phone numbers with different formats
        phones = ["+12345678901", "1234567890"]
        result = self.inference.detect_pattern(phones)
        assert result == "phone"
