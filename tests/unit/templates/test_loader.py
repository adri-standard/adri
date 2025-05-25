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
    TemplateLoadError,
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
        assert loader.max_template_size == 10 * 1024 * 1024  # 10MB
    
    def test_init_custom(self):
        """Test initialization with custom parameters."""
        loader = TemplateLoader(
            trust_all=True,
            offline_mode=True,
            cache_ttl=3600,
            max_template_size=1024
        )
        
        assert loader.trust_all is True
        assert loader.offline_mode is True
        assert loader.cache_ttl == 3600
        assert loader.max_template_size == 1024
    
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
        # Mock the registry to return a template class
        mock_template_class = Mock(spec=BaseTemplate)
        mock_template_class.return_value = Mock(spec=BaseTemplate)
        
        with patch('adri.templates.registry.TemplateRegistry.has_template', return_value=True):
            with patch('adri.templates.registry.TemplateRegistry.get_template', return_value=mock_template_class):
                template = self.loader.load_template("production")
                
                assert template is not None
    
    def test_load_from_registry_with_version(self):
        """Test loading specific version from registry."""
        mock_template_class = Mock(spec=BaseTemplate)
        mock_template_class.return_value = Mock(spec=BaseTemplate)
        
        with patch('adri.templates.registry.TemplateRegistry.has_template', return_value=True):
            with patch('adri.templates.registry.TemplateRegistry.get_template', return_value=mock_template_class) as mock_get:
                template = self.loader.load_template("basel-iii@2.0.0")
                
                # Check that get_template was called with correct version
                mock_get.assert_called_with("basel-iii", "2.0.0")
    
    @patch('urllib.request.urlopen')
    def test_load_from_url_trusted(self, mock_urlopen):
        """Test loading template from trusted URL."""
        # Create loader that trusts all sources
        loader = TemplateLoader(trust_all=True, cache_dir=self.temp_dir)
        
        template_content = """
        template:
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
        mock_response.read.return_value = template_content.encode('utf-8')
        mock_response.headers = {'content-length': str(len(template_content))}
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        template = loader.load_template("https://example.com/template.yaml")
        
        assert isinstance(template, YAMLTemplate)
        assert template.template_id == "url-template"
    
    def test_load_from_url_untrusted(self):
        """Test loading from untrusted URL raises error."""
        with pytest.raises(TemplateSecurityError, match="not in trusted domains"):
            self.loader.load_template("https://untrusted.com/template.yaml")
    
    def test_load_from_url_trusted_domain(self):
        """Test loading from trusted domain."""
        # github.com is in default trusted domains
        with patch('urllib.request.urlopen') as mock_urlopen:
            template_content = """
            template:
              id: github-template
              version: 1.0.0
              name: GitHub Template
              authority: Test Authority
              description: Template from GitHub
            
            requirements:
              overall_minimum: 70
            """
            
            mock_response = MagicMock()
            mock_response.read.return_value = template_content.encode('utf-8')
            mock_response.headers = {'content-length': str(len(template_content))}
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            template = self.loader.load_template("https://github.com/org/repo/template.yaml")
            
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
        
        with pytest.raises(TemplateSecurityError, match="dangerous patterns"):
            self.loader._validate_security(dangerous_content, "evil.yaml")
    
    def test_validate_security_size_limit(self):
        """Test security validation enforces size limit."""
        loader = TemplateLoader(max_template_size=100)  # Very small limit
        
        large_content = "x" * 200  # Exceeds limit
        
        with pytest.raises(TemplateSecurityError, match="exceeds maximum"):
            loader._validate_security(large_content, "large.yaml")
    
    def test_cache_operations(self):
        """Test cache save and load operations."""
        url = "https://example.com/template.yaml"
        content = """
        template:
          id: cached-template
          version: 1.0.0
          name: Cached Template
          authority: Test Authority
          description: Template for caching
        
        requirements:
          overall_minimum: 70
        """
        
        # Save to cache
        self.loader._save_to_cache(url, content)
        
        # Load from cache
        cached_content = self.loader._load_from_cache(url)
        
        assert cached_content == content
    
    def test_cache_expiry(self):
        """Test cache expiry based on TTL."""
        loader = TemplateLoader(cache_ttl=1, cache_dir=self.temp_dir)  # 1 second TTL
        
        url = "https://example.com/template.yaml"
        content = "test content"
        
        # Save to cache
        loader._save_to_cache(url, content)
        
        # Should be in cache immediately
        assert loader._load_from_cache(url) == content
        
        # Wait for expiry
        import time
        time.sleep(2)
        
        # Should be expired now
        assert loader._load_from_cache(url) is None
    
    def test_offline_mode(self):
        """Test offline mode only uses cache."""
        loader = TemplateLoader(offline_mode=True, cache_dir=self.temp_dir)
        
        # URL not in cache should fail
        with pytest.raises(TemplateLoadError, match="offline mode"):
            loader.load_template("https://example.com/template.yaml")
    
    def test_clear_cache(self):
        """Test clearing the cache."""
        url = "https://example.com/template.yaml"
        content = "test content"
        
        # Save to cache
        self.loader._save_to_cache(url, content)
        assert self.loader._load_from_cache(url) == content
        
        # Clear cache
        self.loader.clear_cache()
        
        # Should be gone
        assert self.loader._load_from_cache(url) is None
    
    def test_list_cached(self):
        """Test listing cached templates."""
        # Add some templates to cache
        self.loader._save_to_cache("https://example.com/template1.yaml", "content1")
        self.loader._save_to_cache("https://example.com/template2.yaml", "content2")
        
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
        
        # Test shortcut resolution
        with patch('adri.templates.registry.TemplateRegistry.has_template', return_value=True):
            # Should recognize as registry ID
            assert self.loader._is_registry_id("production")
            assert self.loader._is_registry_id("basel-iii")
    
    def test_invalid_template_file(self):
        """Test loading invalid template file."""
        # Create invalid template file
        template_file = Path(self.temp_dir) / "invalid.yaml"
        template_file.write_text("invalid: yaml: content:")
        
        with pytest.raises(TemplateValidationError):
            self.loader.load_template(str(template_file))
    
    def test_non_existent_file(self):
        """Test loading non-existent file."""
        with pytest.raises(TemplateLoadError, match="not found"):
            self.loader.load_template("/non/existent/file.yaml")
    
    def test_url_connection_error(self):
        """Test handling URL connection errors."""
        loader = TemplateLoader(trust_all=True)
        
        with patch('urllib.request.urlopen', side_effect=Exception("Connection failed")):
            with pytest.raises(TemplateLoadError, match="Connection failed"):
                loader.load_template("https://example.com/template.yaml")
