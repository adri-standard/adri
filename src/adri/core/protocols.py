"""Core protocols and interfaces for the ADRI framework.

This module defines the fundamental protocols and abstract base classes that establish
the architectural contracts for validation rules, dimension assessors, CLI commands,
and other core components.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol


class ValidationRule(Protocol):
    """Protocol for individual validation rules.

    Defines the interface that all validation rules must implement to ensure
    consistent behavior across the validation system.
    """

    def validate(self, value: Any, context: dict[str, Any]) -> bool:
        """Validate a value against this rule.

        Args:
            value: The value to validate
            context: Additional context information for validation

        Returns:
            True if the value passes validation, False otherwise
        """
        ...

    def get_error_message(self, value: Any) -> str:
        """Get a human-readable error message for a failed validation.

        Args:
            value: The value that failed validation

        Returns:
            A descriptive error message explaining why validation failed
        """
        ...


class DimensionAssessor(ABC):
    """Base class for dimension-specific assessors.

    Each data quality dimension (validity, completeness, consistency, freshness,
    plausibility) has its own assessor that implements this interface.
    """

    @abstractmethod
    def assess(self, data: Any, requirements: dict[str, Any]) -> float:
        """Assess the quality dimension for the given data.

        Args:
            data: The data to assess (typically a pandas DataFrame)
            requirements: The dimension-specific requirements from the standard

        Returns:
            A score between 0.0 and 20.0 representing the dimension quality
        """
        ...

    @abstractmethod
    def get_dimension_name(self) -> str:
        """Get the name of this dimension.

        Returns:
            The dimension name (e.g., "validity", "completeness")
        """
        ...

    def get_weight(self, requirements: dict[str, Any]) -> float:
        """Get the weight for this dimension from requirements.

        Args:
            requirements: The dimension-specific requirements

        Returns:
            The weight to apply to this dimension's score
        """
        return requirements.get("weight", 1.0)

    def get_minimum_score(self, requirements: dict[str, Any]) -> float:
        """Get the minimum acceptable score for this dimension.

        Args:
            requirements: The dimension-specific requirements

        Returns:
            The minimum score threshold for this dimension
        """
        return requirements.get("minimum_score", 15.0)


class Command(ABC):
    """Base class for CLI commands.

    Each CLI command implements this interface to ensure consistent behavior
    and enable the command registry pattern.
    """

    @abstractmethod
    def execute(self, args: dict[str, Any]) -> int:
        """Execute the command with the given arguments.

        Args:
            args: Command-line arguments and options

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        ...

    @abstractmethod
    def get_description(self) -> str:
        """Get a description of what this command does.

        Returns:
            A brief description for help text
        """
        ...

    def get_name(self) -> str:
        """Get the name of this command.

        By default, uses the class name with 'Command' suffix removed.
        Can be overridden for custom command names.

        Returns:
            The command name as it should appear in CLI
        """
        class_name = self.__class__.__name__
        if class_name.endswith("Command"):
            return class_name[:-7].lower().replace("_", "-")
        return class_name.lower()


class DataLoader(Protocol):
    """Protocol for data loading implementations.

    Defines the interface for loading data from various file formats.
    """

    def load(self, file_path: str) -> list[dict[str, Any]]:
        """Load data from a file.

        Args:
            file_path: Path to the data file

        Returns:
            List of records as dictionaries
        """
        ...

    def get_supported_formats(self) -> list[str]:
        """Get the file formats supported by this loader.

        Returns:
            List of supported file extensions (e.g., ['.csv', '.json'])
        """
        ...


class StandardLoader(Protocol):
    """Protocol for standard loading implementations.

    Defines the interface for loading ADRI standards from various sources.
    """

    def load(self, source: str) -> dict[str, Any]:
        """Load a standard from the given source.

        Args:
            source: Path to standard file or other source identifier

        Returns:
            Standard as a dictionary
        """
        ...

    def validate_standard(self, standard: dict[str, Any]) -> list[str]:
        """Validate that a standard has the required structure.

        Args:
            standard: The standard dictionary to validate

        Returns:
            List of validation errors (empty if valid)
        """
        ...


class ResultSerializer(Protocol):
    """Protocol for result serialization implementations.

    Defines the interface for serializing assessment results to various formats.
    """

    def serialize(self, result: Any) -> str:
        """Serialize an assessment result.

        Args:
            result: The assessment result to serialize

        Returns:
            Serialized result as a string
        """
        ...

    def get_format_name(self) -> str:
        """Get the name of the output format.

        Returns:
            Format name (e.g., "json", "yaml", "xml")
        """
        ...
