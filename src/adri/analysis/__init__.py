"""
ADRI Analysis Module.

Data analysis and contract generation functionality.
Provides data profiling and automatic contract generation capabilities.

Components:
- DataProfiler: Analyzes data patterns and structure
- ContractGenerator: Creates YAML contracts from data analysis
- TypeInference: Infers data types and validation rules

This module provides the "Data Scientist" functionality for the ADRI framework.
"""

# Import analysis components
from .data_profiler import DataProfiler, profile_dataframe
from .contract_generator import generate_contract_from_data, ContractGenerator

# Import all analysis components
from .type_inference import (
    infer_types_from_dataframe,
    infer_validation_rules_from_data,
    TypeInference,
)

# Export all components
__all__ = [
    "DataProfiler",
    "ContractGenerator",
    "TypeInference",
    "profile_dataframe",
    "generate_contract_from_data",
    "infer_types_from_dataframe",
    "infer_validation_rules_from_data",
]
