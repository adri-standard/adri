"""Unit tests for template registry."""

import pytest
from unittest.mock import Mock, patch
from adri.templates.registry import TemplateRegistry
from adri.templates.base import BaseTemplate
from adri.templates.exceptions import TemplateNotFoundError, TemplateValidationError
from adri.report import ADRIScoreReport
from adri.templates.evaluation import TemplateEvaluation


class TestTemplate(BaseTemplate):
    """Test template for registry tests."""
    
    template_id = "test-template"
    template_version = "1.0.0"
    template_name = "Test Template"
    template_authority = "Test Authority"
    template_description = "A test template"
    
    def evaluate(self, report: ADRIScoreReport) -> TemplateEvaluation:
        evaluation = TemplateEvaluation(
            template_id=self.template_id,
            template_version=self.template_version,
            template_name=self.template_name
        )
        evaluation.finalize()
        return evaluation


class TestTemplateV2(TestTemplate):
    """Version 2 of test template."""
    template_version = "2.0.0"


class TestTemplateRegistry:
    """Test the template registry functionality."""
    
    def setup_method(self):
        """Clear registry before each test."""
        TemplateRegistry._templates.clear()
        TemplateRegistry._metadata.clear()
        TemplateRegistry._instance_cache.clear()
    
    def test_register_template(self):
        """Test registering a template."""
        TemplateRegistry.register(TestTemplate)
        
        assert "test-template" in TemplateRegistry._templates
        assert "1.0.0" in TemplateRegistry._templates["test-template"]
        assert TemplateRegistry._templates["test-template"]["1.0.0"] == TestTemplate
    
    def test_register_multiple_versions(self):
        """Test registering multiple versions of same template."""
        TemplateRegistry.register(TestTemplate)
        TemplateRegistry.register(TestTemplateV2)
        
        assert "test-template" in TemplateRegistry._templates
        assert "1.0.0" in TemplateRegistry._templates["test-template"]
        assert "2.0.0" in TemplateRegistry._templates["test-template"]
    
    def test_register_duplicate_version(self):
        """Test registering duplicate version raises error."""
        TemplateRegistry.register(TestTemplate)
        
        # Create another template with same ID and version
        class DuplicateTemplate(TestTemplate):
            pass
        
        with pytest.raises(TemplateValidationError, match="already registered"):
            TemplateRegistry.register(DuplicateTemplate)
    
    def test_get_template_specific_version(self):
        """Test getting specific version of template."""
        TemplateRegistry.register(TestTemplate)
        TemplateRegistry.register(TestTemplateV2)
        
        template_class = TemplateRegistry.get_template("test-template", "1.0.0")
        assert template_class == TestTemplate
        
        template_class = TemplateRegistry.get_template("test-template", "2.0.0")
        assert template_class == TestTemplateV2
    
    def test_get_template_latest_version(self):
        """Test getting latest version when no version specified."""
        TemplateRegistry.register(TestTemplate)  # 1.0.0
        TemplateRegistry.register(TestTemplateV2)  # 2.0.0
        
        # Should return latest version (2.0.0)
        template_class = TemplateRegistry.get_template("test-template")
        assert template_class == TestTemplateV2
    
    def test_get_template_not_found(self):
        """Test getting non-existent template raises error."""
        with pytest.raises(TemplateNotFoundError):
            TemplateRegistry.get_template("non-existent")
    
    def test_get_template_version_not_found(self):
        """Test getting non-existent version raises error."""
        TemplateRegistry.register(TestTemplate)
        
        with pytest.raises(TemplateNotFoundError):
            TemplateRegistry.get_template("test-template", "9.9.9")
    
    def test_list_templates(self):
        """Test listing all registered templates."""
        TemplateRegistry.register(TestTemplate)
        TemplateRegistry.register(TestTemplateV2)
        
        # Register another template
        class AnotherTemplate(TestTemplate):
            template_id = "another-template"
            template_version = "1.0.0"
        
        TemplateRegistry.register(AnotherTemplate)
        
        templates = TemplateRegistry.list_templates()
        assert len(templates) == 3
        
        # Check format
        template_info = next(t for t in templates if t["id"] == "test-template" and t["version"] == "1.0.0")
        assert template_info["name"] == "Test Template"
        assert template_info["authority"] == "Test Authority"
        assert template_info["description"] == "A test template"
    
    def test_get_instance_caching(self):
        """Test that instances are cached."""
        TemplateRegistry.register(TestTemplate)
        
        # Get instance twice
        instance1 = TemplateRegistry.get_instance("test-template", "1.0.0")
        instance2 = TemplateRegistry.get_instance("test-template", "1.0.0")
        
        # Should be the same instance
        assert instance1 is instance2
    
    def test_get_instance_with_config(self):
        """Test getting instance with configuration."""
        class ConfigurableTemplate(TestTemplate):
            def __init__(self, config=None):
                self.config = config or {}
        
        TemplateRegistry.register(ConfigurableTemplate)
        
        config = {"threshold": 90}
        instance = TemplateRegistry.get_instance("test-template", "1.0.0", config)
        
        assert instance.config == config
    
    def test_clear_cache(self):
        """Test clearing instance cache."""
        TemplateRegistry.register(TestTemplate)
        
        # Get instance to populate cache
        instance1 = TemplateRegistry.get_instance("test-template", "1.0.0")
        
        # Clear cache
        TemplateRegistry.clear_cache()
        
        # Get instance again
        instance2 = TemplateRegistry.get_instance("test-template", "1.0.0")
        
        # Should be different instances
        assert instance1 is not instance2
    
    def test_has_template(self):
        """Test checking if template exists."""
        TemplateRegistry.register(TestTemplate)
        
        assert TemplateRegistry.has_template("test-template") is True
        assert TemplateRegistry.has_template("test-template", "1.0.0") is True
        assert TemplateRegistry.has_template("test-template", "2.0.0") is False
        assert TemplateRegistry.has_template("non-existent") is False
    
    def test_get_versions(self):
        """Test getting all versions of a template."""
        TemplateRegistry.register(TestTemplate)
        TemplateRegistry.register(TestTemplateV2)
        
        versions = TemplateRegistry.get_versions("test-template")
        assert versions == ["1.0.0", "2.0.0"]
        
        # Non-existent template
        with pytest.raises(TemplateNotFoundError):
            TemplateRegistry.get_versions("non-existent")
    
    def test_store_metadata(self):
        """Test storing template metadata."""
        metadata = {
            "author": "Test Author",
            "tags": ["test", "example"],
            "created_date": "2024-01-01"
        }
        
        TemplateRegistry.store_metadata("test-template", "1.0.0", metadata)
        
        stored = TemplateRegistry.get_metadata("test-template", "1.0.0")
        assert stored == metadata
    
    def test_get_metadata_not_found(self):
        """Test getting metadata for non-existent template."""
        metadata = TemplateRegistry.get_metadata("non-existent", "1.0.0")
        assert metadata == {}
    
    def test_version_sorting(self):
        """Test that versions are sorted correctly."""
        # Register templates in non-sequential order
        class V1(TestTemplate):
            template_version = "1.0.0"
        
        class V10(TestTemplate):
            template_version = "1.10.0"
        
        class V2(TestTemplate):
            template_version = "1.2.0"
        
        class V1_1(TestTemplate):
            template_version = "1.1.0"
        
        TemplateRegistry.register(V10)
        TemplateRegistry.register(V1)
        TemplateRegistry.register(V1_1)
        TemplateRegistry.register(V2)
        
        versions = TemplateRegistry.get_versions("test-template")
        
        # Should be sorted correctly
        assert versions == ["1.0.0", "1.1.0", "1.2.0", "1.10.0"]
        
        # Latest should be 1.10.0
        latest = TemplateRegistry.get_template("test-template")
        assert latest.template_version == "1.10.0"
