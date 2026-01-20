"""
ADRI Validator Module.

Data validation engine and assessment functionality.
Core validation logic migrated from core/assessor.py.

Components:
- ValidationEngine: Core validation engine
- DataQualityAssessor: Main assessment interface
- AssessmentResult: Result data structures
- validate_standard: Unified mode-aware standard validation (NEW)
- validate_conversation_structure: Conversation mode validation helper (NEW)
- validate_standard_schema_v2: Field requirements validation (backward compatibility)

This module provides the core validation capabilities for the ADRI framework.
"""

# Import validator components
from .engine import (
    AssessmentResult,
    DataQualityAssessor,
    DimensionScore,
    FieldAnalysis,
    RuleExecutionResult,
    ValidationEngine,
)

# Import loader utilities
from .loaders import load_data, load_contract

# Import schema validation functions
from .schema_validator import (
    validate_standard,
    validate_conversation_structure,
    validate_standard_schema_v2,
)

# Export all components
__all__ = [
    "ValidationEngine",
    "DataQualityAssessor",
    "AssessmentResult",
    "DimensionScore",
    "FieldAnalysis",
    "RuleExecutionResult",
    "load_data",
    "load_contract",
    "validate_standard",
    "validate_conversation_structure",
    "validate_standard_schema_v2",
]
