# Test Coverage for Release Process

This document details how the ADRI release process (documented in RELEASING.md) is tested and validated.

## Release Process Steps and Testing

### 1. Version Determination

| Process Step | Testing Method | Coverage |
|--------------|----------------|----------|
| Semantic versioning decision | Human review based on documented policy | ⚠️ Manual |
| Breaking change identification | PR review process | ⚠️ Manual |
| Feature vs bug fix classification | PR labels and review | ⚠️ Manual |

### 2. Version Updates

| File | Automated Testing | Manual Testing |
|------|-------------------|----------------|
| adri/version.py | tests/infrastructure/test_version_infrastructure.py | scripts/verify_version.py |
| pyproject.toml | tests/infrastructure/test_version_infrastructure.py | scripts/verify_version.py |
| Version consistency | .github/workflows/publish.yml | ✅ Automated |

### 3. Documentation Updates

| Document | Required Updates | Testing |
|----------|------------------|---------|
| CHANGELOG.md | Move unreleased → version section | .github/workflows/publish.yml |
| VERSIONS.md | Add compatibility info | tests/infrastructure/test_version_infrastructure.py |
| Release notes | Extract from CHANGELOG | ⚠️ Manual |

### 4. Pull Request Process

| Requirement | Enforcement | Testing |
|-------------|-------------|---------|
| Branch naming (release/vX.Y.Z) | GitHub branch protection | ✅ Automated |
| CI tests pass | GitHub Actions required | ✅ Automated |
| Two maintainer approvals | GitHub PR settings | ✅ Automated |

### 5. Tagging and Release

| Step | Automation | Validation |
|------|------------|------------|
| Git tag creation | Manual with instructions | Tag format validation in publish.yml |
| Tag push | Manual command | Triggers automated workflow |
| GitHub release creation | Manual via UI | Triggers publish.yml |

### 6. Publishing Pipeline

| Stage | Implementation | Testing |
|-------|----------------|---------|
| Version verification | publish.yml | ✅ Every release |
| CHANGELOG verification | publish.yml | ✅ Every release |
| Package build | publish.yml | ✅ Every release |
| Package validation | twine check in publish.yml | ✅ Every release |
| Import test | publish.yml | ✅ Every release |
| PyPI upload | pypa/gh-action-pypi-publish | ✅ Every release |

### 7. Post-Release Verification

| Check | Method | Coverage |
|-------|--------|----------|
| PyPI availability | Manual check | ❌ Not automated |
| Package installation | Manual test | ❌ Not automated |
| Version verification | Manual import | ❌ Not automated |

## Test Files

### Infrastructure Tests
**File**: `tests/infrastructure/test_version_infrastructure.py`

Tests:
- GitHub workflow configuration validity
- Publish script configuration
- Version file existence
- Release documentation structure

### Integration Tests
**File**: `tests/integration/test_publishing.py`

Tests:
- TestPyPI publishing workflow
- Version generation for testing
- Package building
- Upload verification

### CI/CD Workflows

**File**: `.github/workflows/publish.yml`
- Triggered on release creation
- Performs all automated checks
- Publishes to PyPI

**File**: `.github/workflows/test-publishing.yml`
- Tests publishing process
- Uses TestPyPI
- Validates workflow

## Manual Testing Procedures

### Pre-Release Checklist
```bash
# 1. Verify version consistency
python scripts/verify_version.py

# 2. Test build locally
python -m build

# 3. Check package
twine check dist/*

# 4. Test installation from wheel
pip install dist/*.whl
python -c "import adri; print(adri.__version__)"
```

### Test Publishing
```bash
# Publish to TestPyPI first
./scripts/publish_pypi.sh --test

# Verify on TestPyPI
pip install -i https://test.pypi.org/simple/ adri=={VERSION}
```

## Coverage Analysis

### Well Tested ✅
- Version consistency checks
- Package build process
- Publishing workflow
- CHANGELOG validation
- Import verification

### Partially Tested ⚠️
- Version determination (manual process)
- Release notes generation
- Documentation updates

### Not Automated ❌
- Post-release verification
- PyPI availability check
- Release announcements

## Recommendations

1. Add post-release automated verification workflow
2. Create release notes template generator
3. Add PyPI availability monitoring
4. Automate version determination helper script

---

Last updated: 2025-01-05
