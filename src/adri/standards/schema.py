"""
Schema definition and validation rules for ADRI standards.

This module defines the expected structure, valid values, and constraints
for ADRI standard files, providing the foundation for comprehensive validation.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class FieldSchema:
    """
    Schema definition for a single field.

    Attributes:
        name: Field name
        required: Whether the field is mandatory
        field_type: Expected Python type(s)
        valid_values: Optional set of valid values (for enums)
        min_value: Optional minimum value (for numeric fields)
        max_value: Optional maximum value (for numeric fields)
        description: Field description for error messages
    """

    name: str
    required: bool
    field_type: type | Tuple[type, ...]
    valid_values: Optional[Set[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""


class StandardSchema:
    """
    Complete schema definition for ADRI standard files.

    This class defines all validation rules, constraints, and expected
    structures for ADRI standards.
    """

    # Top-level sections
    REQUIRED_SECTIONS = ["standards", "requirements"]
    OPTIONAL_SECTIONS: List[str] = ["record_identification", "metadata", "dimensions"]

    # Standards section required fields
    STANDARDS_REQUIRED_FIELDS = ["id", "name", "version", "description"]

    # Requirements section required subsections
    REQUIREMENTS_REQUIRED_SUBSECTIONS = ["dimension_requirements", "overall_minimum"]

    # Dimension names that can have requirements
    VALID_DIMENSIONS = {
        "validity",
        "completeness",
        "consistency",
        "freshness",
        "plausibility",
    }

    # At least one dimension must be specified
    MIN_DIMENSIONS_REQUIRED = 1

    # Dimension requirement fields
    DIMENSION_REQUIRED_FIELDS = ["weight"]
    DIMENSION_OPTIONAL_FIELDS = ["minimum_score", "field_requirements"]

    # Weight constraints (0-5 scale)
    WEIGHT_MIN = 0
    WEIGHT_MAX = 5

    # Score constraints (0-100 percentage)
    SCORE_MIN = 0
    SCORE_MAX = 100

    # Field requirement types
    VALID_FIELD_REQUIREMENT_TYPES = {"required", "format", "range", "lookup", "custom"}

    # Field requirement rule types
    VALID_RULE_TYPES = {
        "not_null",
        "not_empty",
        "regex",
        "min_length",
        "max_length",
        "min_value",
        "max_value",
        "in_set",
        "custom_function",
    }

    @classmethod
    def get_standards_section_schema(cls) -> Dict[str, FieldSchema]:
        """
        Get field schema for the 'standards' section.

        Returns:
            Dictionary mapping field names to their schemas
        """
        return {
            "id": FieldSchema(
                name="id",
                required=True,
                field_type=str,
                description="Unique identifier for the standard",
            ),
            "name": FieldSchema(
                name="name",
                required=True,
                field_type=str,
                description="Human-readable name of the standard",
            ),
            "version": FieldSchema(
                name="version",
                required=True,
                field_type=str,
                description="Version string (e.g., '1.0.0')",
            ),
            "description": FieldSchema(
                name="description",
                required=True,
                field_type=str,
                description="Description of the standard's purpose",
            ),
            "author": FieldSchema(
                name="author",
                required=False,
                field_type=str,
                description="Author of the standard",
            ),
            "created": FieldSchema(
                name="created",
                required=False,
                field_type=str,
                description="Creation date (ISO format)",
            ),
            "updated": FieldSchema(
                name="updated",
                required=False,
                field_type=str,
                description="Last update date (ISO format)",
            ),
            "tags": FieldSchema(
                name="tags",
                required=False,
                field_type=list,
                description="List of tags for categorization",
            ),
        }

    @classmethod
    def get_dimension_requirement_schema(cls) -> Dict[str, FieldSchema]:
        """
        Get field schema for dimension requirements.

        Returns:
            Dictionary mapping field names to their schemas
        """
        return {
            "weight": FieldSchema(
                name="weight",
                required=True,
                field_type=(int, float),
                min_value=cls.WEIGHT_MIN,
                max_value=cls.WEIGHT_MAX,
                description="Dimension weight (0-5 scale)",
            ),
            "minimum_score": FieldSchema(
                name="minimum_score",
                required=False,
                field_type=(int, float),
                min_value=cls.SCORE_MIN,
                max_value=cls.SCORE_MAX,
                description="Minimum acceptable score for this dimension (0-100)",
            ),
            "field_requirements": FieldSchema(
                name="field_requirements",
                required=False,
                field_type=dict,
                description="Field-specific validation requirements",
            ),
        }

    @classmethod
    def validate_top_level_structure(cls, standard: Dict[str, Any]) -> List[str]:
        """
        Validate top-level structure of a standard.

        Args:
            standard: Parsed standard dictionary

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check for required sections
        for section in cls.REQUIRED_SECTIONS:
            if section not in standard:
                errors.append(f"Missing required top-level section: '{section}'")

        # Check for unexpected top-level keys
        valid_sections = set(cls.REQUIRED_SECTIONS + cls.OPTIONAL_SECTIONS)
        for key in standard.keys():
            if key not in valid_sections:
                errors.append(
                    f"Unexpected top-level section: '{key}'. "
                    f"Valid sections are: {', '.join(sorted(valid_sections))}"
                )

        return errors

    @classmethod
    def validate_field_type(
        cls, value: Any, expected_type: type | Tuple[type, ...], field_path: str
    ) -> Optional[str]:
        """
        Validate that a field has the expected type.

        Args:
            value: Value to check
            expected_type: Expected type or tuple of types
            field_path: Dot-notation path to field for error messages

        Returns:
            Error message if invalid, None if valid
        """
        if isinstance(expected_type, tuple):
            if not isinstance(value, expected_type):
                type_names = " or ".join(t.__name__ for t in expected_type)
                return (
                    f"Field '{field_path}' has incorrect type. "
                    f"Expected {type_names}, got {type(value).__name__}"
                )
        else:
            if not isinstance(value, expected_type):
                return (
                    f"Field '{field_path}' has incorrect type. "
                    f"Expected {expected_type.__name__}, got {type(value).__name__}"
                )
        return None

    @classmethod
    def validate_numeric_range(
        cls,
        value: float | int,
        min_value: Optional[float],
        max_value: Optional[float],
        field_path: str,
    ) -> Optional[str]:
        """
        Validate that a numeric value is within the expected range.

        Args:
            value: Numeric value to check
            min_value: Minimum allowed value (inclusive)
            max_value: Maximum allowed value (inclusive)
            field_path: Dot-notation path to field for error messages

        Returns:
            Error message if invalid, None if valid
        """
        if min_value is not None and value < min_value:
            return f"Field '{field_path}' value {value} is below minimum {min_value}"

        if max_value is not None and value > max_value:
            return f"Field '{field_path}' value {value} exceeds maximum {max_value}"

        return None

    @classmethod
    def validate_value_in_set(
        cls, value: Any, valid_values: Set[Any], field_path: str
    ) -> Optional[str]:
        """
        Validate that a value is in the set of valid values.

        Args:
            value: Value to check
            valid_values: Set of valid values
            field_path: Dot-notation path to field for error messages

        Returns:
            Error message if invalid, None if valid
        """
        if value not in valid_values:
            return (
                f"Field '{field_path}' has invalid value '{value}'. "
                f"Must be one of: {', '.join(str(v) for v in sorted(valid_values))}"
            )
        return None

    @classmethod
    def get_dimension_names(cls) -> Set[str]:
        """
        Get the set of valid dimension names.

        Returns:
            Set of valid dimension names
        """
        return cls.VALID_DIMENSIONS.copy()

    @classmethod
    def is_valid_dimension(cls, dimension: str) -> bool:
        """
        Check if a dimension name is valid.

        Args:
            dimension: Dimension name to check

        Returns:
            True if valid, False otherwise
        """
        return dimension in cls.VALID_DIMENSIONS

    @classmethod
    def validate_version_string(cls, version: str) -> Optional[str]:
        """
        Validate version string format.

        Args:
            version: Version string to validate

        Returns:
            Error message if invalid, None if valid
        """
        if not version or not isinstance(version, str):
            return "Version must be a non-empty string"

        # Basic semantic versioning check (X.Y.Z or similar)
        parts = version.split(".")
        if len(parts) < 2:
            return (
                f"Version '{version}' does not follow semantic versioning format. "
                "Expected format: 'X.Y.Z' or similar"
            )

        return None

    @classmethod
    def validate_overall_minimum(cls, overall_minimum: Any) -> Optional[str]:
        """
        Validate overall_minimum field.

        Args:
            overall_minimum: Value to validate

        Returns:
            Error message if invalid, None if valid
        """
        # Check type
        if not isinstance(overall_minimum, (int, float)):
            return f"overall_minimum must be a number, got {type(overall_minimum).__name__}"

        # Check range
        return cls.validate_numeric_range(
            overall_minimum,
            cls.SCORE_MIN,
            cls.SCORE_MAX,
            "requirements.overall_minimum",
        )
