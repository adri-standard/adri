"""
Registry for dimension assessors in the Agent Data Readiness Index.

This module provides a registry for dimension assessors, allowing them to be
dynamically registered and discovered.
"""

from typing import Dict, Type, List, Any

from .base import BaseDimensionAssessor


class DimensionRegistry:
    """
    Registry for dimension assessors.
    
    This class provides a central registry for all dimension assessors,
    allowing them to be dynamically registered and discovered.
    """
    
    _dimensions: Dict[str, Type[BaseDimensionAssessor]] = {}
    
    @classmethod
    def register(cls, name: str, dimension_class: Type[BaseDimensionAssessor]) -> None:
        """
        Register a dimension assessor.
        
        Args:
            name: Name of the dimension
            dimension_class: Dimension assessor class
        """
        cls._dimensions[name] = dimension_class
        
    @classmethod
    def get_dimension(cls, name: str) -> Type[BaseDimensionAssessor]:
        """
        Get a dimension assessor by name.
        
        Args:
            name: Name of the dimension
            
        Returns:
            Type[BaseDimensionAssessor]: Dimension assessor class
            
        Raises:
            ValueError: If the dimension is not registered
        """
        if name not in cls._dimensions:
            raise ValueError(f"Dimension '{name}' not registered")
        return cls._dimensions[name]
        
    @classmethod
    def get_all_dimensions(cls) -> Dict[str, Type[BaseDimensionAssessor]]:
        """
        Get all registered dimensions.
        
        Returns:
            Dict[str, Type[BaseDimensionAssessor]]: Dictionary of dimension name to assessor class
        """
        return cls._dimensions.copy()
        
    @classmethod
    def list_dimensions(cls) -> List[str]:
        """
        List all registered dimension names.
        
        Returns:
            List[str]: List of dimension names
        """
        return list(cls._dimensions.keys())

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/test_assessor.py (dimension registration and retrieval)
# 
# 2. Integration tests:
#    - tests/integration/test_cli.py (dimension discovery and execution)
#
# 3. Dimension registration through decorator in:
#    - adri/dimensions/validity.py
#    - adri/dimensions/completeness.py
#    - adri/dimensions/freshness.py
#    - adri/dimensions/consistency.py
#    - adri/dimensions/plausibility.py
#
# Complete test coverage details are documented in:
# docs/test_coverage/DIMENSIONS_test_coverage.md
# ----------------------------------------------
