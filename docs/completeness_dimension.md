# Completeness Dimension

## Overview

The Completeness dimension of the Agent Data Readiness Index (ADRI) evaluates whether all expected data is present, and most importantly, whether this information is explicitly communicated to agents.

This document explains how completeness assessment works in ADRI, including scoring mechanisms, configuration options, and practical examples.

## How Completeness Assessment Works

Completeness assessment operates on two key principles:

1. **Explicit Metadata**: Rewarding datasets that explicitly communicate completeness information to agents
2. **Implicit Analysis**: Providing fallback assessment through automated analysis when explicit metadata isn't available

### Scoring Components

Completeness assessment produces a score from 0-20 points. In default mode, scores are based on the four components below. In template mode, the 20 points are distributed among weighted rules defined in the template.

#### Default Mode Components

| Component | Max Score | Description |
|-----------|-----------|-------------|
| Overall Completeness | 5 | The percentage of non-missing values across the dataset |
| Null Distinction | 5 | Whether missing values are explicitly distinguished from nulls |
| Explicit Metrics | 5 | Whether completeness metrics are explicitly available to agents |
| Section Awareness | 5 | Whether completeness is tracked at the section level |

#### Template Mode Scoring

When using templates, the Completeness dimension scoring works differently:

1. **Rule Weights**: Each rule has a weight parameter that determines its contribution to the dimension score
2. **20-Point Total**: All rule weights within the completeness dimension must sum to 20 points
3. **Flexible Distribution**: You can allocate more weight to critical fields

Example template configuration:
```yaml
dimensions:
  completeness:
    rules:
      - type: required_fields
        params:
          weight: 15  # 15 out of 20 points - critical
          required_columns: ["id", "name", "email"]
          threshold: 1.0
      - type: population_density
        params:
          weight: 5   # 5 out of 20 points
          threshold: 0.90
          check_columns: ["phone", "address"]
```

### Explicit vs. Implicit Assessment

#### Explicit Metadata Assessment

ADRI first checks for explicit completeness metadata through:

1. **Companion Files**: Looking for `.completeness.json` files with explicit completeness information
2. **Metadata Files**: Examining companion metadata files (e.g., `.meta.json`)
3. **Data Documentation**: Checking for explicit missing value markers

When explicit metadata is found, it awards full points for the relevant components.

#### Implicit (Automated) Assessment

When explicit metadata isn't available, ADRI performs automated analysis:

1. **Missing Value Detection**: Calculates basic missing value statistics
2. **Special Null Detection**: Identifies potential special null values (e.g., "-999", "N/A")
3. **Section Inference**: Attempts to group related fields into logical sections
4. **Required Field Detection**: Identifies which fields appear to be required vs. optional

The implicit assessment can award partial points (typically 50-70% of maximum) for each component when it can detect completeness patterns automatically, but this behavior is configurable.

## Companion File Requirements

ADRI looks for specific companion files alongside the main data file to find explicit completeness metadata:

| File Type | Naming Convention | Purpose |
|-----------|-------------------|---------|
| Completeness Info | `{filename}.completeness.json` | Contains explicit completeness metrics |
| Metadata | `{filename}.meta.json` | May contain missing value markers and completeness info |
| Data Dictionary | `{filename}_dictionary.csv` | May provide info about required vs. optional fields |

### Example Completeness File

```json
{
  "overall_completeness_percent": 98.5,
  "missing_value_markers": ["N/A", "-999", "NULL"],
  "completeness_metrics": {
    "by_column": {
      "customer_id": 100.0,
      "email": 87.2,
      "phone": 62.4
    },
    "required_fields": ["customer_id", "name", "email"],
    "optional_fields": ["phone", "address", "notes"]
  },
  "section_completeness": {
    "contact_info": {
      "fields": ["email", "phone", "address"],
      "completeness_percent": 83.7
    },
    "demographics": {
      "fields": ["age", "gender", "income"],
      "completeness_percent": 76.2
    }
  }
}
```

## Implicit Detection Methods

When explicit metadata is not available, ADRI applies these implicit detection methods:

### Special Null Detection

```python
# Examples of common null indicators in string columns
null_strings = ["n/a", "na", "none", "null", "missing", "unknown", "-", ""]

# Examples of sentinel values in numeric columns
sentinel_values = [-999, -9999, -1, 9999, 999]
```

### Section Inference

ADRI attempts to identify logical sections in data through:

1. **Name Prefixes**: Grouping columns that share common prefixes (e.g., "address_line1", "address_city")
2. **Co-occurrence**: Identifying groups of columns that tend to be null together
3. **Semantic Grouping**: Using column names to infer related fields

### Data Density Analysis

Measuring the overall information density of the dataset:

```python
# Typical calculation
density = (total_cells - null_cells - blank_strings) / total_cells * 100
```

## Configuration Options

ADRI's completeness assessment behavior can be configured through several options:

### Global Scoring Weights

You can adjust the maximum score for each component by modifying `COMPLETENESS_SCORING` in the configuration:

```python
COMPLETENESS_SCORING = {
    "MAX_OVERALL_COMPLETENESS_SCORE": 5,
    "MAX_NULL_DISTINCTION_SCORE": 5,
    "MAX_EXPLICIT_METRICS_SCORE": 5,
    "MAX_SECTION_AWARENESS_SCORE": 5
}
```

### Requiring Explicit Metadata

Setting `REQUIRE_EXPLICIT_METADATA` to `True` enforces a strict requirement for explicit metadata:

```python
COMPLETENESS_SCORING = {
    # ...other settings...
    "REQUIRE_EXPLICIT_METADATA": True
}
```

When enabled:
- Only explicit metadata will receive full points
- Implicit assessment will receive minimal or zero points
- This encourages data providers to create proper metadata

### Configuration Methods

You can configure these settings through:

1. **YAML Configuration**:
   ```yaml
   completeness_scoring:
     MAX_OVERALL_COMPLETENESS_SCORE: 5
     REQUIRE_EXPLICIT_METADATA: true
   ```

2. **Environment Variables**:
   ```bash
   export ADRI_REQUIRE_EXPLICIT_METADATA=true
   ```

3. **Python API**:
   ```python
   from adri.config.config import Configuration, set_config
   
   config = Configuration({
       "completeness_scoring": {
           "REQUIRE_EXPLICIT_METADATA": True
       }
   })
   set_config(config)
   ```

## Practical Examples

### Example 1: Dataset With Explicit Metadata

A CSV file `customers.csv` with an accompanying `customers.completeness.json` file will receive:
- Full points for null distinction if missing value markers are defined
- Full points for explicit metrics if completeness percentages are provided
- Full points for section awareness if data sections are defined
- Points for overall completeness based on the actual completeness percentage

### Example 2: Clean Dataset Without Metadata

A CSV file with high completeness but no accompanying metadata:
- When `REQUIRE_EXPLICIT_METADATA=False`: Will receive points for overall completeness plus partial points for components that can be inferred
- When `REQUIRE_EXPLICIT_METADATA=True`: Will receive points only for overall completeness

### Example 3: Dataset With Special Null Values

A CSV file using special values like "N/A" or -999 to represent missing data:
- When `REQUIRE_EXPLICIT_METADATA=False`: Will receive partial points for null distinction if these patterns are detected
- When `REQUIRE_EXPLICIT_METADATA=True`: Will receive minimal points despite the patterns

## Common Warnings and Findings

ADRI will produce findings for common completeness issues:

- "Data is moderately complete (>80%)"
- "Special null indicators detected through analysis"
- "No explicit distinction between missing values and nulls"
- "Basic completeness metrics calculated through analysis"
- "No section-level completeness information"
- "Detected potential data sections through analysis"

## Best Practices

To achieve a high Completeness score:

1. **Provide Explicit Metadata**: Create a `.completeness.json` companion file
2. **Define Missing Value Markers**: Explicitly list all values that represent missing data
3. **Distinguish Null Types**: Differentiate between "missing" (never collected) and "null" (collected but empty)
4. **Identify Required Fields**: Clearly mark which fields are required vs. optional
5. **Define Data Sections**: Group related fields into logical sections with completeness metrics for each
6. **Document Thresholds**: Define minimum required completeness thresholds for critical fields

## Common Recommendations

Based on assessment findings, ADRI typically recommends:

1. "Implement explicit markers for missing vs. null values"
2. "Provide explicit completeness metrics accessible to agents"
3. "Implement section-level completeness tracking"
4. "Improve data completeness to at least 90%"
5. "Implement a comprehensive completeness framework with explicit agent communication"

## Purpose & Test Coverage

**Why this file exists**: Provides comprehensive documentation on the Completeness dimension, which evaluates whether all expected data is present and whether this information is explicitly communicated to agents.

**Key responsibilities**:
- Explain how completeness assessment works in ADRI
- Detail scoring components for data completeness evaluation
- Document explicit vs. implicit metadata detection
- Provide practical examples and configuration options
- Guide best practices for achieving high completeness scores

**Test coverage**: This document's examples, claims, and features should be verified by tests documented in [completeness_dimension_test_coverage.md](./test_coverage/completeness_dimension_test_coverage.md)
