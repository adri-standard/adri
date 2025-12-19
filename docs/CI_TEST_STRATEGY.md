# CI Test Strategy for Physical Code Separation

## Overview

The physical code separation architecture implements a comprehensive multi-stage testing strategy to ensure code quality at both the enterprise and open source levels before any sync occurs.

## Test Execution Flow

### Stage 1: Enterprise Testing (Pre-Extraction)

**Purpose:** Verify enterprise code is stable before extraction

**Test Suite:**
```bash
pytest tests/test_decorator.py tests/enterprise/ -v
```

**Coverage:**
- Open source decorator tests (20 tests)
- Enterprise decorator wrapper tests (9 tests)
- Enterprise Verodat integration tests (11 tests)
- **Total: 40 tests**

**Exit Criteria:**
- All tests must pass
- If any test fails → Abort sync immediately

**Why This Matters:**
- Ensures changes to `src/adri/` don't break enterprise features
- Validates enterprise wrapper still delegates correctly
- Confirms no regressions in enterprise-only features

### Stage 2: Code Extraction

**Purpose:** Extract open source code from enterprise repository

**Process:**
```bash
python scripts/extract_opensource.py --output /tmp/adri-opensource
```

**Operations:**
- Copy `src/adri/` directory wholesale (136 files)
- Copy open source tests (24 test files)
- Copy shared test utilities
- Generate extraction report

**Validation Checks:**
- No enterprise imports in extracted code
- All Python files have valid syntax
- Directory structure is correct
- Required files are present

### Stage 3: Extraction Validation

**Purpose:** Validate extracted code has zero enterprise dependencies

**Checks:**
1. **Import Scanning:**
   - Scans all Python files in `src/adri/`
   - Searches for: `adri_enterprise`, `from adri.logging.enterprise`
   - Exit if any enterprise imports found

2. **Syntax Validation:**
   - Parses all Python files with AST
   - Ensures valid syntax
   - Catches any syntax errors introduced

3. **Report Generation:**
   - Creates `SYNC_REPORT.md`
   - Lists all extracted files
   - Shows validation status

**Exit Criteria:**
- Report status must be "PASSED"
- Zero enterprise imports detected
- All files have valid syntax

### Stage 4: Open Source Testing (Post-Extraction)

**Purpose:** Verify extracted code works as standalone open source package

**Test Suite:**
```bash
cd /tmp/adri-opensource
pip install -e .
pytest tests/test_decorator.py -v
```

**Coverage:**
- Open source decorator tests (20 tests)
- Tests run in isolated environment
- No enterprise dependencies available
- Pure open source package validation

**Exit Criteria:**
- All tests must pass in isolation
- Package must install without enterprise deps
- If any test fails → Abort sync

**Why This Matters:**
- Confirms open source code is truly standalone
- Validates no hidden enterprise dependencies
- Ensures community can use code as-is

### Stage 5: Sync to Upstream

**Purpose:** Create PR with validated code

**Process:**
- Copy extracted code to upstream repo clone
- Create feature branch
- Commit changes
- Create automated PR

**PR Includes:**
- All validated code changes
- SYNC_REPORT.md as artifact
- Test results summary
- Links to CI run

---

## Test Matrix

| Stage | Location | Tests | Purpose | Exit on Fail |
|-------|----------|-------|---------|--------------|
| 1 | Enterprise Repo | 40 tests | Validate stability | Yes |
| 2 | Extraction | N/A | Extract code | No |
| 3 | Extracted Code | Validation | Check purity | Yes |
| 4 | Isolated Environment | 20 tests | Verify standalone | Yes |
| 5 | Upstream PR | Manual | Community review | No |

---

## Failure Scenarios

### Scenario 1: Enterprise Tests Fail
**When:** Before extraction
**Action:** Abort immediately, do not extract
**Resolution:** Fix enterprise code, re-run workflow

### Scenario 2: Enterprise Import Detected
**When:** After extraction, during validation
**Action:** Abort, do not create PR
**Resolution:** Remove enterprise dependency, re-run

### Scenario 3: Open Source Tests Fail
**When:** Testing extracted code in isolation
**Action:** Abort, do not create PR
**Resolution:** Fix open source code, ensure standalone works

### Scenario 4: Syntax Errors
**When:** During extraction validation
**Action:** Abort immediately
**Resolution:** Fix syntax errors, re-run extraction

---

## Quality Gates

### Gate 1: Enterprise Stability
```
✓ All enterprise tests pass
✓ Both tiers work correctly
✓ No regressions introduced
```

### Gate 2: Clean Extraction
```
✓ 136 source files extracted
✓ 24 test files extracted
✓ All required files present
```

### Gate 3: Zero Enterprise Leakage
```
✓ No adri_enterprise imports
✓ No enterprise.py imports
✓ Clean dependency tree
```

### Gate 4: Standalone Functionality
```
✓ Package installs independently
✓ All open source tests pass
✓ No missing dependencies
```

---

## Continuous Integration Benefits

### Automated Quality Assurance
- Every commit triggers full test suite
- No manual intervention needed
- Consistent test execution

### Fast Feedback
- Developers know within minutes if changes break sync
- Issues caught before merge to main
- Reduced debugging time

### Documentation
- Every sync includes detailed report
- Test results preserved as artifacts
- Audit trail for all syncs

### Safety
- Multiple validation layers
- Cannot sync broken code
- Enterprise and open source both validated

---

## Manual Testing (Optional)

Developers can test locally before pushing:

```bash
# Test enterprise code
pytest tests/test_decorator.py tests/enterprise/ -v

# Test extraction
python scripts/extract_opensource.py --output /tmp/test-sync

# Test extracted code
cd /tmp/test-sync
pip install -e .
pytest tests/test_decorator.py -v
```

---

## Test Report Example

```
======================================================================
ADRI Open Source Extraction
======================================================================
Enterprise repo: /Users/thomas/github/verodat/adri-enterprise
Output directory: /tmp/adri-opensource

Step 1: Extracting open source code...
  ✓ Copied 136 files

Step 2: Extracting tests...
  ✓ Copied 24 test files

Step 3: Copying supporting files...
  ✓ Copied README, LICENSE, etc.

Step 4: Validating extraction...
  ✓ No enterprise imports detected
  ✓ All Python files have valid syntax

Step 5: Generating sync report...
  ✓ Report saved to /tmp/adri-opensource/SYNC_REPORT.md

======================================================================
Extraction Summary
======================================================================
Files copied:     136
Test files:       24
Directories:      33
Total size:       1969.9 KB
Validation:       PASSED ✓
======================================================================
```

---

## Success Metrics

- **Enterprise Tests:** 40/40 passing
- **Extraction:** 100% success rate
- **Validation:** 0 enterprise imports
- **Open Source Tests:** 20/20 passing
- **Overall:** 100% automated quality assurance

---

This comprehensive testing strategy ensures that code quality is maintained at every stage of the sync process, protecting both enterprise and open source repositories from regressions or contamination.
