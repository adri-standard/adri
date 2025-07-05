"""
Type inference module for ADRI V2.

This module provides utilities for inferring data types and constraints
from data values.
"""

import re
from typing import Any, Dict, List, Optional

import pandas as pd


class TypeInference:
    """
    Provides type inference utilities for data analysis.

    This class contains helper methods for inferring data types
    and constraints from raw data values.
    """

    def __init__(self):
        """Initialize the TypeInference."""
        # Common patterns for type detection
        self.patterns = {
            "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
            "phone": re.compile(r"^[\+]?[1-9][\d]{0,15}$"),
            "url": re.compile(r"^https?://[^\s/$.?#].[^\s]*$"),
            "uuid": re.compile(
                r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
            ),
            "date_iso": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
            "date_us": re.compile(r"^\d{2}/\d{2}/\d{4}$"),
            "time": re.compile(r"^\d{2}:\d{2}:\d{2}$"),
        }

    def infer_type(self, values: List[Any]) -> str:
        """
        Infer the most likely type for a list of values.

        Args:
            values: List of values to analyze

        Returns:
            Inferred type as string
        """
        if not values:
            return "string"

        # Remove None/null values
        non_null_values = [v for v in values if v is not None and pd.notna(v)]

        if not non_null_values:
            return "string"

        # Check for boolean
        if self._is_boolean_type(non_null_values):
            return "boolean"

        # Check for integer
        if self._is_integer_type(non_null_values):
            return "integer"

        # Check for float
        if self._is_float_type(non_null_values):
            return "float"

        # Check for date
        if self._is_date_type(non_null_values):
            return "date"

        # Default to string
        return "string"

    def infer_constraints(self, values: List[Any], data_type: str) -> dict:
        """
        Infer constraints for values of a given type.

        Args:
            values: List of values to analyze
            data_type: The inferred data type

        Returns:
            Dictionary of constraints
        """
        constraints: dict = {}

        # Remove None/null values
        non_null_values = [v for v in values if v is not None and pd.notna(v)]

        if not non_null_values:
            return constraints

        if data_type == "integer":
            constraints.update(self._infer_integer_constraints(non_null_values))
        elif data_type == "float":
            constraints.update(self._infer_float_constraints(non_null_values))
        elif data_type == "string":
            constraints.update(self._infer_string_constraints(non_null_values))
        elif data_type == "date":
            constraints.update(self._infer_date_constraints(non_null_values))

        return constraints

    def detect_pattern(self, values: List[str]) -> Optional[str]:
        """
        Detect common patterns in string values.

        Args:
            values: List of string values

        Returns:
            Pattern name if detected, None otherwise
        """
        if not values:
            return None

        # Check each pattern
        for pattern_name, pattern_regex in self.patterns.items():
            if all(pattern_regex.match(str(v)) for v in values if v):
                return pattern_name

        return None

    def _is_boolean_type(self, values: List[Any]) -> bool:
        """Check if values represent boolean type."""
        try:
            unique_values = set(str(v).lower() for v in values)
            boolean_values = {
                "true",
                "false",
                "1",
                "0",
                "yes",
                "no",
                "t",
                "f",
                "y",
                "n",
            }
            return unique_values.issubset(boolean_values) and len(unique_values) <= 2
        except Exception:
            return False

    def _is_integer_type(self, values: List[Any]) -> bool:
        """Check if values represent integer type."""
        try:
            for value in values:
                float_val = float(value)
                if float_val != int(float_val):
                    return False
            return True
        except Exception:
            return False

    def _is_float_type(self, values: List[Any]) -> bool:
        """Check if values represent float type."""
        try:
            for value in values:
                float(value)
            return True
        except Exception:
            return False

    def _is_date_type(self, values: List[Any]) -> bool:
        """Check if values represent date type."""
        try:
            sample_size = min(5, len(values))
            sample_values = values[:sample_size]

            for value in sample_values:
                str_val = str(value)
                if any(
                    pattern.match(str_val)
                    for pattern in [self.patterns["date_iso"], self.patterns["date_us"]]
                ):
                    return True
            return False
        except Exception:
            return False

    def _infer_integer_constraints(self, values: List[Any]) -> dict:
        """Infer constraints for integer values."""
        int_values = [int(float(v)) for v in values]

        return {
            "min_value": min(int_values),
            "max_value": max(int_values),
            "avg_value": sum(int_values) / len(int_values),
        }

    def _infer_float_constraints(self, values: List[Any]) -> dict:
        """Infer constraints for float values."""
        float_values = [float(v) for v in values]

        return {
            "min_value": min(float_values),
            "max_value": max(float_values),
            "avg_value": sum(float_values) / len(float_values),
        }

    def _infer_string_constraints(self, values: List[Any]) -> dict:
        """Infer constraints for string values."""
        str_values = [str(v) for v in values]
        lengths = [len(s) for s in str_values]

        constraints: Dict[str, Any] = {
            "min_length": min(lengths),
            "max_length": max(lengths),
            "avg_length": float(sum(lengths) / len(lengths)),
        }

        # Check for patterns
        pattern = self.detect_pattern(str_values)
        if pattern:
            constraints["pattern"] = pattern

        return constraints

    def _infer_date_constraints(self, values: List[Any]) -> dict:
        """Infer constraints for date values."""
        str_values = [str(v) for v in values]

        # Try to determine date format
        if str_values:
            sample_value = str_values[0]
            if self.patterns["date_iso"].match(sample_value):
                date_format = "YYYY-MM-DD"
            elif self.patterns["date_us"].match(sample_value):
                date_format = "MM/DD/YYYY"
            else:
                date_format = "unknown"

            return {"format": date_format}

        return {}
