"""
Tests for the TypeInference module.
"""

import pytest
import pandas as pd

from adri.analysis.type_inference import TypeInference


class TestTypeInferenceInit:
    """Test TypeInference initialization."""

    def test_init_creates_patterns(self):
        """Test that initialization creates regex patterns."""
        inference = TypeInference()
        
        assert hasattr(inference, 'patterns')
        assert isinstance(inference.patterns, dict)
        
        # Check that expected patterns exist
        expected_patterns = [
            "email", "phone", "url", "uuid", 
            "date_iso", "date_us", "time"
        ]
        
        for pattern in expected_patterns:
            assert pattern in inference.patterns
            assert hasattr(inference.patterns[pattern], 'match')


class TestInferType:
    """Test the infer_type method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.inference = TypeInference()

    def test_infer_type_empty_list(self):
        """Test type inference with empty list."""
        result = self.inference.infer_type([])
        assert result == "string"

    def test_infer_type_all_none(self):
        """Test type inference with all None values."""
        result = self.inference.infer_type([None, None, None])
        assert result == "string"

    def test_infer_type_all_nan(self):
        """Test type inference with all NaN values."""
        result = self.inference.infer_type([pd.NA, pd.NaT, float('nan')])
        assert result == "string"

    def test_infer_type_boolean_true_false(self):
        """Test boolean type inference with true/false."""
        result = self.inference.infer_type(["true", "false", "true"])
        assert result == "boolean"

    def test_infer_type_boolean_1_0(self):
        """Test boolean type inference with 1/0."""
        result = self.inference.infer_type(["1", "0", "1", "0"])
        assert result == "boolean"

    def test_infer_type_boolean_yes_no(self):
        """Test boolean type inference with yes/no."""
        result = self.inference.infer_type(["yes", "no", "yes"])
        assert result == "boolean"

    def test_infer_type_boolean_mixed_case(self):
        """Test boolean type inference with mixed case."""
        result = self.inference.infer_type(["True", "FALSE", "true"])
        assert result == "boolean"

    def test_infer_type_integer(self):
        """Test integer type inference."""
        result = self.inference.infer_type([1, 2, 3, 4, 5])
        assert result == "integer"

    def test_infer_type_integer_strings(self):
        """Test integer type inference with string numbers."""
        result = self.inference.infer_type(["1", "2", "3", "4"])
        assert result == "integer"

    def test_infer_type_float(self):
        """Test float type inference."""
        result = self.inference.infer_type([1.5, 2.7, 3.14])
        assert result == "float"

    def test_infer_type_float_strings(self):
        """Test float type inference with string floats."""
        result = self.inference.infer_type(["1.5", "2.7", "3.14"])
        assert result == "float"

    def test_infer_type_date_iso(self):
        """Test date type inference with ISO format."""
        result = self.inference.infer_type(["2023-01-01", "2023-12-31"])
        assert result == "date"

    def test_infer_type_date_us(self):
        """Test date type inference with US format."""
        result = self.inference.infer_type(["01/01/2023", "12/31/2023"])
        assert result == "date"

    def test_infer_type_string_default(self):
        """Test string type inference as default."""
        result = self.inference.infer_type(["hello", "world", "test"])
        assert result == "string"

    def test_infer_type_mixed_with_none(self):
        """Test type inference with mixed values including None."""
        result = self.inference.infer_type([1, 2, None, 3, 4])
        assert result == "integer"

    def test_infer_type_priority_boolean_over_integer(self):
        """Test that boolean has priority over integer for 1/0."""
        result = self.inference.infer_type(["1", "0"])
        assert result == "boolean"

    def test_infer_type_integer_over_float_when_whole_numbers(self):
        """Test that integer is chosen over float for whole numbers."""
        result = self.inference.infer_type([1.0, 2.0, 3.0])
        assert result == "integer"


class TestInferConstraints:
    """Test the infer_constraints method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.inference = TypeInference()

    def test_infer_constraints_empty_list(self):
        """Test constraint inference with empty list."""
        result = self.inference.infer_constraints([], "string")
        assert result == {}

    def test_infer_constraints_all_none(self):
        """Test constraint inference with all None values."""
        result = self.inference.infer_constraints([None, None], "string")
        assert result == {}

    def test_infer_constraints_integer(self):
        """Test constraint inference for integers."""
        values = [1, 5, 3, 9, 2]
        result = self.inference.infer_constraints(values, "integer")
        
        assert "min_value" in result
        assert "max_value" in result
        assert "avg_value" in result
        assert result["min_value"] == 1
        assert result["max_value"] == 9
        assert result["avg_value"] == 4.0

    def test_infer_constraints_float(self):
        """Test constraint inference for floats."""
        values = [1.5, 2.7, 3.14]
        result = self.inference.infer_constraints(values, "float")
        
        assert "min_value" in result
        assert "max_value" in result
        assert "avg_value" in result
        assert result["min_value"] == 1.5
        assert result["max_value"] == 3.14

    def test_infer_constraints_string(self):
        """Test constraint inference for strings."""
        values = ["hello", "world", "test"]
        result = self.inference.infer_constraints(values, "string")
        
        assert "min_length" in result
        assert "max_length" in result
        assert "avg_length" in result
        assert result["min_length"] == 4  # "test"
        assert result["max_length"] == 5  # "hello", "world"

    def test_infer_constraints_string_with_pattern(self):
        """Test constraint inference for strings with pattern."""
        values = ["test@example.com", "user@domain.org"]
        result = self.inference.infer_constraints(values, "string")
        
        assert "pattern" in result
        assert result["pattern"] == "email"

    def test_infer_constraints_date(self):
        """Test constraint inference for dates."""
        values = ["2023-01-01", "2023-12-31"]
        result = self.inference.infer_constraints(values, "date")
        
        assert "format" in result
        assert result["format"] == "YYYY-MM-DD"

    def test_infer_constraints_date_us_format(self):
        """Test constraint inference for US date format."""
        values = ["01/01/2023", "12/31/2023"]
        result = self.inference.infer_constraints(values, "date")
        
        assert "format" in result
        assert result["format"] == "MM/DD/YYYY"

    def test_infer_constraints_unknown_type(self):
        """Test constraint inference for unknown type."""
        values = ["test", "data"]
        result = self.inference.infer_constraints(values, "unknown_type")
        
        assert result == {}


class TestDetectPattern:
    """Test the detect_pattern method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.inference = TypeInference()

    def test_detect_pattern_empty_list(self):
        """Test pattern detection with empty list."""
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
        values = [
            "123e4567-e89b-12d3-a456-426614174000",
            "987fcdeb-51d2-43a1-b123-456789abcdef"
        ]
        result = self.inference.detect_pattern(values)
        assert result == "uuid"

    def test_detect_pattern_date_iso(self):
        """Test ISO date pattern detection."""
        values = ["2023-01-01", "2023-12-31", "2024-06-15"]
        result = self.inference.detect_pattern(values)
        assert result == "date_iso"

    def test_detect_pattern_date_us(self):
        """Test US date pattern detection."""
        values = ["01/01/2023", "12/31/2023", "06/15/2024"]
        result = self.inference.detect_pattern(values)
        assert result == "date_us"

    def test_detect_pattern_time(self):
        """Test time pattern detection."""
        values = ["12:30:45", "09:15:00", "23:59:59"]
        result = self.inference.detect_pattern(values)
        assert result == "time"

    def test_detect_pattern_no_match(self):
        """Test pattern detection with no matching pattern."""
        values = ["random", "text", "values"]
        result = self.inference.detect_pattern(values)
        assert result is None

    def test_detect_pattern_partial_match(self):
        """Test pattern detection with partial match."""
        values = ["test@example.com", "not_an_email", "user@domain.org"]
        result = self.inference.detect_pattern(values)
        assert result is None

    def test_detect_pattern_with_empty_values(self):
        """Test pattern detection with some empty values."""
        values = ["test@example.com", "", "user@domain.org"]
        result = self.inference.detect_pattern(values)
        assert result == "email"


class TestPrivateMethods:
    """Test private helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.inference = TypeInference()

    def test_is_boolean_type_true_false(self):
        """Test boolean type detection with true/false."""
        result = self.inference._is_boolean_type(["true", "false"])
        assert result is True

    def test_is_boolean_type_1_0(self):
        """Test boolean type detection with 1/0."""
        result = self.inference._is_boolean_type([1, 0])
        assert result is True

    def test_is_boolean_type_yes_no(self):
        """Test boolean type detection with yes/no."""
        result = self.inference._is_boolean_type(["yes", "no"])
        assert result is True

    def test_is_boolean_type_mixed_case(self):
        """Test boolean type detection with mixed case."""
        result = self.inference._is_boolean_type(["True", "FALSE"])
        assert result is True

    def test_is_boolean_type_single_value(self):
        """Test boolean type detection with single value."""
        result = self.inference._is_boolean_type(["true"])
        assert result is True

    def test_is_boolean_type_non_boolean(self):
        """Test boolean type detection with non-boolean values."""
        result = self.inference._is_boolean_type(["hello", "world"])
        assert result is False

    def test_is_boolean_type_too_many_unique(self):
        """Test boolean type detection with too many unique values."""
        result = self.inference._is_boolean_type(["true", "false", "maybe"])
        assert result is False

    def test_is_boolean_type_exception_handling(self):
        """Test boolean type detection exception handling."""
        result = self.inference._is_boolean_type([object(), object()])
        assert result is False

    def test_is_integer_type_valid(self):
        """Test integer type detection with valid integers."""
        result = self.inference._is_integer_type([1, 2, 3])
        assert result is True

    def test_is_integer_type_string_integers(self):
        """Test integer type detection with string integers."""
        result = self.inference._is_integer_type(["1", "2", "3"])
        assert result is True

    def test_is_integer_type_float_whole_numbers(self):
        """Test integer type detection with float whole numbers."""
        result = self.inference._is_integer_type([1.0, 2.0, 3.0])
        assert result is True

    def test_is_integer_type_with_decimals(self):
        """Test integer type detection with decimal numbers."""
        result = self.inference._is_integer_type([1.5, 2.7])
        assert result is False

    def test_is_integer_type_invalid(self):
        """Test integer type detection with invalid values."""
        result = self.inference._is_integer_type(["hello", "world"])
        assert result is False

    def test_is_float_type_valid(self):
        """Test float type detection with valid floats."""
        result = self.inference._is_float_type([1.5, 2.7, 3.14])
        assert result is True

    def test_is_float_type_integers(self):
        """Test float type detection with integers."""
        result = self.inference._is_float_type([1, 2, 3])
        assert result is True

    def test_is_float_type_string_numbers(self):
        """Test float type detection with string numbers."""
        result = self.inference._is_float_type(["1.5", "2.7"])
        assert result is True

    def test_is_float_type_invalid(self):
        """Test float type detection with invalid values."""
        result = self.inference._is_float_type(["hello", "world"])
        assert result is False

    def test_is_float_type_exception_objects(self):
        """Test float type detection with objects that raise exceptions."""
        class BadFloatObject:
            def __float__(self):
                raise ValueError("Cannot convert to float")
        
        result = self.inference._is_float_type([BadFloatObject()])
        assert result is False

    def test_is_date_type_iso_format(self):
        """Test date type detection with ISO format."""
        result = self.inference._is_date_type(["2023-01-01", "2023-12-31"])
        assert result is True

    def test_is_date_type_us_format(self):
        """Test date type detection with US format."""
        result = self.inference._is_date_type(["01/01/2023", "12/31/2023"])
        assert result is True

    def test_is_date_type_mixed_formats(self):
        """Test date type detection with mixed formats."""
        result = self.inference._is_date_type(["2023-01-01", "01/01/2023"])
        assert result is True

    def test_is_date_type_invalid(self):
        """Test date type detection with invalid dates."""
        result = self.inference._is_date_type(["hello", "world"])
        assert result is False

    def test_is_date_type_exception_handling(self):
        """Test date type detection exception handling."""
        result = self.inference._is_date_type([object(), object()])
        assert result is False

    def test_infer_integer_constraints(self):
        """Test integer constraint inference."""
        values = [1, 5, 3]
        result = self.inference._infer_integer_constraints(values)
        
        assert result["min_value"] == 1
        assert result["max_value"] == 5
        assert result["avg_value"] == 3.0

    def test_infer_float_constraints(self):
        """Test float constraint inference."""
        values = [1.5, 2.5, 3.5]
        result = self.inference._infer_float_constraints(values)
        
        assert result["min_value"] == 1.5
        assert result["max_value"] == 3.5
        assert result["avg_value"] == 2.5

    def test_infer_string_constraints(self):
        """Test string constraint inference."""
        values = ["hello", "world"]
        result = self.inference._infer_string_constraints(values)
        
        assert result["min_length"] == 5
        assert result["max_length"] == 5
        assert result["avg_length"] == 5.0

    def test_infer_string_constraints_with_pattern(self):
        """Test string constraint inference with pattern."""
        values = ["test@example.com", "user@domain.org"]
        result = self.inference._infer_string_constraints(values)
        
        assert "pattern" in result
        assert result["pattern"] == "email"

    def test_infer_date_constraints_iso(self):
        """Test date constraint inference with ISO format."""
        values = ["2023-01-01", "2023-12-31"]
        result = self.inference._infer_date_constraints(values)
        
        assert result["format"] == "YYYY-MM-DD"

    def test_infer_date_constraints_us(self):
        """Test date constraint inference with US format."""
        values = ["01/01/2023", "12/31/2023"]
        result = self.inference._infer_date_constraints(values)
        
        assert result["format"] == "MM/DD/YYYY"

    def test_infer_date_constraints_unknown(self):
        """Test date constraint inference with unknown format."""
        values = ["some random date"]
        result = self.inference._infer_date_constraints(values)
        
        assert result["format"] == "unknown"

    def test_infer_date_constraints_empty(self):
        """Test date constraint inference with empty values."""
        result = self.inference._infer_date_constraints([])
        assert result == {}


class TestTypeInferenceIntegration:
    """Integration tests for TypeInference."""

    def setup_method(self):
        """Set up test fixtures."""
        self.inference = TypeInference()

    def test_full_workflow_integer(self):
        """Test complete workflow for integer data."""
        values = [1, 2, 3, 4, 5]
        
        # Infer type
        data_type = self.inference.infer_type(values)
        assert data_type == "integer"
        
        # Infer constraints
        constraints = self.inference.infer_constraints(values, data_type)
        assert constraints["min_value"] == 1
        assert constraints["max_value"] == 5

    def test_full_workflow_email_strings(self):
        """Test complete workflow for email string data."""
        values = ["test@example.com", "user@domain.org", "admin@site.net"]
        
        # Infer type
        data_type = self.inference.infer_type(values)
        assert data_type == "string"
        
        # Infer constraints
        constraints = self.inference.infer_constraints(values, data_type)
        assert constraints["pattern"] == "email"
        
        # Detect pattern directly
        pattern = self.inference.detect_pattern(values)
        assert pattern == "email"

    def test_full_workflow_mixed_data_with_nulls(self):
        """Test complete workflow with mixed data including nulls."""
        values = [1, 2, None, 3, pd.NA, 4]
        
        # Infer type (should ignore nulls)
        data_type = self.inference.infer_type(values)
        assert data_type == "integer"
        
        # Infer constraints (should ignore nulls)
        constraints = self.inference.infer_constraints(values, data_type)
        assert constraints["min_value"] == 1
        assert constraints["max_value"] == 4

    def test_edge_case_single_value(self):
        """Test edge case with single value."""
        values = ["test@example.com"]
        
        data_type = self.inference.infer_type(values)
        assert data_type == "string"
        
        constraints = self.inference.infer_constraints(values, data_type)
        assert constraints["pattern"] == "email"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
