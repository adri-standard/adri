"""
ADRI Certification Templates

This module provides a framework for defining and evaluating data quality
requirements through certification templates. Templates allow industry bodies,
regulatory authorities, and organizations to specify their specific data
quality standards while leveraging the ADRI assessment methodology.
"""

from .base import BaseTemplate
from .evaluation import TemplateEvaluation, TemplateGap, TemplateRequirement
from .registry import TemplateRegistry
from .loader import TemplateLoader
from .yaml_template import YAMLTemplate
from .exceptions import (
    TemplateError,
    TemplateNotFoundError,
    TemplateValidationError,
    TemplateSecurityError,
    TemplateVersionError,
    TemplateCacheError
)

__all__ = [
    'BaseTemplate',
    'TemplateEvaluation',
    'TemplateGap',
    'TemplateRequirement',
    'TemplateRegistry',
    'TemplateLoader',
    'YAMLTemplate',
    'TemplateError',
    'TemplateNotFoundError',
    'TemplateValidationError',
    'TemplateSecurityError',
    'TemplateVersionError',
    'TemplateCacheError',
]

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/templates/test_base_template.py
#    - tests/unit/templates/test_registry.py
#    - tests/unit/templates/test_evaluation.py
# 
# 2. Integration tests:
#    - tests/integration/templates/test_template_assessment.py
#    - tests/integration/templates/test_url_loading.py
#
# Complete test coverage details are documented in:
# docs/test_coverage/TEMPLATES_test_coverage.md
# ----------------------------------------------
