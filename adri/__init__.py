"""
ADRI - Stop Your AI Agents Breaking on Bad Data.

A data quality assessment framework that protects AI agents from unreliable data.
Simple decorator-based API with comprehensive CLI tools for data teams.

Key Features:
- @adri_protected decorator for automatic data quality checks
- CLI tools for assessment, standard generation, and reporting
- YAML-based standards for transparency and collaboration
- Five-dimension quality assessment (validity, completeness, freshness, consistency, plausibility)
- Framework integrations for LangChain, CrewAI, LangGraph, and more

Quick Start:
    from adri import adri_protected

    @adri_protected(data_param="customer_data")
    def my_agent_function(customer_data):
        # Your agent logic here
        return process_data(customer_data)

CLI Usage:
    adri setup                              # Initialize ADRI in project
    adri generate-standard data.csv         # Generate quality standard
    adri assess data.csv --standard std.yaml  # Run assessment
"""

from .decorators.guard import adri_protected
from .version import __version__, get_version_info

# Import what actually exists, with fallbacks for missing components
try:
    from .core.assessor import DataQualityAssessor
except ImportError:
    DataQualityAssessor = None  # type: ignore

try:
    from .core.protection import DataProtectionEngine
except ImportError:
    DataProtectionEngine = None  # type: ignore

try:
    from .analysis.data_profiler import DataProfiler
except ImportError:
    DataProfiler = None  # type: ignore

try:
    from .analysis.standard_generator import StandardGenerator
except ImportError:
    StandardGenerator = None  # type: ignore

__all__ = ["__version__", "adri_protected", "get_version_info"]

# Add available components to __all__
if DataQualityAssessor is not None:
    __all__.append("DataQualityAssessor")
if DataProtectionEngine is not None:
    __all__.append("DataProtectionEngine")
if DataProfiler is not None:
    __all__.append("DataProfiler")
if StandardGenerator is not None:
    __all__.append("StandardGenerator")

# Version information
__author__ = "Thomas"
__email__ = "thomas@adri.dev"
__license__ = "MIT"
__description__ = (
    "Stop Your AI Agents Breaking on Bad Data - Data Quality Assessment Framework"
)
__url__ = "https://github.com/adri-framework/adri"
