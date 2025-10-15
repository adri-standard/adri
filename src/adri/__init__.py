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

    @adri_protected(standard="customer_data_standard")
    def my_agent_function(customer_data):
        # Your agent logic here
        return process_data(customer_data)

CLI Usage:
    adri setup                              # Initialize ADRI in project
    adri generate-standard data.csv         # Generate quality standard
    adri assess data.csv --standard std.yaml  # Run assessment
"""

from .analysis import DataProfiler, StandardGenerator, TypeInference
from .config.loader import ConfigurationLoader

# Core public API imports
from .decorator import adri_protected
from .guard.modes import DataProtectionEngine
from .logging.enterprise import send_to_verodat
from .logging.local import LocalLogger

# Core component imports
from .validator.engine import DataQualityAssessor, ValidationEngine

# Version information - updated import for src/ layout
from .version import __version__, get_version_info

# Public API exports
__all__ = [
    "__version__",
    "get_version_info",
    "adri_protected",
    "DataQualityAssessor",
    "ValidationEngine",
    "DataProtectionEngine",
    "LocalLogger",
    "send_to_verodat",
    "ConfigurationLoader",
    "DataProfiler",
    "StandardGenerator",
    "TypeInference",
]

# Package metadata
__author__ = "Thomas"
__email__ = "thomas@adri.dev"
__license__ = "MIT"
__description__ = (
    "Stop Your AI Agents Breaking on Bad Data - Data Quality Assessment Framework"
)
__url__ = "https://github.com/adri-framework/adri"
# Release v4.3.0
# Trigger CI for v4.4.0 changelog
