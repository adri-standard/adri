"""
YAML-based template implementation for ADRI.

This module provides a template class that can be configured via YAML files,
allowing industry bodies and organizations to define certification requirements
without writing Python code.
"""

import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
import yaml
from datetime import datetime

from .base import BaseTemplate
from .evaluation import TemplateEvaluation, TemplateGap
from .exceptions import TemplateValidationError
from ..report import AssessmentReport

logger = logging.getLogger(__name__)


class YAMLTemplate(BaseTemplate):
    """
    Template defined via YAML configuration.
    
    This allows templates to be defined declaratively without Python code,
    making it easier for non-developers to create and maintain templates.
    """
    
    def __init__(self, template_source: Union[str, Path, Dict[str, Any]], config: Optional[Dict[str, Any]] = None):
        """
        Initialize YAML template.
        
        Args:
            template_source: Path to YAML file, YAML string, or dict
            config: Optional configuration overrides
        """
        # Load template data
        if isinstance(template_source, dict):
            self.template_data = template_source
        elif isinstance(template_source, (str, Path)):
            self.template_data = self._load_template(template_source)
        else:
            raise ValueError("template_source must be a path, string, or dict")
        
        # Extract metadata
        self._extract_metadata()
        
        # Validate template structure
        self._validate_template()
        
        # Initialize parent
        super().__init__(config)
    
    def _load_template(self, source: Union[str, Path]) -> Dict[str, Any]:
        """Load template from file or string."""
        try:
            # Check if it's a Path object or a file path string
            if isinstance(source, Path):
                # It's a Path object
                if source.exists():
                    with open(source, 'r') as f:
                        return yaml.safe_load(f)
                else:
                    raise TemplateValidationError(f"File not found: {source}")
            elif isinstance(source, str):
                # Try to determine if it's a file path or YAML content
                # If it starts with typical YAML content or contains newlines, treat as YAML
                if '\n' in source or source.strip().startswith(('template:', 'requirements:', '{', '-')):
                    # It's likely YAML content
                    return yaml.safe_load(source)
                else:
                    # It might be a file path
                    path = Path(source)
                    if path.exists():
                        with open(path, 'r') as f:
                            return yaml.safe_load(f)
                    else:
                        # Last resort: try to parse as YAML anyway
                        return yaml.safe_load(source)
            else:
                raise TemplateValidationError(f"Invalid source type: {type(source)}")
        except yaml.YAMLError as e:
            raise TemplateValidationError(f"Invalid YAML: {e}")
        except TemplateValidationError:
            raise
        except Exception as e:
            raise TemplateValidationError(f"Could not load template: {e}")
    
    def _extract_metadata(self):
        """Extract metadata from template data."""
        metadata = self.template_data.get('template', {})
        
        self.template_id = metadata.get('id')
        self.template_version = metadata.get('version')
        self.template_name = metadata.get('name')
        self.authority = metadata.get('authority')
        self.description = metadata.get('description', '')
        
        # Optional metadata
        if metadata.get('effective_date'):
            try:
                self.effective_date = datetime.fromisoformat(metadata['effective_date'])
            except ValueError:
                logger.warning(f"Invalid effective_date format: {metadata['effective_date']}")
        
        self.jurisdiction = metadata.get('jurisdiction', [])
        if isinstance(self.jurisdiction, str):
            self.jurisdiction = [self.jurisdiction]
    
    def _validate_template(self):
        """Validate template structure."""
        required_sections = ['template', 'requirements']
        for section in required_sections:
            if section not in self.template_data:
                raise TemplateValidationError(f"Template missing required section: {section}")
        
        # Validate requirements structure
        reqs = self.template_data['requirements']
        if not isinstance(reqs, dict):
            raise TemplateValidationError("Requirements must be a dictionary")
        
        # Validate dimension requirements if present
        if 'dimension_requirements' in reqs:
            dim_reqs = reqs['dimension_requirements']
            if not isinstance(dim_reqs, dict):
                raise TemplateValidationError("dimension_requirements must be a dictionary")
            
            valid_dimensions = ['validity', 'completeness', 'freshness', 'consistency', 'plausibility']
            for dim in dim_reqs:
                if dim not in valid_dimensions:
                    raise TemplateValidationError(f"Unknown dimension: {dim}")
    
    def get_requirements(self) -> Dict[str, Any]:
        """Get the requirements defined by this template."""
        return self.template_data.get('requirements', {})
    
    def evaluate(self, report: AssessmentReport) -> TemplateEvaluation:
        """
        Evaluate an assessment report against this template.
        
        Args:
            report: The ADRI assessment report to evaluate
            
        Returns:
            TemplateEvaluation containing compliance results
        """
        evaluation = TemplateEvaluation(
            template_id=self.template_id,
            template_version=self.template_version,
            template_name=self.template_name
        )
        
        requirements = self.get_requirements()
        
        # Check overall score requirement
        if 'overall_minimum' in requirements:
            min_score = requirements['overall_minimum']
            actual_score = report.overall_score
            
            if actual_score >= min_score:
                evaluation.add_passed_requirement('overall_score')
            else:
                gap = TemplateGap(
                    requirement_id='overall_score',
                    requirement_type='overall',
                    requirement_description=f"Overall score must be at least {min_score}",
                    expected_value=min_score,
                    actual_value=actual_score,
                    gap_severity='blocking' if min_score - actual_score > 20 else 'high',
                    remediation_hint="Improve data quality across all dimensions"
                )
                evaluation.add_gap(gap)
        
        # Check dimension requirements
        dim_reqs = requirements.get('dimension_requirements', {})
        for dimension, dim_config in dim_reqs.items():
            self._evaluate_dimension(dimension, dim_config, report, evaluation)
        
        # Check mandatory fields
        mandatory_fields = requirements.get('mandatory_fields', [])
        if mandatory_fields:
            self._evaluate_mandatory_fields(mandatory_fields, report, evaluation)
        
        # Add recommendations
        evaluation.recommendations = self._generate_recommendations(evaluation.gaps)
        
        # Finalize evaluation
        evaluation.finalize()
        
        return evaluation
    
    def _evaluate_dimension(
        self, 
        dimension: str, 
        config: Dict[str, Any], 
        report: AssessmentReport, 
        evaluation: TemplateEvaluation
    ):
        """Evaluate a specific dimension requirement."""
        if dimension not in report.dimension_results:
            logger.warning(f"Dimension {dimension} not found in report")
            return
        
        actual_score = report.dimension_results[dimension]['score']
        
        # Check minimum score
        if 'minimum_score' in config:
            min_score = config['minimum_score']
            requirement_id = f"{dimension}_minimum_score"
            
            if actual_score >= min_score:
                evaluation.add_passed_requirement(requirement_id)
            else:
                gap = TemplateGap(
                    requirement_id=requirement_id,
                    requirement_type='dimension',
                    requirement_description=f"{dimension.title()} score must be at least {min_score}",
                    expected_value=min_score,
                    actual_value=actual_score,
                    gap_severity=self._calculate_severity(min_score - actual_score),
                    remediation_hint=f"Focus on improving {dimension} dimension"
                )
                evaluation.add_gap(gap)
        
        # Check specific rules
        if 'required_rules' in config:
            self._evaluate_required_rules(dimension, config['required_rules'], report, evaluation)
    
    def _evaluate_mandatory_fields(
        self, 
        fields: list, 
        report: AssessmentReport, 
        evaluation: TemplateEvaluation
    ):
        """Evaluate mandatory field requirements."""
        # This would check if the data source has the required fields
        # For now, we'll add a placeholder implementation
        logger.info(f"Checking mandatory fields: {fields}")
        # In a real implementation, this would inspect the data source metadata
    
    def _evaluate_required_rules(
        self, 
        dimension: str, 
        rules: list, 
        report: AssessmentReport, 
        evaluation: TemplateEvaluation
    ):
        """Evaluate specific rule requirements."""
        # This would check if specific rules passed
        # For now, we'll add a placeholder
        logger.info(f"Checking required rules for {dimension}: {rules}")
    
    def _calculate_severity(self, gap_size: float) -> str:
        """Calculate gap severity based on size."""
        if gap_size > 10:
            return 'blocking'
        elif gap_size > 5:
            return 'high'
        elif gap_size > 2:
            return 'medium'
        else:
            return 'low'
    
    def _generate_recommendations(self, gaps: list) -> list:
        """Generate recommendations based on gaps."""
        recommendations = []
        
        # Group gaps by dimension
        dimension_gaps = {}
        for gap in gaps:
            if gap.requirement_type == 'dimension':
                dim = gap.requirement_id.split('_')[0]
                if dim not in dimension_gaps:
                    dimension_gaps[dim] = []
                dimension_gaps[dim].append(gap)
        
        # Generate dimension-specific recommendations
        for dim, dim_gaps in dimension_gaps.items():
            if len(dim_gaps) > 0:
                recommendations.append(
                    f"Improve {dim} dimension: Address {len(dim_gaps)} gaps"
                )
        
        # Add general recommendations
        if len(gaps) > 5:
            recommendations.append(
                "Consider a comprehensive data quality improvement initiative"
            )
        
        return recommendations
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path], config: Optional[Dict[str, Any]] = None) -> 'YAMLTemplate':
        """
        Create a YAMLTemplate from a file.
        
        Args:
            file_path: Path to YAML file
            config: Optional configuration overrides
            
        Returns:
            YAMLTemplate instance
        """
        return cls(file_path, config)
    
    @classmethod
    def from_string(cls, yaml_string: str, config: Optional[Dict[str, Any]] = None) -> 'YAMLTemplate':
        """
        Create a YAMLTemplate from a YAML string.
        
        Args:
            yaml_string: YAML content as string
            config: Optional configuration overrides
            
        Returns:
            YAMLTemplate instance
        """
        return cls(yaml_string, config)

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/templates/test_yaml_template.py
#    - tests/unit/templates/test_yaml_validation.py
# 
# 2. Integration tests:
#    - tests/integration/templates/test_yaml_evaluation.py
#    - tests/integration/templates/test_yaml_loading.py
#
# Complete test coverage details are documented in:
# docs/test_coverage/TEMPLATES_test_coverage.md
# ----------------------------------------------
