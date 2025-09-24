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
    """Check if value is within the required numeric range."""
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


def check_allowed_values(value: Any, field_req: Dict[str, Any]) -> bool:
    """Check if value is in allowed_values (robust to number/string comparisons)."""
    allowed = field_req.get("allowed_values")
    if not isinstance(allowed, list):
        return True
    try:
        val_str = str(value)
    except Exception:
        val_str = f"{value}"
    allowed_str = {str(v) for v in allowed}
    return val_str in allowed_str


def check_length_bounds(value: Any, field_req: Dict[str, Any]) -> bool:
    """Check if string length within min_length/max_length when provided."""
    min_len = field_req.get("min_length")
    max_len = field_req.get("max_length")
    # If neither bound provided, this check passes
    if min_len is None and max_len is None:
        return True
    try:
        s = str(value)
    except Exception:
        # If cannot stringify, consider as failure when any constraint exists
        return False
    L = len(s)
    if min_len is not None and L < int(min_len):
        return False
    if max_len is not None and L > int(max_len):
        return False
    return True


def _parse_date_iso(date_str: str):
    """Parse YYYY-MM-DD into a date object; returns None on failure."""
    from datetime import datetime

    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").date()
    except Exception:
        return None


def _parse_datetime_iso(datetime_str: str):
    """Parse ISO datetime (best effort) into a datetime; returns None on failure."""
    from datetime import datetime

    try:
        # datetime.fromisoformat handles 'YYYY-MM-DD' and 'YYYY-MM-DDTHH:MM:SS' without Z
        s = str(datetime_str).replace("Z", "")
        return datetime.fromisoformat(s)
    except Exception:
        return None


def check_date_bounds(value: Any, field_req: Dict[str, Any]) -> bool:
    """Check value against date/datetime bounds if provided.

    Supports:
      - after_date / before_date (YYYY-MM-DD inclusive)
      - after_datetime / before_datetime (ISO-like; inclusive)
    """
    after_d = field_req.get("after_date")
    before_d = field_req.get("before_date")
    after_dt = field_req.get("after_datetime")
    before_dt = field_req.get("before_datetime")

    # If no date-related bounds configured, pass
    if not any([after_d, before_d, after_dt, before_dt]):
        return True

    # If datetime bounds present, try datetime comparison first
    if after_dt or before_dt:
        v_dt = _parse_datetime_iso(value)
        if v_dt is None:
            return False
        if after_dt:
            a_dt = _parse_datetime_iso(after_dt)
            if a_dt and v_dt < a_dt:
                return False
        if before_dt:
            b_dt = _parse_datetime_iso(before_dt)
            if b_dt and v_dt > b_dt:
                return False
        return True

    # Otherwise use date bounds
    v_d = _parse_date_iso(value)
    if v_d is None:
        return False
    if after_d:
        a_d = _parse_date_iso(after_d)
        if a_d and v_d < a_d:
            return False
    if before_d:
        b_d = _parse_date_iso(before_d)
        if b_d and v_d > b_d:
            return False
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

    # Allowed values validation
    if not check_allowed_values(value, field_req):
        result["passed"] = False
        result["errors"].append(
            f"Value not in allowed_values: {field_req.get('allowed_values', [])}"
        )

    # Length bounds validation
    if not check_length_bounds(value, field_req):
        result["passed"] = False
        min_len = field_req.get("min_length")
        max_len = field_req.get("max_length")
        if min_len is not None and max_len is not None:
            result["errors"].append(
                f"Value length must be between {min_len} and {max_len}"
            )
        elif min_len is not None:
            result["errors"].append(f"Value length must be at least {min_len}")
        elif max_len is not None:
            result["errors"].append(f"Value length must be at most {max_len}")

    # Pattern validation
    if not check_field_pattern(value, field_req):
        result["passed"] = False
        result["errors"].append(
            f"Value does not match required pattern: {field_req.get('pattern', '')}"
        )

    # Numeric range validation
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

    # Date/datetime bounds validation
    if not check_date_bounds(value, field_req):
        result["passed"] = False
        after_d = field_req.get("after_date") or field_req.get("after_datetime")
        before_d = field_req.get("before_date") or field_req.get("before_datetime")
        if after_d and before_d:
            result["errors"].append(
                f"Value must be within date bounds [{after_d}, {before_d}]"
            )
        elif after_d:
            result["errors"].append(f"Value must be on/after {after_d}")
        elif before_d:
            result["errors"].append(f"Value must be on/before {before_d}")

    return result
