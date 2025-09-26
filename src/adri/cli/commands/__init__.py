"""CLI commands package for the ADRI framework.

This package contains individual command implementations that replace the
monolithic cli.py structure. Each command is implemented as a focused class
following the Command pattern.
"""

from .assess import AssessCommand
from .config import (
    ListStandardsCommand,
    ShowConfigCommand,
    ShowStandardCommand,
    ValidateStandardCommand,
)
from .generate_standard import GenerateStandardCommand
from .list_assessments import ListAssessmentsCommand
from .scoring import ScoringExplainCommand, ScoringPresetApplyCommand
from .setup import SetupCommand
from .view_logs import ViewLogsCommand

__all__ = [
    "SetupCommand",
    "AssessCommand",
    "GenerateStandardCommand",
    "ListAssessmentsCommand",
    "ViewLogsCommand",
    "ShowConfigCommand",
    "ValidateStandardCommand",
    "ListStandardsCommand",
    "ShowStandardCommand",
    "ScoringExplainCommand",
    "ScoringPresetApplyCommand",
]
