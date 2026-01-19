"""
Exception classes and result types for ADRI standard validation.

This module provides structured exception types and result containers for
validating ADRI standard files, enabling clear error reporting and programmatic
handling of validation outcomes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """
    Represents a single validation error or warning.

    Attributes:
        message: Human-readable error description
        path: Dot-notation path to the problematic field (e.g., "requirements.dimension_requirements.validity.weight")
        severity: Severity level of the issue
        expected: Optional description of expected value/format
        actual: Optional description of actual value found
        suggestion: Optional suggestion for fixing the issue
    """

    message: str
    path: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    expected: str | None = None
    actual: str | None = None
    suggestion: str | None = None

    def __str__(self) -> str:
        """Format error as human-readable string."""
        parts = [f"[{self.severity.value.upper()}] {self.path}: {self.message}"]

        if self.expected:
            parts.append(f"  Expected: {self.expected}")

        if self.actual:
            parts.append(f"  Actual: {self.actual}")

        if self.suggestion:
            parts.append(f"  Suggestion: {self.suggestion}")

        return "\n".join(parts)


@dataclass
class ValidationWarning(ValidationError):
    """Convenience class for warnings (severity automatically set to WARNING)."""

    def __post_init__(self):
        """Ensure severity is set to WARNING."""
        self.severity = ValidationSeverity.WARNING


@dataclass
class ValidationResult:
    """
    Container for validation results.

    Attributes:
        is_valid: Whether the standard passed validation
        errors: List of validation errors found
        warnings: List of validation warnings found
        standard_path: Path to the validated standard file
        metadata: Optional metadata about the validation process
    """

    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)
    standard_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        """Check if any errors were found."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings were found."""
        return len(self.warnings) > 0

    @property
    def error_count(self) -> int:
        """Get total number of errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Get total number of warnings."""
        return len(self.warnings)

    def add_error(self, message: str, path: str, **kwargs) -> None:
        """
        Add a validation error.

        Args:
            message: Error description
            path: Path to problematic field
            **kwargs: Additional ValidationError parameters
        """
        self.errors.append(
            ValidationError(
                message=message, path=path, severity=ValidationSeverity.ERROR, **kwargs
            )
        )
        self.is_valid = False

    def add_warning(self, message: str, path: str, **kwargs) -> None:
        """
        Add a validation warning.

        Args:
            message: Warning description
            path: Path to field
            **kwargs: Additional ValidationError parameters
        """
        self.warnings.append(
            ValidationError(
                message=message,
                path=path,
                severity=ValidationSeverity.WARNING,
                **kwargs,
            )
        )

    def format_errors(self) -> str:
        """Format all errors as a readable string."""
        if not self.has_errors:
            return "No errors found."

        lines = [f"Found {self.error_count} error(s):"]
        for error in self.errors:
            lines.append(str(error))
            lines.append("")  # Blank line between errors

        return "\n".join(lines)

    def format_warnings(self) -> str:
        """Format all warnings as a readable string."""
        if not self.has_warnings:
            return "No warnings found."

        lines = [f"Found {self.warning_count} warning(s):"]
        for warning in self.warnings:
            lines.append(str(warning))
            lines.append("")  # Blank line between warnings

        return "\n".join(lines)

    def format_summary(self) -> str:
        """
        Return a formatted summary of validation results.

        Returns:
            Multi-line string with validation summary
        """
        lines = []

        if self.standard_path:
            lines.append(f"Standard: {self.standard_path}")

        lines.append(f"Status: {'VALID' if self.is_valid else 'INVALID'}")
        lines.append(f"Errors: {self.error_count}")
        lines.append(f"Warnings: {self.warning_count}")

        if self.has_errors:
            lines.append("")
            lines.append(self.format_errors())

        if self.has_warnings:
            lines.append("")
            lines.append(self.format_warnings())

        return "\n".join(lines)

    def __str__(self) -> str:
        """String representation showing summary."""
        return self.format_summary()


class SchemaValidationError(Exception):
    """
    Exception raised when a standard fails schema validation.

    This exception includes structured validation results that can be
    programmatically inspected to understand what failed.

    Attributes:
        message: Human-readable error message
        validation_result: Detailed validation results
        standard_path: Path to the invalid standard file
    """

    def __init__(
        self,
        message: str,
        validation_result: ValidationResult | None = None,
        standard_path: str | None = None,
    ):
        """
        Initialize schema validation error.

        Args:
            message: Error message
            validation_result: Optional validation result details
            standard_path: Optional path to standard file
        """
        super().__init__(message)
        self.validation_result = validation_result
        self.standard_path = standard_path

    def __str__(self) -> str:
        """Return string representation with exception details."""
        parts = [super().__str__()]

        if self.standard_path:
            parts.append(f"\nStandard: {self.standard_path}")

        if self.validation_result:
            parts.append("\nValidation Details:")
            parts.append(self.validation_result.format_summary())

        return "\n".join(parts)


class InvalidStandardError(SchemaValidationError):
    """Raise exception when standard file is structurally invalid."""


class MissingRequiredFieldError(SchemaValidationError):
    """Raised when a required field is missing from the standard."""


class InvalidFieldTypeError(SchemaValidationError):
    """Raised when a field has an incorrect type."""


class InvalidFieldValueError(SchemaValidationError):
    """Raised when a field value is outside valid range or set."""
