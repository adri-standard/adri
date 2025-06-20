# Context-Efficient Testing Guide

When working with AI assistants that have context window limitations, running comprehensive test suites can cause issues due to excessive output. This guide explains how to run tests efficiently while maintaining visibility into failures.

## The Problem

Running full test suites with verbose output can generate thousands of lines, quickly exceeding context windows and causing:
- AI assistant errors
- Loss of conversation context
- Inability to analyze test results

## The Solution

We've created specialized test runners that provide compact, actionable summaries without overwhelming the context window.

### 1. Summary Test Runner (`scripts/run_tests_summary.py`)

The most advanced solution, providing:
- Progress tracking without storing all output
- Grouped failure analysis
- Common issue identification
- Actionable fix suggestions

#### Usage:

```bash
# Run all tests with summary
python scripts/run_tests_summary.py

# Run specific test directory
python scripts/run_tests_summary.py tests/integration

# Limit detailed failures shown
python scripts/run_tests_summary.py --max-failures 5
```

#### Features:
- **Progress Indicators**: Shows dots for progress without verbose output
- **Failure Grouping**: Groups failures by module for easier analysis
- **Pattern Recognition**: Identifies common failure types
- **Fix Suggestions**: Provides actionable next steps

#### Example Output:
```
Running tests with context-efficient summary...
------------------------------------------------------------
.................................................. [50]
.................................................. [100]

============================================================
TEST EXECUTION SUMMARY
============================================================
Total Tests: 150
Passed:  125
Failed:  23
Skipped: 2
Duration: 45.32s

============================================================
FAILURES BY MODULE
============================================================

tests/integration/scenarios/test_banking.py: 3 failures
  - test_mixed_transaction_formats
    → Mixed formats should reduce validity score
  - test_transaction_validation_rules
    → Validation failures should significantly reduce score
  ... and 1 more

tests/integration/test_cli.py: 5 failures
  - test_cli_with_custom_config
    → Config file 'test_config.yaml' not found
  ... and 4 more

============================================================
RECOMMENDED ACTIONS
============================================================

Score Assertion Failures: 12 occurrences
  → Review scoring logic and thresholds

File/Resource Not Found: 8 occurrences
  → Verify file paths and test data

AttributeError: 3 occurrences
  → Check object attributes and API changes
```

### 2. Compact Test Runner (`scripts/run_tests_compact.py`)

A simpler solution that:
- Captures only failure names
- Provides basic counts
- Minimal output

#### Usage:
```bash
python scripts/run_tests_compact.py tests/unit
```

### 3. Manual Test Running Strategies

When debugging specific failures:

#### Run Single Test
```bash
pytest tests/unit/test_assessor.py::TestAssessor::test_specific_method -xvs
```

#### Run with Minimal Output
```bash
pytest tests/ -q --tb=no
```

#### Save Results to File
```bash
pytest tests/ > test_results.txt 2>&1
# Then analyze the file separately
```

## Best Practices for Context-Efficient Testing

### 1. Test in Stages
Instead of running all tests at once:
```bash
# Stage 1: Unit tests
python scripts/run_tests_summary.py tests/unit

# Stage 2: Integration tests
python scripts/run_tests_summary.py tests/integration

# Stage 3: Specific problem areas
python scripts/run_tests_summary.py tests/integration/scenarios
```

### 2. Focus on Failures
Use pytest's last-failed feature:
```bash
# Run only previously failed tests
pytest --lf

# Run failed tests first
pytest --ff
```

### 3. Use Test Markers
Group related tests:
```python
<!-- audience: ai-builders -->
@pytest.mark.slow
def test_heavy_computation():
    pass
```

```bash
# Run excluding slow tests
pytest -m "not slow"
```

### 4. Create Test Categories
Organize tests by priority:
```bash
# Critical path tests
pytest tests/unit/core tests/integration/critical

# All non-critical tests
pytest tests/ -k "not critical"
```

## Troubleshooting

### JSON Report Issues
If pytest-json-report is not installed:
```bash
pip install pytest-json-report
```

### Progress Not Showing
Ensure stdout is not being captured:
```bash
pytest -s  # Disable output capturing
```

### Still Too Much Output
Use the `--max-failures` option:
```bash
python scripts/run_tests_summary.py --max-failures 3
```

## Integration with AI Assistants

When working with AI assistants:

1. **Start with Summary**: Always use the summary runner first
2. **Drill Down**: Only request verbose output for specific failures
3. **Batch Fixes**: Group similar failures and fix in batches
4. **Verify Incrementally**: Test fixes in small groups

Example workflow:
```bash
# 1. Get overview
python scripts/run_tests_summary.py

# 2. Fix a specific module
# Make changes...

# 3. Test just that module
pytest tests/integration/scenarios/test_banking.py -v

# 4. Verify overall progress
python scripts/run_tests_summary.py
```

## Summary

Context-efficient testing is essential when working with AI assistants. By using specialized test runners and following best practices, you can:
- Maintain full visibility into test failures
- Avoid context window overflow
- Get actionable insights for fixing issues
- Work more efficiently with AI assistance

Remember: The goal is to get the information you need without overwhelming the context window.
