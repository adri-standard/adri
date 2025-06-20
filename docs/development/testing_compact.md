# Compact Testing Guide for ADRI

## Problem
Running the full test suite with verbose output can exceed LLM context windows, making it difficult to debug and fix issues.

## Solution: Compact Test Runner

The `scripts/run_tests_compact.py` script provides a context-efficient way to run tests.

### Features

1. **Summarized Output**: Shows only counts and failure names
2. **Grouped Testing**: Run tests by category to limit output
3. **JSON Results**: Machine-readable output for tracking progress
4. **Selective Testing**: Target specific test files or groups

### Usage

```bash
# Run all tests with compact output
python scripts/run_tests_compact.py

# Run specific test groups
python scripts/run_tests_compact.py -g unit-core
python scripts/run_tests_compact.py -g unit-templates
python scripts/run_tests_compact.py -g unit-examples
python scripts/run_tests_compact.py -g integration
python scripts/run_tests_compact.py -g infrastructure

# Run specific test file
python scripts/run_tests_compact.py tests/unit/test_assessor.py

# Show more detail for failures (use sparingly)
python scripts/run_tests_compact.py --no-capture

# Run all groups sequentially
python scripts/run_tests_compact.py -g
```

### Output Management

Test results are saved to:
- `test_results/test_results_<timestamp>.json` - Machine-readable results
- `test_results/test_output_<timestamp>.txt` - Full pytest output (optional)

### Best Practices for LLM-Assisted Development

1. **Start with Group Testing**: Run one test group at a time
   ```bash
   python scripts/run_tests_compact.py -g unit-core
   ```

2. **Focus on Specific Failures**: Once you identify failing tests, run just those
   ```bash
   python scripts/run_tests_compact.py tests/unit/test_certification_guard.py
   ```

3. **Use JSON Results**: Parse the JSON output to track progress programmatically
   ```python
<!-- audience: ai-builders -->
   import json
   with open('test_results/test_results_latest.json') as f:
       results = json.load(f)
       print(f"Failed: {results['failed_count']}")
   ```

4. **Incremental Fixes**: Fix one test file at a time to avoid context overflow

5. **Clear Output Between Runs**: The script only shows the summary, keeping context usage low

### Example Workflow

```bash
# 1. Get overview
python scripts/run_tests_compact.py -g

# 2. Focus on a failing group
python scripts/run_tests_compact.py -g unit-core

# 3. Fix specific test
python scripts/run_tests_compact.py tests/unit/test_assessor.py

# 4. Verify fix
python scripts/run_tests_compact.py tests/unit/test_assessor.py

# 5. Re-run group to ensure no regressions
python scripts/run_tests_compact.py -g unit-core
```

### pytest.ini Configuration

The project includes a `pytest.ini` file that helps reduce output:

```ini
[pytest]
addopts = -q --tb=short --no-header
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

This configuration:
- `-q`: Quiet mode (less verbose)
- `--tb=short`: Shorter traceback format
- `--no-header`: Skip pytest header info

### Tips for Context Management

1. **Don't use `-v` or `--verbose`** unless absolutely necessary
2. **Avoid `--capture=no`** except for specific debugging
3. **Use test groups** to limit scope
4. **Clean up output** between test runs
5. **Focus on one issue at a time**

By following these practices, you can effectively work with the test suite without exceeding context limits.
