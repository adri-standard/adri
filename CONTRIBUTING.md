# Contributing to ADRI

We love your input! We want to make contributing to the Agent Data Readiness Index as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### Issue-First Workflow

To maintain project visibility and enable collaboration, we follow an issue-first approach for most contributions.

#### When Issues Are Required

Create an issue **before** starting work on:
- Any functional changes to the codebase
- New features (even small ones)
- Bug fixes (except critical hotfixes)
- Documentation changes beyond simple typos
- Any changes to standards, templates, or dimensions
- Refactoring or code improvements

#### When Direct PRs Are Allowed

You may submit a PR without a prior issue for:
- Typo fixes in documentation
- Formatting improvements
- Comment clarifications
- Build/CI configuration improvements
- Emergency security fixes (create issue after PR)

### Contribution Workflow

1. **Check Existing Issues**: Search for existing issues to avoid duplicates
2. **Create or Claim an Issue**: 
   - Create a new issue describing what you plan to work on
   - Comment on an existing issue to claim it
   - Wait for maintainer acknowledgment before starting major work
3. **Fork the Repository**: Create your own fork
4. **Create a Feature Branch**: 
   - Use descriptive branch names: `issue-123-add-validation`
   - Format: `issue-<number>-<short-description>`
5. **Make Your Changes**: 
   - Follow coding standards
   - Write/update tests
   - Update documentation
6. **Commit with Issue References**:
   - Use `Fixes #123` in commit messages to auto-close issues
   - Or `Related to #123` for partial implementations
7. **Push and Create PR**:
   - Push to your fork
   - Create a PR referencing the issue
   - Use PR template to provide context

### Pull Request Best Practices

- **Branch Naming**: Use `issue-<number>-<short-description>` format
- **Commit Messages**: Reference issues with `Fixes #123` or `Related to #123`
- **PR Title**: Include issue number, e.g., "Fix validation logic for empty fields (#123)"
- **PR Description**: Use the PR template and provide context about the changes
- **Small PRs**: Keep changes focused - one issue per PR when possible

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

## Contributing Templates

Templates are a crucial part of ADRI's value proposition. They define standardized data quality requirements for specific use cases and industries.

For detailed guidance on creating and contributing templates, see our dedicated **[Template Contribution Guide](docs/CONTRIBUTING_TEMPLATES.md)**.

### Quick Template Contribution

1. Browse existing templates in `adri/templates/catalog/`
2. Copy a similar template as your starting point
3. Customize for your use case
4. Test with real data
5. Submit a PR with your template

Templates help the entire community by establishing industry standards for agent-ready data.

## Questions?

Feel free to contact the project maintainers if you have any questions or need further clarification.
