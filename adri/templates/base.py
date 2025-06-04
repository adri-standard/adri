"""
Base template class for ADRI certification templates.

This module provides the abstract base class that all certification
templates must inherit from, ensuring consistent interfaces and behavior.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..report import ADRIScoreReport
from .evaluation import TemplateEvaluation


class BaseTemplate(ABC):
    """
    Base class for all ADRI certification templates.
    
    Templates define specific data quality requirements that can be
    evaluated against ADRI assessment reports. Each template represents
    a set of standards from an authority (regulatory body, industry
    consortium, or organization).
    """
    
    # Template metadata - must be defined by subclasses
    template_id: str = None
    template_version: str = None
    template_name: str = None
    authority: str = None
    description: str = None
    effective_date: Optional[datetime] = None
    jurisdiction: Optional[List[str]] = None
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the template.
        
        Args:
            config: Optional configuration to override default requirements
        """
        self.config = config or {}
        self._validate_metadata()
        
    def _validate_metadata(self):
        """Validate that required metadata is defined."""
        required_fields = ['template_id', 'template_version', 'template_name', 'authority']
        for field in required_fields:
            if not getattr(self, field, None):
                raise ValueError(f"Template must define {field}")
    
    @abstractmethod
    def get_requirements(self) -> Dict[str, Any]:
        """
        Get the requirements defined by this template.
        
        Returns:
            Dict containing:
                - overall_minimum: Minimum overall score required
                - dimension_requirements: Per-dimension requirements
                - custom_rules: Any custom validation rules
                - mandatory_fields: Required data fields
        """
        pass
    
    @abstractmethod
    def evaluate(self, report: ADRIScoreReport) -> TemplateEvaluation:
        """
        Evaluate an assessment report against this template.
        
        Args:
            report: The ADRI assessment report to evaluate
            
        Returns:
            TemplateEvaluation containing compliance results
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get template metadata.
        
        Returns:
            Dictionary containing template metadata
        """
        return {
            'id': self.template_id,
            'version': self.template_version,
            'name': self.template_name,
            'authority': self.authority,
            'description': self.description,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'jurisdiction': self.jurisdiction,
            'requirements_summary': self._get_requirements_summary()
        }
    
    def _get_requirements_summary(self) -> Dict[str, Any]:
        """
        Get a summary of template requirements.
        
        Returns:
            Summary of key requirements
        """
        reqs = self.get_requirements()
        return {
            'overall_minimum_score': reqs.get('overall_minimum'),
            'dimensions_with_requirements': list(reqs.get('dimension_requirements', {}).keys()),
            'has_custom_rules': bool(reqs.get('custom_rules')),
            'has_mandatory_fields': bool(reqs.get('mandatory_fields'))
        }
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """
        Check if this template is applicable in a given context.
        
        Args:
            context: Context information (e.g., industry, location, use case)
            
        Returns:
            True if template is applicable
        """
        # Default implementation - can be overridden
        if self.jurisdiction and context.get('location'):
            return context['location'] in self.jurisdiction
        return True
    
    def get_certification_info(self) -> Dict[str, Any]:
        """
        Get certification information for this template.
        
        Returns:
            Dictionary containing certification details
        """
        return {
            'certifying_authority': self.authority,
            'certification_name': f"{self.template_name} Compliance",
            'certification_id_prefix': getattr(self, 'certification_id_prefix', f"ADRI-{self.template_id.upper()}"),
            'validity_period_days': getattr(self, 'validity_period_days', 365),  # Default, can be overridden
        }

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/templates/test_base_template.py
# 
# 2. Integration tests:
#    - tests/integration/templates/test_template_inheritance.py
#
# 3. Template implementations:
#    - adri/templates/yaml_template.py
#    - adri/templates/catalog/financial/basel.py
#
# Complete test coverage details are documented in:
# docs/test_coverage/TEMPLATES_test_coverage.md
# ----------------------------------------------
