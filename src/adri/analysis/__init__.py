"""
ADRI Analysis Module.

Data analysis and standard generation functionality.
Provides data profiling and automatic standard generation capabilities.

Components:
- DataProfiler: Analyzes data patterns and structure
- StandardGenerator: Creates YAML standards from data analysis
- TypeInference: Infers data types and validation rules

This module provides the "Data Scientist" functionality for the ADRI framework.
"""

# Import analysis components
from .data_profiler import DataProfiler, profile_dataframe
from .standard_generator import generate_standard_from_data, StandardGenerator

# Import all analysis components
from .type_inference import (
    infer_types_from_dataframe,
    infer_validation_rules_from_data,
    TypeInference,
)

# Export all components
__all__ = [
    "DataProfiler",
    "StandardGenerator",
    "TypeInference",
    "profile_dataframe",
    "generate_standard_from_data",
    "infer_types_from_dataframe",
    "infer_validation_rules_from_data",
]
