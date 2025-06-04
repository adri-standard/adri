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
from ..report import ADRIScoreReport

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
        
        # Apply config overrides if provided
        if config:
            self._apply_config_overrides(config)
        
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
    
    def _apply_config_overrides(self, config: Dict[str, Any]):
        """Apply configuration overrides to template data."""
        # Deep merge config into template_data
        if 'requirements' in config:
            if 'requirements' not in self.template_data:
                self.template_data['requirements'] = {}
            
            # Merge requirements
            for key, value in config['requirements'].items():
                self.template_data['requirements'][key] = value
    
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
    
    def evaluate(self, report: ADRIScoreReport) -> TemplateEvaluation:
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
        
        # Check custom rules
        custom_rules = requirements.get('custom_rules', [])
        if custom_rules:
            self._evaluate_custom_rules(custom_rules, report, evaluation)
        
        # Add recommendations
        evaluation.recommendations = self._generate_recommendations(evaluation.gaps)
        
        # Finalize evaluation
        evaluation.finalize()
        
        return evaluation
    
    def _evaluate_dimension(
        self, 
        dimension: str, 
        config: Dict[str, Any], 
        report: ADRIScoreReport, 
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
        
        # Check other dimension-specific requirements (e.g., max_missing_percentage)
        if 'max_missing_percentage' in config and dimension == 'completeness':
            self._evaluate_max_missing_percentage(config['max_missing_percentage'], report, evaluation)
    
    def _evaluate_mandatory_fields(
        self, 
        fields: list, 
        report: ADRIScoreReport, 
        evaluation: TemplateEvaluation
    ):
        """Evaluate mandatory field requirements."""
        # Check if dimension findings contain field presence information
        if 'completeness' in report.dimension_findings:
            field_presence = report.dimension_findings.get('completeness', {}).get('field_presence', {})
            
            for field in fields:
                if field in field_presence:
                    if field_presence[field]:
                        evaluation.add_passed_requirement(f"mandatory_field_{field}")
                    else:
                        gap = TemplateGap(
                            requirement_id=f"mandatory_field_{field}",
                            requirement_type='field',
                            requirement_description=f"Mandatory field '{field}' is missing",
                            expected_value=True,
                            actual_value=False,
                            gap_severity='high',
                            remediation_hint=f"Ensure data source includes '{field}' field"
                        )
                        evaluation.add_gap(gap)
                else:
                    # Field not tracked in report, log for now
                    logger.warning(f"Mandatory field '{field}' not found in field presence tracking")
        else:
            logger.info(f"No field presence information available for mandatory fields: {fields}")
    
    def _evaluate_required_rules(
        self, 
        dimension: str, 
        rules: list, 
        report: ADRIScoreReport, 
        evaluation: TemplateEvaluation
    ):
        """Evaluate specific rule requirements."""
        # Check if dimension findings contain rule results
        if dimension in report.dimension_findings:
            dim_findings = report.dimension_findings[dimension]
            
            for rule in rules:
                if rule in dim_findings:
                    if dim_findings[rule]:
                        evaluation.add_passed_requirement(f"{dimension}_rule_{rule}")
                    else:
                        gap = TemplateGap(
                            requirement_id=f"{dimension}_rule_{rule}",
                            requirement_type='rule',
                            requirement_description=f"Required rule '{rule}' failed for {dimension}",
                            expected_value=True,
                            actual_value=False,
                            gap_severity='high',
                            remediation_hint=f"Ensure {dimension} dimension passes '{rule}' rule"
                        )
                        evaluation.add_gap(gap)
                else:
                    logger.warning(f"Required rule '{rule}' not found in {dimension} findings")
        else:
            logger.info(f"No findings available for {dimension} dimension rules: {rules}")
    
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
    
    def _evaluate_max_missing_percentage(
        self,
        max_percentage: float,
        report: ADRIScoreReport,
        evaluation: TemplateEvaluation
    ):
        """Evaluate max missing percentage requirement for completeness."""
        # Check if completeness findings contain missing percentage
        if 'completeness' in report.dimension_findings:
            missing_percentage = report.dimension_findings.get('completeness', {}).get('missing_percentage')
            
            if missing_percentage is not None:
                requirement_id = 'completeness_max_missing_percentage'
                
                if missing_percentage <= max_percentage:
                    evaluation.add_passed_requirement(requirement_id)
                else:
                    gap = TemplateGap(
                        requirement_id=requirement_id,
                        requirement_type='dimension',
                        requirement_description=f"Missing data percentage must not exceed {max_percentage}%",
                        expected_value=max_percentage,
                        actual_value=missing_percentage,
                        gap_severity='high' if missing_percentage - max_percentage > 10 else 'medium',
                        remediation_hint="Reduce missing data in the dataset"
                    )
                    gap.dimension = 'completeness'  # Add dimension attribute
                    evaluation.add_gap(gap)
            else:
                logger.warning("Missing percentage not found in completeness findings")
        else:
            logger.info("No completeness findings available for max missing percentage check")
    
    def _evaluate_custom_rules(
        self,
        custom_rules: list,
        report: ADRIScoreReport,
        evaluation: TemplateEvaluation
    ):
        """Evaluate custom validation rules."""
        for rule in custom_rules:
            rule_id = rule.get('id', 'custom_rule')
            description = rule.get('description', 'Custom rule')
            expression = rule.get('expression', '')
            
            # Create a safe evaluation context with dimension scores
            context = {
                'overall_score': report.overall_score,
                'validity_score': report.dimension_scores.get('validity', 0),
                'completeness_score': report.dimension_scores.get('completeness', 0),
                'freshness_score': report.dimension_scores.get('freshness', 0),
                'consistency_score': report.dimension_scores.get('consistency', 0),
                'plausibility_score': report.dimension_scores.get('plausibility', 0)
            }
            
            try:
                # Evaluate the expression in a safe context
                # In production, this should use a proper expression evaluator
                result = eval(expression, {"__builtins__": {}}, context)
                
                if result:
                    evaluation.add_passed_requirement(rule_id)
                else:
                    gap = TemplateGap(
                        requirement_id=rule_id,
                        requirement_type='custom',
                        requirement_description=description,
                        expected_value=True,
                        actual_value=False,
                        gap_severity='high',
                        remediation_hint=f"Ensure custom rule '{rule_id}' is satisfied"
                    )
                    evaluation.add_gap(gap)
                    
            except Exception as e:
                logger.error(f"Error evaluating custom rule '{rule_id}': {e}")
                # Treat evaluation errors as failures
                gap = TemplateGap(
                    requirement_id=rule_id,
                    requirement_type='custom',
                    requirement_description=f"{description} (evaluation error)",
                    expected_value=True,
                    actual_value=False,
                    gap_severity='high',
                    remediation_hint=f"Fix custom rule expression: {str(e)}"
                )
                evaluation.add_gap(gap)
    
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
