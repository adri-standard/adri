"""
ADRI rules package.

This package contains all diagnostic rule implementations for data quality assessment.
"""

from .base import DiagnosticRule
from .registry import RuleRegistry
from .validity import *
from .completeness import *
from .freshness import *
from .consistency import *
from .plausibility import *
