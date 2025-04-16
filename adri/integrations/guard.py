"""
Guard decorator for enforcing data quality standards in agent functions.

This module provides the adri_guarded decorator that can be used to ensure
data sources meet minimum quality standards before being used by agents.
"""

import functools
import inspect
from typing import Any, Callable, Optional, Union
from pathlib import Path

from ..assessor import DataSourceAssessor


def adri_guarded(min_score: float = 80, data_source_param: str = "data_source"):
    """
    Decorator to guard agent functions with ADRI quality checks.
    
    This decorator assesses the quality of a data source before allowing
    the decorated function to proceed. If the data quality doesn't meet
    the minimum score, it raises a ValueError with details about the issues.
    
    Args:
        min_score: Minimum ADRI score required to proceed (0-100)
        data_source_param: Name of the parameter containing the data source path
        
    Raises:
        ValueError: If data quality doesn't meet the minimum score
        
    Example:
        ```python
        @adri_guarded(min_score=70)
        def analyze_customer_data(data_source, analysis_type):
            # This function will only run if data_source meets
            # the minimum quality score of 70
            print(f"Analyzing {data_source} for {analysis_type}")
            # ... analysis code ...
            return results
        ```
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract data source path from args or kwargs
            data_source = None
            if data_source_param in kwargs:
                data_source = kwargs[data_source_param]
            
            if not data_source:
                # Try to find it in positional args based on function signature
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if data_source_param in params:
                    idx = params.index(data_source_param)
                    if idx < len(args):
                        data_source = args[idx]
            
            if not data_source:
                raise ValueError(f"Could not find data source parameter '{data_source_param}'")
                
            # Assess data quality
            assessor = DataSourceAssessor()
            report = assessor.assess_file(data_source)
            
            # Check if quality meets minimum score
            if report.overall_score < min_score:
                raise ValueError(
                    f"Data quality insufficient for agent use. "
                    f"ADRI Score: {report.overall_score}/100 "
                    f"(Required: {min_score}/100)\n"
                    f"Readiness Level: {report.readiness_level}\n"
                    f"Top Issues: {report.summary_findings[:3]}"
                )
                
            # If quality is sufficient, proceed with the function
            return func(*args, **kwargs)
            
        return wrapper
    return decorator
