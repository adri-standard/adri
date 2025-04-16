"""
Agent Data Readiness Index (ADRI)

A framework for evaluating how well data sources communicate their quality to AI agents.
"""

import logging

# Import dimensions and connectors to ensure registries are populated
from . import dimensions
from . import connectors

from .assessor import DataSourceAssessor
from .report import AssessmentReport
from .dimensions import DimensionRegistry, register_dimension
from .connectors import ConnectorRegistry, register_connector
from .integrations import adri_guarded

__version__ = "0.1.0"
__author__ = "Verodat"

# Set up a null handler to avoid "No handler found" warnings
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "DataSourceAssessor",
    "AssessmentReport",
    "DimensionRegistry",
    "ConnectorRegistry",
    "register_dimension",
    "register_connector",
    "adri_guarded",
]
