"""
Unit tests for completeness dimension assessment with configuration options.
"""

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

from adri.dimensions.completeness import CompletenessAssessor
from adri.config.config import Configuration, set_config


class TestCompletenessAssessor(unittest.TestCase):
    """Test cases for the CompletenessAssessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.assessor = CompletenessAssessor()
    
    def test_completeness_with_explicit_metadata(self):
        """Test completeness assessment with explicit metadata."""
        # Create mock connector with explicit completeness info
        connector = MagicMock()
        connector.get_name.return_value = "test_dataset"
        connector.get_completeness_results.return_value = {
            "has_explicit_completeness_info": True,
            "overall_completeness_percent": 95.5,
            "missing_value_markers": ["NA", "NULL", "-999"],
            "completeness_metrics": {
                "by_column": {
                    "id": 100.0,
                    "name": 98.5,
                    "email": 85.2
                }
            },
            "section_completeness": {
                "personal_info": {
                    "completeness_percent": 96.8
                },
                "contact_info": {
                    "completeness_percent": 84.6
                }
            }
        }
        
        # Run assessment
        score, findings, recommendations = self.assessor.assess(connector)
        
        # Check score components in findings
        score_components = None
        for finding in findings:
            if "Score components:" in finding:
                score_components = eval(finding.split("Score components: ")[1])
                break
        
        self.assertIsNotNone(score_components, "Score components not found in findings")
        self.assertEqual(score_components.get("overall_completeness"), 4)
        self.assertEqual(score_components.get("null_distinction"), 5)
        self.assertEqual(score_components.get("explicit_metrics"), 5)
        self.assertEqual(score_components.get("section_awareness"), 5)
        
        # Check overall score
        self.assertEqual(score, 19) # 4 + 5 + 5 + 5 = 19
    
    def test_completeness_with_implicit_metadata_allowed(self):
        """Test completeness assessment with implicit metadata allowed."""
        # Configure to allow implicit metadata
        config = Configuration({
            "completeness_scoring": {
                "REQUIRE_EXPLICIT_METADATA": False
            }
        })
        set_config(config)
        
        # Create mock connector with only implicit completeness info
        connector = MagicMock()
        connector.get_name.return_value = "test_dataset"
        connector.get_completeness_results.return_value = {
            "has_explicit_completeness_info": False,
            "actual_overall_completeness_percent": 92.3,
            "special_null_indicators": {
                "age": "-999",
                "income": "N/A"
            },
            "inferred_sections": {
                "address": ["address_line1", "address_city", "address_state"],
                "contact": ["email", "phone"]
            }
        }
        
        # Run assessment
        score, findings, recommendations = self.assessor.assess(connector)
        
        # Check score components in findings
        score_components = None
        for finding in findings:
            if "Score components:" in finding:
                score_components = eval(finding.split("Score components: ")[1])
                break
        
        self.assertIsNotNone(score_components, "Score components not found in findings")
        self.assertEqual(score_components.get("overall_completeness"), 4)  # Based on 92.3%
        
        # Verify partial points are awarded for implicit detection
        self.assertGreater(score_components.get("null_distinction", 0), 0)
        self.assertGreater(score_components.get("explicit_metrics", 0), 0)
        self.assertGreater(score_components.get("section_awareness", 0), 0)
        
        # Score should be substantial but less than perfect
        self.assertGreater(score, 10)
        self.assertLess(score, 20)
    
    def test_completeness_with_implicit_metadata_not_allowed(self):
        """Test completeness assessment with implicit metadata not allowed."""
        # Configure to require explicit metadata and reset the CompletenessAssessor
        config = Configuration({
            "completeness_scoring": {
                "REQUIRE_EXPLICIT_METADATA": True
            }
        })
        set_config(config)
        
        # Create a new assessor to pick up the configuration change
        self.assessor = CompletenessAssessor()
        
        # Create mock connector with only implicit completeness info
        connector = MagicMock()
        connector.get_name.return_value = "test_dataset"
        connector.get_completeness_results.return_value = {
            "has_explicit_completeness_info": False,
            "actual_overall_completeness_percent": 92.3,
            "special_null_indicators": {
                "age": "-999",
                "income": "N/A"
            },
            "inferred_sections": {
                "address": ["address_line1", "address_city", "address_state"],
                "contact": ["email", "phone"]
            }
        }
        
        # Run assessment
        score, findings, recommendations = self.assessor.assess(connector)
        
        # Check score components in findings
        score_components = None
        for finding in findings:
            if "Score components:" in finding:
                score_components = eval(finding.split("Score components: ")[1])
                break
        
        self.assertIsNotNone(score_components, "Score components not found in findings")
        
        # Overall completeness score should still be awarded
        self.assertEqual(score_components.get("overall_completeness"), 4)  # Based on 92.3%
        
        # Verify no points for components requiring explicit metadata
        self.assertEqual(score_components.get("null_distinction", 0), 0)
        self.assertEqual(score_components.get("explicit_metrics", 0), 0) 
        self.assertEqual(score_components.get("section_awareness", 0), 0)
        
        # Score should be low (only the overall completeness points)
        self.assertLessEqual(score, 5)
        
        # Check for appropriate findings
        metadata_required_found = False
        for finding in findings:
            if "explicit metadata required" in finding.lower():
                metadata_required_found = True
                break
        self.assertTrue(metadata_required_found, 
                      "No finding mentioning explicit metadata requirement")


if __name__ == "__main__":
    unittest.main()
