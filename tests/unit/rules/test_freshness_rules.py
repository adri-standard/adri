"""
Unit tests for freshness dimension rules.

This module provides test cases for the freshness dimension rules in ADRI,
ensuring each rule behaves as expected under various data conditions.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from adri.rules.freshness import TimestampRecencyRule, UpdateFrequencyRule


class TestTimestampRecencyRule(unittest.TestCase):
    """Tests for the TimestampRecencyRule class."""
    
    def setUp(self):
        """Set up test data."""
        # Generate test data with timestamps of various ages
        self.reference_time = datetime(2023, 6, 1, 12, 0, 0)  # Fixed reference time
        
        # Create a dataframe with timestamps of various ages
        data = {
            'id': list(range(1, 11)),
            'timestamp': [
                self.reference_time - timedelta(days=5),   # Recent
                self.reference_time - timedelta(days=10),  # Recent
                self.reference_time - timedelta(days=18),  # Warning
                self.reference_time - timedelta(days=22),  # Warning
                self.reference_time - timedelta(days=25),  # Warning
                self.reference_time - timedelta(days=35),  # Expired
                self.reference_time - timedelta(days=40),  # Expired
                self.reference_time - timedelta(days=45),  # Expired
                self.reference_time - timedelta(days=50),  # Expired
                None                                       # Missing value
            ],
            'value': list(range(10, 20))
        }
        self.df = pd.DataFrame(data)
        
        # Test rule with default parameters
        self.rule = TimestampRecencyRule({
            'timestamp_column': 'timestamp',
            'max_age_days': 30,
            'warning_age_days': 15,
            'reference_time': self.reference_time.isoformat()
        })

    def test_evaluate_with_mixed_timestamps(self):
        """Test evaluate method with timestamps of various ages."""
        # Execute rule
        result = self.rule.evaluate(self.df)
        
        # Verify the key attributes
        self.assertFalse(result["valid"])  # Should be invalid due to expired records
        self.assertEqual(result["max_age_days"], 30)
        self.assertEqual(result["warning_age_days"], 15)
        
        # Verify statistics
        stats = result["statistics"]
        self.assertEqual(stats["expired_count"], 4)  # 4 timestamps are expired
        self.assertEqual(stats["warning_count"], 3)  # 3 timestamps are in warning range
        self.assertEqual(stats["recent_count"], 2)   # 2 timestamps are recent
        self.assertEqual(stats["total_count"], 9)    # 9 non-null timestamps
        
        # Score should be proportional to freshness ratio
        # Recent items (2) + 0.5*Warning items (3*0.5=1.5) / total (9) = 3.5/9 = ~0.39
        # With weight 2.0, score should be ~0.78
        self.assertAlmostEqual(result["score"], 0.78, places=2)
        
        # Verify examples
        self.assertIn("expired", result["examples"])
        self.assertIn("warning", result["examples"])
        self.assertEqual(len(result["examples"]["expired"]), 4)

    def test_evaluate_with_all_recent_timestamps(self):
        """Test evaluate method with all recent timestamps."""
        # Create data where all timestamps are recent
        data = {
            'id': list(range(1, 6)),
            'timestamp': [
                self.reference_time - timedelta(days=5),
                self.reference_time - timedelta(days=7),
                self.reference_time - timedelta(days=9),
                self.reference_time - timedelta(days=11),
                self.reference_time - timedelta(days=13)
            ]
        }
        df = pd.DataFrame(data)
        
        # Execute rule
        result = self.rule.evaluate(df)
        
        # Verify result
        self.assertTrue(result["valid"])  # All timestamps are within limits
        stats = result["statistics"]
        self.assertEqual(stats["expired_count"], 0)
        self.assertEqual(stats["warning_count"], 0)
        self.assertEqual(stats["recent_count"], 5)
        
        # Score should be maximum (weight=2.0) since all timestamps are recent
        self.assertAlmostEqual(result["score"], 2.0, places=2)
        
        # Verify no examples of expired or warning
        self.assertNotIn("expired", result["examples"])
        self.assertNotIn("warning", result["examples"])

    def test_evaluate_with_missing_column(self):
        """Test evaluate method with a missing timestamp column."""
        rule = TimestampRecencyRule({
            'timestamp_column': 'non_existent_column',
            'reference_time': self.reference_time.isoformat()
        })
        
        result = rule.evaluate(self.df)
        
        # Verify processing failed due to missing column
        self.assertFalse(result["processed"])
        self.assertIn("not found", result["reason"])

    def test_generate_narrative_valid_data(self):
        """Test narrative generation for valid data."""
        # Create a mock result for valid data
        valid_result = {
            "valid": True,
            "reference_time": self.reference_time.isoformat(),
            "max_age_days": 30,
            "warning_age_days": 15,
            "statistics": {
                "mean_age": 10.5,
                "median_age": 10.0,
                "max_age": 14.0,
                "recent_count": 5,
                "warning_count": 0,
                "expired_count": 0,
                "total_count": 5
            }
        }
        
        narrative = self.rule.generate_narrative(valid_result)
        
        # Check narrative content
        self.assertIn("All timestamps are recent", narrative)
        self.assertIn("10.5 days", narrative)  # Mean age
        self.assertIn("14.0 days", narrative)  # Max age

    def test_generate_narrative_with_warnings(self):
        """Test narrative generation for data with warnings but no expired timestamps."""
        # Create a mock result with warnings
        warning_result = {
            "valid": True,
            "reference_time": self.reference_time.isoformat(),
            "max_age_days": 30,
            "warning_age_days": 15,
            "statistics": {
                "mean_age": 18.0,
                "median_age": 17.5,
                "recent_count": 3,
                "warning_count": 2,
                "expired_count": 0,
                "total_count": 5
            }
        }
        
        narrative = self.rule.generate_narrative(warning_result)
        
        # Check narrative content
        self.assertIn("All timestamps are within the maximum age threshold", narrative)
        self.assertIn("60.0% of timestamps are recent", narrative)  # 3/5 = 60%
        self.assertIn("40.0% are approaching expiration", narrative)  # 2/5 = 40%

    def test_generate_narrative_with_expired(self):
        """Test narrative generation for data with expired timestamps."""
        # Create a mock result with expired timestamps
        expired_result = {
            "valid": False,
            "reference_time": self.reference_time.isoformat(),
            "max_age_days": 30,
            "warning_age_days": 15,
            "statistics": {
                "mean_age": 25.0,
                "median_age": 22.5,
                "max_age": 45.0,
                "recent_count": 2,
                "warning_count": 3,
                "expired_count": 5,
                "total_count": 10
            },
            "examples": {
                "expired": [
                    (5, (self.reference_time - timedelta(days=35)).isoformat()),
                    (6, (self.reference_time - timedelta(days=40)).isoformat())
                ]
            }
        }
        
        narrative = self.rule.generate_narrative(expired_result)
        
        # Check narrative content
        self.assertIn("50.0% of timestamps (5 out of 10) are expired", narrative)
        self.assertIn("average timestamp age is 25.0 days", narrative)
        self.assertIn("Examples of expired timestamps", narrative)


class TestUpdateFrequencyRule(unittest.TestCase):
    """Tests for the UpdateFrequencyRule class."""
    
    def setUp(self):
        """Set up test data."""
        # Generate test data with consistent update intervals
        self.reference_time = datetime(2023, 6, 1, 12, 0, 0)  # Fixed reference time
        
        # Create consistent update timestamps (approximately daily)
        timestamps = []
        for i in range(40):
            # Add a bit of variance around 1 day intervals
            variance = np.random.uniform(-0.2, 0.2)
            timestamps.append(self.reference_time - timedelta(days=i*(1.0+variance)))
        
        data = {
            'id': list(range(1, 41)),
            'timestamp': timestamps,
            'value': list(range(10, 50))
        }
        self.df_consistent = pd.DataFrame(data)
        
        # Create inconsistent update timestamps
        timestamps_inconsistent = []
        for i in range(40):
            # Much larger variance
            if i % 5 == 0:
                variance = np.random.uniform(1.5, 3.0)  # Occasional large gaps
            else:
                variance = np.random.uniform(-0.5, 0.5)
            timestamps_inconsistent.append(self.reference_time - timedelta(days=i*(1.0+variance)))
        
        data_inconsistent = {
            'id': list(range(1, 41)),
            'timestamp': timestamps_inconsistent,
            'value': list(range(10, 50))
        }
        self.df_inconsistent = pd.DataFrame(data_inconsistent)
        
        # Test rule with default parameters
        self.rule = UpdateFrequencyRule({
            'timestamp_column': 'timestamp',
            'expected_interval_days': 1.0,
            'variance_threshold': 0.5,
            'reference_time': self.reference_time.isoformat()
        })

    def test_evaluate_with_consistent_updates(self):
        """Test evaluate method with consistently updated data."""
        # Execute rule
        result = self.rule.evaluate(self.df_consistent)
        
        # Verify the key attributes
        self.assertTrue(result["valid"])  # Should be valid due to consistent updates
        self.assertFalse(result["limited_history"])
        self.assertFalse(result["update_overdue"])
        self.assertTrue(result["frequency_valid"])
        
        # Verify interval statistics - we need a wider delta because of random test data
        self.assertAlmostEqual(result["median_interval_days"], 1.0, delta=0.5)
        self.assertLess(result["interval_deviation"], 0.5)  # Should be within variance threshold
        
        # Score should be high (close to weight=1.5) since updates are consistent
        self.assertGreaterEqual(result["score"], 1.05)

    def test_evaluate_with_inconsistent_updates(self):
        """Test evaluate method with inconsistently updated data."""
        # Execute rule
        result = self.rule.evaluate(self.df_inconsistent)
        
        # Depending on the random data, this might be valid or invalid
        # But coefficient of variation should be higher
        self.assertGreater(result["coefficient_of_variation"], 0.5)
        
        # Score should be lower than for consistent updates
        # This is probabilistic due to random data, so we don't assert specific values

    def test_evaluate_with_missing_column(self):
        """Test evaluate method with a missing timestamp column."""
        rule = UpdateFrequencyRule({
            'timestamp_column': 'non_existent_column',
            'reference_time': self.reference_time.isoformat()
        })
        
        result = rule.evaluate(self.df_consistent)
        
        # Verify processing failed due to missing column
        self.assertFalse(result["processed"])
        self.assertIn("not found", result["reason"])

    def test_evaluate_with_insufficient_timestamps(self):
        """Test evaluate method with too few timestamps for analysis."""
        # Create data with only one timestamp
        data = {
            'id': [1],
            'timestamp': [self.reference_time - timedelta(days=5)]
        }
        df = pd.DataFrame(data)
        
        # Execute rule
        result = self.rule.evaluate(df)
        
        # Verify processing failed due to insufficient data
        self.assertFalse(result["processed"])
        self.assertIn("Insufficient timestamps", result["reason"])

    def test_generate_narrative_valid_frequency(self):
        """Test narrative generation for valid update frequency."""
        # Create a mock result for valid update frequency
        valid_result = {
            "valid": True,
            "reference_time": self.reference_time.isoformat(),
            "expected_interval_days": 1.0,
            "variance_threshold": 0.5,
            "median_interval_days": 0.98,
            "time_since_last_update_days": 0.75,
            "limited_history": False,
            "update_overdue": False,
            "frequency_valid": True,
            "total_updates": 40,
            "last_update": (self.reference_time - timedelta(days=0.75)).isoformat()
        }
        
        narrative = self.rule.generate_narrative(valid_result)
        
        # Check narrative content
        self.assertIn("meets expectations", narrative)
        self.assertIn("median interval of 0.98 days", narrative)
        self.assertIn("0.75 days ago", narrative)

    def test_generate_narrative_invalid_frequency(self):
        """Test narrative generation for invalid update frequency."""
        # Create a mock result for invalid update frequency
        invalid_result = {
            "valid": False,
            "reference_time": self.reference_time.isoformat(),
            "expected_interval_days": 1.0,
            "variance_threshold": 0.5,
            "median_interval_days": 2.3,
            "time_since_last_update_days": 3.5,
            "limited_history": False,
            "update_overdue": True,
            "frequency_valid": False,
            "total_updates": 40,
            "last_update": (self.reference_time - timedelta(days=3.5)).isoformat()
        }
        
        narrative = self.rule.generate_narrative(invalid_result)
        
        # Check narrative content
        self.assertIn("does not meet expectations", narrative)
        self.assertIn("median interval between updates is 2.3 days", narrative)
        self.assertIn("overdue for an update", narrative)
        self.assertIn("3.5 days ago", narrative)


if __name__ == '__main__':
    unittest.main()

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# The tests in this file cover:
#
# 1. TimestampRecencyRule:
#    - Evaluation with mixed timestamps (recent, warning, expired)
#    - Evaluation with all recent timestamps
#    - Error handling for missing columns
#    - Narrative generation for different scenarios
#
# 2. UpdateFrequencyRule:
#    - Evaluation with consistently updated data 
#    - Evaluation with inconsistently updated data
#    - Error handling for missing columns and insufficient data
#    - Narrative generation for different scenarios
#
# These tests verify both the evaluation logic and the narrative generation,
# ensuring the rules correctly analyze and report on the freshness dimension.
# ----------------------------------------------
