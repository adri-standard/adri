"""
ADRI Validator Module.

Data validation engine and assessment functionality.
Core validation logic migrated from core/assessor.py.

Components:
- ValidationEngine: Core validation engine
- DataQualityAssessor: Main assessment interface
- AssessmentResult: Result data structures

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
from .loaders import load_data, load_standard

# Export all components
__all__ = [
    "ValidationEngine",
    "DataQualityAssessor",
    "AssessmentResult",
    "DimensionScore",
    "FieldAnalysis",
    "RuleExecutionResult",
    "load_data",
    "load_standard",
]
