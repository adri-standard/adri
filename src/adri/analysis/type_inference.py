"""
ADRI Type Inference

Data type inference and validation rule generation.
Migrated and updated for the new src/ layout architecture.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd


class TypeInference:
    """
    Infers data types and appropriate validation rules from data patterns.

    This component analyzes data to determine the most appropriate
    ADRI validation rules and type constraints.
    """

    def __init__(self):
        """Initialize the type inference engine."""
        pass

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
        except:
            pass

        # Default to string
        return "string"

    def infer_field_constraints(
        self, series: pd.Series, field_type: str
    ) -> Dict[str, Any]:
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

    def _infer_numeric_constraints(self, series: pd.Series) -> Dict[str, Any]:
        """Infer constraints for numeric fields."""
        constraints = {}

        try:
            numeric_series = pd.to_numeric(series, errors="coerce").dropna()
            if len(numeric_series) > 0:
                constraints["min_value"] = float(numeric_series.min())
                constraints["max_value"] = float(numeric_series.max())
        except:
            pass

        return constraints

    def _infer_string_constraints(self, series: pd.Series) -> Dict[str, Any]:
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

    def _detect_string_pattern(self, series: pd.Series) -> Optional[str]:
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

    def _infer_date_constraints(self, series: pd.Series) -> Dict[str, Any]:
        """Infer constraints for date/datetime fields."""
        constraints = {}

        try:
            # Try to parse as datetime
            date_series = pd.to_datetime(series, errors="coerce").dropna()
            if len(date_series) > 0:
                constraints["after_date"] = date_series.min().isoformat()
                constraints["before_date"] = date_series.max().isoformat()
        except:
            pass

        return constraints

    def infer_validation_rules(self, data: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
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
def infer_types_from_dataframe(data: pd.DataFrame) -> Dict[str, str]:
    """
    Infer ADRI types for all columns in a DataFrame.

    Args:
        data: DataFrame to analyze

    Returns:
        Dictionary mapping column names to ADRI types
    """
    inference = TypeInference()
    return {col: inference.infer_field_type(data[col]) for col in data.columns}


def infer_validation_rules_from_data(data: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Infer complete validation rules from a DataFrame.

    Args:
        data: DataFrame to analyze

    Returns:
        Dictionary of validation rules for all fields
    """
    inference = TypeInference()
    return inference.infer_validation_rules(data)
