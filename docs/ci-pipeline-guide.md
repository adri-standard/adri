# CI Pipeline Guide

## Overview

The ADRI repository uses a streamlined CI architecture designed for **fast feedback** and **comprehensive validation** while maintaining **high quality standards**.

## CI Architecture

### Core CI Pipeline (ci-core.yml) - **BLOCKING**
**Trigger**: Pull Requests and Push to main
**Duration**: < 45 minutes
**Purpose**: Comprehensive validation required for merge approval

**Jobs:**
- **Quality Gate** (15 min): Pre-commit hooks, code formatting, fast unit tests
- **Core Test Matrix** (45 min): Python 3.10, 3.11, 3.12 with full test coverage
- **Core Performance** (30 min): Performance benchmarks and stress testing
- **Core Security** (15 min): Security scanning with bandit, safety, pip-audit
- **Core Build** (15 min): Package building and distribution validation
- **Core Success** (3 min): Final validation gate - ALL must pass to merge

### Non-Core CI Pipeline (ci-non-core.yml) - **NON-BLOCKING**
**Trigger**: Pull Requests, Push to main, Daily schedule
**Duration**: < 30 minutes
**Purpose**: Quality feedback without blocking development

**Jobs:**
- **Examples Integration** (30 min): Framework integration testing (mock mode)
- **Examples Dependencies** (20 min): Dependency error handling validation
- **Demo Validation** (25 min): Demo quality and credibility checks
- **Examples Smoke Tests** (15 min): Basic import and functionality validation
- **Error Handling** (20 min): Error handling pattern validation
- **Development Tools** (15 min): Development scripts and utilities validation

### Validation Workflows - **BLOCKING**
**Required for PR merge:**
- **Branch Naming Validation**: Enforces issue-first development workflow
- **Conventional Commits**: Validates commit message format
- **PR Issue Link Validation**: Ensures PRs reference GitHub issues

## Workflow Optimization Features

### Intelligent Caching
- **Dependencies**: Automatic caching of pip dependencies with cache key versioning
- **Build Artifacts**: Caching of build outputs and test results
- **Pre-commit**: Caching of pre-commit environments

### Parallel Execution
- **Matrix Strategy**: Parallel testing across Python versions
- **Job Parallelization**: Independent jobs run concurrently
- **Conditional Execution**: Smart path-based triggering

### Timeout Management
- **Quality Gate**: 15 minutes maximum
- **Individual Tests**: 10 minutes per test suite
- **Overall Pipeline**: 45 minutes hard limit

## Developer Workflow

### Pull Request Process
1. **Create PR** → Triggers `ci-essential.yml`
2. **Quick Feedback** → Results in < 15 minutes
3. **Address Issues** → Fix any failing quality gates
4. **PR Approval** → Merge triggers `ci-comprehensive.yml`
5. **Full Validation** → Complete testing suite

### Local Development
```bash
# Run pre-commit hooks locally
pre-commit run --all-files

# Run quick tests
pytest tests/examples/smoke_tests/ -v

# Run specific framework tests
pytest tests/examples/integration_tests/test_langchain_live.py -v
```

### Debugging CI Failures

#### Quality Gate Failures
```bash
# Fix formatting issues
black . --check
isort . --check-only

# Run flake8 locally
flake8 .

# Test pre-commit hooks
pre-commit run --all-files
```

#### Dependency Issues
```bash
# Check dependency conflicts
pip check

# Validate requirements
pip-audit

# Test virtual environment
python -m venv test_env
source test_env/bin/activate  # or test_env\Scripts\activate on Windows
pip install -e .
```

#### Framework Integration Issues
```bash
# Test specific framework
python examples/langchain-customer-service.py

# Run dependency validation
python tests/examples/dependency_tests/test_dependency_validation.py
```

## Security Scanning

### Automated Security Checks
- **Bandit**: Python code security analysis
- **Safety**: Known vulnerability scanning
- **pip-audit**: Package vulnerability assessment
- **Dependency Review**: GitHub native dependency scanning

### Security Thresholds
- **Critical vulnerabilities**: Block PR merge
- **High vulnerabilities**: Require review and mitigation plan
- **Medium/Low vulnerabilities**: Warning with tracking

## Performance Monitoring

### Benchmarking
- **Execution Time**: Framework initialization and execution timing
- **Memory Usage**: Peak memory consumption tracking
- **Dependency Load Time**: Import and dependency resolution timing

### Performance Thresholds
- **Fast Tests**: < 30 seconds per test file
- **Integration Tests**: < 5 minutes per framework
- **Overall Suite**: < 45 minutes total

## Configuration Files

### Pre-commit Configuration (`.pre-commit-config.yaml`)
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer

  - repo: https://github.com/psf/black
    rev: 25.1.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pycqa/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
```

### Project Configuration (`pyproject.toml`)
Key CI-related configurations:
```toml
[tool.black]
line-length = 88
target-version = ['py310']

[tool.isort]
profile = "black"
line_length = 88

[tool.pytest.ini_options]
timeout = 300
addopts = "--cov=adri --cov-report=html --cov-report=term-missing --cov-fail-under=90"
```

## Troubleshooting Common Issues

### Issue: Pre-commit Hook Failures
**Symptoms**: CI fails with `InvalidConfigError`
**Solution**:
```bash
# Verify .pre-commit-config.yaml exists in repository root
ls -la .pre-commit-config.yaml

# Reinstall pre-commit hooks
pre-commit clean
pre-commit install
pre-commit run --all-files
```

### Issue: Version Inconsistencies
**Symptoms**: Different tool versions between pyproject.toml and pre-commit
**Solution**: Ensure version alignment:
- `black==25.1.0` in both files
- `isort==5.12.0` in both files
- `flake8` consistent across configurations

### Issue: Test Timeouts
**Symptoms**: Tests fail with timeout errors
**Solution**:
```bash
# Run tests with verbose output
pytest -v --tb=short

# Increase timeout for specific tests
pytest --timeout=600 tests/examples/integration_tests/
```

### Issue: Dependency Conflicts
**Symptoms**: Import errors or dependency resolution failures
**Solution**:
```bash
# Check for conflicts
pip check

# Create clean environment
python -m venv clean_env
source clean_env/bin/activate
pip install -e .
```

## Monitoring and Metrics

### CI Health Metrics
- **Success Rate**: Target > 95% for essential pipeline
- **Duration**: Essential < 15min, Comprehensive < 45min
- **Queue Time**: Target < 2 minutes wait time
- **Failure Rate by Category**: Track quality vs infrastructure failures

### Performance Tracking
- **Build Times**: Monitor trends and optimization opportunities
- **Resource Usage**: CPU and memory consumption patterns
- **Cache Hit Rates**: Optimize caching strategies

## Emergency Procedures

### Critical CI Failure
1. **Assess Impact**: Is it blocking all development?
2. **Quick Fix**: Apply immediate hotfix if possible
3. **Rollback Option**: Restore previous working workflows from archived/
4. **Communication**: Notify team of CI status and expected resolution

### Rollback Procedure
```bash
# Restore archived workflows if needed
cp .github/workflows/archived/test.yml .github/workflows/
cp .github/workflows/archived/pre-commit.yml .github/workflows/

# Commit and push emergency restore
git add .github/workflows/
git commit -m "emergency: restore previous CI workflows"
git push origin main
```

## Best Practices

### For Developers
- **Run pre-commit locally** before pushing
- **Keep PRs focused** to minimize CI complexity
- **Monitor CI results** and address failures quickly
- **Use draft PRs** for experimental work

### For Maintainers
- **Review CI logs** regularly for optimization opportunities
- **Monitor security reports** and address vulnerabilities promptly
- **Update dependencies** systematically
- **Optimize workflow performance** based on metrics

## Support and Escalation

### Getting Help
1. **Check this guide** for common solutions
2. **Review CI logs** for specific error messages
3. **Consult team members** for complex issues
4. **Create issue** for persistent problems

### Escalation Path
1. **Developer** → Fix obvious issues locally
2. **Team Lead** → Review complex CI problems
3. **DevOps/Admin** → Infrastructure and workflow changes
4. **Security Team** → Security-related CI failures

---

**Last Updated**: Phase 4 of CI Optimization (January 2025)
**Version**: v1.0 - Streamlined CI Architecture
