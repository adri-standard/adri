# ADRI Testing Approach

This document outlines the comprehensive testing approach for the Agent Data Readiness Index (ADRI) project, covering both functional components and infrastructure elements.

## Table of Contents
- [Overall Test Strategy](#overall-test-strategy)
- [Functional Testing](#functional-testing)
- [Non-Functional Testing](#non-functional-testing)
- [CI/CD Pipeline Testing](#cicd-pipeline-testing)
- [Content & Documentation Testing](#content-documentation-testing)
- [Test Data Management](#test-data-management)
- [Regression Testing Process](#regression-testing-process)
- [Test Reporting](#test-reporting)

## Overall Test Strategy

### Testing Philosophy and Objectives

ADRI follows these key testing principles:

1. **Quality-First Approach**: Testing is a critical component of our development process, not an afterthought.
2. **Continuous Testing**: Tests are run throughout the development lifecycle, not just before releases.
3. **Automation Focus**: We automate tests wherever possible to ensure consistency and repeatability.
4. **Comprehensive Coverage**: We aim to test all aspects of the system, including functionality, performance, and usability.
5. **Real-World Testing**: Tests should simulate real-world usage patterns and edge cases.

### Testing Pyramid

```mermaid
graph TB
    subgraph pyramid [" "]
        E2E[End-to-End Tests<br/>Complete Workflows<br/>Real User Scenarios]
        INT[Integration Tests<br/>Component Interactions<br/>API Contracts]
        UNIT[Unit Tests<br/>Individual Functions<br/>Isolated Logic]
        
        UNIT --> INT
        INT --> E2E
        
        U_COUNT[Many Tests<br/>Fast Execution<br/>100% Required]
        I_COUNT[Moderate Tests<br/>Medium Speed<br/>100% Required]
        E_COUNT[Few Tests<br/>Slower Execution<br/>Critical Paths]
    end
    
    UNIT -.-> U_COUNT
    INT -.-> I_COUNT
    E2E -.-> E_COUNT
    
    Base[Foundation: 80% Code Coverage Minimum]
    
    style UNIT fill:#10b981,stroke:#059669,stroke-width:3px,color:#fff
    style INT fill:#3b82f6,stroke:#2563eb,stroke-width:3px,color:#fff
    style E2E fill:#8b5cf6,stroke:#7c3aed,stroke-width:3px,color:#fff
    style U_COUNT fill:#d1fae5,stroke:#10b981,stroke-width:2px
    style I_COUNT fill:#dbeafe,stroke:#3b82f6,stroke-width:2px
    style E_COUNT fill:#ede9fe,stroke:#8b5cf6,stroke-width:2px
    style Base fill:#1e293b,stroke:#0f172a,stroke-width:3px,color:#fff,font-weight:bold
    
    classDef pyramidStyle fill:none,stroke:none
    class pyramid pyramidStyle
```

### Testing Environments

- **Local Development**: Developers run tests locally during development
- **CI/CD Pipeline**: Automated tests run on pull requests and merges
- **Staging**: Pre-production environment for integration testing
- **Production**: Monitoring and smoke tests in production

### Pass/Fail Criteria

- **Unit Tests**: All unit tests must pass (100% pass rate)
- **Integration Tests**: All integration tests must pass (100% pass rate)
- **Code Coverage**: Minimum 80% code coverage for new code
- **Performance Benchmarks**: Response times within defined thresholds
- **Documentation Build**: Documentation must build without errors and pass link validation

## Functional Testing

### Unit Testing

Unit tests focus on testing individual components in isolation:

- **Framework**: pytest
- **Structure**: Test files in `tests/unit/` directory mirroring the project structure
- **Naming Convention**: `test_[component].py` for test files, `test_[function]` for test functions
- **Coverage**: Run with `pytest --cov=adri tests/unit/`
- **Mock External Dependencies**: Use pytest's monkeypatch or unittest.mock

#### Version Management Unit Tests

ADRI includes specific unit tests for the version management system:

- **File**: `tests/unit/test_version.py`
- **Scope**: Verifies version constants, compatibility checking, and version embedding in reports
- **Coverage**:
  - Tests version constants and formats
  - Tests version compatibility logic
  - Tests that reports properly embed version information
  - Tests version warning generation when loading reports from incompatible versions

#### Running Unit Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run specific unit tests
pytest tests/unit/test_assessor.py

# Run with coverage
pytest --cov=adri tests/unit/
```

### Integration Testing

Integration tests verify interactions between components:

- **Framework**: pytest
- **Structure**: Test files in `tests/integration/` directory
- **Scope**: Test interactions between multiple components
- **Environment**: Uses test configuration files in `tests/config/`

#### Version Management Integration Tests

ADRI includes integration tests for the version management system:

- **File**: `tests/integration/test_version_integration.py`
- **Scope**: Verifies that version information is properly propagated through the CLI and assessment process
- **Coverage**:
  - Tests that CLI operations correctly embed version information in reports
  - Tests that the version consistency script functions correctly
  - Tests end-to-end version propagation from code to reports

#### Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run specific integration tests
pytest tests/integration/test_cli.py
```

### End-to-End Testing

End-to-end tests verify the entire application flow:

- **Framework**: pytest with custom fixtures
- **Structure**: Test files in `tests/e2e/` directory
- **Focus**: Test complete user workflows
- **Data**: Uses sample datasets in `tests/data/`

## Non-Functional Testing

### Performance Testing

- **Tool**: pytest-benchmark
- **Metrics**: Response time, throughput, resource usage
- **Thresholds**: Define acceptable performance thresholds
- **Environment**: Testing in an environment similar to production

### Security Testing

- **Static Analysis**: Use bandit for static security analysis
- **Dependency Scanning**: Use safety to check for vulnerable dependencies
- **Authentication Testing**: Verify auth mechanisms work correctly

### Accessibility Testing

- **Documentation**: Test documentation for accessibility issues
- **CLI**: Ensure CLI is usable with screen readers
- **Web Components**: Test web components against WCAG guidelines

## CI/CD Pipeline Testing

### GitHub Actions Workflows

ADRI uses several GitHub Actions workflows for testing:

1. **tests.yml**: Runs unit and integration tests
2. **type-check.yml**: Runs type checking with mypy
3. **docs.yml**: Builds and deploys documentation
4. **update-catalog.yml**: Updates community dataset catalog
5. **test-publishing.yml**: Tests the PyPI publishing process using TestPyPI

### CI/CD Pipeline Flow

```mermaid
flowchart LR
    subgraph "Developer"
        DEV[Local Development<br/>Write Code & Tests]
        COMMIT[Git Commit<br/>Push to Branch]
    end
    
    subgraph "GitHub Actions"
        subgraph "PR Checks"
            LINT[Code Style<br/>Black, isort, flake8]
            TYPE[Type Checking<br/>mypy]
            UNIT_PR[Unit Tests<br/>pytest unit/]
            INT_PR[Integration Tests<br/>pytest integration/]
            COV[Coverage Check<br/>≥80% required]
            DOC_BUILD[Docs Build<br/>mkdocs build]
        end
        
        subgraph "Main Branch"
            UNIT_MAIN[Full Test Suite]
            PUBLISH[TestPyPI<br/>Publishing Test]
            DEPLOY_DOCS[Deploy Docs<br/>GitHub Pages]
        end
        
        subgraph "Release"
            TAG[Version Tag]
            PYPI[PyPI Release]
            ANNOUNCE[Release Notes]
        end
    end
    
    DEV --> COMMIT
    COMMIT --> LINT
    LINT -->|Pass| TYPE
    TYPE -->|Pass| UNIT_PR
    UNIT_PR -->|Pass| INT_PR
    INT_PR -->|Pass| COV
    COV -->|Pass| DOC_BUILD
    
    DOC_BUILD -->|Merge| UNIT_MAIN
    UNIT_MAIN --> PUBLISH
    PUBLISH --> DEPLOY_DOCS
    
    DEPLOY_DOCS -->|Tag| TAG
    TAG --> PYPI
    PYPI --> ANNOUNCE
    
    style DEV fill:#fbbf24,stroke:#f59e0b
    style COMMIT fill:#fbbf24,stroke:#f59e0b
    style LINT fill:#60a5fa,stroke:#3b82f6
    style TYPE fill:#60a5fa,stroke:#3b82f6
    style UNIT_PR fill:#10b981,stroke:#059669
    style INT_PR fill:#10b981,stroke:#059669
    style COV fill:#10b981,stroke:#059669
    style DOC_BUILD fill:#60a5fa,stroke:#3b82f6
    style UNIT_MAIN fill:#10b981,stroke:#059669
    style PUBLISH fill:#a78bfa,stroke:#7c3aed
    style DEPLOY_DOCS fill:#a78bfa,stroke:#7c3aed
    style TAG fill:#f472b6,stroke:#ec4899
    style PYPI fill:#f472b6,stroke:#ec4899
    style ANNOUNCE fill:#f472b6,stroke:#ec4899
```

#### TestPyPI Publishing Integration Test

We have a dedicated workflow for testing the PyPI publishing process:

- **File**: `.github/workflows/test-publishing.yml`
- **Purpose**: Verifies that package building and publishing to PyPI works correctly
- **Scope**: 
  - Generates a unique development version
  - Builds the package with this version
  - Publishes to TestPyPI (not the production PyPI)
  - Verifies the published package is accessible
- **Security**: Uses GitHub Secrets for storing the TestPyPI token
- **When It Runs**: 
  - On pushes to the develop branch
  - On pull requests to the develop branch
  - Manually via workflow_dispatch

We provide a robust standalone script for testing the publishing process:

- **File**: `test_publish_to_testpypi.py`
- **Features**:
  - Automatic dependency installation
  - Detailed progress reporting
  - Error handling and recovery
  - Automatic cleanup
  - Secure token handling

```bash
# To run the test locally (PowerShell):
$env:TESTPYPI_API_TOKEN="your-token-here"
python test_publish_to_testpypi.py
# Remove token after testing
Remove-Item Env:TESTPYPI_API_TOKEN

# To run the test locally (Bash/Zsh):
export TESTPYPI_API_TOKEN="your-token-here"
python test_publish_to_testpypi.py
unset TESTPYPI_API_TOKEN  # Important: unset when done
```

### Pull Request Checks

Each PR undergoes these automated checks:
- Code style (Black, isort)
- Type checking (mypy)
- Linting (flake8)
- Unit and integration tests
- Documentation build

### Manual Triggers

You can manually trigger workflows from the GitHub Actions tab:

1. Go to GitHub repository -> Actions
2. Select the workflow to run
3. Click "Run workflow" and select the branch

## Content & Documentation Testing

### Documentation Build Verification

- **Tool**: mkdocs with material theme
- **Process**: Documentation is built and verified during CI/CD
- **Link Checking**: Verify internal and external links
- **Rendering**: Check rendering of complex elements like tables and code blocks

### Version Infrastructure Testing

We have implemented infrastructure tests for the version management system:

- **File**: `tests/infrastructure/test_version_infrastructure.py`
- **Scope**: Verifies infrastructure components of the version management system
- **Coverage**:
  - Tests GitHub Actions workflow configuration for version checks
  - Tests publishing script configuration and function
  - Tests version consistency across all version-related files
  - Tests documentation structure and content for version management
  - Tests presence of required version files
- **Execution**: Run with `python -m unittest tests/infrastructure/test_version_infrastructure.py`

### Link Validation Testing

We have implemented comprehensive link validation to ensure users don't encounter broken links:

- **Purpose**: Validates that links in user-facing HTML and Markdown files point to existing resources
- **Script Location**: `tests/infrastructure/test_links.py`
- **Execution**: Run with `python -m unittest tests/infrastructure/test_links.py`
- **Coverage**:
  - Key files: `index.html`, `README.md`
  - Documentation: All files in `docs/` directory
  - Benchmark: Public pages in `benchmark/public/`
- **Validation Features**:
  - Identifies broken internal links
  - Detects references to old path structures after project restructuring
  - Validates both relative and absolute paths
  - Warns about external links to non-trusted domains
  - Excludes non-user-facing directories from validation

```bash
# Run link validation tests
python -m unittest tests/infrastructure/test_links.py
```

### GitHub Pages Configuration Testing

We have a dedicated testing process for GitHub Pages:

1. **Configuration Testing**:
   - Run `python tests/infrastructure/test_site_config.py` to verify site configuration
   - Ensure environment variables are set correctly

2. **Build Verification**:
   - Run `SITE_BASE_URL=<url> python -m mkdocs build` to build the site
   - Check generated files in `site/docs/` directory 

3. **URL Reference Testing**:
   - Test that the site contains proper canonical URLs
   - Verify social sharing links are correct
   - Check GitHub repository links

4. **Migration Testing**:
   - Test the process of switching between private and public repository URLs
   - Update `site_config.yml` and rebuild the site 
   - Verify all references are updated correctly

5. **Workflow Testing**:
   - Test the GitHub Actions workflow locally
   - Verify the workflow sets environment variables correctly

#### GitHub Pages Test Script

```bash
# Run full GitHub Pages test suite
python tests/infrastructure/test_github_pages.py
```

### Community Catalog Testing

- **Process**: Verify catalog updates with `python scripts/update_catalog.py --test`
- **Validation**: Check JSON schema and data integrity
- **Visualization**: Verify data visualization components

## Test Data Management

### Sample Datasets

- **Location**: Sample datasets stored in `tests/data/` directory
- **Versioning**: Version controlled along with test code
- **Types**: Include various data formats (CSV, JSON, etc.)
- **Size**: Include both small datasets for quick tests and larger ones for performance testing

### Test Fixtures

- **Framework**: pytest fixtures
- **Location**: Fixtures defined in `tests/conftest.py`
- **Scope**: Define fixtures with appropriate scopes (session, module, function)
- **Parameterization**: Use parameterized tests for data-driven testing

### Mock Data

- **Tool**: unittest.mock or pytest's monkeypatch
- **Strategy**: Mock external dependencies in unit tests
- **Implementation**: Use fixture factories to create mock objects

## Regression Testing Process

### Identifying Regression Tests

- **Critical Paths**: Identify tests covering critical functionality
- **Historical Issues**: Include tests for previously fixed bugs
- **High-Risk Areas**: Focus on areas with frequent changes

### Regression Test Suite

- **Automation**: Regression tests are automated and run in CI/CD
- **Frequency**: Run on all pull requests and scheduled builds
- **Time**: Optimize test suite to run quickly without sacrificing coverage

### Bug-Driven Testing

When bugs are found:
1. Create a failing test that reproduces the bug
2. Fix the bug and verify the test passes
3. Include the test in the regression test suite

## Test Reporting

### CI/CD Reports

- **Location**: Test reports available in GitHub Actions
- **Format**: HTML reports for human readability, JSON for machine processing
- **Coverage**: Code coverage reports generated by pytest-cov

### Test Documentation

- **Location**: Test documentation in `docs/testing/` directory
- **Content**: Test strategies, procedures, and guidelines
- **Examples**: Example test cases for different components

### Issue Tracking

- **Tool**: GitHub Issues
- **Process**: Create issues for test failures
- **Labels**: Use labels to categorize test-related issues
- **Templates**: Use issue templates for reporting test failures

---

## Appendix: Test Cheatsheet

### Common Testing Commands

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=adri

# Run specific test file
pytest tests/unit/test_assessor.py

# Run specific test function
pytest tests/unit/test_assessor.py::test_assess

# Run with verbose output
pytest -v

# Run with JUnit XML report
pytest --junitxml=results.xml
```

### Creating New Tests

1. Create a test file in the appropriate directory
2. Import the module to test
3. Write test functions using pytest fixtures
4. Run the tests to verify they pass

## Purpose & Test Coverage

**Why this file exists**: Provides comprehensive documentation of ADRI's testing philosophy, strategies, and practices to ensure high-quality, reliable software delivery.

**Key responsibilities**:
- Define testing principles and objectives
- Document testing procedures for all test types (unit, integration, E2E)
- Guide CI/CD pipeline testing configuration
- Explain test data management strategies
- Provide testing commands and examples

**Test coverage**: This document's examples, claims, and features should be verified by tests documented in [TESTING_test_coverage.md](test_coverage/TESTING_test_coverage.md)
