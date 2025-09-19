"""
ADRI Validation Rules.

Field-level validation logic extracted from the original AssessmentEngine.
Contains functions for type checking, pattern matching, and range validation.
"""

from typing import Any, Dict


def check_field_type(value: Any, field_req: Dict[str, Any]) -> bool:
    """Check if value matches the required type."""
    required_type = field_req.get("type", "string")

    try:
        if required_type == "integer":
            int(value)
            return True
        elif required_type == "float":
            float(value)
            return True
        elif required_type == "string":
            return isinstance(value, str)
        elif required_type == "boolean":
            return isinstance(value, bool) or str(value).lower() in [
                "true",
                "false",
                "1",
                "0",
            ]
        elif required_type == "date":
            # Basic date validation
            import re

            date_patterns = [
                r"^\d{4}-\d{2}-\d{2}$",  # YYYY-MM-DD
                r"^\d{2}/\d{2}/\d{4}$",  # MM/DD/YYYY
            ]
            return any(re.match(pattern, str(value)) for pattern in date_patterns)
    except Exception:
        return False

    return True


def check_field_pattern(value: Any, field_req: Dict[str, Any]) -> bool:
    """Check if value matches the required pattern (e.g., email regex)."""
    pattern = field_req.get("pattern")
    if not pattern:
        return True

    try:
        import re

        return bool(re.match(pattern, str(value)))
    except Exception:
        return False


def check_field_range(value: Any, field_req: Dict[str, Any]) -> bool:
    """Check if value is within the required range."""
    try:
        numeric_value = float(value)

        min_val = field_req.get("min_value")
        max_val = field_req.get("max_value")

        if min_val is not None and numeric_value < min_val:
            return False

        if max_val is not None and numeric_value > max_val:
            return False

        return True
    except Exception:
        # Not a numeric value, skip range check
        return True


def check_primary_key_uniqueness(data, standard_config):
    """
    Check for duplicate primary key values in the dataset.

    Args:
        data: DataFrame containing the data to validate
        standard_config: Standard configuration dictionary

    Returns:
        List of validation failures for duplicate primary keys
    """
    import pandas as pd

    failures = []

    # Get primary key configuration from standard
    record_id_config = standard_config.get("record_identification", {})
    primary_key_fields = record_id_config.get("primary_key_fields", [])

    if not primary_key_fields:
        return failures  # No primary key defined, skip check

    # Check if all primary key fields exist in data
    missing_pk_fields = [
        field for field in primary_key_fields if field not in data.columns
    ]
    if missing_pk_fields:
        return failures  # Can't validate if primary key fields don't exist

    # Create composite key for uniqueness checking
    if len(primary_key_fields) == 1:
        # Single primary key
        pk_field = primary_key_fields[0]
        duplicates = data[data.duplicated(subset=[pk_field], keep=False)]

        if not duplicates.empty:
            # Group duplicates by value
            duplicate_groups = duplicates.groupby(pk_field)

            for pk_value, group in duplicate_groups:
                if pd.isna(pk_value):
                    continue  # Skip null primary keys

                duplicate_record_ids = []
                for idx in group.index:
                    record_id = f"{pk_value} (Row {idx + 1})"
                    duplicate_record_ids.append(record_id)

                if len(duplicate_record_ids) > 1:
                    failures.append(
                        {
                            "validation_id": f"pk_dup_{pk_value}".replace(" ", "_"),
                            "dimension": "consistency",
                            "field": pk_field,
                            "issue": "duplicate_primary_key",
                            "affected_rows": len(duplicate_record_ids),
                            "affected_percentage": (
                                len(duplicate_record_ids) / len(data)
                            )
                            * 100,
                            "samples": duplicate_record_ids,
                            "remediation": f"Remove duplicate {pk_field} values: {pk_value}",
                        }
                    )
    else:
        # Compound primary key
        duplicates = data[data.duplicated(subset=primary_key_fields, keep=False)]

        if not duplicates.empty:
            # Group duplicates by compound key
            duplicate_groups = duplicates.groupby(primary_key_fields)

            for pk_values, group in duplicate_groups:
                # Create compound key string
                if isinstance(pk_values, tuple):
                    pk_str = ":".join(str(v) for v in pk_values if pd.notna(v))
                else:
                    pk_str = str(pk_values)

                duplicate_record_ids = []
                for idx in group.index:
                    record_id = f"{pk_str} (Row {idx + 1})"
                    duplicate_record_ids.append(record_id)

                if len(duplicate_record_ids) > 1:
                    failures.append(
                        {
                            "validation_id": f"pk_dup_{pk_str}".replace(
                                " ", "_"
                            ).replace(":", "_"),
                            "dimension": "consistency",
                            "field": ",".join(primary_key_fields),
                            "issue": "duplicate_compound_key",
                            "affected_rows": len(duplicate_record_ids),
                            "affected_percentage": (
                                len(duplicate_record_ids) / len(data)
                            )
                            * 100,
                            "samples": duplicate_record_ids,
                            "remediation": f"Remove duplicate compound key values: {pk_str}",
                        }
                    )

    return failures


def validate_field(
    field_name: str, value: Any, field_requirements: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate a single field value against its requirements.

    Args:
        field_name: Name of the field being validated
        value: The value to validate
        field_requirements: Dictionary of field requirements

    Returns:
        Dictionary containing validation result with details
    """
    result = {
        "field": field_name,
        "value": value,
        "passed": True,
        "errors": [],
        "warnings": [],
    }

    if field_name not in field_requirements:
        # No requirements defined for this field
        return result

    field_req = field_requirements[field_name]

    # Check if field is nullable and value is null
    nullable = field_req.get("nullable", True)
    if not nullable and (value is None or str(value).strip() == ""):
        result["passed"] = False
        result["errors"].append("Field is required but value is null/empty")
        return result

    # If value is null and field is nullable, skip other checks
    if value is None or str(value).strip() == "":
        return result

    # Type validation
    if not check_field_type(value, field_req):
        result["passed"] = False
        result["errors"].append(
            f"Value does not match required type: {field_req.get('type', 'string')}"
        )

    # Pattern validation
    if not check_field_pattern(value, field_req):
        result["passed"] = False
        result["errors"].append(
            f"Value does not match required pattern: {field_req.get('pattern', '')}"
        )

    # Range validation
    if not check_field_range(value, field_req):
        result["passed"] = False
        min_val = field_req.get("min_value")
        max_val = field_req.get("max_value")
        if min_val is not None and max_val is not None:
            result["errors"].append(f"Value must be between {min_val} and {max_val}")
        elif min_val is not None:
            result["errors"].append(f"Value must be at least {min_val}")
        elif max_val is not None:
            result["errors"].append(f"Value must be at most {max_val}")

    return result
