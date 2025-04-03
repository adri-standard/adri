"""
Validation utilities for the Agent Data Readiness Index.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        bool: True if the configuration is valid
        
    Raises:
        ValueError: If the configuration is invalid
    """
    # For now, this is a simple implementation that just logs and accepts any config
    # In a full implementation, this would check for required fields, validate types, etc.
    
    if not config:
        logger.debug("Using default configuration")
        return True
        
    logger.debug(f"Validating configuration with keys: {list(config.keys())}")
    
    # Validate dimension weights if present
    if "dimensions" in config:
        dimensions = config["dimensions"]
        for dim_name, dim_config in dimensions.items():
            if "weight" in dim_config and not isinstance(dim_config["weight"], (int, float)):
                raise ValueError(f"Dimension weight for {dim_name} must be a number")
                
    return True
