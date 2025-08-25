# Token Explosion Prevention Measures

## Overview
This document describes the measures implemented to prevent token explosion in the ADRI Validator test suite, particularly for performance and stress tests that work with large datasets.

## Problem Statement
Performance and stress tests were causing token explosion issues due to:
- Large dataset outputs in test failures
- Verbose test output from hundreds/thousands of test iterations
- Full DataFrame representations in assertion failures
- Extensive logging during performance tests

## Solutions Implemented

### 1. Test Utilities Module (`tests/test_utils.py`)
Created comprehensive utilities for managing test output:

#### OutputLimiter Class
- **Purpose**: Truncates test output to prevent token explosion
- **Features**:
  - Configurable output limits via environment variables
  - Special handling for DataFrames, arrays, lists, and dictionaries
  - Context-aware truncation messages

**Environment Variables**:
- `ADRI_TEST_MAX_OUTPUT`: Maximum characters for general output (default: 1000)
- `ADRI_TEST_MAX_DF_ROWS`: Maximum DataFrame rows to display (default: 10)
- `ADRI_TEST_MAX_LIST_ITEMS`: Maximum list items to show (default: 10)

#### TestDataGenerator Class
- **Purpose**: Generate test data with size controls
- **Features**:
  - Automatic size limiting based on test type
  - Environment-based overrides
  - Warning messages when datasets are reduced

**Environment Variables**:
- `ADRI_TEST_MAX_ROWS`: Override maximum dataset rows
- `ADRI_SKIP_SLOW_TESTS`: Skip slow-running tests

### 2. Pytest Configuration

#### pytest.ini
```ini
# Limit output verbosity
addopts = -q --tb=short --maxfail=3 --disable-warnings
console_output_style = progress
timeout = 30
```

#### Test Markers
- `@pytest.mark.quick`: Fast tests (< 100 rows)
- `@pytest.mark.performance`: Performance tests (skipped by default)
- `@pytest.mark.stress`: Stress tests (skipped by default)
- `@pytest.mark.ci_only`: CI-only tests
- `@pytest.mark.audit`: Audit logging tests
- `@pytest.mark.csv_output`: CSV output tests

### 3. Shared Test Configuration (`tests/conftest.py`)
- Automatic output limiting for all tests
- Shared fixtures for common test needs
- Custom command-line options for selective test execution
- Automatic skipping of expensive tests

**Custom CLI Options**:
- `--performance`: Run performance tests
- `--stress`: Run stress tests
- `--all-tests`: Run all tests including expensive ones

### 4. Performance Test Updates

#### test_comprehensive_performance.py
- Added `@pytest.mark.performance` to all test classes
- Integrated OutputLimiter and TestDataGenerator
- Added skip conditions for CI environments
- Reduced default dataset sizes

#### test_stress_performance.py
- Added `@pytest.mark.stress` to all test classes
- Implemented automatic dataset size reduction
- Added `skip_if_ci()` for memory-intensive tests
- Configurable stress test parameters

## Usage Examples

### Running Tests with Controlled Output

```bash
# Run only quick tests (default)
pytest

# Run with performance tests
pytest --performance

# Run with stress tests
pytest --stress

# Run all tests
pytest --all-tests

# Run with custom limits
ADRI_TEST_MAX_ROWS=100 pytest
ADRI_TEST_MAX_OUTPUT=500 pytest

# Skip slow tests
ADRI_SKIP_SLOW_TESTS=1 pytest

# Run in CI with reduced datasets
CI=1 ADRI_TEST_MAX_ROWS=1000 pytest
```

### Using Test Utilities in New Tests

```python
from tests.test_utils import OutputLimiter, TestDataGenerator, skip_if_ci

def test_with_controlled_output():
    # Generate safe dataset
    data = TestDataGenerator.generate_dataset(
        rows=10000,  # Will be limited if needed
        cols=10,
        test_type='performance'
    )

    # Use safe assertions
    try:
        assert len(data) == expected_len
    except AssertionError:
        # Output will be automatically truncated
        print(OutputLimiter.truncate(data, "actual data"))
        raise

def test_skip_in_ci():
    skip_if_ci()  # Skip this test in CI
    # Memory-intensive test code here
```

## Benefits

1. **Prevents Token Explosion**: Output is automatically limited to reasonable sizes
2. **Flexible Configuration**: Environment variables allow runtime adjustment
3. **CI-Friendly**: Tests automatically adapt to CI environments
4. **Developer-Friendly**: Full output available locally, limited in CI
5. **Performance**: Expensive tests skipped by default
6. **Maintainable**: Centralized configuration and utilities

## Best Practices

1. **Always use test markers** for categorizing tests
2. **Use TestDataGenerator** for creating test datasets
3. **Apply skip_if_ci()** to memory/CPU intensive tests
4. **Set reasonable timeouts** for long-running tests
5. **Use OutputLimiter** when displaying large objects in test output
6. **Configure CI pipelines** with appropriate environment variables

## Environment Variable Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `ADRI_TEST_MAX_OUTPUT` | 1000 | Maximum characters in output |
| `ADRI_TEST_MAX_DF_ROWS` | 10 | Maximum DataFrame rows to display |
| `ADRI_TEST_MAX_LIST_ITEMS` | 10 | Maximum list items to show |
| `ADRI_TEST_MAX_ROWS` | 0 (no limit) | Maximum dataset rows |
| `ADRI_SKIP_SLOW_TESTS` | false | Skip slow tests |
| `ADRI_RUN_PERFORMANCE_TESTS` | false | Enable performance tests |
| `ADRI_STRESS_LOG_ENTRIES` | 10000 | Number of stress test log entries |
| `CI` | false | Running in CI environment |

## Monitoring and Maintenance

1. **Regular Review**: Periodically review test execution times
2. **Adjust Limits**: Update limits based on CI capacity
3. **Profile Tests**: Use pytest-profiling to identify slow tests
4. **Clean Up**: Remove or optimize tests that consistently timeout

## Conclusion

These measures ensure that the ADRI Validator test suite can run efficiently in both local development and CI/CD environments without causing token explosion or resource exhaustion. The flexible configuration allows teams to adjust behavior based on their specific needs and constraints.
