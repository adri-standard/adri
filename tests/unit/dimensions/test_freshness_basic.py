"""
Unit tests for freshness dimension assessment with configuration options.
"""

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

from adri.dimensions.freshness import FreshnessAssessor
from adri.config.config import Configuration, set_config


class TestFreshnessAssessor(unittest.TestCase):
    """Test cases for the FreshnessAssessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.assessor = FreshnessAssessor()
    
    def test_freshness_with_explicit_metadata(self):
        """Test freshness assessment with explicit metadata."""
        # Create mock connector with explicit freshness info
        connector = MagicMock()
        connector.get_name.return_value = "test_dataset"
        connector.get_freshness_results.return_value = {
            "has_explicit_freshness_info": True,
            "file_modified_time": "2025-05-21T10:30:00Z",
            "file_age_hours": 8.5,
            "max_age_hours": 24,
            "is_fresh": True,
            "update_frequency": "daily"
        }
        
        # Run assessment
        score, findings, recommendations = self.assessor.assess(connector)
        
        # Check score components in findings
        score_components = self._extract_score_components(findings)
        
        self.assertIsNotNone(score_components, "Score components not found in findings")
        self.assertEqual(score_components.get("has_timestamp"), 4)
        self.assertEqual(score_components.get("data_age"), 2)  # Age between 1-24 hours
        self.assertEqual(score_components.get("has_sla"), 4)
        self.assertEqual(score_components.get("meets_sla"), 3)
        self.assertEqual(score_components.get("explicit_communication"), 6)
        
        # Check overall score
        self.assertEqual(score, 19)  # 4 + 2 + 4 + 3 + 6 = 19
    
    def test_freshness_with_implicit_metadata_allowed(self):
        """Test freshness assessment with implicit metadata allowed."""
        # Configure to allow implicit metadata
        config = Configuration({
            "freshness_scoring": {
                "REQUIRE_EXPLICIT_METADATA": False
            }
        })
        set_config(config)
        
        # Create mock connector with only implicit freshness info
        connector = MagicMock()
        connector.get_name.return_value = "test_dataset"
        connector.get_freshness_results.return_value = {
            "has_explicit_freshness_info": False,
            "actual_file_modified_time": "2025-05-21T10:30:00Z",
            "actual_file_age_hours": 8.5,
            "inferred_max_age_hours": 24,
            "detected_update_frequency": "daily"
        }
        
        # Run assessment
        score, findings, recommendations = self.assessor.assess(connector)
        
        # Check score components in findings
        score_components = self._extract_score_components(findings)
        
        self.assertIsNotNone(score_components, "Score components not found in findings")
        
        # Verify partial points are awarded for implicit detection
        self.assertEqual(score_components.get("has_timestamp"), 2)  # 70% of 4 rounded down to 2
        self.assertEqual(score_components.get("data_age"), 2)  # Age between 1-24 hours
        self.assertEqual(score_components.get("has_sla"), 2)  # 50% of 4 rounded down to 2
        self.assertTrue(score_components.get("meets_sla", 0) > 0) # Partial points for meeting inferred SLA
        self.assertEqual(score_components.get("explicit_communication"), 3)  # 50% of 6 rounded down to 3
        
        # Score should be substantial but less than perfect
        self.assertGreater(score, 10)
        self.assertLess(score, 19)
    
    def test_freshness_with_implicit_metadata_not_allowed(self):
        """Test freshness assessment with implicit metadata not allowed."""
        # Configure to require explicit metadata and reset the FreshnessAssessor
        config = Configuration({
            "freshness_scoring": {
                "REQUIRE_EXPLICIT_METADATA": True
            }
        })
        set_config(config)
        
        # Create a new assessor to pick up the configuration change
        self.assessor = FreshnessAssessor()
        
        # Create mock connector with only implicit freshness info
        connector = MagicMock()
        connector.get_name.return_value = "test_dataset"
        connector.get_freshness_results.return_value = {
            "has_explicit_freshness_info": False,
            "actual_file_modified_time": "2025-05-21T10:30:00Z",
            "actual_file_age_hours": 8.5,
            "inferred_max_age_hours": 24,
            "detected_update_frequency": "daily"
        }
        
        # Run assessment
        score, findings, recommendations = self.assessor.assess(connector)
        
        # Check score components in findings
        score_components = self._extract_score_components(findings)
        
        self.assertIsNotNone(score_components, "Score components not found in findings")
        
        # Verify no points for components requiring explicit metadata
        self.assertEqual(score_components.get("has_timestamp", 0), 0)
        self.assertEqual(score_components.get("has_sla", 0), 0) 
        self.assertEqual(score_components.get("explicit_communication", 0), 0)
        
        # Score should be very low
        self.assertLessEqual(score, 5)
        
        # Check for appropriate findings
        metadata_required_found = False
        for finding in findings:
            if "explicit metadata required" in finding.lower():
                metadata_required_found = True
                break
        self.assertTrue(metadata_required_found, 
                      "No finding mentioning explicit metadata requirement")
    
    def _extract_score_components(self, findings):
        """Helper to extract score components from findings list."""
        for finding in findings:
            if "Score components:" in finding:
                return eval(finding.split("Score components: ")[1])
        return None


if __name__ == "__main__":
    unittest.main()
