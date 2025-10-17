# Contributing to ADRI

Thank you for your interest in contributing to ADRI! We welcome contributions that help make data quality protection easier for AI agent engineers.

## Quick Start

1. **Fork** the repository on GitHub
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/adri.git
   cd adri
   ```

3. **Set up** development environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   pre-commit install
   ```

4. **Make your changes** and test:
   ```bash
   pytest tests/
   ```

5. **Submit** a pull request

## What We're Looking For

### High Priority

- 🐛 **Bug fixes** - Especially for decorator behavior
- 🔧 **Framework integrations** - New AI agent framework examples
- 📝 **Documentation** - Clearer examples, better guides
- ✨ **Usability improvements** - Make ADRI easier to use

### Welcome Contributions

- 🧪 **Tests** - Increase coverage
- 📊 **Standards** - Domain-specific quality standards
- 💡 **Examples** - Real-world use cases
- 🎨 **Code quality** - Performance, clarity, maintainability

### Not Currently Accepting

- 🚫 **Major architectural changes** - Discuss first in issues
- 🚫 **Breaking changes** - Must maintain decorator API stability

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

Focus on:
- **Decorator-first** patterns
- **Developer experience**
- **Framework agnostic** solutions
- **Clear, simple code**

### 3. Write Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/decorators/test_guard.py

# Run with coverage
pytest --cov=adri --cov-report=html
```

### 4. Update Documentation

If you're adding features:
- Update relevant docs in `docs/`
- Add examples if applicable
- Update `CHANGELOG.md`

### 5. Run Quality Checks

```bash
# Format code
black adri/

# Check style
flake8 adri/

# Run pre-commit hooks
pre-commit run --all-files
```

### 6. Submit Pull Request

- Write a clear title and description
- Reference any related issues
- Ensure CI passes

## Code Standards

### Python Style

- Follow **PEP 8** (enforced by flake8)
- Use **Black** formatting (automatic with pre-commit)
- Write **docstrings** for public functions
- Add **type hints** where helpful

### Testing

- Write tests for new features
- Maintain high test coverage
- Use descriptive test names
- Test edge cases

### Documentation

- Keep docs concise and actionable
- Use code examples liberally
- Focus on developer workflow
- Maintain decorator-first narrative

## Commit Messages

Use clear, descriptive commit messages:

```bash
# Good
git commit -m "Add LangGraph integration example"
git commit -m "Fix: Decorator fails with empty DataFrame"
git commit -m "Docs: Update QUICKSTART with CLI section"

# Avoid
git commit -m "Fix bug"
git commit -m "Update files"
git commit -m "Changes"
```

## Pull Request Guidelines

### Title Format

- **feat:** New feature
- **fix:** Bug fix
- **docs:** Documentation
- **test:** Tests
- **refactor:** Code refactoring
- **perf:** Performance improvement

### Description Template

```markdown
## Summary
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- Change 1
- Change 2
- Change 3

## Testing
How was this tested?

## Related Issues
Fixes #123
```

## Reporting Issues

### Bug Reports

Include:
- **Clear description** of the problem
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Environment** (Python version, OS, ADRI version)
- **Code example** (if applicable)

### Feature Requests

Include:
- **Use case** - What problem does this solve?
- **Proposed solution** - How should it work?
- **Alternatives** - Other approaches considered?
- **Impact** - Who benefits from this?

## Getting Help

- 📖 **Documentation**: [Full docs](https://github.com/adri-standard/adri)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/adri-standard/adri/discussions)
- 🐛 **Issues**: [Search existing issues](https://github.com/adri-standard/adri/issues)
- 📝 **Examples**: [examples/](examples/)

## Development Tips

### Running Specific Tests

```bash
# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Specific test
pytest tests/unit/decorators/test_guard.py::test_basic_protection
```

### Debugging

```bash
# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Enter debugger on failure
pytest --pdb
```

### Local Documentation

```bash
# Generate HTML docs (if using Sphinx)
cd docs
make html
open _build/html/index.html
```

## Project Structure

```
adri/
├── adri/                      # Main package
│   ├── __init__.py           # Public API
│   └── validator/            # Core implementation
│       ├── decorators/       # @adri_protected
│       ├── core/             # Protection engine
│       ├── analysis/         # Profiling & generation
│       ├── standards/        # Standard loading
│       ├── config/           # Configuration
│       └── cli/              # CLI commands
├── docs/                     # Documentation
├── examples/                 # Framework examples
├── tests/                    # Test suite
└── standards/                # Bundled standards
```

## Code of Conduct

Be respectful, inclusive, and constructive. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Recognition

Contributors are recognized in:
- Pull request comments
- Release notes
- Project README

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to ADRI!** Every improvement helps AI agent engineers build more reliable workflows. 🙏

Questions? Open a [discussion](https://github.com/adri-standard/adri/discussions) or reach out in an [issue](https://github.com/adri-standard/adri/issues).
