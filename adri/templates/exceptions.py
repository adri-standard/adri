"""
Exceptions for the ADRI templates system.
"""


class TemplateError(Exception):
    """Base exception for all template-related errors."""
    pass


class TemplateNotFoundError(TemplateError):
    """Raised when a requested template cannot be found."""
    pass


class TemplateLoadError(TemplateError):
    """Raised when a template cannot be loaded."""
    pass


class TemplateValidationError(TemplateError):
    """Raised when a template fails validation."""
    pass


class TemplateSecurityError(TemplateError):
    """Raised when a template fails security checks."""
    pass


class TemplateVersionError(TemplateError):
    """Raised when there are template version conflicts."""
    pass


class TemplateCacheError(TemplateError):
    """Raised when there are template caching issues."""
    pass

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/templates/test_exceptions.py
# 
# 2. Integration tests:
#    - tests/integration/templates/test_error_handling.py
#
# Complete test coverage details are documented in:
# docs/test_coverage/TEMPLATES_test_coverage.md
# ----------------------------------------------
