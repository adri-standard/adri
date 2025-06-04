"""
Template guard for validating templates before use.

This module provides validation and safety checks for templates
to ensure they won't cause the system to hang or fail unexpectedly.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple, List
import yaml

from .base import BaseTemplate
from .exceptions import (
    TemplateValidationError,
    TemplateNotFoundError,
    TemplateError
)

logger = logging.getLogger(__name__)


class TemplateGuard:
    """
    Guard class that validates templates before they're used in assessments.
    
    Provides:
    - Pre-flight validation checks
    - Structural validation
    - Rule validation
    - Fallback mechanisms
    """
    
    # Required template sections
    REQUIRED_SECTIONS = ['template', 'requirements', 'dimensions']
    
    # Required template metadata fields
    REQUIRED_METADATA = ['id', 'version', 'name']
    
    # Valid dimension names
    VALID_DIMENSIONS = ['validity', 'completeness', 'consistency', 'freshness', 'plausibility']
    
    # Expected points per dimension
    EXPECTED_DIMENSION_POINTS = 20
    
    @classmethod
    def validate_template_source(cls, source: Union[str, Path]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a template source exists and is accessible.
        
        Args:
            source: Template file path or identifier
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Handle URL sources
            if isinstance(source, str) and source.startswith(('http://', 'https://')):
                # URLs are handled by the loader with proper error handling
                return True, None
            
            # Handle file paths
            source_path = Path(source)
            if not source_path.exists():
                return False, f"Template file not found: {source}"
            
            if not source_path.is_file():
                return False, f"Template source is not a file: {source}"
            
            if source_path.suffix not in ['.yaml', '.yml']:
                return False, f"Template must be a YAML file: {source}"
            
            # Check file is readable
            try:
                with open(source_path, 'r') as f:
                    f.read(1)
            except Exception as e:
                return False, f"Cannot read template file: {e}"
            
            return True, None
            
        except Exception as e:
            return False, f"Error validating template source: {e}"
    
    @classmethod
    def validate_template_content(cls, content: Union[str, Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Validate template content structure and rules.
        
        Args:
            content: Template content (YAML string or parsed dict)
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Parse if string
            if isinstance(content, str):
                try:
                    template_data = yaml.safe_load(content)
                except yaml.YAMLError as e:
                    errors.append(f"Invalid YAML: {e}")
                    return False, errors
            else:
                template_data = content
            
            # Check required sections
            for section in cls.REQUIRED_SECTIONS:
                if section not in template_data:
                    errors.append(f"Missing required section: '{section}'")
            
            # If basic structure is missing, return early
            if errors:
                return False, errors
            
            # Validate template metadata
            template_section = template_data.get('template', {})
            for field in cls.REQUIRED_METADATA:
                if field not in template_section:
                    errors.append(f"Missing required template field: '{field}'")
            
            # Validate requirements
            requirements = template_data.get('requirements', {})
            if 'overall_minimum' not in requirements:
                errors.append("Missing 'overall_minimum' in requirements")
            elif not isinstance(requirements['overall_minimum'], (int, float)):
                errors.append("'overall_minimum' must be a number")
            elif not 0 <= requirements['overall_minimum'] <= 100:
                errors.append("'overall_minimum' must be between 0 and 100")
            
            # Validate dimension minimums if present
            if 'dimension_minimums' in requirements:
                dim_mins = requirements['dimension_minimums']
                if not isinstance(dim_mins, dict):
                    errors.append("'dimension_minimums' must be a dictionary")
                else:
                    for dim, value in dim_mins.items():
                        if dim not in cls.VALID_DIMENSIONS:
                            errors.append(f"Invalid dimension in minimums: '{dim}'")
                        if not isinstance(value, (int, float)) or not 0 <= value <= 20:
                            errors.append(f"Dimension minimum for '{dim}' must be 0-20")
            
            # Validate dimensions
            dimensions = template_data.get('dimensions', {})
            if not dimensions:
                errors.append("Template must define at least one dimension")
            
            for dim_name, dim_config in dimensions.items():
                if dim_name not in cls.VALID_DIMENSIONS:
                    errors.append(f"Invalid dimension name: '{dim_name}'")
                    continue
                
                # Check dimension structure
                if not isinstance(dim_config, dict):
                    errors.append(f"Dimension '{dim_name}' must be a dictionary")
                    continue
                
                # Validate rules
                rules = dim_config.get('rules', [])
                if not rules:
                    errors.append(f"Dimension '{dim_name}' has no rules defined")
                    continue
                
                # Check total points
                total_weight = 0
                for i, rule in enumerate(rules):
                    if not isinstance(rule, dict):
                        errors.append(f"Rule {i} in dimension '{dim_name}' must be a dictionary")
                        continue
                    
                    if 'type' not in rule:
                        errors.append(f"Rule {i} in dimension '{dim_name}' missing 'type'")
                    
                    if 'params' not in rule:
                        errors.append(f"Rule {i} in dimension '{dim_name}' missing 'params'")
                    elif 'weight' in rule.get('params', {}):
                        weight = rule['params']['weight']
                        if isinstance(weight, (int, float)):
                            total_weight += weight
                        else:
                            errors.append(f"Rule weight in '{dim_name}' must be numeric")
                
                # Validate total weight
                if total_weight != cls.EXPECTED_DIMENSION_POINTS:
                    errors.append(
                        f"Dimension '{dim_name}' rules total {total_weight} points, "
                        f"expected {cls.EXPECTED_DIMENSION_POINTS}"
                    )
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Unexpected error during validation: {e}")
            return False, errors
    
    @classmethod
    def get_fallback_template(cls) -> Dict[str, Any]:
        """
        Get a minimal fallback template for emergency use.
        
        This template provides basic assessment capabilities when
        the requested template cannot be loaded.
        
        Returns:
            Dictionary containing fallback template data
        """
        return {
            'template': {
                'id': 'fallback/emergency',
                'version': '1.0.0',
                'name': 'Emergency Fallback Template',
                'description': 'Minimal template used when requested template fails to load',
                'authority': 'ADRI Framework'
            },
            'requirements': {
                'overall_minimum': 50,
                'dimension_minimums': {
                    'validity': 10,
                    'completeness': 10,
                    'consistency': 10,
                    'freshness': 10,
                    'plausibility': 10
                }
            },
            'dimensions': {
                'validity': {
                    'weight': 1.0,
                    'rules': [
                        {
                            'type': 'type_consistency',
                            'params': {
                                'enabled': True,
                                'weight': 20,
                                'threshold': 0.80,
                                'analyze_all_columns': True
                            }
                        }
                    ]
                },
                'completeness': {
                    'weight': 1.0,
                    'rules': [
                        {
                            'type': 'required_fields',
                            'params': {
                                'enabled': True,
                                'weight': 20,
                                'threshold': 0.70
                            }
                        }
                    ]
                },
                'consistency': {
                    'weight': 1.0,
                    'rules': [
                        {
                            'type': 'cross_field',
                            'params': {
                                'enabled': True,
                                'weight': 20,
                                'validation_type': 'auto_detect'
                            }
                        }
                    ]
                },
                'freshness': {
                    'weight': 1.0,
                    'rules': [
                        {
                            'type': 'timestamp_recency',
                            'params': {
                                'enabled': True,
                                'weight': 20,
                                'max_age_days': 365,
                                'auto_detect_timestamp': True
                            }
                        }
                    ]
                },
                'plausibility': {
                    'weight': 1.0,
                    'rules': [
                        {
                            'type': 'range',
                            'params': {
                                'enabled': True,
                                'weight': 20,
                                'auto_detect_ranges': True
                            }
                        }
                    ]
                }
            },
            'certification': {
                'enabled': False
            }
        }
    
    @classmethod
    def validate_and_fix_template(cls, template_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Validate template and attempt to fix common issues.
        
        Args:
            template_data: Template data dictionary
            
        Returns:
            Tuple of (fixed_template_data, warnings)
        """
        warnings = []
        fixed_data = template_data.copy()
        
        # Fix missing weight in dimensions
        dimensions = fixed_data.get('dimensions', {})
        for dim_name, dim_config in dimensions.items():
            if 'weight' not in dim_config:
                dim_config['weight'] = 1.0
                warnings.append(f"Added default weight to dimension '{dim_name}'")
        
        # Fix missing enabled in rules
        for dim_name, dim_config in dimensions.items():
            rules = dim_config.get('rules', [])
            for i, rule in enumerate(rules):
                if 'params' in rule and 'enabled' not in rule['params']:
                    rule['params']['enabled'] = True
                    warnings.append(f"Added default 'enabled=True' to rule {i} in '{dim_name}'")
        
        # Add missing overall_minimum if dimension_minimums exist
        requirements = fixed_data.get('requirements', {})
        if 'dimension_minimums' in requirements and 'overall_minimum' not in requirements:
            # Calculate from dimension minimums
            total = sum(requirements['dimension_minimums'].values())
            requirements['overall_minimum'] = total
            warnings.append(f"Calculated overall_minimum={total} from dimension minimums")
        
        return fixed_data, warnings
    
    @classmethod
    def create_safe_template_loader(cls, assessor_instance):
        """
        Create a wrapper around template loading with safety checks.
        
        Args:
            assessor_instance: The DataSourceAssessor instance
            
        Returns:
            A safe template loading function
        """
        def safe_load_template(source, config=None):
            """Safely load a template with validation and fallback."""
            logger.info(f"TemplateGuard: Validating template source: {source}")
            
            # Pre-flight validation
            is_valid, error = cls.validate_template_source(source)
            if not is_valid:
                logger.warning(f"Template source validation failed: {error}")
                logger.info("Using fallback template")
                # Return fallback template wrapped in YAMLTemplate
                from .yaml_template import YAMLTemplate
                fallback_data = cls.get_fallback_template()
                return YAMLTemplate(fallback_data, config)
            
            # Try to load the template
            try:
                from .loader import TemplateLoader
                loader = TemplateLoader()
                template = loader.load_template(source, config)
                
                # Validate loaded template
                if hasattr(template, 'template_data'):
                    is_valid, errors = cls.validate_template_content(template.template_data)
                    if not is_valid:
                        logger.warning(f"Template validation errors: {errors}")
                        # Try to fix common issues
                        fixed_data, warnings = cls.validate_and_fix_template(template.template_data)
                        if warnings:
                            logger.info(f"Applied template fixes: {warnings}")
                        
                        # Re-validate
                        is_valid, errors = cls.validate_template_content(fixed_data)
                        if is_valid:
                            template.template_data = fixed_data
                        else:
                            raise TemplateValidationError(f"Template validation failed: {errors}")
                
                return template
                
            except Exception as e:
                logger.error(f"Failed to load template: {e}")
                logger.info("Using fallback template")
                from .yaml_template import YAMLTemplate
                fallback_data = cls.get_fallback_template()
                return YAMLTemplate(fallback_data, config)
        
        return safe_load_template
