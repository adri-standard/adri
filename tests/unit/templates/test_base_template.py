"""Unit tests for the base template class."""

import pytest
from unittest.mock import Mock
from adri.templates.base import BaseTemplate
from adri.report import AssessmentReport
from adri.templates.evaluation import TemplateEvaluation


class ConcreteTemplate(BaseTemplate):
    """Concrete implementation for testing."""
    
    template_id = "test-template"
    template_version = "1.0.0"
    template_name = "Test Template"
    template_authority = "Test Authority"
    template_description = "A test template"
    
    def evaluate(self, report: AssessmentReport) -> TemplateEvaluation:
        """Simple evaluation implementation."""
        evaluation = TemplateEvaluation(
            template_id=self.template_id,
            template_version=self.template_version,
            template_name=self.template_name
        )
        evaluation.finalize()
        return evaluation


class TestBaseTemplate:
    """Test the base template functionality."""
    
    def test_abstract_class_enforcement(self):
        """Test that BaseTemplate cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseTemplate()
    
    def test_concrete_implementation(self):
        """Test that concrete implementations work correctly."""
        template = ConcreteTemplate()
        assert template.template_id == "test-template"
        assert template.template_version == "1.0.0"
        assert template.template_name == "Test Template"
    
    def test_get_metadata(self):
        """Test metadata extraction."""
        template = ConcreteTemplate()
        metadata = template.get_metadata()
        
        assert metadata["id"] == "test-template"
        assert metadata["version"] == "1.0.0"
        assert metadata["name"] == "Test Template"
        assert metadata["authority"] == "Test Authority"
        assert metadata["description"] == "A test template"
    
    def test_get_certification_info(self):
        """Test certification info generation."""
        template = ConcreteTemplate()
        cert_info = template.get_certification_info()
        
        assert cert_info["certifying_authority"] == "Test Authority"
        assert cert_info["certification_name"] == "Test Template Certification"
        assert cert_info["certification_id_prefix"] == "TEST-"
        assert cert_info["validity_period_days"] == 365
    
    def test_custom_certification_info(self):
        """Test custom certification info."""
        class CustomTemplate(ConcreteTemplate):
            validity_period_days = 180
            certification_id_prefix = "CUSTOM-"
        
        template = CustomTemplate()
        cert_info = template.get_certification_info()
        
        assert cert_info["validity_period_days"] == 180
        assert cert_info["certification_id_prefix"] == "CUSTOM-"
    
    def test_is_applicable_default(self):
        """Test default applicability check."""
        template = ConcreteTemplate()
        report = Mock(spec=AssessmentReport)
        
        # Default implementation always returns True
        assert template.is_applicable(report) is True
    
    def test_custom_is_applicable(self):
        """Test custom applicability check."""
        class SelectiveTemplate(ConcreteTemplate):
            def is_applicable(self, report: AssessmentReport) -> bool:
                return report.source_type == "database"
        
        template = SelectiveTemplate()
        
        # Test with matching source
        report1 = Mock(spec=AssessmentReport)
        report1.source_type = "database"
        assert template.is_applicable(report1) is True
        
        # Test with non-matching source
        report2 = Mock(spec=AssessmentReport)
        report2.source_type = "file"
        assert template.is_applicable(report2) is False
    
    def test_missing_required_attributes(self):
        """Test that missing required attributes raise errors."""
        class IncompleteTemplate(BaseTemplate):
            # Missing required class attributes
            def evaluate(self, report: AssessmentReport) -> TemplateEvaluation:
                pass
        
        template = IncompleteTemplate()
        
        # Should raise AttributeError when accessing required attributes
        with pytest.raises(AttributeError):
            _ = template.template_id
    
    def test_config_override(self):
        """Test configuration override mechanism."""
        class ConfigurableTemplate(ConcreteTemplate):
            default_threshold = 80
            
            def __init__(self, config=None):
                self.config = config or {}
                self.threshold = self.config.get('threshold', self.default_threshold)
        
        # Test with default
        template1 = ConfigurableTemplate()
        assert template1.threshold == 80
        
        # Test with override
        template2 = ConfigurableTemplate({'threshold': 90})
        assert template2.threshold == 90
