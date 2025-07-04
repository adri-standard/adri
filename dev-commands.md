# ADRI Validator Development Commands

## Quality Checks
```bash
# Format code
black adri/ tests/

# Sort imports
isort adri/ tests/

# Lint code
flake8 adri/ tests/

# Type checking
mypy adri/

# Security scan
bandit -r adri/
safety check

# All quality checks
black adri/ tests/ && isort adri/ tests/ && flake8 adri/ tests/ && mypy adri/
```

## Testing
```bash
# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=adri --cov-report=html

# Run integration tests
pytest tests/integration/ -v

# Run performance benchmarks
pytest tests/test_benchmarks.py --benchmark-only

# Run all tests
pytest tests/ -v
```

## Pre-commit
```bash
# Run pre-commit on all files
pre-commit run --all-files

# Update pre-commit hooks
pre-commit autoupdate

# Skip pre-commit for a commit
git commit -m "message" --no-verify
```

## Package Building
```bash
# Build package
python -m build

# Check package
twine check dist/*

# Install locally
pip install -e .
```

## Development Workflow
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes
3. Run quality checks: `black . && isort . && flake8 . && mypy adri/`
4. Run tests: `pytest tests/ -v`
5. Commit changes: `git commit -m "feat: your feature"`
6. Push and create PR: `git push origin feature/your-feature`
