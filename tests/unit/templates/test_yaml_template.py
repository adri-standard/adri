"""Unit tests for YAML template implementation."""

import pytest
import yaml
from unittest.mock import Mock
from adri.templates.yaml_template import YAMLTemplate
from adri.templates.exceptions import TemplateValidationError
from adri.report import AssessmentReport
from adri.templates.evaluation import TemplateEvaluation, TemplateGap


class TestYAMLTemplate:
    """Test the YAML template functionality."""
    
    def test_from_string_valid(self):
        """Test creating template from valid YAML string."""
        yaml_content = """
        template:
          id: test-template
          version: 1.0.0
          name: Test Template
          authority: Test Authority
          description: A test template
        
        requirements:
          overall_minimum: 70
          dimension_requirements:
            validity:
              minimum_score: 14
        """
        
        template = YAMLTemplate.from_string(yaml_content)
        
        assert template.template_id == "test-template"
        assert template.template_version == "1.0.0"
        assert template.template_name == "Test Template"
        assert template.template_authority == "Test Authority"
        assert template.template_description == "A test template"
    
    def test_from_string_invalid_yaml(self):
        """Test creating template from invalid YAML."""
        yaml_content = """
        invalid: yaml: content:
        - this is not valid
        """
        
        with pytest.raises(TemplateValidationError, match="Invalid YAML"):
            YAMLTemplate.from_string(yaml_content)
    
    def test_from_file(self, tmp_path):
        """Test creating template from file."""
        yaml_content = """
        template:
          id: file-template
          version: 1.0.0
          name: File Template
          authority: Test Authority
          description: Template from file
        
        requirements:
          overall_minimum: 80
        """
        
        template_file = tmp_path / "template.yaml"
        template_file.write_text(yaml_content)
        
        template = YAMLTemplate.from_file(str(template_file))
        
        assert template.template_id == "file-template"
        assert template.template_version == "1.0.0"
    
    def test_validate_structure_missing_required(self):
        """Test validation fails with missing required fields."""
        # Missing template.id
        yaml_content = """
        template:
          version: 1.0.0
          name: Test Template
          authority: Test Authority
          description: A test template
        
        requirements:
          overall_minimum: 70
        """
        
        with pytest.raises(TemplateValidationError, match="Missing required field"):
            YAMLTemplate.from_string(yaml_content)
    
    def test_validate_structure_invalid_version(self):
        """Test validation fails with invalid version format."""
        yaml_content = """
        template:
          id: test-template
          version: invalid-version
          name: Test Template
          authority: Test Authority
          description: A test template
        
        requirements:
          overall_minimum: 70
        """
        
        with pytest.raises(TemplateValidationError, match="Invalid version format"):
            YAMLTemplate.from_string(yaml_content)
    
    def test_evaluate_overall_minimum(self):
        """Test evaluation against overall minimum score."""
        yaml_content = """
        template:
          id: test-template
          version: 1.0.0
          name: Test Template
          authority: Test Authority
          description: A test template
        
        requirements:
          overall_minimum: 80
        """
        
        template = YAMLTemplate.from_string(yaml_content)
        
        # Create mock report with score below minimum
        report = Mock(spec=AssessmentReport)
        report.overall_score = 70
        report.dimension_scores = {"validity": 70, "completeness": 70}
        
        evaluation = template.evaluate(report)
        
        assert not evaluation.compliant
        assert len(evaluation.gaps) == 1
        assert evaluation.gaps[0].requirement_id == "overall_minimum"
        assert evaluation.gaps[0].expected_value == 80
        assert evaluation.gaps[0].actual_value == 70
    
    def test_evaluate_dimension_requirements(self):
        """Test evaluation of dimension-specific requirements."""
        yaml_content = """
        template:
          id: test-template
          version: 1.0.0
          name: Test Template
          authority: Test Authority
          description: A test template
        
        requirements:
          dimension_requirements:
            validity:
              minimum_score: 16
              required_rules:
                - data_types_defined
                - schemas_validated
            completeness:
              minimum_score: 14
              max_missing_percentage: 10
        """
        
        template = YAMLTemplate.from_string(yaml_content)
        
        # Create mock report
        report = Mock(spec=AssessmentReport)
        report.overall_score = 75
        report.dimension_scores = {"validity": 12, "completeness": 18}
        report.dimension_findings = {
            "validity": {
                "data_types_defined": False,
                "schemas_validated": True,
                "other_rule": True
            },
            "completeness": {
                "missing_percentage": 15
            }
        }
        
        evaluation = template.evaluate(report)
        
        assert not evaluation.compliant
        assert len(evaluation.gaps) == 3  # 1 validity score + 1 validity rule + 1 completeness percentage
        
        # Check validity score gap
        validity_gap = next(g for g in evaluation.gaps if g.dimension == "validity" and "minimum" in g.requirement_description)
        assert validity_gap.expected_value == 16
        assert validity_gap.actual_value == 12
        
        # Check missing rule gap
        rule_gap = next(g for g in evaluation.gaps if "data_types_defined" in g.requirement_description)
        assert rule_gap.expected_value is True
        assert rule_gap.actual_value is False
        
        # Check completeness percentage gap
        completeness_gap = next(g for g in evaluation.gaps if g.dimension == "completeness")
        assert completeness_gap.expected_value == 10
        assert completeness_gap.actual_value == 15
    
    def test_evaluate_mandatory_fields(self):
        """Test evaluation of mandatory field requirements."""
        yaml_content = """
        template:
          id: test-template
          version: 1.0.0
          name: Test Template
          authority: Test Authority
          description: A test template
        
        requirements:
          mandatory_fields:
            - customer_id
            - transaction_date
            - amount
        """
        
        template = YAMLTemplate.from_string(yaml_content)
        
        # Create mock report
        report = Mock(spec=AssessmentReport)
        report.overall_score = 85
        report.dimension_scores = {"validity": 85, "completeness": 85}
        report.dimension_findings = {
            "completeness": {
                "field_presence": {
                    "customer_id": True,
                    "transaction_date": False,
                    "amount": True
                }
            }
        }
        
        evaluation = template.evaluate(report)
        
        assert not evaluation.compliant
        assert len(evaluation.gaps) == 1
        assert "transaction_date" in evaluation.gaps[0].requirement_description
    
    def test_evaluate_custom_rules(self):
        """Test evaluation of custom validation rules."""
        yaml_content = """
        template:
          id: test-template
          version: 1.0.0
          name: Test Template
          authority: Test Authority
          description: A test template
        
        requirements:
          custom_rules:
            - id: high_validity_or_completeness
              description: Either validity or completeness must be above 18
              expression: validity_score > 18 or completeness_score > 18
        """
        
        template = YAMLTemplate.from_string(yaml_content)
        
        # Create mock report where neither dimension meets the requirement
        report = Mock(spec=AssessmentReport)
        report.overall_score = 70
        report.dimension_scores = {"validity": 14, "completeness": 14}
        
        evaluation = template.evaluate(report)
        
        assert not evaluation.compliant
        assert len(evaluation.gaps) == 1
        assert "high_validity_or_completeness" in evaluation.gaps[0].requirement_id
    
    def test_evaluate_compliant(self):
        """Test evaluation when all requirements are met."""
        yaml_content = """
        template:
          id: test-template
          version: 1.0.0
          name: Test Template
          authority: Test Authority
          description: A test template
        
        requirements:
          overall_minimum: 70
          dimension_requirements:
            validity:
              minimum_score: 14
        """
        
        template = YAMLTemplate.from_string(yaml_content)
        
        # Create mock report that meets all requirements
        report = Mock(spec=AssessmentReport)
        report.overall_score = 85
        report.dimension_scores = {"validity": 16, "completeness": 18}
        
        evaluation = template.evaluate(report)
        
        assert evaluation.compliant
        assert len(evaluation.gaps) == 0
        assert evaluation.certification_eligible
    
    def test_certification_info(self):
        """Test certification info extraction from YAML."""
        yaml_content = """
        template:
          id: test-template
          version: 1.0.0
          name: Test Template
          authority: Test Authority
          description: A test template
        
        certification:
          validity_period_days: 180
          id_prefix: TST-
        
        requirements:
          overall_minimum: 70
        """
        
        template = YAMLTemplate.from_string(yaml_content)
        
        cert_info = template.get_certification_info()
        assert cert_info["validity_period_days"] == 180
        assert cert_info["certification_id_prefix"] == "TST-"
    
    def test_with_config_override(self):
        """Test template with configuration override."""
        yaml_content = """
        template:
          id: test-template
          version: 1.0.0
          name: Test Template
          authority: Test Authority
          description: A test template
        
        requirements:
          overall_minimum: 70
        """
        
        # Override the overall minimum requirement
        config = {"requirements": {"overall_minimum": 90}}
        template = YAMLTemplate.from_string(yaml_content, config)
        
        # Create mock report
        report = Mock(spec=AssessmentReport)
        report.overall_score = 80  # Above original 70, but below override 90
        report.dimension_scores = {"validity": 80}
        
        evaluation = template.evaluate(report)
        
        assert not evaluation.compliant
        assert evaluation.gaps[0].expected_value == 90
    
    def test_generate_recommendations(self):
        """Test recommendation generation based on gaps."""
        yaml_content = """
        template:
          id: test-template
          version: 1.0.0
          name: Test Template
          authority: Test Authority
          description: A test template
        
        requirements:
          overall_minimum: 80
          dimension_requirements:
            validity:
              minimum_score: 16
        
        recommendations:
          validity:
            low_score: "Implement comprehensive data validation rules"
          general:
            overall_low: "Focus on improving data quality processes"
        """
        
        template = YAMLTemplate.from_string(yaml_content)
        
        # Create mock report with low validity
        report = Mock(spec=AssessmentReport)
        report.overall_score = 70
        report.dimension_scores = {"validity": 12, "completeness": 18}
        
        evaluation = template.evaluate(report)
        
        assert len(evaluation.recommendations) > 0
        assert any("validation rules" in rec for rec in evaluation.recommendations)
