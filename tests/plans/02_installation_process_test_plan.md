# Installation Process Test Plan

This test plan focuses on the second component of the ADRI user journey: "Installation Process". It validates that users can successfully install the ADRI package using various methods described in the documentation.

## Prerequisites

- Python 3.8+ installed
- Pip package manager
- Virtual environment tool (optional but recommended)
- Access to the cloned ADRI repository (from previous test plan)
- Internet connection to access PyPI

## Test Cases

### 1. Basic PyPI Installation

**Test ID:** 2.1

**Description:** Install ADRI via pip from PyPI.

**Steps:**
1. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv adri-test-env
   source adri-test-env/bin/activate  # On Windows: adri-test-env\Scripts\activate
   ```

2. Install ADRI from PyPI:
   ```bash
   pip install adri
   ```

3. Verify installation:
   ```bash
   pip list | grep adri
   ```

**Expected Result:**
- Package installs without errors
- `pip list` shows adri package with the expected version
- No dependency conflicts reported

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 2. Source Installation

**Test ID:** 2.2

**Description:** Install ADRI from the cloned source repository.

**Steps:**
1. Create and activate a fresh virtual environment:
   ```bash
   python -m venv adri-source-env
   source adri-source-env/bin/activate  # On Windows: adri-source-env\Scripts\activate
   ```

2. Navigate to the cloned repository directory:
   ```bash
   cd test-adri-clone  # Or wherever the repository was cloned to
   ```

3. Install from source:
   ```bash
   pip install -e .
   ```

4. Verify installation:
   ```bash
   pip list | grep adri
   ```

**Expected Result:**
- Package installs without errors
- `pip list` shows adri package in development mode
- No dependency conflicts reported

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 3. Database Extras Installation

**Test ID:** 2.3

**Description:** Install ADRI with database extras.

**Steps:**
1. Create and activate a fresh virtual environment:
   ```bash
   python -m venv adri-db-env
   source adri-db-env/bin/activate  # On Windows: adri-db-env\Scripts\activate
   ```

2. Install ADRI with database extras:
   ```bash
   pip install adri[database]
   ```

3. Verify installation:
   ```bash
   pip list | grep -E 'adri|psycopg2|sqlalchemy|mysqlclient'  # Adjust based on expected DB dependencies
   ```

**Expected Result:**
- Package and database dependencies install without errors
- `pip list` shows adri package and required database dependencies
- No dependency conflicts reported

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 4. API Extras Installation

**Test ID:** 2.4

**Description:** Install ADRI with API extras.

**Steps:**
1. Create and activate a fresh virtual environment:
   ```bash
   python -m venv adri-api-env
   source adri-api-env/bin/activate  # On Windows: adri-api-env\Scripts\activate
   ```

2. Install ADRI with API extras:
   ```bash
   pip install adri[api]
   ```

3. Verify installation:
   ```bash
   pip list | grep -E 'adri|requests|aiohttp'  # Adjust based on expected API dependencies
   ```

**Expected Result:**
- Package and API dependencies install without errors
- `pip list` shows adri package and required API dependencies
- No dependency conflicts reported

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 5. CLI Command Availability

**Test ID:** 2.5

**Description:** Verify that the ADRI CLI command is available after installation.

**Steps:**
1. Activate one of the virtual environments where ADRI was installed:
   ```bash
   source adri-test-env/bin/activate  # Or any other environment from previous tests
   ```

2. Check if the CLI command is available:
   ```bash
   adri --help
   ```

3. Verify the output shows available commands and options

**Expected Result:**
- `adri --help` command runs without errors
- Help text displays with available commands (e.g., `assess`)
- Help text matches documentation

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

### 6. Installation Documentation Accuracy

**Test ID:** 2.6

**Description:** Verify that the installation instructions in the documentation match the actual installation process.

**Steps:**
1. Compare the installation steps performed in tests 2.1-2.5 with the instructions in:
   - README.md
   - Implementation-Guide.md
   - Any other documentation mentioning installation

**Criteria to Check:**
- [ ] Installation commands match documentation
- [ ] Prerequisites accurately listed
- [ ] Virtual environment usage correctly explained
- [ ] Extra dependencies (database, API) properly documented
- [ ] Troubleshooting guidance provided for common issues

**Assessment:**
- [ ] Excellent (all criteria met)
- [ ] Good (most criteria met)
- [ ] Fair (some criteria met)
- [ ] Poor (few criteria met)

**Notes:**
_____________________________

### 7. Version Consistency

**Test ID:** 2.7

**Description:** Verify that the installed version matches the latest version on PyPI and in the repository.

**Steps:**
1. Check the installed version:
   ```bash
   pip show adri | grep Version
   ```

2. Check the latest version on PyPI:
   ```bash
   pip index versions adri
   ```

3. Check the version in the repository:
   ```bash
   grep -r "version" --include="*.py" test-adri-clone
   # Or check setup.py, pyproject.toml, or version.py
   ```

**Expected Result:**
- Installed version matches the latest version on PyPI
- Installed version matches the version in the repository
- Version format follows semantic versioning (X.Y.Z)

**Actual Result:**
- [ ] Pass
- [ ] Fail

**Notes:**
_____________________________

## Test Results Summary

**Overall Status:**
- [ ] All tests passed
- [ ] Some tests passed with minor issues
- [ ] Major issues detected

**Key Findings:**

**Recommendations:**

## Next Steps

After completing this test plan, proceed to the next logical component in the user journey: "Basic CLI Usage" test plan.
