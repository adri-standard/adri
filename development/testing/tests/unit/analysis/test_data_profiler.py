"""
Unit tests for the DataProfiler class.

This module tests the data profiling functionality using TDD approach.
"""

import unittest
from datetime import datetime

import pandas as pd

from adri.analysis.data_profiler import DataProfiler


class TestDataProfiler(unittest.TestCase):
    """Test cases for DataProfiler class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test DataFrame with various data types
        self.test_data = pd.DataFrame(
            {
                "customer_id": [1, 2, 3, 4, 5],
                "name": [
                    "John Doe",
                    "Jane Smith",
                    "Bob Johnson",
                    "Alice Brown",
                    "Charlie Wilson",
                ],
                "email": [
                    "john.doe@email.com",
                    "jane.smith@email.com",
                    "bob.johnson@email.com",
                    "alice.brown@email.com",
                    "charlie.wilson@email.com",
                ],
                "age": [25, 30, 35, 28, 42],
                "registration_date": [
                    "2023-01-15",
                    "2023-02-20",
                    "2023-03-10",
                    "2023-04-05",
                    "2023-05-12",
                ],
                "account_balance": [1500.50, 2750.00, 500.25, 3200.75, 1800.00],
                "is_active": [True, True, False, True, True],
                "optional_field": ["value1", None, "value3", None, "value5"],
            }
        )

        self.profiler = DataProfiler()

    def test_profile_data_basic_structure(self):
        """Test that profile_data returns expected structure."""
        profile = self.profiler.profile_data(self.test_data)

        # Check top-level structure
        self.assertIn("summary", profile)
        self.assertIn("fields", profile)

        # Check summary structure
        summary = profile["summary"]
        self.assertIn("total_rows", summary)
        self.assertIn("total_columns", summary)
        self.assertIn("data_types", summary)

        # Check fields structure
        fields = profile["fields"]
        self.assertEqual(len(fields), len(self.test_data.columns))

        # Each field should have required properties
        for field_name, field_info in fields.items():
            self.assertIn("type", field_info)
            self.assertIn("nullable", field_info)
            self.assertIn("null_count", field_info)
            self.assertIn("null_percentage", field_info)

    def test_profile_data_summary_metrics(self):
        """Test summary metrics calculation."""
        profile = self.profiler.profile_data(self.test_data)
        summary = profile["summary"]

        # Check basic counts
        self.assertEqual(summary["total_rows"], 5)
        self.assertEqual(summary["total_columns"], 8)

        # Check data types summary
        data_types = summary["data_types"]
        self.assertIn("integer", data_types)
        self.assertIn("string", data_types)
        self.assertIn("float", data_types)
        self.assertIn("boolean", data_types)

    def test_profile_integer_field(self):
        """Test profiling of integer fields."""
        profile = self.profiler.profile_data(self.test_data)

        # Check customer_id field (integer)
        customer_id_profile = profile["fields"]["customer_id"]
        self.assertEqual(customer_id_profile["type"], "integer")
        self.assertFalse(customer_id_profile["nullable"])
        self.assertEqual(customer_id_profile["null_count"], 0)
        self.assertEqual(customer_id_profile["null_percentage"], 0.0)
        self.assertIn("min_value", customer_id_profile)
        self.assertIn("max_value", customer_id_profile)
        self.assertEqual(customer_id_profile["min_value"], 1)
        self.assertEqual(customer_id_profile["max_value"], 5)

    def test_profile_string_field(self):
        """Test profiling of string fields."""
        profile = self.profiler.profile_data(self.test_data)

        # Check name field (string)
        name_profile = profile["fields"]["name"]
        self.assertEqual(name_profile["type"], "string")
        self.assertFalse(name_profile["nullable"])
        self.assertIn("min_length", name_profile)
        self.assertIn("max_length", name_profile)
        self.assertIn("avg_length", name_profile)

    def test_profile_email_field_pattern(self):
        """Test pattern detection for email fields."""
        profile = self.profiler.profile_data(self.test_data)

        # Check email field pattern detection
        email_profile = profile["fields"]["email"]
        self.assertEqual(email_profile["type"], "string")
        self.assertIn("pattern", email_profile)
        # Should detect email pattern (check for @ symbol in regex)
        self.assertIn("@", email_profile["pattern"])

    def test_profile_float_field(self):
        """Test profiling of float fields."""
        profile = self.profiler.profile_data(self.test_data)

        # Check account_balance field (float)
        balance_profile = profile["fields"]["account_balance"]
        self.assertEqual(balance_profile["type"], "float")
        self.assertFalse(balance_profile["nullable"])
        self.assertIn("min_value", balance_profile)
        self.assertIn("max_value", balance_profile)
        self.assertEqual(balance_profile["min_value"], 500.25)
        self.assertEqual(balance_profile["max_value"], 3200.75)

    def test_profile_boolean_field(self):
        """Test profiling of boolean fields."""
        profile = self.profiler.profile_data(self.test_data)

        # Check is_active field (boolean)
        active_profile = profile["fields"]["is_active"]
        self.assertEqual(active_profile["type"], "boolean")
        self.assertFalse(active_profile["nullable"])

    def test_profile_nullable_field(self):
        """Test profiling of fields with null values."""
        profile = self.profiler.profile_data(self.test_data)

        # Check optional_field (has nulls)
        optional_profile = profile["fields"]["optional_field"]
        self.assertEqual(optional_profile["type"], "string")
        self.assertTrue(optional_profile["nullable"])
        self.assertEqual(optional_profile["null_count"], 2)
        self.assertEqual(optional_profile["null_percentage"], 40.0)

    def test_profile_date_field(self):
        """Test profiling of date fields."""
        profile = self.profiler.profile_data(self.test_data)

        # Check registration_date field
        date_profile = profile["fields"]["registration_date"]
        # Should be detected as date or string with date pattern
        self.assertIn(date_profile["type"], ["date", "string"])
        if date_profile["type"] == "string":
            self.assertIn("pattern", date_profile)

    def test_profile_empty_dataframe(self):
        """Test profiling of empty DataFrame."""
        empty_df = pd.DataFrame()
        profile = self.profiler.profile_data(empty_df)

        summary = profile["summary"]
        self.assertEqual(summary["total_rows"], 0)
        self.assertEqual(summary["total_columns"], 0)
        self.assertEqual(len(profile["fields"]), 0)

    def test_profile_single_row_dataframe(self):
        """Test profiling of single-row DataFrame."""
        single_row_df = self.test_data.head(1)
        profile = self.profiler.profile_data(single_row_df)

        summary = profile["summary"]
        self.assertEqual(summary["total_rows"], 1)
        self.assertEqual(summary["total_columns"], 8)

    def test_profile_data_with_max_rows_limit(self):
        """Test profiling with max_rows limit."""
        # Create larger dataset
        large_data = pd.concat([self.test_data] * 100, ignore_index=True)

        # Profile with limit
        profile = self.profiler.profile_data(large_data, max_rows=10)

        # Should only analyze first 10 rows
        summary = profile["summary"]
        self.assertEqual(summary["analyzed_rows"], 10)
        self.assertEqual(summary["total_rows"], 500)  # Original size


if __name__ == "__main__":
    unittest.main()
