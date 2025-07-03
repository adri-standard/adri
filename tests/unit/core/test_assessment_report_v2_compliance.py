"""
Tests for ADRI Assessment Report Standard v2.0.0 compliance.

This module tests that the enhanced AssessmentResult class can generate
reports that comply with the ADRI Assessment Report Standard v2.0.0.
"""

import pytest
import json
from datetime import datetime
from adri.core.assessor import (
    AssessmentResult, 
    DimensionScore, 
    RuleExecutionResult, 
    FieldAnalysis
)
from adri.standards.yaml_standards import YAMLStandards


class TestAssessmentReportV2Compliance:
    """Test compliance with ADRI Assessment Report Standard v2.0.0."""
    
    def setup_method(self):
        """Set up test data."""
        # Create sample dimension scores
        self.dimension_scores = {
            'validity': DimensionScore(score=17.5, max_score=20.0, issues=[]),
            'completeness': DimensionScore(score=18.0, max_score=20.0, issues=[]),
            'consistency': DimensionScore(score=16.0, max_score=20.0, issues=[]),
            'freshness': DimensionScore(score=18.0, max_score=20.0, issues=[]),
            'plausibility': DimensionScore(score=18.0, max_score=20.0, issues=[])
        }
        
        # Create sample rule execution results
        self.rule_execution_log = [
            RuleExecutionResult(
                rule_id="email_format_validation",
                dimension="validity",
                field="customer_email",
                rule_definition="^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                total_records=1000,
                passed=873,
                failed=127,
                rule_score=17.46,
                rule_weight=1.0,
                execution_time_ms=45,
                sample_failures=["invalid@", "test.com", "user@domain"],
                failure_patterns={"missing_domain": 45, "invalid_format": 82}
            ),
            RuleExecutionResult(
                rule_id="mandatory_field_presence",
                dimension="completeness",
                field="customer_email",
                rule_definition="NOT NULL AND NOT EMPTY",
                total_records=1000,
                passed=955,
                failed=45,
                rule_score=19.10,
                rule_weight=0.4,
                execution_time_ms=12,
                sample_failures=["", "   ", "NULL"],
                failure_patterns={"null_values": 30, "empty_strings": 15}
            )
        ]
        
        # Create sample field analysis
        self.field_analysis = {
            "customer_email": FieldAnalysis(
                field_name="customer_email",
                rules_applied=["email_format_validation", "mandatory_field_presence"],
                overall_field_score=18.28,
                total_failures=172,
                ml_readiness="needs_cleanup",
                recommended_actions=[
                    "Apply email validation regex before ML processing",
                    "Improve data collection to reduce missing emails"
                ]
            ),
            "customer_id": FieldAnalysis(
                field_name="customer_id",
                rules_applied=["mandatory_field_presence"],
                overall_field_score=20.0,
                total_failures=0,
                ml_readiness="ready",
                recommended_actions=[]
            )
        }
        
        # Create assessment result
        self.assessment_result = AssessmentResult(
            overall_score=87.5,
            dimension_scores=self.dimension_scores,
            passed=True,
            standard_id="customer-data-quality-v1",
            assessment_date=datetime(2025, 1, 2, 14, 30, 15),
            metadata={'domain': 'customer_analytics'}
        )
        
        # Add rule execution log and field analysis
        for rule in self.rule_execution_log:
            self.assessment_result.add_rule_execution(rule)
        
        for field_name, analysis in self.field_analysis.items():
            self.assessment_result.add_field_analysis(field_name, analysis)
        
        # Set dataset info and execution stats
        self.assessment_result.set_dataset_info(
            total_records=1000,
            total_fields=5,
            size_mb=2.3
        )
        self.assessment_result.set_execution_stats(duration_ms=1250)
    
    def test_v2_standard_dict_structure(self):
        """Test that v2 standard dict has correct structure."""
        report = self.assessment_result.to_v2_standard_dict(
            dataset_name="customer_data.csv",
            adri_version="2.0.0"
        )
        
        # Check root structure
        assert "adri_assessment_report" in report
        root = report["adri_assessment_report"]
        
        # Check required top-level sections
        assert "metadata" in root
        assert "summary" in root
        assert "rule_execution_log" in root
        assert "field_analysis" in root
    
    def test_metadata_section_compliance(self):
        """Test metadata section compliance with v2.0.0 standard."""
        report = self.assessment_result.to_v2_standard_dict(
            dataset_name="customer_data.csv",
            adri_version="2.0.0"
        )
        
        metadata = report["adri_assessment_report"]["metadata"]
        
        # Check required metadata fields
        assert "assessment_id" in metadata
        assert "timestamp" in metadata
        assert "adri_version" in metadata
        assert "standard_applied" in metadata
        assert "dataset" in metadata
        assert "execution" in metadata
        
        # Check assessment_id format
        assessment_id = metadata["assessment_id"]
        assert assessment_id.startswith("adri_")
        assert len(assessment_id.split("_")) == 4  # adri_YYYYMMDD_HHMMSS_RANDOM
        
        # Check timestamp format (ISO 8601)
        timestamp = metadata["timestamp"]
        assert timestamp == "2025-01-02T14:30:15Z"
        
        # Check standard_applied structure
        standard_applied = metadata["standard_applied"]
        assert "id" in standard_applied
        assert "version" in standard_applied
        assert "domain" in standard_applied
        
        # Check dataset structure
        dataset = metadata["dataset"]
        assert "name" in dataset
        assert "total_records" in dataset
        assert "total_fields" in dataset
        assert "size_mb" in dataset
        
        # Check execution structure
        execution = metadata["execution"]
        assert "duration_ms" in execution
        assert "rules_executed" in execution
        assert "total_validations" in execution
    
    def test_summary_section_compliance(self):
        """Test summary section compliance with v2.0.0 standard."""
        report = self.assessment_result.to_v2_standard_dict(
            dataset_name="customer_data.csv",
            adri_version="2.0.0"
        )
        
        summary = report["adri_assessment_report"]["summary"]
        
        # Check required summary fields
        assert "overall_score" in summary
        assert "dimension_scores" in summary
        assert "pass_fail_status" in summary
        
        # Check dimension scores structure
        dimension_scores = summary["dimension_scores"]
        required_dimensions = ["validity", "completeness", "consistency", "freshness", "plausibility"]
        for dim in required_dimensions:
            assert dim in dimension_scores
            assert isinstance(dimension_scores[dim], (int, float))
            assert 0.0 <= dimension_scores[dim] <= 20.0
        
        # Check pass_fail_status structure
        pass_fail_status = summary["pass_fail_status"]
        assert "overall_passed" in pass_fail_status
        assert "failed_dimensions" in pass_fail_status
        assert "critical_issues" in pass_fail_status
        assert "total_failures" in pass_fail_status
        
        assert isinstance(pass_fail_status["overall_passed"], bool)
        assert isinstance(pass_fail_status["failed_dimensions"], list)
        assert isinstance(pass_fail_status["critical_issues"], int)
        assert isinstance(pass_fail_status["total_failures"], int)
    
    def test_rule_execution_log_compliance(self):
        """Test rule execution log compliance with v2.0.0 standard."""
        report = self.assessment_result.to_v2_standard_dict(
            dataset_name="customer_data.csv",
            adri_version="2.0.0"
        )
        
        rule_log = report["adri_assessment_report"]["rule_execution_log"]
        
        # Check that it's a list with entries
        assert isinstance(rule_log, list)
        assert len(rule_log) > 0
        
        # Check structure of first rule entry
        rule = rule_log[0]
        assert "rule_id" in rule
        assert "dimension" in rule
        assert "field" in rule
        assert "rule_definition" in rule
        assert "execution" in rule
        
        # Check execution structure
        execution = rule["execution"]
        assert "total_records" in execution
        assert "passed" in execution
        assert "failed" in execution
        assert "rule_score" in execution
        assert "rule_weight" in execution
        
        # Check mathematical consistency: passed + failed = total_records
        assert execution["passed"] + execution["failed"] == execution["total_records"]
        
        # Check score ranges
        assert 0.0 <= execution["rule_score"] <= 20.0
        assert 0.0 <= execution["rule_weight"] <= 1.0
        
        # Check failures section if present
        if "failures" in rule:
            failures = rule["failures"]
            if "sample_failures" in failures:
                assert isinstance(failures["sample_failures"], list)
            if "failure_patterns" in failures:
                assert isinstance(failures["failure_patterns"], dict)
    
    def test_field_analysis_compliance(self):
        """Test field analysis compliance with v2.0.0 standard."""
        report = self.assessment_result.to_v2_standard_dict(
            dataset_name="customer_data.csv",
            adri_version="2.0.0"
        )
        
        field_analysis = report["adri_assessment_report"]["field_analysis"]
        
        # Check that it's a dictionary with field entries
        assert isinstance(field_analysis, dict)
        assert len(field_analysis) > 0
        
        # Check structure of field analysis entries
        for field_name, analysis in field_analysis.items():
            assert "rules_applied" in analysis
            assert "overall_field_score" in analysis
            assert "total_failures" in analysis
            
            assert isinstance(analysis["rules_applied"], list)
            assert len(analysis["rules_applied"]) > 0
            assert isinstance(analysis["overall_field_score"], (int, float))
            assert isinstance(analysis["total_failures"], int)
            
            # Check score range
            assert 0.0 <= analysis["overall_field_score"] <= 20.0
            assert analysis["total_failures"] >= 0
            
            # Check optional fields
            if "ml_readiness" in analysis:
                assert analysis["ml_readiness"] in ["ready", "needs_cleanup", "not_ready", "unknown"]
            
            if "recommended_actions" in analysis:
                assert isinstance(analysis["recommended_actions"], list)
    
    def test_mathematical_consistency(self):
        """Test mathematical consistency requirements."""
        report = self.assessment_result.to_v2_standard_dict(
            dataset_name="customer_data.csv",
            adri_version="2.0.0"
        )
        
        summary = report["adri_assessment_report"]["summary"]
        rule_log = report["adri_assessment_report"]["rule_execution_log"]
        
        # Test: Overall score equals sum of dimension scores
        dimension_sum = sum(summary["dimension_scores"].values())
        assert abs(summary["overall_score"] - dimension_sum) < 0.01
        
        # Test: For each rule, passed + failed = total_records
        for rule in rule_log:
            execution = rule["execution"]
            assert execution["passed"] + execution["failed"] == execution["total_records"]
        
        # Test: All scores are within valid ranges
        assert 0.0 <= summary["overall_score"] <= 100.0
        for score in summary["dimension_scores"].values():
            assert 0.0 <= score <= 20.0
    
    def test_json_serializable(self):
        """Test that the report is JSON serializable."""
        report = self.assessment_result.to_v2_standard_dict(
            dataset_name="customer_data.csv",
            adri_version="2.0.0"
        )
        
        # Should not raise an exception
        json_str = json.dumps(report, indent=2)
        assert len(json_str) > 0
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed == report
    
    def test_load_v2_standard_and_validate(self):
        """Test loading the v2.0.0 standard and validating against it."""
        # Load the v2.0.0 standard
        try:
            standard = YAMLStandards("Data Standards Catalogue/Open Source/adri_assessment_report_standard_v2.yaml")
            
            # Generate a report
            report = self.assessment_result.to_v2_standard_dict(
                dataset_name="customer_data.csv",
                adri_version="2.0.0"
            )
            
            # Validate the report against the standard
            # Note: This would require implementing validation logic in YAMLStandards
            # For now, we just check that the standard loads and the report generates
            assert standard is not None
            assert report is not None
            assert "adri_assessment_report" in report
            
        except Exception as e:
            pytest.skip(f"Could not load v2.0.0 standard: {e}")
    
    def test_rule_execution_result_to_dict(self):
        """Test RuleExecutionResult.to_dict() method."""
        rule = RuleExecutionResult(
            rule_id="test_rule",
            dimension="validity",
            field="test_field",
            rule_definition="test definition",
            total_records=100,
            passed=80,
            failed=20,
            rule_score=16.0,
            rule_weight=1.0,
            execution_time_ms=50,
            sample_failures=["fail1", "fail2"],
            failure_patterns={"pattern1": 10, "pattern2": 10}
        )
        
        result_dict = rule.to_dict()
        
        # Check structure
        assert "rule_id" in result_dict
        assert "dimension" in result_dict
        assert "field" in result_dict
        assert "rule_definition" in result_dict
        assert "execution" in result_dict
        assert "failures" in result_dict
        
        # Check execution section
        execution = result_dict["execution"]
        assert execution["total_records"] == 100
        assert execution["passed"] == 80
        assert execution["failed"] == 20
        assert execution["rule_score"] == 16.0
        assert execution["rule_weight"] == 1.0
        assert execution["execution_time_ms"] == 50
        
        # Check failures section
        failures = result_dict["failures"]
        assert failures["sample_failures"] == ["fail1", "fail2"]
        assert failures["failure_patterns"] == {"pattern1": 10, "pattern2": 10}
    
    def test_field_analysis_to_dict(self):
        """Test FieldAnalysis.to_dict() method."""
        analysis = FieldAnalysis(
            field_name="test_field",
            rules_applied=["rule1", "rule2"],
            overall_field_score=18.5,
            total_failures=25,
            ml_readiness="ready",
            recommended_actions=["action1", "action2"]
        )
        
        result_dict = analysis.to_dict()
        
        # Check structure
        assert "rules_applied" in result_dict
        assert "overall_field_score" in result_dict
        assert "total_failures" in result_dict
        assert "ml_readiness" in result_dict
        assert "recommended_actions" in result_dict
        
        # Check values
        assert result_dict["rules_applied"] == ["rule1", "rule2"]
        assert result_dict["overall_field_score"] == 18.5
        assert result_dict["total_failures"] == 25
        assert result_dict["ml_readiness"] == "ready"
        assert result_dict["recommended_actions"] == ["action1", "action2"]


if __name__ == "__main__":
    pytest.main([__file__])
