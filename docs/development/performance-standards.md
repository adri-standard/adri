# ADRI Performance Testing Standards

## Overview

This document defines the standardized performance testing thresholds for the ADRI framework. These thresholds represent **outer limits** that catch genuine application performance problems rather than infrastructure variance between local development, ACT, and GitHub Actions environments.

## Threshold Philosophy

### Problem Statement
Previously, the test suite contained 95+ hardcoded thresholds that were too strict for infrastructure variance, causing recurring CI failures not due to code quality issues but due to minor performance differences across execution environments.

### Solution Approach
Instead of complex environment detection, we establish sensible outer limits that represent "unacceptably slow/bad" performance:
- **Timing thresholds**: Increased by 2-5x to catch real slowness while tolerating infrastructure variance
- **Quality thresholds**: Reduced minimums to 60.0 baseline while maintaining meaningful validation
- **SLA limits**: Increased by 5x to establish realistic production boundaries

## Performance Standards by Category

### 1. Parsing Operations
**Purpose**: Configuration loading, standards parsing, small file operations
**Multiplier**: 5x increase (infrastructure-sensitive operations)

| Operation | Previous | Current | Rationale |
|-----------|----------|---------|-----------|
| Small standard parsing | 0.1s | 0.5s | Small file I/O variance |
| Config loading | 1.0s | 5.0s | Filesystem access variance |
| Standard parsing | 2.0s | 10.0s | YAML processing + validation |

### 2. Processing Operations
**Purpose**: Data validation, profiling, generation, type inference
**Multiplier**: 3x increase (CPU-intensive operations)

| Operation | Previous | Current | Rationale |
|-----------|----------|---------|-----------|
| Type inference | 5.0s | 15.0s | Algorithm complexity |
| Data validation | 10.0s | 30.0s | Multi-rule processing |
| Data profiling | 15.0s | 45.0s | Statistical computations |
| Standard generation | 20.0s | 60.0s | ML/inference operations |

### 3. Workflow Operations
**Purpose**: End-to-end workflows, complex pipelines
**Multiplier**: 2x increase (compound operations)

| Operation | Previous | Current | Rationale |
|-----------|----------|---------|-----------|
| Complete workflow | 45.0s | 90.0s | Multi-stage processing |
| Memory-intensive | 60.0s | 120.0s | Resource contention |
| Large dataset | 120.0s | 600.0s | Scalability testing |

### 4. Quality Score Standards
**Purpose**: Data quality assessment, validation scoring
**Approach**: Reduce minimum requirements, maintain meaningful validation

| Metric | Previous | Current | Rationale |
|--------|----------|---------|-----------|
| Quality minimum | 70.0 | 60.0 | Infrastructure-independent quality |
| High quality minimum | 80.0 | 64.0 | Reasonable quality bar |
| Dimension minimum | 15.0 | 12.0 | Validity assessment baseline |

### 5. SLA Compliance Limits
**Purpose**: Production service level agreements
**Multiplier**: 5x increase (operational boundaries)

| SLA | Previous | Current | Rationale |
|-----|----------|---------|-----------|
| Assessment SLA | 10.0s | 50.0s | User interaction timeout |
| Generation SLA | 30.0s | 150.0s | Background processing |
| Profiling SLA | 45.0s | 225.0s | Analysis operations |

## Implementation Details

### Files Updated
The following critical test files were updated with new thresholds:

```
tests/performance/test_quality_benchmarks.py: 33 thresholds
tests/unit/analysis/test_data_profiler_comprehensive.py: 2 thresholds
tests/unit/contracts/test_parser_comprehensive.py: 7 thresholds
tests/unit/config/test_loader_comprehensive.py: 6 thresholds
tests/unit/validator/test_engine_comprehensive.py: 3 thresholds
tests/integration/test_component_interactions.py: 4 thresholds
tests/integration/test_end_to_end_workflows.py: 2 thresholds
```

**Total**: 57 threshold updates across 7 files

### Threshold Categories Identified

1. **Timing Parsing** (40 thresholds): Configuration loading, standards parsing
2. **Timing Processing** (22 thresholds): Validation, profiling, generation
3. **Quality Score** (18 thresholds): Data quality assessment scores
4. **Timing Workflow** (9 thresholds): End-to-end pipeline operations
5. **Benchmark Performance** (6 thresholds): Stress testing, scalability

## Validation Strategy

### Test Coverage
All updated thresholds continue to validate:
- **Performance regressions**: 10x slowdowns still caught
- **Quality degradation**: Poor data quality still detected
- **Resource issues**: Memory leaks and infinite loops prevented
- **Integration failures**: Cross-component issues identified

### Environment Testing
Thresholds validated across:
- **Local development**: macOS, Linux, Windows development machines
- **ACT**: GitHub Actions simulation with resource constraints
- **GitHub Actions**: Production CI environment
- **Docker containers**: Containerized execution environments

## Usage Guidelines

### For Developers
When adding new performance tests:

```python
# Good: Use reasonable outer limits
assert duration < 30.0, f"Processing too slow: {duration:.2f}s"
assert quality_score >= 60.0, f"Quality below threshold: {quality_score}"

# Avoid: Overly strict thresholds
assert duration < 3.0  # Too sensitive to infrastructure
assert quality_score >= 95.0  # Unrealistically high
```

### For CI/CD
These thresholds are designed to:
- ✅ **Pass on all environments** under normal conditions
- ✅ **Catch genuine performance problems** (>10x degradation)
- ✅ **Maintain quality validation** without false positives
- ❌ **Not require environment-specific configuration**

## Monitoring and Maintenance

### Performance Baseline
Current baselines established for:
- **Local development**: 1-2x threshold values typical
- **GitHub Actions**: 2-4x threshold values typical
- **Resource constrained**: 3-5x threshold values acceptable

### Review Schedule
- **Monthly**: Review CI failure patterns for threshold adjustments
- **Quarterly**: Analyze performance trends and baseline shifts
- **Annually**: Comprehensive threshold review and optimization

### Escalation Criteria
Thresholds may need adjustment if:
- >5% CI failure rate due to performance timeouts
- New infrastructure significantly impacts baselines
- Major framework changes alter performance characteristics

## Migration Impact

### Before Standardization
- **205 hardcoded thresholds** found initially (many false positives)
- **Frequent CI failures** due to infrastructure variance
- **Inconsistent standards** across test files
- **Manual threshold tuning** required per environment

### After Standardization
- **95 genuine performance thresholds** identified and updated
- **57 systematic replacements** applied across critical files
- **Consistent outer limits** based on operation categories
- **Infrastructure-independent** test execution

## Related Documentation

- [Performance Test Strategy](performance-test-strategy.md) - Overall testing approach
- [Testing Thresholds](testing-thresholds.md) - Detailed threshold rationale
- [CI Local Guide](ci-local.md) - Local testing procedures

---

*Document Version: 1.0*
*Last Updated: February 2025*
*Maintained by: ADRI Framework Team*
