"""
Consistency dimension assessment for the Agent Data Readiness Index.

This module evaluates whether data elements maintain logical relationships,
and most importantly, whether this information is explicitly communicated to agents.
"""

import logging
from typing import Dict, List, Tuple, Any, Optional

from ..connectors import BaseConnector
from . import BaseDimensionAssessor, register_dimension

logger = logging.getLogger(__name__)


@register_dimension(
    name="consistency",
    description="Whether data elements maintain logical relationships"
)
class ConsistencyAssessor(BaseDimensionAssessor):
    """
    Assessor for the Consistency dimension.
    
    Evaluates whether data elements maintain logical relationships and whether
    this information is explicitly communicated to agents.
    """
    
    def assess(self, connector: BaseConnector) -> Tuple[float, List[str], List[str]]:
        """
        Assess the consistency dimension for a data source.
        
        Args:
            connector: Data source connector
            
        Returns:
            Tuple containing:
                - score (0-20)
                - list of findings
                - list of recommendations
        """
        logger.info(f"Assessing consistency dimension for {connector.get_name()}")
        
        findings = []
        recommendations = []
        score_components = {}
        
        # Get consistency information
        consistency_info = connector.get_consistency_results()
        
        if consistency_info:
            # 1. Check if consistency rules are defined
            rule_results = consistency_info.get("rule_results", [])
            num_rules = len(rule_results)
            
            if num_rules > 0:
                findings.append(f"Consistency rules defined: {num_rules}")
                
                # Score based on number of rules
                if num_rules >= 10:
                    score_components["rules_defined"] = 4
                elif num_rules >= 5:
                    score_components["rules_defined"] = 3
                elif num_rules >= 2:
                    score_components["rules_defined"] = 2
                else:
                    score_components["rules_defined"] = 1
                    recommendations.append("Define more consistency rules")
                
                # 2. Check rule types
                relationship_rules = [r for r in rule_results if r.get("type") == "relationship"]
                if relationship_rules:
                    findings.append(f"Relationship-based consistency rules: {len(relationship_rules)}")
                    score_components["rule_types"] = 3
                else:
                    findings.append("No relationship-based consistency rules defined")
                    score_components["rule_types"] = 0
                    recommendations.append("Implement relationship-based consistency rules (e.g., field1 < field2)")
                
                # 3. Check if rules pass
                valid_overall = consistency_info.get("valid_overall", False)
                invalid_rules = [r for r in rule_results if not r.get("valid", True)]
                
                if valid_overall:
                    findings.append("All consistency rules pass")
                    score_components["rule_validity"] = 4
                else:
                    findings.append(f"{len(invalid_rules)} of {num_rules} consistency rules fail")
                    if len(invalid_rules) / num_rules < 0.2:
                        score_components["rule_validity"] = 3
                    elif len(invalid_rules) / num_rules < 0.5:
                        score_components["rule_validity"] = 2
                    else:
                        score_components["rule_validity"] = 1
                    recommendations.append("Address consistency rule violations")
                
                # 4. Check for cross-dataset consistency
                cross_dataset_rules = [
                    r for r in rule_results 
                    if "cross_dataset" in r or "cross_source" in r or r.get("type") == "cross_dataset"
                ]
                
                if cross_dataset_rules:
                    findings.append(f"Cross-dataset consistency rules: {len(cross_dataset_rules)}")
                    score_components["cross_dataset"] = 3
                else:
                    findings.append("No cross-dataset consistency rules defined")
                    score_components["cross_dataset"] = 0
                    recommendations.append("Implement cross-dataset consistency checks")
                
                # 5. Evaluate whether consistency results are communicated to agents
                if "communication_format" in consistency_info or consistency_info.get("explicitly_communicated"):
                    findings.append("Consistency results are explicitly communicated to agents")
                    score_components["explicit_communication"] = 6
                else:
                    findings.append("Consistency results are not explicitly communicated to agents")
                    score_components["explicit_communication"] = 0
                    recommendations.append("Make consistency results explicitly available to agents")
            else:
                findings.append("No consistency rules defined")
                recommendations.append("Define and implement basic consistency rules")
                score_components["rules_defined"] = 0
                score_components["rule_types"] = 0
                score_components["rule_validity"] = 0
                score_components["cross_dataset"] = 0
                score_components["explicit_communication"] = 0
        else:
            # No consistency information available
            findings.append("No consistency information is available")
            recommendations.append("Implement basic consistency checking and expose it to agents")
            score_components["rules_defined"] = 0
            score_components["rule_types"] = 0
            score_components["rule_validity"] = 0
            score_components["cross_dataset"] = 0
            score_components["explicit_communication"] = 0
        
        # Calculate overall score (0-20)
        # Weight: 
        # - rules_defined: 4 points max
        # - rule_types: 3 points max
        # - rule_validity: 4 points max
        # - cross_dataset: 3 points max
        # - explicit_communication: 6 points max
        score = sum(score_components.values())
        
        # Ensure we don't exceed the maximum score
        score = min(score, 20)
        
        # Add score component breakdown to findings
        findings.append(f"Score components: {score_components}")
        
        # Add recommendations if score is not perfect
        if score < 20 and score < 10:
            recommendations.append(
                "Implement a comprehensive consistency framework with explicit agent communication"
            )
                
        logger.info(f"Consistency assessment complete. Score: {score}")
        return score, findings, recommendations
