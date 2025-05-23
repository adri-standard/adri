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
OutlierDetectionRule(params={
    "column": "temperature",
    "method": "zscore",
    "threshold": 3.0,
    "exclude_outliers": True
})
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
ValueDistributionRule(params={
    "column": "response_time",
    "distribution_type": "exponential",
    "test_method": "ks",
    "p_threshold": 0.05,
    "distribution_params": {"scale": 30}
})
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
RangeCheckRule(params={
    "column": "age",
    "min_value": 0,
    "max_value": 120,
    "quantile_based": False
})
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
PatternFrequencyRule(params={
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
})
```

## Usage Examples

### Basic Usage

```python
from adri import ADRIAssessor
from adri.datasource import CSVDataSource
from adri.rules.plausibility import OutlierDetectionRule, ValueDistributionRule
from adri.rules.registry import RuleRegistry

# Create data source
data_source = CSVDataSource("data.csv")

# Create and register rules
registry = RuleRegistry()
registry.register(OutlierDetectionRule(params={
    "column": "temperature",
    "method": "zscore",
    "threshold": 3.0
}))

# Create assessor and run assessment
assessor = ADRIAssessor(registry=registry)
report = assessor.assess(data_source)
```

### Common Plausibility Checks

1. **Detecting Extreme Values**:
   ```python
   OutlierDetectionRule(params={
       "column": "transaction_amount", 
       "method": "iqr",
       "multiplier": 1.5
   })
   ```

2. **Validating Age Ranges**:
   ```python
   RangeCheckRule(params={
       "column": "age",
       "min_value": 0,
       "max_value": 120
   })
   ```

3. **Verifying Expected Distributions**:
   ```python
   ValueDistributionRule(params={
       "column": "wait_time",
       "distribution_type": "exponential",
       "test_method": "chi2"
   })
   ```

4. **Analyzing Category Frequencies**:
   ```python
   PatternFrequencyRule(params={
       "column": "status_code",
       "max_categories": 10,
       "min_frequency": 0.01,
       "max_frequency": 0.5
   })
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
