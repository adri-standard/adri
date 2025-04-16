"""
Completeness dimension assessment for the Agent Data Readiness Index.

This module evaluates whether all expected data is present, and most importantly,
whether this information is explicitly communicated to agents.
"""

import logging
from typing import Dict, List, Tuple, Any, Optional

from ..connectors import BaseConnector
from . import BaseDimensionAssessor, register_dimension

logger = logging.getLogger(__name__)


@register_dimension(
    name="completeness",
    description="Whether all expected data is present"
)
class CompletenessAssessor(BaseDimensionAssessor):
    """
    Assessor for the Completeness dimension.
    
    Evaluates whether all expected data is present and whether
    this information is explicitly communicated to agents.
    """
    
    def assess(self, connector: BaseConnector) -> Tuple[float, List[str], List[str]]:
        """
        Assess the completeness dimension for a data source.
        
        Args:
            connector: Data source connector
            
        Returns:
            Tuple containing:
                - score (0-20)
                - list of findings
                - list of recommendations
        """
        logger.info(f"Assessing completeness dimension for {connector.get_name()}")
        
        findings = []
        recommendations = []
        score_components = {}
        
        # Get completeness information
        completeness_info = connector.get_completeness_results()
        
        # 1. Check if completeness information is available
        if completeness_info:
            # Calculate the overall completeness percentage
            has_explicit_info = completeness_info.get("has_explicit_completeness_info", False)
            
            overall_completeness = completeness_info.get(
                "overall_completeness_percent", 
                completeness_info.get("actual_overall_completeness_percent", 0)
            )
            
            findings.append(f"Overall completeness: {overall_completeness:.1f}%")
            
            # 2. Evaluate the overall completeness
            if overall_completeness >= 98:
                score_components["overall_completeness"] = 5
                findings.append("Data is nearly 100% complete")
            elif overall_completeness >= 90:
                score_components["overall_completeness"] = 4
                findings.append("Data is highly complete (>90%)")
            elif overall_completeness >= 80:
                score_components["overall_completeness"] = 3
                findings.append("Data is moderately complete (>80%)")
            elif overall_completeness >= 60:
                score_components["overall_completeness"] = 2
                findings.append("Data has significant missing values (<80% complete)")
                recommendations.append("Improve data completeness to at least 90%")
            else:
                score_components["overall_completeness"] = 1
                findings.append("Data has severe completeness issues (<60% complete)")
                recommendations.append("Address critical completeness issues before using with agents")
            
            # 3. Evaluate whether missing values are explicitly marked
            null_distinction = False
            if has_explicit_info and "missing_value_markers" in completeness_info:
                null_distinction = True
                score_components["null_distinction"] = 5
                findings.append("Missing values are explicitly distinguished from nulls")
            else:
                score_components["null_distinction"] = 0
                findings.append("No explicit distinction between missing values and nulls")
                recommendations.append("Implement explicit markers for missing vs. null values")
            
            # 4. Evaluate whether completeness metrics are explicitly exposed
            explicit_metrics = False
            if has_explicit_info and "completeness_metrics" in completeness_info:
                explicit_metrics = True
                score_components["explicit_metrics"] = 5
                findings.append("Explicit completeness metrics are available to agents")
            else:
                score_components["explicit_metrics"] = 0
                findings.append("No explicit completeness metrics available to agents")
                recommendations.append("Provide explicit completeness metrics accessible to agents")
            
            # 5. Evaluate section-level awareness
            section_awareness = False
            if has_explicit_info and "section_completeness" in completeness_info:
                section_awareness = True
                score_components["section_awareness"] = 5
                findings.append("Section-level completeness information is available")
            else:
                score_components["section_awareness"] = 0
                findings.append("No section-level completeness information")
                recommendations.append("Implement section-level completeness tracking")
        else:
            # No completeness information available
            findings.append("No completeness information is available")
            recommendations.append("Implement basic completeness tracking and expose it to agents")
            score_components["overall_completeness"] = 0
            score_components["null_distinction"] = 0
            score_components["explicit_metrics"] = 0
            score_components["section_awareness"] = 0
        
        # Calculate overall score (0-20)
        # Weight: 
        # - overall_completeness: 5 points max
        # - null_distinction: 5 points max
        # - explicit_metrics: 5 points max
        # - section_awareness: 5 points max
        score = sum(score_components.values())
        
        # Ensure we don't exceed the maximum score
        score = min(score, 20)
        
        # Add score component breakdown to findings
        findings.append(f"Score components: {score_components}")
        
        # Add recommendations if score is not perfect
        if score < 20 and score < 10:
            recommendations.append(
                "Implement a comprehensive completeness framework with explicit agent communication"
            )
                
        logger.info(f"Completeness assessment complete. Score: {score}")
        return score, findings, recommendations
