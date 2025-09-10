# CI Troubleshooting Guide

Quick reference for resolving common CI pipeline issues in the ADRI repository.

## Quick Diagnostics

### Check CI Status
```bash
# View recent CI runs
gh run list --limit 10

# Check specific run details
gh run view <run-id>

# View logs for failed run
gh run view <run-id> --log
```

### Validate Local Environment
```bash
# Check pre-commit configuration
pre-commit run --all-files

# Validate Python environment
python -c "import adri; print('✓ ADRI imports successfully')"

# Test dependency resolution
pip check
```

## Common Issues & Solutions

### 🔴 Pre-commit Failures

#### InvalidConfigError: .pre-commit-config.yaml not found
```bash
# Verify config file exists in root
ls -la .pre-commit-config.yaml

# If missing, copy from development/config/
cp development/config/.pre-commit-config.yaml .
git add .pre-commit-config.yaml
git commit -m "fix: add missing pre-commit config to root"
```

#### Version Mismatch Errors
**Error**: `black==25.1.0` vs `black>=23.0` conflict
```bash
# Fix in pyproject.toml
sed -i 's/black>=23.0/black==25.1.0/' pyproject.toml
sed -i 's/isort>=5.12/isort==5.12.0/' pyproject.toml

git add pyproject.toml
git commit -m "fix: align tool versions with pre-commit config"
```

#### Hook Installation Issues
```bash
# Clean and reinstall hooks
pre-commit clean
pre-commit install
pre-commit run --all-files
```

### 🔴 Test Failures

#### Framework Import Errors
**Error**: `ModuleNotFoundError: No module named 'langchain'`
```bash
# Install optional dependencies
pip install -e ".[langchain]"

# Or install all framework dependencies
pip install -e ".[all]"

# Verify installation
python -c "import langchain; print('✓ LangChain available')"
```

#### Test Timeout Issues
**Error**: `FAILED due to timeout`
```bash
# Run specific test with increased timeout
pytest tests/examples/integration_tests/test_langchain_live.py --timeout=600 -v

# Check for infinite loops or hanging processes
pytest tests/examples/integration_tests/ --timeout=300 --tb=short
```

#### Dependency Validation Failures
```bash
# Check specific dependency conflicts
python tests/examples/dependency_tests/test_dependency_validation.py

# Test virtual environment isolation
python -m venv test_env
source test_env/bin/activate
pip install -e .
python -c "import adri; print('✓ Clean environment works')"
deactivate
rm -rf test_env
```

### 🔴 Security Scan Failures

#### Bandit Security Issues
**Error**: `Issue: [B105:hardcoded_password_string]`
```bash
# Run bandit locally to see specific issues
bandit -r adri/ -f json

# Common fixes:
# 1. Move secrets to environment variables
# 2. Use getpass for password input
# 3. Add # nosec comment for false positives
```

#### Safety Vulnerability Warnings
**Error**: `vulnerability found in package`
```bash
# Check vulnerabilities
safety check

# Update vulnerable packages
pip install --upgrade <package-name>

# If cannot update, document in .safety-project.ini
```

#### pip-audit Failures
```bash
# Run pip-audit locally
pip-audit

# Fix by updating dependencies
pip install --upgrade pip
pip install --upgrade -r requirements.txt
```

### 🔴 Build Failures

#### Package Installation Issues
**Error**: `ERROR: Failed building wheel`
```bash
# Clean build artifacts
rm -rf build/ dist/ *.egg-info/

# Reinstall with verbose output
pip install -e . -v

# Check for missing system dependencies
# On macOS: brew install <package>
# On Ubuntu: apt-get install <package>
```

#### Jekyll Documentation Build Failures
**Error**: `Jekyll build failed`
```bash
# Check Jekyll configuration
cd docs/
bundle install
bundle exec jekyll build --verbose

# Common issues:
# 1. Missing front matter in .md files
# 2. Invalid YAML syntax
# 3. Broken internal links
```

### 🔴 Performance Issues

#### Slow CI Execution
**Symptoms**: CI takes > 20 minutes for essential pipeline
```bash
# Check for:
# 1. Cache misses - verify cache keys
# 2. Network timeouts - check dependency downloads
# 3. Resource constraints - review concurrent jobs

# Optimize by:
# 1. Using cache-hit workflows
# 2. Reducing test matrix size for PR validation
# 3. Skipping tests on documentation-only changes
```

#### Memory Issues
**Error**: `Killed (OOM)`
```bash
# Reduce memory usage:
# 1. Limit concurrent test processes
pytest tests/ -n 2  # Instead of auto

# 2. Use pytest-xdist with memory limits
pytest tests/ --maxfail=5 --disable-warnings

# 3. Split large test files into smaller modules
```

## Workflow-Specific Issues

### CI Essential Pipeline

#### Quality Gate Failures
```bash
# Fix code formatting
black . --check --diff
isort . --check-only --diff

# Fix linting issues
flake8 . --statistics

# Run all quality checks
pre-commit run --all-files
```

#### Fast Test Failures
```bash
# Run smoke tests locally
pytest tests/examples/smoke_tests/ -v

# Check for import issues
python -c "import adri.decorators; print('✓')"
python -c "import adri.standards; print('✓')"
```

### CI Comprehensive Pipeline

#### Matrix Test Failures
**Error**: Tests pass on Python 3.10 but fail on 3.12
```bash
# Test specific Python version locally
pyenv install 3.12.0
pyenv local 3.12.0
python -m venv test312
source test312/bin/activate
pip install -e .
pytest tests/examples/integration_tests/ -v
```

#### Integration Test Timeouts
```bash
# Test framework-specific timeouts
export FRAMEWORK_TIMEOUT=300
pytest tests/examples/integration_tests/test_langchain_live.py -v

# Check for API rate limits or network issues
curl -I https://api.openai.com/v1/models
```

## Emergency Procedures

### 🚨 Critical CI Failure (Blocking All Development)

1. **Immediate Assessment**
   ```bash
   # Check if main branch is affected
   gh run list --branch main --limit 5
   
   # Check if specific to current PR
   gh run list --branch $(git branch --show-current) --limit 5
   ```

2. **Quick Fix Options**
   ```bash
   # Option A: Revert problematic commit
   git revert <commit-hash>
   git push origin <branch>
   
   # Option B: Skip CI temporarily (emergency only)
   git commit --allow-empty -m "ci: skip CI [skip ci]"
   ```

3. **Rollback Procedure**
   ```bash
   # Restore previous working workflows
   cp .github/workflows/archived/test.yml .github/workflows/
   cp .github/workflows/archived/pre-commit.yml .github/workflows/
   
   git add .github/workflows/
   git commit -m "emergency: restore previous CI workflows"
   git push origin main
   ```

### 🚨 Security Alert Blocking Merge

1. **Immediate Action**
   ```bash
   # Check security alerts
   gh security-advisory list
   
   # Review specific vulnerability
   safety check --json | jq '.vulnerabilities'
   ```

2. **Mitigation Steps**
   ```bash
   # Update vulnerable dependency
   pip install --upgrade <vulnerable-package>
   
   # If update not available, add exception
   echo "<vulnerable-package>==<version>" >> .safety-project.ini
   ```

## Monitoring & Prevention

### Daily Health Checks
```bash
# Check CI success rate
gh run list --status completed --limit 20 | grep -c "✓"

# Monitor build times
gh run list --limit 10 --json | jq '.[] | {workflow: .name, duration: .updated_at}'

# Check cache hit rates
# Review workflow logs for "Cache hit" messages
```

### Weekly Maintenance
```bash
# Update dependencies
pip list --outdated
pip install --upgrade pip setuptools wheel

# Review security advisories
gh security-advisory list

# Clean up old workflow runs
gh run list --status completed --limit 100 | tail -50 | cut -f3 | xargs -I {} gh run delete {}
```

## Getting Help

### Internal Resources
1. **Documentation**: Check `/docs/ci-pipeline-guide.md`
2. **Team Chat**: Post in `#dev-ops` channel
3. **Issue Tracker**: Create issue with `ci:bug` label

### External Resources
1. **GitHub Actions**: https://docs.github.com/en/actions/troubleshooting
2. **Pre-commit**: https://pre-commit.com/
3. **pytest**: https://docs.pytest.org/en/stable/

### Information to Include in Help Requests
```bash
# Gather diagnostic information
echo "=== CI Run Information ==="
gh run view <run-id> --json | jq '{id: .id, status: .status, conclusion: .conclusion, workflow: .name}'

echo "=== Local Environment ==="
python --version
pip --version
git --version

echo "=== Repository State ==="
git status
git log --oneline -5

echo "=== Dependency State ==="
pip list | head -20
pip check
```

---

**Quick Links:**
- [CI Pipeline Guide](./ci-pipeline-guide.md)
- [GitHub Actions Status](https://github.com/adri-standard/adri/actions)
- [Security Advisories](https://github.com/adri-standard/adri/security/advisories)

**Last Updated**: Phase 4 of CI Optimization (January 2025)
