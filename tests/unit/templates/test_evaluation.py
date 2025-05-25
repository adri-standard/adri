"""Unit tests for template evaluation classes."""

import pytest
from datetime import datetime
from adri.templates.evaluation import TemplateGap, TemplateEvaluation


class TestTemplateGap:
    """Test the TemplateGap class."""
    
    def test_gap_creation(self):
        """Test creating a template gap."""
        gap = TemplateGap(
            requirement_id="REQ-001",
            requirement_description="Minimum validity score",
            expected_value=80,
            actual_value=60,
            dimension="validity"
        )
        
        assert gap.requirement_id == "REQ-001"
        assert gap.requirement_description == "Minimum validity score"
        assert gap.expected_value == 80
        assert gap.actual_value == 60
        assert gap.dimension == "validity"
    
    def test_gap_size_calculation(self):
        """Test gap size calculation."""
        # Numeric gap
        gap1 = TemplateGap(
            requirement_id="REQ-001",
            requirement_description="Score requirement",
            expected_value=80,
            actual_value=60,
            dimension="validity"
        )
        assert gap1.gap_size == 20
        
        # Boolean gap (True expected, False actual)
        gap2 = TemplateGap(
            requirement_id="REQ-002",
            requirement_description="Boolean requirement",
            expected_value=True,
            actual_value=False,
            dimension="completeness"
        )
        assert gap2.gap_size == 100
        
        # Boolean gap (both True - no gap)
        gap3 = TemplateGap(
            requirement_id="REQ-003",
            requirement_description="Boolean requirement",
            expected_value=True,
            actual_value=True,
            dimension="completeness"
        )
        assert gap3.gap_size == 0
        
        # String gap
        gap4 = TemplateGap(
            requirement_id="REQ-004",
            requirement_description="String requirement",
            expected_value="required",
            actual_value="missing",
            dimension="validity"
        )
        assert gap4.gap_size == 100
    
    def test_severity_calculation(self):
        """Test severity calculation based on gap size."""
        # High severity (gap > 50)
        gap1 = TemplateGap(
            requirement_id="REQ-001",
            requirement_description="Large gap",
            expected_value=100,
            actual_value=40,
            dimension="validity"
        )
        assert gap1.severity == "high"
        
        # Medium severity (20 < gap <= 50)
        gap2 = TemplateGap(
            requirement_id="REQ-002",
            requirement_description="Medium gap",
            expected_value=100,
            actual_value=70,
            dimension="validity"
        )
        assert gap2.severity == "medium"
        
        # Low severity (gap <= 20)
        gap3 = TemplateGap(
            requirement_id="REQ-003",
            requirement_description="Small gap",
            expected_value=100,
            actual_value=85,
            dimension="validity"
        )
        assert gap3.severity == "low"
    
    def test_gap_to_dict(self):
        """Test gap serialization to dictionary."""
        gap = TemplateGap(
            requirement_id="REQ-001",
            requirement_description="Test requirement",
            expected_value=80,
            actual_value=60,
            dimension="validity"
        )
        gap.remediation_hint = "Improve data validation"
        
        gap_dict = gap.to_dict()
        
        assert gap_dict["requirement_id"] == "REQ-001"
        assert gap_dict["requirement_description"] == "Test requirement"
        assert gap_dict["expected_value"] == 80
        assert gap_dict["actual_value"] == 60
        assert gap_dict["dimension"] == "validity"
        assert gap_dict["gap_size"] == 20
        assert gap_dict["severity"] == "low"
        assert gap_dict["remediation_hint"] == "Improve data validation"


class TestTemplateEvaluation:
    """Test the TemplateEvaluation class."""
    
    def test_evaluation_creation(self):
        """Test creating a template evaluation."""
        evaluation = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        
        assert evaluation.template_id == "test-template"
        assert evaluation.template_version == "1.0.0"
        assert evaluation.template_name == "Test Template"
        assert evaluation.gaps == []
        assert evaluation.overall_score is None
        assert evaluation.compliance_score is None
        assert evaluation.finalized is False
    
    def test_add_gap(self):
        """Test adding gaps to evaluation."""
        evaluation = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        
        gap1 = TemplateGap(
            requirement_id="REQ-001",
            requirement_description="First requirement",
            expected_value=80,
            actual_value=60,
            dimension="validity"
        )
        
        gap2 = TemplateGap(
            requirement_id="REQ-002",
            requirement_description="Second requirement",
            expected_value=True,
            actual_value=False,
            dimension="completeness"
        )
        
        evaluation.add_gap(gap1)
        evaluation.add_gap(gap2)
        
        assert len(evaluation.gaps) == 2
        assert evaluation.gaps[0] == gap1
        assert evaluation.gaps[1] == gap2
    
    def test_finalize_with_scores(self):
        """Test finalizing evaluation with scores."""
        evaluation = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        
        # Add some gaps
        gap = TemplateGap(
            requirement_id="REQ-001",
            requirement_description="Score requirement",
            expected_value=80,
            actual_value=60,
            dimension="validity"
        )
        evaluation.add_gap(gap)
        
        # Finalize with scores
        evaluation.finalize(
            overall_score=75,
            dimension_scores={"validity": 60, "completeness": 90}
        )
        
        assert evaluation.finalized is True
        assert evaluation.overall_score == 75
        assert evaluation.dimension_scores == {"validity": 60, "completeness": 90}
        assert evaluation.evaluated_at is not None
        
        # Calculate compliance score
        assert evaluation.compliance_score == 75.0  # (60 + 90) / 2
    
    def test_compliance_determination(self):
        """Test compliance and certification eligibility."""
        # Compliant evaluation (no gaps)
        eval1 = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        eval1.finalize(overall_score=85)
        
        assert eval1.compliant is True
        assert eval1.certification_eligible is True
        assert eval1.certification_blockers == []
        
        # Non-compliant evaluation (has gaps)
        eval2 = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        gap = TemplateGap(
            requirement_id="REQ-001",
            requirement_description="Failed requirement",
            expected_value=80,
            actual_value=60,
            dimension="validity"
        )
        eval2.add_gap(gap)
        eval2.finalize(overall_score=70)
        
        assert eval2.compliant is False
        assert eval2.certification_eligible is False
        assert len(eval2.certification_blockers) > 0
    
    def test_get_summary(self):
        """Test evaluation summary generation."""
        evaluation = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        
        # Before finalization
        assert evaluation.get_summary() == "Evaluation in progress"
        
        # Compliant
        evaluation.finalize(overall_score=90)
        assert evaluation.get_summary() == "COMPLIANT - Meets all requirements"
        
        # Non-compliant
        gap = TemplateGap(
            requirement_id="REQ-001",
            requirement_description="Failed requirement",
            expected_value=80,
            actual_value=60,
            dimension="validity"
        )
        evaluation.add_gap(gap)
        evaluation.compliant = False
        assert evaluation.get_summary() == "NON-COMPLIANT - 1 requirement gaps found"
    
    def test_generate_remediation_plan(self):
        """Test remediation plan generation."""
        evaluation = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        
        # Add gaps with different severities
        gap1 = TemplateGap(
            requirement_id="REQ-001",
            requirement_description="Critical requirement",
            expected_value=100,
            actual_value=40,
            dimension="validity"
        )
        gap1.remediation_hint = "Implement data validation"
        
        gap2 = TemplateGap(
            requirement_id="REQ-002",
            requirement_description="Minor requirement",
            expected_value=100,
            actual_value=90,
            dimension="completeness"
        )
        gap2.remediation_hint = "Fill missing values"
        
        evaluation.add_gap(gap1)
        evaluation.add_gap(gap2)
        evaluation.finalize(overall_score=65)
        
        plan = evaluation.generate_remediation_plan()
        
        assert len(plan) == 2
        # High severity gaps should come first
        assert plan[0]["gap"]["severity"] == "high"
        assert plan[0]["priority"] == "High"
        assert plan[0]["remediation_steps"][0] == "Implement data validation"
        
        assert plan[1]["gap"]["severity"] == "low"
        assert plan[1]["priority"] == "Low"
    
    def test_add_recommendation(self):
        """Test adding recommendations."""
        evaluation = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        
        evaluation.add_recommendation("Consider implementing automated validation")
        evaluation.add_recommendation("Review data collection processes")
        
        assert len(evaluation.recommendations) == 2
        assert "automated validation" in evaluation.recommendations[0]
    
    def test_to_dict(self):
        """Test evaluation serialization to dictionary."""
        evaluation = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        
        gap = TemplateGap(
            requirement_id="REQ-001",
            requirement_description="Test requirement",
            expected_value=80,
            actual_value=60,
            dimension="validity"
        )
        evaluation.add_gap(gap)
        evaluation.add_recommendation("Improve data quality")
        evaluation.finalize(overall_score=75)
        
        eval_dict = evaluation.to_dict()
        
        assert eval_dict["template_id"] == "test-template"
        assert eval_dict["template_version"] == "1.0.0"
        assert eval_dict["template_name"] == "Test Template"
        assert eval_dict["compliant"] is False
        assert eval_dict["overall_score"] == 75
        assert len(eval_dict["gaps"]) == 1
        assert len(eval_dict["recommendations"]) == 1
        assert eval_dict["finalized"] is True
        assert "evaluated_at" in eval_dict
        assert "remediation_plan" in eval_dict
    
    def test_cannot_modify_after_finalize(self):
        """Test that evaluation cannot be modified after finalization."""
        evaluation = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        
        evaluation.finalize(overall_score=80)
        
        # Should not be able to add gaps after finalization
        gap = TemplateGap(
            requirement_id="REQ-001",
            requirement_description="Late gap",
            expected_value=100,
            actual_value=50,
            dimension="validity"
        )
        
        with pytest.raises(ValueError, match="Cannot modify finalized evaluation"):
            evaluation.add_gap(gap)
