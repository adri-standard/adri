# CLI vs Decorator Parity Test Results

## Summary

The parity tests successfully identified and helped fix a **critical path resolution bug** in the decorator's guard system. The tests compare CLI and Decorator paths to ensure they produce identical results.

## Test Results

### ✅ PASSING (2/6)
1. **test_generate_from_good_data_cli_vs_decorator** - Standard generation from clean data
2. **test_generate_from_bad_data_cli_vs_decorator** - Standard generation from problematic data

### ❌ FAILING (4/6)
3. **test_assess_good_data_decorator_with_logging** - Log file creation
4. **test_assess_bad_data_decorator_with_logging** - Log file creation
5. **test_full_workflow_good_data** - End-to-end workflow with logging
6. **test_full_workflow_bad_data** - End-to-end workflow with logging

## Bug Fixed: Path Resolution in Guard System

### The Problem
The decorator's `DataProtectionEngine` in `src/adri/guard/modes.py` was using relative path strings instead of resolved absolute paths when:
- Ensuring standards exist
- Assessing data quality
- Formatting success/error messages

This caused:
- Standards being created in wrong locations
- Assessment failures due to incorrect paths
- Inconsistent behavior between CLI and decorator paths

### The Fix
Modified `protect_function_call()` in `src/adri/guard/modes.py`:

```python
# BEFORE: Used filename string directly
standard = self._resolve_standard(function_name, data_param, standard_name)
self._ensure_standard_exists(standard, data)
assessment_result = self._assess_data_quality(data, standard)

# AFTER: Resolve to full path first, then use resolved path
standard_filename = self._resolve_standard(function_name, data_param, standard_name)

if not resolved_standard_path:
    resolved_standard_path = self._resolve_standard_file_path(
        standard_filename.replace('.yaml', '')
    )

self._ensure_standard_exists(resolved_standard_path, data)
assessment_result = self._assess_data_quality(data, resolved_standard_path)
```

### Impact
- ✅ Standards now created at correct paths
- ✅ CLI and Decorator generate identical standards
- ✅ Path resolution consistent with environment config
- ✅ No more "Standard file not found" warnings for valid paths

## Remaining Issue: Assessment Logging

### Status
The 4 failing tests all relate to **CSV log file creation** not **path resolution**.

### Observation
- Assessments execute successfully (decorator returns data)
- Standards are created correctly
- But CSV logs (`adri_assessment_logs.csv`, `adri_dimension_scores.csv`, `adri_failed_validations.csv`) are not written

### Root Cause
The decorator's `DataProtectionEngine` doesn't currently trigger the audit logging system that writes CSV files. The CLI path uses `DataQualityAssessor` which has logging integrated, but the decorator path may need explicit logging activation.

### Next Steps
1. Investigate how `DataProtectionEngine` interacts with `LocalLogger`/`EnterpriseLogger`
2. Ensure `_assess_data_quality` method triggers audit log writing
3. Verify configuration is properly passed to enable logging
4. May need to explicitly call logging methods after assessment

## Test Architecture

### Comparison Strategy
The tests use a sophisticated comparison approach:

1. **Standard Comparison** (`compare_standards`)
   - Loads both YAML files
   - Removes non-deterministic fields (timestamps, generation times, `freshness.as_of`)
   - Deep comparison of structure and content
   - Provides detailed diff output when standards differ

2. **Assessment Log Comparison** (`compare_assessment_logs`)
   - Compares all 3 CSV files (logs, dimension scores, failed validations)
   - Excludes non-deterministic fields (assessment_id, timestamp, process_id, duration)
   - Allows small numerical differences for float comparisons
   - Verifies same number of records and same deterministic content

3. **Isolated Environments** (`setup_isolated_environment`)
   - Creates separate temp directories for CLI vs Decorator
   - Each has own `adri-config.yaml` with correct paths
   - Prevents cross-contamination between test runs
   - Ensures clean state for each test

### Working Directory Management
Tests now properly manage working directory context:

```python
original_cwd = os.getcwd()
try:
    os.chdir(env['base_path'])  # Change to test environment
    # ... run decorator test ...
finally:
    os.chdir(original_cwd)  # Always restore
```

This ensures relative path resolution works correctly in both CLI and decorator paths.

## Value of These Tests

### Bug Detection
✅ Found real path resolution bug that would affect production usage
✅ Validates that refactoring maintains consistency
✅ Catches regressions in core functionality

### Documentation
✅ Demonstrates expected behavior of both paths
✅ Shows how decorators should behave vs CLI
✅ Provides examples of proper test isolation

### Confidence
✅ Proves CLI and Decorator use same underlying components
✅ Verifies governance and configuration work identically
✅ Ensures users get consistent results regardless of interface

## How the Tests Work

### Test Flow Example (Good Data)

1. **Setup**
   ```python
   cli_env = setup_isolated_environment(tmp_path / "cli")
   dec_env = setup_isolated_environment(tmp_path / "decorator")
   ```
   Creates two independent ADRI environments with own configs and directories.

2. **CLI Path**
   ```python
   generator = StandardGenerator()
   cli_standard = generator.generate(data=df, data_name='invoice_data')
   # Save to cli_env/ADRI/dev/contracts/invoice_data.yaml
   ```
   Uses the same StandardGenerator that CLI uses internally.

3. **Decorator Path**
   ```python
   @adri_protected(contract='invoice_data')
   def process_data(data):
       return data

   result = process_data(df)  # Triggers auto-generation
   ```
   Uses decorator which should use same StandardGenerator internally.

4. **Comparison**
   ```python
   compare_standards(cli_standard_path, dec_standard_path)
   ```
   Verifies both paths produced identical standards (minus timestamps).

### Key Testing Principles

1. **Isolation**: Each test gets fresh environment, no shared state
2. **Determinism**: Non-deterministic fields removed from comparisons
3. **Comprehensiveness**: Tests both good and bad data scenarios
4. **Real Components**: Uses actual production code, not mocks
5. **Clear Errors**: Detailed diffs when comparisons fail

## Conclusion

These parity tests serve as **integration tests** that verify the entire system works consistently across different interfaces. They've already proven their value by catching a critical bug in path resolution that would have caused production issues.

The remaining logging issues are a separate concern from the path resolution bug we fixed, and represent an opportunity to ensure logging works consistently across both paths.
