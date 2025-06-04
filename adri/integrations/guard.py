"""
Guard decorator for enforcing data quality standards in agent functions.

This module provides the adri_guarded decorator that can be used to ensure
data sources meet minimum quality standards before being used by agents.

Test coverage for this implementation is documented in:
docs/test_coverage/guard_implementation_test_coverage.md
"""

import functools
import inspect
from typing import Any, Callable, Dict, Optional, Union
from pathlib import Path
from datetime import datetime, timedelta

from ..assessor import DataSourceAssessor
from ..report import ADRIScoreReport


def adri_guarded(
    min_score: float = 80, 
    data_source_param: str = "data_source", 
    dimensions: Optional[Dict[str, float]] = None,
    use_cached_reports: bool = True,
    max_report_age_hours: Optional[int] = None,
    save_reports: bool = True,
    verbose: bool = False
):
    """
    Decorator to guard agent functions with ADRI quality checks.
    
    This decorator first checks for an existing ADRI report file. If found and valid,
    it uses that report for validation. Otherwise, it performs a new assessment.
    
    Args:
        min_score: Minimum ADRI score required to proceed (0-100)
        data_source_param: Name of the parameter containing the data source path
        dimensions: Optional dictionary of dimension-specific score requirements
        use_cached_reports: Whether to use existing report files (default: True)
        max_report_age_hours: Maximum age of report files in hours (default: None)
        save_reports: Whether to save new assessment reports (default: True)
        verbose: Whether to print status messages during assessment (default: False)
        
    Raises:
        ValueError: If data quality doesn't meet the minimum score
        
    Example:
        ```python
        @adri_guarded(
            min_score=70,
            dimensions={"plausibility": 15},
            use_cached_reports=True,
            max_report_age_hours=24
        )
        def analyze_customer_data(data_source, analysis_type):
            # This function will first check for an existing report file
            # before running a new assessment
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
            
            # Initialize report to None
            report = None
            report_path = Path(data_source).with_suffix('').with_suffix('.adri_score_report.json')
            
            # Check for existing report if caching is enabled
            if use_cached_reports and report_path.exists():
                try:
                    # Load the existing report
                    report = ADRIScoreReport.load_json(report_path)
                    
                    # Verify report is not too old if max_age specified
                    if max_report_age_hours is not None:
                        # Handle datetime in string or datetime format
                        if isinstance(report.assessment_time, str):
                            report_time = datetime.fromisoformat(report.assessment_time)
                        else:
                            # If assessment_time is already a datetime object or something else
                            # In production code, we'd add more robust handling here
                            report_time = datetime.now()  # Default to now if unparseable
                        max_age = timedelta(hours=max_report_age_hours)
                        
                        if datetime.now() - report_time > max_age:
                            if verbose:
                                print(f"Cached report exceeded max age ({max_report_age_hours} hours)")
                            report = None  # Report too old, need fresh assessment
                        elif verbose:
                            print(f"Using cached assessment report from {report.assessment_time}")
                    elif verbose:
                        print(f"Using cached assessment report (no age limit)")
                            
                except Exception as e:
                    if verbose:
                        print(f"Could not use cached report: {e}")
                    report = None  # Invalid report, need fresh assessment
            
            # If no valid cached report, perform assessment
            if report is None:
                if verbose:
                    print("Running fresh ADRI assessment...")
                assessor = DataSourceAssessor()
                report = assessor.assess_file(data_source)
                
                # Save the new report for future use if requested
                if save_reports:
                    try:
                        report.save_json(report_path)
                        if verbose:
                            print(f"Saved assessment report to {report_path}")
                    except Exception as e:
                        if verbose:
                            print(f"Could not save assessment report: {e}")
            
            # Check overall score requirement
            if report.overall_score < min_score:
                raise ValueError(
                    f"Data quality insufficient for agent use. "
                    f"ADRI Score: {report.overall_score}/100 "
                    f"(Required: {min_score}/100)\n"
                    f"Top Issues: {report.summary_findings[:3]}"
                )
            
            # Check dimension-specific requirements if specified
            if dimensions:
                for dim_name, required_score in dimensions.items():
                    if dim_name in report.dimension_results:
                        actual_score = report.dimension_results[dim_name]["score"]
                        if actual_score < required_score:
                            raise ValueError(
                                f"Dimension '{dim_name}' score insufficient: "
                                f"{actual_score}/20 (required: {required_score}/20)\n"
                                f"Top Issues: {report.dimension_results[dim_name]['findings'][:2]}"
                            )
                    else:
                        raise ValueError(f"Required dimension '{dim_name}' not found in report")
                
            # If quality is sufficient, proceed with the function
            return func(*args, **kwargs)
            
        return wrapper
    return decorator
