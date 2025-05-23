# Contributing to ADRI

We love your input! We want to make contributing to the Agent Data Readiness Index as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### Pull Requests

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Pull Request Requirements

- Update documentation as needed
- Write or update tests for the changes
- Ensure the test suite passes
- Make sure your code follows the existing style guidelines
- The code should be clean, readable, and maintainable

## Development Setup

1. Clone the repository
   ```bash
   git clone https://github.com/YourUsername/agent-data-readiness-index.git
   cd agent-data-readiness-index
   ```

2. Set up a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install development dependencies
   ```bash
   pip install -e ".[dev]"
   ```

4. Run tests
   ```bash
   pytest
   ```

## Coding Standards

- Follow PEP 8 style guide for Python code
- Use meaningful variable and function names
- Write docstrings for all functions, classes, and modules
- Keep functions and methods focused on a single responsibility
- Use type hints where appropriate

## Testing

- Write unit tests for all new functionality
- Ensure all tests pass before submitting a pull request
- Aim for high test coverage for new code

## Documentation

- Update the documentation to reflect any changes in functionality
- Document new features, APIs, and configuration options
- Use clear, concise language in documentation
- Include examples where helpful

## Reporting Bugs

We use GitHub issues to track public bugs. Report a bug by opening a new issue.

### Bug Report Template

**Title**: Short description of the bug

**Description**:
- Detailed description of the problem
- Steps to reproduce the behavior
- Expected behavior
- Screenshots (if applicable)
- Environment information:
  - ADRI version
  - Python version
  - Operating system
  - Additional context

## Feature Requests

We welcome feature requests! Please provide the following information:

- Clear description of the feature
- Rationale: why this feature would be beneficial
- Examples of how the feature would be used
- Potential implementation details (if you have ideas)

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## License

By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).

## Questions?

Feel free to contact the project maintainers if you have any questions or need further clarification.
