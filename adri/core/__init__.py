"""
ADRI Core Module.

Core functionality for data quality protection and assessment.
"""

from .protection import DataProtectionEngine, ProtectionError

__all__ = ["DataProtectionEngine", "ProtectionError"]
