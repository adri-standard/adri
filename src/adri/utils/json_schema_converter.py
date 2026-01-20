"""ADRI to JSON Schema Converter Utility.

This module provides utilities to convert ADRI field_requirements to JSON Schema
format for structural validation of LLM-generated JSON output.

Key Features:
- Type mapping: ADRI types → JSON Schema types
- Array handling: items, minItems, maxItems
- String constraints: pattern, minLength, maxLength
- Numeric constraints: minimum, maximum
- Enum support: valid_values → enum
- Nullable handling: anyOf with null type

This is a reusable utility for frameworks that need JSON Schema validation
of data against ADRI specifications.
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


# SQL Reserved Words to warn about in field names
SQL_RESERVED_WORDS = {
    "SELECT",
    "FROM",
    "WHERE",
    "ORDER",
    "GROUP",
    "BY",
    "INSERT",
    "UPDATE",
    "DELETE",
    "JOIN",
    "INNER",
    "OUTER",
    "LEFT",
    "RIGHT",
    "FULL",
    "CROSS",
    "CASE",
    "WHEN",
    "THEN",
    "ELSE",
    "END",
    "NULL",
    "TRUE",
    "FALSE",
    "DATE",
    "TIME",
    "TIMESTAMP",
    "USER",
    "COUNT",
    "SUM",
    "AVG",
    "MIN",
    "MAX",
    "DISTINCT",
    "UNION",
    "INTERSECT",
    "EXCEPT",
    "HAVING",
    "AS",
    "ON",
    "CREATE",
    "DROP",
    "ALTER",
    "TABLE",
    "INDEX",
    "VIEW",
    "TRIGGER",
    "PRIMARY",
    "FOREIGN",
    "KEY",
    "REFERENCES",
    "CHECK",
    "UNIQUE",
    "AND",
    "OR",
    "NOT",
    "IN",
    "BETWEEN",
    "LIKE",
    "IS",
    "EXISTS",
}


class ADRIToJSONSchemaConverter:
    """Converts ADRI field_requirements to JSON Schema format."""

    # ADRI type to JSON Schema type mapping
    TYPE_MAPPING = {
        "string": "string",
        "integer": "integer",
        "float": "number",
        "boolean": "boolean",
        "date": "string",  # Dates are ISO strings
        "array": "array",
    }

    def __init__(self, strict_arrays: bool = True):
        """Initialize converter.

        Args:
            strict_arrays: If True, require items definition for array types
        """
        self.strict_arrays = strict_arrays
        self.warnings: List[str] = []

    def convert(self, adri_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ADRI field_requirements to JSON Schema.

        Args:
            adri_spec: ADRI specification with field_requirements

        Returns:
            JSON Schema dictionary

        Raises:
            ValueError: If ADRI spec is invalid or missing required fields
        """
        self.warnings.clear()

        if not adri_spec:
            raise ValueError("ADRI specification cannot be empty")

        if "field_requirements" not in adri_spec:
            raise ValueError("ADRI specification missing 'field_requirements' section")

        field_requirements = adri_spec["field_requirements"]
        if not isinstance(field_requirements, dict):
            raise ValueError("field_requirements must be a dictionary")

        # Build JSON Schema
        json_schema = {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        }

        # Convert each field
        for field_name, field_spec in field_requirements.items():
            try:
                property_schema = self._convert_field(field_name, field_spec)
                json_schema["properties"][field_name] = property_schema

                # Add to required if not nullable
                if not field_spec.get("nullable", False):
                    json_schema["required"].append(field_name)

            except Exception as e:
                logger.error(f"Error converting field '{field_name}': {e}")
                self.warnings.append(
                    f"Failed to convert field '{field_name}': {str(e)}"
                )

        if not json_schema["properties"]:
            raise ValueError("No valid fields found in ADRI specification")

        return json_schema

    def _convert_field(
        self, field_name: str, field_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert single ADRI field to JSON Schema property.

        Args:
            field_name: Name of the field
            field_spec: ADRI field specification

        Returns:
            JSON Schema property definition
        """
        if "type" not in field_spec:
            raise ValueError(f"Field '{field_name}' missing 'type' attribute")

        adri_type = field_spec["type"]
        if adri_type not in self.TYPE_MAPPING:
            raise ValueError(
                f"Field '{field_name}' has invalid type '{adri_type}'. "
                f"Valid types: {list(self.TYPE_MAPPING.keys())}"
            )

        # Start with base type
        property_schema = {"type": self.TYPE_MAPPING[adri_type]}

        # Add description if present
        if "description" in field_spec:
            property_schema["description"] = field_spec["description"]

        # Handle type-specific constraints
        if adri_type == "array":
            self._add_array_constraints(field_name, field_spec, property_schema)
        elif adri_type == "string":
            self._add_string_constraints(field_name, field_spec, property_schema)
        elif adri_type in ["integer", "float"]:
            self._add_numeric_constraints(field_name, field_spec, property_schema)

        # Handle nullable fields
        if field_spec.get("nullable", False):
            property_schema = {"anyOf": [property_schema, {"type": "null"}]}

        return property_schema

    def _add_array_constraints(
        self,
        field_name: str,
        field_spec: Dict[str, Any],
        property_schema: Dict[str, Any],
    ) -> None:
        """Add array-specific constraints to property schema.

        Args:
            field_name: Name of the field
            field_spec: ADRI field specification
            property_schema: JSON Schema property (modified in place)
        """
        # Array items definition (required in strict mode)
        if "items" in field_spec:
            items_spec = field_spec["items"]
            if isinstance(items_spec, dict):
                # Single item type
                property_schema["items"] = self._convert_items_spec(items_spec)
            else:
                self.warnings.append(
                    f"Field '{field_name}': items specification has unexpected format"
                )
        elif self.strict_arrays:
            self.warnings.append(
                f"Field '{field_name}': array type should define 'items' specification"
            )

        # Array length constraints
        if "min_items" in field_spec:
            property_schema["minItems"] = field_spec["min_items"]

        if "max_items" in field_spec:
            property_schema["maxItems"] = field_spec["max_items"]

    def _convert_items_spec(self, items_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Convert array items specification to JSON Schema.

        Args:
            items_spec: ADRI items specification

        Returns:
            JSON Schema items definition
        """
        if "type" not in items_spec:
            return {}  # Default to any type

        item_type = items_spec["type"]
        if item_type not in self.TYPE_MAPPING:
            return {}

        item_schema = {"type": self.TYPE_MAPPING[item_type]}

        # Add string constraints for string items
        if item_type == "string":
            if "min_length" in items_spec:
                item_schema["minLength"] = items_spec["min_length"]
            if "max_length" in items_spec:
                item_schema["maxLength"] = items_spec["max_length"]
            if "pattern" in items_spec:
                item_schema["pattern"] = items_spec["pattern"]

        # Add numeric constraints for numeric items
        elif item_type in ["integer", "float"]:
            if "min_value" in items_spec:
                item_schema["minimum"] = items_spec["min_value"]
            if "max_value" in items_spec:
                item_schema["maximum"] = items_spec["max_value"]

        return item_schema

    def _add_string_constraints(
        self,
        field_name: str,
        field_spec: Dict[str, Any],
        property_schema: Dict[str, Any],
    ) -> None:
        """Add string-specific constraints to property schema.

        Args:
            field_name: Name of the field
            field_spec: ADRI field specification
            property_schema: JSON Schema property (modified in place)
        """
        # Pattern constraint
        if "pattern" in field_spec:
            property_schema["pattern"] = field_spec["pattern"]

        # Length constraints
        if "min_length" in field_spec:
            property_schema["minLength"] = field_spec["min_length"]

        if "max_length" in field_spec:
            property_schema["maxLength"] = field_spec["max_length"]

        # Enum constraint
        if "valid_values" in field_spec:
            valid_values = field_spec["valid_values"]
            if isinstance(valid_values, list) and valid_values:
                property_schema["enum"] = valid_values

    def _add_numeric_constraints(
        self,
        field_name: str,
        field_spec: Dict[str, Any],
        property_schema: Dict[str, Any],
    ) -> None:
        """Add numeric-specific constraints to property schema.

        Args:
            field_name: Name of the field
            field_spec: ADRI field specification
            property_schema: JSON Schema property (modified in place)
        """
        # Range constraints
        if "min_value" in field_spec:
            property_schema["minimum"] = field_spec["min_value"]

        if "max_value" in field_spec:
            property_schema["maximum"] = field_spec["max_value"]

        # Enum constraint (for numeric enums)
        if "valid_values" in field_spec:
            valid_values = field_spec["valid_values"]
            if isinstance(valid_values, list) and valid_values:
                property_schema["enum"] = valid_values

    def get_warnings(self) -> List[str]:
        """Get conversion warnings.

        Returns:
            List of warning messages
        """
        return self.warnings.copy()


def convert_adri_to_json_schema(
    adri_spec: Dict[str, Any], strict_arrays: bool = True
) -> Dict[str, Any]:
    """Convert ADRI field_requirements to JSON Schema.

    Convenience function for one-off conversions.

    Args:
        adri_spec: ADRI specification with field_requirements
        strict_arrays: If True, warn if array types lack items definition

    Returns:
        JSON Schema dictionary

    Raises:
        ValueError: If ADRI spec is invalid
    """
    converter = ADRIToJSONSchemaConverter(strict_arrays=strict_arrays)
    json_schema = converter.convert(adri_spec)

    # Log warnings
    warnings = converter.get_warnings()
    if warnings:
        logger.warning(
            f"ADRI to JSON Schema conversion produced {len(warnings)} warnings:"
        )
        for warning in warnings:
            logger.warning(f"  - {warning}")

    return json_schema
