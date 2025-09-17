"""
ADRI Validation Rules

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


def validate_field(field_name: str, value: Any, field_requirements: Dict[str, Any]) -> Dict[str, Any]:
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
        "warnings": []
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
        result["errors"].append(f"Value does not match required type: {field_req.get('type', 'string')}")
    
    # Pattern validation
    if not check_field_pattern(value, field_req):
        result["passed"] = False
        result["errors"].append(f"Value does not match required pattern: {field_req.get('pattern', '')}")
    
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
