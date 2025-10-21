"""Custom exception hierarchy for the ADRI framework.

This module defines a comprehensive set of exceptions that provide clear error
handling and debugging information throughout the ADRI system.
"""


class ADRIError(Exception):
    """Base exception class for all ADRI-related errors.

    All custom ADRI exceptions should inherit from this base class to provide
    consistent error handling and identification.
    """

    def __init__(self, message: str, details: str = None):
        """Initialize the ADRI error.

        Args:
            message: The main error message
            details: Optional additional details about the error
        """
        self.message = message
        self.details = details
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the complete error message."""
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


# Configuration and Setup Errors
class ConfigurationError(ADRIError):
    """Raised when there are configuration-related issues."""


class ProjectNotFoundError(ConfigurationError):
    """Raised when ADRI project root cannot be located."""


class EnvironmentError(ConfigurationError):
    """Raised when there are environment-related configuration issues."""


# Data Loading and Processing Errors
class DataLoadingError(ADRIError):
    """Raised when data cannot be loaded from the specified source."""


class DataFormatError(DataLoadingError):
    """Raised when data is in an unexpected or invalid format."""


class DataValidationError(ADRIError):
    """Raised when data fails validation checks."""


# Backward compatibility alias for tests
ValidationError = DataValidationError


# Standard-Related Errors
class StandardError(ADRIError):
    """Base class for standard-related errors."""


class StandardNotFoundError(StandardError):
    """Raised when a requested standard cannot be found."""


class StandardValidationError(StandardError):
    """Raised when a standard file is invalid or malformed."""


class StandardGenerationError(StandardError):
    """Raised when standard generation fails."""


# Assessment and Validation Errors
class AssessmentError(ADRIError):
    """Base class for assessment-related errors."""


class DimensionAssessmentError(AssessmentError):
    """Raised when a dimension assessment fails."""

    def __init__(self, dimension_name: str, message: str, details: str = None):
        """Initialize dimension assessment error.

        Args:
            dimension_name: The name of the dimension that failed
            message: The main error message
            details: Optional additional details about the error
        """
        self.dimension_name = dimension_name
        formatted_message = (
            f"Assessment failed for dimension '{dimension_name}': {message}"
        )
        super().__init__(formatted_message, details)


class ValidationRuleError(AssessmentError):
    """Raised when a validation rule encounters an error."""

    def __init__(
        self,
        rule_name: str,
        field_name: str = None,
        message: str = "",
        details: str = None,
    ):
        """Initialize validation rule error.

        Args:
            rule_name: The name of the validation rule that failed
            field_name: The field being validated (if applicable)
            message: The main error message
            details: Optional additional details about the error
        """
        self.rule_name = rule_name
        self.field_name = field_name

        if field_name:
            formatted_message = (
                f"Validation rule '{rule_name}' failed for field '{field_name}'"
            )
        else:
            formatted_message = f"Validation rule '{rule_name}' failed"

        if message:
            formatted_message += f": {message}"

        super().__init__(formatted_message, details)


# CLI and Command Errors
class CommandError(ADRIError):
    """Base class for CLI command errors."""


class CommandNotFoundError(CommandError):
    """Raised when a requested command cannot be found."""


class CommandExecutionError(CommandError):
    """Raised when a command fails during execution."""

    def __init__(
        self, command_name: str, exit_code: int, message: str = "", details: str = None
    ):
        """Initialize command execution error.

        Args:
            command_name: The name of the command that failed
            exit_code: The exit code returned by the command
            message: The main error message
            details: Optional additional details about the error
        """
        self.command_name = command_name
        self.exit_code = exit_code

        formatted_message = (
            f"Command '{command_name}' failed with exit code {exit_code}"
        )
        if message:
            formatted_message += f": {message}"

        super().__init__(formatted_message, details)


class ArgumentValidationError(CommandError):
    """Raised when command arguments are invalid."""


# Registry and Component Errors
class RegistryError(ADRIError):
    """Base class for component registry errors."""


class ComponentNotFoundError(RegistryError):
    """Raised when a requested component cannot be found in the registry."""

    def __init__(self, component_type: str, component_name: str, details: str = None):
        """Initialize component not found error.

        Args:
            component_type: The type of component (e.g., 'dimension_assessor', 'command')
            component_name: The name of the component that wasn't found
            details: Optional additional details about the error
        """
        self.component_type = component_type
        self.component_name = component_name

        message = f"{component_type} '{component_name}' not found in registry"
        super().__init__(message, details)


class ComponentRegistrationError(RegistryError):
    """Raised when a component cannot be registered."""


# File and I/O Errors
class FileOperationError(ADRIError):
    """Base class for file operation errors."""


class FileNotFoundError(FileOperationError):
    """Raised when a required file cannot be found."""


class FilePermissionError(FileOperationError):
    """Raised when there are insufficient permissions to access a file."""


class SerializationError(ADRIError):
    """Raised when serialization or deserialization fails."""


# Performance and Resource Errors
class PerformanceError(ADRIError):
    """Raised when performance constraints are violated."""


class ResourceExhaustedError(ADRIError):
    """Raised when system resources are exhausted."""


class TimeoutError(ADRIError):
    """Raised when an operation times out."""


# Utility functions for error handling
def chain_exception(exc: Exception, cause: Exception) -> Exception:
    """Chain exceptions to preserve the original cause.

    Args:
        exc: The new exception to raise
        cause: The original exception that caused this error

    Returns:
        The new exception with the cause chained
    """
    exc.__cause__ = cause
    return exc


def format_validation_errors(errors: list) -> str:
    """Format a list of validation errors into a readable message.

    Args:
        errors: List of validation error messages

    Returns:
        Formatted error message string
    """
    if not errors:
        return "No validation errors"

    if len(errors) == 1:
        return f"Validation error: {errors[0]}"

    formatted_errors = "\n".join(f" - {error}" for error in errors)
    return f"Validation errors:\n{formatted_errors}"
