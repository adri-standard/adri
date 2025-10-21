"""
ADRI Type Inference.

Data type inference and validation rule generation.
Migrated and updated for the new src/ layout architecture.
"""

from typing import Any

import pandas as pd


class InferenceResult:
    """Result of type inference operation."""

    def __init__(
        self, field_types: dict, confidence_scores: dict = None, metadata: dict = None
    ):
        """Initialize InferenceResult with type inference data."""
        self.field_types = field_types
        self.confidence_scores = confidence_scores or {}
        self.metadata = metadata or {}


class FieldTypeInfo:
    """Type information for a single field."""

    def __init__(
        self, inferred_type: str, confidence: float = 1.0, sample_values: list = None
    ):
        """Initialize FieldTypeInfo with field type information."""
        self.inferred_type = inferred_type
        self.confidence = confidence
        self.sample_values = sample_values or []


class TypeInference:
    """
    Infers data types and appropriate validation rules from data patterns.

    This component analyzes data to determine the most appropriate
    ADRI validation rules and type constraints.
    """

    def __init__(self):
        """Initialize the type inference engine."""

    def infer_types(self, data: pd.DataFrame) -> "InferenceResult":
        """
        Infer types for all fields in a DataFrame.

        Args:
            data: DataFrame to analyze

        Returns:
            InferenceResult containing field types and confidence scores
        """
        if data is None:
            raise ValueError("Data cannot be None")

        if data.empty:
            return InferenceResult({}, {}, {})

        field_types = {}
        confidence_scores = {}

        for column in data.columns:
            try:
                # Infer the field type
                field_type = self.infer_field_type(data[column])
                constraints = self.infer_field_constraints(data[column], field_type)

                # Create FieldTypeInfo with proper attributes
                field_info = FieldTypeInfo(field_type)
                field_info.primary_type = field_type
                field_info.constraints = constraints

                # Add specialized type detection
                if field_type == "string":
                    specialized = self._detect_specialized_type(data[column])
                    if specialized:
                        field_info.specialized_type = specialized

                field_types[column] = field_info

                # Calculate confidence score based on data quality
                confidence = self._calculate_confidence(data[column], field_type)
                confidence_scores[column] = confidence

            except Exception:
                # Fallback for problematic columns
                field_info = FieldTypeInfo("string")
                field_info.primary_type = "string"
                field_types[column] = field_info
                confidence_scores[column] = 0.5

        return InferenceResult(field_types, confidence_scores)

    def infer_types_from_profile(self, profile_result) -> "InferenceResult":
        """
        Infer types using data profiler results.

        Args:
            profile_result: Result from data profiler

        Returns:
            InferenceResult with enhanced type information
        """
        field_types = {}
        confidence_scores = {}

        if hasattr(profile_result, "field_profiles"):
            for field_name, profile in profile_result.field_profiles.items():
                # Extract type from profile
                if hasattr(profile, "field_type"):
                    field_type = profile.field_type
                else:
                    field_type = "string"

                # Create enhanced field info
                field_info = FieldTypeInfo(field_type)
                field_info.primary_type = field_type

                # Add pattern confidence if available
                if hasattr(profile, "pattern_matches") and hasattr(
                    profile, "total_count"
                ):
                    if profile.total_count > 0:
                        pattern_confidence = (
                            profile.pattern_matches / profile.total_count
                        )
                        field_info.pattern_confidence = pattern_confidence
                        confidence_scores[field_name] = pattern_confidence
                    else:
                        confidence_scores[field_name] = 0.5
                else:
                    confidence_scores[field_name] = (
                        0.8  # Default high confidence from profiler
                    )

                field_types[field_name] = field_info

        return InferenceResult(field_types, confidence_scores)

    def _detect_specialized_type(self, series: pd.Series) -> str | None:
        """Detect specialized types for string data."""
        if len(series) == 0:
            return None

        sample_values = series.dropna().astype(str).head(100)
        if len(sample_values) == 0:
            return None

        # Email detection
        email_pattern = r"^[^@]+@[^@]+\.[^@]+$"
        email_matches = sample_values.str.match(email_pattern).sum()
        if email_matches > len(sample_values) * 0.8:
            return "email"

        # Phone detection
        phone_pattern = r"^[\+]?[0-9\s\-\(\)]+$"
        phone_matches = sample_values.str.match(phone_pattern).sum()
        if phone_matches > len(sample_values) * 0.8:
            return "phone"

        # Currency detection
        currency_pattern = r"^\$[\d,]+\.?\d*$"
        currency_matches = sample_values.str.match(currency_pattern).sum()
        if currency_matches > len(sample_values) * 0.8:
            return "currency"

        return None

    def _calculate_confidence(self, series: pd.Series, field_type: str) -> float:
        """Calculate confidence score for type inference."""
        if len(series) == 0:
            return 0.0

        non_null_count = series.notna().sum()
        total_count = len(series)

        # Base confidence on null percentage
        data_completeness = non_null_count / total_count

        # Adjust based on type-specific factors
        if field_type in ["integer", "float"]:
            try:
                numeric_series = pd.to_numeric(series, errors="coerce")
                successful_conversions = numeric_series.notna().sum()
                type_accuracy = (
                    successful_conversions / non_null_count if non_null_count > 0 else 0
                )
                return min(data_completeness * type_accuracy, 1.0)
            except (ValueError, TypeError, AttributeError):
                return 0.5

        elif field_type == "boolean":
            try:
                bool_values = series.dropna().astype(str).str.lower()
                bool_matches = bool_values.isin(
                    ["true", "false", "yes", "no", "1", "0"]
                ).sum()
                type_accuracy = (
                    bool_matches / non_null_count if non_null_count > 0 else 0
                )
                return min(data_completeness * type_accuracy, 1.0)
            except (ValueError, TypeError, AttributeError):
                return 0.5

        # For strings and other types, use data completeness as primary factor
        return min(
            data_completeness * 0.9, 1.0
        )  # Slightly reduce confidence for string inference

    def infer_field_type(self, series: pd.Series) -> str:
        """
        Infer the most appropriate ADRI type for a field.

        Args:
            series: Pandas Series to analyze

        Returns:
            ADRI type string (string, integer, float, boolean, date, datetime)
        """
        # Handle empty series
        if len(series) == 0:
            return "string"

        # Remove nulls for analysis
        non_null_series = series.dropna()
        if len(non_null_series) == 0:
            return "string"

        # Check pandas dtype first
        if pd.api.types.is_integer_dtype(series):
            return "integer"
        elif pd.api.types.is_float_dtype(series):
            return "float"
        elif pd.api.types.is_bool_dtype(series):
            return "boolean"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"

        # For object/string types, do pattern analysis
        return self._infer_string_type(non_null_series)

    def _infer_string_type(self, series: pd.Series) -> str:
        """Infer type for string/object columns."""
        sample_values = series.astype(str).head(100)

        # Check for date patterns
        date_patterns = [
            r"^\d{4}-\d{2}-\d{2}$",  # YYYY-MM-DD
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",  # ISO datetime
            r"^\d{2}/\d{2}/\d{4}$",  # MM/DD/YYYY
        ]

        for pattern in date_patterns:
            if sample_values.str.match(pattern).sum() > len(sample_values) * 0.8:
                return "datetime" if "T" in pattern else "date"

        # Check for boolean patterns
        bool_patterns = sample_values.str.lower().isin(
            ["true", "false", "yes", "no", "1", "0"]
        )
        if bool_patterns.sum() > len(sample_values) * 0.8:
            return "boolean"

        # Check for numeric patterns
        try:
            numeric_values = pd.to_numeric(sample_values, errors="coerce")
            if numeric_values.notna().sum() > len(sample_values) * 0.8:
                if (numeric_values % 1 == 0).all():
                    return "integer"
                else:
                    return "float"
        except (ValueError, TypeError, AttributeError):
            pass

        # Default to string
        return "string"

    def infer_field_constraints(
        self, series: pd.Series, field_type: str
    ) -> dict[str, Any]:
        """
        Infer appropriate constraints for a field.

        Args:
            series: Pandas Series to analyze
            field_type: ADRI type for the field

        Returns:
            Dictionary of constraints
        """
        constraints = {}
        non_null_series = series.dropna()

        # Nullable constraint
        null_percentage = (series.isnull().sum() / len(series)) * 100
        constraints["nullable"] = null_percentage > 5  # Allow nulls if >5% are null

        if len(non_null_series) == 0:
            return constraints

        # Type-specific constraints
        if field_type in ["integer", "float"]:
            constraints.update(self._infer_numeric_constraints(non_null_series))
        elif field_type == "string":
            constraints.update(self._infer_string_constraints(non_null_series))
        elif field_type in ["date", "datetime"]:
            constraints.update(self._infer_date_constraints(non_null_series))

        return constraints

    def _infer_numeric_constraints(self, series: pd.Series) -> dict[str, Any]:
        """Infer constraints for numeric fields."""
        constraints = {}

        try:
            numeric_series = pd.to_numeric(series, errors="coerce").dropna()
            if len(numeric_series) > 0:
                constraints["min_value"] = float(numeric_series.min())
                constraints["max_value"] = float(numeric_series.max())
        except (ValueError, TypeError, AttributeError):
            pass

        return constraints

    def _infer_string_constraints(self, series: pd.Series) -> dict[str, Any]:
        """Infer constraints for string fields."""
        constraints = {}
        string_series = series.astype(str)

        # Length constraints
        lengths = string_series.str.len()
        constraints["min_length"] = int(lengths.min())
        constraints["max_length"] = int(lengths.max())

        # Pattern detection
        pattern = self._detect_string_pattern(string_series)
        if pattern:
            constraints["pattern"] = pattern

        # Allowed values (if low cardinality)
        unique_values = series.unique()
        if len(unique_values) <= 10:  # Low cardinality
            constraints["allowed_values"] = list(unique_values)

        return constraints

    def _detect_string_pattern(self, series: pd.Series) -> str | None:
        """Detect common string patterns."""
        sample_values = series.head(100)

        # Email pattern
        email_pattern = r"^[^@]+@[^@]+\.[^@]+$"
        if sample_values.str.match(email_pattern).sum() > len(sample_values) * 0.8:
            return email_pattern

        # Phone pattern
        phone_pattern = r"^[\+]?[0-9\s\-\(\)]+$"
        if sample_values.str.match(phone_pattern).sum() > len(sample_values) * 0.8:
            return phone_pattern

        # ID pattern (letters/numbers with separators)
        id_pattern = r"^[A-Z0-9_\-]+$"
        if (
            sample_values.str.upper().str.match(id_pattern).sum()
            > len(sample_values) * 0.8
        ):
            return r"^[A-Za-z0-9_\-]+$"

        return None

    def _infer_date_constraints(self, series: pd.Series) -> dict[str, Any]:
        """Infer constraints for date/datetime fields."""
        constraints = {}

        try:
            # Try to parse as datetime
            date_series = pd.to_datetime(series, errors="coerce").dropna()
            if len(date_series) > 0:
                constraints["after_date"] = date_series.min().isoformat()
                constraints["before_date"] = date_series.max().isoformat()
        except (ValueError, TypeError, AttributeError):
            pass

        return constraints

    def infer_validation_rules(self, data: pd.DataFrame) -> dict[str, dict[str, Any]]:
        """
        Infer complete validation rules for all fields in a DataFrame.

        Args:
            data: DataFrame to analyze

        Returns:
            Dictionary mapping field names to their inferred rules
        """
        validation_rules = {}

        for column in data.columns:
            field_type = self.infer_field_type(data[column])
            constraints = self.infer_field_constraints(data[column], field_type)

            validation_rules[column] = {"type": field_type, **constraints}

        return validation_rules


# Convenience functions
def infer_types_from_dataframe(data: pd.DataFrame) -> dict[str, str]:
    """
    Infer ADRI types for all columns in a DataFrame.

    Args:
        data: DataFrame to analyze

    Returns:
        Dictionary mapping column names to ADRI types
    """
    inference = TypeInference()
    return {col: inference.infer_field_type(data[col]) for col in data.columns}


def infer_validation_rules_from_data(data: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """
    Infer complete validation rules from a DataFrame.

    Args:
        data: DataFrame to analyze

    Returns:
        Dictionary of validation rules for all fields
    """
    inference = TypeInference()
    return inference.infer_validation_rules(data)


def check_allowed_values(series: pd.Series, max_unique: int = 10) -> list | None:
    """
    Check if a series has a small set of allowed values.

    Args:
        series: Pandas Series to analyze
        max_unique: Maximum number of unique values to consider as allowed values

    Returns:
        List of allowed values if cardinality is low, None otherwise
    """
    if series.isnull().all():
        return None

    # Remove nulls and get unique values
    unique_values = series.dropna().unique()

    if len(unique_values) <= max_unique:
        return list(unique_values)

    return None
