"""Unit tests for template exception classes."""

import pytest
from adri.templates.exceptions import (
    TemplateError,
    TemplateNotFoundError,
    TemplateValidationError,
    TemplateLoadError,
    TemplateSecurityError
)


class TestTemplateExceptions:
    """Test template exception classes."""
    
    def test_base_template_error(self):
        """Test base TemplateError."""
        error = TemplateError("Base template error")
        assert str(error) == "Base template error"
        assert isinstance(error, Exception)
    
    def test_template_not_found_error(self):
        """Test TemplateNotFoundError."""
        error = TemplateNotFoundError("Template 'test-template' not found")
        assert str(error) == "Template 'test-template' not found"
        assert isinstance(error, TemplateError)
        
        # Test with template ID
        error2 = TemplateNotFoundError(template_id="missing-template")
        assert "missing-template" in str(error2)
    
    def test_template_validation_error(self):
        """Test TemplateValidationError."""
        error = TemplateValidationError("Invalid template structure")
        assert str(error) == "Invalid template structure"
        assert isinstance(error, TemplateError)
        
        # Test with validation details
        error2 = TemplateValidationError(
            "Missing required field",
            field="template.id",
            template_source="test.yaml"
        )
        assert "Missing required field" in str(error2)
        assert hasattr(error2, 'field')
        assert error2.field == "template.id"
    
    def test_template_load_error(self):
        """Test TemplateLoadError."""
        error = TemplateLoadError("Failed to load template from URL")
        assert str(error) == "Failed to load template from URL"
        assert isinstance(error, TemplateError)
        
        # Test with source details
        error2 = TemplateLoadError(
            "Connection timeout",
            source="https://example.com/template.yaml",
            cause="Network error"
        )
        assert "Connection timeout" in str(error2)
        assert hasattr(error2, 'source')
        assert error2.source == "https://example.com/template.yaml"
    
    def test_template_security_error(self):
        """Test TemplateSecurityError."""
        error = TemplateSecurityError("Untrusted template source")
        assert str(error) == "Untrusted template source"
        assert isinstance(error, TemplateError)
        
        # Test with security details
        error2 = TemplateSecurityError(
            "Domain not in trusted list",
            domain="untrusted.com",
            trusted_domains=["trusted1.com", "trusted2.com"]
        )
        assert "Domain not in trusted list" in str(error2)
        assert hasattr(error2, 'domain')
        assert error2.domain == "untrusted.com"
    
    def test_exception_inheritance(self):
        """Test exception inheritance chain."""
        # All template exceptions should inherit from TemplateError
        assert issubclass(TemplateNotFoundError, TemplateError)
        assert issubclass(TemplateValidationError, TemplateError)
        assert issubclass(TemplateLoadError, TemplateError)
        assert issubclass(TemplateSecurityError, TemplateError)
        
        # TemplateError should inherit from Exception
        assert issubclass(TemplateError, Exception)
    
    def test_exception_with_cause(self):
        """Test exceptions with underlying causes."""
        try:
            # Simulate an underlying error
            raise ValueError("Original error")
        except ValueError as e:
            # Wrap in template error
            template_error = TemplateLoadError("Failed to parse YAML")
            template_error.__cause__ = e
            
            assert template_error.__cause__ is not None
            assert isinstance(template_error.__cause__, ValueError)
            assert str(template_error.__cause__) == "Original error"
    
    def test_custom_error_attributes(self):
        """Test custom attributes on exceptions."""
        # Create error with custom attributes
        error = TemplateValidationError("Validation failed")
        error.template_id = "test-template"
        error.validation_errors = [
            "Missing required field: name",
            "Invalid version format"
        ]
        
        assert hasattr(error, 'template_id')
        assert error.template_id == "test-template"
        assert hasattr(error, 'validation_errors')
        assert len(error.validation_errors) == 2
    
    def test_error_messages(self):
        """Test error message formatting."""
        # Simple message
        error1 = TemplateError("Simple error")
        assert str(error1) == "Simple error"
        
        # Message with formatting
        template_id = "basel-iii"
        version = "1.0.0"
        error2 = TemplateNotFoundError(
            f"Template '{template_id}' version '{version}' not found in registry"
        )
        assert template_id in str(error2)
        assert version in str(error2)
        
        # Empty message
        error3 = TemplateError("")
        assert str(error3) == ""
        
        # None message (should handle gracefully)
        error4 = TemplateError()
        assert str(error4) == ""
