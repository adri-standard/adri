"""
Additional tests for AssessmentEngine to improve coverage.
Focuses on testing the missing lines identified in coverage analysis.
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from adri.core.assessor import (
    AssessmentEngine,
    AssessmentResult,
    BundledStandardWrapper,
    DataQualityAssessor,
    DimensionScore,
    FieldAnalysis,
    RuleExecutionResult,
)


class TestBundledStandardWrapper:
    """Test the BundledStandardWrapper class."""

    def test_bundled_standard_wrapper_init(self):
        """Test BundledStandardWrapper initialization."""
        standard_dict = {
            "requirements": {
                "field_requirements": {"name": {"type": "string"}},
                "overall_minimum": 80.0,
            }
        }
        wrapper = BundledStandardWrapper(standard_dict)
        assert wrapper.standard_dict == standard_dict

    def test_get_field_requirements(self):
        """Test getting field requirements."""
        standard_dict = {
            "requirements": {
                "field_requirements": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                }
            }
        }
        wrapper = BundledStandardWrapper(standard_dict)
        field_reqs = wrapper.get_field_requirements()
        assert field_reqs == {"name": {"type": "string"}, "age": {"type": "integer"}}

    def test_get_field_requirements_empty(self):
        """Test getting field requirements when empty."""
        wrapper = BundledStandardWrapper({})
        field_reqs = wrapper.get_field_requirements()
        assert field_reqs == {}

    def test_get_overall_minimum(self):
        """Test getting overall minimum score."""
        standard_dict = {"requirements": {"overall_minimum": 85.0}}
        wrapper = BundledStandardWrapper(standard_dict)
        assert wrapper.get_overall_minimum() == 85.0

    def test_get_overall_minimum_default(self):
        """Test getting overall minimum with default value."""
        wrapper = BundledStandardWrapper({})
        assert wrapper.get_overall_minimum() == 75.0


class TestAssessmentResult:
    """Test AssessmentResult class methods."""

    def test_assessment_result_init_with_all_params(self):
        """Test AssessmentResult initialization with all parameters."""
        dimension_scores = {"validity": DimensionScore(18.0)}
        metadata = {"test": "value"}
        assessment_date = datetime.now()

        result = AssessmentResult(
            overall_score=85.0,
            passed=True,
            dimension_scores=dimension_scores,
            standard_id="test_standard",
            assessment_date=assessment_date,
            metadata=metadata,
        )

        assert result.overall_score == 85.0
        assert result.passed is True
        assert result.dimension_scores == dimension_scores
        assert result.standard_id == "test_standard"
        assert result.assessment_date == assessment_date
        assert result.metadata == metadata
        assert result.rule_execution_log == []
        assert result.field_analysis == {}

    def test_add_rule_execution(self):
        """Test adding rule execution results."""
        result = AssessmentResult(85.0, True, {})
        rule_result = RuleExecutionResult(rule_id="test_rule")

        result.add_rule_execution(rule_result)
        assert len(result.rule_execution_log) == 1
        assert result.rule_execution_log[0] == rule_result

    def test_add_field_analysis(self):
        """Test adding field analysis."""
        result = AssessmentResult(85.0, True, {})
        field_analysis = FieldAnalysis("test_field")

        result.add_field_analysis("test_field", field_analysis)
        assert "test_field" in result.field_analysis
        assert result.field_analysis["test_field"] == field_analysis

    def test_set_dataset_info(self):
        """Test setting dataset information."""
        result = AssessmentResult(85.0, True, {})
        result.set_dataset_info(1000, 10, 5.5)

        assert hasattr(result, "dataset_info")
        assert result.dataset_info["total_records"] == 1000
        assert result.dataset_info["total_fields"] == 10
        assert result.dataset_info["size_mb"] == 5.5

    def test_set_execution_stats_with_duration_ms(self):
        """Test setting execution stats with duration_ms parameter."""
        result = AssessmentResult(85.0, True, {})
        result.set_execution_stats(duration_ms=1500, rules_executed=5)

        assert hasattr(result, "execution_stats")
        assert result.execution_stats["total_execution_time_ms"] == 1500
        assert result.execution_stats["duration_ms"] == 1500
        assert result.execution_stats["rules_executed"] == 5

    def test_set_execution_stats_with_total_execution_time_ms(self):
        """Test setting execution stats with total_execution_time_ms parameter."""
        result = AssessmentResult(85.0, True, {})
        result.set_execution_stats(total_execution_time_ms=2000)

        assert result.execution_stats["total_execution_time_ms"] == 2000
        assert result.execution_stats["duration_ms"] == 2000
        assert result.execution_stats["rules_executed"] == 0

    def test_to_standard_dict(self):
        """Test converting to standard dictionary format."""
        dimension_scores = {"validity": DimensionScore(18.0)}
        result = AssessmentResult(85.0, True, dimension_scores)

        with patch("adri.core.report_generator.ReportGenerator") as mock_generator:
            mock_instance = Mock()
            mock_generator.return_value = mock_instance
            mock_instance.generate_report.return_value = {"test": "report"}

            report_dict = result.to_standard_dict()

            mock_generator.assert_called_once()
            mock_instance.generate_report.assert_called_once_with(result)
            assert report_dict == {"test": "report"}

    def test_to_v2_standard_dict_with_defaults(self):
        """Test converting to v2 standard dictionary with default values."""
        dimension_scores = {"validity": DimensionScore(18.0)}
        result = AssessmentResult(85.0, True, dimension_scores)

        report_dict = result.to_v2_standard_dict()

        assert "adri_assessment_report" in report_dict
        report = report_dict["adri_assessment_report"]
        assert "metadata" in report
        assert "summary" in report
        assert report["summary"]["overall_score"] == 85.0
        assert report["summary"]["overall_passed"] is True

    def test_to_v2_standard_dict_with_all_data(self):
        """Test converting to v2 standard dictionary with all data."""
        dimension_scores = {
            "validity": DimensionScore(18.0),
            "completeness": DimensionScore(19.0),
        }
        result = AssessmentResult(
            85.0, True, dimension_scores, "test_standard", datetime.now()
        )

        # Add dataset info and execution stats
        result.set_dataset_info(1000, 10, 5.5)
        result.set_execution_stats(1500, 3)

        # Add rule execution and field analysis
        rule_result = RuleExecutionResult(rule_id="test_rule")
        result.add_rule_execution(rule_result)

        field_analysis = FieldAnalysis("test_field", total_failures=2)
        result.add_field_analysis("test_field", field_analysis)

        report_dict = result.to_v2_standard_dict("test_dataset", "2.0.0")

        report = report_dict["adri_assessment_report"]
        assert report["metadata"]["dataset_name"] == "test_dataset"
        assert report["metadata"]["adri_version"] == "2.0.0"
        assert report["metadata"]["standard_id"] == "test_standard"
        assert "dataset_info" in report["metadata"]
        assert "execution_stats" in report["metadata"]

    def test_to_dict(self):
        """Test to_dict method."""
        result = AssessmentResult(85.0, True, {})

        with patch.object(result, "to_v2_standard_dict") as mock_to_v2:
            mock_to_v2.return_value = {"test": "dict"}

            result_dict = result.to_dict()

            mock_to_v2.assert_called_once()
            assert result_dict == {"test": "dict"}


class TestDimensionScore:
    """Test DimensionScore class."""

    def test_dimension_score_init_with_all_params(self):
        """Test DimensionScore initialization with all parameters."""
        issues = ["issue1", "issue2"]
        details = {"field1": 18.0}

        score = DimensionScore(15.0, 20.0, issues, details)

        assert score.score == 15.0
        assert score.max_score == 20.0
        assert score.issues == issues
        assert score.details == details

    def test_dimension_score_init_with_defaults(self):
        """Test DimensionScore initialization with default parameters."""
        score = DimensionScore(15.0)

        assert score.score == 15.0
        assert score.max_score == 20.0
        assert score.issues == []
        assert score.details == {}

    def test_percentage_calculation(self):
        """Test percentage calculation."""
        score = DimensionScore(15.0, 20.0)
        assert score.percentage() == 75.0

        score = DimensionScore(10.0, 25.0)
        assert score.percentage() == 40.0


class TestFieldAnalysis:
    """Test FieldAnalysis class."""

    def test_field_analysis_init_with_all_params(self):
        """Test FieldAnalysis initialization with all parameters."""
        rules_applied = ["rule1", "rule2"]
        recommended_actions = ["action1", "action2"]

        analysis = FieldAnalysis(
            field_name="test_field",
            data_type="string",
            null_count=5,
            total_count=100,
            rules_applied=rules_applied,
            overall_field_score=85.0,
            total_failures=3,
            ml_readiness="good",
            recommended_actions=recommended_actions,
        )

        assert analysis.field_name == "test_field"
        assert analysis.data_type == "string"
        assert analysis.null_count == 5
        assert analysis.total_count == 100
        assert analysis.rules_applied == rules_applied
        assert analysis.overall_field_score == 85.0
        assert analysis.total_failures == 3
        assert analysis.ml_readiness == "good"
        assert analysis.recommended_actions == recommended_actions
        assert analysis.completeness == 0.95  # (100-5)/100

    def test_field_analysis_init_with_defaults(self):
        """Test FieldAnalysis initialization with default parameters."""
        analysis = FieldAnalysis("test_field")

        assert analysis.field_name == "test_field"
        assert analysis.data_type is None
        assert analysis.null_count is None
        assert analysis.total_count is None
        assert analysis.rules_applied == []
        assert analysis.overall_field_score is None
        assert analysis.total_failures == 0
        assert analysis.ml_readiness is None
        assert analysis.recommended_actions == []
        assert analysis.completeness is None

    def test_field_analysis_completeness_zero_total(self):
        """Test completeness calculation with zero total count."""
        analysis = FieldAnalysis("test_field", null_count=0, total_count=0)
        assert analysis.completeness == 0.0

    def test_to_dict_with_all_fields(self):
        """Test converting field analysis to dictionary with all fields."""
        analysis = FieldAnalysis(
            field_name="test_field",
            data_type="string",
            null_count=5,
            total_count=100,
            rules_applied=["rule1"],
            overall_field_score=85.0,
            total_failures=3,
            ml_readiness="good",
            recommended_actions=["action1"],
        )

        result_dict = analysis.to_dict()

        assert result_dict["field_name"] == "test_field"
        assert result_dict["data_type"] == "string"
        assert result_dict["null_count"] == 5
        assert result_dict["total_count"] == 100
        assert result_dict["completeness"] == 0.95
        assert result_dict["rules_applied"] == ["rule1"]
        assert result_dict["overall_field_score"] == 85.0
        assert result_dict["total_failures"] == 3
        assert result_dict["ml_readiness"] == "good"
        assert result_dict["recommended_actions"] == ["action1"]

    def test_to_dict_with_minimal_fields(self):
        """Test converting field analysis to dictionary with minimal fields."""
        analysis = FieldAnalysis("test_field")

        result_dict = analysis.to_dict()

        assert result_dict["field_name"] == "test_field"
        assert result_dict["rules_applied"] == []
        assert result_dict["overall_field_score"] is None
        assert result_dict["total_failures"] == 0
        assert result_dict["ml_readiness"] is None
        assert result_dict["recommended_actions"] == []
        # Should not include None fields
        assert "data_type" not in result_dict
        assert "null_count" not in result_dict
        assert "total_count" not in result_dict
        assert "completeness" not in result_dict


class TestRuleExecutionResult:
    """Test RuleExecutionResult class."""

    def test_rule_execution_result_new_signature(self):
        """Test RuleExecutionResult with new signature."""
        sample_failures = ["failure1", "failure2"]
        failure_patterns = {"pattern1": 5}

        result = RuleExecutionResult(
            rule_id="test_rule",
            dimension="validity",
            field="test_field",
            rule_definition="test definition",
            total_records=100,
            passed=95,
            failed=5,
            rule_score=18.0,
            rule_weight=1.0,
            execution_time_ms=150,
            sample_failures=sample_failures,
            failure_patterns=failure_patterns,
            message="test message",
        )

        assert result.rule_id == "test_rule"
        assert result.rule_name == "test_rule"  # Backward compatibility
        assert result.dimension == "validity"
        assert result.field == "test_field"
        assert result.rule_definition == "test definition"
        assert result.total_records == 100
        assert result.passed == 95
        assert result.failed == 5
        assert result.rule_score == 18.0
        assert result.score == 18.0  # Backward compatibility
        assert result.rule_weight == 1.0
        assert result.execution_time_ms == 150
        assert result.sample_failures == sample_failures
        assert result.failure_patterns == failure_patterns
        assert result.message == "test message"

    def test_rule_execution_result_old_signature(self):
        """Test RuleExecutionResult with old signature for backward compatibility."""
        result = RuleExecutionResult(
            rule_name="old_rule",
            passed=True,
            score=19.0,
            message="old message",
            dimension="completeness",
            field="old_field",
        )

        assert result.rule_name == "old_rule"
        assert result.rule_id == "old_rule"
        assert result.passed is True
        assert result.score == 19.0
        assert result.rule_score == 19.0
        assert result.message == "old message"
        assert result.dimension == "completeness"
        assert result.field == "old_field"

    def test_to_dict_complete(self):
        """Test converting rule execution result to dictionary."""
        result = RuleExecutionResult(
            rule_id="test_rule",
            dimension="validity",
            field="test_field",
            rule_definition="test definition",
            total_records=100,
            passed=95,
            failed=5,
            rule_score=18.0,
            rule_weight=1.0,
            execution_time_ms=150,
            sample_failures=["failure1"],
            failure_patterns={"pattern1": 5},
            message="test message",
        )

        result_dict = result.to_dict()

        assert result_dict["rule_id"] == "test_rule"
        assert result_dict["rule_name"] == "test_rule"
        assert result_dict["dimension"] == "validity"
        assert result_dict["field"] == "test_field"
        assert result_dict["rule_definition"] == "test definition"
        assert result_dict["total_records"] == 100
        assert result_dict["passed"] == 95
        assert result_dict["failed"] == 5
        assert result_dict["rule_score"] == 18.0
        assert result_dict["score"] == 18.0
        assert result_dict["rule_weight"] == 1.0
        assert result_dict["execution_time_ms"] == 150
        assert result_dict["sample_failures"] == ["failure1"]
        assert result_dict["failure_patterns"] == {"pattern1": 5}
        assert result_dict["message"] == "test message"

        # Check v2.0 compliance fields
        assert "execution" in result_dict
        assert result_dict["execution"]["total_records"] == 100
        assert result_dict["execution"]["passed"] == 95
        assert result_dict["execution"]["failed"] == 5
        assert result_dict["execution"]["execution_time_ms"] == 150
        assert result_dict["execution"]["rule_score"] == 18.0
        assert result_dict["execution"]["rule_weight"] == 1.0

        assert "failures" in result_dict
        assert result_dict["failures"]["sample_failures"] == ["failure1"]
        assert result_dict["failures"]["failure_patterns"] == {"pattern1": 5}
        assert result_dict["failures"]["total_failed"] == 5

    def test_to_dict_with_boolean_passed(self):
        """Test to_dict with boolean passed value."""
        result = RuleExecutionResult(
            rule_id="test_rule",
            total_records=100,
            passed=True,  # Boolean instead of int
            failed=5,
        )

        result_dict = result.to_dict()

        # The current implementation keeps boolean as-is, so test actual behavior
        assert result_dict["passed"] is True
        assert result_dict["execution"]["passed"] is True


class TestDataQualityAssessor:
    """Test DataQualityAssessor class."""

    def test_data_quality_assessor_init(self):
        """Test DataQualityAssessor initialization."""
        assessor = DataQualityAssessor()
        assert hasattr(assessor, "engine")
        assert isinstance(assessor.engine, AssessmentEngine)

    def test_assess_with_pandas_series(self):
        """Test assess method with pandas Series."""
        assessor = DataQualityAssessor()
        series = pd.Series([1, 2, 3, 4, 5], name="test_column")

        with patch.object(assessor.engine, "_basic_assessment") as mock_basic:
            mock_basic.return_value = AssessmentResult(85.0, True, {})

            assessor.assess(series)

            mock_basic.assert_called_once()
            # Check that series was converted to DataFrame
            call_args = mock_basic.call_args[0][0]
            assert isinstance(call_args, pd.DataFrame)
            assert "test_column" in call_args.columns

    def test_assess_with_dict(self):
        """Test assess method with dictionary."""
        assessor = DataQualityAssessor()
        data_dict = {"name": "John", "age": 30}

        with patch.object(assessor.engine, "_basic_assessment") as mock_basic:
            mock_basic.return_value = AssessmentResult(85.0, True, {})

            assessor.assess(data_dict)

            mock_basic.assert_called_once()
            # Check that dict was converted to DataFrame
            call_args = mock_basic.call_args[0][0]
            assert isinstance(call_args, pd.DataFrame)
            assert "name" in call_args.columns
            assert "age" in call_args.columns

    def test_assess_with_list(self):
        """Test assess method with list."""
        assessor = DataQualityAssessor()
        data_list = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]

        with patch.object(assessor.engine, "_basic_assessment") as mock_basic:
            mock_basic.return_value = AssessmentResult(85.0, True, {})

            assessor.assess(data_list)

            mock_basic.assert_called_once()
            # Check that list was converted to DataFrame
            call_args = mock_basic.call_args[0][0]
            assert isinstance(call_args, pd.DataFrame)
            assert len(call_args) == 2

    def test_assess_with_standard_path(self):
        """Test assess method with standard path."""
        assessor = DataQualityAssessor()
        data = pd.DataFrame({"name": ["John", "Jane"], "age": [30, 25]})

        with patch.object(assessor.engine, "assess") as mock_assess:
            mock_assess.return_value = AssessmentResult(85.0, True, {})

            assessor.assess(data, "test_standard.yaml")

            mock_assess.assert_called_once_with(data, "test_standard.yaml")


class TestAssessmentEngineAdvanced:
    """Test advanced AssessmentEngine methods."""

    def test_assess_with_standard_dict(self):
        """Test assess_with_standard_dict method."""
        engine = AssessmentEngine()
        data = pd.DataFrame({"name": ["John", "Jane"], "age": [30, 25]})
        standard_dict = {
            "requirements": {
                "field_requirements": {
                    "name": {"type": "string", "nullable": False},
                    "age": {"type": "integer", "min_value": 0, "max_value": 150},
                },
                "overall_minimum": 80.0,
            }
        }

        result = engine.assess_with_standard_dict(data, standard_dict)

        assert isinstance(result, AssessmentResult)
        assert 0 <= result.overall_score <= 100
        assert isinstance(result.passed, bool)
        assert len(result.dimension_scores) == 5

    def test_assess_with_standard_dict_exception(self):
        """Test assess_with_standard_dict with exception handling."""
        engine = AssessmentEngine()
        data = pd.DataFrame({"name": ["John", "Jane"], "age": [30, 25]})

        # Invalid standard dict that will cause exception
        standard_dict = {"invalid": "structure"}

        # The method should handle the exception and return a result
        result = engine.assess_with_standard_dict(data, standard_dict)

        # Should return a valid AssessmentResult even with invalid standard
        assert isinstance(result, AssessmentResult)
        assert 0 <= result.overall_score <= 100

    def test_assess_with_load_standard_exception(self):
        """Test assess method with load_standard exception."""
        engine = AssessmentEngine()
        data = pd.DataFrame({"name": ["John", "Jane"], "age": [30, 25]})

        with patch("adri.cli.commands.load_standard") as mock_load:
            mock_load.side_effect = Exception("Failed to load standard")

            result = engine.assess(data, "invalid_standard.yaml")

            # Should fallback to basic assessment
            assert isinstance(result, AssessmentResult)
            assert 0 <= result.overall_score <= 100

    def test_check_field_type_edge_cases(self):
        """Test _check_field_type with various edge cases."""
        engine = AssessmentEngine()

        # Test integer type
        assert engine._check_field_type("123", {"type": "integer"}) is True
        assert engine._check_field_type("abc", {"type": "integer"}) is False

        # Test float type
        assert engine._check_field_type("123.45", {"type": "float"}) is True
        assert engine._check_field_type("abc", {"type": "float"}) is False

        # Test string type
        assert engine._check_field_type("hello", {"type": "string"}) is True
        assert engine._check_field_type(123, {"type": "string"}) is False

        # Test boolean type
        assert engine._check_field_type(True, {"type": "boolean"}) is True
        assert engine._check_field_type("true", {"type": "boolean"}) is True
        assert engine._check_field_type("1", {"type": "boolean"}) is True
        assert engine._check_field_type("invalid", {"type": "boolean"}) is False

        # Test date type
        assert engine._check_field_type("2023-01-01", {"type": "date"}) is True
        assert engine._check_field_type("01/01/2023", {"type": "date"}) is True
        assert engine._check_field_type("invalid-date", {"type": "date"}) is False

        # Test unknown type
        assert engine._check_field_type("value", {"type": "unknown"}) is True

        # Test exception handling
        assert engine._check_field_type(None, {"type": "integer"}) is False

    def test_check_field_pattern_edge_cases(self):
        """Test _check_field_pattern with various edge cases."""
        engine = AssessmentEngine()

        # Test with valid pattern
        field_req = {"pattern": r"^[a-zA-Z]+$"}
        assert engine._check_field_pattern("hello", field_req) is True
        assert engine._check_field_pattern("hello123", field_req) is False

        # Test with no pattern
        field_req = {}
        assert engine._check_field_pattern("anything", field_req) is True

        # Test with invalid regex
        field_req = {"pattern": "["}  # Invalid regex
        assert engine._check_field_pattern("test", field_req) is False

    def test_check_field_range_edge_cases(self):
        """Test _check_field_range with various edge cases."""
        engine = AssessmentEngine()

        # Test with min and max values
        field_req = {"min_value": 10, "max_value": 100}
        assert engine._check_field_range("50", field_req) is True
        assert engine._check_field_range("5", field_req) is False
        assert engine._check_field_range("150", field_req) is False

        # Test with only min value
        field_req = {"min_value": 10}
        assert engine._check_field_range("15", field_req) is True
        assert engine._check_field_range("5", field_req) is False

        # Test with only max value
        field_req = {"max_value": 100}
        assert engine._check_field_range("50", field_req) is True
        assert engine._check_field_range("150", field_req) is False

        # Test with no range constraints
        field_req = {}
        assert engine._check_field_range("anything", field_req) is True

        # Test with non-numeric value
        field_req = {"min_value": 10, "max_value": 100}
        assert engine._check_field_range("non-numeric", field_req) is True

    def test_is_valid_email_edge_cases(self):
        """Test _is_valid_email with various edge cases."""
        engine = AssessmentEngine()

        # Valid emails
        assert engine._is_valid_email("test@example.com") is True
        assert engine._is_valid_email("user.name@domain.co.uk") is True

        # Invalid emails
        assert engine._is_valid_email("invalid-email") is False
        assert engine._is_valid_email("test@@example.com") is False  # Multiple @
        assert engine._is_valid_email("test@") is False
        assert engine._is_valid_email("@example.com") is False
        assert engine._is_valid_email("test@example") is False  # No TLD

    def test_assess_validity_with_age_column(self):
        """Test _assess_validity with age column."""
        engine = AssessmentEngine()
        data = pd.DataFrame(
            {"age": [25, 30, 200, -5, "invalid"]}  # Mix of valid and invalid ages
        )

        score = engine._assess_validity(data)

        # Should detect invalid ages and return score < 20
        assert 0 <= score <= 20
        assert score < 20  # Should be less than perfect due to invalid values

    def test_assess_validity_with_email_column(self):
        """Test _assess_validity with email column."""
        engine = AssessmentEngine()
        data = pd.DataFrame(
            {"email": ["valid@test.com", "invalid-email", "another@test.com"]}
        )

        score = engine._assess_validity(data)

        # Should detect invalid email and return score < 20
        assert 0 <= score <= 20
        assert score < 20  # Should be less than perfect due to invalid email

    def test_assess_validity_no_special_columns(self):
        """Test _assess_validity with no special columns."""
        engine = AssessmentEngine()
        data = pd.DataFrame({"name": ["John", "Jane"], "value": [1, 2]})

        score = engine._assess_validity(data)

        # Should return default good score when no special columns
        assert score == 18.0

    def test_assess_completeness_empty_data(self):
        """Test _assess_completeness with empty data."""
        engine = AssessmentEngine()
        data = pd.DataFrame()

        score = engine._assess_completeness(data)

        assert score == 0.0

    def test_assess_completeness_with_missing_values(self):
        """Test _assess_completeness with missing values."""
        engine = AssessmentEngine()
        data = pd.DataFrame({"name": ["John", None, "Jane"], "age": [30, 25, None]})

        score = engine._assess_completeness(data)

        # Should calculate completeness based on missing values
        # 2 missing out of 6 total cells = 4/6 = 0.667 completeness
        # Score should be 0.667 * 20 = 13.33
        assert 0 <= score <= 20
        assert score < 20  # Should be less than perfect due to missing values
