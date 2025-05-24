# ADRI Documentation Testing Framework

A comprehensive testing framework to ensure the quality, accuracy, and consistency of ADRI documentation.

## Overview

This testing framework validates ADRI documentation across five key phases:

1. **Code Examples Testing** - Ensures all code snippets in documentation are executable
2. **Link Validation** - Verifies internal and external links are valid
3. **Vision Alignment** - Checks terminology consistency and alignment with ADRI vision
4. **Content Structure** - Validates document structure and formatting
5. **Comprehensive Reporting** - Generates detailed HTML and Markdown reports

## Project Structure

```
tests/documentation/
├── README.md                    # This file
├── __init__.py                  # Package initialization
├── base_doc_test.py            # Base test class with common functionality
├── test_code_examples.py       # Phase 1: Code example testing
├── test_links.py               # Phase 2: Link validation
├── test_vision_alignment.py    # Phase 3: Vision alignment checking
├── test_content_structure.py   # Phase 4: Content structure validation
├── run_all_tests.py           # Phase 5: Test runner with reporting
├── test_config.yaml           # Configuration file
├── utils/                     # Utility modules
│   ├── __init__.py
│   ├── code_extractor.py      # Extract and classify code blocks
│   ├── link_validator.py      # Validate various link types
│   └── vision_checker.py      # Check vision alignment
├── fixtures/                  # Test data (created at runtime)
│   ├── sample_data.csv
│   └── test_config.yaml
└── reports/                   # Generated reports (created at runtime)
    ├── doc_test_results.html
    ├── doc_test_summary.md
    ├── vision_alignment_report.txt
    └── results.json
```

## Installation

The framework uses Python standard library and common packages:

```bash
pip install pyyaml markdown requests
```

## Usage

### Run All Tests

```bash
python tests/documentation/run_all_tests.py
```

### Run Specific Phases

```bash
# Run only code and link tests
python tests/documentation/run_all_tests.py --phases code,links

# Skip external link validation (faster)
python tests/documentation/run_all_tests.py --skip-external
```

### Run Individual Test Phases

```bash
# Test code examples only
python tests/documentation/test_code_examples.py

# Test links only
python tests/documentation/test_links.py

# Test vision alignment only
python tests/documentation/test_vision_alignment.py

# Test content structure only
python tests/documentation/test_content_structure.py
```

## Configuration

Edit `test_config.yaml` to customize:

- **Documentation paths** - Which files to test
- **Code testing settings** - Timeout, skip patterns
- **Link validation** - External link checking, timeouts
- **Vision alignment** - Core terms, deprecated terms
- **Content structure** - Required sections, formatting rules
- **Reporting** - Output formats and paths

## Test Phases

### Phase 1: Code Examples Testing

- Extracts Python code blocks from markdown files
- Classifies code as inline, snippet, complete, or interactive
- Executes code in isolated environment with timeout
- Creates test fixtures for data-dependent examples
- Skips pseudo-code and placeholder examples

### Phase 2: Link Validation

- Extracts all link types (internal docs, code files, external URLs, anchors)
- Validates file existence for internal links
- Checks HTTP status for external links (with caching)
- Verifies anchor targets exist in documents
- Parallel checking for better performance

### Phase 3: Vision Alignment

- Ensures consistent terminology usage
- Flags deprecated terms
- Checks document tone (positive vs negative)
- Validates required sections by document type
- Verifies key ADRI principles are mentioned
- Generates alignment score (0.0 to 1.0)

### Phase 4: Content Structure

- Validates document structure by type (dimension, guide, integration)
- Checks header hierarchy and depth
- Ensures consistent formatting (code blocks, lists, bold)
- Identifies orphaned documents
- Verifies metadata completeness

### Phase 5: Comprehensive Reporting

- Runs all test phases
- Generates HTML report with visual summary
- Creates Markdown report for documentation
- Produces JSON results for CI/CD integration
- GitHub Actions compatible output

## Report Outputs

### HTML Report
Beautiful, responsive report with:
- Summary cards showing pass/fail statistics
- Phase-by-phase breakdown
- Visual indicators (colors, icons)
- Professional styling

### Markdown Report
Simple text report with:
- Summary table
- Phase results
- Suitable for inclusion in documentation

### JSON Results
Machine-readable format with:
- Detailed test results
- Timestamps
- Phase-specific data
- CI/CD integration ready

## CI/CD Integration

The framework is designed for continuous integration:

```yaml
# Example GitHub Actions workflow
- name: Test Documentation
  run: |
    pip install pyyaml markdown requests
    python tests/documentation/run_all_tests.py
```

The test runner returns appropriate exit codes:
- 0 = All tests passed
- 1 = Some tests failed

## Extending the Framework

To add new test types:

1. Create a new test file inheriting from `BaseDocumentationTest`
2. Implement test methods following the pattern
3. Add to `run_all_tests.py` test phases
4. Update configuration in `test_config.yaml`

## Best Practices

1. **Run regularly** - Include in CI/CD pipeline
2. **Fix failures promptly** - Broken examples confuse users
3. **Update config** - Keep terminology and structure rules current
4. **Review reports** - Look for patterns in failures
5. **Iterate** - Improve tests based on real issues found

## Troubleshooting

### Code tests failing
- Check if imports are available
- Verify test fixtures exist
- Review timeout settings

### Link tests failing
- External sites may be temporarily down
- Use `--skip-external` for offline testing
- Check for moved/renamed files

### Vision alignment issues
- Review and update terminology in config
- Check for new deprecated terms
- Ensure consistent word usage

### Structure issues
- Validate against document type patterns
- Check for proper markdown formatting
- Ensure files are properly linked

## Contributing

When adding new documentation:
1. Follow existing patterns for document type
2. Use consistent terminology from vision
3. Include working code examples
4. Test locally before committing
5. Fix any test failures

---

*This testing framework ensures ADRI documentation remains high-quality, accurate, and aligned with project vision.*
