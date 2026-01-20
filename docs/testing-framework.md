# ADRI Comprehensive Testing Framework

## Overview

The ADRI Comprehensive Testing Framework provides 100% GitHub CI compatibility validation through local testing using ACT (GitHub Actions runner). This framework is specifically designed to test the recent CLI path resolution enhancements and ensure all changes work seamlessly across different environments and directory structures.

## Framework Components

### 1. Core Test Suites

#### Path Resolution Tests (`tests/test_path_resolution_comprehensive.py`)
- **Purpose**: Comprehensive validation of the new intelligent path resolution system
- **Coverage**: Project root detection, cross-directory execution, tutorial/dev/prod paths
- **Test Classes**:
  - `TestPathResolutionCore`: Core functionality testing
  - `TestPathResolutionIntegration`: CLI command integration
  - `TestPathResolutionCrossDirectory`: Cross-directory validation
  - `TestPathResolutionPerformance`: Performance validation

#### Environment Documentation Tests (`tests/test_environment_documentation.py`)
- **Purpose**: Validation of comprehensive environment documentation in config.yaml
- **Coverage**: Documentation completeness, switching instructions, workflow recommendations
- **Test Classes**:
  - `TestEnvironmentDocumentation`: Documentation completeness validation
  - `TestConfigurationValidation`: Config structure and content validation
  - `TestHelpGuideEnvironmentInformation`: Help guide accuracy testing
  - `TestShowConfigEnvironmentDisplay`: Command output validation

#### CLI Workflow Integration Tests (`tests/test_cli_workflow_integration.py`)
- **Purpose**: End-to-end workflow testing with path resolution integration
- **Coverage**: Complete guided workflows, cross-directory consistency, artifact validation
- **Test Classes**:
  - `TestCompleteWorkflowIntegration`: Full workflow testing
  - `TestWorkflowIntegration`: Environment-aware workflow testing
  - `TestACTWorkflowValidation`: GitHub Actions compatibility validation

### 2. Testing Scripts

#### Comprehensive ACT Testing (`scripts/comprehensive-act-test.sh`)
```bash
# Full GitHub CI compatibility testing with detailed reporting
./scripts/comprehensive-act-test.sh

# Features:
# - Full matrix testing across OS/Python versions
# - Path resolution validation in CI environment
# - Artifact validation and dependency testing
# - Performance benchmarks
# - Comprehensive compatibility reporting
```

#### Pre-PR Validation (`scripts/validate-github-compatibility.sh`)
```bash
# Quick validation before creating PRs
./scripts/validate-github-compatibility.sh

# Fast mode (skip ACT testing)
./scripts/validate-github-compatibility.sh --fast

# Generate report only
./scripts/validate-github-compatibility.sh --report-only

# Features:
# - Pre-commit validation
# - Path resolution enhancement validation
# - Performance regression detection
# - Comprehensive reporting with recommendations
```

#### Enhanced Local CI Testing (`scripts/local-ci-test.sh`)
```bash
# Enhanced local CI testing with path resolution validation
./scripts/local-ci-test.sh

# Includes:
# - Path resolution validation in CI-like environment
# - ACT-based workflow testing
# - Complete GitHub Actions workflow execution
# - Path resolution compatibility testing in ACT environment
```

### 3. Performance Benchmarks

#### CLI Path Resolution Benchmarks (`tests/performance/cli_path_resolution_benchmarks.py`)
```bash
# Run performance benchmarks
python tests/performance/cli_path_resolution_benchmarks.py --benchmark

# Features:
# - Project root detection performance testing
# - Path resolution speed benchmarks
# - Memory usage validation
# - Concurrent operation testing
# - Performance regression detection
```

### 4. Mock Project Fixtures

#### Mock Projects (`tests/fixtures/mock_projects.py`)
- **ProjectFixtureManager**: Manages creation and cleanup of test projects
- **MockProjectFixtures**: Factory for different project types
- **TestDataGenerator**: Generates realistic test data
- **Available Fixtures**:
  - Simple ADRI project
  - Complex multi-directory project
  - Deep nested project (performance testing)
  - Enterprise project (comprehensive governance)

## Usage Guide

### Quick Start

1. **Run basic validation before committing:**
   ```bash
   ./scripts/validate-github-compatibility.sh --fast
   ```

2. **Run comprehensive GitHub CI validation:**
   ```bash
   ./scripts/comprehensive-act-test.sh
   ```

3. **Test specific enhancements:**
   ```bash
   python -m pytest tests/test_path_resolution_comprehensive.py -v
   python -m pytest tests/test_environment_documentation.py -v
   ```

### Complete Testing Workflow

#### For Feature Development
```bash
# 1. During development - quick validation
./scripts/validate-github-compatibility.sh --fast

# 2. Before committing - full local CI
./scripts/local-ci-test.sh

# 3. Before creating PR - comprehensive validation
./scripts/comprehensive-act-test.sh

# 4. Performance validation
python tests/performance/cli_path_resolution_benchmarks.py --benchmark
```

#### For CI/CD Integration
```bash
# Validate new GitHub workflow
act -W .github/workflows/test-validation.yml

# Test specific workflow jobs
act -W .github/workflows/test-validation.yml -j path-resolution-validation
act -W .github/workflows/test-validation.yml -j enhanced-test-suite
act -W .github/workflows/test-validation.yml -j integration-workflow-test
```

### Testing Different Scenarios

#### Cross-Directory Testing
```python
# Use mock project context for testing from different directories
from tests.fixtures.mock_projects import mock_project_context, MockProjectFixtures

with mock_project_context(MockProjectFixtures.complex_multi_directory_project(), "docs/src") as project_root:
    # Test commands from docs/src directory
    root = _find_adri_project_root()
    assert root == project_root
```

#### Performance Testing
```python
# Use performance benchmarks for regression testing
from tests.performance.cli_path_resolution_benchmarks import PathResolutionBenchmarks

benchmarks = PathResolutionBenchmarks()
benchmark = benchmarks.benchmark_function(
    "test_operation",
    lambda: _find_adri_project_root(),
    iterations=1000
)
assert benchmarks.validate_benchmark(benchmark, "project_root_finding")
```

## Configuration

### ACT Configuration (`.actrc`)
The framework includes optimized ACT configuration for:
- Consistent Linux container usage (`ubuntu-latest`)
- Resource limits (4GB memory, 2 CPUs)
- Artifact handling
- Security isolation
- Performance optimization

### GitHub Workflows

#### Test Validation Workflow (`.github/workflows/test-validation.yml`)
- **Triggers**: Changes to CLI, tests, config files, scripts
- **Jobs**:
  - `path-resolution-validation`: Core path resolution testing
  - `enhanced-test-suite`: New test suite validation
  - `workflow-compatibility`: Workflow structure validation
  - `environment-documentation-check`: Documentation verification
  - `integration-workflow-test`: End-to-end integration testing

## Performance Standards

### Performance Thresholds
- **Project Root Finding**: ≤0.01s average, ≥100 ops/sec
- **Path Resolution**: ≤0.001s average, ≥1000 ops/sec
- **Cross-Directory Operations**: ≤0.01s average, ≥50 ops/sec
- **Concurrent Operations**: ≤0.02s average, ≥25 ops/sec

### Memory Usage
- Memory increase should be <50MB during intensive operations
- No memory leaks during repeated operations

## Troubleshooting

### Common Issues

#### ACT Not Working
```bash
# Install ACT
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash  # Linux

# Verify installation
act --version
```

#### Performance Issues
```bash
# Run performance benchmarks to identify bottlenecks
python tests/performance/cli_path_resolution_benchmarks.py --benchmark

# Check for performance regressions
./scripts/validate-github-compatibility.sh
```

#### Test Failures
```bash
# Run specific test suites to isolate issues
python -m pytest tests/test_path_resolution_comprehensive.py -v --tb=short
python -m pytest tests/test_environment_documentation.py -v --tb=short

# Check test coverage
python -m pytest tests/ --cov=src/adri/cli --cov-report=html
```

### Debug Mode

#### Verbose Testing
```bash
# Enable verbose output for debugging
python -m pytest tests/test_path_resolution_comprehensive.py -v -s

# ACT verbose mode
act -W .github/workflows/test-validation.yml -v
```

#### Detailed Reporting
```bash
# Generate detailed validation report
./scripts/validate-github-compatibility.sh --report-only

# View comprehensive ACT test results
cat tests/coverage/act-logs/comprehensive-test-report.txt
```

## Integration with Existing Testing

### Pre-commit Integration
The framework integrates with existing pre-commit hooks:
```bash
# Run all pre-commit checks including new path resolution validation
pre-commit run --all-files
```

### Coverage Integration
```bash
# Run with coverage for path resolution functions
python -m pytest tests/test_path_resolution_comprehensive.py --cov=src/adri/cli --cov-report=html

# View coverage report
open tests/coverage/html/index.html
```

### CI/CD Pipeline Integration
The framework is designed to work seamlessly with existing GitHub Actions:
- Extends existing CI workflow validation
- Adds specific path resolution testing
- Maintains all existing functionality
- Provides additional confidence layers

## Best Practices

### Before Creating PRs
1. Run quick validation: `./scripts/validate-github-compatibility.sh --fast`
2. Fix any failing tests
3. Run comprehensive validation: `./scripts/comprehensive-act-test.sh`
4. Verify 95%+ success rate before creating PR

### During Development
1. Use mock project fixtures for consistent testing environments
2. Run specific test suites for targeted validation
3. Monitor performance benchmarks for regressions
4. Validate cross-directory functionality regularly

### For Maintainers
1. Review comprehensive test reports before merging PRs
2. Monitor performance trends over time
3. Update performance thresholds as needed
4. Ensure all new features have corresponding tests

## Reporting

### Test Reports
- **JSON Reports**: Machine-readable results in `tests/coverage/`
- **Human-readable Reports**: Summary reports in `tests/coverage/act-logs/`
- **Coverage Reports**: HTML coverage reports in `tests/coverage/html/`
- **Performance Reports**: Benchmark results with trend analysis

### Key Metrics
- **Success Rate**: Percentage of tests passing
- **Performance Metrics**: Operation speed and resource usage
- **Coverage Metrics**: Code coverage for enhanced features
- **Compatibility Score**: GitHub CI compatibility rating

This framework provides comprehensive validation that ensures your changes will work flawlessly in GitHub CI, preventing merge conflicts and ensuring smooth feature development.
