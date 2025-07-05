"""
Data profiling module for ADRI V2.

This module provides functionality to analyze data structure and content
to support automatic standard generation.
"""

import logging
import re
import warnings
from typing import Any, Dict, Optional

import pandas as pd


class DataProfiler:
    """
    Analyzes data to extract structure, types, and constraints.

    This class profiles data to understand field types, null patterns,
    value ranges, and other characteristics needed for standard generation.
    """

    def __init__(self):
        """Initialize the DataProfiler."""
        # Email pattern for basic email detection
        self.email_pattern = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )

        # Date patterns for basic date detection
        self.date_patterns = [
            re.compile(r"^\d{4}-\d{2}-\d{2}$"),  # YYYY-MM-DD
            re.compile(r"^\d{2}/\d{2}/\d{4}$"),  # MM/DD/YYYY
            re.compile(r"^\d{2}-\d{2}-\d{4}$"),  # MM-DD-YYYY
        ]

    def profile_data(
        self, data: pd.DataFrame, max_rows: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Profile a DataFrame to extract structure and characteristics.

        Args:
            data: DataFrame to profile
            max_rows: Maximum number of rows to analyze (None for all)

        Returns:
            Dictionary containing profiling results
        """
        if data.empty:
            return self._create_empty_profile()

        # Apply row limit if specified
        original_rows = len(data)
        if max_rows and len(data) > max_rows:
            data = data.head(max_rows)
        analyzed_rows = len(data)

        # Create profile structure
        profile = {
            "summary": self._create_summary(data, original_rows, analyzed_rows),
            "fields": {},
        }

        # Profile each field
        for column in data.columns:
            profile["fields"][column] = self._profile_field(data[column])

        return profile

    def _create_empty_profile(self) -> Dict[str, Any]:
        """Create profile for empty DataFrame."""
        return {
            "summary": {
                "total_rows": 0,
                "total_columns": 0,
                "analyzed_rows": 0,
                "data_types": {},
            },
            "fields": {},
        }

    def _create_summary(
        self, data: pd.DataFrame, original_rows: int, analyzed_rows: int
    ) -> Dict[str, Any]:
        """Create summary statistics for the dataset."""
        # Count data types
        data_types: Dict[str, int] = {}
        for column in data.columns:
            field_type = self._infer_field_type(data[column])
            data_types[field_type] = data_types.get(field_type, 0) + 1

        return {
            "total_rows": original_rows,
            "total_columns": len(data.columns),
            "analyzed_rows": analyzed_rows,
            "data_types": data_types,
        }

    def _profile_field(self, series: pd.Series) -> Dict[str, Any]:
        """Profile a single field (column)."""
        field_profile = {
            "type": self._infer_field_type(series),
            "nullable": self._is_nullable(series),
            "null_count": int(series.isnull().sum()),
            "null_percentage": float((series.isnull().sum() / len(series)) * 100),
        }

        # Add type-specific profiling
        if field_profile["type"] == "integer":
            field_profile.update(self._profile_integer_field(series))
        elif field_profile["type"] == "float":
            field_profile.update(self._profile_float_field(series))
        elif field_profile["type"] == "string":
            field_profile.update(self._profile_string_field(series))
        elif field_profile["type"] == "boolean":
            field_profile.update(self._profile_boolean_field(series))
        elif field_profile["type"] == "date":
            field_profile.update(self._profile_date_field(series))

        return field_profile

    def _infer_field_type(self, series: pd.Series) -> str:
        """Infer the type of a field based on its values."""
        # Remove null values for type inference
        non_null_series = series.dropna()

        if len(non_null_series) == 0:
            return "string"  # Default for all-null columns

        # Check for boolean
        if self._is_boolean_series(non_null_series):
            return "boolean"

        # Check for integer
        if self._is_integer_series(non_null_series):
            return "integer"

        # Check for float
        if self._is_float_series(non_null_series):
            return "float"

        # Check for date
        if self._is_date_series(non_null_series):
            return "date"

        # Default to string
        return "string"

    def _is_boolean_series(self, series: pd.Series) -> bool:
        """Check if series contains boolean values."""
        try:
            # Check if all values are boolean-like
            unique_values = set(str(v).lower() for v in series.unique())
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

    def _is_integer_series(self, series: pd.Series) -> bool:
        """Check if series contains integer values."""
        try:
            # Try to convert to numeric and check if all are integers
            numeric_series = pd.to_numeric(series, errors="coerce")
            if numeric_series.isnull().any():
                return False
            # Explicitly convert to bool to satisfy mypy
            result = (numeric_series % 1 == 0).all()
            return bool(result)
        except Exception:
            return False

    def _is_float_series(self, series: pd.Series) -> bool:
        """Check if series contains float values."""
        try:
            # Try to convert to numeric
            numeric_series = pd.to_numeric(series, errors="coerce")
            # Explicitly convert to bool to satisfy mypy
            result = not numeric_series.isnull().any()
            return bool(result)
        except Exception:
            return False

    def _is_date_series(self, series: pd.Series) -> bool:
        """Check if series contains date values."""
        try:
            # Check if values match common date patterns
            sample_size = min(10, len(series))
            sample_values = series.head(sample_size).astype(str)

            for value in sample_values:
                # Explicitly convert to bool to satisfy mypy
                if bool(any(pattern.match(value) for pattern in self.date_patterns)):
                    return True
            return False
        except Exception:
            return False

    def _is_nullable(self, series: pd.Series) -> bool:
        """Determine if field should be considered nullable."""
        null_percentage = (series.isnull().sum() / len(series)) * 100
        # Explicitly convert to bool to satisfy mypy
        return bool(null_percentage > 0)

    def _profile_integer_field(self, series: pd.Series) -> Dict[str, Any]:
        """Profile integer field characteristics."""
        non_null_series = pd.to_numeric(series.dropna(), errors="coerce")

        # Handle empty series
        if len(non_null_series) == 0:
            return {
                "min_value": 0,
                "max_value": 0,
                "avg_value": 0.0,
            }

        try:
            # Use pandas methods for compatibility with tests
            # Suppress warnings for all-NaN operations
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                min_val = non_null_series.min()
                max_val = non_null_series.max()
                mean_val = non_null_series.mean()

            # Check for any remaining special values
            if pd.isna(min_val) or pd.isna(max_val) or pd.isna(mean_val):
                return {
                    "min_value": 0,
                    "max_value": 0,
                    "avg_value": 0.0,
                }

            return {
                "min_value": int(min_val),
                "max_value": int(max_val),
                "avg_value": float(mean_val),
            }
        except (ValueError, TypeError, OverflowError):
            # If any conversion fails, return safe defaults
            return {
                "min_value": 0,
                "max_value": 0,
                "avg_value": 0.0,
            }

    def _profile_float_field(self, series: pd.Series) -> Dict[str, Any]:
        """Profile float field characteristics."""
        non_null_series = pd.to_numeric(series.dropna(), errors="coerce")

        # Handle empty series
        if len(non_null_series) == 0:
            return {
                "min_value": 0.0,
                "max_value": 0.0,
                "avg_value": 0.0,
            }

        try:
            # Use pandas methods for compatibility with tests
            # Suppress warnings for all-NaN operations
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                min_val = non_null_series.min()
                max_val = non_null_series.max()
                mean_val = non_null_series.mean()

            # Check for any remaining special values
            if pd.isna(min_val) or pd.isna(max_val) or pd.isna(mean_val):
                return {
                    "min_value": 0.0,
                    "max_value": 0.0,
                    "avg_value": 0.0,
                }

            return {
                "min_value": float(min_val),
                "max_value": float(max_val),
                "avg_value": float(mean_val),
            }
        except (ValueError, TypeError, OverflowError):
            # If any conversion fails, return safe defaults
            return {
                "min_value": 0.0,
                "max_value": 0.0,
                "avg_value": 0.0,
            }

    def _profile_string_field(self, series: pd.Series) -> Dict[str, Any]:
        """Profile string field characteristics."""
        non_null_series = series.dropna().astype(str)

        # Handle empty series
        if len(non_null_series) == 0:
            return {
                "min_length": 0,
                "max_length": 0,
                "avg_length": 0.0,
            }

        try:
            # Calculate string lengths with error handling
            lengths = non_null_series.str.len()

            # Use pandas methods for compatibility with tests
            # Suppress warnings for all-NaN operations
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                min_len = lengths.min()
                max_len = lengths.max()
                mean_len = lengths.mean()

            # Check for any remaining special values
            if pd.isna(min_len) or pd.isna(max_len) or pd.isna(mean_len):
                return {
                    "min_length": 0,
                    "max_length": 0,
                    "avg_length": 0.0,
                }

            profile: Dict[str, Any] = {
                "min_length": int(min_len),
                "max_length": int(max_len),
                "avg_length": float(mean_len),
            }

            # Check for patterns
            pattern = self._detect_string_pattern(non_null_series)
            if pattern:
                profile["pattern"] = pattern

            return profile
        except (ValueError, TypeError, OverflowError):
            # If any conversion fails, return safe defaults
            return {
                "min_length": 0,
                "max_length": 0,
                "avg_length": 0.0,
            }

    def _profile_boolean_field(self, series: pd.Series) -> Dict[str, Any]:
        """Profile boolean field characteristics."""
        non_null_series = series.dropna()

        # Count true/false values
        value_counts = non_null_series.value_counts()

        # Use .get() for safe access to avoid future warnings
        # Handle integer 1 as boolean True explicitly
        int_one_count = 0
        if 1 in value_counts.index:
            int_one_count = value_counts.loc[1]

        true_count = (
            value_counts.get(True, 0)
            + value_counts.get("true", 0)
            + value_counts.get("True", 0)
            + int_one_count
        )

        return {
            "true_count": int(true_count),
            "false_count": int(len(non_null_series) - true_count),
        }

    def _profile_date_field(self, series: pd.Series) -> Dict[str, Any]:
        """Profile date field characteristics."""
        non_null_series = series.dropna().astype(str)

        # Try to parse dates to get min/max
        try:
            parsed_dates = pd.to_datetime(non_null_series, errors="coerce")
            valid_dates = parsed_dates.dropna()

            if len(valid_dates) > 0:
                return {
                    "min_date": valid_dates.min().strftime("%Y-%m-%d"),
                    "max_date": valid_dates.max().strftime("%Y-%m-%d"),
                    "date_format": self._detect_date_format(non_null_series.iloc[0]),
                }
        except Exception as e:
            logging.warning(f"Failed to parse dates: {e}")

        return {"date_format": "unknown"}

    def _detect_string_pattern(self, series: pd.Series) -> Optional[str]:
        """Detect common patterns in string fields."""
        # Check if all values match email pattern
        if len(series) > 0 and all(
            self.email_pattern.match(str(val)) for val in series
        ):
            return "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"

        # Could add more pattern detection here (phone numbers, IDs, etc.)

        return None

    def _detect_date_format(self, sample_value: str) -> str:
        """Detect the format of a date string."""
        for pattern in self.date_patterns:
            if pattern.match(sample_value):
                if "-" in sample_value and len(sample_value) == 10:
                    if sample_value.startswith("2"):  # Likely YYYY-MM-DD
                        return "YYYY-MM-DD"
                    else:  # Likely MM-DD-YYYY
                        return "MM-DD-YYYY"
                elif "/" in sample_value:
                    return "MM/DD/YYYY"

        return "unknown"
