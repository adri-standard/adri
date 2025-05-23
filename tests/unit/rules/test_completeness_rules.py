"""
Unit tests for completeness dimension rules.

This module provides test cases for the completeness dimension rules in ADRI,
ensuring each rule behaves as expected under various data conditions.
"""

import unittest
import pandas as pd
import numpy as np

from adri.rules.completeness import RequiredFieldRule, PopulationDensityRule, SchemaCompletenessRule


class TestRequiredFieldRule(unittest.TestCase):
    """Tests for the RequiredFieldRule class."""
    
    def setUp(self):
        """Set up test data."""
        # Create a dataframe with some missing values
        data = {
            'id': list(range(1, 11)),
            'name': ['Alice', 'Bob', 'Charlie', None, 'Eve', 'Frank', None, 'Helen', 'Ivan', 'Julia'],
            'age': [25, 30, None, None, 45, 50, 55, None, 65, 70],
            'email': [f'user{i}@example.com' if i != 4 and i != 8 else None for i in range(1, 11)],
            'optional_field': [None] * 10  # This field is entirely empty
        }
        self.df = pd.DataFrame(data)
        
        # Test rule with default parameters
        self.rule = RequiredFieldRule({
            'required_fields': ['id', 'name', 'age', 'email'],
            'threshold': 0.9  # 90% completeness required
        })

    def test_evaluate_with_missing_values(self):
        """Test evaluate method with data containing missing values."""
        # Execute rule
        result = self.rule.evaluate(self.df)
        
        # Verify the key attributes
        self.assertFalse(result["valid"])  # Should be invalid due to missing values
        
        # Calculate expected completeness:
        # id: 10/10 complete
        # name: 8/10 complete
        # age: 7/10 complete
        # email: 8/10 complete
        # Total: 33/40 = 0.825
        expected_completeness = 33/40
        self.assertAlmostEqual(result["overall_completeness"], expected_completeness, places=3)
        
        # Check total missing count
        self.assertEqual(result["total_missing"], 7)  # 0 + 2 + 3 + 2 = 7 missing values
        
        # Check field-specific results
        field_results = result["field_results"]
        self.assertEqual(field_results["id"]["null_count"], 0)
        self.assertEqual(field_results["name"]["null_count"], 2)
        self.assertEqual(field_results["age"]["null_count"], 3)
        self.assertEqual(field_results["email"]["null_count"], 2)
        
        # Score calculation:
        # completeness / threshold * weight = 0.825 / 0.9 * 2.0 = 1.83
        self.assertAlmostEqual(result["score"], 1.83, places=2)

    def test_evaluate_with_complete_data(self):
        """Test evaluate method with complete data (no missing values)."""
        # Create complete data
        data = {
            'id': list(range(1, 6)),
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, 35, 40, 45],
            'email': ['a@example.com', 'b@example.com', 'c@example.com', 'd@example.com', 'e@example.com']
        }
        df_complete = pd.DataFrame(data)
        
        # Execute rule
        result = self.rule.evaluate(df_complete)
        
        # Verify result
        self.assertTrue(result["valid"])  # All required fields are complete
        self.assertEqual(result["total_missing"], 0)
        self.assertEqual(result["overall_completeness"], 1.0)
        
        # Score should be maximum weight (2.0) since data is complete
        self.assertAlmostEqual(result["score"], 2.0, places=2)

    def test_evaluate_with_missing_fields(self):
        """Test evaluate method with missing required fields."""
        # Rule with fields that don't exist in the dataframe
        rule = RequiredFieldRule({
            'required_fields': ['id', 'name', 'age', 'email', 'non_existent_field'],
            'threshold': 0.9
        })
        
        result = rule.evaluate(self.df)
        
        # Verify processing detected the missing field
        self.assertFalse(result["valid"])
        self.assertIn("missing_fields", result)
        self.assertIn("non_existent_field", result["missing_fields"])

    def test_generate_narrative_valid_data(self):
        """Test narrative generation for valid data."""
        # Create a mock result for valid data
        valid_result = {
            "valid": True,
            "overall_completeness": 0.95,
            "threshold": 0.9,
            "total_records": 100
        }
        
        narrative = self.rule.generate_narrative(valid_result)
        
        # Check narrative content
        self.assertIn("95.0% complete", narrative)
        self.assertIn("meets or exceeds the 90.0% threshold", narrative)

    def test_generate_narrative_with_missing_values(self):
        """Test narrative generation for data with missing values."""
        # Create a mock result with missing values
        invalid_result = {
            "valid": False,
            "overall_completeness": 0.85,
            "threshold": 0.9,
            "total_records": 100,
            "field_results": {
                "name": {
                    "null_count": 8,
                    "completeness_rate": 0.92,
                    "missing_indices": [4, 7]
                },
                "age": {
                    "null_count": 12,
                    "completeness_rate": 0.88,
                    "missing_indices": [2, 3, 7]
                },
                "email": {
                    "null_count": 5,
                    "completeness_rate": 0.95,
                    "missing_indices": [4, 8]
                }
            }
        }
        
        narrative = self.rule.generate_narrative(invalid_result)
        
        # Check narrative content
        self.assertIn("only 85.0% complete", narrative)
        self.assertIn("below the required 90.0% threshold", narrative)
        self.assertIn("Field 'age' has 12 missing values", narrative)
        self.assertIn("indices: 2, 3, 7", narrative)


class TestPopulationDensityRule(unittest.TestCase):
    """Tests for the PopulationDensityRule class."""
    
    def setUp(self):
        """Set up test data."""
        # Create a dataframe with varying population density
        data = {
            'id': list(range(1, 11)),  # Fully populated (100%)
            'col1': ['A', 'B', 'C', 'D', 'E', None, None, None, None, None],  # 50% populated
            'col2': ['X', 'Y', None, None, None, None, None, None, None, None],  # 20% populated
            'col3': [1, 2, 3, None, 5, 6, 7, None, 9, 10],  # 80% populated
            'exclude_me': [None] * 10  # 0% populated, will be excluded
        }
        self.df = pd.DataFrame(data)
        
        # Test rule with default parameters
        self.rule = PopulationDensityRule({
            'threshold': 0.6,  # 60% overall density required
            'column_threshold': 0.5,  # 50% per column required
            'exclude_columns': ['exclude_me']
        })

    def test_evaluate_basic(self):
        """Test basic evaluate method functionality."""
        # Execute rule
        result = self.rule.evaluate(self.df)
        
        # Verify the key attributes
        # Expected density: (10 + 5 + 2 + 8) / (10*4) = 25/40 = 0.625
        expected_density = 25/40
        self.assertAlmostEqual(result["overall_density"], expected_density, places=3)
        
        # With density 0.625 and threshold 0.6, should be valid
        self.assertTrue(result["valid"])
        
        # Check sparse columns
        self.assertEqual(result["sparse_columns"], 1)  # Only col2 is below 50%
        
        # Column results
        column_results = result["column_results"]
        self.assertEqual(column_results["id"]["null_count"], 0)
        self.assertEqual(column_results["col1"]["null_count"], 5)
        self.assertEqual(column_results["col2"]["null_count"], 8)
        self.assertEqual(column_results["col3"]["null_count"], 2)
        
        # Check if sparse columns are correctly identified
        self.assertFalse(column_results["id"]["is_sparse"])
        self.assertFalse(column_results["col1"]["is_sparse"])  # At threshold, not sparse
        self.assertTrue(column_results["col2"]["is_sparse"])
        self.assertFalse(column_results["col3"]["is_sparse"])

    def test_evaluate_below_threshold(self):
        """Test evaluate method with data below threshold."""
        # Adjust rule to have higher threshold
        rule = PopulationDensityRule({
            'threshold': 0.7,  # 70% overall density required (our data is ~62.5%)
            'column_threshold': 0.5,
            'exclude_columns': ['exclude_me']
        })
        
        result = rule.evaluate(self.df)
        
        # Verify result is invalid due to threshold
        self.assertFalse(result["valid"])
        
        # Score calculation:
        # density / threshold * weight = 0.625 / 0.7 * 1.5 = 1.34
        self.assertAlmostEqual(result["score"], 1.34, places=2)

    def test_generate_narrative_valid_data(self):
        """Test narrative generation for valid data."""
        # Create a mock result for valid data with some sparse columns
        valid_result = {
            "valid": True,
            "overall_density": 0.75,
            "threshold": 0.6,
            "sparse_columns": 2,
            "columns_analyzed": 10,
            "column_threshold": 0.5
        }
        
        narrative = self.rule.generate_narrative(valid_result)
        
        # Check narrative content
        self.assertIn("good overall population density of 75.0%", narrative)
        self.assertIn("2 out of 10 columns are sparsely populated", narrative)

    def test_generate_narrative_below_threshold(self):
        """Test narrative generation for data below threshold."""
        # Create a mock result for data below threshold
        invalid_result = {
            "valid": False,
            "overall_density": 0.55,
            "threshold": 0.6,
            "sparse_columns": 3,
            "columns_analyzed": 10,
            "column_threshold": 0.5,
            "column_results": {
                "col1": {"density": 0.3, "null_count": 7, "is_sparse": True},
                "col2": {"density": 0.2, "null_count": 8, "is_sparse": True},
                "col3": {"density": 0.4, "null_count": 6, "is_sparse": True}
            }
        }
        
        narrative = self.rule.generate_narrative(invalid_result)
        
        # Check narrative content
        self.assertIn("low overall population density of 55.0%", narrative)
        self.assertIn("3 out of 10 columns are sparsely populated", narrative)
        self.assertIn("Column 'col2' is only 20.0% populated", narrative)


class TestSchemaCompletenessRule(unittest.TestCase):
    """Tests for the SchemaCompletenessRule class."""
    
    def setUp(self):
        """Set up test data."""
        # Create a simple dataframe
        data = {
            'id': list(range(1, 6)),
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, 35, 40, 45],
            'email': ['a@example.com', 'b@example.com', 'c@example.com', 'd@example.com', 'e@example.com'],
            'extra_field': [1, 2, 3, 4, 5]  # Not in expected schema
        }
        self.df = pd.DataFrame(data)
        
        # Test rule with default parameters
        self.rule = SchemaCompletenessRule({
            'expected_fields': ['id', 'name', 'age', 'email', 'missing_field'],
            'allow_extra_fields': True,
            'case_sensitive': True
        })

    def test_evaluate_with_missing_expected_fields(self):
        """Test evaluate method with missing expected fields."""
        # Execute rule
        result = self.rule.evaluate(self.df)
        
        # Verify the key attributes
        self.assertFalse(result["valid"])  # Should be invalid due to missing expected field
        self.assertFalse(result["schema_complete"])
        
        # Check missing fields
        self.assertEqual(result["missing_fields"], ['missing_field'])
        
        # Check extra fields
        self.assertEqual(result["extra_fields"], ['extra_field'])
        
        # Completeness ratio: 4/5 expected fields present = 0.8
        # Score = weight * ratio = 2.0 * 0.8 = 1.6
        self.assertAlmostEqual(result["score"], 1.6, places=2)

    def test_evaluate_with_disallowed_extra_fields(self):
        """Test evaluate method with disallowed extra fields."""
        # Rule with extra fields not allowed
        rule = SchemaCompletenessRule({
            'expected_fields': ['id', 'name', 'age', 'email'],
            'allow_extra_fields': False,
            'case_sensitive': True
        })
        
        result = rule.evaluate(self.df)
        
        # Verify result
        self.assertFalse(result["valid"])  # Should be invalid due to extra field
        self.assertTrue(result["schema_complete"])  # But all expected fields are present
        self.assertEqual(result["extra_fields"], ['extra_field'])
        
        # Score calculation:
        # All expected fields present (1.0), but penalized for extra field
        # Penalty = extra_fields/actual_fields * 0.5 = 1/5 * 0.5 = 0.1
        # Final ratio = 1.0 * (1.0 - 0.1) = 0.9
        # Score = weight * ratio = 2.0 * 0.9 = 1.8
        self.assertAlmostEqual(result["score"], 1.8, places=2)

    def test_evaluate_with_perfect_match(self):
        """Test evaluate with perfect schema match."""
        # Create dataframe with exact expected fields
        data = {
            'id': list(range(1, 6)),
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, 35, 40, 45],
            'email': ['a@example.com', 'b@example.com', 'c@example.com', 'd@example.com', 'e@example.com']
        }
        df_perfect = pd.DataFrame(data)
        
        rule = SchemaCompletenessRule({
            'expected_fields': ['id', 'name', 'age', 'email'],
            'allow_extra_fields': False,
            'case_sensitive': True
        })
        
        result = rule.evaluate(df_perfect)
        
        # Verify result
        self.assertTrue(result["valid"])
        self.assertTrue(result["schema_complete"])
        self.assertEqual(len(result["missing_fields"]), 0)
        self.assertEqual(len(result["extra_fields"]), 0)
        
        # Score should be maximum weight (2.0) since schema matches perfectly
        self.assertAlmostEqual(result["score"], 2.0, places=2)

    def test_evaluate_with_case_insensitive(self):
        """Test evaluate with case-insensitive field matching."""
        # Create dataframe with differently cased fields
        data = {
            'ID': list(range(1, 6)),
            'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'AGE': [25, 30, 35, 40, 45],
            'Email': ['a@example.com', 'b@example.com', 'c@example.com', 'd@example.com', 'e@example.com']
        }
        df_case = pd.DataFrame(data)
        
        rule = SchemaCompletenessRule({
            'expected_fields': ['id', 'name', 'age', 'email'],
            'allow_extra_fields': True,
            'case_sensitive': False  # Case-insensitive matching
        })
        
        result = rule.evaluate(df_case)
        
        # Verify result
        self.assertTrue(result["valid"])
        self.assertTrue(result["schema_complete"])
        self.assertEqual(len(result["missing_fields"]), 0)
        self.assertEqual(len(result["extra_fields"]), 0)

    def test_generate_narrative_complete_match(self):
        """Test narrative generation for perfect schema match."""
        # Create a mock result for perfect match
        perfect_result = {
            "valid": True,
            "schema_complete": True,
            "expected_fields": ['id', 'name', 'age', 'email'],
            "actual_fields": ['id', 'name', 'age', 'email'],
            "missing_fields": [],
            "extra_fields": []
        }
        
        narrative = self.rule.generate_narrative(perfect_result)
        
        # Check narrative content
        self.assertIn("Data schema is complete with exactly the expected 4 fields", narrative)
        self.assertIn("No fields are missing or extra", narrative)

    def test_generate_narrative_with_extra_fields(self):
        """Test narrative generation for schema with allowed extra fields."""
        # Create a mock result with extra fields
        extra_result = {
            "valid": True,
            "schema_complete": True,
            "expected_fields": ['id', 'name', 'age', 'email'],
            "actual_fields": ['id', 'name', 'age', 'email', 'extra1', 'extra2'],
            "missing_fields": [],
            "extra_fields": ['extra1', 'extra2'],
            "allow_extra_fields": True
        }
        
        narrative = self.rule.generate_narrative(extra_result)
        
        # Check narrative content
        self.assertIn("Data schema contains all 4 expected fields", narrative)
        self.assertIn("Additionally, there are 2 extra fields", narrative)
        self.assertIn("which is allowed", narrative)

    def test_generate_narrative_with_missing_fields(self):
        """Test narrative generation for schema with missing fields."""
        # Create a mock result with missing fields
        missing_result = {
            "valid": False,
            "schema_complete": False,
            "expected_fields": ['id', 'name', 'age', 'email', 'address', 'phone'],
            "actual_fields": ['id', 'name', 'email'],
            "missing_fields": ['age', 'address', 'phone'],
            "extra_fields": [],
            "allow_extra_fields": True
        }
        
        narrative = self.rule.generate_narrative(missing_result)
        
        # Check narrative content
        self.assertIn("Data schema is missing 3 expected fields", narrative)
        self.assertIn("age, address, phone", narrative)
        self.assertIn("Missing fields affect data completeness", narrative)


if __name__ == '__main__':
    unittest.main()

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# The tests in this file cover:
#
# 1. RequiredFieldRule:
#    - Evaluation with data containing missing values
#    - Evaluation with complete data (no missing values)
#    - Error handling for missing required fields
#    - Narrative generation for different scenarios
#
# 2. PopulationDensityRule:
#    - Basic evaluation functionality
#    - Evaluation with data below threshold
#    - Narrative generation for different scenarios
#
# 3. SchemaCompletenessRule:
#    - Evaluation with missing expected fields
#    - Evaluation with disallowed extra fields
#    - Evaluation with perfect schema match
#    - Case-insensitive field matching
#    - Narrative generation for different scenarios
#
# These tests verify both the evaluation logic and the narrative generation,
# ensuring the rules correctly analyze and report on data completeness.
# ----------------------------------------------
