# ADRI Validator - Local Testing Scripts

This directory contains scripts to help you test your code locally before committing, ensuring that GitHub Actions will pass without issues.

## Available Scripts

### 1. `test_local.py` (Python-based, Cross-platform)

A comprehensive Python script that runs all the same checks as GitHub Actions.

#### Basic Usage

```bash
# Run all checks (comprehensive)
python scripts/test_local.py

# Quick check (faster, essential checks only)
python scripts/test_local.py --quick

# Simulate exact CI workflow
python scripts/test_local.py --ci

# Run specific check types
python scripts/test_local.py --coverage
python scripts/test_local.py --security
```

#### Features

- **Code Formatting**: Black, isort
- **Code Quality**: Flake8, MyPy
- **Security**: Bandit, Safety
- **Testing**: Unit tests, Integration tests
- **Coverage**: With HTML report generation
- **Documentation**: Docstring checks
- **Pre-commit**: Runs pre-commit hooks if configured
- **Common Issues**: Detects print statements, TODO comments

### 2. `test-local.sh` (Bash script, Unix/Linux/macOS)

A bash script that provides similar functionality with colored output.

#### Usage

```bash
# Make executable (first time only)
chmod +x scripts/test-local.sh

# Run all checks
./scripts/test-local.sh
```

## Installation Requirements

Before using these scripts, ensure you have the required tools installed:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Or install individual tools
pip install black isort flake8 mypy pytest pytest-cov bandit safety pre-commit
```

## Using `act` for Local GitHub Actions Testing

For the most accurate simulation of GitHub Actions, install and use `act`:

### Installation

```bash
# macOS with Homebrew
brew install act

# Or using the install script
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

### Usage

```bash
# Run all workflows
act

# Run specific workflow
act -W .github/workflows/test.yml

# Run specific job
act -j test

# List all actions that would run
act -l
```

## Pre-commit Hooks

To catch issues before committing, set up pre-commit hooks:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hook scripts
pre-commit install

# Run against all files (testing)
pre-commit run --all-files
```

Now, every time you commit, the hooks will automatically run and prevent commits with issues.

## Quick Testing Workflow

1. **Before starting work**: Pull latest changes
   ```bash
   git pull origin main
   ```

2. **During development**: Run quick checks frequently
   ```bash
   python scripts/test_local.py --quick
   ```

3. **Before committing**: Run comprehensive checks
   ```bash
   python scripts/test_local.py --ci
   ```

4. **If all passes**: Commit with confidence
   ```bash
   git add .
   git commit -m "your commit message"
   ```

## Common Issues and Solutions

### Flake8 Errors

- **E712**: Use `is True` instead of `== True`
- **D205**: Add blank line between docstring summary and description
- **F401**: Remove unused imports
- **E501**: Line too long (max 88 chars with Black)

### MyPy Errors

- Add type hints to function signatures
- Use `Optional[]` for nullable types
- Import types from `typing` module

### Black Formatting

- Run `black adri/ tests/` to auto-format
- Configure your IDE to format on save

### Coverage Below Threshold

- Add more tests for uncovered lines
- Use `pytest --cov=adri --cov-report=html` to see detailed report
- Open `htmlcov/index.html` in browser for visual coverage

## CI/CD Pipeline Overview

Our GitHub Actions workflow includes:

1. **Quality Gate**: Code formatting and linting
2. **Test Suite**: Unit and integration tests with coverage
3. **Security Scan**: Vulnerability and dependency checks
4. **Performance**: Benchmark tests
5. **Release**: Automated PyPI releases on tags

## Tips for Success

1. **Run checks early and often**: Don't wait until you're ready to commit
2. **Use --quick mode during development**: Faster feedback loop
3. **Fix issues immediately**: Don't let them accumulate
4. **Keep dependencies updated**: Run `pip install --upgrade -e ".[dev]"` regularly
5. **Use pre-commit hooks**: Automatic checking on every commit

## Troubleshooting

### Script not found
```bash
# Run from project root
cd adri-validator
python scripts/test_local.py
```

### Missing dependencies
```bash
# Install all dev dependencies
pip install -e ".[dev]"
```

### Permission denied
```bash
# Make scripts executable
chmod +x scripts/test_local.py
chmod +x scripts/test-local.sh
```

### Tests failing locally but not in CI
```bash
# Ensure you're using the same Python version
python --version  # Should be 3.8+

# Clean up cache and artifacts
rm -rf .pytest_cache __pycache__ .coverage htmlcov
```

## Contributing

When adding new checks or modifying the testing process:

1. Update both `test_local.py` and `test-local.sh`
2. Ensure consistency with `.github/workflows/` configurations
3. Document any new requirements in this README
4. Test the scripts themselves before committing

## Support

If you encounter issues with these scripts:

1. Check this README for solutions
2. Ensure all dependencies are installed
3. Check GitHub Actions logs for comparison
4. Open an issue with detailed error messages

---

**Remember**: The goal is to catch issues locally before they reach CI/CD. A few minutes of local testing saves hours of debugging failed builds!
