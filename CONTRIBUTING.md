# Contributing to ADRI

**Stop AI Agents Breaking on Bad Data**

Thank you for your interest in contributing to ADRI! We welcome contributions from the AI framework community to help protect agents from bad data with one line of code.

**Join the Movement**: Help make AI agents bulletproof across LangChain, CrewAI, AutoGen, LlamaIndex, Haystack, LangGraph, and Semantic Kernel.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Reporting Issues](#reporting-issues)
- [Submitting Pull Requests](#submitting-pull-requests)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to ensure a welcoming environment for all contributors.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/adri.git
   cd adri
   ```
3. Add the upstream repository as a remote:
   ```bash
   git remote add upstream https://github.com/adri-standard/adri.git
   ```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip and virtualenv (or conda)
- Git

### Setting Up Your Development Environment

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the package in development mode with all dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

4. Run the test suite to verify everything is working:
   ```bash
   pytest
   ```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug Fixes**: Fix issues reported in our issue tracker
- **Features**: Implement new features or enhance existing ones
- **Documentation**: Improve documentation, add examples, or fix typos
- **Tests**: Add missing tests or improve test coverage
- **Standards**: Contribute new data quality standards or improve existing ones
- **Framework Integration**: Add support for new AI agent frameworks
- **Performance**: Optimize code for better performance

### Finding Issues to Work On

- Check our [issue tracker](https://github.com/adri-standard/adri/issues) for open issues
- Look for issues labeled `good first issue` if you're new to the project
- Issues labeled `help wanted` are particularly important to the project

## Reporting Issues

### Before Reporting

1. Check if the issue has already been reported
2. Ensure you're using the latest version of ADRI
3. Verify the issue is reproducible

### How to Report

When creating an issue, please include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Your environment details (Python version, OS, etc.)
- Any relevant code samples or error messages
- Screenshots if applicable

## Submitting Pull Requests

### Before You Submit

1. Ensure your code follows our coding standards
2. Write or update tests for your changes
3. Update documentation if needed
4. Run the full test suite locally
5. Ensure all pre-commit hooks pass

### Pull Request Process

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them with descriptive messages:
   ```bash
   git commit -m "feat: add new validation for data completeness"
   ```

3. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Open a Pull Request on GitHub with:
   - A clear title and description
   - Reference to any related issues
   - A summary of the changes made
   - Screenshots or examples if applicable

5. Address any feedback from reviewers promptly

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Test additions or modifications
- `chore:` Maintenance tasks
- `perf:` Performance improvements

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints for function parameters and return values
- Maximum line length: 100 characters
- Use descriptive variable and function names

### Code Quality Tools

We use the following tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **bandit**: Security analysis

Run all checks with:
```bash
pre-commit run --all-files
```

## Testing Guidelines

### Writing Tests

- Write tests for all new features and bug fixes
- Place tests in the appropriate directory under `tests/`
- Use descriptive test names that explain what is being tested
- Include both positive and negative test cases
- Mock external dependencies when appropriate

### Test Structure

```python
def test_descriptive_name():
    """Test that [specific behavior] works correctly."""
    # Arrange
    input_data = prepare_test_data()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_value
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=adri --cov-report=html

# Run specific test file
pytest tests/unit/test_specific.py

# Run with verbose output
pytest -v
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function.

    Longer description if needed, explaining the function's
    purpose and behavior in more detail.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is invalid

    Example:
        >>> function_name("test", 42)
        True
    """
```

### Updating Documentation

- Update relevant documentation when adding or modifying features
- Ensure examples in documentation are working and tested
- Keep the README.md up to date with new features
- Document any breaking changes in CHANGELOG.md

## Creating New Standards

If you're contributing a new data quality standard:

1. Create a YAML file in `adri/standards/bundled/`
2. Follow the existing standard template structure
3. Include comprehensive test cases
4. Document the standard's purpose and usage
5. Add examples demonstrating the standard

Example standard structure:
```yaml
meta:
  name: "your_standard_name"
  version: "1.0.0"
  description: "Clear description of what this standard validates"
  author: "Your Name"

fields:
  - name: "field_name"
    type: "string"
    required: true
    constraints:
      - type: "pattern"
        value: "^[A-Z]+$"
        message: "Field must contain only uppercase letters"
```

## Framework Integration

When adding support for a new AI agent framework:

1. Create an example in `examples/` directory
2. Ensure the @adri_protected decorator works seamlessly
3. Document any framework-specific considerations
4. Add integration tests
5. Update the README with the new framework

## Performance Considerations

- Avoid premature optimization
- Profile code before optimizing
- Consider memory usage for large datasets
- Use generators for processing large files
- Cache expensive computations when appropriate

## Release Process

We follow semantic versioning (MAJOR.MINOR.PATCH):

- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

## Community

### Getting Help

- Check the documentation first
- Search existing issues and discussions
- Ask questions in GitHub Discussions
- Join our community chat (if available)

### Staying Updated

- Watch the repository for updates
- Subscribe to release notifications
- Follow our blog/changelog for major updates

## Recognition

Contributors who make significant contributions will be:
- Added to the AUTHORS file
- Mentioned in release notes
- Given credit in the documentation

## License

By contributing to ADRI, you agree that your contributions will be licensed under the same license as the project (Apache 2.0).

## Questions?

If you have questions about contributing, feel free to:
- Open a discussion on GitHub
- Contact the maintainers
- Check our FAQ section

Thank you for helping make ADRI better for everyone! 🎉
