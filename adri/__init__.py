"""
Agent Data Readiness Index (ADRI)

A framework for evaluating how well data sources communicate their quality to AI agents.
"""

import logging

from .assessor import DataSourceAssessor
from .report import AssessmentReport

__version__ = "0.1.0"
__author__ = "Verodat"

# Set up a null handler to avoid "No handler found" warnings
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "DataSourceAssessor",
    "AssessmentReport",
]
