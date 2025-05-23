"""
Registry for ADRI diagnostic rules.

This module provides the RuleRegistry that maintains a catalog of all
available diagnostic rules and facilitates their discovery and use.
"""

from typing import Dict, List, Type, Any, Optional, Set
import logging

from .base import DiagnosticRule

logger = logging.getLogger(__name__)


class RuleRegistry:
    """
    Registry that maintains a catalog of all available diagnostic rules.
    
    The registry provides methods to register rules, retrieve them by ID,
    and get organized views of all available rules.
    """
    
    _rules = {}  # Mapping of rule_id to rule class
    
    @classmethod
    def register(cls, rule_class):
        """
        Register a rule class with the registry.
        
        This method is typically used as a decorator on rule classes.
        
        Args:
            rule_class: The rule class to register
            
        Returns:
            The rule class (to allow decorator usage)
        """
        if not issubclass(rule_class, DiagnosticRule):
            raise TypeError(f"Rule class {rule_class.__name__} must inherit from DiagnosticRule")
            
        rule_id = rule_class.rule_id
        if not rule_id:
            raise ValueError(f"Rule class {rule_class.__name__} missing rule_id")
            
        if rule_id in cls._rules:
            logger.warning(f"Overwriting existing rule with ID {rule_id}")
            
        cls._rules[rule_id] = rule_class
        logger.debug(f"Registered rule {rule_id}: {rule_class.__name__}")
        
        return rule_class
    
    @classmethod
    def get_rule(cls, rule_id: str) -> Optional[Type[DiagnosticRule]]:
        """
        Get a rule class by its ID.
        
        Args:
            rule_id: The ID of the rule to retrieve
            
        Returns:
            The rule class, or None if not found
        """
        return cls._rules.get(rule_id)
    
    @classmethod
    def list_rules(cls) -> Dict[str, Type[DiagnosticRule]]:
        """
        Get a dictionary of all registered rules.
        
        Returns:
            Dict mapping rule IDs to rule classes
        """
        return cls._rules.copy()
    
    @classmethod
    def get_rule_grid(cls) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get a grid view of all rules organized by dimension.
        
        Returns:
            Dict mapping dimension names to lists of rule metadata
        """
        grid = {}
        
        for rule_id, rule_class in cls._rules.items():
            dimension = rule_class.dimension
            
            if dimension not in grid:
                grid[dimension] = []
                
            # Create a temporary instance to get metadata
            # We don't pass any params so defaults will be used
            rule_instance = rule_class()
            
            grid[dimension].append(rule_instance.get_metadata())
            
        return grid
    
    @classmethod
    def get_rules_by_dimension(cls, dimension: str) -> Dict[str, Type[DiagnosticRule]]:
        """
        Get all rules for a specific dimension.
        
        Args:
            dimension: The dimension to filter by
            
        Returns:
            Dict mapping rule IDs to rule classes for the specified dimension
        """
        return {
            rule_id: rule_class
            for rule_id, rule_class in cls._rules.items()
            if rule_class.dimension == dimension
        }
    
    @classmethod
    def get_dimensions(cls) -> Set[str]:
        """
        Get the set of all dimensions that have registered rules.
        
        Returns:
            Set of dimension names
        """
        return {rule_class.dimension for rule_class in cls._rules.values()}
    
    @classmethod
    def create_rule(cls, rule_id: str, params: Optional[Dict[str, Any]] = None) -> Optional[DiagnosticRule]:
        """
        Create an instance of a rule by its ID.
        
        Args:
            rule_id: The ID of the rule to create
            params: Optional parameters to pass to the rule constructor
            
        Returns:
            An instance of the rule, or None if the rule ID is not found
        """
        rule_class = cls.get_rule(rule_id)
        
        if not rule_class:
            return None
            
        return rule_class(params)
    
    @classmethod
    def create_all_rules(cls, params_dict: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, DiagnosticRule]:
        """
        Create instances of all registered rules.
        
        Args:
            params_dict: Optional dict mapping rule IDs to parameter dicts
            
        Returns:
            Dict mapping rule IDs to rule instances
        """
        params_dict = params_dict or {}
        
        return {
            rule_id: rule_class(params_dict.get(rule_id, {}))
            for rule_id, rule_class in cls._rules.items()
        }
    
    @classmethod
    def generate_markdown_grid(cls) -> str:
        """
        Generate a Markdown representation of the rule grid.
        
        Returns:
            Markdown string containing a table of all rules
        """
        grid = cls.get_rule_grid()
        
        markdown = "# ADRI Diagnostic Rules\n\n"
        
        for dimension, rules in sorted(grid.items()):
            markdown += f"## {dimension.capitalize()} Dimension\n\n"
            markdown += "| Rule ID | Name | Description | Parameters |\n"
            markdown += "|---------|------|-------------|------------|\n"
            
            for rule in sorted(rules, key=lambda r: r["id"]):
                params_str = ", ".join([p["name"] for p in rule["parameters"]])
                markdown += f"| `{rule['id']}` | {rule['name']} | {rule['description']} | {params_str} |\n"
            
            markdown += "\n"
        
        return markdown

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/test_assessor.py (rule registration and retrieval)
# 
# 2. Integration tests:
#    - tests/integration/test_cli.py (rule discovery and execution)
#
# 3. Rule registration in:
#    - All rule implementation files that use the @RuleRegistry.register decorator
#    - tests/unit/dimensions/test_validity_detection.py (rule discovery)
#    - tests/unit/dimensions/test_completeness.py (rule discovery)
#
# 4. Documentation generation:
#    - adri/rules/rule_grid.md (generated through generate_markdown_grid)
#
# Complete test coverage details are documented in:
# docs/test_coverage/RULES_test_coverage.md
# ----------------------------------------------
