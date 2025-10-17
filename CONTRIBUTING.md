# Contributing to verodat-adri

**Enterprise Edition: Stop AI Agents Breaking on Bad Data**

Thank you for your interest in contributing to verodat-adri! We welcome contributions from the AI framework community to help protect agents from bad data with enterprise-grade features.

**Join the Movement**: Help make AI agents bulletproof across LangChain, CrewAI, AutoGen, LlamaIndex, Haystack, LangGraph, and Semantic Kernel.

---

## 🚀 **Quick Start - New Contributors**

**Want to jump right in?** Check out our **[Quick Contribution Guide](development/docs/QUICK_CONTRIBUTION_GUIDE.md)** for the fastest path to contributing!

- 🌟 **First time?** → [Browse good first issues](https://github.com/Verodat/verodat-adri/labels/good%20first%20issue)
- 🔧 **Have an idea?** → [Create an issue](https://github.com/Verodat/verodat-adri/issues/new/choose)
- 📚 **See a typo?** → Just fix it and create a PR!

**Our smart automation adapts to your changes** - documentation updates are super easy, core functionality gets extra quality attention.

---

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
   git clone https://github.com/YOUR_USERNAME/verodat-adri.git
   cd verodat-adri
   ```
3. Add the upstream repository as a remote (for syncing with community ADRI):
   ```bash
   git remote add upstream https://github.com/adri-standard/adri.git
   ```
   Note: This upstream points to community ADRI for core module synchronization.

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

### Issue-First Workflow ⚠️ ENFORCED

**All contributions MUST start with a GitHub issue.** This is automatically enforced by our CI pipeline - branches that don't follow the issue-first convention will be rejected.

📚 **Complete Guide**: See our detailed [Issue-Driven Development Workflow](docs/CONTRIBUTOR_DOCS/ISSUE_DRIVEN_WORKFLOW.md) for comprehensive instructions and examples.

#### Before You Code

1. **Check existing issues** - Your idea might already be discussed
2. **Create an issue** - Use our comprehensive issue templates for consistency:

### Available Issue Templates

We provide specialized templates to streamline different types of contributions:

**General Templates:**
- **🚀 Feature Request** - For completely new functionality
- **⚡ Enhancement** - For improvements to existing features
- **🐛 Bug Report** - For general bugs or unexpected behavior
- **🐛 Data Quality Bug Report** - For issues specific to data quality assessment or validation
- **💬 Discussion** - For architectural decisions or community input

**Framework-Specific Templates:**
- **AutoGen Integration** - Issues with Microsoft AutoGen framework
- **CrewAI Integration** - Issues with CrewAI framework
- **LangChain Integration** - Issues with LangChain framework

**Template Features:**
- Pre-filled labels and assignees
- Structured sections for consistent reporting
- Framework compatibility checkboxes
- Integration with our issue-driven workflow
- Automatic branch naming guidance

**Choosing the Right Template:**
- Use **Bug Report** for general issues
- Use **Data Quality Bug Report** for validation/assessment problems
- Use framework-specific templates when the issue is framework-related
- Use **Feature Request** for new capabilities
- Use **Enhancement** for improving existing features
- Use **Discussion** for broader topics requiring community input
3. **Get feedback** - Allow time for community input before implementation
4. **Issue assignment** - Comment on the issue to request assignment

#### Branch Naming Convention ⚠️ AUTOMATICALLY ENFORCED

Create branches that reference the issue number using our standardized format:

```bash
# Format: type/issue-{number}-brief-description
feat/issue-123-user-authentication
fix/issue-456-memory-leak
docs/issue-789-api-documentation
enhance/issue-321-performance-improvement
```

**Valid types**: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `style`, `perf`, `enhance`, `hotfix`

🚨 **IMPORTANT**: Our branch validation workflow will automatically reject branches that don't follow this convention. You'll get immediate feedback with helpful guidance on how to fix the branch name.

#### What Happens If You Don't Follow Convention:

```bash
❌ BRANCH REJECTED: Invalid naming convention
Required format: type/issue-{number}-description

To fix this:
1. Create a GitHub issue for your work
2. Rename your branch: git branch -m type/issue-{number}-description
3. Push again: git push -u origin HEAD
```

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

- Check our [issue tracker](https://github.com/Verodat/verodat-adri/issues) for open issues
- Look for issues labeled `good first issue` if you're new to the project
- Issues labeled `help wanted` are particularly important to the project
- **No issue for your idea?** Create one using our templates!

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

1. **Ensure you have a linked issue** - All PRs must reference a GitHub issue

2. Create a new branch following our naming convention:
   ```bash
   git checkout -b feat/issue-123-your-feature-name
   ```

3. Make your changes and commit them with descriptive messages:
   ```bash
   git commit -m "feat: add new validation for data completeness (fixes #123)"
   ```

4. Push your branch to your fork:
   ```bash
   git push origin feat/issue-123-your-feature-name
   ```

5. Open a Pull Request on GitHub using the PR template:
   - **Required**: Link to the GitHub issue (e.g., "Fixes #123")
   - Clear title and description
   - Completed testing checklist
   - Documentation updates (if applicable)
   - Screenshots or examples if applicable

6. **Automated checks**: Our GitHub Actions will verify:
   - Issue is properly linked
   - Branch naming follows convention
   - All tests pass
   - Code quality standards are met

7. Address any feedback from reviewers promptly

#### PR Requirements

✅ **Must Have:**
- Linked GitHub issue
- Proper branch naming
- Passing automated tests
- Updated documentation (if needed)
- Conventional commit messages

❌ **Will Block Merge:**
- No linked issue
- Failing tests
- Code quality issues
- Missing documentation for new features

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
- Maximum line length: 88 characters (enforced by Black)
- Use descriptive variable and function names

### Cross-Platform Compatibility ⚠️ CRITICAL

**ADRI runs on Windows, macOS, and Linux.** Always specify `encoding='utf-8'` when opening text files:

```python
# ✅ CORRECT - Works on all platforms
with open('file.yaml', 'r', encoding='utf-8') as f:
    content = f.read()

# ❌ WRONG - Fails on Windows (uses cp1252 instead of UTF-8)
with open('file.yaml', 'r') as f:
    content = f.read()
```

**Why this matters**: Windows uses cp1252 encoding by default, while macOS/Linux use UTF-8. Code that works on your Mac will fail on Windows CI if you don't specify encoding.

**VS Code Snippets**: Type `openr`, `openw`, `yamlload`, etc. for auto-completion with correct encoding.

**Pre-commit Hook**: Our encoding check will catch missing encoding parameters before commit.

**See**: [Cross-Platform Best Practices Guide](docs/development/CROSS_PLATFORM_BEST_PRACTICES.md)

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

By contributing to verodat-adri, you agree that your contributions will be licensed under the same license as the project (Apache 2.0).

## Enterprise Features

When contributing to verodat-adri, be aware of:
- **Protected Enterprise Modules**: src/adri/logging/enterprise.py, src/adri/events/, src/adri/callbacks/
- **Syncable Core Modules**: src/adri/decorator.py, src/adri/validator/, src/adri/guard/
- See [UPSTREAM_SYNC.md](UPSTREAM_SYNC.md) for synchronization guidelines
- See [ENTERPRISE_FEATURES.md](ENTERPRISE_FEATURES.md) for feature differentiation

## Questions?

If you have questions about contributing, feel free to:
- Open a discussion on GitHub: https://github.com/Verodat/verodat-adri/discussions
- Contact the Verodat team: adri@verodat.com
- Check our FAQ section
- Review community ADRI: https://github.com/adri-standard/adri

Thank you for helping make verodat-adri better for everyone! 🎉
