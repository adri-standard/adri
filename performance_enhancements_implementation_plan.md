# Implementation Plan

## Overview
Enhance the GitHub Actions performance testing infrastructure with timeout protection, benchmark comparison capabilities, and standardized performance thresholds.

This implementation addresses three critical enhancements to the existing performance testing setup in the ADRI Validator project. The project currently has two performance workflows (test.yml and performance.yml), with performance.yml being more comprehensive but lacking integration with the main CI pipeline. These enhancements will ensure performance tests complete within reasonable time limits, enable tracking of performance regressions across commits, and establish clear performance standards that must be met for builds to pass. The implementation will unify performance testing approaches across workflows while maintaining backward compatibility.

## Types
Define configuration types and data structures for performance benchmarking and comparison.

The following type definitions will be used throughout the implementation:

```typescript
interface BenchmarkConfig {
  timeout_seconds: number;           // Maximum time allowed for each benchmark test
  comparison_enabled: boolean;       // Enable benchmark comparison with previous results
  thresholds: PerformanceThresholds; // Performance regression thresholds
  artifacts_retention_days: number;  // How long to keep benchmark artifacts
}

interface PerformanceThresholds {
  decorator_overhead_percent: number;     // Max allowed decorator overhead (default: 10)
  max_protected_time_ms: number;          // Max execution time for protected functions (default: 100)
  cli_max_time_10k_rows_ms: number;       // Max CLI execution time for 10K rows (default: 5000)
  memory_per_row_kb: number;              // Max memory usage per row (default: 1.0)
  regression_tolerance_percent: number;    // Allowed performance regression (default: 10)
}

interface BenchmarkResult {
  timestamp: string;
  commit_sha: string;
  branch: string;
  test_name: string;
  execution_time_ms: number;
  memory_usage_mb?: number;
  data_size?: number;
  passed_thresholds: boolean;
}

interface ComparisonReport {
  current: BenchmarkResult[];
  previous?: BenchmarkResult[];
  regressions: RegressionItem[];
  improvements: ImprovementItem[];
  summary: ComparisonSummary;
}

interface RegressionItem {
  test_name: string;
  current_time_ms: number;
  previous_time_ms: number;
  regression_percent: number;
  exceeds_threshold: boolean;
}
```

## Files
Modify existing workflow files and create new supporting scripts for benchmark comparison.

### Modified Files:
1. **.github/workflows/test.yml**
   - Add timeout configuration to performance job
   - Integrate benchmark comparison logic
   - Add performance threshold checks
   - Store benchmark results for comparison

2. **.github/workflows/performance.yml**
   - Add pytest-timeout to dependencies
   - Enhance benchmark comparison with previous runs
   - Standardize threshold configuration
   - Improve artifact management

3. **pyproject.toml**
   - Ensure pytest-timeout is in test dependencies
   - Add benchmark comparison tools to optional dependencies

### New Files:
1. **scripts/compare_benchmarks.py**
   - Script to compare current benchmark results with previous runs
   - Generate regression reports
   - Output GitHub Step Summary formatted results

2. **.github/benchmark-thresholds.yml**
   - Centralized configuration for performance thresholds
   - Shared across all workflows
   - Version controlled and reviewable

3. **scripts/download_previous_benchmark.py**
   - Download previous benchmark artifacts from GitHub
   - Handle branch comparisons (main vs feature branches)
   - Cache management for local development

## Functions
Create new functions and modify existing ones to support performance enhancements.

### New Functions:

1. **scripts/compare_benchmarks.py::load_benchmark_results(file_path: str) -> dict**
   - File path: scripts/compare_benchmarks.py
   - Load and parse benchmark JSON results
   - Handle different benchmark formats (pytest-benchmark, custom)
   - Validate result structure

2. **scripts/compare_benchmarks.py::compare_results(current: dict, previous: dict, thresholds: dict) -> ComparisonReport**
   - File path: scripts/compare_benchmarks.py
   - Compare current and previous benchmark results
   - Calculate regression percentages
   - Apply threshold checks

3. **scripts/compare_benchmarks.py::generate_github_summary(report: ComparisonReport) -> str**
   - File path: scripts/compare_benchmarks.py
   - Generate markdown formatted summary for GitHub
   - Include tables, charts, and status indicators
   - Highlight regressions and improvements

4. **scripts/download_previous_benchmark.py::fetch_artifact(run_id: str, token: str) -> bytes**
   - File path: scripts/download_previous_benchmark.py
   - Download benchmark artifact from GitHub API
   - Handle authentication and rate limiting
   - Implement retry logic

### Modified Functions:

1. **tests/test_benchmarks.py::test_benchmark_* (all benchmark tests)**
   - Current file path: tests/test_benchmarks.py
   - Add @pytest.mark.timeout(60) decorators to all benchmark tests
   - Ensure consistent result format for comparison
   - Add memory profiling where missing

## Classes
No new classes required; modifications to existing test classes only.

### Modified Classes:

1. **tests/test_benchmarks.py::TestPerformanceBenchmarks**
   - File path: tests/test_benchmarks.py
   - Add class-level timeout configuration
   - Implement setup for benchmark comparison baseline
   - Add teardown to save results in consistent format

## Dependencies
Add new Python packages and update existing ones for benchmark comparison and timeout support.

### New Dependencies:
1. **pytest-timeout>=2.2.0**
   - Already added to pyproject.toml but needs verification
   - Required for timeout protection
   - Add to all workflow files

2. **tabulate>=0.9.0**
   - For generating formatted comparison tables
   - Used in GitHub summary generation
   - Add to optional dev dependencies

3. **pyyaml>=6.0** (already present)
   - For reading threshold configuration files
   - Verify version compatibility

### GitHub Actions:
1. **actions/download-artifact@v4**
   - For downloading previous benchmark results
   - Already in use, verify configuration

2. **actions/github-script@v7**
   - For GitHub API interactions
   - Add for fetching previous workflow runs

## Testing
Comprehensive testing strategy for performance enhancements.

### Test Files to Create:
1. **tests/test_benchmark_timeout.py**
   - Test that benchmarks respect timeout settings
   - Verify timeout enforcement doesn't affect results
   - Test graceful handling of timeout exceptions

2. **tests/test_benchmark_comparison.py**
   - Test comparison logic with various scenarios
   - Test regression detection accuracy
   - Test threshold application

### Modified Test Files:
1. **tests/test_benchmarks.py**
   - Add timeout markers to all tests
   - Ensure consistent result output format
   - Add tests for threshold validation

### Validation Strategy:
1. Run benchmarks with artificially low timeouts to verify enforcement
2. Create synthetic benchmark results to test comparison logic
3. Test with various threshold configurations
4. Validate GitHub summary generation output

## Implementation Order
Step-by-step implementation sequence to minimize disruption and ensure smooth integration.

1. **Add timeout protection to tests (Step 1)**
   - Update pyproject.toml to confirm pytest-timeout dependency
   - Add timeout decorators to tests/test_benchmarks.py
   - Update test.yml workflow to pass --timeout flag
   - Test locally with various timeout values

2. **Create threshold configuration file (Step 2)**
   - Create .github/benchmark-thresholds.yml with default values
   - Add configuration loading logic to workflows
   - Test threshold validation in performance.yml first

3. **Implement benchmark comparison scripts (Step 3)**
   - Create scripts/compare_benchmarks.py with core logic
   - Create scripts/download_previous_benchmark.py for artifact retrieval
   - Add unit tests for comparison functions
   - Test locally with sample data

4. **Update performance.yml workflow (Step 4)**
   - Add benchmark comparison job
   - Integrate threshold checks with existing regression checks
   - Add artifact download and comparison steps
   - Test in feature branch with PR

5. **Update test.yml workflow (Step 5)**
   - Add timeout configuration to performance job
   - Add benchmark comparison step
   - Integrate threshold checks
   - Ensure consistency with performance.yml

6. **Create comparison visualization (Step 6)**
   - Enhance GitHub summary generation
   - Add trend charts if possible
   - Create detailed regression reports
   - Test with various data scenarios

7. **Add comparison tests (Step 7)**
   - Create tests/test_benchmark_timeout.py
   - Create tests/test_benchmark_comparison.py
   - Run full test suite to ensure no regressions

8. **Documentation and rollout (Step 8)**
   - Update README with performance testing information
   - Document threshold configuration
   - Create PR with all changes
   - Monitor initial runs for issues

9. **Fine-tune thresholds (Step 9)**
   - Collect baseline data from main branch
   - Adjust thresholds based on actual performance
   - Update configuration file
   - Document threshold rationale

10. **Enable enforcement (Step 10)**
    - Make threshold checks required for merge
    - Enable comparison for all PRs
    - Set up notifications for performance regressions
    - Monitor and iterate based on feedback
