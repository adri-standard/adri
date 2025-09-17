"""
ADRI Validator Module

Handles data quality assessment and validation engine functionality.
Consolidates functionality from the original core/assessor.py and related components.

Components:
- ValidationEngine: Main assessment orchestrator (renamed from AssessmentEngine)
- DataQualityAssessor: Core data quality assessment functionality
- Data loaders: CSV, JSON, Parquet loading utilities
- Validation rules: Field-level validation logic

This module provides the core assessment capabilities for the ADRI framework.
"""

# Import validation engine and assessor
from .engine import ValidationEngine, DataQualityAssessor, AssessmentResult, DimensionScore, FieldAnalysis, RuleExecutionResult

# Import data loaders
from .loaders import load_data, load_csv, load_json, load_parquet, load_standard, detect_format, get_data_info

# Import validation rules
from .rules import validate_field, check_field_type, check_field_pattern, check_field_range

# Export all components
__all__ = [
    # Engine components
    "ValidationEngine", 
    "DataQualityAssessor", 
    "AssessmentResult", 
    "DimensionScore", 
    "FieldAnalysis", 
    "RuleExecutionResult",
    # Data loaders
    "load_data", 
    "load_csv", 
    "load_json", 
    "load_parquet", 
    "load_standard", 
    "detect_format", 
    "get_data_info",
    # Validation functions
    "validate_field", 
    "check_field_type", 
    "check_field_pattern", 
    "check_field_range"
]
