"""
Command-line interface for ADRI V2.

This module provides the CLI commands for the simplified ADRI implementation.
"""

from .commands import (
    setup_command, 
    assess_command, 
    validate_standard_command, 
    show_config_command,
    generate_adri_standard_command,
    list_standards_command,
    list_training_data_command,
    list_assessments_command,
    clean_cache_command,
    export_report_command,
    show_standard_command,
    explain_failure_command
)

__all__ = [
    'setup_command', 
    'assess_command', 
    'validate_standard_command', 
    'show_config_command',
    'generate_adri_standard_command',
    'list_standards_command',
    'list_training_data_command',
    'list_assessments_command',
    'clean_cache_command',
    'export_report_command',
    'show_standard_command',
    'explain_failure_command'
]
