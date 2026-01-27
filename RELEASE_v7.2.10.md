# Release Instructions for ADRI v7.2.10

## Critical Bug Fix: Threshold Paradox Resolution

This release fixes a critical threshold resolution timing bug in the decorator that caused inconsistent behavior between assessment and execution decisions.

---

## 🔍 Pre-Release Checklist

- [x] Bug fix implemented in `src/adri/guard/modes.py`
- [x] CHANGELOG.md updated with v7.2.10 entry
- [ ] All tests passing
- [ ] Code quality checks passed
- [ ] Git working directory clean

---

## 📦 Release Process

### Step 1: Verify Tests Pass

```bash
# Run full test suite
pytest

# Verify no flake8 issues
flake8 src/

# Verify black formatting
black --check src/

# Optional: Run specific decorator tests
pytest tests/unit/test_decorator.py -v
pytest tests/integration/test_decorator_threshold_resolution.py -v
```

### Step 2: Clean Build Artifacts

```bash
# Remove old build artifacts
rm -rf dist/ build/ *.egg-info src/*.egg-info

# Clean Python cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
```

### Step 3: Create Git Tag

```bash
# Commit changes
git add CHANGELOG.md src/adri/guard/modes.py RELEASE_v7.2.10.md
git commit -m "Release v7.2.10: Fix threshold paradox bug

- Fixed threshold resolution timing in @adri_protected decorator
- Threshold now resolved AFTER contract creation
- Ensures contract-specified thresholds always respected
- Fixes inconsistency between assessment (75.0) and execution (80.0)
"

# Create annotated tag for v7.2.10
git tag -a v7.2.10 -m "Release v7.2.10 - Threshold Paradox Fix

Critical bug fix for threshold resolution timing issue.

Changes:
- Fixed threshold paradox in decorator
- Ensures contract thresholds take precedence
- Assessment and execution now use same threshold

See CHANGELOG.md for details.
"

# Push commit and tag
git push origin main
git push origin v7.2.10
```

### Step 4: Build Both Packages

#### A. Build Enterprise Package (verodat-adri)

```bash
# Ensure pyproject.enterprise.toml is active
cp pyproject.enterprise.toml pyproject.toml

# Build enterprise distribution
python -m build

# Verify enterprise package
ls -lh dist/
# Should see: verodat_adri-7.2.10-py3-none-any.whl
#             verodat-adri-7.2.10.tar.gz
```

#### B. Extract and Build Open Source Package (adri)

```bash
# Extract open source version
python scripts/extract_opensource.py

# Switch to open source directory
cd dist-opensource/

# Build open source distribution
python -m build

# Verify open source package
ls -lh dist/
# Should see: adri-7.2.10-py3-none-any.whl
#             adri-7.2.10.tar.gz

# Return to main directory
cd ..
```

### Step 5: Test Packages Locally (Recommended)

```bash
# Create test virtual environment
python -m venv test-env
source test-env/bin/activate  # or `test-env\Scripts\activate` on Windows

# Test enterprise package
pip install dist/verodat_adri-7.2.10-py3-none-any.whl
python -c "from adri import __version__; print(f'Enterprise: {__version__}')"
pip uninstall verodat-adri -y

# Test open source package
pip install dist-opensource/dist/adri-7.2.10-py3-none-any.whl
python -c "from adri import __version__; print(f'Open Source: {__version__}')"
pip uninstall adri -y

# Clean up test environment
deactivate
rm -rf test-env/
```

### Step 6: Publish to PyPI

#### A. Publish Enterprise Package (verodat-adri)

```bash
# Ensure you're in enterprise repo root
pwd  # Should show: .../verodat-adri-enterprise

# Publish to PyPI (requires PYPI_TOKEN_VERODAT_ADRI)
python -m twine upload dist/verodat_adri-7.2.10* \
    --username __token__ \
    --password $PYPI_TOKEN_VERODAT_ADRI

# Or use .pypirc configuration
python -m twine upload dist/verodat_adri-7.2.10*
```

#### B. Publish Open Source Package (adri)

```bash
# Switch to open source directory
cd dist-opensource/

# Publish to PyPI (requires PYPI_TOKEN_ADRI)
python -m twine upload dist/adri-7.2.10* \
    --username __token__ \
    --password $PYPI_TOKEN_ADRI

# Or use .pypirc configuration
python -m twine upload dist/adri-7.2.10*

# Return to main directory
cd ..
```

### Step 7: Verify PyPI Publications

```bash
# Check PyPI pages
open https://pypi.org/project/verodat-adri/
open https://pypi.org/project/adri/

# Test installation from PyPI
pip install --upgrade verodat-adri
pip install --upgrade adri
```

### Step 8: Create GitHub Release

1. Go to: https://github.com/Verodat/verodat-adri/releases/new
2. Tag: `v7.2.10`
3. Title: `v7.2.10 - Threshold Paradox Fix`
4. Description:
```markdown
## Critical Bug Fix: Threshold Paradox Resolution

This patch release fixes a critical threshold resolution bug that caused inconsistent behavior between assessment and execution decisions in the decorator.

### What's Fixed

**Threshold Paradox Bug**: Fixed threshold resolution timing issue in `@adri_protected` decorator
- **Bug**: Threshold was resolved BEFORE contract auto-generation, causing decorator to use config default (80.0) instead of contract-specified threshold (75.0)
- **Impact**: Assessments passed with 75.0 threshold, but execution decisions incorrectly used 80.0
- **Fix**: Moved threshold resolution to AFTER contract creation to ensure contract-specified thresholds are always respected
- **Result**: Assessment threshold and execution threshold now always consistent

### Installation

**Enterprise (requires Verodat API key):**
```bash
pip install --upgrade verodat-adri
```

**Open Source:**
```bash
pip install --upgrade adri
```

### Full Changelog

See [CHANGELOG.md](https://github.com/Verodat/verodat-adri/blob/main/CHANGELOG.md) for complete details.
```

---

## 🔒 Security Notes

- Use PyPI API tokens (not username/password)
- Store tokens in environment variables or .pypirc
- Never commit tokens to git
- Test packages locally before publishing

---

## 📋 Post-Release Checklist

- [ ] Both packages published to PyPI
- [ ] GitHub release created
- [ ] Installation verified from PyPI
- [ ] Documentation updated (if needed)
- [ ] Team notified of release
- [ ] Monitor for any issues

---

## 🆘 Troubleshooting

### Build fails with "No module named 'setuptools_scm'"
```bash
pip install setuptools-scm
```

### Twine upload fails with authentication error
```bash
# Verify token is set
echo $PYPI_TOKEN_VERODAT_ADRI
echo $PYPI_TOKEN_ADRI

# Or configure .pypirc
cat > ~/.pypirc << EOF
[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE
EOF
```

### Version number not updating
```bash
# setuptools_scm requires clean git state and tags
git status  # Should be clean
git describe --tags  # Should show v7.2.10
```

---

## 📞 Support

- Issues: https://github.com/Verodat/verodat-adri/issues
- Email: adri@verodat.com
