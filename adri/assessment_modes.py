"""
Assessment modes for ADRI.

This module defines different assessment modes that control how ADRI evaluates data sources.
"""

from enum import Enum
from typing import Dict, Any, Optional


class AssessmentMode(Enum):
    """
    Defines the different modes of assessment available in ADRI.
    """
    
    # Discovery mode: Analyze raw data and suggest improvements
    DISCOVERY = "discovery"
    
    # Validation mode: Verify compliance with metadata and templates  
    VALIDATION = "validation"
    
    # Auto mode: Intelligently choose between discovery and validation
    AUTO = "auto"


class ModeConfig:
    """
    Configuration specific to each assessment mode.
    """
    
    @staticmethod
    def get_mode_config(mode: AssessmentMode) -> Dict[str, Any]:
        """
        Get the configuration for a specific assessment mode.
        
        Args:
            mode: The assessment mode
            
        Returns:
            Dictionary of configuration values for the mode
        """
        configs = {
            AssessmentMode.DISCOVERY: {
                # Discovery mode: analyze quality AND generate metadata
                "require_explicit_metadata": False,
                "suggest_templates": True,
                "generate_metadata": True,  # Always generate helpful metadata
                "intrinsic_quality_weight": 1.0,  # Only score on actual quality
                "metadata_quality_weight": 0.0,   # No penalty for missing metadata
                "business_logic_enabled": True,   # Enable business-specific checks
                "auto_generate_metadata": True,   # New: automatically create metadata
                "metadata_penalty": False,        # New: don't penalize missing metadata
                # Template discovery configuration
                "template_discovery_enabled": True,
                "template_confidence_threshold": 0.7,
                "suggest_top_templates": 3,
                "auto_apply_template": False,  # Require user confirmation
            },
            AssessmentMode.VALIDATION: {
                # Validation mode: verify data meets declared standards
                "require_explicit_metadata": True,
                "suggest_templates": False,
                "generate_metadata": False,
                "intrinsic_quality_weight": 0.2,      # Some weight on actual quality
                "metadata_quality_weight": 0.0,       # No metadata quality score
                "claims_compliance_weight": 0.8,      # New: weight on meeting claims
                "business_logic_enabled": False,      # Focus on declared standards
                "verify_claims": True,                # New: verify against declarations
                "metadata_penalty": False,            # No penalty, just verification
            },
            AssessmentMode.AUTO: {
                # Auto mode starts permissive and adjusts based on what's available
                "require_explicit_metadata": False,
                "suggest_templates": True,
                "generate_metadata": True,
                "intrinsic_quality_weight": 0.5,
                "metadata_quality_weight": 0.5,
                "business_logic_enabled": True,
            }
        }
        
        return configs.get(mode, configs[AssessmentMode.AUTO])
    
    @staticmethod
    def detect_mode(connector, has_metadata: bool = False, has_template: bool = False) -> AssessmentMode:
        """
        Automatically detect which mode to use based on available information.
        
        Args:
            connector: The data connector
            has_metadata: Whether ADRI metadata files exist
            has_template: Whether a template is specified
            
        Returns:
            The detected assessment mode
        """
        # If we have metadata or template, use validation mode
        if has_metadata or has_template:
            return AssessmentMode.VALIDATION
            
        # Check if connector has schema information
        schema = connector.get_schema()
        if schema and "fields" in schema and len(schema["fields"]) > 0:
            # Has some schema, might be validation mode
            # But check if it's comprehensive
            fields_with_validation = sum(
                1 for f in schema["fields"] 
                if any(k in f for k in ["format", "pattern", "min_value", "max_value", "allowed_values"])
            )
            
            # If more than 50% of fields have validation rules, use validation mode
            if fields_with_validation / len(schema["fields"]) > 0.5:
                return AssessmentMode.VALIDATION
        
        # Default to discovery mode for raw data
        return AssessmentMode.DISCOVERY
