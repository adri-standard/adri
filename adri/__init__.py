"""
Agent Data Readiness Index (ADRI) package.

This package provides tools for assessing the quality of data sources
for use with AI agents, focusing on multiple dimensions of data quality.
"""

from .version import __version__
from .integrations.guard import adri_guarded
from .assessor import DataSourceAssessor

__all__ = ["__version__", "adri_guarded", "DataSourceAssessor"]
