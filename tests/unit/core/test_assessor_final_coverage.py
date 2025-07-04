"""
Final coverage test for assessor.py module.

This test targets the remaining missing lines to achieve maximum coverage.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime

from adri.core.assessor import (
    AssessmentEngine,
    AssessmentResult,
    DimensionScore,
    FieldAnalysis,
    RuleExecutionResult,
    DataQualityAssessor,
    BundledStandardWrapper
)


class TestAssessorFinalCoverage(unittest.TestCase):
    """Final coverage test for assessor module."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = AssessmentEngine()
        self.sample_data = pd.DataFrame({
            'email': ['test@example.com', 'invalid-email', 'user@domain.org'],
            'age': [25, 150, 30],
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson']
        })

    def test_assessment_engine_assess_exception_fallback_line_89(self):
        """Test assess method exception fallback (line 89)."""
        # Mock load_standard from the cli.commands module to raise an exception
        with patch('adri.cli.commands.load_standard') as mock_load:
            mock_load.side_effect = Exception("Standard loading failed")
            
            result = self.engine.assess(self.sample_data, "invalid_standard.yaml")
            
            # Should fallback to basic assessment
            self.assertIsInstance(result, AssessmentResult)
            self.assertGreater(result.overall_score, 0)

    def test_assessment_result_to_v2_standard_dict_lines_354_382(self):
        """Test AssessmentResult.to_v2_standard_dict method (lines 354-382)."""
        # Create assessment result with all optional attributes
        dimension_scores = {
            'validity': DimensionScore(18.0),
            'completeness': DimensionScore(16.0),
            'consistency': DimensionScore(15.0),
            'freshness': DimensionScore(19.0),
            'plausibility': DimensionScore(17.0)
        }
        
        result = AssessmentResult(
            overall_score=85.0,
            passed=True,
            dimension_scores=dimension_scores,
            standard_id="test-standard-v1",
            assessment_date=datetime.now(),
            metadata={"domain": "test_domain"}
        )
        
        # Add rule execution log
        rule_result = RuleExecutionResult(
            rule_id="test_rule",
            dimension="validity",
            field="email",
            rule_definition="Email format validation",
            total_records=100,
            passed=95,
            failed=5,
            rule_score=19.0
        )
        result.add_rule_execution(rule_result)
        
        # Add field analysis
        field_analysis = FieldAnalysis(
            field_name="email",
            data_type="string",
            null_count=0,
            total_count=100,
            overall_field_score=18.5,
            total_failures=5,
            ml_readiness="ready",
            recommended_actions=["validate_format"]
        )
        result.add_field_analysis("email", field_analysis)
        
        # Set dataset info
        result.set_dataset_info(total_records=100, total_fields=3, size_mb=0.5)
        
        # Set execution stats
        result.set_execution_stats(total_execution_time_ms=1500, rules_executed=5)
        
        # Test to_v2_standard_dict
        report = result.to_v2_standard_dict(dataset_name="test_dataset", adri_version="2.0.0")
        
        # Verify structure
        self.assertIn("adri_assessment_report", report)
        self.assertIn("metadata", report["adri_assessment_report"])
        self.assertIn("summary", report["adri_assessment_report"])
        self.assertIn("rule_execution_log", report["adri_assessment_report"])
        self.assertIn("field_analysis", report["adri_assessment_report"])
        
        # Verify metadata fields
        metadata = report["adri_assessment_report"]["metadata"]
        self.assertEqual(metadata["dataset_name"], "test_dataset")
        self.assertEqual(metadata["adri_version"], "2.0.0")
        self.assertEqual(metadata["standard_id"], "test-standard-v1")
        
        # Verify dataset object
        self.assertIn("dataset", metadata)
        self.assertEqual(metadata["dataset"]["name"], "test_dataset")
        self.assertEqual(metadata["dataset"]["size_mb"], 0.5)
        
        # Verify standard_applied object
        self.assertIn("standard_applied", metadata)
        self.assertEqual(metadata["standard_applied"]["id"], "test-standard-v1")
        
        # Verify execution object
        self.assertIn("execution", metadata)
        self.assertEqual(metadata["execution"]["total_execution_time_ms"], 1500)
        self.assertEqual(metadata["execution"]["duration_ms"], 1500)
        
        # Verify summary
        summary = report["adri_assessment_report"]["summary"]
        self.assertEqual(summary["overall_score"], 85.0)
        self.assertTrue(summary["overall_passed"])
        
        # Verify pass_fail_status object
        self.assertIn("pass_fail_status", summary)
        pass_fail = summary["pass_fail_status"]
        self.assertTrue(pass_fail["overall_passed"])
        self.assertIn("dimension_passed", pass_fail)
        self.assertIn("failed_dimensions", pass_fail)
        self.assertIn("critical_issues", pass_fail)
        self.assertIn("total_failures", pass_fail)

    def test_rule_execution_result_old_signature_lines_430_432(self):
        """Test RuleExecutionResult with old signature (lines 430-432)."""
        # Test old signature compatibility
        rule_result = RuleExecutionResult(
            rule_name="old_rule",
            passed=True,  # Boolean passed
            score=18.5,
            message="Rule passed successfully"
        )
        
        # Verify old signature fields are set correctly
        self.assertEqual(rule_result.rule_name, "old_rule")
        self.assertEqual(rule_result.rule_id, "old_rule")
        self.assertTrue(rule_result.passed)
        self.assertEqual(rule_result.score, 18.5)
        self.assertEqual(rule_result.rule_score, 18.5)
        self.assertEqual(rule_result.message, "Rule passed successfully")
        
        # Verify defaults for new fields
        self.assertEqual(rule_result.dimension, "unknown")
        self.assertEqual(rule_result.field, "unknown")
        self.assertEqual(rule_result.rule_definition, "")

    def test_rule_execution_result_to_dict_passed_count_fix_lines_479_480(self):
        """Test RuleExecutionResult.to_dict with passed count fix (lines 479-480)."""
        # Test the actual behavior - the old signature stores boolean passed directly
        rule_result = RuleExecutionResult(
            rule_name="test_rule",  # Use old signature
            total_records=100,
            passed=True,  # Boolean passed in old signature
            failed=5,
            score=18.0
        )
        
        result_dict = rule_result.to_dict()
        
        # The current implementation stores the boolean directly
        # This test verifies the current behavior and covers lines 479-480
        self.assertTrue(result_dict["passed"])  # Should be True (boolean)
        self.assertTrue(result_dict["execution"]["passed"])  # Should be True (boolean)
        
        # Test with numeric passed value to cover the isinstance check
        rule_result_numeric = RuleExecutionResult(
            rule_id="test_rule_numeric",
            total_records=100,
            passed=95,  # Numeric passed
            failed=5,
            rule_score=18.0
        )
        
        result_dict_numeric = rule_result_numeric.to_dict()
        self.assertEqual(result_dict_numeric["passed"], 95)  # Should be numeric
        self.assertEqual(result_dict_numeric["execution"]["passed"], 95)

    def test_rule_execution_result_to_dict_execution_field_lines_484_485(self):
        """Test RuleExecutionResult.to_dict execution field (lines 484-485)."""
        rule_result = RuleExecutionResult(
            rule_id="test_rule",
            total_records=100,
            passed=95,
            failed=5,
            rule_score=18.0,
            rule_weight=1.5,
            execution_time_ms=250
        )
        
        result_dict = rule_result.to_dict()
        
        # Verify execution field structure
        self.assertIn("execution", result_dict)
        execution = result_dict["execution"]
        self.assertEqual(execution["total_records"], 100)
        self.assertEqual(execution["passed"], 95)
        self.assertEqual(execution["failed"], 5)
        self.assertEqual(execution["execution_time_ms"], 250)
        self.assertEqual(execution["rule_score"], 18.0)
        self.assertEqual(execution["rule_weight"], 1.5)

    def test_rule_execution_result_to_dict_failures_field_lines_489_490(self):
        """Test RuleExecutionResult.to_dict failures field (lines 489-490)."""
        rule_result = RuleExecutionResult(
            rule_id="test_rule",
            failed=5,
            sample_failures=["error1", "error2"],
            failure_patterns={"pattern1": 3, "pattern2": 2}
        )
        
        result_dict = rule_result.to_dict()
        
        # Verify failures field structure
        self.assertIn("failures", result_dict)
        failures = result_dict["failures"]
        self.assertEqual(failures["sample_failures"], ["error1", "error2"])
        self.assertEqual(failures["failure_patterns"], {"pattern1": 3, "pattern2": 2})
        self.assertEqual(failures["total_failed"], 5)

    def test_data_quality_assessor_series_handling_lines_505_507(self):
        """Test DataQualityAssessor with pandas Series (lines 505-507)."""
        assessor = DataQualityAssessor()
        
        # Create a pandas Series
        series_data = pd.Series([1, 2, 3, 4, 5], name="test_column")
        
        # Test assess method with Series
        result = assessor.assess(series_data)
        
        # Should convert Series to DataFrame and assess
        self.assertIsInstance(result, AssessmentResult)
        self.assertGreater(result.overall_score, 0)

    def test_assessment_engine_check_field_type_date_line_662(self):
        """Test _check_field_type with date type (line 662)."""
        field_req = {"type": "date"}
        
        # Test valid date formats
        self.assertTrue(self.engine._check_field_type("2023-12-25", field_req))
        self.assertTrue(self.engine._check_field_type("12/25/2023", field_req))
        
        # Test invalid date format
        self.assertFalse(self.engine._check_field_type("invalid-date", field_req))

    def test_assessment_engine_check_field_pattern_exception_line_675(self):
        """Test _check_field_pattern with exception (line 675)."""
        field_req = {"pattern": "[invalid_regex"}  # Invalid regex
        
        # Should handle regex compilation error gracefully
        result = self.engine._check_field_pattern("test_value", field_req)
        self.assertFalse(result)

    def test_assessment_engine_check_field_range_exception_line_698(self):
        """Test _check_field_range with exception (line 698)."""
        field_req = {"min_value": 10, "max_value": 100}
        
        # Test with non-numeric value (should not raise exception)
        result = self.engine._check_field_range("non-numeric", field_req)
        self.assertTrue(result)  # Should return True for non-numeric values

    def test_assessment_engine_assess_validity_email_exception_line_708(self):
        """Test _assess_validity email check exception (line 708)."""
        # Create data with problematic email values
        data = pd.DataFrame({
            'email': [None, 123, "valid@email.com"]  # Mix of types
        })
        
        # Should handle type conversion gracefully
        score = self.engine._assess_validity(data)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 20)

    def test_assessment_engine_assess_validity_age_exception_lines_732_734(self):
        """Test _assess_validity age check exception (lines 732-734)."""
        # Create data with problematic age values
        data = pd.DataFrame({
            'age': ["not_a_number", None, "25"]
        })
        
        # Should handle conversion errors gracefully
        score = self.engine._assess_validity(data)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 20)

    def test_assessment_engine_assess_completeness_empty_data_lines_750_752(self):
        """Test _assess_completeness with empty data (lines 750-752)."""
        empty_data = pd.DataFrame()
        
        score = self.engine._assess_completeness(empty_data)
        self.assertEqual(score, 0.0)

    def test_assessment_engine_is_valid_email_multiple_at_line_757(self):
        """Test _is_valid_email with multiple @ symbols (line 757)."""
        # Test email with multiple @ symbols
        invalid_email = "user@@domain.com"
        result = self.engine._is_valid_email(invalid_email)
        self.assertFalse(result)
        
        # Test email with no @ symbol
        invalid_email2 = "userdomain.com"
        result2 = self.engine._is_valid_email(invalid_email2)
        self.assertFalse(result2)
        
        # Test valid email
        valid_email = "user@domain.com"
        result3 = self.engine._is_valid_email(valid_email)
        self.assertTrue(result3)

    def test_assessment_engine_public_methods_with_requirements(self):
        """Test public assessment methods with requirements."""
        data = pd.DataFrame({
            'email': ['test@example.com', 'invalid'],
            'name': ['John Doe', 'jane smith'],
            'age': [25, 30]
        })
        
        # Test assess_validity with field requirements
        field_requirements = {
            'email': {'type': 'string', 'pattern': r'^[^@]+@[^@]+\.[^@]+$'},
            'age': {'type': 'integer', 'min_value': 0, 'max_value': 120}
        }
        score = self.engine.assess_validity(data, field_requirements)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 20)
        
        # Test assess_completeness with requirements
        completeness_req = {'mandatory_fields': ['email', 'name']}
        score = self.engine.assess_completeness(data, completeness_req)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 20)
        
        # Test assess_consistency with requirements
        consistency_req = {
            'format_rules': {
                'name': 'title_case',
                'email': 'lowercase'
            }
        }
        score = self.engine.assess_consistency(data, consistency_req)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 20)
        
        # Test assess_freshness with requirements
        freshness_req = {'date_fields': ['created_date']}
        score = self.engine.assess_freshness(data, freshness_req)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 20)
        
        # Test assess_plausibility with requirements
        plausibility_req = {
            'business_rules': {
                'age': {'min': 0, 'max': 120}
            },
            'outlier_detection': {
                'age': {'method': 'range', 'min': 0, 'max': 150}
            }
        }
        score = self.engine.assess_plausibility(data, plausibility_req)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 20)

    def test_bundled_standard_wrapper(self):
        """Test BundledStandardWrapper functionality."""
        standard_dict = {
            "requirements": {
                "overall_minimum": 80.0,
                "field_requirements": {
                    "email": {"type": "string", "nullable": False},
                    "age": {"type": "integer", "min_value": 0, "max_value": 120}
                }
            }
        }
        
        wrapper = BundledStandardWrapper(standard_dict)
        
        # Test get_field_requirements
        field_reqs = wrapper.get_field_requirements()
        self.assertEqual(len(field_reqs), 2)
        self.assertIn("email", field_reqs)
        self.assertIn("age", field_reqs)
        
        # Test get_overall_minimum
        min_score = wrapper.get_overall_minimum()
        self.assertEqual(min_score, 80.0)

    def test_field_analysis_completeness_calculation(self):
        """Test FieldAnalysis completeness calculation."""
        # Test with valid counts
        analysis = FieldAnalysis(
            field_name="test_field",
            total_count=100,
            null_count=10
        )
        self.assertEqual(analysis.completeness, 0.9)
        
        # Test with zero total count
        analysis_zero = FieldAnalysis(
            field_name="test_field",
            total_count=0,
            null_count=0
        )
        self.assertEqual(analysis_zero.completeness, 0.0)
        
        # Test without counts
        analysis_none = FieldAnalysis(field_name="test_field")
        self.assertIsNone(analysis_none.completeness)

    def test_assessment_result_set_execution_stats_duration_alias(self):
        """Test AssessmentResult.set_execution_stats with duration_ms alias."""
        result = AssessmentResult(85.0, True, {})
        
        # Test with duration_ms parameter
        result.set_execution_stats(duration_ms=1500, rules_executed=5)
        
        self.assertEqual(result.execution_stats["total_execution_time_ms"], 1500)
        self.assertEqual(result.execution_stats["duration_ms"], 1500)
        self.assertEqual(result.execution_stats["rules_executed"], 5)


if __name__ == "__main__":
    unittest.main()
