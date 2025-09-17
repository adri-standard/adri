"""
ADRI Logging Module

Handles audit logging and enterprise logging functionality.
Consolidates logging components from the original core/audit_logger*.py and core/verodat_logger.py.

Components:
- LocalLogger: Local CSV-based logging implementation
- EnterpriseLogger: Enterprise/Verodat logging implementation
- log_to_csv: CSV audit logging function
- log_to_verodat: Verodat logging function

This module provides unified logging interfaces for the ADRI framework.
"""

# Import local CSV-based logging
from .local import LocalLogger, AuditRecord, log_to_csv, CSVAuditLogger

# Import enterprise Verodat logging
from .enterprise import EnterpriseLogger, log_to_verodat, VerodatLogger

# Export all components
__all__ = [
    "LocalLogger", 
    "AuditRecord", 
    "log_to_csv", 
    "CSVAuditLogger",
    "EnterpriseLogger", 
    "log_to_verodat", 
    "VerodatLogger"
]
