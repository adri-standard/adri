"""
Validity dimension assessment for the Agent Data Readiness Index.

This module evaluates whether data adheres to required types, formats, and ranges,
and most importantly, whether this information is explicitly communicated to agents.
"""

import logging
from typing import Dict, List, Tuple, Any, Optional

from ..connectors import BaseConnector
from . import BaseDimensionAssessor, register_dimension

logger = logging.getLogger(__name__)


@register_dimension(
    name="validity",
    description="Whether data adheres to required types, formats, and ranges"
)
class ValidityAssessor(BaseDimensionAssessor):
    """
    Assessor for the Validity dimension.
    
    Evaluates whether data adheres to required types, formats, and ranges,
    and whether this information is explicitly communicated to agents.
    """
    
    def assess(self, connector: BaseConnector) -> Tuple[float, List[str], List[str]]:
        """
        Assess the validity dimension for a data source.
        
        Args:
            connector: Data source connector
            
        Returns:
            Tuple containing:
                - score (0-20)
                - list of findings
                - list of recommendations
        """
        logger.info(f"Assessing validity dimension for {connector.get_name()}")
        
        findings = []
        recommendations = []
        score_components = {}
        
        # Get schema information
        schema = connector.get_schema()
        
        # 1. Evaluate whether data types are explicitly defined
        field_types_defined = "fields" in schema and all("type" in f for f in schema.get("fields", []))
        score_components["types_defined"] = 5 if field_types_defined else 0
        
        if field_types_defined:
            findings.append("Data types are explicitly defined for all fields")
        else:
            findings.append("Data types are not explicitly defined for all fields")
            recommendations.append("Define explicit data types for all fields")
        
        # 2. Evaluate whether data formats are defined (e.g., date formats, patterns)
        formats_defined = False
        format_fields = []
        
        for field in schema.get("fields", []):
            if "format" in field or "pattern" in field:
                format_fields.append(field["name"])
                
        formats_defined = len(format_fields) > 0
        score_components["formats_defined"] = 3 if formats_defined else 0
        
        if formats_defined:
            findings.append(f"Data formats are defined for {len(format_fields)} fields")
        else:
            findings.append("No explicit format definitions found")
            recommendations.append("Define formats (e.g., date patterns, string patterns) for applicable fields")
        
        # 3. Evaluate whether valid ranges are defined
        ranges_defined = False
        range_fields = []
        
        for field in schema.get("fields", []):
            if "min_value" in field or "max_value" in field or "allowed_values" in field:
                range_fields.append(field["name"])
                
        ranges_defined = len(range_fields) > 0
        score_components["ranges_defined"] = 3 if ranges_defined else 0
        
        if ranges_defined:
            findings.append(f"Valid ranges are defined for {len(range_fields)} fields")
        else:
            findings.append("No explicit range definitions found")
            recommendations.append("Define valid ranges (min/max values, allowed values) for applicable fields")
        
        # 4. Evaluate whether validation is performed
        validation_supported = connector.supports_validation()
        validation_results = connector.get_validation_results() if validation_supported else None
        validation_performed = validation_results is not None
        score_components["validation_performed"] = 3 if validation_performed else 0
        
        if validation_performed:
            findings.append("Validation is performed on this data source")
            
            # Check if validation results indicate any issues
            if not validation_results.get("valid_overall", True):
                invalid_rules = [
                    r for r in validation_results.get("rule_results", [])
                    if not r.get("valid", True)
                ]
                findings.append(f"Found {len(invalid_rules)} validation rule violations")
        else:
            findings.append("No evidence of validation being performed")
            recommendations.append("Implement validation rules for this data source")
        
        # 5. Most importantly, evaluate whether validation results are communicated to agents
        validation_communicated = (
            validation_performed and 
            isinstance(validation_results, dict) and
            len(validation_results) > 0
        )
        score_components["validation_communicated"] = 6 if validation_communicated else 0
        
        if validation_communicated:
            findings.append("Validation results are explicitly communicated in machine-readable format")
        else:
            findings.append("Validation results are not explicitly communicated to agents")
            recommendations.append(
                "Ensure validation results are explicitly communicated to agents in a machine-readable format"
            )
        
        # Calculate overall score (0-20)
        score = sum(score_components.values())
        
        # Ensure we don't exceed the maximum score
        score = min(score, 20)
        
        # Add score component breakdown to findings
        findings.append(f"Score components: {score_components}")
        
        # Add recommendations if score is not perfect
        if score < 20:
            if score < 10:
                recommendations.append(
                    "Implement a comprehensive validity framework with explicit agent communication"
                )
                
        logger.info(f"Validity assessment complete. Score: {score}")
        return score, findings, recommendations
