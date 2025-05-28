"""
Registry for ADRI certification templates.

This module provides a registry pattern for managing and discovering
certification templates, similar to the existing dimension and connector
registries in ADRI.
"""

import logging
from typing import Dict, Type, Optional, List, Any
from pathlib import Path

from .base import BaseTemplate
from .exceptions import TemplateNotFoundError, TemplateVersionError

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """
    Central registry for certification templates.
    
    Manages template registration, discovery, and instantiation.
    Supports versioned templates and lazy loading.
    """
    
    # Class-level storage for registered templates
    _templates: Dict[str, Dict[str, Type[BaseTemplate]]] = {}
    _instances: Dict[str, BaseTemplate] = {}
    _instance_cache: Dict[str, BaseTemplate] = {}  # Alias for compatibility
    _metadata: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def register(cls, template_class: Type[BaseTemplate], template_id: Optional[str] = None, version: Optional[str] = None):
        """
        Register a template class.
        
        Args:
            template_class: Template class (must inherit from BaseTemplate)
            template_id: Optional template ID (defaults to class attribute)
            version: Optional version string (defaults to class attribute)
        """
        if not issubclass(template_class, BaseTemplate):
            raise ValueError(f"{template_class} must inherit from BaseTemplate")
        
        # Get template_id from class if not provided
        if template_id is None:
            template_id = getattr(template_class, 'template_id', None)
            if not template_id:
                raise ValueError(f"{template_class} must define template_id")
        
        # Get version from class if not provided
        if version is None:
            version = getattr(template_class, 'template_version', None)
            if not version:
                raise ValueError(f"{template_class} must define template_version")
        
        # Initialize nested dict if needed
        if template_id not in cls._templates:
            cls._templates[template_id] = {}
            cls._metadata[template_id] = {}
        
        # Check if already registered
        if version in cls._templates[template_id]:
            from .exceptions import TemplateValidationError
            raise TemplateValidationError(
                f"Template {template_id} version {version} already registered"
            )
        
        # Register the template class
        cls._templates[template_id][version] = template_class
        
        # Store metadata
        cls._metadata[template_id][version] = {
            'class': template_class.__name__,
            'module': template_class.__module__,
            'version': version
        }
        
        logger.info(f"Registered template: {template_id} v{version}")
    
    @classmethod
    def get_template(
        cls, 
        template_id: str, 
        version: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseTemplate:
        """
        Get a template instance.
        
        Args:
            template_id: Template identifier
            version: Specific version (if None, uses latest)
            config: Optional configuration for the template
            
        Returns:
            Template instance
            
        Raises:
            TemplateNotFoundError: If template not found
            TemplateVersionError: If specific version not found
        """
        # Build cache key
        cache_key = f"{template_id}:{version or 'latest'}"
        if config:
            cache_key += f":{hash(str(sorted(config.items())))}"
        
        # Check cache first
        if cache_key in cls._instances:
            return cls._instances[cache_key]
        
        # Check if template exists
        if template_id not in cls._templates:
            raise TemplateNotFoundError(
                f"Template '{template_id}' not found. "
                f"Available templates: {cls.list_templates()}"
            )
        
        # Get version
        if version is None:
            # Get latest version (sorted)
            available_versions = list(cls._templates[template_id].keys())
            if not available_versions:
                raise TemplateVersionError(f"No versions available for {template_id}")
            # Simple version sorting - in production would use proper semver
            version = sorted(available_versions)[-1]
        elif version not in cls._templates[template_id]:
            raise TemplateVersionError(
                f"Version '{version}' not found for template '{template_id}'. "
                f"Available versions: {list(cls._templates[template_id].keys())}"
            )
        
        # Instantiate template
        template_class = cls._templates[template_id][version]
        instance = template_class(config)
        
        # Cache the instance
        cls._instances[cache_key] = instance
        
        return instance
    
    @classmethod
    def list_templates(cls) -> List[Dict[str, Any]]:
        """
        List all registered templates with their information.
        
        Returns:
            List of template information dictionaries
        """
        templates = []
        for template_id, versions in cls._templates.items():
            for version, template_class in versions.items():
                info = {
                    "id": template_id,
                    "version": version,
                    "name": getattr(template_class, 'template_name', 'Unknown'),
                    "authority": getattr(template_class, 'template_authority', 'Unknown'),
                    "description": getattr(template_class, 'template_description', ''),
                }
                templates.append(info)
        return templates
    
    @classmethod
    def has_template(cls, template_id: str, version: Optional[str] = None) -> bool:
        """
        Check if a template exists.
        
        Args:
            template_id: Template identifier
            version: Specific version to check (if None, checks if any version exists)
            
        Returns:
            True if template exists, False otherwise
        """
        if template_id not in cls._templates:
            return False
        
        if version is None:
            return True
        
        return version in cls._templates[template_id]
    
    @classmethod
    def get_versions(cls, template_id: str) -> List[str]:
        """
        Get all versions of a template.
        
        Args:
            template_id: Template identifier
            
        Returns:
            List of version strings
            
        Raises:
            TemplateNotFoundError: If template not found
        """
        if template_id not in cls._templates:
            raise TemplateNotFoundError(f"Template '{template_id}' not found")
        
        return list(cls._templates[template_id].keys())
    
    @classmethod
    def get_instance(
        cls,
        template_id: str,
        version: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseTemplate:
        """
        Get a template instance (alias for get_template).
        
        Args:
            template_id: Template identifier
            version: Specific version (if None, uses latest)
            config: Optional configuration for the template
            
        Returns:
            Template instance
        """
        return cls.get_template(template_id, version, config)
    
    @classmethod
    def store_metadata(cls, template_id: str, version: str, metadata: Dict[str, Any]):
        """
        Store additional metadata for a template.
        
        Args:
            template_id: Template identifier
            version: Template version
            metadata: Metadata dictionary
        """
        if template_id not in cls._metadata:
            cls._metadata[template_id] = {}
        if version not in cls._metadata[template_id]:
            cls._metadata[template_id][version] = {}
        
        cls._metadata[template_id][version].update(metadata)
    
    @classmethod
    def get_metadata(cls, template_id: str, version: str) -> Dict[str, Any]:
        """
        Get metadata for a template.
        
        Args:
            template_id: Template identifier
            version: Template version
            
        Returns:
            Metadata dictionary (empty if not found)
        """
        if template_id not in cls._metadata:
            return {}
        if version not in cls._metadata[template_id]:
            return {}
        
        return cls._metadata[template_id][version].copy()
    
    @classmethod
    def list_versions(cls, template_id: str) -> List[str]:
        """
        List all versions of a template.
        
        Args:
            template_id: Template identifier
            
        Returns:
            List of version strings
            
        Raises:
            TemplateNotFoundError: If template not found
        """
        if template_id not in cls._templates:
            raise TemplateNotFoundError(f"Template '{template_id}' not found")
        
        return list(cls._templates[template_id].keys())
    
    @classmethod
    def get_template_info(cls, template_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a template without instantiating it.
        
        Args:
            template_id: Template identifier
            version: Specific version (if None, returns all versions)
            
        Returns:
            Template information
        """
        if template_id not in cls._metadata:
            raise TemplateNotFoundError(f"Template '{template_id}' not found")
        
        if version:
            if version not in cls._metadata[template_id]:
                raise TemplateVersionError(f"Version '{version}' not found")
            return cls._metadata[template_id][version]
        else:
            return cls._metadata[template_id]
    
    @classmethod
    def clear_cache(cls):
        """Clear the instance cache."""
        cls._instances.clear()
        logger.info("Template instance cache cleared")
    
    @classmethod
    def unregister(cls, template_id: str, version: Optional[str] = None):
        """
        Unregister a template (mainly for testing).
        
        Args:
            template_id: Template identifier
            version: Specific version to remove (if None, removes all)
        """
        if template_id not in cls._templates:
            return
        
        if version:
            cls._templates[template_id].pop(version, None)
            cls._metadata[template_id].pop(version, None)
            # Clean up empty dicts
            if not cls._templates[template_id]:
                del cls._templates[template_id]
                del cls._metadata[template_id]
        else:
            del cls._templates[template_id]
            del cls._metadata[template_id]
        
        # Clear relevant cache entries
        keys_to_remove = [k for k in cls._instances.keys() if k.startswith(f"{template_id}:")]
        for key in keys_to_remove:
            del cls._instances[key]
    
    @classmethod
    def discover_templates(cls, path: Path):
        """
        Discover and register templates from a directory.
        
        Args:
            path: Directory path to search for templates
        """
        # This would be implemented to dynamically load templates
        # from Python files or YAML/JSON definitions
        logger.info(f"Discovering templates in {path}")
        # Implementation would go here
        pass

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/templates/test_registry.py
#    - tests/unit/templates/test_registry_versioning.py
# 
# 2. Integration tests:
#    - tests/integration/templates/test_template_discovery.py
#    - tests/integration/templates/test_registry_caching.py
#
# Complete test coverage details are documented in:
# docs/test_coverage/TEMPLATES_test_coverage.md
# ----------------------------------------------
