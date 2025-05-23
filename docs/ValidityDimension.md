# Validity Dimension

## Overview

The Validity dimension of the Agent Data Readiness Index (ADRI) evaluates whether data adheres to required types, formats, and ranges, and most importantly, whether this information is explicitly communicated to agents.

This document provides a detailed explanation of how validity assessment works in ADRI, including scoring mechanisms, configuration options, and practical examples.

## How Validity Assessment Works

The validity assessment operates on two key principles:

1. **Explicit Metadata**: Rewarding datasets that explicitly communicate validity requirements to agents
2. **Implicit Analysis**: Providing fallback assessment through automated analysis when explicit metadata isn't available

### Scoring Components

Validity assessment produces a score from 0-20 points across five components:

| Component | Max Score | Description |
|-----------|-----------|-------------|
| Types Defined | 5 | Whether data types are explicitly defined for all fields |
| Formats Defined | 3 | Whether format patterns (e.g., date formats, ID patterns) are defined for applicable fields |
| Ranges Defined | 3 | Whether valid value ranges are defined for applicable fields |
| Validation Performed | 3 | Whether validation is performed on the data source |
| Validation Communicated | 6 | Whether validation results are explicitly communicated to agents |

### Explicit vs. Implicit Assessment

#### Explicit Metadata Assessment

ADRI first checks for explicit validity metadata through:

1. **Schema Definitions**: Looking for explicit type, format, and range definitions in schemas
2. **Validation Files**: Checking for companion validation files (e.g., `.validation.json`)
3. **Metadata Files**: Examining companion metadata files (e.g., `.meta.json`)

When explicit metadata is found, it awards full points for the relevant components.

#### Implicit (Automated) Assessment

When explicit metadata isn't available, ADRI performs automated analysis:

1. **Type Inference**: Analyzes data patterns to detect field types
2. **Consistency Checking**: Identifies values that don't match the inferred types
3. **Format Validation**: Detects invalid date formats, inconsistent ID patterns, etc.
4. **Range Analysis**: Identifies out-of-range values (e.g., negative values in positive fields)
5. **Statistical Analysis**: Detects outliers and anomalies

The implicit assessment can award partial points (up to 90% of maximum) for each component when data is consistently formatted, but this behavior is configurable.

## Companion File Requirements

ADRI looks for specific companion files alongside the main data file to find explicit validity metadata:

| File Type | Naming Convention | Purpose |
|-----------|-------------------|---------|
| Validation Rules | `{filename}.validation.json` | Contains explicit validation rules |
| Metadata | `{filename}.meta.json` | Contains format and range definitions |
| Data Dictionary | `{filename}_dictionary.csv` | Provides field descriptions and valid values |

### Example Validation File

```json
{
  "rules": [
    {
      "name": "Customer ID Format",
      "field": "customer_id",
      "condition": {
        "pattern": "^[A-Z]{2}\\d{4}$"
      }
    },
    {
      "name": "Price Range",
      "field": "price",
      "condition": {
        "min_value": 0,
        "max_value": 10000
      }
    },
    {
      "name": "Valid Payment Methods",
      "field": "payment_method",
      "condition": {
        "allowed_values": ["Credit Card", "PayPal", "Bank Transfer", "Cash"]
      }
    }
  ]
}
```

## Configuration Options

ADRI's validity assessment behavior can be configured through several options:

### Global Scoring Weights

You can adjust the maximum score for each component by modifying `VALIDITY_SCORING` in the configuration:

```python
VALIDITY_SCORING = {
    "MAX_TYPES_DEFINED_SCORE": 5,
    "MAX_FORMATS_DEFINED_SCORE": 3,
    "MAX_RANGES_DEFINED_SCORE": 3,
    "MAX_VALIDATION_PERFORMED_SCORE": 3,
    "MAX_VALIDATION_COMMUNICATED_SCORE": 6
}
```

### Requiring Explicit Metadata

Setting `REQUIRE_EXPLICIT_METADATA` to `True` enforces a strict requirement for explicit metadata:

```python
VALIDITY_SCORING = {
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
   validity_scoring:
     MAX_TYPES_DEFINED_SCORE: 5
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
       "validity_scoring": {
           "REQUIRE_EXPLICIT_METADATA": True
       }
   })
   set_config(config)
   ```

## Practical Examples

### Example 1: Dataset With Explicit Metadata

A CSV file `customers.csv` with an accompanying `customers.validation.json` file will receive:
- Full points for validation performed and communicated
- Points for types/formats/ranges if defined in the validation file

### Example 2: Clean Dataset Without Metadata

A CSV file with consistently formatted data but no accompanying metadata:
- When `REQUIRE_EXPLICIT_METADATA=False`: Will receive up to 90% of points based on automated assessment
- When `REQUIRE_EXPLICIT_METADATA=True`: Will receive minimal points despite clean data

### Example 3: Dataset With Validity Issues

A CSV file with inconsistent types, invalid dates, etc.:
- Will have each issue detected and documented in findings
- Specific recommendations will be generated for each detected issue
- Score will be reduced proportionally to the number and severity of issues

## Common Warnings in Assessment

ADRI will produce findings for common validity issues:

- "Data types are inconsistent in X of Y columns"
- "Invalid date formats detected in column 'X': N invalid values"
- "Inconsistent ID formats in column 'X'"
- "Negative values detected in column 'X' where values should be positive"
- "Statistical outliers detected in column 'X'"

## Best Practices

To achieve a high Validity score:

1. **Provide Explicit Schemas**: Include data types and formats for all fields
2. **Create Validation Files**: Define validation rules in companion files
3. **Document Valid Ranges**: Define min/max values and allowed values
4. **Ensure Consistency**: Fix type inconsistencies and format violations
5. **Communicate to Agents**: Make validation results available in machine-readable format

## Common Recommendations

Based on assessment findings, ADRI typically recommends:

1. "Define explicit data types for all fields"
2. "Define formats for applicable fields"
3. "Define valid ranges for applicable fields"
4. "Implement validation rules for this data source"
5. "Ensure validation results are explicitly communicated to agents"
