"""
ADRI Logging Module.

Audit logging and enterprise integration functionality.
Provides local JSONL logging and enterprise Verodat integration.

Components:
- LocalLogger: JSONL-based audit logging for local development
- EnterpriseLogger: Verodat integration for enterprise environments
- ReasoningLogger: JSONL-based logging for AI reasoning prompts and responses
- WorkflowLogger: JSONL-based logging for workflow execution and data provenance
- ADRILogReader: JSONL log reader for workflow orchestration and CLI commands

This module provides comprehensive audit logging for the ADRI framework.
"""

from .enterprise import EnterpriseLogger

# Import logging components
from .local import LocalLogger
from .log_reader import (
    ADRILogReader,
    AssessmentLogRecord,
    DimensionScoreRecord,
    FailedValidationRecord,
)
from .reasoning import ReasoningLogger
from .workflow import WorkflowLogger

# Export all components
__all__ = [
    "LocalLogger",
    "EnterpriseLogger",
    "ReasoningLogger",
    "WorkflowLogger",
    "ADRILogReader",
    "AssessmentLogRecord",
    "DimensionScoreRecord",
    "FailedValidationRecord",
]
