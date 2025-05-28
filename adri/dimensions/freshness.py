"""
Freshness dimension assessment for the Agent Data Readiness Index.

This module evaluates whether data is current enough for the decision,
and most importantly, whether this information is explicitly communicated to agents.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional

from ..config.config import get_config
from ..connectors import BaseConnector
from . import BaseDimensionAssessor, register_dimension
from .business_freshness import calculate_business_freshness_score

logger = logging.getLogger(__name__)


@register_dimension(
    name="freshness",
    description="Whether data is current enough for the decision"
)
class FreshnessAssessor(BaseDimensionAssessor):
    """
    Assessor for the Freshness dimension.
    
    Evaluates whether data is current enough for the decision and whether
    this information is explicitly communicated to agents.
    """
    
    def assess(self, connector: BaseConnector) -> Tuple[float, List[str], List[str]]:
        """
        Assess the freshness dimension for a data source.
        
        Args:
            connector: Data source connector
            
        Returns:
            Tuple containing:
                - score (0-20)
                - list of findings
                - list of recommendations
        """
        logger.info(f"Assessing freshness dimension for {connector.get_name()}")
        
        # Get scoring constants from the latest configuration
        config = get_config()
        scoring = config.get_freshness_scoring()
        
        MAX_HAS_TIMESTAMP_SCORE = scoring["MAX_HAS_TIMESTAMP_SCORE"]
        MAX_DATA_AGE_SCORE = scoring["MAX_DATA_AGE_SCORE"]
        MAX_HAS_SLA_SCORE = scoring["MAX_HAS_SLA_SCORE"]
        MAX_MEETS_SLA_SCORE = scoring["MAX_MEETS_SLA_SCORE"]
        MAX_EXPLICIT_COMMUNICATION_SCORE = scoring["MAX_EXPLICIT_COMMUNICATION_SCORE"]
        REQUIRE_EXPLICIT_METADATA = self.config.get("REQUIRE_EXPLICIT_METADATA", scoring["REQUIRE_EXPLICIT_METADATA"])
        
        findings = []
        recommendations = []
        score_components = {}
        
        # Check if we're in discovery mode and have business logic enabled
        business_logic_enabled = self.config.get("business_logic_enabled", False)
        if not REQUIRE_EXPLICIT_METADATA and business_logic_enabled and hasattr(connector, 'df'):
            # Use business-focused freshness scoring
            business_score, business_findings, business_recommendations = calculate_business_freshness_score(
                connector.df, 
                data_type=None  # Auto-detect
            )
            
            # In discovery mode, business freshness takes precedence
            findings.extend(business_findings)
            recommendations.extend(business_recommendations)
            
            # Start with business score as the base
            return business_score, findings, recommendations
        
        # Get freshness information
        freshness_info = connector.get_freshness_results()
        
        if freshness_info:
            has_explicit_info = freshness_info.get("has_explicit_freshness_info", False)
            
            # 1. Check if timestamp information is available
            has_timestamp = False
            age_hours = None
            
            if has_explicit_info and "file_modified_time" in freshness_info:
                has_timestamp = True
                modified_time = freshness_info["file_modified_time"]
                
                findings.append(f"Last update timestamp: {modified_time}")
                score_components["has_timestamp"] = MAX_HAS_TIMESTAMP_SCORE
                
                # Calculate age from explicit metadata
                age_hours = freshness_info.get("file_age_hours")
                if age_hours is not None:
                    findings.append(f"Data age: {age_hours:.1f} hours")
                    
                    # Assess the age
                    if age_hours <= 1:
                        findings.append("Data is very fresh (updated within the last hour)")
                        score_components["data_age"] = MAX_DATA_AGE_SCORE
                    elif age_hours <= 24:
                        findings.append("Data is reasonably fresh (updated within 24 hours)")
                        score_components["data_age"] = int(MAX_DATA_AGE_SCORE * 0.67)  # ~2/3 of max
                    elif age_hours <= 72:
                        findings.append("Data is somewhat stale (updated within 3 days)")
                        score_components["data_age"] = int(MAX_DATA_AGE_SCORE * 0.33)  # ~1/3 of max
                        recommendations.append("Update data more frequently")
                    else:
                        findings.append("Data is stale (not updated in over 3 days)")
                        score_components["data_age"] = 0
                        recommendations.append("Implement more frequent data updates")
                else:
                    score_components["data_age"] = 0
                    findings.append("Age of data could not be determined")
                    recommendations.append("Ensure data age information is available")
            elif not REQUIRE_EXPLICIT_METADATA and "actual_file_modified_time" in freshness_info:
                # Award partial points for automatically detected timestamps
                has_timestamp = True
                modified_time = freshness_info["actual_file_modified_time"]
                
                # Partial points (70% of max) for implicit timestamp detection
                timestamp_score = int(MAX_HAS_TIMESTAMP_SCORE * 0.7)  # 70% of max
                score_components["has_timestamp"] = timestamp_score
                findings.append(f"Last update timestamp detected: {modified_time} (from file system metadata)")
                
                # Calculate age from implicit metadata
                age_hours = freshness_info.get("actual_file_age_hours")
                if age_hours is not None:
                    findings.append(f"Data age: {age_hours:.1f} hours")
                    
                    # Assess the age
                    if age_hours <= 1:
                        findings.append("Data is very fresh (updated within the last hour)")
                        score_components["data_age"] = MAX_DATA_AGE_SCORE
                    elif age_hours <= 24:
                        findings.append("Data is reasonably fresh (updated within 24 hours)")
                        score_components["data_age"] = int(MAX_DATA_AGE_SCORE * 0.67)  # ~2/3 of max
                    elif age_hours <= 72:
                        findings.append("Data is somewhat stale (updated within 3 days)")
                        score_components["data_age"] = int(MAX_DATA_AGE_SCORE * 0.33)  # ~1/3 of max
                        recommendations.append("Update data more frequently")
                    else:
                        findings.append("Data is stale (not updated in over 3 days)")
                        score_components["data_age"] = 0
                        recommendations.append("Implement more frequent data updates")
                else:
                    score_components["data_age"] = 0
                    findings.append("Age of data could not be determined")
                    recommendations.append("Ensure data age information is available")
            else:
                score_components["has_timestamp"] = 0
                score_components["data_age"] = 0
                if REQUIRE_EXPLICIT_METADATA:
                    findings.append("No timestamp information available (explicit metadata required)")
                else:
                    findings.append("No timestamp information available")
                recommendations.append("Add timestamp information to data")
            
            # 2. Check if freshness SLAs are defined
            has_sla = False
            meets_sla = None
            
            if has_explicit_info and "max_age_hours" in freshness_info:
                has_sla = True
                max_age = freshness_info["max_age_hours"]
                findings.append(f"Freshness SLA defined: maximum age {max_age} hours")
                score_components["has_sla"] = MAX_HAS_SLA_SCORE
                
                # Check if meeting SLA
                if "is_fresh" in freshness_info:
                    meets_sla = freshness_info["is_fresh"]
                    if meets_sla:
                        findings.append("Data meets defined freshness SLA")
                        score_components["meets_sla"] = MAX_MEETS_SLA_SCORE
                    else:
                        findings.append("Data does not meet defined freshness SLA")
                        recommendations.append("Update data to meet defined freshness SLA")
                        score_components["meets_sla"] = 1
                elif age_hours is not None:
                    meets_sla = age_hours <= max_age
                    if meets_sla:
                        findings.append(f"Data meets implied freshness SLA (age: {age_hours:.1f} hours, max: {max_age} hours)")
                        score_components["meets_sla"] = MAX_MEETS_SLA_SCORE
                    else:
                        findings.append(f"Data does not meet implied freshness SLA (age: {age_hours:.1f} hours, max: {max_age} hours)")
                        recommendations.append("Update data to meet freshness SLA")
                        score_components["meets_sla"] = 1
                else:
                    score_components["meets_sla"] = 0
                    findings.append("Cannot determine if data meets freshness SLA")
                    recommendations.append("Implement explicit freshness checking mechanism")
            elif not REQUIRE_EXPLICIT_METADATA and "inferred_max_age_hours" in freshness_info:
                # Award partial points for automatically inferred SLAs
                has_sla = True
                max_age = freshness_info["inferred_max_age_hours"]
                
                # Partial points (50% of max) for implicit SLA detection
                sla_score = int(MAX_HAS_SLA_SCORE * 0.5)  # 50% of max
                score_components["has_sla"] = sla_score
                findings.append(f"Freshness SLA inferred: estimated maximum age {max_age} hours (partial credit)")
                
                # Check if meeting inferred SLA
                if age_hours is not None:
                    meets_sla = age_hours <= max_age
                    if meets_sla:
                        findings.append(f"Data meets inferred freshness SLA (age: {age_hours:.1f} hours, max: {max_age} hours)")
                        meets_sla_score = int(MAX_MEETS_SLA_SCORE * 0.7)  # 70% of max
                        score_components["meets_sla"] = meets_sla_score
                    else:
                        findings.append(f"Data does not meet inferred freshness SLA (age: {age_hours:.1f} hours, max: {max_age} hours)")
                        recommendations.append("Update data more frequently to meet freshness needs")
                        score_components["meets_sla"] = 1
                else:
                    score_components["meets_sla"] = 0
                    findings.append("Cannot determine if data meets inferred freshness SLA")
                    recommendations.append("Implement explicit freshness checking mechanism")
            else:
                score_components["has_sla"] = 0
                score_components["meets_sla"] = 0
                if REQUIRE_EXPLICIT_METADATA:
                    findings.append("No freshness SLA defined (explicit metadata required)")
                else:
                    findings.append("No freshness SLA defined")
                recommendations.append("Define explicit freshness SLAs for data")
            
            # 3. Evaluate freshness communication to agents
            if has_explicit_info:
                score_components["explicit_communication"] = MAX_EXPLICIT_COMMUNICATION_SCORE
                findings.append("Freshness information is explicitly communicated to agents")
            elif not REQUIRE_EXPLICIT_METADATA:
                # Award partial points for automatically calculated freshness information
                comm_score = int(MAX_EXPLICIT_COMMUNICATION_SCORE * 0.5)  # 50% of max
                score_components["explicit_communication"] = comm_score
                findings.append("Basic freshness information available through analysis (partial credit)")
            else:
                score_components["explicit_communication"] = 0
                findings.append("Freshness information is not explicitly communicated to agents (explicit metadata required)")
                recommendations.append("Make freshness information explicitly available to agents")
        else:
            # No freshness information available
            findings.append("No freshness information is available")
            recommendations.append("Implement basic freshness tracking and expose it to agents")
            score_components["has_timestamp"] = 0
            score_components["data_age"] = 0
            score_components["has_sla"] = 0
            score_components["meets_sla"] = 0
            score_components["explicit_communication"] = 0
        
        # Calculate overall score (0-20)
        # Weight: 
        # - has_timestamp: 4 points max
        # - data_age: 3 points max
        # - has_sla: 4 points max
        # - meets_sla: 3 points max
        # - explicit_communication: 6 points max
        score = sum(score_components.values())
        
        # Ensure we don't exceed the maximum score
        score = min(score, 20)
        
        # Add score component breakdown to findings
        findings.append(f"Score components: {score_components}")
        
        # Add recommendations if score is not perfect
        if score < 20 and score < 10:
            recommendations.append(
                "Implement a comprehensive freshness framework with explicit agent communication"
            )
                
        logger.info(f"Freshness assessment complete. Score: {score}")
        return score, findings, recommendations
