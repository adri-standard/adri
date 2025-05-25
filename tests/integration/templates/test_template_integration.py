"""Integration tests for the templates system."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from adri.assessor import AssessmentReport
from adri.templates.loader import TemplateLoader
from adri.templates.registry import TemplateRegistry
from adri.templates.yaml_template import YAMLTemplate
from adri.templates.base import BaseTemplate
from adri.templates.evaluation import TemplateEvaluation
from adri.templates.exceptions import TemplateNotFoundError, TemplateValidationError


class ProductionTemplate(BaseTemplate):
    """A production-ready template for integration testing."""
    
    template_id = "production"
    template_version = "1.0.0"
    template_name = "Production Data Template"
    template_authority = "ADRI Standards Board"
    template_description = "Standard template for production data quality"
    
    def evaluate(self, report: AssessmentReport) -> TemplateEvaluation:
        evaluation = TemplateEvaluation(
            template_id=self.template_id,
            template_version=self.template_version,
            template_name=self.template_name
        )
        
        # Check overall score
        if report.overall_score < 80:
            evaluation.add_gap(
                requirement_id="overall_minimum",
                requirement_description="Overall score must be at least 80",
                expected_value=80,
                actual_value=report.overall_score,
                dimension="overall"
            )
        
        # Check dimension scores
        for dimension, score in report.dimension_scores.items():
            if score < 16:
                evaluation.add_gap(
                    requirement_id=f"{dimension}_minimum",
                    requirement_description=f"{dimension.capitalize()} score must be at least 16",
                    expected_value=16,
                    actual_value=score,
                    dimension=dimension
                )
        
        evaluation.finalize(
            overall_score=report.overall_score,
            dimension_scores=report.dimension_scores
        )
        
        return evaluation


class TestTemplateIntegration:
    """Test the complete templates workflow."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clear registry
        TemplateRegistry._templates.clear()
        TemplateRegistry._metadata.clear()
        TemplateRegistry._instance_cache.clear()
        
        # Register test template
        TemplateRegistry.register(ProductionTemplate)
        
        # Create temp directory for file operations
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        # Clean up temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_and_evaluate_from_registry(self):
        """Test loading template from registry and evaluating."""
        # Create loader
        loader = TemplateLoader()
        
        # Load template from registry
        template = loader.load_template("production")
        
        assert isinstance(template, ProductionTemplate)
        assert template.template_id == "production"
        
        # Create a mock report
        report = Mock(spec=AssessmentReport)
        report.overall_score = 85
        report.dimension_scores = {
            "validity": 17,
            "completeness": 18,
            "freshness": 16,
            "consistency": 17,
            "plausibility": 17
        }
        
        # Evaluate
        evaluation = template.evaluate(report)
        
        assert evaluation.compliant is True
        assert len(evaluation.gaps) == 0
        assert evaluation.certification_eligible is True
    
    def test_load_yaml_template_from_file(self):
        """Test loading YAML template from file."""
        # Create YAML template file
        yaml_content = """
        template:
          id: file-test
          version: 1.0.0
          name: File Test Template
          authority: Test Authority
          description: Template loaded from file
        
        requirements:
          overall_minimum: 75
          dimension_requirements:
            validity:
              minimum_score: 15
        """
        
        template_file = Path(self.temp_dir) / "test_template.yaml"
        template_file.write_text(yaml_content)
        
        # Load template
        loader = TemplateLoader()
        template = loader.load_template(str(template_file))
        
        assert isinstance(template, YAMLTemplate)
        assert template.template_id == "file-test"
        
        # Create report that fails requirements
        report = Mock(spec=AssessmentReport)
        report.overall_score = 70  # Below minimum
        report.dimension_scores = {"validity": 14, "completeness": 18}
        
        # Evaluate
        evaluation = template.evaluate(report)
        
        assert evaluation.compliant is False
        assert len(evaluation.gaps) == 2  # Overall and validity
    
    def test_template_with_certification(self):
        """Test template evaluation with certification info."""
        yaml_content = """
        template:
          id: cert-test
          version: 1.0.0
          name: Certification Test Template
          authority: Certification Authority
          description: Template with certification config
        
        certification:
          validity_period_days: 180
          id_prefix: CERT-
        
        requirements:
          overall_minimum: 80
        """
        
        template = YAMLTemplate.from_string(yaml_content)
        
        # Check certification info
        cert_info = template.get_certification_info()
        assert cert_info["validity_period_days"] == 180
        assert cert_info["certification_id_prefix"] == "CERT-"
        assert cert_info["certifying_authority"] == "Certification Authority"
        
        # Create compliant report
        report = Mock(spec=AssessmentReport)
        report.overall_score = 85
        report.dimension_scores = {"validity": 17, "completeness": 17}
        
        evaluation = template.evaluate(report)
        assert evaluation.certification_eligible is True
    
    def test_template_version_management(self):
        """Test managing multiple template versions."""
        # Register version 2
        class ProductionTemplateV2(ProductionTemplate):
            template_version = "2.0.0"
            
            def evaluate(self, report: AssessmentReport) -> TemplateEvaluation:
                # More stringent requirements
                evaluation = TemplateEvaluation(
                    template_id=self.template_id,
                    template_version=self.template_version,
                    template_name=self.template_name
                )
                
                if report.overall_score < 85:  # Higher threshold
                    evaluation.add_gap(
                        requirement_id="overall_minimum",
                        requirement_description="Overall score must be at least 85",
                        expected_value=85,
                        actual_value=report.overall_score,
                        dimension="overall"
                    )
                
                evaluation.finalize(
                    overall_score=report.overall_score,
                    dimension_scores=report.dimension_scores
                )
                
                return evaluation
        
        TemplateRegistry.register(ProductionTemplateV2)
        
        # Load specific versions
        loader = TemplateLoader()
        
        v1 = loader.load_template("production@1.0.0")
        assert v1.template_version == "1.0.0"
        
        v2 = loader.load_template("production@2.0.0")
        assert v2.template_version == "2.0.0"
        
        # Default should be latest
        latest = loader.load_template("production")
        assert latest.template_version == "2.0.0"
        
        # Test different requirements
        report = Mock(spec=AssessmentReport)
        report.overall_score = 82
        report.dimension_scores = {"validity": 16, "completeness": 16}
        
        # V1 should pass
        eval_v1 = v1.evaluate(report)
        assert eval_v1.compliant is True
        
        # V2 should fail
        eval_v2 = v2.evaluate(report)
        assert eval_v2.compliant is False
    
    def test_yaml_template_complex_requirements(self):
        """Test YAML template with complex requirement expressions."""
        yaml_content = """
        template:
          id: complex-test
          version: 1.0.0
          name: Complex Requirements Template
          authority: Test Authority
          description: Template with complex validation rules
        
        requirements:
          overall_minimum: 70
          
          dimension_requirements:
            validity:
              minimum_score: 14
              required_rules:
                - data_types_defined
                - schemas_validated
            
            completeness:
              minimum_score: 14
              max_missing_percentage: 15
          
          mandatory_fields:
            - customer_id
            - transaction_date
            - amount
          
          custom_rules:
            - id: high_quality_check
              description: Either validity and completeness both above 16, or overall above 85
              expression: (validity_score > 16 and completeness_score > 16) or overall_score > 85
        """
        
        template = YAMLTemplate.from_string(yaml_content)
        
        # Create report with mixed compliance
        report = Mock(spec=AssessmentReport)
        report.overall_score = 75
        report.dimension_scores = {"validity": 15, "completeness": 15}
        report.dimension_findings = {
            "validity": {
                "data_types_defined": True,
                "schemas_validated": False
            },
            "completeness": {
                "missing_percentage": 10,
                "field_presence": {
                    "customer_id": True,
                    "transaction_date": True,
                    "amount": False
                }
            }
        }
        
        evaluation = template.evaluate(report)
        
        # Should have gaps for:
        # 1. schemas_validated rule
        # 2. amount field missing
        # 3. custom rule failing
        assert evaluation.compliant is False
        assert len(evaluation.gaps) >= 3
        
        # Check specific gaps
        rule_gaps = [g for g in evaluation.gaps if "schemas_validated" in g.requirement_description]
        assert len(rule_gaps) == 1
        
        field_gaps = [g for g in evaluation.gaps if "amount" in g.requirement_description]
        assert len(field_gaps) == 1
        
        custom_gaps = [g for g in evaluation.gaps if g.requirement_id == "high_quality_check"]
        assert len(custom_gaps) == 1
    
    def test_remediation_plan_generation(self):
        """Test generating remediation plans from evaluations."""
        yaml_content = """
        template:
          id: remediation-test
          version: 1.0.0
          name: Remediation Test Template
          authority: Test Authority
          description: Template for testing remediation plans
        
        requirements:
          dimension_requirements:
            validity:
              minimum_score: 16
            completeness:
              minimum_score: 16
            consistency:
              minimum_score: 14
        """
        
        template = YAMLTemplate.from_string(yaml_content)
        
        # Create report with failures
        report = Mock(spec=AssessmentReport)
        report.overall_score = 65
        report.dimension_scores = {
            "validity": 10,  # Major gap
            "completeness": 15,  # Minor gap
            "consistency": 18,  # Passing
            "freshness": 14,
            "plausibility": 12
        }
        
        evaluation = template.evaluate(report)
        plan = evaluation.generate_remediation_plan()
        
        # Should have 2 items in plan
        assert len(plan) == 2
        
        # Validity should be prioritized (larger gap)
        assert plan[0]["gap"]["dimension"] == "validity"
        assert plan[0]["priority"] == "High"
        
        # Completeness should be second
        assert plan[1]["gap"]["dimension"] == "completeness"
        assert plan[1]["priority"] == "Low"
    
    @patch('urllib.request.urlopen')
    def test_load_template_from_url(self, mock_urlopen):
        """Test loading template from URL with caching."""
        # Create loader with trust_all for testing
        loader = TemplateLoader(trust_all=True, cache_dir=self.temp_dir)
        
        yaml_content = """
        template:
          id: url-test
          version: 1.0.0
          name: URL Test Template
          authority: Test Authority
          description: Template loaded from URL
        
        requirements:
          overall_minimum: 75
        """
        
        # Mock URL response
        from unittest.mock import MagicMock
        mock_response = MagicMock()
        mock_response.read.return_value = yaml_content.encode('utf-8')
        mock_response.headers = {'content-length': str(len(yaml_content))}
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # First load - should hit URL
        template1 = loader.load_template("https://example.com/template.yaml")
        assert template1.template_id == "url-test"
        assert mock_urlopen.call_count == 1
        
        # Second load - should use cache
        template2 = loader.load_template("https://example.com/template.yaml")
        assert template2.template_id == "url-test"
        assert mock_urlopen.call_count == 1  # No additional call
        
        # List cached templates
        cached = loader.list_cached()
        assert len(cached) == 1
        assert cached[0]['url'] == "https://example.com/template.yaml"
    
    def test_error_handling(self):
        """Test error handling throughout the system."""
        loader = TemplateLoader()
        
        # Non-existent template
        with pytest.raises(TemplateNotFoundError):
            loader.load_template("non-existent")
        
        # Invalid YAML file
        invalid_file = Path(self.temp_dir) / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content:")
        
        with pytest.raises(TemplateValidationError):
            loader.load_template(str(invalid_file))
        
        # Invalid version format in YAML
        invalid_version = """
        template:
          id: test
          version: invalid-version
          name: Test
          authority: Test
          description: Test
        
        requirements:
          overall_minimum: 70
        """
        
        with pytest.raises(TemplateValidationError, match="version"):
            YAMLTemplate.from_string(invalid_version)
