"""
Tests to improve coverage for adri.analysis.type_inference module.

These tests target specific uncovered lines to reach 100% coverage.
"""

import pytest
from adri.analysis.type_inference import TypeInference


class TestTypeInferenceCoverage:
    """Tests targeting specific uncovered lines in type_inference.py."""

    def test_is_boolean_type_exception_handling(self):
        """Test _is_boolean_type exception handling (lines 142-143)."""
        type_inference = TypeInference()
        
        # Create values that will cause an exception in the boolean type check
        # Using objects that can't be converted to string properly
        class BadObject:
            def __str__(self):
                raise ValueError("Cannot convert to string")
        
        bad_values = [BadObject(), BadObject()]
        
        # This should trigger the exception handling and return False
        result = type_inference._is_boolean_type(bad_values)
        assert result is False

    def test_is_float_type_exception_handling(self):
        """Test _is_float_type exception handling (lines 179-180)."""
        type_inference = TypeInference()
        
        # Test with objects that raise exceptions when converted to float
        class BadFloatObject:
            def __float__(self):
                raise ValueError("Cannot convert to float")
            def __str__(self):
                return "1.5"  # Looks like a float but raises exception
        
        bad_objects = [BadFloatObject()]
        result = type_inference._is_float_type(bad_objects)
        assert result is False
        
        # Test with complex objects that cause various exceptions
        class ComplexBadObject:
            def __float__(self):
                raise TypeError("Complex type error")
        
        complex_bad_objects = [ComplexBadObject()]
        result = type_inference._is_float_type(complex_bad_objects)
        assert result is False
        
        # Test with objects that raise AttributeError
        class AttributeErrorObject:
            def __getattribute__(self, name):
                if name == '__float__':
                    raise AttributeError("No float method")
                return super().__getattribute__(name)
        
        attr_error_objects = [AttributeErrorObject()]
        result = type_inference._is_float_type(attr_error_objects)
        assert result is False

    def test_is_boolean_type_with_valid_values(self):
        """Test _is_boolean_type with valid boolean values."""
        type_inference = TypeInference()
        
        # Test with valid boolean values
        boolean_values = ["true", "false"]
        result = type_inference._is_boolean_type(boolean_values)
        assert result is True
        
        # Test with numeric boolean values
        numeric_boolean_values = ["1", "0"]
        result = type_inference._is_boolean_type(numeric_boolean_values)
        assert result is True
        
        # Test with yes/no values
        yes_no_values = ["yes", "no"]
        result = type_inference._is_boolean_type(yes_no_values)
        assert result is True

    def test_is_float_type_with_valid_values(self):
        """Test _is_float_type with valid float values."""
        type_inference = TypeInference()
        
        # Test with valid float values
        float_values = ["1.5", "2.7", "3.14"]
        result = type_inference._is_float_type(float_values)
        assert result is True
        
        # Test with integer values (should also be valid floats)
        integer_values = ["1", "2", "3"]
        result = type_inference._is_float_type(integer_values)
        assert result is True

    def test_is_boolean_type_edge_cases(self):
        """Test _is_boolean_type with edge cases."""
        type_inference = TypeInference()
        
        # Test with mixed case (using valid boolean values)
        mixed_case_values = ["True", "FALSE"]
        result = type_inference._is_boolean_type(mixed_case_values)
        assert result is True
        
        # Test with single letter boolean values
        single_letter_values = ["t", "f"]
        result = type_inference._is_boolean_type(single_letter_values)
        assert result is True
        
        # Test with too many unique values (should return False)
        too_many_values = ["true", "false", "maybe"]
        result = type_inference._is_boolean_type(too_many_values)
        assert result is False
        
        # Test with non-boolean values
        non_boolean_values = ["apple", "banana"]
        result = type_inference._is_boolean_type(non_boolean_values)
        assert result is False

    def test_is_float_type_edge_cases(self):
        """Test _is_float_type with edge cases."""
        type_inference = TypeInference()
        
        # Test with scientific notation
        scientific_values = ["1.5e10", "2.3E-5"]
        result = type_inference._is_float_type(scientific_values)
        assert result is True
        
        # Test with negative values
        negative_values = ["-1.5", "-2.7"]
        result = type_inference._is_float_type(negative_values)
        assert result is True
        
        # Test with mixed valid and invalid (should return False)
        mixed_values = ["1.5", "not_a_number"]
        result = type_inference._is_float_type(mixed_values)
        assert result is False

    def test_comprehensive_type_inference_workflow(self):
        """Test the complete type inference workflow."""
        type_inference = TypeInference()
        
        # Test boolean inference
        boolean_data = ["true", "false", "true"]
        inferred_type = type_inference.infer_type(boolean_data)
        assert inferred_type == "boolean"
        
        # Test integer inference
        integer_data = ["1", "2", "3"]
        inferred_type = type_inference.infer_type(integer_data)
        assert inferred_type == "integer"
        
        # Test float inference
        float_data = ["1.5", "2.7", "3.14"]
        inferred_type = type_inference.infer_type(float_data)
        assert inferred_type == "float"
        
        # Test string inference (fallback)
        string_data = ["apple", "banana", "cherry"]
        inferred_type = type_inference.infer_type(string_data)
        assert inferred_type == "string"

    def test_exception_handling_in_complex_objects(self):
        """Test exception handling with complex objects that cause various errors."""
        type_inference = TypeInference()
        
        # Create an object that raises different types of exceptions
        class ComplexBadObject:
            def __init__(self, error_type):
                self.error_type = error_type
            
            def __str__(self):
                if self.error_type == "value_error":
                    raise ValueError("Value error in string conversion")
                elif self.error_type == "type_error":
                    raise TypeError("Type error in string conversion")
                else:
                    raise RuntimeError("Runtime error in string conversion")
            
            def __float__(self):
                raise ArithmeticError("Cannot convert to float")
        
        # Test boolean type inference with various exception types
        for error_type in ["value_error", "type_error", "runtime_error"]:
            bad_objects = [ComplexBadObject(error_type) for _ in range(3)]
            result = type_inference._is_boolean_type(bad_objects)
            assert result is False
        
        # Test float type inference with objects that can't be converted to float
        float_bad_objects = [ComplexBadObject("any") for _ in range(3)]
        result = type_inference._is_float_type(float_bad_objects)
        assert result is False
