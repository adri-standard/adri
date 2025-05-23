"""
Utility functions for data type inference and validation.

This module provides helper functions to automatically infer data types
and detect quality issues in datasets.
"""

import re
import pandas as pd
from datetime import datetime
from typing import Any, List, Dict, Union, Optional


def is_numeric(value: Any) -> bool:
    """Check if a value can be converted to a numeric type."""
    if pd.isna(value):
        return False
    
    # Handle already numeric types
    if isinstance(value, (int, float)):
        return True
    
    # Handle string representations
    if isinstance(value, str):
        # Remove currency symbols and commas
        cleaned = re.sub(r'[$,\s]', '', value)
        # Remove + or - prefix if present
        cleaned = cleaned.lstrip('+-')
        return cleaned.replace('.', '', 1).isdigit()
        
    return False


def is_integer(value: Any) -> bool:
    """Check if a value represents an integer."""
    if pd.isna(value):
        return False
    
    # Handle actual integers
    if isinstance(value, int):
        return True
    
    # Handle floats that are effectively integers
    if isinstance(value, float):
        return value.is_integer()
    
    # Handle string representations
    if isinstance(value, str):
        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[$,\s]', '', value)
        # Remove + or - prefix if present
        cleaned = cleaned.lstrip('+-')
        return cleaned.isdigit()
        
    return False


def is_date_like(value: Any) -> bool:
    """Check if a value looks like a date."""
    if pd.isna(value):
        return False
    
    # Already a datetime
    if isinstance(value, (datetime, pd.Timestamp)):
        return True
    
    # String representations
    if isinstance(value, str):
        # Common date formats check
        date_patterns = [
            r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
            r'\d{1,2}-\d{1,2}-\d{4}',  # DD-MM-YYYY or MM-DD-YYYY
            r'\d{1,2}/\d{1,2}/\d{4}',  # DD/MM/YYYY or MM/DD/YYYY
            r'\d{4}/\d{1,2}/\d{1,2}',  # YYYY/MM/DD
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, value):
                return True
                
        # Try to parse with pandas
        try:
            pd.to_datetime(value)
            return True
        except:
            pass
            
    return False


def is_id_like(value: Any) -> bool:
    """Check if a value looks like an ID field."""
    if pd.isna(value):
        return False
    
    # IDs are typically strings or numbers with a consistent format
    if isinstance(value, (int, str)):
        str_val = str(value)
        
        # Common ID patterns
        id_patterns = [
            r'^[A-Z]\d+$',  # Letter followed by numbers (e.g., P1234)
            r'^\d+$',       # Pure numeric ID
            r'^[A-Z]{1,3}\d+$',  # Few letters followed by numbers (e.g., AB123)
            r'^[A-Z0-9]+$',  # Alphanumeric without spaces or symbols
        ]
        
        for pattern in id_patterns:
            if re.match(pattern, str_val):
                return True
                
    return False


def get_id_pattern(values: List[Any]) -> Optional[str]:
    """
    Determine the most common ID pattern in a list of values.
    Returns the regex pattern that matches most of the IDs.
    """
    if not values or len(values) == 0:
        return None
    
    # Consider only non-null values
    valid_values = [str(v) for v in values if not pd.isna(v)]
    if not valid_values:
        return None
    
    # Check for common patterns
    patterns = {
        r'^\d+$': 'numeric_only',
        r'^[A-Z]\d+$': 'letter_numbers',
        r'^[A-Z]{1,3}\d+$': 'letters_numbers',
        r'^[A-Z0-9]+$': 'alphanumeric'
    }
    
    # Count matches for each pattern
    pattern_counts = {pattern: 0 for pattern in patterns}
    
    for value in valid_values:
        for pattern in patterns:
            if re.match(pattern, str(value)):
                pattern_counts[pattern] += 1
                break
    
    # Find the most common pattern
    if pattern_counts:
        most_common = max(pattern_counts.items(), key=lambda x: x[1])
        if most_common[1] > 0:
            return most_common[0]
    
    return None


def id_pattern_confidence(values: List[Any]) -> float:
    """
    Check how confidently a column can be classified as an ID column.
    Returns confidence between 0 and 1.
    """
    if len(values) == 0:
        return 0.0
    
    # Count values matching common ID patterns
    id_like_count = sum(is_id_like(val) for val in values)
    
    # Check uniqueness (IDs tend to be unique)
    unique_ratio = len(set(str(v) for v in values)) / len(values)
    
    # Combine pattern matching with uniqueness
    pattern_confidence = id_like_count / len(values)
    
    # Weight uniqueness more heavily for ID columns
    return 0.7 * pattern_confidence + 0.3 * unique_ratio


def check_id_consistency(values: List[Any]) -> Dict[str, Any]:
    """
    Check if values follow a consistent ID pattern.
    
    Returns:
        Dictionary with consistency information
    """
    if len(values) == 0:
        return {"consistent": True, "inconsistent_values": []}
    
    # Filter out nulls
    valid_values = [v for v in values if not pd.isna(v)]
    if not valid_values:
        return {"consistent": True, "inconsistent_values": []}
    
    # Get the most common pattern
    common_pattern = get_id_pattern(valid_values)
    
    # If we couldn't determine a pattern, treat all as consistent
    if not common_pattern:
        return {"consistent": True, "inconsistent_values": []}
    
    # Check each value against the pattern
    inconsistent = []
    for val in valid_values:
        if not re.match(common_pattern, str(val)):
            inconsistent.append(val)
    
    return {
        "consistent": len(inconsistent) == 0,
        "common_pattern": common_pattern,
        "inconsistent_values": inconsistent,
        "inconsistent_ratio": len(inconsistent) / len(valid_values) if valid_values else 0
    }


def categorical_confidence(values: List[Any]) -> float:
    """
    Check how confidently a column can be classified as categorical.
    Returns confidence between 0 and 1.
    """
    if len(values) == 0:
        return 0.0
    
    # Categorical columns have limited distinct values compared to total
    unique_count = len(set(str(v) for v in values))
    
    if unique_count == 1:
        # Single value columns are likely categorical but not very interesting
        return 0.7
    elif unique_count < min(10, len(values) * 0.1):
        # Few distinct values relative to dataset size
        return 0.9
    elif unique_count < min(20, len(values) * 0.2):
        # Moderate number of distinct values
        return 0.7
    else:
        # Too many distinct values for a typical categorical
        return 0.3


def find_inconsistent_values(series: pd.Series, expected_type: str) -> List[Any]:
    """
    Find values in a series that don't match the expected type.
    
    Args:
        series: Pandas Series to check
        expected_type: Expected type ('numeric', 'integer', 'date', 'id', etc.)
    
    Returns:
        List of inconsistent values
    """
    checker_map = {
        'numeric': is_numeric,
        'integer': is_integer,
        'date': is_date_like,
        'id': is_id_like,
    }
    
    checker = checker_map.get(expected_type, lambda x: True)
    
    # Find values that don't match the expected type
    inconsistent = []
    for val in series:
        if not pd.isna(val) and not checker(val):
            inconsistent.append(val)
            
    return inconsistent


def detect_outliers(series: pd.Series) -> Dict[str, Any]:
    """
    Detect statistical outliers in a numeric series.
    
    Args:
        series: Pandas Series with numeric data
    
    Returns:
        Dictionary with outlier information
    """
    # Filter to numeric values
    numeric_series = pd.to_numeric(series, errors='coerce').dropna()
    
    if len(numeric_series) < 5:  # Need enough data for meaningful stats
        return {"outliers_found": False}
        
    # Use IQR method for outlier detection
    q1 = numeric_series.quantile(0.25)
    q3 = numeric_series.quantile(0.75)
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outliers = numeric_series[(numeric_series < lower_bound) | (numeric_series > upper_bound)]
    
    return {
        "outliers_found": len(outliers) > 0,
        "outlier_count": len(outliers),
        "outlier_percent": len(outliers) / len(numeric_series) * 100,
        "outlier_examples": outliers.head(5).tolist(),
        "lower_bound": lower_bound,
        "upper_bound": upper_bound
    }


def is_mostly_positive(series: pd.Series) -> bool:
    """Check if a numeric series is predominantly positive."""
    numeric_series = pd.to_numeric(series, errors='coerce').dropna()
    
    if len(numeric_series) == 0:
        return False
        
    # If more than 80% of values are positive, consider it "mostly positive"
    return (numeric_series > 0).mean() > 0.8


def find_invalid_dates(series: pd.Series) -> List[Any]:
    """Find values in a series that look like dates but are invalid."""
    invalid_dates = []
    
    for val in series:
        if pd.isna(val):
            continue
            
        # If it looks like a date pattern but can't be parsed
        if isinstance(val, str) and is_date_like(val):
            try:
                pd.to_datetime(val)
            except:
                invalid_dates.append(val)
                
    return invalid_dates
