"""
Tests to cover missing lines in StandardGenerator.

These tests specifically target the uncovered lines to achieve higher coverage.
"""

import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from adri.analysis.standard_generator import StandardGenerator


class TestStandardGeneratorCoverage(unittest.TestCase):
    """Test StandardGenerator missing lines coverage."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = StandardGenerator()

    def test_generate_standards_metadata_with_data_suffix(self):
        """Test standards metadata generation with 'Data' suffix (line 62)."""
        # Test with a name that doesn't end with 'Data'
        result = self.generator._generate_standards_metadata("Customer")
        self.assertIn("Customer Data Quality Standard", result["name"])

    def test_generate_standards_metadata_without_data_suffix(self):
        """Test standards metadata generation without adding 'Data' suffix."""
        # Test with a name that already ends with 'Data'
        result = self.generator._generate_standards_metadata("Customer Data")
        self.assertIn("Customer Data Quality Standard", result["name"])

    def test_calculate_overall_minimum_with_adjustment(self):
        """Test overall minimum calculation with negative adjustment (line 107)."""
        # Create a profile that will trigger negative adjustment
        profile = {
            "summary": {
                "total_records": 100,
                "null_percentage": 15.0,  # High null percentage
                "duplicate_percentage": 10.0,  # High duplicate percentage
            },
            "fields": {
                "field1": {"type": "string", "nullable": True},
                "field2": {"type": "integer", "nullable": True},
                "field3": {"type": "string", "nullable": True},
                "field4": {"type": "integer", "nullable": False},
            },
        }

        thresholds = {"completeness_min": 85, "validity_min": 90, "consistency_min": 80}

        result = self.generator._calculate_overall_minimum(profile, thresholds)
        # Should apply negative adjustment due to high nullable field ratio (75% > 30%)
        self.assertLess(result, 85.0)

    def test_generate_single_field_requirement_date_type(self):
        """Test single field requirements generation for date type (lines 190-191)."""
        field_profile = {
            "type": "date",
            "nullable": False,
            "null_count": 0,
            "null_percentage": 0.0,
            "date_format": "YYYY-MM-DD",
        }

        result = self.generator._generate_single_field_requirement(
            "date_field", field_profile
        )

        self.assertEqual(result["type"], "date")
        self.assertFalse(result["nullable"])
        self.assertIn("format", result)
        self.assertEqual(result["format"], "YYYY-MM-DD")

    def test_generate_integer_constraints_id_field_behavior(self):
        """Test integer constraints for ID-like field (lines 220-222)."""
        field_profile = {
            "min_value": 18,  # This will be treated as ID field since 18 >= 1 and 65 <= 1000000
            "max_value": 65,
            "avg_value": 35.5,
        }

        result = self.generator._generate_integer_constraints(field_profile)

        # Should detect as ID field (min >= 1 and max <= 1000000) and apply ID-specific constraints
        self.assertEqual(result["min_value"], max(1, 18))  # 18
        self.assertEqual(result["max_value"], min(1000000, 65 * 2))  # 130

    def test_generate_integer_constraints_id_field(self):
        """Test integer constraints for ID-like field (lines 220-222)."""
        field_profile = {"min_value": 1, "max_value": 1000, "avg_value": 500.0}

        result = self.generator._generate_integer_constraints(field_profile)

        # Should detect as ID field (min >= 1 and max <= 1000000) and apply ID-specific constraints
        self.assertEqual(result["min_value"], max(1, 1))  # 1
        self.assertEqual(result["max_value"], min(1000000, 1000 * 2))  # 2000

    def test_generate_integer_constraints_age_field(self):
        """Test integer constraints for age-like field (lines 226-231)."""
        field_profile = {
            "min_value": 0,  # Must start at 0 to avoid ID field detection
            "max_value": 150,
            "avg_value": 45.0,
        }

        result = self.generator._generate_integer_constraints(field_profile)

        # Should detect as age field (min >= 0 and max <= 150) and apply age-specific constraints
        # But since min_value is 0, it won't match ID field condition (min >= 1)
        self.assertEqual(result["min_value"], max(0, 0 - 5))  # 0
        self.assertEqual(result["max_value"], min(150, 150 + 10))  # 150

    def test_generate_integer_constraints_general_field(self):
        """Test integer constraints for general numeric field (lines 229-231)."""
        field_profile = {
            "min_value": 2000000,  # Outside ID range (> 1000000)
            "max_value": 5000000,
            "avg_value": 3000000.0,
        }

        result = self.generator._generate_integer_constraints(field_profile)

        # Should use exact min/max for general numeric fields (outside ID and age ranges)
        self.assertEqual(result["min_value"], 2000000)
        self.assertEqual(result["max_value"], 5000000)

    def test_generate_integer_constraints_negative_range(self):
        """Test integer constraints for negative range (general field)."""
        field_profile = {
            "min_value": -100,  # Negative min, so not ID or age field
            "max_value": 50,
            "avg_value": -25.0,
        }

        result = self.generator._generate_integer_constraints(field_profile)

        # Should use exact min/max for general numeric fields
        self.assertEqual(result["min_value"], -100)
        self.assertEqual(result["max_value"], 50)

    def test_generate_float_constraints_with_positive_min_value(self):
        """Test float constraints generation with positive min_value (line 247)."""
        field_profile = {"min_value": 10.5, "max_value": 100.7, "avg_value": 55.6}

        result = self.generator._generate_float_constraints(field_profile)

        # For positive min values, should set to 0.0
        self.assertEqual(result["min_value"], 0.0)
        # Note: max_value is not set for floats in the actual implementation

    def test_generate_float_constraints_with_negative_min_value(self):
        """Test float constraints generation with negative min_value (line 247)."""
        field_profile = {"min_value": -10.5, "max_value": 100.7, "avg_value": 55.6}

        result = self.generator._generate_float_constraints(field_profile)

        # For negative min values, should keep the actual min value
        self.assertEqual(result["min_value"], -10.5)

    def test_generate_string_constraints_with_pattern(self):
        """Test string constraints with pattern detection (line 277)."""
        field_profile = {
            "min_length": 10,
            "max_length": 20,
            "avg_length": 15.0,
            "pattern": "^[A-Z]{2}[0-9]{3}$",  # Pattern detected
        }

        result = self.generator._generate_string_constraints(field_profile)

        # Implementation adjusts min_length by -1 and max_length by +10
        self.assertEqual(result["min_length"], max(1, 10 - 1))  # 9
        self.assertEqual(result["max_length"], 20 + 10)  # 30
        self.assertEqual(result["pattern"], "^[A-Z]{2}[0-9]{3}$")

    def test_generate_date_constraints_with_format(self):
        """Test date constraints generation with format (lines 285-293)."""
        field_profile = {"date_format": "YYYY-MM-DD HH:mm:ss"}

        result = self.generator._generate_date_constraints(field_profile)

        self.assertEqual(result["format"], "YYYY-MM-DD HH:mm:ss")

    def test_generate_date_constraints_unknown_format(self):
        """Test date constraints with unknown format."""
        field_profile = {"date_format": "unknown"}

        result = self.generator._generate_date_constraints(field_profile)

        # Should not include format for unknown date format
        self.assertNotIn("format", result)

    def test_generate_date_constraints_no_format(self):
        """Test date constraints without date_format."""
        field_profile = {}

        result = self.generator._generate_date_constraints(field_profile)

        # Should return empty constraints
        self.assertEqual(result, {})

    def test_generate_metadata_temporal_data(self):
        """Test metadata generation for temporal data (line 320)."""
        data_profile = {
            "summary": {"total_rows": 1000, "total_columns": 5},
            "fields": {
                "created_date": {"type": "date"},
                "updated_timestamp": {"type": "date"},
                "name": {"type": "string"},
            },
        }

        result = self.generator._generate_metadata("test_data", data_profile)

        # Should include temporal tag due to date fields
        self.assertIn("temporal", result["tags"])

    def test_generate_metadata_no_temporal_data(self):
        """Test metadata generation without temporal data."""
        data_profile = {
            "summary": {"total_rows": 1000, "total_columns": 2},
            "fields": {"name": {"type": "string"}, "age": {"type": "integer"}},
        }

        result = self.generator._generate_metadata("test_data", data_profile)

        # Should not include temporal tag
        self.assertNotIn("temporal", result["tags"])

    def test_convert_to_serializable_int_conversion(self):
        """Test JSON serializer with int conversion (line 344)."""
        # Test with numpy int64
        result = self.generator._convert_to_serializable(np.int64(42))
        self.assertEqual(result, 42)
        self.assertIsInstance(result, int)

    def test_convert_to_serializable_float_conversion(self):
        """Test JSON serializer with float conversion (line 346)."""
        # Test with numpy float64
        result = self.generator._convert_to_serializable(np.float64(3.14))
        self.assertEqual(result, 3.14)
        self.assertIsInstance(result, float)

    def test_convert_to_serializable_ndarray_conversion(self):
        """Test JSON serializer with ndarray conversion (line 348)."""
        # Test with numpy array
        arr = np.array([1, 2, 3])
        result = self.generator._convert_to_serializable(arr)
        self.assertEqual(result, [1, 2, 3])
        self.assertIsInstance(result, list)

    def test_convert_to_serializable_scalar_conversion(self):
        """Test JSON serializer with scalar conversion (line 350)."""
        # Test with numpy scalar
        scalar = np.float64(2.5)
        result = self.generator._convert_to_serializable(scalar)
        self.assertEqual(result, 2.5)

    def test_convert_to_serializable_generic_ndarray(self):
        """Test JSON serializer with generic ndarray (line 352)."""
        # Test with multi-dimensional array
        arr = np.array([[1, 2], [3, 4]])
        result = self.generator._convert_to_serializable(arr)
        self.assertEqual(result, [[1, 2], [3, 4]])
        self.assertIsInstance(result, list)

    def test_convert_to_serializable_regular_object(self):
        """Test JSON serializer with regular object."""
        # Test with regular Python object
        result = self.generator._convert_to_serializable("regular_string")
        self.assertEqual(result, "regular_string")

    def test_comprehensive_standard_generation_with_edge_cases(self):
        """Test comprehensive standard generation covering multiple edge cases."""
        # Create a complex profile that will trigger various code paths
        complex_profile = {
            "summary": {
                "total_records": 1000,
                "null_percentage": 12.0,
                "duplicate_percentage": 8.0,
            },
            "fields": {
                "customer_id": {
                    "type": "integer",
                    "nullable": False,
                    "null_percentage": 0.0,
                    "min_value": 1,
                    "max_value": 1000,
                    "avg_value": 500.5,
                },
                "age": {
                    "type": "integer",
                    "nullable": True,
                    "null_percentage": 5.0,
                    "min_value": 18,
                    "max_value": 65,
                    "avg_value": 35.2,
                },
                "salary": {
                    "type": "float",
                    "nullable": True,
                    "null_percentage": 10.0,
                    "min_value": 30000.0,
                    "max_value": 150000.0,
                    "avg_value": 75000.0,
                },
                "email": {
                    "type": "string",
                    "nullable": False,
                    "null_percentage": 0.0,
                    "min_length": 10,
                    "max_length": 50,
                    "avg_length": 25.0,
                    "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                },
                "created_date": {
                    "type": "date",
                    "nullable": False,
                    "null_percentage": 0.0,
                    "date_format": "YYYY-MM-DD",
                },
                "updated_timestamp": {
                    "type": "date",
                    "nullable": True,
                    "null_percentage": 15.0,
                    "date_format": "YYYY-MM-DD HH:mm:ss",
                },
            },
        }

        # Generate standard with correct parameters
        generation_config = {
            "default_thresholds": {
                "completeness_min": 85,
                "validity_min": 90,
                "consistency_min": 80,
            }
        }

        standard = self.generator.generate_standard(
            data_profile=complex_profile,
            data_name="Complex Customer",
            generation_config=generation_config,
        )

        # Verify the standard structure
        self.assertIn("standards", standard)
        self.assertIn("requirements", standard)

        # Check standards metadata
        standards_section = standard["standards"]
        self.assertIn(
            "Complex Customer Data Quality Standard", standards_section["name"]
        )
        self.assertEqual(standards_section["authority"], "ADRI Auto-Generated")
        self.assertEqual(standards_section["version"], "1.0.0")

        # Check requirements
        requirements = standard["requirements"]
        self.assertIn("overall_minimum", requirements)
        self.assertIn("field_requirements", requirements)

        # Verify field requirements cover all edge cases
        field_reqs = requirements["field_requirements"]

        # Age field should have age-specific constraints
        age_req = field_reqs["age"]
        self.assertEqual(age_req["type"], "integer")
        self.assertTrue(age_req["nullable"])
        self.assertIn("min_value", age_req)
        self.assertIn("max_value", age_req)

        # Email should have pattern
        email_req = field_reqs["email"]
        self.assertEqual(email_req["type"], "string")
        self.assertFalse(email_req["nullable"])
        self.assertIn("pattern", email_req)

        # Date fields should have format
        created_date_req = field_reqs["created_date"]
        self.assertEqual(created_date_req["type"], "date")
        self.assertIn("format", created_date_req)
        self.assertEqual(created_date_req["format"], "YYYY-MM-DD")

        # Check metadata section has tags including temporal
        metadata_section = standard["metadata"]
        self.assertIn("tags", metadata_section)
        self.assertIn("temporal", metadata_section["tags"])


if __name__ == "__main__":
    unittest.main()
