# Test Coverage for Version Policy

This document details how the ADRI version policy (documented in VERSIONS.md) is tested and enforced.

## Version Policy Components

### Semantic Versioning Rules

| Policy | Implementation | Testing | Enforcement |
|--------|----------------|---------|-------------|
| MAJOR for scoring changes | VERSIONS.md policy | Human review | PR review process |
| MINOR for new features | VERSIONS.md policy | Human review | PR review process |
| PATCH for bug fixes | VERSIONS.md policy | Human review | PR review process |
| Score compatibility tracking | adri/version.py | tests/unit/test_version.py | ✅ Automated |

### Version Compatibility

| Feature | Implementation | Test Coverage |
|---------|----------------|---------------|
| Compatible version list | `__score_compatible_versions__` in version.py | tests/unit/test_version.py |
| Compatibility checking | `is_version_compatible()` | tests/unit/test_version.py |
| Compatibility messages | `get_score_compatibility_message()` | tests/unit/test_version.py |
| Report version checking | adri/report.py | tests/unit/test_report.py |

### Version Documentation

| Document | Purpose | Testing |
|----------|---------|---------|
| VERSIONS.md | Version history and compatibility matrix | tests/infrastructure/test_version_infrastructure.py |
| CHANGELOG.md | Detailed change log | .github/workflows/publish.yml |
| Version in reports | Track which version created report | tests/integration/test_version_integration.py |

## Test Implementation

### Unit Tests

**File**: `tests/unit/test_version.py`

Tests:
```python
- test_version_constants()  # Verify version format
- test_version_compatibility_checking()  # Test compatibility logic
- test_report_version_embedding()  # Ensure version in reports
- test_report_version_loading()  # Check compatibility on load
```

### Infrastructure Tests

**File**: `tests/infrastructure/test_version_infrastructure.py`

Tests:
```python
- test_versions_md_contains_current_version()  # Current version documented
- test_version_consistency_with_pyproject()  # Version files match
- test_release_documentation_structure()  # Docs follow standard
```

### Integration Tests

**File**: `tests/integration/test_version_integration.py`

Tests:
```python
- test_cli_embeds_version_in_report()  # CLI adds version to reports
- test_version_consistency_script()  # Verify script works
```

## Policy Enforcement

### Automated Checks

| Check | Where | What it validates |
|-------|-------|-------------------|
| Version format | tests/unit/test_version.py | Follows semver format |
| Compatibility list | tests/unit/test_version.py | Valid version strings |
| Version in reports | Multiple tests | Always embedded |
| Version consistency | CI/CD pipeline | All files match |

### Manual Review Points

| Policy | Review Stage | Reviewer Responsibility |
|--------|--------------|------------------------|
| MAJOR version decision | PR review | Check for scoring changes |
| MINOR version decision | PR review | Verify backward compatibility |
| Compatibility matrix update | PR review | Ensure VERSIONS.md updated |
| CHANGELOG completeness | Release PR | All changes documented |

## Version Compatibility Matrix Testing

### Matrix Validation

The compatibility matrix in VERSIONS.md is validated by:
1. Ensuring all listed versions exist in version history
2. Checking score compatibility claims against code
3. Verifying matrix is updated with new releases

### Score Compatibility Testing

```python
# Example test case
def test_score_compatibility_between_versions():
    # Test that 0.1.0 and 0.2.0b1 are marked compatible
    assert "0.1.0" in __score_compatible_versions__
    assert "0.2.0b1" in __score_compatible_versions__
    
    # Test compatibility function
    assert is_version_compatible("0.1.0")
    assert is_version_compatible("0.2.0b1")
```

## CI/CD Integration

### Pull Request Checks

Every PR runs:
- Version consistency tests
- Compatibility function tests
- Documentation structure tests

### Release Workflow

The publish.yml workflow:
1. Verifies version matches tag
2. Checks CHANGELOG has version
3. Validates version format
4. Ensures compatibility data updated

## Coverage Gaps and Recommendations

### Well Covered ✅
- Version compatibility logic
- Version embedding in reports
- Version consistency checks
- Compatibility message generation

### Needs Improvement ⚠️
- Automated scoring methodology change detection
- Version migration testing framework
- Compatibility matrix validation

### Recommendations
1. Add automated tests to detect scoring methodology changes
2. Create version migration test harness
3. Add compatibility matrix schema validation
4. Build automated version policy compliance checker

## Manual Testing Procedures

### Before Major Version Change
```bash
# 1. Review all scoring logic changes
git diff main...feature/branch -- adri/dimensions/

# 2. Verify compatibility list updated
grep "__score_compatible_versions__" adri/version.py

# 3. Check VERSIONS.md updated
grep "Score Compatible" VERSIONS.md
```

### Version Policy Compliance Check
```bash
# Run version policy compliance script (to be created)
python scripts/check_version_policy.py
```

---

Last updated: 2025-01-05
