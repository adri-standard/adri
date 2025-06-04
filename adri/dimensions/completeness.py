"""
Completeness dimension assessment for the Agent Data Readiness Index.

This module evaluates whether all expected data is present, and most importantly,
whether this information is explicitly communicated to agents.
"""

import logging
from typing import Dict, List, Tuple, Any, Optional

from ..config.config import get_config
from ..connectors import BaseConnector
from . import BaseDimensionAssessor, register_dimension
from .business_completeness import calculate_business_completeness_score
from ..rules.registry import RuleRegistry

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
    
    def _process_template_rules(self, connector: BaseConnector) -> Tuple[float, List[str], List[str]]:
        """
        Process template-specific rules if they are set.
        
        Args:
            connector: Data source connector
            
        Returns:
            Tuple containing:
                - score (0-20)
                - list of findings
                - list of recommendations
        """
        if not self.template_rules:
            return 0, [], []
            
        total_score = 0
        findings = []
        recommendations = []
        
        # Calculate total weight to validate it sums to 20
        total_weight = sum(rule.get('params', {}).get('weight', 0) for rule in self.template_rules)
        
        # Warn if weights don't sum to 20
        if abs(total_weight - 20) > 0.01:  # Allow for floating point precision
            logger.warning(
                f"Completeness dimension rule weights sum to {total_weight}, not 20. "
                f"Scores may not be as expected. Consider adjusting weights to sum to 20."
            )
            findings.append(
                f"⚠️ Rule weights sum to {total_weight} instead of 20. "
                f"Each dimension should have rules totaling 20 points."
            )
        
        # Process each template rule
        for rule_config in self.template_rules:
            rule_type = rule_config.get('type')
            rule_params = rule_config.get('params', {})
            rule_weight = rule_params.get('weight', 0)
            
            # Try to get the rule class from registry
            rule_class = RuleRegistry.get_rule(f"completeness.{rule_type.lower()}")
            if not rule_class:
                # Try without the dimension prefix
                rule_class = RuleRegistry.get_rule(rule_type.lower())
                
            if not rule_class:
                logger.warning(f"Unknown rule type: {rule_type}")
                continue
                
            # Create rule instance with template parameters
            rule = rule_class(rule_params)
            
            # Execute the rule
            try:
                result = rule.evaluate(connector)
                
                # Extract score from rule result
                rule_score = result.get('score', 0)
                
                # The rule_score represents how well the rule passed (0 to rule_weight)
                # Since weights now represent portions of 20, we use the score directly
                # but cap it at the rule's weight
                actual_score = min(rule_score, rule_weight)
                total_score += actual_score
                
                # Generate narrative for findings
                narrative = rule.generate_narrative(result)
                if narrative:
                    findings.append(f"[{rule_type}] {narrative}")
                    
                # Add score information to findings for transparency
                if actual_score < rule_weight:
                    findings.append(
                        f"[{rule_type}] Scored {actual_score:.1f}/{rule_weight} points"
                    )
                    
                # Add specific findings from rule result
                if 'column_results' in result:
                    for col, details in result.get('column_results', {}).items():
                        if details.get('missing_count', 0) > 0:
                            findings.append(f"Column '{col}' has {details['missing_count']} missing values")
                            
                # Add recommendations based on rule results
                if not result.get('valid', True):
                    recommendations.append(f"Address {rule_type} issues to improve data quality")
                    
            except Exception as e:
                logger.error(f"Error executing rule {rule_type}: {e}")
                findings.append(f"Failed to execute rule {rule_type}: {str(e)}")
                
        # Ensure score doesn't exceed 20
        total_score = min(total_score, 20)
        
        return total_score, findings, recommendations
    
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
        
        # Get scoring constants from the latest configuration
        config = get_config()
        scoring = config.get_completeness_scoring()
        
        MAX_OVERALL_COMPLETENESS_SCORE = scoring["MAX_OVERALL_COMPLETENESS_SCORE"]
        MAX_NULL_DISTINCTION_SCORE = scoring["MAX_NULL_DISTINCTION_SCORE"]
        MAX_EXPLICIT_METRICS_SCORE = scoring["MAX_EXPLICIT_METRICS_SCORE"]
        MAX_SECTION_AWARENESS_SCORE = scoring["MAX_SECTION_AWARENESS_SCORE"]
        REQUIRE_EXPLICIT_METADATA = self.config.get("REQUIRE_EXPLICIT_METADATA", scoring["REQUIRE_EXPLICIT_METADATA"])
        
        findings = []
        recommendations = []
        score_components = {}
        
        # If template rules are set, use them instead of standard assessment
        if self.template_rules:
            logger.info("Using template-specific completeness rules")
            return self._process_template_rules(connector)
        
        # Check if we're in discovery mode and have business logic enabled
        business_logic_enabled = self.config.get("business_logic_enabled", False)
        if not REQUIRE_EXPLICIT_METADATA and business_logic_enabled and hasattr(connector, 'df'):
            # Use business-focused completeness scoring
            business_score, business_findings, business_recommendations = calculate_business_completeness_score(
                connector.df, 
                data_type=None  # Auto-detect
            )
            
            # In discovery mode, business completeness takes precedence
            findings.extend(business_findings)
            recommendations.extend(business_recommendations)
            
            # Start with business score as the base
            return business_score, findings, recommendations
        
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
                score_components["null_distinction"] = MAX_NULL_DISTINCTION_SCORE
                findings.append("Missing values are explicitly distinguished from nulls")
            elif not REQUIRE_EXPLICIT_METADATA and "special_null_indicators" in completeness_info:
                # Award partial points for automatic detection of special null indicators
                special_nulls = completeness_info.get("special_null_indicators", {})
                if special_nulls and len(special_nulls) > 0:
                    null_distinction = True
                    null_score = int(MAX_NULL_DISTINCTION_SCORE * 0.7)  # 70% of max
                    score_components["null_distinction"] = null_score
                    findings.append("Special null indicators detected through analysis")
                    findings.append(f"Detected potential null indicators: {list(special_nulls.keys())}")
                else:
                    score_components["null_distinction"] = 0
                    findings.append("No explicit distinction between missing values and nulls")
                    recommendations.append("Implement explicit markers for missing vs. null values")
            else:
                score_components["null_distinction"] = 0
                if REQUIRE_EXPLICIT_METADATA:
                    findings.append("No explicit distinction between missing values and nulls (explicit metadata required)")
                else:
                    findings.append("No explicit or implicit distinction between missing values and nulls")
                recommendations.append("Implement explicit markers for missing vs. null values")
            
            # 4. Evaluate whether completeness metrics are explicitly exposed
            explicit_metrics = False
            if has_explicit_info and "completeness_metrics" in completeness_info:
                explicit_metrics = True
                score_components["explicit_metrics"] = MAX_EXPLICIT_METRICS_SCORE
                findings.append("Explicit completeness metrics are available to agents")
            elif not REQUIRE_EXPLICIT_METADATA:
                # Award partial points for automatically calculated completeness metrics
                metrics_score = int(MAX_EXPLICIT_METRICS_SCORE * 0.6)  # 60% of max
                score_components["explicit_metrics"] = metrics_score
                findings.append("Basic completeness metrics calculated through analysis")
            else:
                score_components["explicit_metrics"] = 0
                findings.append("No explicit completeness metrics available to agents (explicit metadata required)")
                recommendations.append("Provide explicit completeness metrics accessible to agents")
            
            # 5. Evaluate section-level awareness
            section_awareness = False
            if has_explicit_info and "section_completeness" in completeness_info:
                section_awareness = True
                score_components["section_awareness"] = MAX_SECTION_AWARENESS_SCORE
                findings.append("Section-level completeness information is available")
            elif not REQUIRE_EXPLICIT_METADATA and "inferred_sections" in completeness_info:
                # Award partial points for automatically inferred sections
                inferred_sections = completeness_info.get("inferred_sections", {})
                if inferred_sections and len(inferred_sections) > 0:
                    section_awareness = True
                    section_score = int(MAX_SECTION_AWARENESS_SCORE * 0.5)  # 50% of max
                    score_components["section_awareness"] = section_score
                    sections_count = len(inferred_sections)
                    findings.append(f"Detected {sections_count} potential data sections through analysis")
                else:
                    score_components["section_awareness"] = 0
                    findings.append("No section-level completeness information")
                    recommendations.append("Implement section-level completeness tracking")
            else:
                score_components["section_awareness"] = 0
                if REQUIRE_EXPLICIT_METADATA:
                    findings.append("No section-level completeness information (explicit metadata required)")
                else:
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
