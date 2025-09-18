"""
ADRI Logging Module.

Audit logging and enterprise integration functionality.
Provides local CSV logging and enterprise Verodat integration.

Components:
- LocalLogger: CSV-based audit logging for local development
- EnterpriseLogger: Verodat integration for enterprise environments

This module provides comprehensive audit logging for the ADRI framework.
"""

from .enterprise import EnterpriseLogger

# Import logging components
from .local import LocalLogger

# Export all components
__all__ = ["LocalLogger", "EnterpriseLogger"]
