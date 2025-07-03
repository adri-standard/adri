"""
Unit tests for the StandardGenerator class.

This module tests the YAML standard generation functionality using TDD approach.
"""

import unittest
from datetime import datetime

from adri.analysis.standard_generator import StandardGenerator


class TestStandardGenerator(unittest.TestCase):
    """Test cases for StandardGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample data profile from DataProfiler
        self.sample_profile = {
            "summary": {
                "total_rows": 5,
                "total_columns": 6,
                "analyzed_rows": 5,
                "data_types": {"integer": 2, "string": 3, "float": 1},
            },
            "fields": {
                "customer_id": {
                    "type": "integer",
                    "nullable": False,
                    "null_count": 0,
                    "null_percentage": 0.0,
                    "min_value": 1,
                    "max_value": 5,
                },
                "name": {
                    "type": "string",
                    "nullable": False,
                    "null_count": 0,
                    "null_percentage": 0.0,
                    "min_length": 8,
                    "max_length": 14,
                    "avg_length": 10.2,
                },
                "email": {
                    "type": "string",
                    "nullable": False,
                    "null_count": 0,
                    "null_percentage": 0.0,
                    "min_length": 20,
                    "max_length": 24,
                    "avg_length": 22.0,
                    "pattern": "email",
                },
                "age": {
                    "type": "integer",
                    "nullable": False,
                    "null_count": 0,
                    "null_percentage": 0.0,
                    "min_value": 25,
                    "max_value": 42,
                },
                "account_balance": {
                    "type": "float",
                    "nullable": False,
                    "null_count": 0,
                    "null_percentage": 0.0,
                    "min_value": 500.25,
                    "max_value": 3200.75,
                },
                "optional_field": {
                    "type": "string",
                    "nullable": True,
                    "null_count": 2,
                    "null_percentage": 40.0,
                    "min_length": 6,
                    "max_length": 6,
                    "avg_length": 6.0,
                },
            },
        }

        # Sample generation config
        self.generation_config = {
            "default_thresholds": {
                "completeness_min": 85,
                "validity_min": 90,
                "consistency_min": 80,
                "freshness_max_age": "7d",
                "plausibility_outlier_threshold": 3.0,
            }
        }

        self.generator = StandardGenerator()

    def test_generate_standard_basic_structure(self):
        """Test that generate_standard returns expected YAML structure."""
        standard = self.generator.generate_standard(
            data_profile=self.sample_profile,
            data_name="test_data",
            generation_config=self.generation_config,
        )

        # Check top-level structure
        self.assertIn("standards", standard)
        self.assertIn("requirements", standard)
        self.assertIn("metadata", standard)

        # Check standards metadata
        standards_meta = standard["standards"]
        self.assertIn("id", standards_meta)
        self.assertIn("name", standards_meta)
        self.assertIn("version", standards_meta)
        self.assertIn("authority", standards_meta)
        self.assertIn("effective_date", standards_meta)
        self.assertIn("description", standards_meta)

        # Check requirements structure
        requirements = standard["requirements"]
        self.assertIn("overall_minimum", requirements)
        self.assertIn("dimension_requirements", requirements)
        self.assertIn("field_requirements", requirements)

    def test_generate_standard_metadata_content(self):
        """Test metadata content generation."""
        standard = self.generator.generate_standard(
            data_profile=self.sample_profile,
            data_name="customer_data",
            generation_config=self.generation_config,
        )

        standards_meta = standard["standards"]

        # Check ID format
        self.assertTrue(standards_meta["id"].startswith("customer"))

        # Check name
        self.assertIn("Customer Data", standards_meta["name"])

        # Check version format (should be semantic version)
        version = standards_meta["version"]
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")

        # Check authority
        self.assertEqual(standards_meta["authority"], "ADRI Auto-Generated")

        # Check effective date (should be today)
        effective_date = standards_meta["effective_date"]
        today = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(effective_date, today)

    def test_generate_standard_overall_minimum(self):
        """Test overall minimum score calculation."""
        standard = self.generator.generate_standard(
            data_profile=self.sample_profile,
            data_name="test_data",
            generation_config=self.generation_config,
        )

        overall_min = standard["requirements"]["overall_minimum"]

        # Should be a reasonable value based on data quality
        self.assertIsInstance(overall_min, (int, float))
        self.assertGreaterEqual(overall_min, 60.0)
        self.assertLessEqual(overall_min, 95.0)

    def test_generate_standard_dimension_requirements(self):
        """Test dimension requirements generation."""
        standard = self.generator.generate_standard(
            data_profile=self.sample_profile,
            data_name="test_data",
            generation_config=self.generation_config,
        )

        dim_requirements = standard["requirements"]["dimension_requirements"]

        # Should have all five dimensions
        expected_dimensions = [
            "validity",
            "completeness",
            "consistency",
            "freshness",
            "plausibility",
        ]
        for dimension in expected_dimensions:
            self.assertIn(dimension, dim_requirements)

            dim_config = dim_requirements[dimension]
            self.assertIn("minimum_score", dim_config)
            self.assertIn("description", dim_config)

            # Score should be reasonable
            score = dim_config["minimum_score"]
            self.assertIsInstance(score, (int, float))
            self.assertGreaterEqual(score, 10.0)
            self.assertLessEqual(score, 20.0)

    def test_generate_standard_field_requirements(self):
        """Test field requirements generation."""
        standard = self.generator.generate_standard(
            data_profile=self.sample_profile,
            data_name="test_data",
            generation_config=self.generation_config,
        )

        field_requirements = standard["requirements"]["field_requirements"]

        # Should have all fields from profile
        for field_name in self.sample_profile["fields"].keys():
            self.assertIn(field_name, field_requirements)

            field_config = field_requirements[field_name]
            self.assertIn("type", field_config)
            self.assertIn("nullable", field_config)
            self.assertIn("description", field_config)

    def test_generate_standard_integer_field_constraints(self):
        """Test integer field constraint generation."""
        standard = self.generator.generate_standard(
            data_profile=self.sample_profile,
            data_name="test_data",
            generation_config=self.generation_config,
        )

        field_requirements = standard["requirements"]["field_requirements"]

        # Check customer_id field (integer)
        customer_id_config = field_requirements["customer_id"]
        self.assertEqual(customer_id_config["type"], "integer")
        self.assertFalse(customer_id_config["nullable"])
        self.assertIn("min_value", customer_id_config)
        self.assertIn("max_value", customer_id_config)

        # Check age field (integer with reasonable constraints)
        age_config = field_requirements["age"]
        self.assertEqual(age_config["type"], "integer")
        self.assertIn("min_value", age_config)
        self.assertIn("max_value", age_config)
        # Should have reasonable age constraints
        self.assertGreaterEqual(age_config["min_value"], 18)
        self.assertLessEqual(age_config["max_value"], 120)

    def test_generate_standard_string_field_constraints(self):
        """Test string field constraint generation."""
        standard = self.generator.generate_standard(
            data_profile=self.sample_profile,
            data_name="test_data",
            generation_config=self.generation_config,
        )

        field_requirements = standard["requirements"]["field_requirements"]

        # Check name field (string)
        name_config = field_requirements["name"]
        self.assertEqual(name_config["type"], "string")
        self.assertFalse(name_config["nullable"])
        self.assertIn("min_length", name_config)
        self.assertIn("max_length", name_config)

        # Check email field (string with pattern)
        email_config = field_requirements["email"]
        self.assertEqual(email_config["type"], "string")
        self.assertIn("pattern", email_config)
        # Should have email regex pattern
        pattern = email_config["pattern"]
        self.assertIn("@", pattern)

    def test_generate_standard_float_field_constraints(self):
        """Test float field constraint generation."""
        standard = self.generator.generate_standard(
            data_profile=self.sample_profile,
            data_name="test_data",
            generation_config=self.generation_config,
        )

        field_requirements = standard["requirements"]["field_requirements"]

        # Check account_balance field (float)
        balance_config = field_requirements["account_balance"]
        self.assertEqual(balance_config["type"], "float")
        self.assertFalse(balance_config["nullable"])
        self.assertIn("min_value", balance_config)
        # Should have reasonable minimum (likely 0.0)
        self.assertGreaterEqual(balance_config["min_value"], 0.0)

    def test_generate_standard_nullable_field(self):
        """Test nullable field handling."""
        standard = self.generator.generate_standard(
            data_profile=self.sample_profile,
            data_name="test_data",
            generation_config=self.generation_config,
        )

        field_requirements = standard["requirements"]["field_requirements"]

        # Check optional_field (nullable)
        optional_config = field_requirements["optional_field"]
        self.assertEqual(optional_config["type"], "string")
        self.assertTrue(optional_config["nullable"])

    def test_generate_standard_with_custom_config(self):
        """Test generation with custom configuration."""
        custom_config = {
            "default_thresholds": {
                "completeness_min": 95,
                "validity_min": 98,
                "consistency_min": 90,
                "freshness_max_age": "1d",
                "plausibility_outlier_threshold": 2.0,
            }
        }

        standard = self.generator.generate_standard(
            data_profile=self.sample_profile,
            data_name="test_data",
            generation_config=custom_config,
        )

        # Should generate higher requirements
        overall_min = standard["requirements"]["overall_minimum"]
        self.assertGreaterEqual(overall_min, 80.0)

    def test_generate_standard_empty_profile(self):
        """Test generation with empty data profile."""
        empty_profile = {
            "summary": {
                "total_rows": 0,
                "total_columns": 0,
                "analyzed_rows": 0,
                "data_types": {},
            },
            "fields": {},
        }

        standard = self.generator.generate_standard(
            data_profile=empty_profile,
            data_name="empty_data",
            generation_config=self.generation_config,
        )

        # Should still generate valid structure
        self.assertIn("standards", standard)
        self.assertIn("requirements", standard)
        self.assertIn("metadata", standard)

        # Field requirements should be empty
        field_requirements = standard["requirements"]["field_requirements"]
        self.assertEqual(len(field_requirements), 0)


if __name__ == "__main__":
    unittest.main()
