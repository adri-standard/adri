"""Severity levels for validation rules.

This module defines the severity levels that can be assigned to validation rules,
controlling whether rule failures affect dimension scores or are logged only.
"""

from enum import Enum


class Severity(str, Enum):
    """Validation rule severity levels.

    Severity determines how validation rule failures are handled:

    - CRITICAL: Failures reduce dimension scores (default for most rules)
    - WARNING: Failures are logged but don't affect scores (e.g., style issues)
    - INFO: Informational only, minimal logging (future use)

    Examples:
        >>> rule = ValidationRule(
        ...     name="Email required",
        ...     severity=Severity.CRITICAL,
        ...     ...
        ... )
        >>> rule.severity == Severity.CRITICAL
        True

        >>> format_rule = ValidationRule(
        ...     name="Lowercase preference",
        ...     severity=Severity.WARNING,
        ...     ...
        ... )
        >>> format_rule.should_penalize_score()
        False
    """

    CRITICAL = "CRITICAL"  # Reduces dimension score when rule fails
    WARNING = "WARNING"  # Logged only, no score impact
    INFO = "INFO"  # Informational only, minimal logging

    def __str__(self) -> str:
        """Return the string value of the severity level."""
        return self.value

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """Create Severity from string value.

        Args:
            value: String representation (e.g., "CRITICAL", "WARNING", "INFO")

        Returns:
            Severity enum instance

        Raises:
            ValueError: If value is not a valid severity level

        Examples:
            >>> Severity.from_string("CRITICAL")
            <Severity.CRITICAL: 'CRITICAL'>
            >>> Severity.from_string("invalid")
            Traceback (most recent call last):
                ...
            ValueError: Invalid severity level: 'invalid'. Must be one of: CRITICAL, WARNING, INFO
        """
        try:
            return cls(value.upper())
        except ValueError:
            valid_values = ", ".join([s.value for s in cls])
            raise ValueError(
                f"Invalid severity level: '{value}'. Must be one of: {valid_values}"
            )

    def should_penalize_score(self) -> bool:
        """Determine if this severity level should affect dimension scores.

        Returns:
            True if CRITICAL (affects score), False otherwise

        Examples:
            >>> Severity.CRITICAL.should_penalize_score()
            True
            >>> Severity.WARNING.should_penalize_score()
            False
            >>> Severity.INFO.should_penalize_score()
            False
        """
        return self == Severity.CRITICAL
