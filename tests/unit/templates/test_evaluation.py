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
            requirement_type="dimension",
            requirement_description="Minimum validity score",
            expected_value=80,
            actual_value=60,
            gap_severity="high"
        )
        
        assert gap.requirement_id == "REQ-001"
        assert gap.requirement_type == "dimension"
        assert gap.requirement_description == "Minimum validity score"
        assert gap.expected_value == 80
        assert gap.actual_value == 60
        assert gap.gap_severity == "high"
    
    def test_gap_size_calculation(self):
        """Test gap size calculation."""
        # Numeric gap
        gap1 = TemplateGap(
            requirement_id="REQ-001",
            requirement_type="dimension",
            requirement_description="Score requirement",
            expected_value=80,
            actual_value=60,
            gap_severity="medium"
        )
        assert gap1.gap_size == 20
        
        # Non-numeric gap
        gap2 = TemplateGap(
            requirement_id="REQ-002",
            requirement_type="rule",
            requirement_description="Boolean requirement",
            expected_value=True,
            actual_value=False,
            gap_severity="high"
        )
        assert gap2.gap_size == 0.0  # Non-numeric values return 0.0
    
    def test_severity_values(self):
        """Test different severity values."""
        # High severity
        gap1 = TemplateGap(
            requirement_id="REQ-001",
            requirement_type="dimension",
            requirement_description="Large gap",
            expected_value=100,
            actual_value=40,
            gap_severity="high"
        )
        assert gap1.gap_severity == "high"
        
        # Medium severity
        gap2 = TemplateGap(
            requirement_id="REQ-002",
            requirement_type="dimension",
            requirement_description="Medium gap",
            expected_value=100,
            actual_value=70,
            gap_severity="medium"
        )
        assert gap2.gap_severity == "medium"
        
        # Low severity
        gap3 = TemplateGap(
            requirement_id="REQ-003",
            requirement_type="dimension",
            requirement_description="Small gap",
            expected_value=100,
            actual_value=85,
            gap_severity="low"
        )
        assert gap3.gap_severity == "low"
    
    def test_gap_to_dict(self):
        """Test gap serialization to dictionary."""
        gap = TemplateGap(
            requirement_id="REQ-001",
            requirement_type="dimension",
            requirement_description="Test requirement",
            expected_value=80,
            actual_value=60,
            gap_severity="medium",
            remediation_hint="Improve data validation"
        )
        
        gap_dict = gap.to_dict()
        
        assert gap_dict["requirement_id"] == "REQ-001"
        assert gap_dict["requirement_type"] == "dimension"
        assert gap_dict["description"] == "Test requirement"
        assert gap_dict["expected"] == 80
        assert gap_dict["actual"] == 60
        assert gap_dict["severity"] == "medium"
        assert gap_dict["remediation"] == "Improve data validation"


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
        assert evaluation.compliance_score == 0.0
        assert evaluation.compliant is False
    
    def test_add_gap(self):
        """Test adding gaps to evaluation."""
        evaluation = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        
        gap1 = TemplateGap(
            requirement_id="REQ-001",
            requirement_type="dimension",
            requirement_description="First requirement",
            expected_value=80,
            actual_value=60,
            gap_severity="medium"
        )
        
        gap2 = TemplateGap(
            requirement_id="REQ-002",
            requirement_type="rule",
            requirement_description="Second requirement",
            expected_value=True,
            actual_value=False,
            gap_severity="blocking"
        )
        
        evaluation.add_gap(gap1)
        evaluation.add_gap(gap2)
        
        assert len(evaluation.gaps) == 2
        assert evaluation.gaps[0] == gap1
        assert evaluation.gaps[1] == gap2
        assert len(evaluation.failed_requirements) == 2
        assert evaluation.certification_eligible is False  # Due to blocking gap
        assert len(evaluation.certification_blockers) == 1
    
    def test_add_passed_requirement(self):
        """Test adding passed requirements."""
        evaluation = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        
        evaluation.add_passed_requirement("REQ-001")
        evaluation.add_passed_requirement("REQ-002")
        
        assert len(evaluation.passed_requirements) == 2
        assert "REQ-001" in evaluation.passed_requirements
        assert "REQ-002" in evaluation.passed_requirements
    
    def test_finalize_with_mixed_results(self):
        """Test finalizing evaluation with both passed and failed requirements."""
        evaluation = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        
        # Add some passed requirements
        evaluation.add_passed_requirement("REQ-001")
        evaluation.add_passed_requirement("REQ-002")
        
        # Add some gaps
        gap = TemplateGap(
            requirement_id="REQ-003",
            requirement_type="dimension",
            requirement_description="Failed requirement",
            expected_value=80,
            actual_value=60,
            gap_severity="medium"
        )
        evaluation.add_gap(gap)
        
        # Finalize the evaluation
        evaluation.finalize()
        
        # 2 passed out of 3 total = 66.7%
        assert evaluation.compliance_score == pytest.approx(66.7, rel=0.1)
        assert evaluation.compliant is False  # Has failed requirements
        assert evaluation.certification_eligible is True  # No blocking gaps
    
    def test_compliance_determination(self):
        """Test compliance and certification eligibility."""
        # Compliant evaluation (no gaps)
        eval1 = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        eval1.add_passed_requirement("REQ-001")
        eval1.finalize()
        
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
            requirement_type="dimension",
            requirement_description="Failed requirement",
            expected_value=80,
            actual_value=60,
            gap_severity="high"
        )
        eval2.add_gap(gap)
        eval2.finalize()
        
        assert eval2.compliant is False
        assert eval2.certification_eligible is False
        assert len(eval2.failed_requirements) > 0
    
    def test_get_summary(self):
        """Test evaluation summary generation."""
        evaluation = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        
        # Compliant
        evaluation.add_passed_requirement("REQ-001")
        evaluation.finalize()
        assert "✅ Fully compliant" in evaluation.get_summary()
        
        # Non-compliant
        evaluation2 = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        gap = TemplateGap(
            requirement_id="REQ-001",
            requirement_type="dimension",
            requirement_description="Failed requirement",
            expected_value=80,
            actual_value=60,
            gap_severity="high"
        )
        evaluation2.add_gap(gap)
        evaluation2.finalize()
        assert "❌ Not compliant" in evaluation2.get_summary()
        assert "1 gaps found" in evaluation2.get_summary()
    
    def test_remediation_plan_generation(self):
        """Test remediation plan generation."""
        evaluation = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        
        # Add gaps with different severities
        gap1 = TemplateGap(
            requirement_id="REQ-001",
            requirement_type="dimension",
            requirement_description="Critical requirement",
            expected_value=100,
            actual_value=40,
            gap_severity="blocking",
            remediation_hint="Implement data validation"
        )
        
        gap2 = TemplateGap(
            requirement_id="REQ-002",
            requirement_type="rule",
            requirement_description="Minor requirement",
            expected_value=100,
            actual_value=90,
            gap_severity="low",
            remediation_hint="Fill missing values"
        )
        
        evaluation.add_gap(gap1)
        evaluation.add_gap(gap2)
        evaluation.finalize()
        
        plan = evaluation.get_remediation_plan()
        
        assert len(plan) == 2
        # Blocking severity gaps should come first
        assert plan[0]["severity"] == "blocking"
        assert plan[0]["priority"] == 1
        assert plan[0]["remediation"] == "Implement data validation"
        
        assert plan[1]["severity"] == "low"
        assert plan[1]["priority"] == 2
    
    def test_remediation_effort_estimation(self):
        """Test remediation effort estimation."""
        # Low effort
        eval1 = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        gap1 = TemplateGap(
            requirement_id="REQ-001",
            requirement_type="dimension",
            requirement_description="Minor issue",
            expected_value=100,
            actual_value=90,
            gap_severity="low"
        )
        eval1.add_gap(gap1)
        eval1.finalize()
        assert eval1.estimated_remediation_effort == "low"
        
        # Medium effort
        eval2 = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        gap2 = TemplateGap(
            requirement_id="REQ-002",
            requirement_type="dimension",
            requirement_description="Major issue",
            expected_value=100,
            actual_value=50,
            gap_severity="high"
        )
        eval2.add_gap(gap2)
        eval2.finalize()
        assert eval2.estimated_remediation_effort == "medium"
        
        # High effort
        eval3 = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        for i in range(3):
            gap = TemplateGap(
                requirement_id=f"REQ-{i}",
                requirement_type="dimension",
                requirement_description=f"Blocking issue {i}",
                expected_value=100,
                actual_value=0,
                gap_severity="blocking"
            )
            eval3.add_gap(gap)
        eval3.finalize()
        assert eval3.estimated_remediation_effort == "high"
    
    def test_to_dict(self):
        """Test evaluation serialization to dictionary."""
        evaluation = TemplateEvaluation(
            template_id="test-template",
            template_version="1.0.0",
            template_name="Test Template"
        )
        
        # Add a passed requirement
        evaluation.add_passed_requirement("REQ-001")
        
        # Add a gap
        gap = TemplateGap(
            requirement_id="REQ-002",
            requirement_type="dimension",
            requirement_description="Test requirement",
            expected_value=80,
            actual_value=60,
            gap_severity="medium"
        )
        evaluation.add_gap(gap)
        evaluation.recommendations.append("Improve data quality")
        evaluation.finalize()
        
        eval_dict = evaluation.to_dict()
        
        assert eval_dict["template_id"] == "test-template"
        assert eval_dict["template_version"] == "1.0.0"
        assert eval_dict["template_name"] == "Test Template"
        assert eval_dict["compliant"] is False
        assert eval_dict["compliance_score"] == 50.0  # 1 passed, 1 failed
        assert len(eval_dict["gaps"]) == 1
        assert len(eval_dict["recommendations"]) == 1
        assert "evaluation_time" in eval_dict
        assert "summary" in eval_dict
