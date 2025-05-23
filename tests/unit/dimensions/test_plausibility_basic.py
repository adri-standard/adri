"""
Unit tests for plausibility dimension assessment with configuration options.
"""

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

from adri.dimensions.plausibility import PlausibilityAssessor
from adri.config.config import Configuration, set_config


class TestPlausibilityAssessor(unittest.TestCase):
    """Test cases for the PlausibilityAssessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.assessor = PlausibilityAssessor()
    
    def test_basic_plausibility_checks(self):
        """Test basic plausibility assessment with a complete ruleset."""
        # Create mock connector with complete plausibility info
        connector = MagicMock()
        connector.get_name.return_value = "test_dataset"
        connector.get_plausibility_results.return_value = {
            "rule_results": [
                {"name": "value_range_check", "valid": True, "type": "range"},
                {"name": "distribution_check", "valid": True, "type": "distribution"},
                {"name": "relationship_check", "valid": True, "type": "relationship"},
                {"name": "consistency_check", "valid": True, "type": "consistency"},
                {"name": "outlier_check", "valid": True, "type": "outlier_detection"},
                {"name": "domain_rule_1", "valid": True, "domain_specific": True},
                {"name": "domain_rule_2", "valid": True, "domain_specific": True}
            ],
            "valid_overall": True,
            "explicitly_communicated": True,
            "communication_format": "json"
        }
        
        # Run assessment
        score, findings, recommendations = self.assessor.assess(connector)
        
        # Check score components in findings
        score_components = self._extract_score_components(findings)
        
        self.assertIsNotNone(score_components, "Score components not found in findings")
        self.assertEqual(score_components.get("rules_defined"), 3)  # 7 rules = 3 points
        self.assertEqual(score_components.get("rule_types"), 3)  # Has outlier rules
        self.assertEqual(score_components.get("rule_validity"), 4)  # All rules valid
        self.assertEqual(score_components.get("domain_specific"), 3)  # Has domain rules
        self.assertEqual(score_components.get("explicit_communication"), 6)  # Explicitly communicated
        
        # Check overall score
        self.assertEqual(score, 19)  # 3 + 3 + 4 + 3 + 6 = 19
    
    def test_outlier_detection(self):
        """Test plausibility assessment with focus on outlier detection."""
        # Create mock connector with outlier detection rules
        connector = MagicMock()
        connector.get_name.return_value = "test_dataset"
        connector.get_plausibility_results.return_value = {
            "rule_results": [
                {"name": "z_score_outlier", "valid": False, "type": "outlier_detection",
                 "details": "Found 3 statistical outliers"},
                {"name": "iqr_outlier", "valid": True, "type": "outlier_detection"}
            ],
            "valid_overall": False,
            "explicitly_communicated": True
        }
        
        # Run assessment
        score, findings, recommendations = self.assessor.assess(connector)
        
        # Check score components in findings
        score_components = self._extract_score_components(findings)
        
        self.assertIsNotNone(score_components, "Score components not found in findings")
        self.assertEqual(score_components.get("rules_defined"), 2)  # 2 rules = 2 points
        self.assertEqual(score_components.get("rule_types"), 3)  # Has outlier rules
        self.assertEqual(score_components.get("rule_validity"), 1)  # 50% rules valid (≥50% invalid = 1 point)
        self.assertEqual(score_components.get("domain_specific"), 0)  # No domain rules
        self.assertEqual(score_components.get("explicit_communication"), 6)  # Explicitly communicated
        
        # Check overall score
        self.assertEqual(score, 12)  # 2 + 3 + 1 + 0 + 6 = 12
        
        # Check for recommendations about domain rules
        domain_recommendation = False
        for recommendation in recommendations:
            if "domain-specific" in recommendation.lower():
                domain_recommendation = True
                break
        self.assertTrue(domain_recommendation, "No recommendation for domain-specific rules")
    
    def test_pattern_recognition(self):
        """Test plausibility assessment with pattern recognition rules."""
        # Create mock connector with pattern rules
        connector = MagicMock()
        connector.get_name.return_value = "test_dataset"
        connector.get_plausibility_results.return_value = {
            "rule_results": [
                {"name": "pattern_check_1", "valid": True, "type": "pattern"},
                {"name": "pattern_check_2", "valid": True, "type": "pattern"},
                {"name": "pattern_check_3", "valid": False, "type": "pattern"},
                {"name": "pattern_check_4", "valid": True, "type": "pattern"},
                {"name": "pattern_check_5", "valid": True, "type": "pattern"}
            ],
            "valid_overall": False,
            "explicitly_communicated": False
        }
        
        # Run assessment
        score, findings, recommendations = self.assessor.assess(connector)
        
        # Check score components in findings
        score_components = self._extract_score_components(findings)
        
        self.assertIsNotNone(score_components, "Score components not found in findings")
        self.assertEqual(score_components.get("rules_defined"), 3)  # 5 rules = 3 points
        self.assertEqual(score_components.get("rule_types"), 0)  # No outlier rules
        self.assertEqual(score_components.get("rule_validity"), 2)  # 80% rules valid (20% invalid = 2 points)
        self.assertEqual(score_components.get("domain_specific"), 0)  # No domain rules
        self.assertEqual(score_components.get("explicit_communication"), 0)  # Not explicitly communicated
        
        # Check overall score
        self.assertEqual(score, 5)  # 3 + 0 + 2 + 0 + 0 = 5
        
        # Check for recommendations
        communication_recommendation = False
        outlier_recommendation = False
        for recommendation in recommendations:
            if "communica" in recommendation.lower():
                communication_recommendation = True
            if "outlier" in recommendation.lower():
                outlier_recommendation = True
        
        self.assertTrue(communication_recommendation, "No recommendation for communication")
        self.assertTrue(outlier_recommendation, "No recommendation for outlier detection")
    
    def test_domain_specific_rules(self):
        """Test plausibility assessment with domain-specific rules."""
        # Create mock connector with domain-specific rules
        connector = MagicMock()
        connector.get_name.return_value = "test_dataset"
        connector.get_plausibility_results.return_value = {
            "rule_results": [
                {"name": "financial_ratio_check", "valid": True, "type": "domain_specific",
                 "domain": "finance"},
                {"name": "medical_range_check", "valid": True, "domain_specific": True,
                 "domain": "healthcare"},
                {"name": "temporal_sequence_check", "valid": False, "domain_specific": True,
                 "domain": "logistics"}
            ],
            "valid_overall": False,
            "explicitly_communicated": True
        }
        
        # Run assessment
        score, findings, recommendations = self.assessor.assess(connector)
        
        # Check score components in findings
        score_components = self._extract_score_components(findings)
        
        self.assertIsNotNone(score_components, "Score components not found in findings")
        self.assertEqual(score_components.get("rules_defined"), 2)  # 3 rules = 2 points
        self.assertEqual(score_components.get("rule_types"), 0)  # No outlier rules
        self.assertEqual(score_components.get("rule_validity"), 2)  # 67% rules valid (≈33% invalid = 2 points)
        self.assertEqual(score_components.get("domain_specific"), 3)  # Has domain rules
        self.assertEqual(score_components.get("explicit_communication"), 6)  # Explicitly communicated
        
        # Check overall score
        self.assertEqual(score, 13)  # 2 + 0 + 2 + 3 + 6 = 13
        
        # Check for recommendations about outlier rules
        outlier_recommendation = False
        for recommendation in recommendations:
            if "outlier" in recommendation.lower():
                outlier_recommendation = True
                break
        self.assertTrue(outlier_recommendation, "No recommendation for outlier detection")
    
    def test_no_plausibility_information(self):
        """Test behavior when no plausibility information is available."""
        # Create mock connector with no plausibility info
        connector = MagicMock()
        connector.get_name.return_value = "test_dataset"
        connector.get_plausibility_results.return_value = None
        
        # Run assessment
        score, findings, recommendations = self.assessor.assess(connector)
        
        # Check score components in findings
        score_components = self._extract_score_components(findings)
        
        self.assertIsNotNone(score_components, "Score components not found in findings")
        
        # All components should be 0
        self.assertEqual(score_components.get("rules_defined"), 0)
        self.assertEqual(score_components.get("rule_types"), 0)
        self.assertEqual(score_components.get("rule_validity"), 0) 
        self.assertEqual(score_components.get("domain_specific"), 0)
        self.assertEqual(score_components.get("explicit_communication"), 0)
        
        # Overall score should be 0
        self.assertEqual(score, 0)
        
        # Check for comprehensive implementation recommendation
        implementation_recommendation = False
        for recommendation in recommendations:
            if "implement" in recommendation.lower() and "plausibility" in recommendation.lower():
                implementation_recommendation = True
                break
        self.assertTrue(implementation_recommendation, "No recommendation for implementing plausibility")
    
    def _extract_score_components(self, findings):
        """Helper to extract score components from findings list."""
        for finding in findings:
            if "Score components:" in finding:
                return eval(finding.split("Score components: ")[1])
        return None


if __name__ == "__main__":
    unittest.main()
