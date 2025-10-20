"""Validation rule data structure.

This module defines the ValidationRule dataclass that represents individual
validation rules with explicit severity levels.
"""

from dataclasses import dataclass
from typing import Any

from .severity import Severity


@dataclass
class ValidationRule:
    """Represents a single validation rule within a field requirement.

    Each validation rule specifies:
    - What is being validated (name, rule_type, rule_expression)
    - Which dimension it belongs to (validity, completeness, etc.)
    - How failures are handled (severity: CRITICAL, WARNING, INFO)
    - Optional metadata (error_message, remediation, penalty_weight)

    Attributes:
        name: Descriptive name for the rule (e.g., "Email format validation")
        dimension: Quality dimension (validity, completeness, consistency, freshness, plausibility)
        severity: How failures are handled (CRITICAL reduces score, WARNING logs only)
        rule_type: Type of validation (type, allowed_values, pattern, not_null, etc.)
        rule_expression: Logic expression for validation (e.g., "IS_NOT_NULL", "REGEX_MATCH(...)")
        error_message: Optional custom error message for failures
        remediation: Optional guidance for fixing failures
        penalty_weight: Weight for CRITICAL rules (default 1.0)

    Examples:
        >>> rule = ValidationRule(
        ...     name="Email required",
        ...     dimension="completeness",
        ...     severity=Severity.CRITICAL,
        ...     rule_type="not_null",
        ...     rule_expression="IS_NOT_NULL"
        ... )
        >>> rule.should_penalize_score()
        True

        >>> format_rule = ValidationRule(
        ...     name="Lowercase preference",
        ...     dimension="consistency",
        ...     severity=Severity.WARNING,
        ...     rule_type="format",
        ...     rule_expression="IS_LOWERCASE",
        ...     error_message="Field should be lowercase"
        ... )
        >>> format_rule.should_penalize_score()
        False
    """

    name: str
    dimension: str
    severity: Severity
    rule_type: str
    rule_expression: str
    error_message: str | None = None
    remediation: str | None = None
    penalty_weight: float = 1.0

    def __post_init__(self):
        """Validate and normalize fields after initialization."""
        # Convert string severity to Severity enum if needed
        if isinstance(self.severity, str):
            self.severity = Severity.from_string(self.severity)

        # Validate dimension
        valid_dimensions = {
            "validity",
            "completeness",
            "consistency",
            "freshness",
            "plausibility",
        }
        if self.dimension not in valid_dimensions:
            raise ValueError(
                f"Invalid dimension: '{self.dimension}'. "
                f"Must be one of: {', '.join(sorted(valid_dimensions))}"
            )

        # Validate penalty_weight
        if self.penalty_weight < 0:
            raise ValueError(f"penalty_weight must be >= 0, got {self.penalty_weight}")

    @classmethod
    def from_dict(cls, rule_dict: dict[str, Any]) -> "ValidationRule":
        """Create ValidationRule from dictionary (YAML parsing).

        Args:
            rule_dict: Dictionary with rule fields

        Returns:
            ValidationRule instance

        Raises:
            ValueError: If required fields are missing
            KeyError: If dictionary structure is invalid

        Examples:
            >>> rule_data = {
            ...     "name": "Email required",
            ...     "dimension": "completeness",
            ...     "severity": "CRITICAL",
            ...     "rule_type": "not_null",
            ...     "rule_expression": "IS_NOT_NULL"
            ... }
            >>> rule = ValidationRule.from_dict(rule_data)
            >>> rule.name
            'Email required'
            >>> rule.severity
            <Severity.CRITICAL: 'CRITICAL'>
        """
        # Required fields
        required_fields = [
            "name",
            "dimension",
            "severity",
            "rule_type",
            "rule_expression",
        ]
        missing_fields = [f for f in required_fields if f not in rule_dict]
        if missing_fields:
            raise ValueError(
                f"Missing required fields in validation rule: {', '.join(missing_fields)}"
            )

        # Extract fields with defaults for optional ones
        return cls(
            name=rule_dict["name"],
            dimension=rule_dict["dimension"],
            severity=rule_dict["severity"],  # Will be converted in __post_init__
            rule_type=rule_dict["rule_type"],
            rule_expression=rule_dict["rule_expression"],
            error_message=rule_dict.get("error_message"),
            remediation=rule_dict.get("remediation"),
            penalty_weight=rule_dict.get("penalty_weight", 1.0),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert ValidationRule to dictionary for serialization.

        Returns:
            Dictionary representation suitable for YAML/JSON

        Examples:
            >>> rule = ValidationRule(
            ...     name="Email required",
            ...     dimension="completeness",
            ...     severity=Severity.CRITICAL,
            ...     rule_type="not_null",
            ...     rule_expression="IS_NOT_NULL"
            ... )
            >>> rule_dict = rule.to_dict()
            >>> rule_dict["severity"]
            'CRITICAL'
            >>> "error_message" in rule_dict
            False
        """
        result = {
            "name": self.name,
            "dimension": self.dimension,
            "severity": self.severity.value,
            "rule_type": self.rule_type,
            "rule_expression": self.rule_expression,
        }

        # Include optional fields only if set
        if self.error_message is not None:
            result["error_message"] = self.error_message
        if self.remediation is not None:
            result["remediation"] = self.remediation
        if self.penalty_weight != 1.0:
            result["penalty_weight"] = self.penalty_weight

        return result

    def should_penalize_score(self) -> bool:
        """Determine if this rule should affect dimension scores when it fails.

        Returns:
            True if severity is CRITICAL (affects score), False otherwise

        Examples:
            >>> critical_rule = ValidationRule(
            ...     name="Required field",
            ...     dimension="completeness",
            ...     severity=Severity.CRITICAL,
            ...     rule_type="not_null",
            ...     rule_expression="IS_NOT_NULL"
            ... )
            >>> critical_rule.should_penalize_score()
            True

            >>> warning_rule = ValidationRule(
            ...     name="Format preference",
            ...     dimension="consistency",
            ...     severity=Severity.WARNING,
            ...     rule_type="format",
            ...     rule_expression="IS_LOWERCASE"
            ... )
            >>> warning_rule.should_penalize_score()
            False
        """
        return self.severity.should_penalize_score()

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"ValidationRule(name='{self.name}', dimension='{self.dimension}', "
            f"severity={self.severity}, rule_type='{self.rule_type}')"
        )
