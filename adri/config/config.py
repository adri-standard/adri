"""
Configuration management for ADRI.

This module handles loading, merging, and providing access to configuration values
from both defaults and user-provided sources.
"""

import os
import yaml
from typing import Dict, Any, Optional
from copy import deepcopy

from .defaults import (
    VALIDITY_SCORING, COMPLETENESS_SCORING, FRESHNESS_SCORING, 
    CONSISTENCY_SCORING, PLAUSIBILITY_SCORING, DEFAULT_ASSESSMENT,
    DEFAULT_RULE_SETTINGS
)

class Configuration:
    """
    Configuration manager for ADRI.
    
    Handles loading and providing access to configuration values.
    """
    
    def __init__(self, user_config: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration with defaults and optional user overrides.
        
        Args:
            user_config: Optional user configuration to override defaults
        """
        self._config = {
            "validity_scoring": deepcopy(VALIDITY_SCORING),
            "completeness_scoring": deepcopy(COMPLETENESS_SCORING),
            "freshness_scoring": deepcopy(FRESHNESS_SCORING),
            "consistency_scoring": deepcopy(CONSISTENCY_SCORING),
            "plausibility_scoring": deepcopy(PLAUSIBILITY_SCORING),
            "assessment": deepcopy(DEFAULT_ASSESSMENT)
        }
        
        # Initialize rule settings
        self._rule_settings = deepcopy(DEFAULT_RULE_SETTINGS)
        
        # Track overridden settings for reporting
        self._overridden_settings = {}
        
        # Apply user configuration if provided
        if user_config:
            self._merge_config(user_config)
            
        # Check for environment variable overrides
        self._apply_env_overrides()
    
    def _merge_config(self, user_config: Dict[str, Any]):
        """Merge user configuration with defaults."""
        if "validity_scoring" in user_config:
            for key, value in user_config["validity_scoring"].items():
                self._config["validity_scoring"][key] = value
        
        if "completeness_scoring" in user_config:
            for key, value in user_config["completeness_scoring"].items():
                self._config["completeness_scoring"][key] = value

        if "freshness_scoring" in user_config:
            for key, value in user_config["freshness_scoring"].items():
                self._config["freshness_scoring"][key] = value
                
        if "consistency_scoring" in user_config:
            for key, value in user_config["consistency_scoring"].items():
                self._config["consistency_scoring"][key] = value
                
        if "plausibility_scoring" in user_config:
            for key, value in user_config["plausibility_scoring"].items():
                self._config["plausibility_scoring"][key] = value
                
        if "assessment" in user_config:
            for key, value in user_config["assessment"].items():
                if isinstance(value, dict) and isinstance(self._config["assessment"].get(key), dict):
                    # Merge nested dictionaries
                    for subkey, subvalue in value.items():
                        self._config["assessment"][key][subkey] = subvalue
                else:
                    self._config["assessment"][key] = value
        
        # Handle rule settings
        if "rules" in user_config:
            for rule_id, rule_config in user_config["rules"].items():
                if rule_id in self._rule_settings:
                    # Track what settings were overridden
                    self._overridden_settings[rule_id] = {}
                    
                    for key, value in rule_config.items():
                        # Only track settings that differ from defaults
                        if key in self._rule_settings[rule_id] and self._rule_settings[rule_id][key] != value:
                            self._overridden_settings[rule_id][key] = {
                                "default": self._rule_settings[rule_id][key],
                                "custom": value
                            }
                        
                        # Apply the override
                        self._rule_settings[rule_id][key] = value
    
    def _apply_env_overrides(self):
        """Apply any environment variable overrides."""
        # Example: ADRI_REQUIRE_EXPLICIT_METADATA=true would override that setting
        if "ADRI_REQUIRE_EXPLICIT_METADATA" in os.environ:
            value = os.environ["ADRI_REQUIRE_EXPLICIT_METADATA"].lower() in ('true', '1', 'yes')
            # Apply to all dimensions
            self._config["validity_scoring"]["REQUIRE_EXPLICIT_METADATA"] = value
            self._config["completeness_scoring"]["REQUIRE_EXPLICIT_METADATA"] = value
            self._config["freshness_scoring"]["REQUIRE_EXPLICIT_METADATA"] = value
            self._config["consistency_scoring"]["REQUIRE_EXPLICIT_METADATA"] = value
            self._config["plausibility_scoring"]["REQUIRE_EXPLICIT_METADATA"] = value
    
    @classmethod
    def from_file(cls, config_path: str) -> 'Configuration':
        """
        Load configuration from a YAML file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration instance with file-based config applied
        """
        with open(config_path, 'r') as f:
            user_config = yaml.safe_load(f)
            
        return cls(user_config)
    
    def get_validity_scoring(self) -> Dict[str, Any]:
        """Get validity dimension scoring configuration."""
        return self._config["validity_scoring"]
    
    def get_completeness_scoring(self) -> Dict[str, Any]:
        """Get completeness dimension scoring configuration."""
        return self._config["completeness_scoring"]
        
    def get_freshness_scoring(self) -> Dict[str, Any]:
        """Get freshness dimension scoring configuration."""
        return self._config["freshness_scoring"]
        
    def get_consistency_scoring(self) -> Dict[str, Any]:
        """Get consistency dimension scoring configuration."""
        return self._config["consistency_scoring"]
    
    def get_plausibility_scoring(self) -> Dict[str, Any]:
        """Get plausibility dimension scoring configuration."""
        return self._config["plausibility_scoring"]
    
    def get_assessment_config(self) -> Dict[str, Any]:
        """Get assessment configuration."""
        return self._config["assessment"]
    
    def require_explicit_metadata(self, dimension: str = "validity") -> bool:
        """
        Check if explicit metadata is required.
        
        Args:
            dimension: The dimension to check (validity, completeness, freshness, consistency, etc.)
            
        Returns:
            Boolean indicating whether explicit metadata is required
        """
        if dimension == "completeness" and "REQUIRE_EXPLICIT_METADATA" in self._config["completeness_scoring"]:
            return self._config["completeness_scoring"]["REQUIRE_EXPLICIT_METADATA"]
        elif dimension == "freshness" and "REQUIRE_EXPLICIT_METADATA" in self._config["freshness_scoring"]:
            return self._config["freshness_scoring"]["REQUIRE_EXPLICIT_METADATA"]
        elif dimension == "consistency" and "REQUIRE_EXPLICIT_METADATA" in self._config["consistency_scoring"]:
            return self._config["consistency_scoring"]["REQUIRE_EXPLICIT_METADATA"]
        elif dimension == "plausibility" and "REQUIRE_EXPLICIT_METADATA" in self._config["plausibility_scoring"]:
            return self._config["plausibility_scoring"]["REQUIRE_EXPLICIT_METADATA"]
        # Default to validity if dimension not specified or not found
        return self._config["validity_scoring"]["REQUIRE_EXPLICIT_METADATA"]
    
    def get_rule_settings(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all rule settings.
        
        Returns:
            Dict mapping rule IDs to their configurations
        """
        return deepcopy(self._rule_settings)
    
    def get_rule_config(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific rule.
        
        Args:
            rule_id: The ID of the rule
            
        Returns:
            Dict containing the rule configuration, or None if not found
        """
        if rule_id in self._rule_settings:
            return deepcopy(self._rule_settings[rule_id])
        return None
    
    def get_overridden_settings(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Get settings that were overridden by user configuration.
        
        Returns:
            Dict containing overridden settings with their default and custom values
        """
        return deepcopy(self._overridden_settings)
    
    def is_rule_enabled(self, rule_id: str) -> bool:
        """
        Check if a rule is enabled.
        
        Args:
            rule_id: The ID of the rule
            
        Returns:
            Boolean indicating whether the rule is enabled
        """
        if rule_id in self._rule_settings:
            return self._rule_settings[rule_id].get("enabled", True)
        return False
    
    def get_rules_by_dimension(self, dimension: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all rule configurations for a specific dimension.
        
        Args:
            dimension: The dimension to filter by
            
        Returns:
            Dict mapping rule IDs to their configurations for the specified dimension
        """
        return {
            rule_id: rule_config
            for rule_id, rule_config in self._rule_settings.items()
            if rule_id.startswith(f"{dimension}.")
        }


# Default instance with base configuration
default_config = Configuration()

def get_config() -> Configuration:
    """Get the current configuration instance."""
    return default_config

def set_config(config: Configuration):
    """Set the current configuration instance."""
    global default_config
    default_config = config
