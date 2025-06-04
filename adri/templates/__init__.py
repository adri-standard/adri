"""
ADRI Template System.

This module provides template management, loading, and matching functionality
for data quality assessments.
"""

from .base import BaseTemplate
from .evaluation import TemplateEvaluation
from .exceptions import (
    TemplateError,
    TemplateNotFoundError,
    TemplateValidationError,
    TemplateSecurityError,
    TemplateCacheError
)
from .guard import TemplateGuard
from .loader import TemplateLoader
from .registry import TemplateRegistry
from .yaml_template import YAMLTemplate
from .matcher import TemplateMatcher, ColumnMatchResult, TemplateMatchResult

__all__ = [
    'BaseTemplate',
    'TemplateEvaluation',
    'TemplateError',
    'TemplateNotFoundError',
    'TemplateValidationError',
    'TemplateSecurityError',
    'TemplateCacheError',
    'TemplateGuard',
    'TemplateLoader',
    'TemplateRegistry',
    'YAMLTemplate',
    'TemplateMatcher',
    'ColumnMatchResult',
    'TemplateMatchResult',
]
