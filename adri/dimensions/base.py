"""
Base dimension assessor for the Agent Data Readiness Index.

This module defines the BaseDimensionAssessor abstract class that all dimension
assessors must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional

from ..connectors import BaseConnector


class BaseDimensionAssessor(ABC):
    """
    Base class for all dimension assessors.
    
    All dimension assessors must inherit from this class and implement
    the assess method.
    """
    
    dimension_name: str = "base"  # Override in subclasses
    dimension_description: str = ""  # Override in subclasses
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the assessor with optional configuration.
        
        Args:
            config: Optional configuration for the assessment
        """
        self.config = config or {}
    
    @abstractmethod
    def assess(self, connector: BaseConnector) -> Tuple[float, List[str], List[str]]:
        """
        Assess the dimension for a data source.
        
        Args:
            connector: Data source connector
            
        Returns:
            Tuple containing:
                - score (0-20)
                - list of findings
                - list of recommendations
        """
        pass

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Abstract class implementation in all dimension assessors:
#    - tests/unit/dimensions/test_validity_detection.py
#    - tests/unit/dimensions/test_completeness.py
#    - tests/unit/dimensions/test_freshness_basic.py
#    - tests/unit/dimensions/test_consistency_basic.py
#    - tests/unit/dimensions/test_plausibility_basic.py
# 
# 2. Integration tests:
#    - tests/unit/test_assessor.py (dimension registration and assessment)
#    - tests/integration/test_cli.py (dimension assessment pipeline)
#
# Complete test coverage details are documented in:
# docs/test_coverage/DIMENSIONS_test_coverage.md
# ----------------------------------------------
