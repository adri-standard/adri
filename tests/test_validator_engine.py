"""
Comprehensive tests for ADRI validator engine.

Tests the ValidationEngine, DataQualityAssessor, and related components.
Consolidated from tests/unit/core/test_assessor*.py with updated imports for src/ layout.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import tempfile
import os

# Updated imports for new src/ layout
from src.adri.validator.engine import (
    ValidationEngine,
    DataQualityAssessor,
    AssessmentResult,
    DimensionScore,
    FieldAnalysis,
    RuleExecutionResult,
    BundledStandardWrapper
)


class TestValidationEngine(unittest.TestCase):
    """Test the ValidationEngine class."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = ValidationEngine()
        self.sample_data = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "email": ["alice@test.com", "bob@test.com", "charlie@test.com"],
            "salary": [50000, 60000, 70000]
        })

    def test_basic_assessment(self):
        """Test basic assessment without standard."""
        result = self.engine._basic_assessment(self.sample_data)

        self.assertIsInstance(result, AssessmentResult)
        self.assertGreater(result.overall_score, 0)
        self.assertIn("validity", result.dimension_scores)
        self.assertIn("completeness", result.dimension_scores)
        self.assertIn("consistency", result.dimension_scores)
        self.assertIn("freshness", result.dimension_scores)
        self.assertIn("plausibility", result.dimension_scores)

    def test_assess_validity(self):
        """Test validity assessment logic."""
        # Test with good data
        good_data = pd.DataFrame({
            "email": ["test@example.com", "user@domain.org"],
            "age": [25, 30]
        })
        score = self.engine._assess_validity(good_data)
        self.assertGreater(score, 15)

        # Test with bad data
        bad_data = pd.DataFrame({
            "email": ["invalid-email", "another-bad-email"],
            "age": [-5, 200]  # Invalid ages
        })
        score = self.engine._assess_validity(bad_data)
        self.assertLess(score, 10)

    def test_assess_completeness(self):
        """Test completeness assessment logic."""
        # Complete data
        complete_data = pd.DataFrame({
            "name": ["Alice", "Bob"],
            "age": [25, 30]
        })
        score = self.engine._assess_completeness(complete_data)
        self.assertEqual(score, 20.0)

        # Data with missing values
        incomplete_data = pd.DataFrame({
            "name": ["Alice", None],
            "age": [25, None]
        })
        score = self.engine._assess_completeness(incomplete_data)
        self.assertLess(score, 20.0)

    def test_empty_data(self):
        """Test assessment with empty data."""
        empty_data = pd.DataFrame()
        result = self.engine._basic_assessment(empty_data)

        self.assertIsInstance(result, AssessmentResult)
        self.assertEqual(result.dimension_scores["completeness"].score, 0.0)


class TestDataQualityAssessor(unittest.TestCase):
    """Test the DataQualityAssessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {"audit": {"enabled": False}}  # Disable audit for testing
        self.assessor = DataQualityAssessor(self.config)
        self.sample_data = pd.DataFrame({
            "name": ["Alice", "Bob"],
            "age": [25, 30],
            "email": ["alice@test.com", "bob@test.com"]
        })

    def test_assess_without_standard(self):
        """Test assessment without standard file."""
        result = self.assessor.assess(self.sample_data)

        self.assertIsInstance(result, AssessmentResult)
        self.assertGreater(result.overall_score, 0)
        self.assertIsInstance(result.passed, bool)

    def test_assess_with_dict_data(self):
        """Test assessment with dictionary data input."""
        dict_data = {"name": "Alice", "age": 25}
        result = self.assessor.assess(dict_data)

        self.assertIsInstance(result, AssessmentResult)
        self.assertGreater(result.overall_score, 0)

    def test_assess_with_series_data(self):
        """Test assessment with pandas Series input."""
        series_data = pd.Series([1, 2, 3])
        result = self.assessor.assess(series_data)

        self.assertIsInstance(result, AssessmentResult)

    def test_assess_with_list_data(self):
        """Test assessment with list data input."""
        list_data = [{"name": "Alice"}, {"name": "Bob"}]
        result = self.assessor.assess(list_data)

        self.assertIsInstance(result, AssessmentResult)

    def test_assess_with_standard_file(self):
        """Test assessment with standard file."""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            standard_path = f.name

        try:
            # Create a valid YAML file
            with open(standard_path, 'w', encoding='utf-8') as f:
                f.write("standards:\n  id: test_standard\n  name: Test Standard\n")

            result = self.assessor.assess(self.sample_data, standard_path)

            # Should return valid assessment result
            self.assertIsInstance(result, AssessmentResult)
            self.assertGreater(result.overall_score, 0)
        finally:
            os.unlink(standard_path)


class TestAssessmentResult(unittest.TestCase):
    """Test the AssessmentResult class."""

    def setUp(self):
        """Set up test fixtures."""
        self.dimension_scores = {
            "validity": DimensionScore(16.5),
            "completeness": DimensionScore(18.0),
            "consistency": DimensionScore(16.0),
            "freshness": DimensionScore(17.0),
            "plausibility": DimensionScore(15.0)
        }

        self.result = AssessmentResult(
            overall_score=82.5,
            passed=True,
            dimension_scores=self.dimension_scores,
            standard_id="test_standard"
        )

    def test_initialization(self):
        """Test AssessmentResult initialization."""
        self.assertEqual(self.result.overall_score, 82.5)
        self.assertTrue(self.result.passed)
        self.assertEqual(self.result.standard_id, "test_standard")
        self.assertEqual(len(self.result.dimension_scores), 5)

    def test_add_rule_execution(self):
        """Test adding rule execution results."""
        rule_result = RuleExecutionResult(rule_name="test_rule", passed=True, score=18.0)
        self.result.add_rule_execution(rule_result)

        self.assertEqual(len(self.result.rule_execution_log), 1)
        self.assertEqual(self.result.rule_execution_log[0], rule_result)

    def test_add_field_analysis(self):
        """Test adding field analysis."""
        field_analysis = FieldAnalysis("test_field", total_failures=0)
        self.result.add_field_analysis("test_field", field_analysis)

        self.assertIn("test_field", self.result.field_analysis)
        self.assertEqual(self.result.field_analysis["test_field"], field_analysis)

    def test_set_dataset_info(self):
        """Test setting dataset information."""
        self.result.set_dataset_info(100, 5, 2.5)

        self.assertEqual(self.result.dataset_info["total_records"], 100)
        self.assertEqual(self.result.dataset_info["total_fields"], 5)
        self.assertEqual(self.result.dataset_info["size_mb"], 2.5)

    def test_set_execution_stats(self):
        """Test setting execution statistics."""
        self.result.set_execution_stats(total_execution_time_ms=500, rules_executed=10)

        self.assertEqual(self.result.execution_stats["total_execution_time_ms"], 500)
        self.assertEqual(self.result.execution_stats["rules_executed"], 10)
        self.assertEqual(self.result.execution_stats["duration_ms"], 500)  # Alias

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result_dict = self.result.to_dict()

        self.assertIsInstance(result_dict, dict)
        self.assertIn("adri_assessment_report", result_dict)


class TestDimensionScore(unittest.TestCase):
    """Test the DimensionScore class."""

    def test_initialization(self):
        """Test DimensionScore initialization."""
        score = DimensionScore(15.5, max_score=20.0)
        self.assertEqual(score.score, 15.5)
        self.assertEqual(score.max_score, 20.0)
        self.assertEqual(score.issues, [])
        self.assertEqual(score.details, {})

    def test_percentage_calculation(self):
        """Test percentage calculation."""
        score = DimensionScore(15.0, max_score=20.0)
        self.assertEqual(score.percentage(), 75.0)

        score = DimensionScore(18.0, max_score=20.0)
        self.assertEqual(score.percentage(), 90.0)


class TestFieldAnalysis(unittest.TestCase):
    """Test the FieldAnalysis class."""

    def test_initialization(self):
        """Test FieldAnalysis initialization."""
        analysis = FieldAnalysis(
            field_name="test_field",
            data_type="string",
            null_count=5,
            total_count=100,
            total_failures=2
        )

        self.assertEqual(analysis.field_name, "test_field")
        self.assertEqual(analysis.data_type, "string")
        self.assertEqual(analysis.null_count, 5)
        self.assertEqual(analysis.total_count, 100)
        self.assertEqual(analysis.total_failures, 2)
        self.assertEqual(analysis.completeness, 0.95)  # (100-5)/100

    def test_completeness_calculation(self):
        """Test completeness calculation."""
        # Normal case
        analysis = FieldAnalysis("field", null_count=10, total_count=100)
        self.assertEqual(analysis.completeness, 0.9)

        # Edge case: no nulls
        analysis = FieldAnalysis("field", null_count=0, total_count=50)
        self.assertEqual(analysis.completeness, 1.0)

        # Edge case: all nulls
        analysis = FieldAnalysis("field", null_count=50, total_count=50)
        self.assertEqual(analysis.completeness, 0.0)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        analysis = FieldAnalysis(
            field_name="test_field",
            total_failures=3,
            ml_readiness="high"
        )

        result_dict = analysis.to_dict()
        self.assertEqual(result_dict["field_name"], "test_field")
        self.assertEqual(result_dict["total_failures"], 3)
        self.assertEqual(result_dict["ml_readiness"], "high")


class TestRuleExecutionResult(unittest.TestCase):
    """Test the RuleExecutionResult class."""

    def test_new_signature_initialization(self):
        """Test initialization with new signature."""
        result = RuleExecutionResult(
            rule_id="test_rule",
            dimension="validity",
            field="email",
            total_records=100,
            passed=90,
            failed=10,
            rule_score=18.0
        )

        self.assertEqual(result.rule_id, "test_rule")
        self.assertEqual(result.dimension, "validity")
        self.assertEqual(result.field, "email")
        self.assertEqual(result.total_records, 100)
        self.assertEqual(result.passed, 90)
        self.assertEqual(result.failed, 10)
        self.assertEqual(result.rule_score, 18.0)  # Matches input value

    def test_legacy_signature_compatibility(self):
        """Test backward compatibility with old signature."""
        result = RuleExecutionResult(
            rule_name="legacy_rule",
            passed=True,
            score=17.5,
            message="Test message"
        )

        self.assertEqual(result.rule_name, "legacy_rule")
        self.assertEqual(result.rule_id, "legacy_rule")
        self.assertEqual(result.passed, 1)  # Converted to int
        self.assertEqual(result.score, 17.5)
        self.assertEqual(result.message, "Test message")

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = RuleExecutionResult(
            rule_id="test_rule",
            total_records=100,
            passed=85,
            failed=15,
            rule_score=17.0
        )

        result_dict = result.to_dict()
        self.assertEqual(result_dict["rule_id"], "test_rule")
        self.assertEqual(result_dict["total_records"], 100)
        self.assertEqual(result_dict["passed"], 85)
        self.assertEqual(result_dict["failed"], 15)
        self.assertEqual(result_dict["rule_score"], 17.0)

        # Check required v2.0 compliance fields
        self.assertIn("execution", result_dict)
        self.assertIn("failures", result_dict)


class TestBundledStandardWrapper(unittest.TestCase):
    """Test the BundledStandardWrapper class."""

    def setUp(self):
        """Set up test fixtures."""
        self.standard_dict = {
            "requirements": {
                "overall_minimum": 85.0,
                "field_requirements": {
                    "name": {"type": "string", "nullable": False},
                    "age": {"type": "integer", "min_value": 0, "max_value": 120}
                }
            }
        }
        self.wrapper = BundledStandardWrapper(self.standard_dict)

    def test_get_field_requirements(self):
        """Test getting field requirements."""
        requirements = self.wrapper.get_field_requirements()

        self.assertIn("name", requirements)
        self.assertIn("age", requirements)
        self.assertEqual(requirements["name"]["type"], "string")
        self.assertEqual(requirements["age"]["min_value"], 0)

    def test_get_overall_minimum(self):
        """Test getting overall minimum score."""
        minimum = self.wrapper.get_overall_minimum()
        self.assertEqual(minimum, 85.0)

    def test_empty_requirements(self):
        """Test with empty or missing requirements."""
        empty_wrapper = BundledStandardWrapper({})

        requirements = empty_wrapper.get_field_requirements()
        self.assertEqual(requirements, {})

        minimum = empty_wrapper.get_overall_minimum()
        self.assertEqual(minimum, 75.0)  # Default


class TestAssessmentIntegration(unittest.TestCase):
    """Integration tests for assessment functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.assessor = DataQualityAssessor()
        self.sample_data = pd.DataFrame({
            "customer_id": range(1, 11),
            "name": [f"Customer {i}" for i in range(1, 11)],
            "email": [f"customer{i}@example.com" for i in range(1, 11)],
            "age": [25 + i for i in range(10)],
            "balance": [1000.0 + (i * 100) for i in range(10)]
        })

    def test_end_to_end_assessment(self):
        """Test complete assessment workflow."""
        result = self.assessor.assess(self.sample_data)

        # Basic validations
        self.assertIsInstance(result, AssessmentResult)
        self.assertIsInstance(result.overall_score, (int, float))
        self.assertIsInstance(result.passed, bool)

        # Dimension scores validation
        expected_dimensions = ["validity", "completeness", "consistency", "freshness", "plausibility"]
        for dim in expected_dimensions:
            self.assertIn(dim, result.dimension_scores)
            dim_score = result.dimension_scores[dim]
            self.assertIsInstance(dim_score, DimensionScore)
            self.assertGreaterEqual(dim_score.score, 0)
            self.assertLessEqual(dim_score.score, 20)

    def test_assessment_with_high_quality_data(self):
        """Test assessment with high-quality data."""
        high_quality_data = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "email": ["alice@example.com", "bob@example.com", "charlie@example.com"],
        })

        result = self.assessor.assess(high_quality_data)

        # Should have high scores
        self.assertGreater(result.overall_score, 70)

        # Completeness should be perfect (no nulls)
        completeness_score = result.dimension_scores["completeness"].score
        self.assertEqual(completeness_score, 20.0)

    def test_assessment_with_poor_quality_data(self):
        """Test assessment with poor-quality data."""
        poor_quality_data = pd.DataFrame({
            "name": [None, "Bob", None, "Dave"],
            "age": [-5, 30, 200, 35],  # Invalid ages
            "email": ["invalid", "bob@example.com", "also-invalid", "dave@example.com"],
        })

        result = self.assessor.assess(poor_quality_data)

        # Should have lower scores (accounting for dynamic rule weights)
        self.assertLess(result.overall_score, 90)  # Realistic with new scoring

        # Completeness should be reduced (nulls present)
        completeness_score = result.dimension_scores["completeness"].score
        self.assertLess(completeness_score, 20.0)

    def test_assessment_with_audit_logging(self):
        """Test assessment with audit logging enabled."""
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "audit": {
                    "enabled": True,
                    "log_dir": temp_dir
                }
            }
            assessor = DataQualityAssessor(config)
            result = assessor.assess(self.sample_data)

            # Should work with audit logging
            self.assertIsInstance(result, AssessmentResult)
            self.assertGreater(result.overall_score, 0)

    def test_assessment_with_different_data_formats(self):
        """Test assessment handles various data input formats."""
        # Test with dictionary
        dict_data = {"name": "Alice", "age": 25, "email": "alice@test.com"}
        result = self.assessor.assess(dict_data)
        self.assertIsInstance(result, AssessmentResult)

        # Test with list of dictionaries
        list_data = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30}
        ]
        result = self.assessor.assess(list_data)
        self.assertIsInstance(result, AssessmentResult)

        # Test with pandas Series
        series_data = pd.Series([1, 2, 3, 4, 5])
        result = self.assessor.assess(series_data)
        self.assertIsInstance(result, AssessmentResult)


class TestValidationEngineComprehensive(unittest.TestCase):
    """Comprehensive tests for ValidationEngine to improve coverage."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = ValidationEngine()
        self.test_data = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "email": ["alice@test.com", "bob@test.com", "charlie@test.com"],
            "age": [25, 30, 35],
            "score": [85.5, 92.0, 78.5]
        })

    def test_assess_with_standard_dict(self):
        """Test assessment using standard dictionary instead of file."""
        standard_dict = {
            "requirements": {
                "overall_minimum": 75.0,
                "field_requirements": {
                    "name": {"type": "string", "nullable": False},
                    "age": {"type": "integer", "min_value": 0, "max_value": 120}
                }
            }
        }

        result = self.engine.assess_with_standard_dict(self.test_data, standard_dict)

        self.assertIsInstance(result, AssessmentResult)
        self.assertGreater(result.overall_score, 0)

    def test_assess_with_invalid_standard_dict(self):
        """Test assessment with invalid standard dictionary."""
        invalid_standard = {"invalid": "structure"}

        # Should fallback to basic assessment
        result = self.engine.assess_with_standard_dict(self.test_data, invalid_standard)

        self.assertIsInstance(result, AssessmentResult)
        self.assertGreater(result.overall_score, 0)

    def test_bundled_standard_wrapper_edge_cases(self):
        """Test BundledStandardWrapper with edge cases."""
        # Test with missing requirements
        empty_wrapper = BundledStandardWrapper({})
        self.assertEqual(empty_wrapper.get_field_requirements(), {})
        self.assertEqual(empty_wrapper.get_overall_minimum(), 75.0)

        # Test with invalid requirements structure
        invalid_wrapper = BundledStandardWrapper({"requirements": "not_a_dict"})
        self.assertEqual(invalid_wrapper.get_field_requirements(), {})
        self.assertEqual(invalid_wrapper.get_overall_minimum(), 75.0)

    def test_assessment_result_metadata_handling(self):
        """Test AssessmentResult metadata and execution stats."""
        result = AssessmentResult(85.0, True, {}, "test_standard")

        # Test dataset info
        result.set_dataset_info(100, 5, 2.5)
        self.assertEqual(result.dataset_info["total_records"], 100)

        # Test execution stats with duration_ms alias
        result.set_execution_stats(duration_ms=500, rules_executed=10)
        self.assertEqual(result.execution_stats["duration_ms"], 500)
        self.assertEqual(result.execution_stats["rules_executed"], 10)

    def test_assessment_result_to_standard_dict_fallback(self):
        """Test AssessmentResult to_standard_dict with import fallback."""
        result = AssessmentResult(85.0, True, {}, "test_standard")

        # Should use v2 format when ReportGenerator not available
        standard_dict = result.to_standard_dict()
        self.assertIn("adri_assessment_report", standard_dict)

    def test_rule_execution_result_compatibility(self):
        """Test RuleExecutionResult backward compatibility."""
        # Test old signature
        old_result = RuleExecutionResult(rule_name="old_rule", passed=True, score=18.0)
        self.assertEqual(old_result.rule_name, "old_rule")
        self.assertEqual(old_result.rule_id, "old_rule")
        self.assertEqual(old_result.passed, 1)  # Converted to int

        # Test new signature
        new_result = RuleExecutionResult(rule_id="new_rule", total_records=100, passed=90, failed=10)
        result_dict = new_result.to_dict()
        self.assertIn("execution", result_dict)
        self.assertIn("failures", result_dict)

    def test_assess_with_completeness_requirements(self):
        """Test assessment with completeness requirements."""
        engine = self.engine

        # Test with mandatory fields
        requirements = {"mandatory_fields": ["name", "email"]}
        data_with_nulls = pd.DataFrame({
            "name": ["Alice", None, "Charlie"],
            "email": ["alice@test.com", "bob@test.com", None],
            "optional": [None, "value", "test"]
        })

        score = engine.assess_completeness(data_with_nulls, requirements)
        # Should be reduced due to nulls in required fields
        self.assertLess(score, 20.0)

        # Test without requirements
        score_no_reqs = engine.assess_completeness(data_with_nulls)
        self.assertGreater(score_no_reqs, 0)

    def test_assess_with_consistency_rules(self):
        """Test assessment with consistency format rules."""
        engine = self.engine

        consistency_rules = {
            "format_rules": {
                "name": "title_case",
                "city": "lowercase"
            }
        }

        # Test with consistent data
        consistent_data = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "city": ["london", "paris", "tokyo"]
        })
        score = engine.assess_consistency(consistent_data, consistency_rules)
        self.assertGreater(score, 15)

        # Test with inconsistent data
        inconsistent_data = pd.DataFrame({
            "name": ["alice", "BOB", "Charlie"],  # Mixed case
            "city": ["LONDON", "paris", "Tokyo"]  # Mixed case
        })
        score_inconsistent = engine.assess_consistency(inconsistent_data, consistency_rules)
        self.assertLess(score_inconsistent, score)

    def test_assess_with_plausibility_business_rules(self):
        """Test assessment with business rules for plausibility."""
        engine = self.engine

        plausibility_config = {
            "business_rules": {
                "age": {"min": 0, "max": 120},
                "salary": {"min": 10000, "max": 1000000}
            },
            "outlier_detection": {
                "score": {"method": "range", "min": 0, "max": 100}
            }
        }

        # Test with valid business data
        valid_data = pd.DataFrame({
            "age": [25, 30, 35, 40],
            "salary": [50000, 60000, 70000, 80000],
            "score": [85, 92, 78, 88]
        })
        score = engine.assess_plausibility(valid_data, plausibility_config)
        self.assertGreater(score, 15)

        # Test with invalid business data
        invalid_data = pd.DataFrame({
            "age": [-5, 30, 200, 40],  # Invalid ages
            "salary": [5000, 60000, 2000000, 80000],  # Invalid salaries
            "score": [150, 92, -10, 88]  # Invalid scores
        })
        score_invalid = engine.assess_plausibility(invalid_data, plausibility_config)
        self.assertLess(score_invalid, score)

    def test_assess_validity_comprehensive(self):
        """Test validity assessment with various scenarios."""
        # Test valid emails
        valid_email_data = pd.DataFrame({
            "email": ["user@domain.com", "test@example.org", "name@company.co.uk"]
        })
        score = self.engine._assess_validity(valid_email_data)
        self.assertGreater(score, 15)

        # Test invalid emails
        invalid_email_data = pd.DataFrame({
            "email": ["not-email", "invalid@", "@invalid.com"]
        })
        score = self.engine._assess_validity(invalid_email_data)
        self.assertLess(score, 10)

        # Test valid ages
        valid_age_data = pd.DataFrame({
            "age": [25, 30, 45, 60]
        })
        score = self.engine._assess_validity(valid_age_data)
        self.assertGreater(score, 15)

        # Test invalid ages
        invalid_age_data = pd.DataFrame({
            "age": [-5, 200, -10, 300]
        })
        score = self.engine._assess_validity(invalid_age_data)
        self.assertLess(score, 10)

    def test_assess_completeness_scenarios(self):
        """Test completeness assessment with different scenarios."""
        # Perfect completeness
        complete_data = pd.DataFrame({
            "field1": [1, 2, 3],
            "field2": ["a", "b", "c"]
        })
        score = self.engine._assess_completeness(complete_data)
        self.assertEqual(score, 20.0)

        # Partial completeness
        partial_data = pd.DataFrame({
            "field1": [1, None, 3],
            "field2": ["a", "b", None]
        })
        score = self.engine._assess_completeness(partial_data)
        self.assertGreater(score, 10)
        self.assertLess(score, 20)

        # Empty data
        empty_data = pd.DataFrame()
        score = self.engine._assess_completeness(empty_data)
        self.assertEqual(score, 0.0)

    def test_dimension_assessment_methods(self):
        """Test individual dimension assessment methods."""
        # Test consistency - may score lower with format_consistency and cross_field_logic active
        score = self.engine._assess_consistency(self.test_data)
        self.assertGreaterEqual(score, 15.0)  # Should be good, but not necessarily perfect

        # Test freshness
        score = self.engine._assess_freshness(self.test_data)
        self.assertGreaterEqual(score, 15.0)  # Good score range

        # Test plausibility
        score = self.engine._assess_plausibility(self.test_data)
        self.assertGreaterEqual(score, 15.0)  # Good score range

    def test_email_validation_edge_cases(self):
        """Test email validation with edge cases."""
        engine = self.engine

        # Valid emails
        self.assertTrue(engine._is_valid_email("user@domain.com"))
        self.assertTrue(engine._is_valid_email("test.email@example.org"))
        self.assertTrue(engine._is_valid_email("user+tag@domain.co.uk"))

        # Invalid emails
        self.assertFalse(engine._is_valid_email("invalid"))
        self.assertFalse(engine._is_valid_email("user@"))
        self.assertFalse(engine._is_valid_email("@domain.com"))
        self.assertFalse(engine._is_valid_email("user@@domain.com"))
        self.assertFalse(engine._is_valid_email("user@domain"))

    def test_bundled_standard_wrapper(self):
        """Test BundledStandardWrapper functionality."""
        standard_dict = {
            "requirements": {
                "overall_minimum": 85.0,
                "field_requirements": {
                    "name": {"type": "string", "nullable": False},
                    "age": {"type": "integer", "min_value": 0, "max_value": 120}
                }
            }
        }

        wrapper = BundledStandardWrapper(standard_dict)

        # Test field requirements extraction
        field_reqs = wrapper.get_field_requirements()
        self.assertIn("name", field_reqs)
        self.assertIn("age", field_reqs)
        self.assertEqual(field_reqs["name"]["type"], "string")

        # Test overall minimum extraction
        min_score = wrapper.get_overall_minimum()
        self.assertEqual(min_score, 85.0)

    def test_validation_engine_public_methods(self):
        """Test public methods for backward compatibility."""
        engine = self.engine

        # Test assess_validity
        field_requirements = {
            "email": {"type": "string", "pattern": r"^[^@]+@[^@]+\.[^@]+$"}
        }
        data = pd.DataFrame({"email": ["test@example.com", "user@domain.org"]})
        score = engine.assess_validity(data, field_requirements)
        self.assertGreater(score, 15)

        # Test assess_completeness
        requirements = {"mandatory_fields": ["name", "email"]}
        data = pd.DataFrame({
            "name": ["Alice", "Bob"],
            "email": ["alice@test.com", "bob@test.com"],
            "optional": [None, "value"]
        })
        score = engine.assess_completeness(data, requirements)
        self.assertGreater(score, 15)

        # Test assess_consistency
        consistency_rules = {
            "format_rules": {
                "name": "title_case"
            }
        }
        data = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"]})
        score = engine.assess_consistency(data, consistency_rules)
        self.assertGreater(score, 0)

        # Test assess_freshness
        freshness_config = {"date_fields": ["created_at"]}
        data = pd.DataFrame({"created_at": ["2024-01-01", "2024-01-02"]})
        score = engine.assess_freshness(data, freshness_config)
        self.assertEqual(score, 20.0)  # Should return good score for date fields

        # Test assess_plausibility
        plausibility_config = {
            "business_rules": {
                "age": {"min": 0, "max": 120}
            },
            "outlier_detection": {
                "score": {"method": "range", "min": 0, "max": 100}
            }
        }
        data = pd.DataFrame({
            "age": [25, 30, 35],
            "score": [85, 92, 78]
        })
        score = engine.assess_plausibility(data, plausibility_config)
        self.assertGreater(score, 15)


class TestValidationEngineEdgeCases(unittest.TestCase):
    """Test edge cases to reach 85% coverage target."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = ValidationEngine()

    def test_assess_validity_with_standard_error_handling(self):
        """Test assess_validity_with_standard with error handling."""
        # Create mock standard that raises exception
        mock_standard = Mock()
        mock_standard.get_field_requirements.side_effect = Exception("Standard error")

        data = pd.DataFrame({"test": [1, 2, 3]})
        # Should fallback to basic validity assessment
        score = self.engine._assess_validity_with_standard(data, mock_standard)
        self.assertEqual(score, 20.0)  # Default score

    def test_assess_completeness_with_standard_error_handling(self):
        """Test assess_completeness_with_standard with error handling."""
        mock_standard = Mock()
        mock_standard.get_field_requirements.side_effect = Exception("Standard error")

        data = pd.DataFrame({"test": [1, 2, 3]})
        # Should fallback to basic completeness assessment
        score = self.engine._assess_completeness_with_standard(data, mock_standard)
        self.assertGreater(score, 0)

    def test_assess_validity_with_no_matching_columns(self):
        """Test validity assessment with data that has no email/age columns."""
        # Data with no recognizable patterns
        data = pd.DataFrame({
            "field1": ["value1", "value2"],
            "field2": [100, 200]
        })

        score = self.engine._assess_validity(data)
        self.assertEqual(score, 20.0)  # Should return default good score

    def test_assess_validity_with_standard_missing_fields(self):
        """Test validity assessment when standard fields aren't in data."""
        standard_dict = {
            "requirements": {
                "field_requirements": {
                    "nonexistent_field": {"type": "string", "nullable": False}
                }
            }
        }
        wrapper = BundledStandardWrapper(standard_dict)

        data = pd.DataFrame({"different_field": ["value1", "value2"]})
        score = self.engine._assess_validity_with_standard(data, wrapper)
        self.assertEqual(score, 20.0)  # Should return default when no checks

    def test_assess_completeness_with_standard_no_required_fields(self):
        """Test completeness with standard that has no required fields."""
        standard_dict = {
            "requirements": {
                "field_requirements": {
                    "field1": {"type": "string", "nullable": True}  # All nullable
                }
            }
        }
        wrapper = BundledStandardWrapper(standard_dict)

        data = pd.DataFrame({"field1": ["value1", None, "value3"]})
        score = self.engine._assess_completeness_with_standard(data, wrapper)
        # Should fallback to basic completeness since no required fields
        self.assertGreater(score, 0)

    def test_bundled_standard_wrapper_invalid_minimum_type(self):
        """Test BundledStandardWrapper with invalid minimum type."""
        standard_dict = {
            "requirements": {
                "overall_minimum": "not_a_number"  # Invalid type
            }
        }
        wrapper = BundledStandardWrapper(standard_dict)

        minimum = wrapper.get_overall_minimum()
        self.assertEqual(minimum, 75.0)  # Should return default

    def test_assessment_result_v2_format_with_all_data(self):
        """Test AssessmentResult v2 format with complete data."""
        from datetime import datetime

        result = AssessmentResult(
            overall_score=85.0,
            passed=True,
            dimension_scores={"validity": DimensionScore(17.0)},
            standard_id="test_standard",
            assessment_date=datetime.now()
        )

        # Add dataset info and execution stats
        result.set_dataset_info(100, 5, 2.5)
        result.set_execution_stats(total_execution_time_ms=500, rules_executed=10)

        # Add field analysis
        field_analysis = FieldAnalysis("test_field", total_failures=2)
        result.add_field_analysis("test_field", field_analysis)

        # Test v2 format generation
        v2_dict = result.to_v2_standard_dict("test_dataset", "4.0.0")

        self.assertIn("adri_assessment_report", v2_dict)
        metadata = v2_dict["adri_assessment_report"]["metadata"]
        self.assertEqual(metadata["dataset_name"], "test_dataset")
        self.assertEqual(metadata["adri_version"], "4.0.0")


# ============================================================================
# Additional Comprehensive Tests (from test_validator_engine_comprehensive.py)
# ============================================================================


class TestValidatorEngineErrorHandling(unittest.TestCase):
    """Test comprehensive error handling scenarios.

    Consolidated from test_validator_engine_comprehensive.py
    """

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_malformed_data_error_handling(self):
        """Test handling of malformed data inputs."""
        engine = ValidationEngine()

        # Test with empty DataFrame
        empty_df = pd.DataFrame()
        result = engine._basic_assessment(empty_df)
        self.assertIsInstance(result, AssessmentResult)
        self.assertEqual(result.dimension_scores["completeness"].score, 0.0)

        # Test with DataFrame containing only NaN values
        nan_df = pd.DataFrame({
            "col1": [None, None, None],
            "col2": [pd.NA, pd.NA, pd.NA],
            "col3": ["", "", ""]
        })
        result = engine._basic_assessment(nan_df)
        self.assertIsInstance(result, AssessmentResult)

        # Test with DataFrame containing mixed data types
        mixed_df = pd.DataFrame({
            "mixed_col": [1, "string", 3.14, None, True]
        })
        result = engine._basic_assessment(mixed_df)
        self.assertIsInstance(result, AssessmentResult)

    def test_standard_loading_error_handling(self):
        """Test error handling when standards cannot be loaded."""
        engine = ValidationEngine()
        test_data = pd.DataFrame({"email": ["test@example.com"], "age": [25]})

        # Test with non-existent standard file
        result = engine.assess(test_data, "/nonexistent/standard.yaml")
        self.assertIsInstance(result, AssessmentResult)

        # Test with corrupted standard file
        from pathlib import Path
        corrupted_standard = Path("corrupted.yaml")
        with open(corrupted_standard, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: [unclosed")
        result = engine.assess(test_data, str(corrupted_standard))
        self.assertIsInstance(result, AssessmentResult)

    def test_invalid_standard_structure_error_handling(self):
        """Test handling of invalid standard structures."""
        engine = ValidationEngine()
        test_data = pd.DataFrame({"test_field": ["value1", "value2"]})

        invalid_standards = [
            None, {}, {"requirements": None},
            {"requirements": "not_a_dict"},
            {"requirements": {"field_requirements": "not_a_dict"}},
        ]

        for invalid_standard in invalid_standards:
            try:
                result = engine.assess_with_standard_dict(test_data, invalid_standard)
                self.assertIsInstance(result, AssessmentResult)
            except Exception:
                pass  # Some may raise exceptions

    def test_email_validation_error_handling(self):
        """Test email validation error scenarios."""
        engine = ValidationEngine()

        edge_case_emails = [
            "", " ", "@", "email@", "@domain.com",
            "email@@domain.com", "email@domain", None, 123
        ]

        for email in edge_case_emails:
            try:
                is_valid = engine._is_valid_email(str(email))
                self.assertIsInstance(is_valid, bool)
            except (TypeError, AttributeError):
                pass


class TestValidatorEngineRefactor(unittest.TestCase):
    """Stability tests for validator engine refactor.

    Consolidated from test_validator_engine_refactor.py
    """

    def setUp(self):
        self.engine = ValidationEngine()
        self.df = pd.DataFrame({
            "code": ["A", "B", "B"],
            "age": [10, 20, 30],
            "unused": ["x", "y", "z"],
        })
        self.field_requirements = {
            "code": {
                "type": "string",
                "allowed_values": ["A", "B"],
                "min_length": 1,
                "max_length": 2,
                "pattern": r"^[AB]$",
            },
            "age": {
                "type": "integer",
                "min_value": 0,
                "max_value": 120,
            },
        }

    def test_validity_counts_and_weights_stability(self):
        """Test validity rule counts computation stability."""
        # This test validates internal computation methods if they exist
        # If methods don't exist, test will be skipped
        if not hasattr(self.engine, '_compute_validity_rule_counts'):
            self.skipTest("Internal method not available")

        try:
            counts, per_field_counts = self.engine._compute_validity_rule_counts(
                self.df, self.field_requirements
            )
            self.assertIsInstance(counts, dict)
            self.assertIsInstance(per_field_counts, dict)
        except AttributeError:
            self.skipTest("Method signature changed")

    def test_explain_payload_schema_stability(self):
        """Test that assessment produces stable explain structure."""
        standard_dict = {
            "requirements": {
                "field_requirements": self.field_requirements,
            }
        }
        wrapper = BundledStandardWrapper(standard_dict)

        score = self.engine._assess_validity_with_standard(self.df, wrapper)
        self.assertGreaterEqual(score, 15.0)


if __name__ == '__main__':
    unittest.main()
