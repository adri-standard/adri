"""
verodat-adri - Enterprise Edition: Stop Your AI Agents Breaking on Bad Data.

An enterprise data quality assessment framework with Verodat cloud integration,
event-driven logging, and workflow orchestration. Built on community ADRI foundation.

Key Features:
- @adri_protected decorator for automatic data quality checks
- Enterprise: Verodat cloud integration with 5s flush (vs 60s community)
- Enterprise: Fast-path logging for <10ms assessment ID capture
- Enterprise: Event-driven architecture for real-time workflow coordination
- Enterprise: Async callbacks and workflow adapters (Prefect, Airflow)
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
from .logging.enterprise import EnterpriseLogger
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
    "EnterpriseLogger",
    "ConfigurationLoader",
    "DataProfiler",
    "StandardGenerator",
    "TypeInference",
]

# Package metadata
__author__ = "Verodat"
__email__ = "adri@verodat.com"
__license__ = "Apache-2.0"
__description__ = (
    "Enterprise Edition: Stop Your AI Agents Breaking on Bad Data - "
    "Data Quality Assessment with Verodat Cloud Integration, Event-Driven Logging, "
    "and Workflow Orchestration"
)
__url__ = "https://github.com/Verodat/verodat-adri"
# verodat-adri v5.0.0 - Enterprise Edition First Release
# Forked from community ADRI v4.4.0 with enterprise features
