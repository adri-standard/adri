# Plausibility Rules for ADRI

This document describes the plausibility dimension rules implemented for the ADRI system.

## Overview

Plausibility rules verify that data appears reasonable and likely to be correct. These rules focus on:

- Statistical outlier detection
- Distribution analysis
- Range validation
- Pattern frequency analysis

These rules help identify values that, while potentially valid according to basic data type and format constraints, are statistically unlikely or logically improbable.

## Implemented Rules

### OutlierDetectionRule

**Purpose**: Detects statistical outliers in numeric data.

**Key Parameters**:
- `column`: Column to analyze for outliers
- `method`: Method for outlier detection - 'zscore', 'iqr', or 'modified_zscore'
- `threshold`: Threshold for outlier detection (e.g., Z-score > 3.0)
- `multiplier`: Multiplier for IQR method (e.g., 1.5 * IQR)
- `exclude_outliers`: Whether to flag outliers as invalid data

**Example**:

```python
# Example configuration for OutlierDetectionRule
outlier_params = {
    "column": "temperature",
    "method": "zscore",
    "threshold": 3.0,
    "exclude_outliers": True
}
```

### ValueDistributionRule

**Purpose**: Evaluates if data follows expected statistical distributions.

**Key Parameters**:
- `column`: Column to analyze for distribution
- `distribution_type`: Expected distribution type - 'normal', 'uniform', 'poisson', 'exponential'
- `test_method`: Statistical test to use - 'ks' (Kolmogorov-Smirnov), 'chi2'
- `p_threshold`: P-value threshold for statistical significance
- `distribution_params`: Parameters for the expected distribution

**Example**:

```python
# Example configuration for ValueDistributionRule
distribution_params = {
    "column": "response_time",
    "distribution_type": "exponential",
    "test_method": "ks",
    "p_threshold": 0.05,
    "distribution_params": {"scale": 30}
}
```

### RangeCheckRule

**Purpose**: Validates if values fall within expected ranges.

**Key Parameters**:
- `column`: Column to check for range compliance
- `min_value`: Minimum allowed value (inclusive)
- `max_value`: Maximum allowed value (inclusive)
- `quantile_based`: Whether min/max values are interpreted as quantiles
- `use_log_scale`: Whether to use logarithmic scale for checks

**Example**:

```python
# Example configuration for RangeCheckRule
range_params = {
    "column": "age",
    "min_value": 0,
    "max_value": 120,
    "quantile_based": False
}
```

### PatternFrequencyRule

**Purpose**: Analyzes frequency distribution of categorical values.

**Key Parameters**:
- `column`: Column to analyze for pattern frequency
- `expected_frequencies`: Expected relative frequencies for specific values
- `max_categories`: Maximum number of unique categories expected
- `min_frequency`: Minimum relative frequency expected for any category
- `max_frequency`: Maximum relative frequency expected for any category
- `tolerance`: Tolerance for frequency deviation from expected

**Example**:

```python
# Example configuration for PatternFrequencyRule
pattern_params = {
    "column": "country",
    "max_categories": 200,
    "min_frequency": 0.001,
    "max_frequency": 0.3,
    "expected_frequencies": {
        "USA": 0.25,
        "Canada": 0.10,
        "UK": 0.12
    },
    "tolerance": 0.05
}
```

## Usage Examples

### Basic Usage

```python
from adri import DataSourceAssessor
from adri.connectors import FileConnector

# Create data source
data_source = FileConnector(filepath="data.csv")

# Create assessor with plausibility rule configuration
assessor = DataSourceAssessor(
    template_mode=True,
    template={
        "dimensions": {
            "plausibility": {
                "rules": [{
                    "type": "outlier_detection",
                    "params": {
                        "column": "temperature",
                        "method": "zscore",
                        "threshold": 3.0,
                        "weight": 20
                    }
                }]
            }
        }
    }
)

# Run assessment
report = assessor.assess(data_source)
```

### Common Plausibility Checks

1. **Detecting Extreme Values**:
   ```python
# Parameters for OutlierDetectionRule
extreme_value_params = {
    "column": "transaction_amount", 
    "method": "iqr",
    "multiplier": 1.5
}
   ```

2. **Validating Age Ranges**:
   ```python
# Parameters for RangeCheckRule
age_range_params = {
    "column": "age",
    "min_value": 0,
    "max_value": 120
}
   ```

3. **Verifying Expected Distributions**:
   ```python
# Parameters for ValueDistributionRule
wait_time_params = {
    "column": "wait_time",
    "distribution_type": "exponential",
    "test_method": "chi2"
}
   ```

4. **Analyzing Category Frequencies**:
   ```python
# Parameters for PatternFrequencyRule
status_frequency_params = {
    "column": "status_code",
    "max_categories": 10,
    "min_frequency": 0.01,
    "max_frequency": 0.5
}
   ```

## Full Example

See `examples/plausibility_assessment.py` for a complete example that demonstrates:

1. Creating synthetic data with plausibility issues
2. Configuring multiple plausibility rules
3. Running the assessment
4. Interpreting and displaying the results

## Best Practices

1. **Calibrate thresholds carefully**: What constitutes an "outlier" or "implausible" value depends heavily on your domain and use case.

2. **Consider combining multiple plausibility checks**: A value might pass one plausibility rule but fail others.

3. **Use domain knowledge**: When available, use domain-specific knowledge to parameterize rules appropriately.

4. **Contextual analysis**: Consider the relationship between fields when determining plausibility (e.g., salary might be implausibly high for entry-level positions but not executives).

5. **Statistical significance**: Remember that statistical tests like those used in ValueDistributionRule should be interpreted with caution, especially for smaller datasets.

## Purpose & Test Coverage

**Why this file exists**: Provides detailed documentation on plausibility rules that verify data appears reasonable and likely to be correct through statistical analysis and domain-specific checks.

**Key responsibilities**:
- Document plausibility rule implementations
- Explain statistical methods for outlier detection
- Provide usage examples for distribution validation
- Show range and pattern frequency checking
- Guide best practices for domain-specific plausibility

**Test coverage**: This document's examples, claims, and features should be verified by tests documented in [plausibility_rules_test_coverage.md](./test_coverage/plausibility_rules_test_coverage.md)
