# CI Test Suite Health Fix - Implementation Plan

**Date:** 2026-01-22  
**Goal:** Eliminate flaky tests and establish rock-solid CI pipeline  
**Approach:** Option A - Deep Dive Comprehensive Fix  
**Estimated Time:** 3-4 hours

---

## Executive Summary

### Current State
- ✅ Package context fix working correctly
- ✅ Baseline regression tests fixed
- ❌ Windows Python 3.11 failing (environmental)
- ⚠️ Existing workarounds: `@pytest.mark.ci_skip`, `continue-on-error` for macOS 3.13
- 🔴 **Problem**: CI uses band-aids instead of fixing root causes

### Target State
- ✅ All tests deterministic and reliable
- ✅ 3-tier CI architecture (Core/Platform/Monitoring)
- ✅ Clear blocking vs informational separation
- ✅ Platform-specific issues properly handled
- ✅ Trust in CI results restored

---

## Phase 1: Diagnostic (30-60 min)

### Objective
Identify ALL flaky tests through systematic testing

### Actions

#### 1.1 Local Flaky Test Detection
```bash
# Install pytest-repeat if not present
pip install pytest-repeat

# Run tests multiple times to expose flakes
pytest tests/ --count=10 -x --tb=short > flaky_test_report.txt 2>&1
```

#### 1.2 Analyze Historical CI Failures
```bash
# Check last 20 CI runs
gh run list --limit 20 --json conclusion,displayTitle,createdAt > ci_history.json

# Find patterns in failures
gh api repos/Verodat/verodat-adri/actions/runs \
  --jq '.workflow_runs[] | select(.conclusion=="failure") | .name' | sort | uniq -c
```

#### 1.3 Catalog Known Issues
- Tests marked with `@pytest.mark.ci_skip`
- Tests with `continue-on-error` workarounds
- Windows-specific failures
- macOS-specific failures

### Deliverables
- [ ] `flaky_test_report.txt` - Full diagnostic output
- [ ] `ci_history.json` - Historical failure data
- [ ] `FLAKY_TESTS.md` - Categorized list of problematic tests

---

## Phase 2: Root Cause Analysis (30-45 min)

### Objective
Categorize each flaky test by root cause

### Categories

#### A. Environmental Issues
**Symptoms:**
- Fails on specific OS (Windows/macOS only)
- Path-related errors
- Line ending issues
- Filesystem timing

**Examples:**
- Windows path separators (`\` vs `/`)
- Case-sensitive filesystem (macOS vs Linux)
- CRLF line endings

#### B. Test Design Flaws
**Symptoms:**
- Passes/fails randomly
- Order-dependent (different results when run alone vs suite)
- Cleanup issues

**Examples:**
- Race conditions
- Global state pollution
- Improper fixture cleanup
- Test order dependencies

#### C. External Dependencies
**Symptoms:**
- Network timeouts
- Filesystem delays
- Non-deterministic data

**Examples:**
- Unmocked network calls
- fsync timing on Windows
- Random data without fixed seed
- Time-based logic

### Analysis Template
For each flaky test:
```markdown
## Test: `test_xyz`

**Status:** Flaky  
**Category:** [Environmental | Design | External]  
**Platform:** [All | Windows | macOS | Linux]  
**Failure Rate:** X/10 runs  
**Root Cause:** [Specific issue]  
**Fix Strategy:** [Specific approach]  
**Priority:** [High | Medium | Low]
```

### Deliverables
- [ ] `FLAKY_TEST_ANALYSIS.md` - Complete root cause analysis
- [ ] Tests grouped by fix strategy
- [ ] Priority order for fixes

---

## Phase 3: Fix Flaky Tests (1-2 hours)

### Objective
Make all tests deterministic and reliable

### Fix Strategies

#### 3.1 Environmental Fixes

**Path Handling:**
```python
# ❌ Before: Brittle
def test_load_file():
    path = "tests/fixtures/data.csv"
    data = load(path)

# ✅ After: Robust
from pathlib import Path

def test_load_file():
    path = Path(__file__).parent / "fixtures" / "data.csv"
    data = load(path)
```

**Platform-Specific Tests:**
```python
import sys
import pytest

# Skip on incompatible platforms
@pytest.mark.skipif(sys.platform == "win32", reason="Unix-only feature")
def test_unix_permissions():
    ...

# Or run with platform-specific expectations
@pytest.mark.parametrize("expected", [
    pytest.param("/path/to/file", marks=pytest.mark.unix),
    pytest.param(r"C:\path\to\file", marks=pytest.mark.windows),
])
def test_paths(expected):
    ...
```

#### 3.2 Test Design Fixes

**Proper Isolation:**
```python
# ❌ Before: Order-dependent
global_cache = {}

def test_a():
    global_cache["key"] = "value"
    
def test_b():
    assert "key" not in global_cache  # Fails if test_a runs first!

# ✅ After: Isolated
@pytest.fixture(autouse=True)
def reset_cache():
    global_cache.clear()
    yield
    global_cache.clear()

def test_a(reset_cache):
    global_cache["key"] = "value"
    
def test_b(reset_cache):
    assert "key" not in global_cache  # Always passes
```

**Proper Cleanup:**
```python
# ❌ Before: Leaks state
def test_temp_file():
    f = open("temp.txt", "w")
    f.write("data")
    # Missing close/cleanup!

# ✅ After: Guaranteed cleanup
import tempfile

def test_temp_file():
    with tempfile.NamedTemporaryFile(mode="w", delete=True) as f:
        f.write("data")
        f.flush()
        # Automatically cleaned up
```

#### 3.3 External Dependency Fixes

**Mock Network Calls:**
```python
# ❌ Before: Real network call
import requests

def test_api():
    response = requests.get("https://api.example.com/data")
    assert response.status_code == 200

# ✅ After: Mocked
from unittest.mock import Mock, patch

def test_api(monkeypatch):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    
    monkeypatch.setattr(requests, 'get', lambda url: mock_response)
    response = requests.get("https://api.example.com/data")
    assert response.status_code == 200
```

**Deterministic Random Data:**
```python
# ❌ Before: Non-deterministic
import random

def test_random_data():
    value = random.randint(1, 100)
    assert value > 0  # Always passes but uses different values

# ✅ After: Fixed seed
import random

def test_random_data():
    random.seed(42)  # Fixed seed for reproducibility
    value = random.randint(1, 100)
    assert value == 52  # Exact expected value
```

### Implementation Order
1. **High Priority**: Tests blocking PR merges (Windows 3.11)
2. **Medium Priority**: Tests marked `ci_skip`
3. **Low Priority**: Monitoring tests (can remain in Tier 3)

### Deliverables
- [ ] All High Priority tests fixed
- [ ] All Medium Priority tests fixed
- [ ] Low Priority tests moved to monitoring tier
- [ ] Tests pass 20/20 times locally

---

## Phase 4: CI Restructure (45-60 min)

### Objective
Implement 3-tier CI architecture

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│ TIER 1: Core Blocking Tests (Must Pass)                │
│ - Ubuntu + Python 3.10, 3.11, 3.12                     │
│ - Stable, deterministic tests only                     │
│ - Fast (<5 min)                                         │
│ - Blocks PR merges                                      │
│ - fail-fast: true                                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ TIER 2: Platform Coverage (Must Pass with Retry)       │
│ - Windows + macOS × Python 3.10, 3.11, 3.12            │
│ - All tests except known flaky                          │
│ - Retry up to 2 times on failure                        │
│ - Reports but uses fail-fast: false                     │
│ - Blocks after 3 consecutive failures                   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ TIER 3: Monitoring (Never Blocks)                      │
│ - Python 3.13 (beta)                                    │
│ - Known flaky tests (retry 5x)                          │
│ - Performance benchmarks                                │
│ - continue-on-error: true                               │
│ - Informational only                                    │
└─────────────────────────────────────────────────────────┘
```

### New CI Configuration

**File:** `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  # ... existing check-changes job ...

  # ============================================================================
  # TIER 1: CORE BLOCKING TESTS (Must Pass)
  # ============================================================================
  test-core:
    name: Core Tests (Ubuntu ${{ matrix.python-version }})
    needs: check-changes
    if: needs.check-changes.outputs.docs-only == 'false'
    runs-on: ubuntu-latest
    strategy:
      fail-fast: true  # Stop immediately on first failure
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      
      - name: Run core tests
        run: |
          pytest tests/ -v \
            --cov=adri --cov-report=xml --cov-report=term \
            -m "not performance and not ci_skip and not flaky and not platform_specific" \
            --maxfail=1  # Stop on first failure

  # ============================================================================
  # TIER 2: PLATFORM COVERAGE (Must Pass with Retry)
  # ============================================================================
  test-platforms:
    name: Platform Tests (${{ matrix.os }}, Python ${{ matrix.python-version }})
    needs: [check-changes, test-core]  # Only run after core passes
    if: needs.check-changes.outputs.docs-only == 'false'
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false  # Let all platforms complete
      matrix:
        os: [windows-latest, macos-latest]
        python-version: ['3.10', '3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
          pip install pytest-rerunfailures  # For retry capability
      
      - name: Run platform tests (with retry)
        shell: bash
        run: |
          # Set Windows-specific environment
          if [ "${{ runner.os }}" = "Windows" ]; then
            export ADRI_SKIP_FSYNC=1
          fi
          
          # Run with automatic retry on failure
          pytest tests/ -v \
            --cov=adri --cov-report=xml \
            -m "not performance and not ci_skip and not flaky" \
            --reruns 2 --reruns-delay 1  # Retry flaky failures

  # ============================================================================
  # TIER 3: MONITORING (Never Blocks)
  # ============================================================================
  test-monitoring:
    name: Monitoring Tests
    needs: check-changes
    if: needs.check-changes.outputs.docs-only == 'false'
    runs-on: ubuntu-latest
    continue-on-error: true  # Never block CI
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python 3.13
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
          allow-prereleases: true
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
          pip install pytest-rerunfailures
      
      - name: Run flaky tests (monitoring only)
        run: |
          pytest tests/ -v \
            -m "flaky" \
            --reruns 5 --reruns-delay 1 || true
      
      - name: Run performance benchmarks (informational)
        run: |
          pytest tests/ -v \
            -m "performance" \
            --benchmark-only || true

  # ============================================================================
  # EXISTING JOBS (build-test, security, etc.)
  # ============================================================================
  # ... keep existing build-test, security, validation jobs ...

  # ============================================================================
  # CI STATUS (Updated Logic)
  # ============================================================================
  ci-status:
    needs: [
      check-changes,
      validate-docs,
      test-core,
      test-platforms,
      build-test,
      security,
      validate-gitignore-protection,
      validate-root-structure
    ]
    if: always()
    runs-on: ubuntu-latest
    
    steps:
      - name: Check CI status
        run: |
          echo "=== CI Status Check ==="
          echo "Docs validation: ${{ needs.validate-docs.result }}"
          echo "Core tests: ${{ needs.test-core.result }}"
          echo "Platform tests: ${{ needs.test-platforms.result }}"
          echo "Build test: ${{ needs.build-test.result }}"
          echo "Security: ${{ needs.security.result }}"
          
          # For docs-only changes
          if [ "${{ needs.validate-docs.result }}" == "success" ]; then
            echo "✅ Documentation validation passed"
            exit 0
          fi
          
          # For code changes - require all essential tests
          REQUIRED_PASS=true
          
          # Core tests MUST pass
          if [ "${{ needs.test-core.result }}" != "success" ]; then
            echo "❌ Core tests failed or skipped"
            REQUIRED_PASS=false
          fi
          
          # Platform tests MUST pass
          if [ "${{ needs.test-platforms.result }}" != "success" ]; then
            echo "❌ Platform tests failed or skipped"
            REQUIRED_PASS=false
          fi
          
          # Build MUST succeed
          if [ "${{ needs.build-test.result }}" != "success" ]; then
            echo "❌ Build test failed"
            REQUIRED_PASS=false
          fi
          
          # Security MUST pass
          if [ "${{ needs.security.result }}" != "success" ]; then
            echo "❌ Security check failed"
            REQUIRED_PASS=false
          fi
          
          if [ "$REQUIRED_PASS" = "true" ]; then
            echo "✅ All required CI checks passed"
            exit 0
          else
            echo "❌ Required CI checks failed"
            exit 1
          fi
```

### Test Markers

**File:** `pyproject.toml` (add to existing markers)

```toml
[tool.pytest.ini_options]
markers = [
    "performance: Performance benchmarks (deselect with '-m \"not performance\"')",
    "ci_skip: Skip in CI but run in pre-commit",
    "flaky: Known flaky tests (monitoring only)",
    "platform_specific: Platform-specific tests (Windows/macOS only)",
    "slow: Slow tests (>5 seconds)",
]
```

### Implementation Steps
1. Update `pyproject.toml` with new markers
2. Mark tests appropriately:
   - High-risk flaky → `@pytest.mark.flaky`
   - Platform-specific → `@pytest.mark.platform_specific`
3. Update `.github/workflows/ci.yml`
4. Test on feature branch before merging

### Deliverables
- [ ] Updated CI configuration
- [ ] Tests properly marked
- [ ] CI passes on test branch

---

## Phase 5: Validation (30 min)

### Objective
Verify new CI architecture works as designed

### Validation Tests

#### 5.1 Local Testing
```bash
# Tier 1 tests (should be <5 min)
time pytest tests/ -m "not performance and not ci_skip and not flaky and not platform_specific"

# All tests except monitoring
time pytest tests/ -m "not performance and not ci_skip and not flaky"

# Flaky tests (for monitoring)
pytest tests/ -m "flaky" --reruns 5
```

#### 5.2 CI Testing
1. Create test branch
2. Push changes
3. Verify:
   - ✅ Core tests pass quickly
   - ✅ Platform tests complete (even if some retry)
   - ✅ Monitoring tests don't block
   - ✅ Failures block correctly

#### 5.3 Failure Simulation
```bash
# Introduce intentional failure
# Verify it blocks in Tier 1 but not in Tier 3
```

### Success Criteria
- [ ] All Tier 1 tests pass in <5 min
- [ ] Platform tests complete within 10 min
- [ ] Monitoring tests don't block merges
- [ ] Real failures still block PRs
- [ ] CI results are trustworthy

---

## Phase 6: Documentation (15 min)

### Objective
Ensure team can maintain CI health long-term

### Documentation

#### 6.1 CI Strategy Guide

**File:** `docs/CI_TEST_STRATEGY.md`

```markdown
# CI Test Strategy

## Overview
Our CI uses a 3-tier architecture to balance speed, reliability, and coverage.

## Test Tiers

### Tier 1: Core Blocking Tests ⛔
**Purpose:** Fast, deterministic validation of core functionality  
**Platforms:** Ubuntu only  
**Python:** 3.10, 3.11, 3.12  
**Time Limit:** <5 minutes  
**Failure Action:** Blocks PR immediately  

**Characteristics:**
- Must be 100% deterministic
- No platform-specific code
- No external dependencies
- Fast execution

**Adding Tests:**
Default placement for new tests. Only exclude if:
- Platform-specific behavior
- Known to be flaky (needs investigation)
- Performance benchmark

### Tier 2: Platform Coverage ⚠️
**Purpose:** Cross-platform validation with resilience  
**Platforms:** Windows, macOS  
**Python:** 3.10, 3.11, 3.12  
**Time Limit:** <10 minutes  
**Failure Action:** Retries 2x, then blocks  

**Characteristics:**
- May have platform-specific behavior
- Includes retry logic for transient issues
- More permissive than Tier 1

**Adding Tests:**
Use `@pytest.mark.platform_specific` for OS-specific tests.

### Tier 3: Monitoring ℹ️
**Purpose:** Track flaky tests and experimental features  
**Platforms:** Ubuntu + Python 3.13  
**Time Limit:** No limit  
**Failure Action:** Never blocks (informational)  

**Characteristics:**
- Known flaky tests under investigation
- Beta Python versions
- Performance benchmarks
- Experimental features

**Adding Tests:**
Use `@pytest.mark.flaky` for tests with known issues.

## Test Markers

### Available Markers
```python
@pytest.mark.performance    # Tier 3 - benchmarks
@pytest.mark.ci_skip       # Only in pre-commit
@pytest.mark.flaky         # Tier 3 - monitoring
@pytest.mark.platform_specific  # Tier 2 only
@pytest.mark.slow          # Long-running tests
```

### Usage Examples
```python
# Platform-specific test
@pytest.mark.platform_specific
@pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
def test_windows_path_handling():
    ...

# Known flaky test (monitoring only)
@pytest.mark.flaky
def test_timing_sensitive_operation():
    ...
```

## When Tests Fail

### Tier 1 Failure
**Action:** Fix immediately  
**Process:**
1. Reproduce locally
2. Fix root cause
3. Verify 20/20 passes locally
4. Push fix

### Tier 2 Failure
**Action:** Investigate, may be transient  
**Process:**
1. Check if retry succeeded
2. If persistent, reproduce locally
3. Fix or promote to Tier 3 if truly flaky

### Tier 3 Failure
**Action:** Create ticket, doesn't block  
**Process:**
1. Create issue to investigate
2. Tag with "test-health"
3. Prioritize based on failure frequency

## Maintaining CI Health

### Monthly Review
- Check Tier 3 tests
- Promote stable tests back to Tier 2/1
- Remove permanently broken tests

### Adding New Features
- Start in Tier 1 if possible
- Mark appropriately if platform-specific
- Never use `continue-on-error` in Tier 1/2

### Red Flags
- ❌ Adding `continue-on-error` to Tier 1/2
- ❌ Using `@pytest.mark.ci_skip` without ticket
- ❌ Ignoring Tier 3 failures indefinitely
```

#### 6.2 Update CONTRIBUTING.md

Add section about test expectations:
```markdown
## Writing Tests

### Test Quality Standards
- **Deterministic:** Same input = same output, every time
- **Isolated:** No dependencies on other tests or state
- **Fast:** Tier 1 tests should complete in <1 second
- **Clear:** Descriptive names and failure messages

### Platform Considerations
Use `pathlib.Path` instead of string concatenation:
```python
# ✅ Good
path = Path(__file__).parent / "fixtures" / "data.csv"

# ❌ Avoid
path = "tests/fixtures/data.csv"
```

### Test Markers
See [CI_TEST_STRATEGY.md](docs/CI_TEST_STRATEGY.md) for details.
```

### Deliverables
- [ ] `docs/CI_TEST_STRATEGY.md` created
- [ ] `CONTRIBUTING.md` updated
- [ ] `CI_TEST_SUITE_HEALTH_FIX.md` (this file) archived
- [ ] Team briefed on new process

---

## Rollout Plan

### Phase 0: Preparation (Before Starting)
- [x] Document current state
- [x] Get user buy-in
- [x] Create this implementation plan

### Phase 1-6: Execution (This Session)
- [ ] Run diagnostics
- [ ] Analyze root causes
- [ ] Fix flaky tests
- [ ] Restructure CI
- [ ] Validate
- [ ] Document

### Phase 7: Deployment
- [ ] Merge to main
- [ ] Monitor first 10 CI runs
- [ ] Adjust thresholds if needed

### Phase 8: Maintenance
- [ ] Monthly CI health review
- [ ] Track Tier 3 tests
- [ ] Continuous improvement

---

## Success Metrics

### Before (Current State)
- ❌ Windows 3.11 blocking PRs
- ❌ Tests marked `ci_skip`
- ❌ `continue-on-error` workarounds
- ❌ Distrust in CI results
- ⏱️ Unknown true failure rate

### After (Target State)
- ✅ All PRs unblocked by flaky tests
- ✅ No `ci_skip` markers
- ✅ `continue-on-error` only in Tier 3
- ✅ 100% trust in CI results
- ✅ <5 min core test feedback
- ✅ Clear blocking vs informational separation

### Key Performance Indicators
- **Core Test Time:** <5 minutes (currently: unknown)
- **False Positive Rate:** 0% (tests fail only on real issues)
- **Platform Coverage:** Windows + macOS validated
- **Developer Confidence:** High (measured by "CI said pass, code is good")

---

## Risk Mitigation

### Risk: Breaking existing workflows
**Mitigation:** Test on feature branch first, gradual rollout

### Risk: Tests still flaky after fixes
**Mitigation:** Tier 3 monitoring catches without blocking

### Risk: CI takes too long
**Mitigation:** Tier 1 is fast, Tier 2/3 parallel, fail-fast on Tier 1

### Risk: Team doesn't adopt new markers
**Mitigation:** Clear documentation, examples, code review enforcement

---

## Post-Fix Monitoring

### Week 1
- Check every CI run
- Note any unexpected failures
- Adjust retry counts if needed

### Week 2-4
- Monitor Tier 3 tests
- Promote stable tests back to Tier 2
- Remove permanently broken tests

### Monthly
- Review CI metrics
- Update this document
- Share wins with team

---

## Appendix: Quick Reference

### Running Tests Locally

```bash
# Core tests only (fast)
pytest tests/ -m "not performance and not ci_skip and not flaky and not platform_specific"

# With coverage
pytest tests/ -m "not performance and not ci_skip and not flaky and not platform_specific" --cov=adri

# All non-flaky tests
pytest tests/ -m "not performance and not ci_skip and not flaky"

# Check for flakiness (run 10 times)
pytest tests/ --count=10 -x

# Check specific test for flakiness
pytest tests/test_xyz.py::test_function --count=20 -v
```

### Common Fixes

```bash
# Fix path handling
find tests/ -name "*.py" -exec sed -i '' 's|"tests/fixtures|Path(__file__).parent / "fixtures|g' {} \;

# Add marker to test
# In test file: @pytest.mark.flaky

# Check which tests would run in each tier
pytest tests/ --collect-only -m "not performance and not ci_skip and not flaky and not platform_specific"
```

---

## Notes / Lessons Learned

*(To be filled in during execution)*

### Phase 1 Notes


### Phase 2 Notes


### Phase 3 Notes


### Phase 4 Notes


### Phase 5 Notes


### Phase 6 Notes


---

**Status:** IN PROGRESS  
**Last Updated:** 2026-01-22  
**Next Review:** After completion
