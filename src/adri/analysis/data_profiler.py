"""
ADRI Data Profiler

Data profiling functionality for automatic standard generation.
Migrated and updated for the new src/ layout architecture.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np


class DataProfiler:
    """
    Analyzes data patterns and structure for standard generation.
    
    This is the "Data Scientist" component that understands your data
    and helps create appropriate quality standards.
    """

    def __init__(self):
        """Initialize the data profiler."""
        pass

    def profile_data(self, data: pd.DataFrame, max_rows: Optional[int] = None) -> Dict[str, Any]:
        """
        Profile a DataFrame to understand its structure and patterns.
        
        Args:
            data: DataFrame to profile
            max_rows: Maximum rows to analyze (for performance)
            
        Returns:
            Dict containing comprehensive data profile
        """
        if max_rows and len(data) > max_rows:
            data = data.head(max_rows)
        
        profile = {
            "summary": self._get_summary_stats(data),
            "fields": self._profile_fields(data),
            "quality_assessment": self._assess_quality_patterns(data),
            "recommendations": self._generate_recommendations(data)
        }
        
        return profile

    def _get_summary_stats(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get basic summary statistics."""
        return {
            "total_rows": int(len(data)),
            "total_columns": int(len(data.columns)),
            "data_types": {str(k): int(v) for k, v in data.dtypes.value_counts().to_dict().items()},
            "memory_usage_mb": float(data.memory_usage(deep=True).sum() / 1024 / 1024),
            "completeness_ratio": float((data.size - data.isnull().sum().sum()) / data.size)
        }

    def _profile_fields(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Profile individual fields."""
        field_profiles = {}
        
        for column in data.columns:
            field_profiles[column] = self._profile_single_field(data[column])
        
        return field_profiles

    def _profile_single_field(self, series: pd.Series) -> Dict[str, Any]:
        """Profile a single field/column."""
        profile = {
            "name": series.name,
            "dtype": str(series.dtype),
            "null_count": int(series.isnull().sum()),
            "null_percentage": float((series.isnull().sum() / len(series)) * 100),
            "unique_count": int(series.nunique()),
            "unique_percentage": float((series.nunique() / len(series)) * 100)
        }
        
        # Add type-specific analysis
        if pd.api.types.is_numeric_dtype(series):
            non_null_series = series.dropna()
            if len(non_null_series) > 0:
                profile.update({
                    "min_value": float(non_null_series.min()),
                    "max_value": float(non_null_series.max()),
                    "mean_value": float(non_null_series.mean()),
                    "median_value": float(non_null_series.median()),
                    "outlier_count": int(self._count_outliers(non_null_series))
                })
        
        elif pd.api.types.is_string_dtype(series) or series.dtype == 'object':
            non_null_series = series.dropna()
            if len(non_null_series) > 0:
                profile.update({
                    "avg_length": float(non_null_series.astype(str).str.len().mean()),
                    "max_length": int(non_null_series.astype(str).str.len().max()),
                    "min_length": int(non_null_series.astype(str).str.len().min()),
                    "common_patterns": self._identify_patterns(non_null_series)
                })
        
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
        except:
            return 0

    def _identify_patterns(self, series: pd.Series) -> List[str]:
        """Identify common patterns in string data."""
        patterns = []
        
        # Check for email patterns
        email_pattern = series.astype(str).str.contains(r'^[^@]+@[^@]+\.[^@]+$', regex=True, na=False)
        if email_pattern.sum() > len(series) * 0.8:
            patterns.append("email")
        
        # Check for phone patterns
        phone_pattern = series.astype(str).str.contains(r'^[\+]?[0-9\s\-\(\)]+$', regex=True, na=False)
        if phone_pattern.sum() > len(series) * 0.8:
            patterns.append("phone")
        
        # Check for date patterns
        date_pattern = series.astype(str).str.contains(r'^\d{4}-\d{2}-\d{2}', regex=True, na=False)
        if date_pattern.sum() > len(series) * 0.8:
            patterns.append("date")
        
        return patterns

    def _assess_quality_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Assess overall quality patterns in the data."""
        return {
            "overall_completeness": float(((data.size - data.isnull().sum().sum()) / data.size) * 100),
            "fields_with_nulls": int(data.isnull().any().sum()),
            "completely_null_fields": int((data.isnull().all()).sum()),
            "duplicate_rows": int(data.duplicated().sum()),
            "potential_issues": self._identify_potential_issues(data)
        }

    def _identify_potential_issues(self, data: pd.DataFrame) -> List[str]:
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
        object_columns = data.select_dtypes(include=['object']).columns
        for col in object_columns:
            if data[col].apply(lambda x: isinstance(x, (int, float))).any():
                issues.append(f"Mixed data types in field: {col}")
        
        return issues

    def _generate_recommendations(self, data: pd.DataFrame) -> List[str]:
        """Generate recommendations for data quality improvement."""
        recommendations = []
        
        # Completeness recommendations
        completeness = ((data.size - data.isnull().sum().sum()) / data.size) * 100
        if completeness < 90:
            recommendations.append("Consider addressing missing values to improve completeness")
        
        # Consistency recommendations
        object_columns = data.select_dtypes(include=['object']).columns
        if len(object_columns) > 0:
            recommendations.append("Review string fields for consistent formatting")
        
        # Performance recommendations
        if len(data) > 10000:
            recommendations.append("Consider data sampling for large datasets")
        
        return recommendations


# Convenience function
def profile_dataframe(data: pd.DataFrame, max_rows: Optional[int] = None) -> Dict[str, Any]:
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
