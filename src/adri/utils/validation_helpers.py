"""Validation helper utilities for the ADRI framework.

This module contains common validation utilities and helper functions that are
used across the validation system for field validation, data checking, and
rule execution.
"""

import hashlib
import re
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd


def validate_field_value(
    value: Any,
    rules: list[Callable[[Any, dict[str, Any]], bool]],
    context: dict[str, Any] = None,
) -> list[str]:
    """Validate a field value against multiple validation rules.

    Args:
        value: Value to validate
        rules: List of validation rule functions
        context: Additional context for validation

    Returns:
        List of validation error messages (empty if all pass)
    """
    if context is None:
        context = {}

    errors = []

    for rule in rules:
        try:
            if not rule(value, context):
                # Try to get error message from rule if it has one
                if hasattr(rule, "get_error_message"):
                    errors.append(rule.get_error_message(value))
                else:
                    errors.append(f"Validation failed for value: {value}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

    return errors


def is_missing_value(value: Any) -> bool:
    """Check if a value should be considered missing/null.

    Args:
        value: Value to check

    Returns:
        True if value is missing, False otherwise
    """
    # Handle pandas null values
    try:
        if pd.isna(value):
            return True
    except Exception:
        pass

    # Handle None
    if value is None:
        return True

    # Handle empty strings
    if isinstance(value, str) and value.strip() == "":
        return True

    return False


def is_valid_email(email: str) -> bool:
    """Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if email format is valid
    """
    if not isinstance(email, str) or not email.strip():
        return False

    # Basic email regex pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def is_valid_url(url: str) -> bool:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if URL format is valid
    """
    if not isinstance(url, str) or not url.strip():
        return False

    # Basic URL regex pattern
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url.strip(), re.IGNORECASE))


def is_valid_phone(phone: str) -> bool:
    """Validate phone number format.

    Args:
        phone: Phone number to validate

    Returns:
        True if phone format is valid
    """
    if not isinstance(phone, str) or not phone.strip():
        return False

    # Remove common separators and spaces
    cleaned = re.sub(r"[\s\-\(\)\+\.]", "", phone)

    # Check if it contains only digits after cleaning
    if not cleaned.isdigit():
        return False

    # Check reasonable length (7-15 digits is typical)
    return 7 <= len(cleaned) <= 15


def parse_date_value(value: Any) -> datetime | None:
    """Parse a value into a datetime object.

    Args:
        value: Value to parse as date

    Returns:
        Datetime object, or None if parsing fails
    """
    if value is None or is_missing_value(value):
        return None

    # If it's already a datetime
    if isinstance(value, datetime):
        return value

    # If it's a date, convert to datetime
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())

    # Try to parse string values
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

        # Common date formats to try
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%m-%d-%Y",
            "%d-%m-%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

        # Try pandas date parsing as fallback
        try:
            return pd.to_datetime(value)
        except Exception:
            pass

    return None


def is_numeric_value(value: Any) -> bool:
    """Check if a value can be treated as numeric.

    Args:
        value: Value to check

    Returns:
        True if value is numeric or can be converted to numeric
    """
    if is_missing_value(value):
        return False

    # Direct numeric types
    if isinstance(value, (int, float)):
        return True

    # Try to convert string to numeric
    if isinstance(value, str):
        try:
            float(value.strip())
            return True
        except (ValueError, AttributeError):
            pass

    return False


def safe_numeric_conversion(value: Any) -> float | None:
    """Safely convert a value to numeric.

    Args:
        value: Value to convert

    Returns:
        Numeric value, or None if conversion fails
    """
    if is_missing_value(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        try:
            return float(value.strip())
        except (ValueError, AttributeError):
            pass

    return None


def generate_record_id(row: Any, row_index: int, primary_key_fields: list[str]) -> str:
    """Generate a record identifier for error reporting.

    Args:
        row: Data row (pandas Series or dict)
        row_index: Index of the row in the dataset
        primary_key_fields: List of primary key field names

    Returns:
        Human-readable record identifier
    """
    if primary_key_fields:
        key_values = []
        for field in primary_key_fields:
            try:
                if hasattr(row, "get"):
                    value = row.get(field)
                elif hasattr(row, "__getitem__"):
                    value = row[field] if field in row else None
                else:
                    value = getattr(row, field, None)

                if value is not None and not is_missing_value(value):
                    key_values.append(str(value))
            except (ValueError, TypeError, AttributeError):
                # Skip invalid field values during key generation
                continue

        if key_values:
            return f"{':'.join(key_values)} (Row {row_index + 1})"

    return f"Row {row_index + 1}"


def calculate_pass_rate(passed_count: int, total_count: int) -> float:
    """Calculate pass rate as a percentage.

    Args:
        passed_count: Number of items that passed
        total_count: Total number of items

    Returns:
        Pass rate as percentage (0.0-100.0)
    """
    if total_count <= 0:
        return 0.0

    return (passed_count / total_count) * 100.0


def normalize_field_name(field_name: str) -> str:
    """Normalize a field name for consistent comparison.

    Args:
        field_name: Field name to normalize

    Returns:
        Normalized field name
    """
    if not isinstance(field_name, str):
        return str(field_name)

    return field_name.strip().lower().replace(" ", "_").replace("-", "_")


def is_sql_reserved_word(word: str) -> bool:
    """Check if a word is a SQL reserved word.

    Args:
        word: Word to check

    Returns:
        True if word is a SQL reserved word
    """
    reserved_words = {
        "select",
        "from",
        "where",
        "order",
        "group",
        "by",
        "insert",
        "update",
        "delete",
        "join",
        "inner",
        "outer",
        "left",
        "right",
        "on",
        "as",
        "and",
        "or",
        "not",
        "in",
        "between",
        "like",
        "is",
        "null",
        "case",
        "when",
        "then",
        "else",
        "end",
        "union",
        "all",
        "distinct",
        "having",
        "exists",
        "create",
        "drop",
        "alter",
        "table",
        "index",
        "view",
        "database",
        "schema",
        "primary",
        "key",
        "foreign",
        "references",
        "unique",
        "constraint",
        "check",
        "default",
        "auto_increment",
        "identity",
        "int",
        "integer",
        "varchar",
        "char",
        "text",
        "date",
        "time",
        "timestamp",
        "datetime",
        "float",
        "double",
        "decimal",
        "numeric",
        "boolean",
        "bit",
        "binary",
        "varbinary",
        "blob",
        "clob",
        "true",
        "false",
        "user",
        "current_user",
        "session_user",
        "count",
        "sum",
        "avg",
        "min",
        "max",
        "coalesce",
        "isnull",
    }

    return word.lower() in reserved_words


def suggest_field_name_alternative(field_name: str) -> str:
    """Suggest an alternative field name if the current one is problematic.

    Args:
        field_name: Original field name

    Returns:
        Suggested alternative field name
    """
    if not is_sql_reserved_word(field_name):
        return field_name

    # Common mapping for reserved words
    alternatives = {
        "order": "order_number",
        "date": "date_value",
        "time": "time_value",
        "user": "user_name",
        "select": "selection",
        "count": "count_value",
        "sum": "sum_value",
        "avg": "avg_value",
        "min": "min_value",
        "max": "max_value",
    }

    lower_name = field_name.lower()
    if lower_name in alternatives:
        return alternatives[lower_name]

    # Default strategy: add suffix
    return f"{field_name}_value"


def generate_file_hash(file_path: str | Path) -> str:
    """Generate a hash for a file for integrity checking.

    Args:
        file_path: Path to the file

    Returns:
        SHA-256 hash of the file (first 8 characters)

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_sha256 = hashlib.sha256()

    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()[:8]
    except OSError as e:
        raise OSError(f"Cannot read file {file_path}: {e}")


def validate_data_types(
    data: pd.DataFrame, expected_types: dict[str, str]
) -> dict[str, list[str]]:
    """Validate data types of DataFrame columns.

    Args:
        data: DataFrame to validate
        expected_types: Dictionary mapping column names to expected type names

    Returns:
        Dictionary mapping column names to lists of validation errors
    """
    errors = {}

    for column, expected_type in expected_types.items():
        if column not in data.columns:
            errors[column] = [f"Column '{column}' not found in data"]
            continue

        column_errors = []
        series = data[column]

        # Check each non-null value in the column
        for idx, value in series.items():
            if is_missing_value(value):
                continue  # Skip null values

            if not _matches_expected_type(value, expected_type):
                column_errors.append(
                    f"Row {idx}: Expected {expected_type}, got {type(value).__name__}"
                )

        if column_errors:
            errors[column] = column_errors

    return errors


def _matches_expected_type(value: Any, expected_type: str) -> bool:
    """Check if a value matches the expected type.

    Args:
        value: Value to check
        expected_type: Expected type name

    Returns:
        True if value matches expected type
    """
    expected_type = expected_type.lower()

    if expected_type in ["string", "str", "text"]:
        return isinstance(value, str)
    elif expected_type in ["integer", "int"]:
        return isinstance(value, int) or (
            isinstance(value, float) and value.is_integer()
        )
    elif expected_type in ["number", "float", "numeric"]:
        return isinstance(value, (int, float))
    elif expected_type in ["boolean", "bool"]:
        return isinstance(value, bool)
    elif expected_type in ["date", "datetime", "timestamp"]:
        return (
            isinstance(value, (date, datetime)) or parse_date_value(value) is not None
        )
    else:
        return True  # Unknown type, assume valid


class ValidationContext:
    """Context object for validation operations.

    Provides a way to pass additional information and state between
    validation rules and assessors.
    """

    def __init__(
        self,
        data: pd.DataFrame | None = None,
        standard: dict[str, Any] | None = None,
        field_name: str | None = None,
        row_index: int | None = None,
    ):
        """Initialize validation context.

        Args:
            data: Full dataset being validated
            standard: ADRI standard being applied
            field_name: Current field being validated
            row_index: Current row index being validated
        """
        self.data = data
        self.standard = standard
        self.field_name = field_name
        self.row_index = row_index
        self._cache: dict[str, Any] = {}

    def get_field_requirements(self, field_name: str | None = None) -> dict[str, Any]:
        """Get field requirements from the standard.

        Args:
            field_name: Field name (uses current field if None)

        Returns:
            Field requirements dictionary
        """
        field_name = field_name or self.field_name
        if not field_name or not self.standard:
            return {}

        field_reqs = self.standard.get("requirements", {}).get("field_requirements", {})
        return field_reqs.get(field_name, {})

    def cache_value(self, key: str, value: Any) -> None:
        """Cache a value for reuse in validation.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = value

    def get_cached_value(self, key: str, default: Any = None) -> Any:
        """Get a cached value.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        return self._cache.get(key, default)

    def clear_cache(self) -> None:
        """Clear the validation cache."""
        self._cache.clear()


def create_validation_summary(
    total_records: int, passed_records: int, failed_validations: list[dict[str, Any]]
) -> dict[str, Any]:
    """Create a summary of validation results.

    Args:
        total_records: Total number of records validated
        passed_records: Number of records that passed validation
        failed_validations: List of failed validation details

    Returns:
        Validation summary dictionary
    """
    failed_records = total_records - passed_records
    pass_rate = calculate_pass_rate(passed_records, total_records)

    # Group failures by type
    failure_types = {}
    for failure in failed_validations:
        failure_type = failure.get("issue", "unknown")
        if failure_type not in failure_types:
            failure_types[failure_type] = 0
        failure_types[failure_type] += 1

    return {
        "total_records": total_records,
        "passed_records": passed_records,
        "failed_records": failed_records,
        "pass_rate_percent": round(pass_rate, 2),
        "total_failures": len(failed_validations),
        "failure_types": failure_types,
        "top_failure_types": sorted(
            failure_types.items(), key=lambda x: x[1], reverse=True
        )[:5],
    }
