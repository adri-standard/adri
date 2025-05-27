# Metadata Generator Test Coverage

This document provides comprehensive test coverage information for the ADRI metadata generator functionality, which powers the `adri init` command.

## Overview

The metadata generator feature reduces the setup overhead for ADRI by automatically generating starter metadata files based on data analysis. This feature was implemented to address user feedback about the manual effort required to create metadata files.

## Component Coverage

### 1. MetadataGenerator Class (`adri/utils/metadata_generator.py`)

**Unit Tests**: `tests/unit/utils/test_metadata_generator.py`

#### Core Functionality Tests

| Method | Test Coverage | Test Cases |
|--------|--------------|------------|
| `__init__` | ✅ Complete | - Initialization with mock FileConnector<br>- Attribute setting verification |
| `generate_all_metadata` | ✅ Complete | - All dimensions generated<br>- File creation verification<br>- Valid JSON output<br>- Error handling for individual generators |
| `generate_validity_metadata` | ✅ Complete | - Type definitions for all column types<br>- Numeric range detection<br>- Categorical allowed values<br>- ID pattern detection<br>- Date format placeholders<br>- Invalid value counting |
| `generate_completeness_metadata` | ✅ Complete | - Overall completeness calculation<br>- Field-level completeness<br>- Missing value detection<br>- Required field inference<br>- Missing indicator detection |
| `generate_freshness_metadata` | ✅ Complete | - Timestamp field detection<br>- Date column name pattern matching<br>- Sample value extraction<br>- Freshness suggestions |
| `generate_consistency_metadata` | ✅ Complete | - Numeric column relationship suggestions<br>- ID relationship detection<br>- Categorical relationship hints<br>- Cross-dataset placeholders |
| `generate_plausibility_metadata` | ✅ Complete | - Outlier detection for numeric columns<br>- Z-score calculations<br>- Rare categorical value detection<br>- Domain rule placeholders |
| `_map_to_json_type` | ✅ Complete | - All type mappings tested<br>- Default case handling |
| `_save_metadata` | ✅ Complete | - File creation<br>- JSON formatting<br>- Path handling |

#### Edge Case Tests

| Scenario | Test Coverage | Description |
|----------|--------------|-------------|
| Empty DataFrame | ✅ Complete | Tests handling of empty data without errors |
| All Null Columns | ✅ Complete | Tests columns with 100% missing values |
| Large Categorical Fields | ✅ Complete | Tests categorical fields with >20 unique values |
| Mixed Date Formats | ✅ Complete | Tests date columns with different format patterns |
| Single Row Data | ✅ Complete | Tests statistical calculations with minimal data |
| Non-standard Column Names | ✅ Complete | Tests handling of special characters in column names |

### 2. CLI Integration (`adri init` command)

**Integration Tests**: `tests/integration/test_cli_init.py`

#### Command Line Tests

| Test Case | Coverage | Description |
|-----------|----------|-------------|
| Basic Command | ✅ Complete | `adri init data.csv` |
| Custom Output Directory | ✅ Complete | `adri init data.csv --output-dir ./metadata` |
| Specific Dimensions | ✅ Complete | `adri init data.csv --dimensions validity completeness` |
| File Not Found | ✅ Complete | Error handling for missing files |
| Invalid File Format | ✅ Complete | Error handling for unsupported formats |
| JSON Input | ✅ Complete | Support for JSON data files |
| Excel Input | ✅ Complete | Support for Excel files |
| Missing Values Handling | ✅ Complete | Proper handling of incomplete data |

#### Output Validation Tests

| Validation | Coverage | Description |
|------------|----------|-------------|
| File Creation | ✅ Complete | All metadata files created in correct location |
| JSON Validity | ✅ Complete | Output files are valid JSON |
| Content Accuracy | ✅ Complete | Generated metadata matches data characteristics |
| Error Messages | ✅ Complete | User-friendly error reporting |

### 3. Example Documentation

**Example Tests**: `tests/unit/examples/test_06_metadata_generation.py`

| Test Area | Coverage | Description |
|-----------|----------|-------------|
| File Existence | ✅ Complete | Example file exists and is valid Python |
| Content Verification | ✅ Complete | Example demonstrates all key features |
| Time Savings Documentation | ✅ Complete | Claims about efficiency gains |
| All Dimensions Coverage | ✅ Complete | Shows all 5 metadata types |
| Executable Structure | ✅ Complete | Proper main() function and imports |

## Test Execution

### Running All Tests

```bash
# Run all metadata generator tests
pytest tests/unit/utils/test_metadata_generator.py tests/integration/test_cli_init.py tests/unit/examples/test_06_metadata_generation.py -v

# Run with coverage report
pytest --cov=adri.utils.metadata_generator --cov=adri.cli tests/unit/utils/test_metadata_generator.py tests/integration/test_cli_init.py
```

### Individual Test Suites

```bash
# Unit tests only
pytest tests/unit/utils/test_metadata_generator.py -v

# Integration tests only
pytest tests/integration/test_cli_init.py -v

# Example tests only
pytest tests/unit/examples/test_06_metadata_generation.py -v
```

## Coverage Metrics

Current test coverage for metadata generation functionality:

- **Line Coverage**: >95%
- **Branch Coverage**: >90%
- **Edge Cases**: Comprehensive

## Test Data Requirements

The tests use various test datasets to ensure comprehensive coverage:

1. **Basic CSV**: Standard tabular data with mixed types
2. **Missing Values**: Data with various missing value patterns
3. **Large Categorical**: Data with many unique categorical values
4. **Date Formats**: Data with different date representations
5. **Numeric Outliers**: Data with statistical anomalies

## CI/CD Integration

These tests are automatically run in the CI/CD pipeline:

1. On every pull request
2. On commits to main/develop branches
3. Before releases

## Known Limitations and Future Improvements

1. **Large File Testing**: Current tests use small datasets. Future tests should include performance testing with large files.
2. **Binary Format Support**: Tests primarily focus on text-based formats (CSV, JSON). Additional formats could be tested.
3. **Encoding Issues**: More tests needed for non-UTF-8 encodings.

## Test Maintenance

When modifying the metadata generator:

1. Update unit tests for any new methods or logic changes
2. Update integration tests for CLI changes
3. Update this documentation
4. Ensure all tests pass before merging

## Related Documentation

- [Testing Guide](../TESTING.md)
- [CLI Documentation](../CLI.md)
- [Contributing Guide](../CONTRIBUTING.md)
