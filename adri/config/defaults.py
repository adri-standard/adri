"""
Default configuration values for ADRI.

This module provides default configuration values that can be overridden
by user-specific configurations at runtime.
"""

# Validity dimension scoring weights
VALIDITY_SCORING = {
    "MAX_TYPES_DEFINED_SCORE": 5,
    "MAX_FORMATS_DEFINED_SCORE": 3,
    "MAX_RANGES_DEFINED_SCORE": 3,
    "MAX_VALIDATION_PERFORMED_SCORE": 3,
    "MAX_VALIDATION_COMMUNICATED_SCORE": 6,
    "REQUIRE_EXPLICIT_METADATA": False  # When True, only explicit metadata gets full points
}

# Completeness dimension scoring weights
COMPLETENESS_SCORING = {
    "MAX_OVERALL_COMPLETENESS_SCORE": 5,
    "MAX_NULL_DISTINCTION_SCORE": 5,
    "MAX_EXPLICIT_METRICS_SCORE": 5,
    "MAX_SECTION_AWARENESS_SCORE": 5,
    "REQUIRE_EXPLICIT_METADATA": False  # Same flag as validity for consistency
}

# Freshness dimension scoring weights
FRESHNESS_SCORING = {
    "MAX_HAS_TIMESTAMP_SCORE": 4,
    "MAX_DATA_AGE_SCORE": 3,
    "MAX_HAS_SLA_SCORE": 4, 
    "MAX_MEETS_SLA_SCORE": 3,
    "MAX_EXPLICIT_COMMUNICATION_SCORE": 6,
    "REQUIRE_EXPLICIT_METADATA": False  # When True, only explicit metadata gets full points
}

# Consistency dimension scoring weights
CONSISTENCY_SCORING = {
    "MAX_RULES_DEFINED_SCORE": 4,
    "MAX_RULE_TYPES_SCORE": 3,
    "MAX_RULE_VALIDITY_SCORE": 4,
    "MAX_CROSS_DATASET_SCORE": 3,
    "MAX_EXPLICIT_COMMUNICATION_SCORE": 6,
    "REQUIRE_EXPLICIT_METADATA": False  # When True, only explicit metadata gets full points
}

# Plausibility dimension scoring weights
PLAUSIBILITY_SCORING = {
    "MAX_RULES_DEFINED_SCORE": 4,
    "MAX_RULE_TYPES_SCORE": 3,
    "MAX_RULE_VALIDITY_SCORE": 4,
    "MAX_CONTEXT_AWARENESS_SCORE": 3,
    "MAX_EXPLICIT_COMMUNICATION_SCORE": 6,
    "REQUIRE_EXPLICIT_METADATA": False  # When True, only explicit metadata gets full points
}

# Default assessment parameters
DEFAULT_ASSESSMENT = {
    "sample_size": 1000,  # Maximum number of records to analyze
    "dimension_weights": {
        "validity": 1.0,
        "completeness": 1.0,
        "freshness": 1.0,
        "consistency": 1.0,
        "plausibility": 1.0
    }
}

# Default rule settings
# Each rule has its own settings with defaults
# These can be overridden in user config
DEFAULT_RULE_SETTINGS = {
    # Validity dimension rules
    "validity.type_consistency": {
        "enabled": True,
        "weight": 2.0,  # Contributes to MAX_TYPES_DEFINED_SCORE
        "threshold": 0.9,  # Minimum required type consistency rate
        "analyze_all_columns": True,  # Whether to analyze all columns or just specified ones
        "importance": "high"
    },
    "validity.range_validation": {
        "enabled": True,
        "weight": 1.5,  # Contributes to MAX_RANGES_DEFINED_SCORE
        "detect_outliers": True,  # Whether to automatically detect outliers as range violations
        "outlier_threshold": 3.0,  # Z-score threshold for outlier detection
        "importance": "medium"
    },
    "validity.format_consistency": {
        "enabled": True,
        "weight": 1.5,  # Contributes to MAX_FORMATS_DEFINED_SCORE
        "date_formats": ["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY"],  # Recognized date formats
        "importance": "medium"
    },
    
    # Completeness dimension rules
    "completeness.missing_values": {
        "enabled": True,
        "weight": 3.0,  # Contributes to MAX_OVERALL_COMPLETENESS_SCORE
        "acceptable_threshold": 0.05,  # Maximum acceptable missing value rate
        "critical_threshold": 0.20,  # Threshold above which completeness is considered critical
        "importance": "high"
    },
    "completeness.required_fields": {
        "enabled": True,
        "weight": 2.0,  # Contributes to MAX_NULL_DISTINCTION_SCORE
        "ignore_explicitly_optional": True,  # Whether to ignore fields marked as optional
        "importance": "high"
    },
    
    # Freshness dimension rules
    "freshness.data_age": {
        "enabled": True,
        "weight": 3.0,  # Contributes to MAX_DATA_AGE_SCORE
        "max_age_hours": 72,  # Maximum acceptable age in hours
        "critical_age_hours": 168,  # Age above which data is considered stale
        "importance": "high"
    },
    "freshness.update_frequency": {
        "enabled": True,
        "weight": 2.0,  # Contributes to MAX_HAS_SLA_SCORE
        "default_frequency": "daily",  # Default expected update frequency
        "importance": "medium"
    },
    
    # Consistency dimension rules
    "consistency.schema_consistency": {
        "enabled": True,
        "weight": 2.0,  # Contributes to MAX_RULES_DEFINED_SCORE
        "require_consistent_types": True,  # Whether to require consistent types across datasets
        "importance": "high"
    },
    "consistency.value_distribution": {
        "enabled": True,
        "weight": 2.0,  # Contributes to MAX_RULE_VALIDITY_SCORE
        "distribution_method": "ks_test",  # Statistical test for distribution comparison
        "significance_level": 0.05,  # P-value threshold for distribution tests
        "importance": "medium"
    },
    
    # Plausibility dimension rules
    "plausibility.outlier_detection": {
        "enabled": True,
        "weight": 2.0,  # Contributes to MAX_RULE_VALIDITY_SCORE
        "method": "zscore",  # Method for outlier detection
        "threshold": 3.0,  # Threshold for outlier detection
        "analyze_numeric_only": True,  # Whether to analyze only numeric columns
        "importance": "high"
    },
    "plausibility.pattern_consistency": {
        "enabled": True,
        "weight": 1.5,  # Contributes to MAX_RULE_TYPES_SCORE
        "min_pattern_confidence": 0.8,  # Minimum confidence for pattern identification
        "importance": "medium"
    },
    "plausibility.domain_specific": {
        "enabled": True,
        "weight": 1.5,  # Contributes to MAX_CONTEXT_AWARENESS_SCORE
        "domains": [],  # List of domains to apply
        "importance": "high"
    }
}

# Version-specific rule settings
# This allows for maintaining backward compatibility as the framework evolves
DEFAULT_RULE_SETTINGS_V1 = DEFAULT_RULE_SETTINGS.copy()
