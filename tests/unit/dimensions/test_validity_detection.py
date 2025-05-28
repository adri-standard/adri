"""
Tests for enhanced validity detection in ADRI.

This test suite verifies that the enhanced validity assessment
can automatically detect validity issues in datasets without
relying on explicit metadata.
"""

import unittest
import pandas as pd
from pathlib import Path

from adri.connectors.file import FileConnector
from adri.dimensions.validity import ValidityAssessor


class TestValidityDetection(unittest.TestCase):
    """Test suite for the enhanced validity detection capabilities."""

    def test_infer_column_types(self):
        """Test automatic column type inference."""
        # Arrange
        connector = FileConnector("tests/datasets/ideal_dataset.csv")
        
        # Act
        column_types = connector.infer_column_types()
        
        # Assert
        self.assertIn("customer_id", column_types)
        self.assertEqual(column_types["customer_id"]["type"], "id")
        self.assertGreater(column_types["customer_id"]["confidence"], 0.8)
        
        self.assertIn("price", column_types)
        self.assertEqual(column_types["price"]["type"], "numeric")
        self.assertGreater(column_types["price"]["confidence"], 0.8)
        
        self.assertIn("purchase_date", column_types)
        self.assertEqual(column_types["purchase_date"]["type"], "date")
        self.assertGreater(column_types["purchase_date"]["confidence"], 0.8)
    
    def test_analyze_validity_on_ideal_dataset(self):
        """Test validity analysis on an ideal dataset."""
        # Arrange
        connector = FileConnector("tests/datasets/ideal_dataset.csv")
        
        # Act
        validity_issues = connector.analyze_validity()
        
        # Assert
        self.assertTrue(validity_issues["valid_overall"])
        self.assertEqual(len(validity_issues["type_inconsistencies"]), 0)
        self.assertEqual(len(validity_issues["format_inconsistencies"]), 0)
        self.assertEqual(len(validity_issues["range_violations"]), 0)
    
    def test_analyze_validity_on_invalid_dataset(self):
        """Test validity analysis on a dataset with known validity issues."""
        # Arrange
        connector = FileConnector("tests/datasets/invalid_dataset.csv")
        
        # Act
        validity_issues = connector.analyze_validity()
        
        # Assert
        self.assertFalse(validity_issues["valid_overall"])
        
        # Check for type inconsistencies (non-numeric values in numeric fields)
        self.assertGreater(len(validity_issues["type_inconsistencies"]), 0)
        
        # Check for format inconsistencies (invalid dates, inconsistent IDs)
        self.assertGreater(len(validity_issues["format_inconsistencies"]), 0)
        
        # Check for range violations (negative values)
        self.assertGreater(len(validity_issues["range_violations"]), 0)
        
        # Check specific column issues
        if "price" in validity_issues["range_violations"]:
            self.assertEqual(validity_issues["range_violations"]["price"]["type"], "negative_values")
        
        if "quantity" in validity_issues["range_violations"]:
            self.assertEqual(validity_issues["range_violations"]["quantity"]["type"], "negative_values")
    
    def test_assessor_differential_scoring(self):
        """Test that the assessor gives better scores to valid datasets than invalid ones."""
        # Arrange
        assessor = ValidityAssessor()
        valid_connector = FileConnector("tests/datasets/ideal_dataset.csv")
        invalid_connector = FileConnector("tests/datasets/invalid_dataset.csv")
        
        # Act
        valid_score, valid_findings, _ = assessor.assess(valid_connector)
        invalid_score, invalid_findings, _ = assessor.assess(invalid_connector)
        
        # Assert
        self.assertGreater(valid_score, invalid_score)
        self.assertGreater(valid_score, 10)  # Valid dataset should get a decent score
        self.assertLess(invalid_score, 10)  # Invalid dataset should get a lower score
        
        # Convert findings to string for easier checking
        valid_findings_text = " ".join(valid_findings).lower()
        invalid_findings_text = " ".join(invalid_findings).lower()
        
        # Valid dataset should have positive findings
        self.assertTrue("data types are consistent" in valid_findings_text or "no type inconsistencies" in valid_findings_text)
        
        # Invalid dataset should identify problems
        self.assertIn("inconsistent", invalid_findings_text)
        self.assertTrue("invalid" in invalid_findings_text or "negative values" in invalid_findings_text)
        
        # Print findings for debugging
        print("\nValid dataset findings:")
        for finding in valid_findings:
            print(f"- {finding}")
            
        print("\nInvalid dataset findings:")
        for finding in invalid_findings:
            print(f"- {finding}")
    
    def test_specific_validity_issues_detection(self):
        """Test detection of specific validity issues in the invalid dataset."""
        # Arrange
        connector = FileConnector("tests/datasets/invalid_dataset.csv")
        
        # Act
        validity_issues = connector.analyze_validity()
        
        # Assert - Check for specific issues we know exist in the invalid dataset
        
        # 1. Type inconsistencies in ID column (some are not numeric)
        customer_id_issues = False
        for col, details in validity_issues["type_inconsistencies"].items():
            if col == "customer_id" and details["expected_type"] == "id":
                customer_id_issues = True
                # Examples should include ABC1 and XYZ25
                examples = [str(ex).upper() for ex in details["inconsistent_examples"]]
                self.assertTrue(any("ABC" in ex for ex in examples) or any("XYZ" in ex for ex in examples))
                break
        
        self.assertTrue(customer_id_issues, "Should detect inconsistent customer ID formats")
        
        # 2. Invalid date formats
        date_format_issues = False
        for col, details in validity_issues["format_inconsistencies"].items():
            if col == "purchase_date" and details["type"] == "invalid_dates":
                date_format_issues = True
                break
        
        self.assertTrue(date_format_issues, "Should detect invalid date formats")
        
        # 3. Negative values in price or quantity
        negative_values_issues = False
        for col, details in validity_issues["range_violations"].items():
            if (col == "price" or col == "quantity") and details["type"] == "negative_values":
                negative_values_issues = True
                break
                
        self.assertTrue(negative_values_issues, "Should detect negative values in numeric columns")


if __name__ == '__main__':
    unittest.main()
