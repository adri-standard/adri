# @ADRI_FEATURE[analysis_data_profiler, scope=OPEN_SOURCE]
# Description: Data profiling engine for analyzing dataset patterns and quality
"""
ADRI Data Profiler.

Data profiling functionality for automatic standard generation.
Migrated and updated for the new src/ layout architecture.
"""

from typing import Any

import pandas as pd


class ProfileResult:
    """Result of data profiling operation with clean, explicit interface.

    Use explicit methods for accessing profile data:
    - profile.to_dict() - Get full profile as dictionary
    - profile.get_field_profile('name') - Get specific field profile
    - profile.get_field_names() - List all field names
    - profile.has_field('name') - Check if field exists

    Direct attribute access still available:
    - profile.field_profiles
    - profile.summary_statistics
    - profile.data_quality_score
    - profile.metadata
    """

    def __init__(
        self,
        field_profiles: dict,
        summary_statistics: dict,
        data_quality_score: float,
        metadata: dict = None,
    ):
        """Initialize ProfileResult with profiling data.

        Args:
            field_profiles: Dictionary of field name -> FieldProfile objects
            summary_statistics: Overall dataset statistics
            data_quality_score: Calculated quality score (0-100)
            metadata: Additional metadata (recommendations, config, etc.)
        """
        self.field_profiles = field_profiles
        self.summary_statistics = summary_statistics
        self.data_quality_score = data_quality_score
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert profile to dictionary format.

        Returns complete profile data as a dictionary for serialization.

        Returns:
            Dictionary with all profile data
        """
        result = {
            "field_profiles": self.field_profiles,
            "summary_statistics": self.summary_statistics,
            "data_quality_score": self.data_quality_score,
            "metadata": self.metadata,
        }

        # Include optional attributes if present
        if hasattr(self, "quality_assessment"):
            result["quality_assessment"] = self.quality_assessment
        if hasattr(self, "fields"):
            result["fields"] = self.fields

        return result

    def get_field_profile(self, field_name: str) -> "FieldProfile":
        """Get profile for a specific field.

        Args:
            field_name: Name of the field to get profile for

        Returns:
            FieldProfile object for the specified field

        Raises:
            KeyError: If field_name is not in the profile
        """
        if field_name not in self.field_profiles:
            raise KeyError(f"Field '{field_name}' not found in profile")
        return self.field_profiles[field_name]

    def get_field_names(self) -> list[str]:
        """Get list of all profiled field names.

        Returns:
            List of field names that were profiled
        """
        return list(self.field_profiles.keys())

    def has_field(self, field_name: str) -> bool:
        """Check if a field exists in the profile.

        Args:
            field_name: Name of the field to check

        Returns:
            True if field is in profile, False otherwise
        """
        return field_name in self.field_profiles

    def get(self, key: str, default=None):
        """Get attribute value (for internal code compatibility).

        Args:
            key: Attribute name
            default: Default value if not found

        Returns:
            Attribute value or default

        Note:
            This method exists for internal code compatibility.
            External code should use explicit methods like get_field_profile().
        """
        return getattr(self, key, default)


class FieldProfile:
    """Profile information for a single field."""

    def __init__(
        self, field_type: str, null_count: int = 0, unique_count: int = 0, **kwargs
    ):
        """Initialize FieldProfile with field statistics."""
        self.field_type = field_type
        self.null_count = null_count
        self.unique_count = unique_count

        # Add all additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get(self, key, default=None):
        """Dict-like get method for internal code use."""
        return getattr(self, key, default)

    def __contains__(self, key):
        """Support 'in' operator for checking attributes."""
        return hasattr(self, key)

    def __getitem__(self, key):
        """Dict-like access for internal code use."""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"'{key}' not found in FieldProfile")

    def setdefault(self, key, default=None):
        """Dict-like setdefault method for internal code use."""
        if hasattr(self, key):
            return getattr(self, key)
        else:
            setattr(self, key, default)
            return default


class DataProfiler:
    """
    Analyzes data patterns and structure for standard generation.

    This is the "Data Scientist" component that understands your data
    and helps create appropriate quality standards.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the data profiler."""
        self.config = config or {}
        self.sample_size = self.config.get("sample_size", 10000)
        self.enable_statistical_analysis = self.config.get(
            "enable_statistical_analysis", True
        )
        self.enable_pattern_detection = self.config.get(
            "enable_pattern_detection", True
        )
        self.null_threshold = self.config.get("null_threshold", 0.05)

    def profile_data(
        self, data: pd.DataFrame, max_rows: int | None = None
    ) -> "ProfileResult":
        """
        Profile a DataFrame to understand its structure and patterns.

        Args:
            data: DataFrame to profile
            max_rows: Maximum rows to analyze (for performance)

        Returns:
            ProfileResult containing comprehensive data profile
        """
        if data is None:
            from src.adri.core.exceptions import DataValidationError

            raise DataValidationError("Data cannot be None")

        if data.empty:
            # Handle empty DataFrame
            return ProfileResult(
                field_profiles={},
                summary_statistics={"total_rows": 0, "total_columns": 0},
                data_quality_score=0.0,
            )

        # Apply sampling if configured
        sample_size = max_rows or self.sample_size
        if len(data) > sample_size:
            data = data.head(sample_size)

        summary_stats = self._get_summary_stats(data)
        field_profiles = self._profile_fields(data)
        quality_assessment = self._assess_quality_patterns(data)
        recommendations = self._generate_recommendations(data)

        # Calculate overall data quality score
        data_quality_score = self._calculate_data_quality_score(
            quality_assessment, field_profiles
        )

        result = ProfileResult(
            field_profiles=field_profiles,
            summary_statistics=summary_stats,
            data_quality_score=data_quality_score,
            metadata={"recommendations": recommendations, "config": self.config},
        )

        # Add quality_assessment as a top-level attribute for API compatibility
        result.quality_assessment = quality_assessment

        # Add fields alias (used by internal generation code that accesses
        # profile.get('fields'))
        result.fields = field_profiles

        return result

    def _get_summary_stats(self, data: pd.DataFrame) -> dict[str, Any]:
        """Get basic summary statistics."""
        return {
            "total_rows": int(len(data)),
            "total_columns": int(len(data.columns)),
            "data_types": {
                str(k): int(v) for k, v in data.dtypes.value_counts().to_dict().items()
            },
            "memory_usage_mb": float(data.memory_usage(deep=True).sum() / 1024 / 1024),
            "completeness_ratio": float(
                (data.size - data.isnull().sum().sum()) / data.size
            ),
        }

    def _profile_fields(self, data: pd.DataFrame) -> dict[str, "FieldProfile"]:
        """Profile individual fields."""
        field_profiles = {}

        for column in data.columns:
            field_data = self._profile_single_field(data[column])

            # Determine field type
            series = data[column]
            if pd.api.types.is_numeric_dtype(series):
                if pd.api.types.is_integer_dtype(series):
                    field_type = "integer"
                else:
                    field_type = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(series):
                field_type = "date"
            else:
                field_type = "string"

            # Create FieldProfile object with all the data
            # Remove keys that are already passed as explicit parameters
            field_data_kwargs = {
                k: v
                for k, v in field_data.items()
                if k not in ["null_count", "unique_count"]
            }

            field_profiles[column] = FieldProfile(
                field_type=field_type,
                null_count=field_data.get("null_count", 0),
                unique_count=field_data.get("unique_count", 0),
                **field_data_kwargs,  # Pass all other attributes
            )

        return field_profiles

    def _profile_single_field(self, series: pd.Series) -> dict[str, Any]:
        """Profile a single field/column."""
        profile = {
            "name": series.name,
            "dtype": str(series.dtype),
            "null_count": int(series.isnull().sum()),
            "null_percentage": float((series.isnull().sum() / len(series)) * 100),
            "unique_count": int(series.astype(str).nunique()),
            "unique_percentage": float(
                (series.astype(str).nunique() / len(series)) * 100
            ),
        }

        # Add type-specific analysis
        if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(
            series
        ):
            non_null_series = series.dropna()
            if len(non_null_series) > 0:
                try:
                    profile.update(
                        {
                            "min_value": float(non_null_series.min()),
                            "max_value": float(non_null_series.max()),
                            "mean_value": float(non_null_series.mean()),
                            "median_value": float(non_null_series.median()),
                            "std_dev": float(non_null_series.std()),
                            "outlier_count": int(self._count_outliers(non_null_series)),
                            "quartiles": [
                                float(non_null_series.quantile(0.25)),
                                float(non_null_series.quantile(0.5)),
                                float(non_null_series.quantile(0.75)),
                            ],
                        }
                    )
                except (TypeError, ValueError):
                    # Fallback for problematic numeric data
                    profile.update(
                        {
                            "min_value": float(non_null_series.min()),
                            "max_value": float(non_null_series.max()),
                            "mean_value": float(non_null_series.mean()),
                        }
                    )
        elif pd.api.types.is_bool_dtype(series):
            # Handle boolean data specifically
            non_null_series = series.dropna()
            if len(non_null_series) > 0:
                true_count = int(non_null_series.sum())
                total_count = len(non_null_series)
                profile.update(
                    {
                        "true_count": true_count,
                        "false_count": total_count - true_count,
                        "true_percentage": float((true_count / total_count) * 100),
                    }
                )

        elif pd.api.types.is_string_dtype(series) or series.dtype == "object":
            non_null_series = series.dropna()
            if len(non_null_series) > 0:
                non_null_str = non_null_series.astype(str)
                # Build small head/tail sample for regex inference and docs
                unique_non_null_str = non_null_str.drop_duplicates()
                head_vals = unique_non_null_str.head(5).tolist()
                tail_vals = (
                    unique_non_null_str.tail(5).tolist()
                    if len(unique_non_null_str) > 5
                    else []
                )
                sample_values = head_vals + [v for v in tail_vals if v not in head_vals]
                # Clamp to at most 10 items
                sample_values = sample_values[:10]

                profile.update(
                    {
                        "avg_length": float(non_null_str.str.len().mean()),
                        "max_length": int(non_null_str.str.len().max()),
                        "min_length": int(non_null_str.str.len().min()),
                        "common_patterns": self._identify_patterns(non_null_series),
                        "sample_values": sample_values,
                    }
                )

        return profile

    def _count_outliers(self, series: pd.Series) -> int:
        """Count outliers using IQR method."""
        try:
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return ((series < lower_bound) | (series > upper_bound)).sum()
        except (ValueError, TypeError):
            return 0

    def _identify_patterns(self, series: pd.Series) -> list[str]:
        """Identify common patterns in string data."""
        patterns = []

        # Check for email patterns
        email_pattern = series.astype(str).str.contains(
            r"^[^@]+@[^@]+\.[^@]+$", regex=True, na=False
        )
        if email_pattern.sum() > len(series) * 0.8:
            patterns.append("email")

        # Check for phone patterns
        phone_pattern = series.astype(str).str.contains(
            r"^[\+]?[0-9\s\-\(\)]+$", regex=True, na=False
        )
        if phone_pattern.sum() > len(series) * 0.8:
            patterns.append("phone")

        # Check for date patterns
        date_pattern = series.astype(str).str.contains(
            r"^\d{4}-\d{2}-\d{2}", regex=True, na=False
        )
        if date_pattern.sum() > len(series) * 0.8:
            patterns.append("date")

        return patterns

    def _assess_quality_patterns(self, data: pd.DataFrame) -> dict[str, Any]:
        """Assess overall quality patterns in the data."""
        return {
            "overall_completeness": float(
                ((data.size - data.isnull().sum().sum()) / data.size) * 100
            ),
            "fields_with_nulls": int(data.isnull().any().sum()),
            "completely_null_fields": int((data.isnull().all()).sum()),
            "duplicate_rows": int(data.duplicated().sum()),
            "potential_issues": self._identify_potential_issues(data),
        }

    def _identify_potential_issues(self, data: pd.DataFrame) -> list[str]:
        """Identify potential data quality issues."""
        issues = []

        # Check for high null rates
        high_null_fields = data.columns[data.isnull().sum() / len(data) > 0.5]
        if len(high_null_fields) > 0:
            issues.append(f"High null rate in {len(high_null_fields)} fields")

        # Check for duplicate rows
        if data.duplicated().sum() > 0:
            issues.append(f"{data.duplicated().sum()} duplicate rows found")

        # Check for inconsistent data types
        object_columns = data.select_dtypes(include=["object"]).columns
        for col in object_columns:
            if data[col].apply(lambda x: isinstance(x, (int, float))).any():
                issues.append(f"Mixed data types in field: {col}")

        return issues

    def _generate_recommendations(self, data: pd.DataFrame) -> list[str]:
        """Generate recommendations for data quality improvement."""
        recommendations = []

        # Completeness recommendations
        completeness = ((data.size - data.isnull().sum().sum()) / data.size) * 100
        if completeness < 90:
            recommendations.append(
                "Consider addressing missing values to improve completeness"
            )

        # Consistency recommendations
        object_columns = data.select_dtypes(include=["object"]).columns
        if len(object_columns) > 0:
            recommendations.append("Review string fields for consistent formatting")

        # Performance recommendations
        if len(data) > 10000:
            recommendations.append("Consider data sampling for large datasets")

        return recommendations

    def _calculate_data_quality_score(
        self,
        quality_assessment: dict[str, Any],
        field_profiles: dict[str, "FieldProfile"],
    ) -> float:
        """Calculate overall data quality score with high sensitivity to quality differences."""
        try:
            # Base score on completeness (0-100) but make it more sensitive
            completeness_score = quality_assessment.get("overall_completeness", 0.0)

            # Penalize for potential issues (more aggressive)
            issues = quality_assessment.get("potential_issues", [])
            issue_penalty = min(len(issues) * 20, 50)  # 20 points per issue

            # More granular penalties for null rates per field
            null_penalty = 0
            total_fields = len(field_profiles)
            for field_profile in field_profiles.values():
                if hasattr(field_profile, "null_percentage"):
                    null_pct = field_profile.null_percentage
                    if null_pct > 0:
                        # Exponential penalty for higher null rates
                        field_penalty = (
                            null_pct / 10
                        ) ** 1.5  # More aggressive penalty
                        null_penalty += field_penalty

            # Average penalty across fields
            avg_null_penalty = null_penalty / max(total_fields, 1)

            # Pattern quality assessment
            pattern_bonus = 0
            pattern_penalty = 0
            for field_profile in field_profiles.values():
                # Bonus for good patterns
                if (
                    hasattr(field_profile, "common_patterns")
                    and field_profile.common_patterns
                ):
                    pattern_bonus += 2
                # Penalty for fields that should have patterns but don't (like emails)
                if (
                    hasattr(field_profile, "name")
                    and "email" in str(field_profile.name).lower()
                ):
                    if (
                        not hasattr(field_profile, "common_patterns")
                        or not field_profile.common_patterns
                    ):
                        pattern_penalty += 5

            pattern_bonus = min(pattern_bonus, 10)

            # Data consistency penalty (fields with extreme invalid values)
            consistency_penalty = 0
            for field_profile in field_profiles.values():
                if (
                    hasattr(field_profile, "outlier_count")
                    and field_profile.outlier_count > 0
                ):
                    # Penalty for outliers
                    consistency_penalty += min(field_profile.outlier_count / 2, 3)

            # Final calculation with multiple factors
            final_score = (
                completeness_score * 0.6  # Weight completeness at 60%
                + 40  # Start with 40 base points for other factors
                - issue_penalty
                - avg_null_penalty
                - pattern_penalty
                - consistency_penalty
                + pattern_bonus
            )

            # Ensure we get meaningful differences between quality levels
            # Apply a scaling factor to spread scores more
            if final_score > 90:
                final_score = 90 + (final_score - 90) * 0.5  # Compress high scores

            return max(0.0, min(100.0, final_score))

        except Exception:
            # Fallback calculation
            return 50.0


# Convenience function
def profile_dataframe(
    data: pd.DataFrame, max_rows: int | None = None
) -> dict[str, Any]:
    """
    Profile a DataFrame using the default profiler.

    Args:
        data: DataFrame to profile
        max_rows: Maximum rows to analyze

    Returns:
        Data profile dictionary
    """
    profiler = DataProfiler()
    return profiler.profile_data(data, max_rows)


# @ADRI_FEATURE_END[analysis_data_profiler]
