"""
Derivation rule structures for ADRI schema-based category derivation.

This module defines the structures for enhanced allowed_values that support:
- Category definitions with business logic descriptions
- Precedence-based evaluation order
- Derivation rules with input fields and conditional logic
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class DerivationRule:
    """
    Defines how to derive a categorical value from other fields.

    Attributes:
        type: Type of derivation logic (e.g., "ordered_conditions", "formula", "direct_mapping")
        inputs: List of input field names that this rule depends on
        logic: Expression or condition that determines when this category applies
        metadata: Optional metadata for additional context

    Example:
        DerivationRule(
            type="ordered_conditions",
            inputs=["project_status", "priority_order"],
            logic="IF project_status = 'At Risk' AND priority_order = 1 THEN 'Critical'"
        )
    """

    type: str
    inputs: list[str]
    logic: str
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        """Validate derivation rule structure."""
        if not self.type:
            raise ValueError("DerivationRule type cannot be empty")
        if not isinstance(self.inputs, list):
            raise ValueError("DerivationRule inputs must be a list")
        if not self.logic:
            raise ValueError("DerivationRule logic cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {"type": self.type, "inputs": self.inputs, "logic": self.logic}
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DerivationRule":
        """Create DerivationRule from dictionary."""
        return cls(
            type=data["type"],
            inputs=data["inputs"],
            logic=data["logic"],
            metadata=data.get("metadata"),
        )


@dataclass
class CategoryDefinition:
    """
    Enhanced definition for a categorical value with business logic.

    Attributes:
        definition: Human-readable description of what this category means
        precedence: Evaluation order (lower numbers = higher priority)
        derivation_rule: Optional rule for deriving this category value
        examples: Optional list of example scenarios
        metadata: Optional metadata for additional context

    Example:
        CategoryDefinition(
            definition="Regulatory/compliance risk with execution challenges",
            precedence=1,
            derivation_rule=DerivationRule(
                type="ordered_conditions",
                inputs=["project_status", "priority_order"],
                logic="IF project_status = 'At Risk' AND priority_order = 1"
            )
        )
    """

    definition: str
    precedence: int
    derivation_rule: DerivationRule | None = None
    examples: list[str] | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        """Validate category definition structure."""
        if not self.definition:
            raise ValueError("CategoryDefinition definition cannot be empty")
        if not isinstance(self.precedence, int):
            raise ValueError("CategoryDefinition precedence must be an integer")
        if self.precedence < 1:
            raise ValueError("CategoryDefinition precedence must be >= 1")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {"definition": self.definition, "precedence": self.precedence}
        if self.derivation_rule:
            result["derivation_rule"] = self.derivation_rule.to_dict()
        if self.examples:
            result["examples"] = self.examples
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CategoryDefinition":
        """Create CategoryDefinition from dictionary."""
        derivation_rule = None
        if "derivation_rule" in data and data["derivation_rule"]:
            derivation_rule = DerivationRule.from_dict(data["derivation_rule"])

        return cls(
            definition=data["definition"],
            precedence=data["precedence"],
            derivation_rule=derivation_rule,
            examples=data.get("examples"),
            metadata=data.get("metadata"),
        )


def validate_enhanced_allowed_values(
    allowed_values: list[str] | dict[str, Any], field_path: str
) -> list[str]:
    """
    Validate enhanced allowed_values structure.

    Args:
        allowed_values: Either a simple list or enhanced dict format
        field_path: Path to the field for error messages

    Returns:
        List of error messages (empty if valid)

    Example:
        errors = validate_enhanced_allowed_values(
            {"High": {"definition": "...", "precedence": 1}},
            "RISK_LEVEL"
        )
    """
    errors = []

    # Handle simple list format (backward compatible)
    if isinstance(allowed_values, list):
        if len(allowed_values) == 0:
            errors.append(f"Field '{field_path}' allowed_values list is empty")
        return errors

    # Handle enhanced dict format
    if not isinstance(allowed_values, dict):
        errors.append(
            f"Field '{field_path}' allowed_values must be a list or dict, "
            f"got {type(allowed_values).__name__}"
        )
        return errors

    if len(allowed_values) == 0:
        errors.append(f"Field '{field_path}' allowed_values dict is empty")
        return errors

    # Validate each category definition
    precedences_seen = set()
    for category_name, category_def in allowed_values.items():
        if not isinstance(category_def, dict):
            errors.append(
                f"Field '{field_path}' category '{category_name}' must be a dict, "
                f"got {type(category_def).__name__}"
            )
            continue

        # Check required fields
        if "definition" not in category_def:
            errors.append(
                f"Field '{field_path}' category '{category_name}' missing required 'definition'"
            )

        if "precedence" not in category_def:
            errors.append(
                f"Field '{field_path}' category '{category_name}' missing required 'precedence'"
            )
        else:
            precedence = category_def["precedence"]
            if not isinstance(precedence, int):
                errors.append(
                    f"Field '{field_path}' category '{category_name}' precedence must be integer, "
                    f"got {type(precedence).__name__}"
                )
            elif precedence < 1:
                errors.append(
                    f"Field '{field_path}' category '{category_name}' precedence must be >= 1, "
                    f"got {precedence}"
                )
            elif precedence in precedences_seen:
                errors.append(
                    f"Field '{field_path}' category '{category_name}' has duplicate precedence {precedence}"
                )
            else:
                precedences_seen.add(precedence)

        # Validate derivation_rule if present
        if "derivation_rule" in category_def:
            rule = category_def["derivation_rule"]
            if not isinstance(rule, dict):
                errors.append(
                    f"Field '{field_path}' category '{category_name}' derivation_rule must be dict"
                )
            else:
                if "type" not in rule:
                    errors.append(
                        f"Field '{field_path}' category '{category_name}' derivation_rule missing 'type'"
                    )
                if "inputs" not in rule:
                    errors.append(
                        f"Field '{field_path}' category '{category_name}' derivation_rule missing 'inputs'"
                    )
                elif not isinstance(rule["inputs"], list):
                    errors.append(
                        f"Field '{field_path}' category '{category_name}' derivation_rule inputs must be list"
                    )
                if "logic" not in rule:
                    errors.append(
                        f"Field '{field_path}' category '{category_name}' derivation_rule missing 'logic'"
                    )

    return errors


def get_category_values(allowed_values: list[str] | dict[str, Any]) -> list[str]:
    """
    Extract the list of valid category values from either format.

    Args:
        allowed_values: Either simple list or enhanced dict format

    Returns:
        List of valid category value strings

    Example:
        values = get_category_values({"High": {...}, "Low": {...}})
        # Returns: ["High", "Low"]
    """
    if isinstance(allowed_values, list):
        return allowed_values
    elif isinstance(allowed_values, dict):
        return list(allowed_values.keys())
    else:
        return []


def get_categories_by_precedence(
    allowed_values: dict[str, Any],
) -> list[tuple[str, CategoryDefinition]]:
    """
    Get categories sorted by precedence order.

    Args:
        allowed_values: Enhanced dict format allowed_values

    Returns:
        List of (category_name, CategoryDefinition) tuples sorted by precedence

    Example:
        categories = get_categories_by_precedence(risk_level_values)
        for name, definition in categories:
            print(f"{name}: precedence {definition.precedence}")
    """
    if not isinstance(allowed_values, dict):
        return []

    categories = []
    for name, def_dict in allowed_values.items():
        if isinstance(def_dict, dict):
            try:
                category_def = CategoryDefinition.from_dict(def_dict)
                categories.append((name, category_def))
            except (ValueError, KeyError):
                # Skip invalid definitions
                continue

    # Sort by precedence (lower = higher priority)
    categories.sort(key=lambda x: x[1].precedence)
    return categories
