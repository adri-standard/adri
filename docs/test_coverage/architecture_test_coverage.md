# Architecture Test Coverage

## Overview

This document outlines the test coverage for the ADRI architecture components and design decisions.

## Component Test Coverage

### 1. Data Source Connectors
- **Unit Tests**: `tests/unit/test_connectors.py`
- **Integration Tests**: `tests/integration/test_connector_integration.py`
- **Coverage**: 85%
- **Key Test Cases**:
  - File connector initialization and data loading
  - Database connector connection handling
  - API connector authentication and retry logic
  - Error handling for invalid data sources

### 2. Dimension Assessors
- **Unit Tests**: `tests/unit/test_dimensions/`
- **Integration Tests**: `tests/integration/test_dimension_integration.py`
- **Coverage**: 92%
- **Key Test Cases**:
  - Each dimension's scoring algorithm
  - Dimension registry functionality
  - Custom dimension registration
  - Weighted score calculations

### 3. Rule System
- **Unit Tests**: `tests/unit/test_rules/`
- **Coverage**: 88%
- **Key Test Cases**:
  - Rule evaluation logic
  - Rule parameter validation
  - Custom rule creation
  - Rule narrative generation

### 4. Report Generation
- **Unit Tests**: `tests/unit/test_report.py`
- **Integration Tests**: `tests/integration/test_report_generation.py`
- **Coverage**: 90%
- **Key Test Cases**:
  - HTML report generation
  - JSON serialization
  - Chart generation
  - Report comparison functionality

### 5. Configuration System
- **Unit Tests**: `tests/unit/test_config.py`
- **Coverage**: 95%
- **Key Test Cases**:
  - Default configuration loading
  - Custom configuration merging
  - Configuration validation
  - Environment variable handling

## Architecture Decision Tests

### 1. Plugin System
- **Test**: Verify dynamic loading of custom components
- **Location**: `tests/infrastructure/test_plugin_system.py`
- **Status**: ✅ Passing

### 2. Scoring Algorithm
- **Test**: Validate weighted dimension scoring
- **Location**: `tests/unit/test_scoring.py`
- **Status**: ✅ Passing

### 3. Metadata Companion Files
- **Test**: Verify metadata file discovery and parsing
- **Location**: `tests/unit/test_metadata.py`
- **Status**: ✅ Passing

### 4. Registry Pattern
- **Test**: Verify registry functionality for dimensions and rules
- **Location**: `tests/unit/test_registry.py`
- **Status**: ✅ Passing

## Performance Tests

### 1. Large Dataset Handling
- **Test**: Process 1GB+ CSV files
- **Location**: `tests/performance/test_large_files.py`
- **Benchmark**: < 30 seconds for 1GB file

### 2. Concurrent Assessment
- **Test**: Multiple simultaneous assessments
- **Location**: `tests/performance/test_concurrency.py`
- **Benchmark**: Linear scaling up to 4 cores

## Integration Tests

### 1. End-to-End Workflow
- **Test**: Complete assessment from file to report
- **Location**: `tests/e2e/test_full_workflow.py`
- **Scenarios**:
  - CSV file assessment
  - Database assessment
  - API endpoint assessment

### 2. Framework Integration
- **Test**: Integration with LangChain, CrewAI, DSPy
- **Location**: `tests/integration/test_framework_integration.py`
- **Coverage**: All major frameworks

## Security Tests

### 1. Input Validation
- **Test**: Malicious file upload attempts
- **Location**: `tests/security/test_input_validation.py`

### 2. SQL Injection Prevention
- **Test**: Database connector SQL injection attempts
- **Location**: `tests/security/test_sql_injection.py`

## Test Maintenance

### Running Architecture Tests
```bash
# Run all architecture-related tests
pytest tests/unit/test_connectors.py tests/unit/test_dimensions/ tests/unit/test_registry.py

# Run with coverage
pytest --cov=adri.connectors --cov=adri.dimensions tests/
```

### Adding New Tests
When modifying architecture:
1. Add unit tests for new components
2. Update integration tests for changed interfaces
3. Add performance tests for new features
4. Document test coverage in this file

## Coverage Goals

- **Overall Target**: 90% code coverage
- **Critical Components**: 95% coverage
- **New Features**: Must include tests before merge

## Related Documentation

- [Architecture Overview](../architecture.md)
- [Testing Strategy](../TESTING.md)
- [Development Guide](../DEVELOPER.md)
