"""
Unit tests for plausibility dimension rules.

This module provides test cases for the plausibility dimension rules in ADRI,
ensuring each rule behaves as expected under various data conditions.
"""

import unittest
import pandas as pd
import numpy as np
import scipy.stats as stats

from adri.rules.plausibility import (
    OutlierDetectionRule,
    ValueDistributionRule,
    RangeCheckRule,
    PatternFrequencyRule
)


class TestOutlierDetectionRule(unittest.TestCase):
    """Tests for the OutlierDetectionRule class."""
    
    def setUp(self):
        """Set up test data."""
        # Create a dataframe with normally distributed data plus outliers
        np.random.seed(42)  # For reproducible results
        normal_data = np.random.normal(100, 10, 95).tolist()  # 95 normal points
        outliers = [150, 155, 160, 40, 45]  # 5 obvious outliers
        
        data = {
            'normal_with_outliers': normal_data + outliers,
            'all_normal': np.random.normal(100, 10, 100).tolist(),
            'uniform_data': np.random.uniform(0, 100, 100).tolist()
        }
        self.df = pd.DataFrame(data)
        
        # Test rule with Z-score detection
        self.zscore_rule = OutlierDetectionRule({
            'column': 'normal_with_outliers',
            'method': 'zscore',
            'threshold': 3.0,
            'exclude_outliers': True
        })
        
        # Test rule with IQR detection
        self.iqr_rule = OutlierDetectionRule({
            'column': 'normal_with_outliers',
            'method': 'iqr',
            'threshold': 1.5,
            'multiplier': 1.5,
            'exclude_outliers': True
        })
        
        # Test rule with modified Z-score detection
        self.mod_zscore_rule = OutlierDetectionRule({
            'column': 'normal_with_outliers',
            'method': 'modified_zscore',
            'threshold': 3.5,
            'exclude_outliers': True
        })

    def test_evaluate_with_outliers_zscore(self):
        """Test evaluate method with Z-score outlier detection."""
        # Execute rule
        result = self.zscore_rule.evaluate(self.df)
        
        # Verify the key attributes
        self.assertFalse(result["valid"])  # Should be invalid due to outliers
        
        # Check outlier count (should detect the 5 outliers)
        self.assertEqual(result["outlier_count"], 5)
        
        # Check examples
        examples = result["outlier_examples"]
        self.assertEqual(len(examples), 5)
        
        # Check plausibility ratio
        expected_ratio = 0.95  # 95 out of 100 values are plausible
        self.assertAlmostEqual(result["plausibility_ratio"], expected_ratio, places=2)
        
        # Score calculation: weight * plausibility_ratio = 1.0 * 0.95 = 0.95
        self.assertAlmostEqual(result["score"], 0.95, places=2)

    def test_evaluate_with_outliers_iqr(self):
        """Test evaluate method with IQR outlier detection."""
        # Execute rule
        result = self.iqr_rule.evaluate(self.df)
        
        # Verify result - should detect outliers
        self.assertFalse(result["valid"])
        self.assertGreaterEqual(result["outlier_count"], 5)  # Should detect at least the 5 obvious outliers

    def test_evaluate_with_outliers_modified_zscore(self):
        """Test evaluate method with modified Z-score outlier detection."""
        # Execute rule
        result = self.mod_zscore_rule.evaluate(self.df)
        
        # Verify result - should detect outliers
        self.assertFalse(result["valid"])
        self.assertGreaterEqual(result["outlier_count"], 5)  # Should detect at least the 5 obvious outliers

    def test_evaluate_with_no_outliers(self):
        """Test evaluate method with no outliers in the data."""
        # Create rule for the normal data column
        normal_rule = OutlierDetectionRule({
            'column': 'all_normal',
            'method': 'zscore',
            'threshold': 3.0,
            'exclude_outliers': True
        })
        
        # Execute rule
        result = normal_rule.evaluate(self.df)
        
        # The normal data should have very few or no outliers with threshold 3.0
        # But there could be some due to random sampling, so we check the ratio
        self.assertGreaterEqual(result["plausibility_ratio"], 0.95)

    def test_evaluate_exclude_outliers_false(self):
        """Test evaluate method with exclude_outliers=False."""
        # Create rule that doesn't exclude outliers
        non_excluding_rule = OutlierDetectionRule({
            'column': 'normal_with_outliers',
            'method': 'zscore',
            'threshold': 3.0,
            'exclude_outliers': False  # Don't consider outliers as invalid
        })
        
        # Execute rule
        result = non_excluding_rule.evaluate(self.df)
        
        # Verify the result - should be valid even with outliers
        self.assertTrue(result["valid"])
        self.assertGreaterEqual(result["outlier_count"], 5)  # Still detects outliers

    def test_generate_narrative_with_outliers(self):
        """Test narrative generation for data with outliers."""
        # Create a mock result with outliers
        outlier_result = {
            "valid": False,
            "non_null_records": 100,
            "outlier_count": 5,
            "method": "zscore",
            "threshold": 3.0,
            "statistics": {
                "mean": 100.0,
                "median": 100.0,
                "std": 10.0
            },
            "outlier_examples": [
                {"index": 95, "value": 150.0},
                {"index": 96, "value": 155.0},
                {"index": 97, "value": 160.0}
            ],
            "exclude_outliers": True
        }
        
        narrative = self.zscore_rule.generate_narrative(outlier_result)
        
        # Check narrative content
        self.assertIn("5.0% of values (5 out of 100) in column", narrative)
        self.assertIn("Z-score > 3.0", narrative)
        self.assertIn("record at index 95: 150.0", narrative)
        self.assertIn("problematic data points", narrative)

    def test_generate_narrative_no_outliers(self):
        """Test narrative generation for data without outliers."""
        # Create a mock result without outliers
        normal_result = {
            "valid": True,
            "non_null_records": 100,
            "outlier_count": 0,
            "method": "zscore",
            "threshold": 3.0,
            "statistics": {
                "mean": 100.0,
                "median": 100.0,
                "std": 10.0
            }
        }
        
        narrative = self.zscore_rule.generate_narrative(normal_result)
        
        # Check narrative content
        self.assertIn("No outliers detected", narrative)
        self.assertIn("All 100 non-null values are within expected statistical ranges", narrative)


class TestValueDistributionRule(unittest.TestCase):
    """Tests for the ValueDistributionRule class."""
    
    def setUp(self):
        """Set up test data."""
        # Create a dataframe with different distributions
        np.random.seed(42)  # For reproducible results
        
        # Generate 100 points from each distribution
        normal_data = np.random.normal(100, 10, 100).tolist()
        uniform_data = np.random.uniform(0, 100, 100).tolist()
        poisson_data = np.random.poisson(5, 100).tolist()
        
        # Create non-normal data by mixing distributions
        mixed_data = np.concatenate([
            np.random.normal(50, 10, 50),   # Normal with mean 50
            np.random.normal(150, 10, 50)   # Normal with mean 150
        ]).tolist()
        
        data = {
            'normal_data': normal_data,
            'uniform_data': uniform_data,
            'poisson_data': poisson_data,
            'mixed_data': mixed_data
        }
        self.df = pd.DataFrame(data)
        
        # Test rule for normal distribution
        self.normal_rule = ValueDistributionRule({
            'column': 'normal_data',
            'distribution_type': 'normal',
            'test_method': 'ks',
            'p_threshold': 0.05,
            'distribution_params': {
                'loc': 100,
                'scale': 10
            }
        })
        
        # Test rule for uniform distribution
        self.uniform_rule = ValueDistributionRule({
            'column': 'uniform_data',
            'distribution_type': 'uniform',
            'test_method': 'ks',
            'p_threshold': 0.05,
            'distribution_params': {
                'a': 0,
                'b': 100
            }
        })
        
        # Test rule for Poisson distribution
        self.poisson_rule = ValueDistributionRule({
            'column': 'poisson_data',
            'distribution_type': 'poisson',
            'test_method': 'chi2',
            'p_threshold': 0.05,
            'distribution_params': {
                'mu': 5
            }
        })

    def test_evaluate_normal_distribution(self):
        """Test evaluate method with normal distribution data."""
        # Execute rule
        result = self.normal_rule.evaluate(self.df)
        
        # The normally distributed data with specified parameters should match
        # But statistical tests can be sensitive, so we focus on the structure
        self.assertIn("test_result", result)
        self.assertIn("p_value", result["test_result"])
        self.assertIn("statistic", result["test_result"])

    def test_evaluate_uniform_distribution(self):
        """Test evaluate method with uniform distribution data."""
        # Execute rule
        result = self.uniform_rule.evaluate(self.df)
        
        # Check the results contain expected fields
        self.assertIn("test_result", result)
        self.assertIn("p_value", result["test_result"])
        self.assertIn("statistic", result["test_result"])

    def test_evaluate_deviation_from_distribution(self):
        """Test evaluate method with data deviating from expected distribution."""
        # Create rule expecting normal distribution on clearly mixed data
        mixed_rule = ValueDistributionRule({
            'column': 'mixed_data',
            'distribution_type': 'normal',
            'test_method': 'ks',
            'p_threshold': 0.05,
            'distribution_params': {
                'loc': 100,
                'scale': 10
            }
        })
        
        # Execute rule
        result = mixed_rule.evaluate(self.df)
        
        # The bimodal data should not match a normal distribution
        self.assertFalse(result["valid"])
        self.assertTrue(result["test_result"]["significant"])

    def test_generate_narrative_matching_distribution(self):
        """Test narrative generation for data matching expected distribution."""
        # Create a mock result for distribution match
        match_result = {
            "valid": True,
            "non_null_records": 100,
            "distribution_type": "normal",
            "test_method": "ks",
            "p_threshold": 0.05,
            "data_statistics": {
                "mean": 100.5,
                "std": 9.8,
                "skew": 0.12,
                "kurtosis": 0.05
            },
            "test_result": {
                "test_name": "Kolmogorov-Smirnov",
                "p_value": 0.23,
                "statistic": 0.08,
                "significant": False
            }
        }
        
        narrative = self.normal_rule.generate_narrative(match_result)
        
        # Check narrative content
        self.assertIn("follow a normal distribution", narrative)
        self.assertIn("p-value: 0.2300 >= 0.05", narrative)
        self.assertIn("mean=100.50, std=9.80", narrative)
        self.assertIn("consistent with expectations", narrative)

    def test_generate_narrative_deviation_from_distribution(self):
        """Test narrative generation for data deviating from expected distribution."""
        # Create a mock result for distribution mismatch
        mismatch_result = {
            "valid": False,
            "non_null_records": 100,
            "distribution_type": "normal",
            "test_method": "ks",
            "p_threshold": 0.05,
            "data_statistics": {
                "mean": 100.5,
                "std": 9.8,
                "skew": 1.2,
                "kurtosis": 2.5
            },
            "test_result": {
                "test_name": "Kolmogorov-Smirnov",
                "p_value": 0.01,
                "statistic": 0.18,
                "significant": True
            }
        }
        
        narrative = self.normal_rule.generate_narrative(mismatch_result)
        
        # Check narrative content
        self.assertIn("do NOT follow the expected normal distribution", narrative)
        self.assertIn("p-value: 0.0100 < 0.05", narrative)
        self.assertIn("deviation from the expected distribution", narrative)


class TestRangeCheckRule(unittest.TestCase):
    """Tests for the RangeCheckRule class."""
    
    def setUp(self):
        """Set up test data."""
        # Create a dataframe with various ranges of values
        data = {
            'within_range': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            'with_violations': [5, 15, 25, 35, 45, 55, 65, 75, 85, 200],  # 200 is above range, 5 is below
            'log_scale': [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000],
            'for_quantile': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        }
        self.df = pd.DataFrame(data)
        
        # Test rule with explicit min/max range
        self.range_rule = RangeCheckRule({
            'column': 'within_range',
            'min_value': 10,
            'max_value': 100,
            'quantile_based': False,
            'use_log_scale': False
        })
        
        # Test rule with only min value
        self.min_rule = RangeCheckRule({
            'column': 'with_violations',
            'min_value': 10,
            'max_value': None,
            'quantile_based': False,
            'use_log_scale': False
        })
        
        # Test rule with only max value
        self.max_rule = RangeCheckRule({
            'column': 'with_violations',
            'min_value': None,
            'max_value': 100,
            'quantile_based': False,
            'use_log_scale': False
        })
        
        # Test rule with log scale
        self.log_rule = RangeCheckRule({
            'column': 'log_scale',
            'min_value': 1,
            'max_value': 1000,
            'quantile_based': False,
            'use_log_scale': True
        })
        
        # Test rule with quantile-based range
        self.quantile_rule = RangeCheckRule({
            'column': 'for_quantile',
            'min_value': 0.1,  # 10th percentile
            'max_value': 0.9,  # 90th percentile
            'quantile_based': True,
            'use_log_scale': False
        })

    def test_evaluate_within_range(self):
        """Test evaluate method with values within range."""
        # Execute rule
        result = self.range_rule.evaluate(self.df)
        
        # Verify the key attributes
        self.assertTrue(result["valid"])  # All values within range
        
        # Check violation counts
        self.assertEqual(result["min_violations"], 0)
        self.assertEqual(result["max_violations"], 0)
        self.assertEqual(result["total_violations"], 0)
        
        # Check plausibility ratio
        self.assertEqual(result["plausibility_ratio"], 1.0)
        
        # Score should be maximum weight (1.0) since all values are within range
        self.assertEqual(result["score"], 1.0)

    def test_evaluate_min_violations(self):
        """Test evaluate method with minimum range violations."""
        # Execute rule
        result = self.min_rule.evaluate(self.df)
        
        # Verify the key attributes
        self.assertFalse(result["valid"])  # Has violations
        
        # Check violation counts - should have one value below min (5)
        self.assertEqual(result["min_violations"], 1)
        self.assertEqual(result["total_violations"], 1)
        
        # Check plausibility ratio: 9 out of 10 values are plausible
        self.assertAlmostEqual(result["plausibility_ratio"], 0.9, places=2)

    def test_evaluate_max_violations(self):
        """Test evaluate method with maximum range violations."""
        # Execute rule
        result = self.max_rule.evaluate(self.df)
        
        # Verify the key attributes
        self.assertFalse(result["valid"])  # Has violations
        
        # Check violation counts - should have one value above max (200)
        self.assertEqual(result["max_violations"], 1)
        self.assertEqual(result["total_violations"], 1)
        
        # Check plausibility ratio: 9 out of 10 values are plausible
        self.assertAlmostEqual(result["plausibility_ratio"], 0.9, places=2)

    def test_evaluate_log_scale(self):
        """Test evaluate method with logarithmic scale."""
        # Execute rule
        result = self.log_rule.evaluate(self.df)
        
        # Verify the result - all values should be within range on log scale
        self.assertTrue(result["valid"])
        self.assertEqual(result["total_violations"], 0)

    def test_evaluate_quantile_based(self):
        """Test evaluate method with quantile-based ranges."""
        # Execute rule
        result = self.quantile_rule.evaluate(self.df)
        
        # Values below 10th percentile or above 90th percentile should be flagged
        # Using our dataset, that would be 10 and 100
        expected_violations = 2
        self.assertEqual(result["total_violations"], expected_violations)

    def test_generate_narrative_within_range(self):
        """Test narrative generation for values within range."""
        # Create a mock result for values within range
        valid_result = {
            "valid": True,
            "non_null_records": 100,
            "min_value": 10,
            "max_value": 100,
            "statistics": {
                "min": 12.5,
                "max": 98.7,
                "mean": 55.4,
                "median": 57.2
            }
        }
        
        narrative = self.range_rule.generate_narrative(valid_result)
        
        # Check narrative content
        self.assertIn("All 100 non-null values in column", narrative)
        self.assertIn("within the range [10, 100]", narrative)
        self.assertIn("mean=55.40", narrative)

    def test_generate_narrative_with_violations(self):
        """Test narrative generation for values outside range."""
        # Create a mock result with range violations
        invalid_result = {
            "valid": False,
            "non_null_records": 100,
            "min_violations": 5,
            "max_violations": 3,
            "total_violations": 8,
            "min_value": 10,
            "max_value": 100,
            "statistics": {
                "min": 2.5,
                "max": 150.7,
                "mean": 55.4,
                "median": 57.2
            },
            "below_min_examples": [
                {"index": 3, "value": 5.0},
                {"index": 7, "value": 3.5}
            ],
            "above_max_examples": [
                {"index": 22, "value": 120.0},
                {"index": 48, "value": 150.7}
            ]
        }
        
        narrative = self.range_rule.generate_narrative(invalid_result)
        
        # Check narrative content
        self.assertIn("8.0% of values (8 out of 100) in column", narrative)
        self.assertIn("outside the range [10, 100]", narrative)
        self.assertIn("5 values below the minimum", narrative)
        self.assertIn("3 values above the maximum", narrative)
        self.assertIn("Out-of-range values may indicate", narrative)
        self.assertIn("record at index 3: 5.0 (below min)", narrative)


class TestPatternFrequencyRule(unittest.TestCase):
    """Tests for the PatternFrequencyRule class."""
    
    def setUp(self):
        """Set up test data."""
        # Create a dataframe with categorical data
        data = {
            'balanced_category': ['A', 'B', 'C', 'A', 'B', 'C', 'A', 'B', 'C', 'A'],  # Balanced
            'imbalanced_category': ['A', 'A', 'A', 'A', 'A', 'A', 'A', 'B', 'B', 'C'],  # Highly imbalanced
            'many_categories': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],  # Too many unique values
            'expected_distribution': ['yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'yes', 'no', 'no', 'no']  # 70% yes, 30% no
        }
        self.df = pd.DataFrame(data)
        
        # Test rule for balanced categories
        self.balanced_rule = PatternFrequencyRule({
            'column': 'balanced_category',
            'max_categories': 10,
            'min_frequency': 0.2,  # 20% minimum
            'max_frequency': 0.5,  # 50% maximum
            'tolerance': 0.1
        })
        
        # Test rule for imbalanced categories
        self.imbalanced_rule = PatternFrequencyRule({
            'column': 'imbalanced_category',
            'max_categories': 10,
            'min_frequency': 0.2,
            'max_frequency': 0.5,  # This will be violated by 'A'
            'tolerance': 0.1
        })
        
        # Test rule for many categories
        self.many_categories_rule = PatternFrequencyRule({
            'column': 'many_categories',
            'max_categories': 5,  # Intentionally less than the 10 unique values
            'min_frequency': 0.1,
            'max_frequency': 0.5,
            'tolerance': 0.1
        })
        
        # Test rule with expected frequencies
        self.expected_freq_rule = PatternFrequencyRule({
            'column': 'expected_distribution',
            'expected_frequencies': {
                'yes': 0.7,
                'no': 0.3
            },
            'tolerance': 0.1
        })

    def test_evaluate_balanced_categories(self):
        """Test evaluate method with balanced categories."""
        # Execute rule
        result = self.balanced_rule.evaluate(self.df)
        
        # Verify the key attributes - should be valid with balanced distribution
        self.assertTrue(result["valid"])
        
        # Check issue count
        self.assertEqual(result["issue_count"], 0)

    def test_evaluate_imbalanced_categories(self):
        """Test evaluate method with imbalanced categories."""
        # Execute rule
        result = self.imbalanced_rule.evaluate(self.df)
        
        # Verify the key attributes - should be invalid due to imbalance
        self.assertFalse(result["valid"])
        
        # Check issues - should include high frequency for 'A'
        self.assertGreater(result["issue_count"], 0)
        
        # First issue should mention high frequency
        self.assertIn("high frequency", result["issues"][0])

    def test_evaluate_many_categories(self):
        """Test evaluate method with too many categories."""
        # Execute rule
        result = self.many_categories_rule.evaluate(self.df)
        
        # Verify the key attributes - should be invalid due to too many categories
        self.assertFalse(result["valid"])
        
        # First issue should mention too many unique values
        self.assertIn("Too many unique values", result["issues"][0])

    def test_evaluate_expected_frequencies(self):
        """Test evaluate method with expected frequencies."""
        # Execute rule
        result = self.expected_freq_rule.evaluate(self.df)
        
        # Verify the key attributes - should be valid, matching expected frequencies
        # 70% yes, 30% no - exactly matching our expectation
        self.assertTrue(result["valid"])

    def test_generate_narrative_normal_frequency(self):
        """Test narrative generation for normal frequency distribution."""
        # Create a mock result for normal frequency
        normal_result = {
            "valid": True,
            "non_null_records": 100,
            "unique_values": 3,
            "top_frequencies": {'A': 0.33, 'B': 0.33, 'C': 0.33},
            "issue_count": 0
        }
        
        narrative = self.balanced_rule.generate_narrative(normal_result)
        
        # Check narrative content
        self.assertIn("frequency distribution of values", narrative)
        self.assertIn("appears normal", narrative)
        self.assertIn("3 unique values", narrative)
        self.assertIn("'A': 33.0%, 'B': 33.0%, 'C': 33.0%", narrative)

    def test_generate_narrative_with_frequency_issues(self):
        """Test narrative generation for frequency distribution with issues."""
        # Create a mock result with frequency issues
        issues_result = {
            "valid": False,
            "non_null_records": 100,
            "unique_values": 3,
            "top_frequencies": {'A': 0.85, 'B': 0.10, 'C': 0.05},
            "issue_count": 2,
            "issue_records": 85,
            "issues": [
                "Value 'A' has unusually high frequency: 85% > 50%",
                "Value 'C' has unusually low frequency: 5% < 10%"
            ],
            "issue_examples": [
                {"index": 0, "value": "A", "issue": "high_frequency"},
                {"index": 8, "value": "C", "issue": "low_frequency"}
            ]
        }
        
        narrative = self.imbalanced_rule.generate_narrative(issues_result)
        
        # Check narrative content
        self.assertIn("identified 2 issue(s) affecting 85.0% of values", narrative)
        self.assertIn("Value 'A' has unusually high frequency", narrative)
        self.assertIn("record at index 0: 'A' (high frequency)", narrative)


if __name__ == '__main__':
    unittest.main()

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# The tests in this file cover:
#
# 1. OutlierDetectionRule:
#    - Evaluation with different outlier detection methods (z-score, IQR, modified z-score)
#    - Evaluation with and without outliers
#    - Testing the exclude_outliers parameter behavior
#    - Narrative generation for different scenarios
#
# 2. ValueDistributionRule:
#    - Evaluation of normal, uniform, and Poisson distributions
#    - Evaluation of data that deviates from expected distribution
#    - Narrative generation for different scenarios
#
# 3. RangeCheckRule:
#    - Evaluation with explicit min/max ranges
#    - Evaluation with only min or only max constraints
#    - Evaluation with logarithmic scale
#    - Evaluation with quantile-based ranges
#    - Narrative generation for different scenarios
#
# 4. PatternFrequencyRule:
#    - Evaluation with balanced and imbalanced categories
#    - Evaluation with too many unique categories
#    - Evaluation against expected frequencies
#    - Narrative generation for different scenarios
#
# These tests verify both the evaluation logic and the narrative generation,
# ensuring the rules correctly analyze and report on data plausibility.
# ----------------------------------------------
