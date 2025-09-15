"""
Additional comprehensive tests for StandardGenerator to achieve 85%+ coverage.
Tests edge cases and exception paths to cover missing lines.
"""

import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from datetime import datetime

from adri.analysis.standard_generator import StandardGenerator


class TestStandardGeneratorEdgeCases(unittest.TestCase):
    """Test edge cases and exception paths in StandardGenerator."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = StandardGenerator()
        
        self.generation_config = {
            "default_thresholds": {
                "completeness_min": 85,
                "validity_min": 90,
                "consistency_min": 80,
                "freshness_max_age": "7d",
                "plausibility_outlier_threshold": 3.0,
            }
        }

    def test_generate_standard_serialization_fallback(self):
        """Test fallback behavior when serialization fails."""
        # Create a profile with objects that might cause serialization issues
        problematic_profile = {
            "summary": {"total_rows": 5, "total_columns": 3},
            "fields": {
                "test_field": {
                    "type": "string",
                    "nullable": False,
                }
            }
        }
        
        # Mock _convert_to_serializable to return non-dict to trigger fallback
        with patch.object(self.generator, '_convert_to_serializable', return_value="not a dict"):
            result = self.generator.generate_standard(
                data_profile=problematic_profile,
                data_name="test_data",
                generation_config=self.generation_config
            )
            
            # Should fallback to empty dict (line 57)
            self.assertEqual(result, {})

    def test_generate_standards_metadata_complex_name_cleaning(self):
        """Test complex name cleaning in standards metadata."""
        # Test with special characters and multiple hyphens
        standard = self.generator.generate_standard(
            data_profile={"summary": {"total_rows": 1, "total_columns": 1}, "fields": {}},
            data_name="complex-_-name--with___special--chars",
            generation_config=self.generation_config
        )
        
        # Check ID cleaning (line 68) - should clean repeated separators
        standards_meta = standard["standards"]
        self.assertNotIn("--", standards_meta["id"])
        # The cleaning replaces multiple hyphens but may not catch all underscore patterns
        self.assertIn("complex", standards_meta["id"])
        self.assertTrue(standards_meta["id"].endswith("-v1"))

    def test_calculate_overall_minimum_high_nullable_ratio(self):
        """Test overall minimum calculation with high nullable field ratio."""
        # Create profile with >30% nullable fields to trigger adjustment
        profile_high_nullable = {
            "summary": {"total_rows": 5, "total_columns": 5},
            "fields": {
                "field1": {"type": "string", "nullable": False},
                "field2": {"type": "string", "nullable": True},  # 20%
                "field3": {"type": "string", "nullable": True},  # 40% 
                "field4": {"type": "string", "nullable": True},  # 60%
                "field5": {"type": "string", "nullable": True},  # 80% nullable
            }
        }
        
        result = self.generator._calculate_overall_minimum(
            profile_high_nullable, 
            self.generation_config["default_thresholds"]
        )
        
        # Should apply -5.0 adjustment for high nullable ratio (line 112)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 60.0)
        self.assertLessEqual(result, 95.0)

    def test_generate_float_constraints_no_min_value(self):
        """Test float constraints when min_value is not in profile."""
        field_profile = {
            "type": "float",
            "nullable": False,
            "max_value": 1000.0
            # No min_value key to test the missing case
        }
        
        constraints = self.generator._generate_float_constraints(field_profile)
        
        # Should not add min_value constraint (covers lines 195-196)
        self.assertNotIn("min_value", constraints)

    def test_generate_float_constraints_negative_min_value(self):
        """Test float constraints with negative minimum value."""
        field_profile = {
            "type": "float",
            "nullable": False,
            "min_value": -100.5,
            "max_value": 1000.0
        }
        
        constraints = self.generator._generate_float_constraints(field_profile)
        
        # Should preserve negative min_value (covers else branch)
        self.assertEqual(constraints["min_value"], -100.5)

    def test_generate_string_constraints_no_pattern(self):
        """Test string constraints when no pattern is detected."""
        field_profile = {
            "type": "string",
            "nullable": False,
            "min_length": 5,
            "max_length": 20
            # No pattern key
        }
        
        constraints = self.generator._generate_string_constraints(field_profile)
        
        # Should not add pattern constraint (covers lines 231-236)
        self.assertNotIn("pattern", constraints)
        self.assertIn("min_length", constraints)
        self.assertIn("max_length", constraints)

    def test_generate_string_constraints_non_email_pattern(self):
        """Test string constraints with non-email pattern."""
        field_profile = {
            "type": "string",
            "nullable": False,
            "min_length": 5,
            "max_length": 20,
            "pattern": "^[A-Z]{3}[0-9]{3}$"  # Not email pattern
        }
        
        constraints = self.generator._generate_string_constraints(field_profile)
        
        # Should preserve original pattern (covers else branch in pattern handling)
        self.assertEqual(constraints["pattern"], "^[A-Z]{3}[0-9]{3}$")

    def test_generate_date_constraints_unknown_format(self):
        """Test date constraints when format is unknown."""
        field_profile = {
            "type": "date",
            "nullable": False,
            "date_format": "unknown"
        }
        
        constraints = self.generator._generate_date_constraints(field_profile)
        
        # Should not add format constraint when unknown (line 252)
        self.assertNotIn("format", constraints)

    def test_generate_date_constraints_no_format(self):
        """Test date constraints when no date_format key exists."""
        field_profile = {
            "type": "date",
            "nullable": False
            # No date_format key
        }
        
        constraints = self.generator._generate_date_constraints(field_profile)
        
        # Should not add format constraint (covers missing key case)
        self.assertNotIn("format", constraints)

    def test_generate_metadata_no_summary(self):
        """Test metadata generation when summary is missing."""
        profile_no_summary = {
            "fields": {
                "test_field": {"type": "string", "nullable": False}
            }
            # No summary key
        }
        
        metadata = self.generator._generate_metadata("test_data", profile_no_summary)
        
        # Should handle missing summary gracefully (line 282)
        self.assertEqual(metadata["source_data_rows"], 0)
        self.assertEqual(metadata["source_data_columns"], 0)
        self.assertIn("tags", metadata)

    def test_convert_to_serializable_numpy_types(self):
        """Test conversion of various numpy types to serializable formats."""
        # Test numpy integer
        np_int = np.int64(42)
        result = self.generator._convert_to_serializable(np_int)
        self.assertEqual(result, 42)
        self.assertIsInstance(result, int)

        # Test numpy float  
        np_float = np.float64(3.14)
        result = self.generator._convert_to_serializable(np_float)
        self.assertEqual(result, 3.14)
        self.assertIsInstance(result, float)

        # Test numpy array
        np_array = np.array([1, 2, 3])
        result = self.generator._convert_to_serializable(np_array)
        self.assertEqual(result, [1, 2, 3])
        self.assertIsInstance(result, list)

    def test_convert_to_serializable_numpy_scalar_with_item(self):
        """Test conversion of numpy scalar with item() method."""
        # Create numpy scalar that has item() method
        np_scalar = np.array(42).item()
        
        # Mock an object that has item() method  
        mock_obj = MagicMock()
        mock_obj.item.return_value = 123
        
        result = self.generator._convert_to_serializable(mock_obj)
        self.assertEqual(result, 123)

    def test_convert_to_serializable_object_with_tolist(self):
        """Test conversion of object with tolist() method."""
        # Mock an object that has tolist() method but NOT item() method
        mock_obj = MagicMock()
        mock_obj.tolist.return_value = [1, 2, 3]
        # Ensure it doesn't have item method
        del mock_obj.item
        
        result = self.generator._convert_to_serializable(mock_obj)
        self.assertEqual(result, [1, 2, 3])

    def test_convert_to_serializable_nested_structures(self):
        """Test conversion of nested dictionaries and lists with numpy objects."""
        nested_data = {
            "integers": [np.int32(1), np.int64(2)],
            "floats": {"pi": np.float32(3.14), "e": np.float64(2.718)},
            "arrays": np.array([4, 5, 6]),
            "mixed": [
                {"value": np.int16(42)},
                [np.float32(1.5), np.int8(7)]
            ]
        }
        
        result = self.generator._convert_to_serializable(nested_data)
        
        # Verify all numpy types are converted
        self.assertEqual(result["integers"], [1, 2])
        self.assertEqual(result["floats"]["pi"], 3.140000104904175)  # float32 precision
        self.assertEqual(result["floats"]["e"], 2.718)
        self.assertEqual(result["arrays"], [4, 5, 6])
        self.assertEqual(result["mixed"][0]["value"], 42)
        self.assertEqual(result["mixed"][1], [1.5, 7])

    def test_convert_to_serializable_regular_objects(self):
        """Test conversion of regular Python objects (no conversion needed)."""
        regular_data = {
            "string": "hello",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }
        
        result = self.generator._convert_to_serializable(regular_data)
        
        # Should return unchanged
        self.assertEqual(result, regular_data)

    def test_integer_constraints_very_large_range(self):
        """Test integer constraints with values outside ID/age ranges."""
        field_profile = {
            "type": "integer",
            "nullable": False,
            "min_value": -999999,
            "max_value": 999999999
        }
        
        constraints = self.generator._generate_integer_constraints(field_profile)
        
        # Should fall through to general numeric field handling
        self.assertEqual(constraints["min_value"], -999999)
        self.assertEqual(constraints["max_value"], 999999999)

    def test_field_description_various_types(self):
        """Test field description generation for various field types."""
        # Test all type descriptions
        types_to_test = ["integer", "float", "string", "boolean", "date", "unknown_type"]
        
        for field_type in types_to_test:
            description = self.generator._generate_field_description("test_field", field_type)
            self.assertIsInstance(description, str)
            self.assertIn("Test Field", description)

    def test_generate_metadata_tag_detection(self):
        """Test metadata tag detection for various field name patterns."""
        # Profile with fields that should trigger different tags
        profile_with_tags = {
            "summary": {"total_rows": 10, "total_columns": 6},
            "fields": {
                "customer_name": {"type": "string"},
                "user_email": {"type": "string"},
                "account_balance": {"type": "float"},
                "transaction_amount": {"type": "float"},
                "created_date": {"type": "date"},
                "update_time": {"type": "date"},
            }
        }
        
        metadata = self.generator._generate_metadata("test_data", profile_with_tags)
        
        # Should detect all tag types
        tags = metadata["tags"]
        self.assertIn("auto-generated", tags)
        self.assertIn("customer-data", tags)
        self.assertIn("personal-data", tags)
        self.assertIn("financial", tags)
        self.assertIn("temporal", tags)


class TestStandardGeneratorIntegration(unittest.TestCase):
    """Integration tests for StandardGenerator with various data scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = StandardGenerator()
        
    def test_generate_standard_complex_profile(self):
        """Test generation with complex, realistic data profile."""
        complex_profile = {
            "summary": {
                "total_rows": 1000,
                "total_columns": 8,
                "analyzed_rows": 1000,
                "data_types": {"integer": 3, "string": 3, "float": 1, "date": 1}
            },
            "fields": {
                "user_id": {
                    "type": "integer",
                    "nullable": False,
                    "min_value": 100001,
                    "max_value": 999999,
                },
                "first_name": {
                    "type": "string", 
                    "nullable": False,
                    "min_length": 2,
                    "max_length": 50,
                },
                "last_name": {
                    "type": "string",
                    "nullable": False, 
                    "min_length": 2,
                    "max_length": 50,
                },
                "email_address": {
                    "type": "string",
                    "nullable": False,
                    "min_length": 10,
                    "max_length": 100,
                    "pattern": "email@domain.com"
                },
                "age_years": {
                    "type": "integer",
                    "nullable": False,
                    "min_value": 18,
                    "max_value": 85,
                },
                "salary": {
                    "type": "float",
                    "nullable": False,
                    "min_value": 25000.0,
                    "max_value": 150000.0,
                },
                "hire_date": {
                    "type": "date",
                    "nullable": False,
                    "date_format": "YYYY-MM-DD"
                },
                "middle_initial": {
                    "type": "string",
                    "nullable": True,
                    "min_length": 1,
                    "max_length": 1,
                }
            }
        }
        
        generation_config = {
            "default_thresholds": {
                "completeness_min": 92,
                "validity_min": 95,
                "consistency_min": 88,
                "freshness_max_age": "30d",
                "plausibility_outlier_threshold": 2.5,
            }
        }
        
        standard = self.generator.generate_standard(
            data_profile=complex_profile,
            data_name="employee_data",
            generation_config=generation_config
        )
        
        # Verify complete structure
        self.assertIn("standards", standard)
        self.assertIn("requirements", standard)
        self.assertIn("metadata", standard)
        
        # Verify field requirements cover all fields
        field_requirements = standard["requirements"]["field_requirements"]
        for field_name in complex_profile["fields"].keys():
            self.assertIn(field_name, field_requirements)
        
        # Verify constraint generation
        self.assertIn("min_value", field_requirements["user_id"])
        self.assertIn("pattern", field_requirements["email_address"])
        self.assertIn("format", field_requirements["hire_date"])
        
        # Verify nullable handling
        self.assertTrue(field_requirements["middle_initial"]["nullable"])
        self.assertFalse(field_requirements["first_name"]["nullable"])

    def test_generate_standard_minimal_profile(self):
        """Test generation with minimal valid profile."""
        minimal_profile = {
            "summary": {"total_rows": 1, "total_columns": 1},
            "fields": {
                "simple_field": {
                    "type": "string",
                    "nullable": False,
                }
            }
        }
        
        minimal_config = {"default_thresholds": {}}
        
        standard = self.generator.generate_standard(
            data_profile=minimal_profile,
            data_name="minimal",
            generation_config=minimal_config
        )
        
        # Should still generate valid structure
        self.assertIn("standards", standard)
        self.assertIn("requirements", standard)
        self.assertIn("metadata", standard)
        
        # Should handle missing threshold gracefully
        overall_min = standard["requirements"]["overall_minimum"]
        self.assertIsInstance(overall_min, float)

    def test_serialization_fallback_cases(self):
        """Test serialization fallback cases."""
        # Test with regular Python objects that don't need conversion
        test_data = {
            "string": "test",
            "int": 42,
            "float": 3.14,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }
        
        result = self.generator._convert_to_serializable(test_data)
        self.assertEqual(result, test_data)


if __name__ == "__main__":
    unittest.main()
