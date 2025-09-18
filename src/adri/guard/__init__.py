"""
ADRI Guard Module.

Handles data protection modes and guard functionality.
Consolidates protection logic from the original core/protection.py.

Components:
- ProtectionMode: Base class for protection modes
- FailFastMode: Fail-fast protection implementation
- SelectiveMode: Selective protection implementation
- WarnOnlyMode: Warning-only protection implementation
- DataProtectionEngine: Main protection orchestrator

This module provides the data protection capabilities for the ADRI framework.
"""

# Import guard mode components
from .modes import (
    DataProtectionEngine,
    fail_fast_mode,
    FailFastMode,
    ProtectionError,
    ProtectionMode,
    selective_mode,
    SelectiveMode,
    warn_only_mode,
    WarnOnlyMode,
)

# Export all components
__all__ = [
    "ProtectionMode",
    "FailFastMode",
    "SelectiveMode",
    "WarnOnlyMode",
    "DataProtectionEngine",
    "ProtectionError",
    "fail_fast_mode",
    "selective_mode",
    "warn_only_mode",
]
