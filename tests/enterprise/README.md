# Enterprise Feature Testing Documentation

This directory contains comprehensive test coverage for all enterprise features in the verodat-adri package.

## Test Structure

### Core Test Files

| File | Purpose | Coverage Target |
|------|---------|-----------------|
| `conftest.py` | Test fixtures and configuration for enterprise testing | 100% |
| `test_license_validation.py` | License validation system tests | 95% |
| `test_reasoning_logger.py` | AI reasoning logging functionality tests | 90% |
| `test_verodat_logging_advanced.py` | Advanced Verodat API integration tests | 90% |
| `test_enterprise_integration.py` | End-to-end component interaction tests | 85% |
| `test_performance.py` | Performance and scalability tests | 85% |

### Test Categories

#### Unit Tests (`@pytest.mark.unit`)
- Individual component functionality
- Isolated testing with comprehensive mocking
- Fast execution (< 1 second per test)

#### Integration Tests (`@pytest.mark.integration`)
- Component interaction validation
- Cross-system communication testing
- Realistic data processing workflows

#### Performance Tests (`@pytest.mark.performance`)
- Load testing and benchmarking
- Memory usage and resource efficiency
- Scalability under concurrent operations

## Enterprise Components Tested

### 1. License Validation System
**File:** `test_license_validation.py`
**Classes Tested:**
- `LicenseValidator` - Singleton pattern, API validation
- `LicenseInfo` - License information data structure
- `LicenseValidationError` - Error handling

**Key Test Scenarios:**
- API key validation with Verodat API
- License caching (24-hour duration)
- Error handling for network issues
- Singleton pattern thread safety
- Concurrent validation performance

**Critical Tests:**
```python
def test_license_validator_singleton_pattern()
def test_api_key_validation_success()
def test_license_cache_behavior()
def test_concurrent_license_validation_performance()
```

### 2. Reasoning Logger
**File:** `test_reasoning_logger.py`
**Classes Tested:**
- `ReasoningLogger` - AI reasoning step logging

**Key Test Scenarios:**
- JSONL file logging (prompts and responses)
- History retrieval and filtering
- Concurrent logging operations
- Large data structure handling
- Error recovery and resilience

**Critical Tests:**
```python
def test_complete_reasoning_step_logging()
def test_concurrent_file_operations()
def test_reasoning_history_retrieval()
def test_large_data_logging_performance()
```

### 3. Verodat API Integration
**File:** `test_verodat_logging_advanced.py`
**Classes Tested:**
- `VerodatLogger` - Enterprise API integration
- `send_to_verodat` - Convenience function

**Key Test Scenarios:**
- Batch processing and retry logic
- Enterprise workflow context handling
- Advanced error scenarios
- Performance under load
- Backward compatibility

**Critical Tests:**
```python
def test_batch_processing_behavior()
def test_api_retry_logic_on_server_errors()
def test_assessment_logging_with_enterprise_context()
def test_concurrent_logging_performance()
```

### 4. Enterprise Integration
**File:** `test_enterprise_integration.py`
**Integration Scenarios:**
- Complete enterprise decorator workflow
- License + Reasoning + Verodat coordination
- Environment-aware contract resolution
- Error propagation and recovery
- Concurrent enterprise workflows

**Critical Tests:**
```python
def test_full_enterprise_decorator_workflow()
def test_enterprise_workflow_with_all_logging_components()
def test_environment_aware_contract_resolution_integration()
def test_concurrent_enterprise_workflows()
```

### 5. Performance Testing
**File:** `test_performance.py`
**Performance Areas:**
- Enterprise decorator overhead
- License validation speed
- Reasoning logger throughput
- Verodat batch processing
- Memory efficiency
- Scalability testing

**Performance Baselines:**
- License validation: < 5.0 seconds
- License cache hits: < 0.1 seconds
- Reasoning log writes: < 0.5 seconds
- Verodat API calls: < 10.0 seconds
- Decorator overhead: < 0.1 seconds

## Running Tests

### All Enterprise Tests
```bash
pytest tests/enterprise/ -v
```

### Specific Test Categories
```bash
# Unit tests only
pytest tests/enterprise/ -m "unit" -v

# Integration tests only
pytest tests/enterprise/ -m "integration" -v

# Performance tests only
pytest tests/enterprise/ -m "performance" -v

# Enterprise-specific tests
pytest tests/enterprise/ -m "enterprise" -v
```

### Specific Components
```bash
# License validation tests
pytest tests/enterprise/test_license_validation.py -v

# Reasoning logger tests
pytest tests/enterprise/test_reasoning_logger.py -v

# Verodat integration tests
pytest tests/enterprise/test_verodat_logging_advanced.py -v

# End-to-end integration tests
pytest tests/enterprise/test_enterprise_integration.py -v

# Performance tests
pytest tests/enterprise/test_performance.py -v
```

### Coverage Analysis
```bash
# Generate coverage report for enterprise module
pytest tests/enterprise/ --cov=src/adri_enterprise --cov-report=html

# Coverage with specific thresholds
pytest tests/enterprise/ --cov=src/adri_enterprise --cov-fail-under=90
```

### Parallel Execution
```bash
# Run tests in parallel for faster execution
pytest tests/enterprise/ -n auto
```

## Test Fixtures

### Key Fixtures from `conftest.py`

| Fixture | Purpose | Usage |
|---------|---------|-------|
| `mock_api_key` | Provides test API key | All license tests |
| `mock_license_info` | Mock successful license validation | License validation tests |
| `mock_verodat_api_success` | Mock successful API responses | API integration tests |
| `temp_log_dir` | Temporary logging directory | Reasoning logger tests |
| `temp_config_dir` | Temporary config with dev/prod setup | Configuration tests |
| `enterprise_env_vars` | Enterprise environment variables | Integration tests |
| `clean_license_cache` | Clear license cache before/after tests | License tests |
| `mock_reasoning_data` | Sample reasoning step data | Reasoning tests |
| `mock_workflow_context` | Sample workflow context | Workflow tests |
| `mock_data_provenance` | Sample data provenance | Provenance tests |
| `performance_baseline` | Performance expectations | Performance tests |

## Mocking Strategy

### API Mocking
- `requests.get` and `requests.post` are mocked for all external API calls
- Successful, failed, and timeout scenarios are tested
- Response data is realistic and based on actual API specifications

### File System Mocking
- Temporary directories are used for all file operations
- Concurrent file access is tested with real file system operations
- Cleanup is automatic via pytest fixtures

### Environment Variable Mocking
- `patch.dict(os.environ, {...})` is used for environment variable testing
- Original values are preserved and restored after tests
- Multiple environment scenarios (dev/prod) are tested

## CI/CD Integration

### GitHub Actions Compatibility
Tests are designed to run in CI environments with:
- No external dependencies (all APIs mocked)
- Deterministic behavior (no timing dependencies)
- Proper cleanup (no file system artifacts)
- Appropriate timeouts (60 seconds max)

### Dependencies for CI
All required test dependencies are specified in `pyproject.toml`:
```toml
[project.optional-dependencies]
test = [
    "pytest>=8.2.0",
    "pytest-cov>=5.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-xdist>=3.3.0",
    "freezegun>=1.2.2",
    "responses>=0.24.0",
    "psutil>=5.9.0",
    # ... additional dependencies
]
```

### Coverage Requirements
- Overall enterprise package: 90% minimum
- License validation: 95% minimum
- Reasoning logger: 90% minimum
- Verodat integration: 90% minimum
- Integration tests: 85% minimum

## Troubleshooting

### Common Issues

#### License Validation Tests Fail
**Problem:** Tests fail with "License validation timeout"
**Solution:** Ensure `mock_verodat_api_success` fixture is being used

#### Reasoning Logger Tests Fail
**Problem:** File permission errors in log directory
**Solution:** Use `temp_log_dir` fixture which provides proper temporary directories

#### Integration Tests Timeout
**Problem:** Tests exceed 60-second timeout
**Solution:** Check for infinite loops or missing mocks in concurrent operations

#### Performance Tests Inconsistent
**Problem:** Performance tests fail on slower systems
**Solution:** Performance baselines are generous; failures indicate real performance issues

### Environment Setup

#### Required Environment Variables for Manual Testing
```bash
export VERODAT_API_KEY="your-test-api-key"
export ADRI_ENV="development"
export ADRI_CONFIG_PATH="/path/to/test/config.yaml"
```

#### Debugging Failed Tests
```bash
# Run with verbose output and no capture
pytest tests/enterprise/test_license_validation.py::test_name -v -s

# Run with debugger
pytest tests/enterprise/test_license_validation.py::test_name --pdb

# Run with detailed traceback
pytest tests/enterprise/test_license_validation.py::test_name --tb=long
```

## Contributing

### Adding New Tests

1. **Choose the appropriate test file** based on the component being tested
2. **Use existing fixtures** from `conftest.py` when possible
3. **Follow naming conventions**: `test_component_functionality_scenario`
4. **Add appropriate markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, etc.
5. **Include docstrings** explaining test purpose and scenarios
6. **Update this documentation** when adding new test categories

### Test Quality Standards

1. **Each test should be independent** - no shared state
2. **Tests should be deterministic** - same result every time
3. **Use descriptive assertions** - `assert result.is_valid is True` not `assert result.is_valid`
4. **Mock external dependencies** - no real API calls or file system dependencies in CI
5. **Include error scenarios** - test both success and failure paths
6. **Performance tests should be realistic** - test actual usage patterns

### Code Coverage

Tests should aim for:
- **Statement coverage**: All lines executed
- **Branch coverage**: All conditional paths tested
- **Function coverage**: All functions called
- **Integration coverage**: All component interactions tested

Use `pytest --cov` to generate coverage reports and identify untested code paths.

## Conclusion

This comprehensive test suite ensures enterprise features work reliably across different environments and usage patterns. The tests provide confidence in the stability, performance, and correctness of all enterprise functionality.

For questions or issues with testing, please refer to the main project documentation or open an issue in the repository.
