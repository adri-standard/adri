"""
Base class for all ADRI diagnostic rules.

This module provides the DiagnosticRule base class that all rules
in the ADRI framework must inherit from, ensuring consistent interfaces
and behavior across all rule implementations.
"""

from typing import Dict, Any, Optional, List, Union
import logging

logger = logging.getLogger(__name__)


class DiagnosticRule:
    """
    Base class for all diagnostic rules in the ADRI framework.
    
    All rules must inherit from this class and implement the required methods.
    Each rule is responsible for evaluating a specific aspect of data quality
    and generating both a score and a narrative description of the findings.
    """
    
    rule_id = None  # Unique identifier (e.g., "plausibility.outlier_detection")
    dimension = None  # Which dimension this rule belongs to
    name = None  # Human-readable name
    description = None  # Detailed description
    version = "1.0.0"  # Rule implementation version
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        Initialize a diagnostic rule.
        
        Args:
            params: Optional parameters to configure the rule behavior
        """
        self.params = params or {}
        self.enabled = self.params.get("enabled", True)
        
        # Validate required class attributes
        if not self.rule_id:
            raise ValueError(f"Rule {self.__class__.__name__} missing rule_id")
        if not self.dimension:
            raise ValueError(f"Rule {self.__class__.__name__} missing dimension")
        if not self.name:
            raise ValueError(f"Rule {self.__class__.__name__} missing name")
            
        logger.debug(f"Initialized rule {self.rule_id} with params: {self.params}")
    
    def evaluate(self, data: Any) -> Dict[str, Any]:
        """
        Evaluate this rule against the provided data.
        
        Args:
            data: Data to evaluate (typically a pandas DataFrame or connector)
            
        Returns:
            Dict containing at minimum:
                - score: Numeric score contribution (0-N)
                - valid: Boolean indicating if the rule passed
                - (other rule-specific result details)
        """
        raise NotImplementedError("Subclasses must implement evaluate()")
    
    def generate_narrative(self, result: Dict[str, Any]) -> str:
        """
        Generate a narrative description of the rule evaluation result.
        
        This narrative should be suitable for inclusion in reports and
        for consumption by AI agents to understand data quality issues.
        
        Args:
            result: The result from evaluate()
            
        Returns:
            String containing the narrative description
        """
        raise NotImplementedError("Subclasses must implement generate_narrative()")
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this rule.
        
        Returns:
            Dict containing rule metadata
        """
        return {
            "id": self.rule_id,
            "dimension": self.dimension,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "parameters": self._get_parameter_metadata()
        }
    
    def _get_parameter_metadata(self) -> List[Dict[str, Any]]:
        """
        Get metadata about the parameters accepted by this rule.
        
        This should be overridden by subclasses to document their parameters.
        
        Returns:
            List of parameter metadata dictionaries
        """
        return [
            {
                "name": "enabled",
                "type": "boolean",
                "default": True,
                "description": "Whether this rule is enabled"
            }
        ]

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/test_assessor.py (base rule functionality)
# 
# 2. Integration tests:
#    - tests/integration/test_cli.py (rule instantiation and registration)
#
# 3. Rule inheritance in:
#    - tests/unit/dimensions/test_validity_detection.py
#    - tests/unit/dimensions/test_completeness.py
#    - tests/unit/dimensions/test_freshness_basic.py
#
# Complete test coverage details are documented in:
# docs/test_coverage/RULES_test_coverage.md
# ----------------------------------------------
