"""
Schema definition and validation rules for ADRI standards.

This module defines the expected structure, valid values, and constraints
for ADRI standard files, providing the foundation for comprehensive validation.
"""

from dataclasses import dataclass
from typing import Any, List, Dict, Union

from .derivation import validate_enhanced_allowed_values, get_category_values


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
    field_type: type | tuple[type, ...]
    valid_values: set[Any] | None = None
    min_value: float | None = None
    max_value: float | None = None
    description: str = ""


class StandardSchema:
    """
    Complete schema definition for ADRI standard files.

    This class defines all validation rules, constraints, and expected
    structures for ADRI standards.
    """

    # Top-level sections
    REQUIRED_SECTIONS = ["contracts", "requirements"]
    OPTIONAL_SECTIONS: list[str] = ["record_identification", "metadata", "dimensions"]

    # Contracts section required fields
    CONTRACTS_REQUIRED_FIELDS = ["id", "name", "version", "description"]

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

    # Validation rule severity levels (new format)
    VALID_SEVERITY_LEVELS = {"CRITICAL", "WARNING", "INFO"}

    # Required fields for ValidationRule objects (new format)
    REQUIRED_VALIDATION_RULE_FIELDS = [
        "name",
        "dimension",
        "severity",
        "rule_type",
        "rule_expression",
    ]

    # Valid rule types per dimension for validation_rules
    VALID_RULE_TYPES_BY_DIMENSION = {
        "validity": {
            "type",
            "allowed_values",
            "pattern",
            "numeric_bounds",
            "date_bounds",
            "length_bounds",
            "custom",
        },
        "completeness": {"not_null", "not_empty", "required_fields"},
        "consistency": {"format", "case", "uniqueness", "cross_field", "primary_key"},
        "freshness": {"age_check", "recency", "staleness"},
        "plausibility": {
            "range_check",
            "categorical_frequency",
            "statistical_outlier",
            "business_rule",
        },
    }

    @classmethod
    def get_contracts_section_schema(cls) -> dict[str, FieldSchema]:
        """
        Get field schema for the 'contracts' section.

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
    def get_dimension_requirement_schema(cls) -> dict[str, FieldSchema]:
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
    def validate_top_level_structure(cls, standard: dict[str, Any]) -> list[str]:
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
        cls, value: Any, expected_type: type | tuple[type, ...], field_path: str
    ) -> str | None:
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
        min_value: float | None,
        max_value: float | None,
        field_path: str,
    ) -> str | None:
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
        cls, value: Any, valid_values: set[Any], field_path: str
    ) -> str | None:
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
    def get_dimension_names(cls) -> set[str]:
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
    def validate_version_string(cls, version: str) -> str | None:
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
    def validate_overall_minimum(cls, overall_minimum: Any) -> str | None:
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

    @classmethod
    def validate_validation_rule(
        cls, rule: dict[str, Any], field_path: str
    ) -> list[str]:
        """
        Validate a single validation rule structure (new format).

        Args:
            rule: Validation rule dictionary
            field_path: Path to the field containing this rule (for error messages)

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check required fields
        for required_field in cls.REQUIRED_VALIDATION_RULE_FIELDS:
            if required_field not in rule:
                errors.append(
                    f"Validation rule at '{field_path}' is missing required field: '{required_field}'"
                )

        # If missing required fields, return early
        if errors:
            return errors

        # Validate severity
        severity = rule.get("severity")
        if severity not in cls.VALID_SEVERITY_LEVELS:
            errors.append(
                f"Validation rule '{rule.get('name')}' at '{field_path}' has invalid severity: '{severity}'. "
                f"Must be one of: {', '.join(sorted(cls.VALID_SEVERITY_LEVELS))}"
            )

        # Validate dimension
        dimension = rule.get("dimension")
        if dimension not in cls.VALID_DIMENSIONS:
            errors.append(
                f"Validation rule '{rule.get('name')}' at '{field_path}' has invalid dimension: '{dimension}'. "
                f"Must be one of: {', '.join(sorted(cls.VALID_DIMENSIONS))}"
            )

        # Validate rule_type for the dimension
        rule_type = rule.get("rule_type")
        if dimension in cls.VALID_RULE_TYPES_BY_DIMENSION:
            valid_types = cls.VALID_RULE_TYPES_BY_DIMENSION[dimension]
            if rule_type not in valid_types:
                errors.append(
                    f"Validation rule '{rule.get('name')}' at '{field_path}' has invalid rule_type '{rule_type}' "
                    f"for dimension '{dimension}'. Valid types: {', '.join(sorted(valid_types))}"
                )

        # Validate optional penalty_weight if present
        if "penalty_weight" in rule:
            penalty_weight = rule["penalty_weight"]
            if not isinstance(penalty_weight, (int, float)):
                errors.append(
                    f"Validation rule '{rule.get('name')}' at '{field_path}' has invalid penalty_weight type. "
                    f"Expected number, got {type(penalty_weight).__name__}"
                )
            elif penalty_weight < 0:
                errors.append(
                    f"Validation rule '{rule.get('name')}' at '{field_path}' has negative penalty_weight: {penalty_weight}"
                )

        return errors

    @classmethod
    def validate_validation_rules_list(
        cls, rules: list[dict[str, Any]], field_path: str
    ) -> list[str]:
        """
        Validate a list of validation rules (new format).

        Args:
            rules: List of validation rule dictionaries
            field_path: Path to the field containing these rules (for error messages)

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if not isinstance(rules, list):
            errors.append(
                f"validation_rules at '{field_path}' must be a list, got {type(rules).__name__}"
            )
            return errors

        if len(rules) == 0:
            errors.append(
                f"validation_rules at '{field_path}' is empty. At least one rule is required."
            )
            return errors

        # Validate each rule
        for idx, rule in enumerate(rules):
            if not isinstance(rule, dict):
                errors.append(
                    f"Validation rule #{idx + 1} at '{field_path}' must be a dictionary, "
                    f"got {type(rule).__name__}"
                )
                continue

            rule_errors = cls.validate_validation_rule(rule, f"{field_path}[{idx}]")
            errors.extend(rule_errors)

        return errors

    @classmethod
    def validate_field_requirement(
        cls, field_name: str, field_req: dict[str, Any], field_path: str
    ) -> list[str]:
        """
        Validate a field requirement structure, including enhanced allowed_values.

        Args:
            field_name: Name of the field
            field_req: Field requirement dictionary
            field_path: Path to the field for error messages

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if not isinstance(field_req, dict):
            errors.append(
                f"Field requirement for '{field_name}' at '{field_path}' must be a dict, "
                f"got {type(field_req).__name__}"
            )
            return errors

        # Validate enhanced allowed_values if present
        if "allowed_values" in field_req:
            allowed_values = field_req["allowed_values"]
            # Use the derivation module's validation function
            av_errors = validate_enhanced_allowed_values(
                allowed_values, f"{field_path}.{field_name}"
            )
            errors.extend(av_errors)

        # Validate is_derived flag if present
        if "is_derived" in field_req:
            is_derived = field_req["is_derived"]
            if not isinstance(is_derived, bool):
                errors.append(
                    f"Field '{field_name}' at '{field_path}' has invalid is_derived type. "
                    f"Expected bool, got {type(is_derived).__name__}"
                )

            # If is_derived is true, enhanced allowed_values should be present
            if is_derived and "allowed_values" not in field_req:
                errors.append(
                    f"Field '{field_name}' at '{field_path}' is marked as is_derived=true "
                    "but has no allowed_values definition"
                )

            # If is_derived is true and allowed_values is present, it should be enhanced format
            if is_derived and "allowed_values" in field_req:
                allowed_values = field_req["allowed_values"]
                if isinstance(allowed_values, list):
                    errors.append(
                        f"Field '{field_name}' at '{field_path}' is marked as is_derived=true "
                        "but allowed_values is in simple list format. Expected enhanced dict format."
                    )

        return errors

    @classmethod
    def validate_field_requirements_section(
        cls, field_requirements: dict[str, Any], section_path: str
    ) -> list[str]:
        """
        Validate the field_requirements section of a standard.

        Args:
            field_requirements: Dictionary of field requirements
            section_path: Path to the section for error messages

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if not isinstance(field_requirements, dict):
            errors.append(
                f"field_requirements at '{section_path}' must be a dict, "
                f"got {type(field_requirements).__name__}"
            )
            return errors

        # Validate each field requirement
        for field_name, field_req in field_requirements.items():
            field_errors = cls.validate_field_requirement(
                field_name, field_req, section_path
            )
            errors.extend(field_errors)

        return errors

    @classmethod
    def get_allowed_values_as_list(
        cls, allowed_values: Union[List[str], Dict[str, Any]]
    ) -> List[str]:
        """
        Extract valid category values from either simple or enhanced format.

        Args:
            allowed_values: Either list or enhanced dict format

        Returns:
            List of valid category value strings
        """
        return get_category_values(allowed_values)
