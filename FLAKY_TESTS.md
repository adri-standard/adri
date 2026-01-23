# Flaky Tests Catalog

**Created:** 2026-01-22  
**Purpose:** Track and categorize all flaky tests in the test suite  
**Status:** Phase 1 - Initial diagnostic complete

---

## Summary

**Total Known Flaky Tests:** 5 marked with `@pytest.mark.ci_skip`  
**Windows 3.11 Specific:** 1 (under investigation)  
**macOS 3.13 Known Issue:** 1 (has `continue-on-error` workaround in CI)

---

## Tests Marked with @pytest.mark.ci_skip

### 1. test_plausibility_categorical_frequency
**File:** `tests/test_plausibility_rules.py`  
**Status:** Marked `ci_skip` - Flaky in CI  
**Symptoms:** Fails intermittently in CI, passes locally  
**Category:** TBD (pending Phase 2 analysis)  
**Platform:** All (fails in CI environment)  
**Priority:** Medium  
**Last Known Failure:** Multiple CI runs in package_context PR  

**Preliminary Notes:**
- Plausibility tests check business rule validation
- May involve statistical calculations or thresholds
- Possible timing or data ordering issue

---

### 2. test_basic_data_profiling (open_source)
**File:** `tests/open_source/test_data_profiler.py`  
**Class:** Unknown (needs inspection)  
**Status:** Marked `ci_skip` - Flaky in CI  
**Symptoms:** Fails intermittently in CI  
**Category:** TBD (likely test design or external dependency)  
**Platform:** All  
**Priority:** Medium  

**Preliminary Notes:**
- Data profiling involves statistical analysis
- May have timing sensitivity
- Could be related to numerical precision or thresholds

---

### 3. test_data_quality_assessment (open_source)
**File:** `tests/open_source/test_data_profiler.py`  
**Class:** Unknown (needs inspection)  
**Status:** Marked `ci_skip` - Flaky in CI  
**Symptoms:** Fails intermittently in CI  
**Category:** TBD  
**Platform:** All  
**Priority:** Medium  

**Preliminary Notes:**
- Quality assessment may involve scoring thresholds
- Potentially timing-dependent calculations
- May overlap with test #2

---

### 4. test_basic_data_profiling (comprehensive)
**File:** `tests/unit/analysis/test_data_profiler_comprehensive.py`  
**Class:** Unknown (needs inspection)  
**Status:** Marked `ci_skip` - Flaky in CI  
**Symptoms:** Fails intermittently in CI  
**Category:** TBD  
**Platform:** All  
**Priority:** Medium  

**Preliminary Notes:**
- Duplicate or variant of test #2
- May be more comprehensive version
- Likely shares same root cause as #2

---

### 5. test_data_quality_assessment (comprehensive)
**File:** `tests/unit/analysis/test_data_profiler_comprehensive.py`  
**Class:** Unknown (needs inspection)  
**Status:** Marked `ci_skip` - Flaky in CI  
**Symptoms:** Fails intermittently in CI  
**Category:** TBD  
**Platform:** All  
**Priority:** Medium  

**Preliminary Notes:**
- Duplicate or variant of test #3
- May be more comprehensive version
- Likely shares same root cause as #3

---

## Platform-Specific Issues

### Windows Python 3.11 Failure
**Status:** ACTIVE - Currently blocking PR #28  
**First Observed:** 2026-01-22 (multiple CI runs)  
**Test:** Unknown (investigation needed)  
**Symptoms:** 
- Fails consistently on Windows + Python 3.11
- Other platforms pass
- Other Python versions on Windows may pass

**CI History:**
```json
{"branch":"fix/package-context-resolution-v7.2.7","date":"2026-01-22T14:24:48Z","title":"fix: package_context resolution for v7.2.7"}
{"branch":"fix/package-context-resolution-v7.2.7","date":"2026-01-22T14:12:36Z","title":"fix: package_context resolution for v7.2.7"}
```

**Hypothesis:**
- Environmental issue (Windows filesystem, path handling)
- Python 3.11 specific behavior
- May be related to package_context path resolution changes
- Could be timing issue (fsync on Windows)

**Priority:** HIGH - Currently blocking PR merge

**Next Steps:**
1. Get exact test name from Windows 3.11 CI logs
2. Reproduce locally on Windows if possible
3. Analyze if related to package_context fix
4. Determine if legitimate failure or environmental flake

---

### macOS Python 3.13 Known Issue
**Status:** KNOWN - Has workaround in CI  
**Workaround:** `continue-on-error: ${{ matrix.os == 'macos-latest' && matrix.python-version == '3.13' }}`  
**File:** `.github/workflows/ci.yml` line 120  
**Test:** Unknown  
**Symptoms:** Fails on macOS + Python 3.13 (beta)  
**Category:** Environmental (beta Python version)  
**Priority:** LOW (Python 3.13 is not released)  

**Notes:**
- Python 3.13 is still in beta
- May resolve when Python 3.13 is officially released
- Current workaround acceptable for now
- Should be moved to Tier 3 (Monitoring) when CI is restructured

---

## Analysis Patterns

### Common Themes (Preliminary)
1. **Data Profiling Tests:** 4 out of 5 marked tests involve data profiling
2. **CI vs Local:** All pass locally, fail in CI (environmental issue)
3. **Timing Sensitivity:** Many involve calculations/analysis (potential race conditions)
4. **Platform Independence:** Most issues affect all platforms in CI

### Potential Root Causes
- [ ] Timing/race conditions in statistical calculations
- [ ] Non-deterministic data generation
- [ ] Threshold calculations with floating-point precision issues  
- [ ] Global state pollution between tests
- [ ] Improper test isolation (fixtures not resetting)
- [ ] External dependencies (filesystem, network)
- [ ] CI environment differences (CPU, memory, timing)

---

## Phase 2 Analysis Tasks

### For Each Test:
1. Read test code to understand what it does
2. Identify root cause category:
   - Environmental (OS/platform specific)
   - Test Design (order-dependent, cleanup issues)
   - External Dependencies (unmocked calls, timing)
3. Determine fix strategy
4. Assign priority (High/Medium/Low)

### Windows 3.11 Specific:
1. Extract exact failure from CI logs
2. Reproduce locally if possible
3. Determine relationship to package_context fix
4. Fix or categorize appropriately

---

## Fix Strategy Guidelines

### High Priority (Blocking)
- Windows 3.11 issue
- Any test causing CI failures on main branch
- Tests that block valid PRs

### Medium Priority (ci_skip marked)
- Current ci_skip tests
- Fix to restore CI coverage
- Can be batched together

### Low Priority (Monitoring)
- Python 3.13 beta issues
- Performance benchmarks
- Experimental features

---

## Progress Tracking

### Phase 1: Diagnostic ✅
- [x] Install pytest-repeat
- [x] Identify tests marked ci_skip
- [x] Analyze CI failure history
- [x] Create this catalog

### Phase 2: Root Cause Analysis (Next)
- [ ] Inspect each test's code
- [ ] Categorize by root cause
- [ ] Identify Windows 3.11 specific failure
- [ ] Create fix strategy for each

### Phase 3: Fix Tests
- [ ] Fix High Priority (Windows 3.11)
- [ ] Fix Medium Priority (ci_skip tests)
- [ ] Verify all fixes with multiple local runs

### Phase 4: CI Restructure
- [ ] Implement 3-tier architecture
- [ ] Add test markers (flaky, platform_specific)
- [ ] Update CI configuration

### Phase 5: Validation
- [ ] Test locally on all platforms
- [ ] Test in CI with feature branch
- [ ] Verify blocking works correctly

### Phase 6: Documentation
- [ ] Create CI_TEST_STRATEGY.md
- [ ] Update CONTRIBUTING.md
- [ ] Archive this document

---

## Notes

- All recent CI failures (last 20 runs) are from `fix/package-context-resolution-v7.2.7` branch
- This suggests the issue is recent, possibly related to package_context changes
- Baseline regression tests were fixed (separate issue, now resolved)
- Need to determine if Windows 3.11 failure is:
  - Related to package_context fix (new issue introduced)
  - Pre-existing flaky test exposed by increased testing
  - Environmental transient issue

---

**Last Updated:** 2026-01-22 14:47  
**Next Review:** After Phase 2 complete  
**Owner:** CI Health Task Force
