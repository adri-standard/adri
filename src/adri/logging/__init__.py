"""
ADRI Logging Module.

Audit logging and Verodat integration functionality.
Provides local JSONL logging and simplified Verodat bridge.

Components:
- LocalLogger: JSONL-based audit logging for local development
- send_to_verodat: Simplified function for basic Verodat integration
- ADRILogReader: JSONL log reader for workflow orchestration and CLI commands

For full enterprise features including ReasoningLogger, WorkflowLogger,
and advanced Verodat integration, use the adri-enterprise package.
"""

from .enterprise import send_to_verodat

# Import logging components
from .local import LocalLogger
from .log_reader import (
    ADRILogReader,
    AssessmentLogRecord,
    DimensionScoreRecord,
    FailedValidationRecord,
)

# Export all components
__all__ = [
    "LocalLogger",
    "send_to_verodat",
    "ADRILogReader",
    "AssessmentLogRecord",
    "DimensionScoreRecord",
    "FailedValidationRecord",
]
