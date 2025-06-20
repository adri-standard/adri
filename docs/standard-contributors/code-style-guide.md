# Code Style Guide

> **Standard Contributors**: Coding standards for ADRI

## Overview

Coding standards and style guidelines for ADRI contributions.

## Python Style

### General Guidelines
- Follow PEP 8 for Python code
- Use type hints for all public functions
- Include comprehensive docstrings
- Maintain test coverage above 80%

### Naming Conventions
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### Documentation
- Use Google-style docstrings
- Include examples in docstrings
- Document all parameters and return values

## Testing Standards

### Test Structure
- One test file per module
- Descriptive test names
- Arrange-Act-Assert pattern
- Mock external dependencies

### Coverage Requirements
- Minimum 80% line coverage
- 100% coverage for critical paths
- Integration tests for public APIs

## Next Steps

- [Testing Guide](testing-guide.md)
- [Contribution Workflow](contribution-workflow.md)
- [Architecture Overview](architecture-overview.md)
