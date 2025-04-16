"""
Dimension assessors for the Agent Data Readiness Index.

This package contains the assessors for each of the five ADRI dimensions:
- Validity: Whether data adheres to required types, formats, and ranges
- Completeness: Whether all expected data is present
- Freshness: Whether data is current enough for the decision
- Consistency: Whether data elements maintain logical relationships
- Plausibility: Whether data values are reasonable based on context
"""

from .base import BaseDimensionAssessor
from .registry import DimensionRegistry


def register_dimension(name: str, description: str = ""):
    """
    Decorator to register a dimension assessor.
    
    Args:
        name: Name of the dimension
        description: Optional description of the dimension
        
    Returns:
        Callable: Decorator function
    """
    def decorator(cls):
        cls.dimension_name = name
        cls.dimension_description = description
        DimensionRegistry.register(name, cls)
        return cls
    return decorator


# Import all dimension assessors
from .validity import ValidityAssessor
from .completeness import CompletenessAssessor
from .freshness import FreshnessAssessor
from .consistency import ConsistencyAssessor
from .plausibility import PlausibilityAssessor


__all__ = [
    "BaseDimensionAssessor",
    "DimensionRegistry",
    "register_dimension",
    "ValidityAssessor",
    "CompletenessAssessor", 
    "FreshnessAssessor",
    "ConsistencyAssessor",
    "PlausibilityAssessor",
]
