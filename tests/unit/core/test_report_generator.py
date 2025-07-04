"""
Tests for the template-driven ReportGenerator.

This module tests the new compile-time template approach for generating
ADRI v0.1.0 compliant assessment reports.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from adri.core.assessor import AssessmentResult, DimensionScore
from adri.core.report_generator import ReportGenerator
from adri.core.report_templates import (
    ADRI_ASSESSMENT_REPORT_TEMPLATE_V0_1_0,
    ASSESSMENT_ID_PATTERN,
    DIMENSION_SCORE_RANGES,
    OVERALL_SCORE_RANGE,
    TIMESTAMP_PATTERN,
)


class TestReportGenerator:
    """Test the ReportGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = ReportGenerator()

        # Create test dimension scores
        self.dimension_scores = {
            "validity": DimensionScore(18.0),
            "completeness": DimensionScore(19.0),
            "consistency": DimensionScore(16.0),
            "freshness": DimensionScore(19.0),
            "plausibility": DimensionScore(15.5),
        }

        # Create test assessment result
        self.assessment_result = AssessmentResult(
            overall_score=87.5,
            passed=True,
            dimension_scores=self.dimension_scores,
            standard_id="test-standard",
        )

    def test_generator_initialization(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator()
        assert generator.template == ADRI_ASSESSMENT_REPORT_TEMPLATE_V0_1_0
        assert generator.template["standard_metadata"]["version"] == "0.1.0"

    def test_generate_assessment_id_format(self):
        """Test assessment ID generation follows correct pattern."""
        timestamp = datetime(2025, 7, 3, 17, 30, 15)

        with patch("random.choices") as mock_choices:
            mock_choices.return_value = ["a", "b", "c", "1", "2", "3"]
            assessment_id = self.generator._generate_assessment_id(timestamp)

        expected = "adri_20250703_173015_abc123"
        assert assessment_id == expected

        # Test pattern compliance
        import re

        pattern = ASSESSMENT_ID_PATTERN
        assert re.match(pattern, assessment_id)

    def test_build_metadata_section(self):
        """Test metadata section generation."""
        timestamp = datetime(2025, 7, 3, 17, 30, 15)
        assessment_id = "adri_20250703_173015_abc123"

        metadata = self.generator._build_metadata(
            self.assessment_result, assessment_id, timestamp
        )

        # Check required fields
        assert metadata["assessment_id"] == assessment_id
        assert metadata["timestamp"] == "2025-07-03T17:30:15Z"
        assert metadata["adri_version"] == "0.1.0"

        # Check standard_applied structure
        assert "standard_applied" in metadata
        assert metadata["standard_applied"]["id"] == "test-standard"
        assert metadata["standard_applied"]["version"] == "1.0.0"
        assert metadata["standard_applied"]["domain"] == "data_quality"

        # Check dataset structure
        assert "dataset" in metadata
        assert "execution" in metadata

    def test_build_summary_section(self):
        """Test summary section generation."""
        summary = self.generator._build_summary(self.assessment_result)

        # Check overall score
        assert summary["overall_score"] == 87.5

        # Check dimension scores extraction
        expected_scores = {
            "validity": 18.0,
            "completeness": 19.0,
            "consistency": 16.0,
            "freshness": 19.0,
            "plausibility": 15.5,
        }
        assert summary["dimension_scores"] == expected_scores

        # Check pass/fail status
        pass_fail = summary["pass_fail_status"]
        assert pass_fail["overall_passed"] is True
        assert pass_fail["failed_dimensions"] == []  # All scores >= 15.0
        assert pass_fail["critical_issues"] == 0
        assert pass_fail["total_failures"] == 0

    def test_build_summary_with_failed_dimensions(self):
        """Test summary section with failed dimensions."""
        # Create assessment with low scores
        low_scores = {
            "validity": DimensionScore(12.0),  # Below 15.0 threshold
            "completeness": DimensionScore(19.0),
            "consistency": DimensionScore(10.0),  # Below 15.0 threshold
            "freshness": DimensionScore(19.0),
            "plausibility": DimensionScore(15.5),
        }

        low_result = AssessmentResult(75.5, False, low_scores)
        summary = self.generator._build_summary(low_result)

        # Check failed dimensions
        failed_dims = summary["pass_fail_status"]["failed_dimensions"]
        assert "validity" in failed_dims
        assert "consistency" in failed_dims
        assert len(failed_dims) == 2

    def test_build_rule_execution_log(self):
        """Test rule execution log generation."""
        rule_log = self.generator._build_rule_execution_log(self.assessment_result)

        # Should generate 5 basic rules (one per dimension)
        assert len(rule_log) == 5

        # Check first rule structure
        validity_rule = rule_log[0]
        assert validity_rule["rule_id"] == "validity_basic_check"
        assert validity_rule["dimension"] == "validity"
        assert validity_rule["field"] == "overall"
        assert validity_rule["rule_definition"] == "Basic validity validation rules"

        # Check execution details
        execution = validity_rule["execution"]
        assert execution["rule_score"] == 18.0
        assert execution["rule_weight"] == 1.0
        assert "total_records" in execution
        assert "passed" in execution
        assert "failed" in execution

    def test_build_field_analysis(self):
        """Test field analysis generation."""
        field_analysis = self.generator._build_field_analysis(self.assessment_result)

        # Should have overall field analysis
        assert "overall" in field_analysis

        overall_analysis = field_analysis["overall"]
        assert "rules_applied" in overall_analysis
        assert "overall_field_score" in overall_analysis
        assert "total_failures" in overall_analysis
        assert "ml_readiness" in overall_analysis

        # Check ML readiness assessment
        assert overall_analysis["ml_readiness"] in [
            "ready",
            "needs_cleanup",
            "not_ready",
        ]

    def test_assess_ml_readiness(self):
        """Test ML readiness assessment logic."""
        # Test different score ranges
        assert self.generator._assess_ml_readiness(95.0) == "ready"
        assert self.generator._assess_ml_readiness(85.0) == "needs_cleanup"
        assert self.generator._assess_ml_readiness(60.0) == "not_ready"
        assert self.generator._assess_ml_readiness(30.0) == "not_ready"

        # Test 0-20 scale scores
        assert self.generator._assess_ml_readiness(19.0) == "ready"  # 95%
        assert self.generator._assess_ml_readiness(16.0) == "needs_cleanup"  # 80%
        assert self.generator._assess_ml_readiness(12.0) == "not_ready"  # 60%

    def test_generate_complete_report(self):
        """Test complete report generation."""
        with patch("adri.core.report_generator.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 7, 3, 17, 30, 15)

            with patch.object(self.generator, "_generate_assessment_id") as mock_id:
                mock_id.return_value = "adri_20250703_173015_abc123"

                report = self.generator.generate_report(self.assessment_result)

        # Check root structure
        assert "adri_assessment_report" in report
        adri_report = report["adri_assessment_report"]

        # Check all required sections
        required_sections = [
            "metadata",
            "summary",
            "rule_execution_log",
            "field_analysis",
        ]
        for section in required_sections:
            assert section in adri_report

    def test_validate_report_success(self):
        """Test successful report validation."""
        report = self.generator.generate_report(self.assessment_result)
        validation = self.generator.validate_report(report)

        assert validation["valid"] is True
        assert len(validation["errors"]) == 0
        assert len(validation["warnings"]) == 0

    def test_validate_report_missing_root(self):
        """Test validation with missing root object."""
        invalid_report = {"wrong_root": {}}
        validation = self.generator.validate_report(invalid_report)

        assert validation["valid"] is False
        assert "Missing root object 'adri_assessment_report'" in validation["errors"]

    def test_validate_report_missing_sections(self):
        """Test validation with missing required sections."""
        incomplete_report = {
            "adri_assessment_report": {
                "metadata": {},
                "summary": {},
                # Missing rule_execution_log and field_analysis
            }
        }

        validation = self.generator.validate_report(incomplete_report)

        assert validation["valid"] is False
        assert any(
            "Missing required section: rule_execution_log" in error
            for error in validation["errors"]
        )
        assert any(
            "Missing required section: field_analysis" in error
            for error in validation["errors"]
        )

    def test_validate_report_mathematical_inconsistency(self):
        """Test validation with mathematical inconsistency."""
        report = self.generator.generate_report(self.assessment_result)

        # Introduce mathematical inconsistency
        report["adri_assessment_report"]["summary"][
            "overall_score"
        ] = 100.0  # Wrong total

        validation = self.generator.validate_report(report)

        assert validation["valid"] is False
        assert any(
            "Mathematical inconsistency" in error for error in validation["errors"]
        )

    def test_handle_assessment_with_custom_attributes(self):
        """Test handling assessment result with custom attributes."""
        # Add custom attributes to assessment result
        self.assessment_result.dataset_name = "test_dataset"
        self.assessment_result.total_records = 1000
        self.assessment_result.total_fields = 5
        self.assessment_result.execution_time_ms = 250

        report = self.generator.generate_report(self.assessment_result)
        metadata = report["adri_assessment_report"]["metadata"]

        assert metadata["dataset"]["name"] == "test_dataset"
        assert metadata["dataset"]["total_records"] == 1000
        assert metadata["dataset"]["total_fields"] == 5
        assert metadata["execution"]["duration_ms"] == 250

    def test_handle_dict_dimension_scores(self):
        """Test handling dimension scores as plain dictionary."""
        # Create assessment with dict dimension scores instead of DimensionScore objects
        dict_scores = {
            "validity": 18.0,
            "completeness": 19.0,
            "consistency": 16.0,
            "freshness": 19.0,
            "plausibility": 15.5,
        }

        dict_result = AssessmentResult(87.5, True, dict_scores)
        summary = self.generator._build_summary(dict_result)

        expected_scores = {
            "validity": 18.0,
            "completeness": 19.0,
            "consistency": 16.0,
            "freshness": 19.0,
            "plausibility": 15.5,
        }
        assert summary["dimension_scores"] == expected_scores

    def test_handle_missing_dimension_scores(self):
        """Test handling assessment result without dimension scores."""
        # Create minimal assessment result
        minimal_result = AssessmentResult(50.0, False, {})

        summary = self.generator._build_summary(minimal_result)

        # Should fallback to zero scores
        expected_scores = {
            "validity": 0.0,
            "completeness": 0.0,
            "consistency": 0.0,
            "freshness": 0.0,
            "plausibility": 0.0,
        }
        assert summary["dimension_scores"] == expected_scores

    def test_template_constants_loaded(self):
        """Test that template constants are properly loaded."""
        # Test template structure
        template = ADRI_ASSESSMENT_REPORT_TEMPLATE_V0_1_0
        assert "standard_metadata" in template
        assert "field_requirements" in template
        assert "business_rules" in template

        # Test dimension ranges
        assert len(DIMENSION_SCORE_RANGES) == 5
        for dim in [
            "validity",
            "completeness",
            "consistency",
            "freshness",
            "plausibility",
        ]:
            assert dim in DIMENSION_SCORE_RANGES
            assert DIMENSION_SCORE_RANGES[dim]["min"] == 0.0
            assert DIMENSION_SCORE_RANGES[dim]["max"] == 20.0

        # Test overall score range
        assert OVERALL_SCORE_RANGE["min"] == 0.0
        assert OVERALL_SCORE_RANGE["max"] == 100.0

    def test_timestamp_format_compliance(self):
        """Test timestamp format compliance with ADRI standard."""
        timestamp = datetime(2025, 7, 3, 17, 30, 15)
        formatted = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

        import re

        assert re.match(TIMESTAMP_PATTERN, formatted)
        assert formatted == "2025-07-03T17:30:15Z"


class TestReportGeneratorEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = ReportGenerator()

    def test_empty_assessment_result(self):
        """Test handling completely empty assessment result."""
        empty_result = AssessmentResult(0.0, False, {})

        # Should not raise exceptions
        report = self.generator.generate_report(empty_result)

        # Should have valid structure
        assert "adri_assessment_report" in report
        validation = self.generator.validate_report(report)
        assert validation["valid"] is True

    def test_none_values_in_assessment(self):
        """Test handling None values in assessment result."""
        # Create assessment with None values
        result = AssessmentResult(None, None, None)

        # Should handle gracefully with defaults
        summary = self.generator._build_summary(result)
        assert summary["overall_score"] == 0.0  # getattr default
        assert summary["pass_fail_status"]["overall_passed"] is False

    def test_malformed_dimension_scores(self):
        """Test handling malformed dimension score objects."""
        # Create mock dimension score without .score attribute
        mock_score = MagicMock()
        del mock_score.score  # Remove score attribute

        malformed_scores = {"validity": mock_score}
        result = AssessmentResult(50.0, False, malformed_scores)

        # Should handle gracefully
        summary = self.generator._build_summary(result)
        assert summary["dimension_scores"]["validity"] == 0.0  # Fallback

    def test_large_numbers_handling(self):
        """Test handling of large numbers in scores."""
        large_scores = {
            "validity": DimensionScore(999999.0),
            "completeness": DimensionScore(999999.0),
            "consistency": DimensionScore(999999.0),
            "freshness": DimensionScore(999999.0),
            "plausibility": DimensionScore(999999.0),
        }

        large_result = AssessmentResult(4999995.0, True, large_scores)

        # Should handle without errors
        report = self.generator.generate_report(large_result)
        assert report["adri_assessment_report"]["summary"]["overall_score"] == 4999995.0

    def test_negative_scores_handling(self):
        """Test handling of negative scores."""
        negative_scores = {
            "validity": DimensionScore(-5.0),
            "completeness": DimensionScore(-10.0),
            "consistency": DimensionScore(-2.0),
            "freshness": DimensionScore(-8.0),
            "plausibility": DimensionScore(-1.0),
        }

        negative_result = AssessmentResult(-26.0, False, negative_scores)

        # Should handle without errors
        summary = self.generator._build_summary(negative_result)
        assert summary["dimension_scores"]["validity"] == -5.0

        # All should be in failed dimensions
        failed_dims = summary["pass_fail_status"]["failed_dimensions"]
        assert len(failed_dims) == 5  # All negative scores < 15.0
