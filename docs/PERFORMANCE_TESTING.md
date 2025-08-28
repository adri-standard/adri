# Performance Testing Guide

## Overview

The ADRI Validator includes comprehensive performance testing infrastructure to ensure optimal performance and detect regressions. This guide covers the performance testing features, configuration, and best practices.

## Features

### 1. Timeout Protection

All performance benchmarks have timeout protection to prevent hanging tests from blocking CI/CD pipelines.

- **Default Timeout**: 60 seconds per test
- **Configuration**: Set in `.github/benchmark-thresholds.yml`
- **Implementation**: Uses `pytest-timeout` with thread-based termination

### 2. Benchmark Comparison

Automatic comparison of benchmark results between commits to detect performance regressions.

- **Automatic PR Comparisons**: Compare feature branch against base branch
- **Historical Tracking**: Store and compare results across multiple runs
- **Regression Detection**: Flag tests that exceed regression tolerance thresholds

### 3. Performance Thresholds

Configurable thresholds for various performance metrics:

- **Decorator Overhead**: Maximum 10% overhead for `@adri_protected`
- **Protected Function Execution**: Maximum 100ms execution time
- **CLI Performance**: Maximum 5 seconds for 10K rows
- **Memory Usage**: Maximum 1KB per row

## Configuration

### Threshold Configuration File

Performance thresholds are configured in `.github/benchmark-thresholds.yml`:

```yaml
# Performance thresholds
thresholds:
  decorator_overhead_percent: 10
  max_protected_time_ms: 100
  cli_max_time_10k_rows_ms: 5000
  memory_per_row_kb: 1.0
  regression_tolerance_percent: 10

# Test-specific thresholds
test_thresholds:
  test_benchmark_data_loading:
    max_time_ms: 2000
    regression_tolerance_percent: 15

# Enforcement settings (initially disabled)
enforcement:
  fail_on_regression: false
  fail_on_threshold_breach: false
```

### Workflow Configuration

Performance tests run in two workflows:

1. **test.yml**: Basic performance checks on PRs and main branch
2. **performance.yml**: Comprehensive performance benchmarks with detailed analysis

## Running Performance Tests

### Local Testing

Run performance benchmarks locally:

```bash
# Run all benchmarks
pytest tests/test_benchmarks.py --benchmark-only

# Run with timeout protection
pytest tests/test_benchmarks.py --benchmark-only --timeout=60

# Generate JSON report
pytest tests/test_benchmarks.py --benchmark-only --benchmark-json=benchmark.json

# Compare with previous results
python scripts/compare_benchmarks.py benchmark.json --previous previous.json --thresholds .github/benchmark-thresholds.yml
```

### CI/CD Pipeline

Performance tests run automatically on:
- Pull requests to main branch
- Pushes to main branch
- Weekly scheduled runs (Sundays at 3 AM UTC)

## Benchmark Comparison

### How It Works

1. **Baseline Collection**: Benchmarks from main branch are stored as artifacts
2. **PR Comparison**: Feature branch benchmarks are compared against baseline
3. **Report Generation**: Detailed comparison report with tables and metrics
4. **GitHub Comments**: Automatic PR comments with performance summary

### Comparison Metrics

- **Regression Detection**: Tests slower by more than tolerance threshold
- **Improvement Detection**: Tests faster by more than 5%
- **New Test Detection**: Tests added in current branch
- **Missing Test Detection**: Tests removed from current branch

### Sample Comparison Report

```markdown
## 📊 Benchmark Comparison Report

### Summary
| Metric | Count |
|--------|-------|
| Total Tests | 8 |
| Regressions | 1 |
| Improvements | 2 |
| Threshold Breaches | 0 |

### ❌ Performance Regressions
| Test | Previous (ms) | Current (ms) | Change | Tolerance |
|------|--------------|--------------|---------|-----------|
| test_benchmark_data_loading | 450.00 | 520.00 | +15.6% | 10% |

### 🎉 Performance Improvements
| Test | Previous (ms) | Current (ms) | Improvement |
|------|--------------|--------------|-------------|
| test_benchmark_assessment_simple | 1000.00 | 850.00 | -15.0% |
```

## Scripts

### compare_benchmarks.py

Compare benchmark results and check thresholds:

```bash
python scripts/compare_benchmarks.py <current.json> \
  --previous <previous.json> \
  --thresholds .github/benchmark-thresholds.yml \
  --output report.md \
  --enforce
```

Options:
- `--previous`: Previous benchmark results for comparison
- `--thresholds`: Path to threshold configuration file
- `--output`: Output file for comparison report
- `--enforce`: Exit with error if thresholds are violated
- `--github-output`: Write to GitHub step summary

### download_previous_benchmark.py

Download previous benchmark artifacts from GitHub Actions:

```bash
python scripts/download_previous_benchmark.py \
  --repo owner/name \
  --branch main \
  --workflow test.yml \
  --artifact benchmark-results \
  --output previous.json
```

Options:
- `--repo`: Repository in format owner/name
- `--branch`: Branch to fetch from
- `--workflow`: Workflow file name
- `--artifact`: Artifact name
- `--token`: GitHub token (or set GITHUB_TOKEN env var)

## Best Practices

### 1. Setting Thresholds

- **Start Conservative**: Begin with loose thresholds and tighten gradually
- **Collect Baseline**: Run benchmarks multiple times to establish baseline
- **Consider Variability**: Account for normal performance variation
- **Document Changes**: Document threshold changes in commit messages

### 2. Writing Benchmarks

```python
@pytest.mark.performance
@pytest.mark.timeout(60)
def test_benchmark_example(benchmark):
    """Example benchmark test."""
    def function_to_test():
        # Your code here
        return result

    result = benchmark(function_to_test)
    assert result is not None
```

### 3. Handling Regressions

When a performance regression is detected:

1. **Review the Report**: Check the comparison report for details
2. **Identify the Cause**: Look for recent changes affecting performance
3. **Profile the Code**: Use profiling tools to identify bottlenecks
4. **Optimize or Accept**: Either fix the regression or adjust thresholds

### 4. Gradual Enforcement

Follow this rollout strategy:

1. **Phase 1**: Deploy with enforcement disabled
2. **Phase 2**: Collect baseline data (1-2 weeks)
3. **Phase 3**: Tune thresholds based on data
4. **Phase 4**: Enable warnings but not failures
5. **Phase 5**: Enable full enforcement

## Troubleshooting

### Common Issues

#### Timeout Errors
```
FAILED tests/test_benchmarks.py::test_example - Failed: Timeout >60.0s
```
**Solution**: Increase timeout in test marker or optimize the test

#### Missing Previous Benchmark
```
Warning: Previous results not found at previous-benchmark.json
```
**Solution**: This is normal for first run or new branches

#### Threshold Violations
```
❌ Threshold violations detected:
  - test_benchmark_data_loading: 2500ms exceeds threshold 2000ms
```
**Solution**: Either optimize the code or adjust the threshold

### Debug Commands

```bash
# Run with verbose output
pytest tests/test_benchmarks.py -vv --benchmark-only

# Check timeout configuration
python -c "import yaml; print(yaml.safe_load(open('.github/benchmark-thresholds.yml')))"

# Test comparison locally
python scripts/compare_benchmarks.py --help
```

## Integration with Other Tools

### pytest-benchmark

The performance tests use pytest-benchmark for accurate measurements:

```bash
# Install
pip install pytest-benchmark

# Run with options
pytest --benchmark-only \
       --benchmark-autosave \
       --benchmark-save-data \
       --benchmark-max-time=5
```

### Memory Profiling

Memory usage is tracked using psutil:

```python
import psutil

process = psutil.Process()
memory_mb = process.memory_info().rss / 1024 / 1024
```

## Future Enhancements

Planned improvements to the performance testing infrastructure:

1. **Trend Analysis**: Track performance trends over time
2. **Automated Bisection**: Automatically find commits that introduced regressions
3. **Performance Dashboard**: Web dashboard for viewing historical data
4. **Custom Metrics**: Support for application-specific performance metrics
5. **Cloud Benchmarking**: Run benchmarks on standardized cloud infrastructure

## Contributing

To contribute to performance testing:

1. Add benchmarks for new features in `tests/test_benchmarks.py`
2. Update thresholds in `.github/benchmark-thresholds.yml` as needed
3. Document performance characteristics in docstrings
4. Include performance impact in PR descriptions

## References

- [pytest-benchmark documentation](https://pytest-benchmark.readthedocs.io/)
- [pytest-timeout documentation](https://pypi.org/project/pytest-timeout/)
- [GitHub Actions artifacts](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)
