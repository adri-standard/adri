"""
Template loader with URL support for ADRI.

This module provides functionality to load templates from various sources
including local files, URLs, and the template registry.
"""

import logging
import hashlib
import json
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from urllib.parse import urlparse
import requests
from datetime import datetime, timedelta

from .base import BaseTemplate
from .yaml_template import YAMLTemplate
from .registry import TemplateRegistry
from .exceptions import (
    TemplateError,
    TemplateNotFoundError,
    TemplateValidationError,
    TemplateSecurityError,
    TemplateCacheError
)

logger = logging.getLogger(__name__)


class TemplateLoader:
    """
    Load templates from various sources with security and caching.
    
    Supports loading from:
    - Local files (YAML/JSON)
    - HTTP/HTTPS URLs
    - Template registry shortcuts
    - Cached templates
    """
    
    # Trusted domains for automatic template loading
    TRUSTED_DOMAINS = [
        'templates.adri.org',
        'raw.githubusercontent.com',
        'gitlab.com',
        'adri.io',
    ]
    
    # Registry shortcuts for common templates
    REGISTRY_SHORTCUTS = {
        'basel-iii': 'https://templates.adri.org/financial/basel-iii/latest',
        'sox': 'https://templates.adri.org/financial/sox/latest',
        'hipaa': 'https://templates.adri.org/healthcare/hipaa/latest',
        'gdpr': 'https://templates.adri.org/privacy/gdpr/latest',
        'production': 'https://templates.adri.org/general/production/latest',
        'development': 'https://templates.adri.org/general/development/latest',
    }
    
    def __init__(
        self, 
        cache_dir: Optional[Union[str, Path]] = None,
        cache_ttl: int = 86400,  # 24 hours
        trust_all: bool = False,
        offline_mode: bool = False
    ):
        """
        Initialize template loader.
        
        Args:
            cache_dir: Directory for caching templates (string or Path)
            cache_ttl: Cache time-to-live in seconds
            trust_all: Trust all sources (use with caution)
            offline_mode: Only use cached templates
        """
        # Handle string or Path input for cache_dir
        if cache_dir is not None:
            self.cache_dir = Path(cache_dir) if isinstance(cache_dir, str) else cache_dir
        else:
            self.cache_dir = Path.home() / '.adri' / 'template_cache'
        self.cache_ttl = cache_ttl
        self.trust_all = trust_all
        self.offline_mode = offline_mode
        
        # Create cache directory if needed
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache metadata file
        self.cache_metadata_file = self.cache_dir / 'metadata.json'
        self.cache_metadata = self._load_cache_metadata()
    
    def load_template(
        self, 
        source: str,
        config: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False
    ) -> BaseTemplate:
        """
        Load a template from any supported source.
        
        Args:
            source: Template identifier, file path, or URL
            config: Optional configuration overrides
            force_refresh: Force refresh even if cached
            
        Returns:
            Template instance
            
        Raises:
            TemplateError: If template cannot be loaded
        """
        logger.info(f"Loading template from: {source}")
        
        # Check for registry shortcut
        if source in self.REGISTRY_SHORTCUTS:
            source = self.REGISTRY_SHORTCUTS[source]
            logger.info(f"Resolved shortcut to: {source}")
        
        # Determine source type and load accordingly
        if source.startswith(('http://', 'https://')):
            return self._load_from_url(source, config, force_refresh)
        elif Path(source).exists():
            return self._load_from_file(source, config)
        else:
            # Try to load from registry
            try:
                return TemplateRegistry.get_template(source, config=config)
            except TemplateNotFoundError:
                # Try as a URL with default registry
                default_url = f"https://templates.adri.org/{source}/latest"
                logger.info(f"Trying default registry URL: {default_url}")
                return self._load_from_url(default_url, config, force_refresh)
    
    def _load_from_url(
        self, 
        url: str,
        config: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False
    ) -> BaseTemplate:
        """Load template from URL with security checks and caching."""
        # Check if offline mode
        if self.offline_mode and not self._is_cached(url):
            raise TemplateError(f"Offline mode: template not cached: {url}")
        
        # Parse URL and extract version if present
        parsed_url = urlparse(url)
        version = None
        if '@' in parsed_url.path:
            path_parts = parsed_url.path.rsplit('@', 1)
            base_path = path_parts[0]
            version = path_parts[1]
            url = url.replace(f'@{version}', '')
        
        # Security check
        if not self._is_trusted_source(url) and not self.trust_all:
            raise TemplateSecurityError(
                f"Untrusted source: {url}. "
                f"Add --trust-all flag or use a trusted domain: {self.TRUSTED_DOMAINS}"
            )
        
        # Check cache unless forced refresh
        if not force_refresh and not self.offline_mode:
            cached_template = self._get_from_cache(url, version)
            if cached_template:
                logger.info(f"Using cached template: {url}")
                return cached_template
        
        # Download template
        try:
            logger.info(f"Downloading template from: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            template_content = response.text
        except requests.RequestException as e:
            if self.offline_mode:
                raise TemplateError(f"Cannot download in offline mode: {e}")
            # Try cache as fallback
            cached_template = self._get_from_cache(url, version, ignore_ttl=True)
            if cached_template:
                logger.warning(f"Download failed, using stale cache: {e}")
                return cached_template
            raise TemplateError(f"Failed to download template: {e}")
        
        # Validate content
        self._validate_template_content(template_content)
        
        # Create template instance
        try:
            template = YAMLTemplate.from_string(template_content, config)
        except Exception as e:
            raise TemplateValidationError(f"Invalid template content: {e}")
        
        # Cache the template
        self._save_to_cache(url, version, template_content)
        
        return template
    
    def _load_from_file(
        self, 
        file_path: Union[str, Path],
        config: Optional[Dict[str, Any]] = None
    ) -> BaseTemplate:
        """Load template from local file."""
        try:
            return YAMLTemplate.from_file(file_path, config)
        except Exception as e:
            raise TemplateError(f"Failed to load template from file: {e}")
    
    def _is_trusted_source(self, url: str) -> bool:
        """Check if URL is from a trusted source."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        return any(
            domain == trusted or domain.endswith(f'.{trusted}')
            for trusted in self.TRUSTED_DOMAINS
        )
    
    def _validate_template_content(self, content: str):
        """Validate template content for security and correctness."""
        # Check size
        max_size = 1024 * 1024  # 1MB
        if len(content) > max_size:
            raise TemplateSecurityError(f"Template too large: {len(content)} bytes")
        
        # Basic structure validation (more checks can be added)
        if not content.strip():
            raise TemplateValidationError("Empty template content")
        
        # Check for potentially dangerous content
        dangerous_patterns = ['exec(', 'eval(', '__import__', 'subprocess']
        for pattern in dangerous_patterns:
            if pattern in content:
                raise TemplateSecurityError(f"Potentially dangerous content: {pattern}")
    
    def _get_cache_key(self, url: str, version: Optional[str] = None) -> str:
        """Generate cache key for URL."""
        key = hashlib.sha256(url.encode()).hexdigest()[:16]
        if version:
            key = f"{key}_{version}"
        return key
    
    def _get_cache_path(self, url: str, version: Optional[str] = None) -> Path:
        """Get cache file path for URL."""
        cache_key = self._get_cache_key(url, version)
        return self.cache_dir / f"{cache_key}.yaml"
    
    def _is_cached(self, url: str, version: Optional[str] = None) -> bool:
        """Check if template is cached."""
        cache_path = self._get_cache_path(url, version)
        return cache_path.exists()
    
    def _get_from_cache(
        self, 
        url: str, 
        version: Optional[str] = None,
        ignore_ttl: bool = False
    ) -> Optional[BaseTemplate]:
        """Get template from cache if valid."""
        cache_path = self._get_cache_path(url, version)
        if not cache_path.exists():
            return None
        
        # Check TTL
        cache_key = self._get_cache_key(url, version)
        if not ignore_ttl and cache_key in self.cache_metadata:
            cached_time = datetime.fromisoformat(self.cache_metadata[cache_key]['cached_at'])
            if datetime.now() - cached_time > timedelta(seconds=self.cache_ttl):
                logger.info(f"Cache expired for: {url}")
                return None
        
        # Load from cache
        try:
            return YAMLTemplate.from_file(cache_path)
        except Exception as e:
            logger.error(f"Failed to load from cache: {e}")
            return None
    
    def _save_to_cache(self, url: str, version: Optional[str], content: str):
        """Save template to cache."""
        cache_path = self._get_cache_path(url, version)
        cache_key = self._get_cache_key(url, version)
        
        try:
            # Save template content
            with open(cache_path, 'w') as f:
                f.write(content)
            
            # Update metadata
            self.cache_metadata[cache_key] = {
                'url': url,
                'version': version,
                'cached_at': datetime.now().isoformat(),
                'size': len(content)
            }
            self._save_cache_metadata()
            
            logger.info(f"Cached template: {url}")
        except Exception as e:
            logger.error(f"Failed to cache template: {e}")
    
    def _load_cache_metadata(self) -> Dict[str, Any]:
        """Load cache metadata."""
        if self.cache_metadata_file.exists():
            try:
                with open(self.cache_metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cache metadata: {e}")
        return {}
    
    def _save_cache_metadata(self):
        """Save cache metadata."""
        try:
            with open(self.cache_metadata_file, 'w') as f:
                json.dump(self.cache_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
    
    def clear_cache(self):
        """Clear all cached templates."""
        try:
            for cache_file in self.cache_dir.glob('*.yaml'):
                cache_file.unlink()
            self.cache_metadata = {}
            self._save_cache_metadata()
            logger.info("Template cache cleared")
        except Exception as e:
            raise TemplateCacheError(f"Failed to clear cache: {e}")
    
    def list_cached(self) -> List[Dict[str, Any]]:
        """List all cached templates."""
        cached = []
        for key, metadata in self.cache_metadata.items():
            metadata['cache_key'] = key
            metadata['expired'] = False
            
            # Check if expired
            cached_time = datetime.fromisoformat(metadata['cached_at'])
            if datetime.now() - cached_time > timedelta(seconds=self.cache_ttl):
                metadata['expired'] = True
            
            cached.append(metadata)
        
        return cached

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/templates/test_loader.py
#    - tests/unit/templates/test_loader_security.py
#    - tests/unit/templates/test_loader_cache.py
# 
# 2. Integration tests:
#    - tests/integration/templates/test_url_loading.py
#    - tests/integration/templates/test_offline_mode.py
#
# Complete test coverage details are documented in:
# docs/test_coverage/TEMPLATES_test_coverage.md
# ----------------------------------------------
