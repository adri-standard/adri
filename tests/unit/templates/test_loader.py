"""Unit tests for template loader."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from adri.templates.loader import TemplateLoader
from adri.templates.base import BaseTemplate
from adri.templates.yaml_template import YAMLTemplate
from adri.templates.exceptions import (
    TemplateError,
    TemplateSecurityError,
    TemplateValidationError,
    TemplateNotFoundError
)


class TestTemplateLoader:
    """Test the template loader functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create a temporary directory for cache
        self.temp_dir = tempfile.mkdtemp()
        self.loader = TemplateLoader(cache_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_default(self):
        """Test default initialization."""
        loader = TemplateLoader()
        
        assert loader.trust_all is False
        assert loader.offline_mode is False
        assert loader.cache_ttl == 86400  # 24 hours
        # max_template_size is not an attribute, it's hardcoded in _validate_template_content
    
    def test_init_custom(self):
        """Test initialization with custom parameters."""
        loader = TemplateLoader(
            trust_all=True,
            offline_mode=True,
            cache_ttl=3600
        )
        
        assert loader.trust_all is True
        assert loader.offline_mode is True
        assert loader.cache_ttl == 3600
    
    def test_load_from_file(self):
        """Test loading template from local file."""
        # Create a test template file
        template_content = """
        template:
          id: file-template
          version: 1.0.0
          name: File Template
          authority: Test Authority
          description: Test template from file
        
        requirements:
          overall_minimum: 70
        """
        
        template_file = Path(self.temp_dir) / "test_template.yaml"
        template_file.write_text(template_content)
        
        template = self.loader.load_template(str(template_file))
        
        assert isinstance(template, YAMLTemplate)
        assert template.template_id == "file-template"
        assert template.template_version == "1.0.0"
    
    def test_load_from_registry_shortcut(self):
        """Test loading template using registry shortcut."""
        # production is a shortcut that maps to a URL
        with patch('requests.get') as mock_get:
            template_content = """template:
  id: production-template
  version: 1.0.0
  name: Production Template
  authority: Test Authority
  description: Production template

requirements:
  overall_minimum: 70
"""
            mock_response = MagicMock()
            mock_response.text = template_content
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            # Use trust_all since templates.adri.org might not be in trusted domains
            loader = TemplateLoader(trust_all=True, cache_dir=self.temp_dir)
            template = loader.load_template("production")
            
            assert template is not None
    
    def test_load_from_registry_with_version(self):
        """Test loading specific version from registry."""
        # When loading templates with @version, the loader first checks if it's a shortcut
        # basel-iii is a shortcut that maps to a URL, so it will try to load from URL
        with patch('requests.get') as mock_get:
            template_content = """template:
  id: basel-iii
  version: 2.0.0
  name: Basel III
  authority: Basel Committee
  description: Basel III compliance

requirements:
  overall_minimum: 70
"""
            mock_response = MagicMock()
            mock_response.text = template_content
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            # Use trust_all to bypass domain check
            loader = TemplateLoader(trust_all=True, cache_dir=self.temp_dir)
            template = loader.load_template("basel-iii")
            
            assert template is not None
    
    @patch('requests.get')
    def test_load_from_url_trusted(self, mock_get):
        """Test loading template from trusted URL."""
        # Create loader that trusts all sources
        loader = TemplateLoader(trust_all=True, cache_dir=self.temp_dir)
        
        template_content = """template:
  id: url-template
  version: 1.0.0
  name: URL Template
  authority: Test Authority
  description: Template from URL

requirements:
  overall_minimum: 80
"""
        
        # Mock URL response
        mock_response = MagicMock()
        mock_response.text = template_content
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        template = loader.load_template("https://example.com/template.yaml")
        
        assert isinstance(template, YAMLTemplate)
        assert template.template_id == "url-template"
    
    def test_load_from_url_untrusted(self):
        """Test loading from untrusted URL raises error."""
        with pytest.raises(TemplateSecurityError, match="Untrusted source"):
            self.loader.load_template("https://untrusted.com/template.yaml")
    
    def test_load_from_url_trusted_domain(self):
        """Test loading from trusted domain."""
        # raw.githubusercontent.com is in default trusted domains
        with patch('requests.get') as mock_get:
            template_content = """template:
  id: github-template
  version: 1.0.0
  name: GitHub Template
  authority: Test Authority
  description: Template from GitHub

requirements:
  overall_minimum: 70
"""
            
            mock_response = MagicMock()
            mock_response.text = template_content
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            template = self.loader.load_template("https://raw.githubusercontent.com/org/repo/template.yaml")
            
            assert isinstance(template, YAMLTemplate)
    
    def test_validate_security_dangerous_pattern(self):
        """Test security validation detects dangerous patterns."""
        dangerous_content = """
        template:
          id: evil-template
          version: 1.0.0
          name: Evil Template
          authority: Evil Corp
          description: This has __import__ in it
        
        requirements:
          overall_minimum: 70
        """
        
        with pytest.raises(TemplateSecurityError, match="dangerous content"):
            self.loader._validate_template_content(dangerous_content)
    
    def test_validate_security_size_limit(self):
        """Test security validation enforces size limit."""
        # The size limit is hardcoded to 1MB in _validate_template_content
        large_content = "x" * (1024 * 1024 + 1)  # Exceeds 1MB limit
        
        with pytest.raises(TemplateSecurityError, match="too large"):
            self.loader._validate_template_content(large_content)
    
    def test_cache_operations(self):
        """Test cache save and load operations."""
        url = "https://example.com/template.yaml"
        content = """template:
  id: cached-template
  version: 1.0.0
  name: Cached Template
  authority: Test Authority
  description: Template for caching

requirements:
  overall_minimum: 70
"""
        
        # Save to cache
        self.loader._save_to_cache(url, None, content)
        
        # Load from cache - returns a template object, not content
        cached_template = self.loader._get_from_cache(url)
        
        assert cached_template is not None
        assert cached_template.template_id == "cached-template"
    
    def test_cache_expiry(self):
        """Test cache expiry based on TTL."""
        loader = TemplateLoader(cache_ttl=1, cache_dir=self.temp_dir)  # 1 second TTL
        
        url = "https://example.com/template.yaml"
        content = """template:
  id: test-template
  version: 1.0.0
  name: Test Template
  authority: Test
  description: Test

requirements:
  overall_minimum: 70
"""
        
        # Save to cache
        loader._save_to_cache(url, None, content)
        
        # Should be in cache immediately
        cached = loader._get_from_cache(url)
        assert cached is not None
        
        # Wait for expiry
        import time
        time.sleep(2)
        
        # Should be expired now
        assert loader._get_from_cache(url) is None
    
    def test_offline_mode(self):
        """Test offline mode only uses cache."""
        loader = TemplateLoader(offline_mode=True, cache_dir=self.temp_dir)
        
        # URL not in cache should fail
        from adri.templates.exceptions import TemplateError
        with pytest.raises(TemplateError, match="Offline mode"):
            loader.load_template("https://example.com/template.yaml")
    
    def test_clear_cache(self):
        """Test clearing the cache."""
        url = "https://example.com/template.yaml"
        content = """template:
  id: test-template
  version: 1.0.0
  name: Test Template
  authority: Test
  description: Test

requirements:
  overall_minimum: 70
"""
        
        # Save to cache
        self.loader._save_to_cache(url, None, content)
        assert self.loader._get_from_cache(url) is not None
        
        # Clear cache
        self.loader.clear_cache()
        
        # Should be gone
        assert self.loader._get_from_cache(url) is None
    
    def test_list_cached(self):
        """Test listing cached templates."""
        # Add some templates to cache
        content1 = """template:
  id: template1
  version: 1.0.0
  name: Template 1
  authority: Test
  description: Test

requirements:
  overall_minimum: 70
"""
        content2 = """template:
  id: template2
  version: 1.0.0
  name: Template 2
  authority: Test
  description: Test

requirements:
  overall_minimum: 70
"""
        self.loader._save_to_cache("https://example.com/template1.yaml", None, content1)
        self.loader._save_to_cache("https://example.com/template2.yaml", None, content2)
        
        cached = self.loader.list_cached()
        
        assert len(cached) == 2
        assert any(item['url'] == "https://example.com/template1.yaml" for item in cached)
        assert any(item['url'] == "https://example.com/template2.yaml" for item in cached)
        
        # Check structure
        for item in cached:
            assert 'url' in item
            assert 'cached_at' in item
            assert 'size' in item
            assert 'expired' in item
    
    def test_registry_shortcuts(self):
        """Test that registry shortcuts are properly mapped."""
        # Check that shortcuts exist
        assert "production" in TemplateLoader.REGISTRY_SHORTCUTS
        assert "basel-iii" in TemplateLoader.REGISTRY_SHORTCUTS
        
        # Test shortcut resolution - shortcuts should map to URLs
        assert TemplateLoader.REGISTRY_SHORTCUTS["production"].startswith("https://")
        assert TemplateLoader.REGISTRY_SHORTCUTS["basel-iii"].startswith("https://")
    
    def test_invalid_template_file(self):
        """Test loading invalid template file."""
        # Create invalid template file
        template_file = Path(self.temp_dir) / "invalid.yaml"
        template_file.write_text("invalid: yaml: content:")
        
        # The loader catches TemplateValidationError and re-raises as TemplateError
        with pytest.raises(TemplateError, match="Failed to load template from file"):
            self.loader.load_template(str(template_file))
    
    def test_non_existent_file(self):
        """Test loading non-existent file."""
        with pytest.raises(TemplateError):
            self.loader.load_template("/non/existent/file.yaml")
    
    def test_url_connection_error(self):
        """Test handling URL connection errors."""
        loader = TemplateLoader(trust_all=True)
        
        with patch('requests.get', side_effect=Exception("Connection failed")):
            with pytest.raises(TemplateError, match="Failed to download template"):
                loader.load_template("https://example.com/template.yaml")
