# ADRI Open-Source Features Reference

> **Last Updated:** October 21, 2025
> **ADRI Version:** 5.0.x

Complete reference for all ADRI features and capabilities.

---

## Table of Contents
- [Overview](#overview)
- [CLI Commands](#cli-commands)
- [Decorator Parameters](#decorator-parameters)
- [Logging System](#logging-system)
- [Standards Library](#standards-library)
- [Standard Validator](#standard-validator)

---

## Overview

ADRI open-source provides core data quality validation capabilities:
- **CLI Tools** for standard management and validation
- **Python Decorator** for runtime data quality checks
- **Local JSONL Logging** for assessment results
- **Standards Library** with 13 pre-built standards
- **Standard Validator** for YAML validation

---

## CLI Commands

### Available Commands

```bash
adri setup              # Initialize ADRI configuration
adri generate-standard  # Generate standards from data samples
adri assess             # Validate data against standards
adri list-standards     # List available standards
adri validate-standard  # Validate standard YAML correctness
adri guide              # Interactive setup walkthrough
```

### Command Details

#### `adri setup`
Initialize ADRI in your project.
```bash
adri setup
```

#### `adri generate-standard`
Generate a standard from sample data.
```bash
adri generate-standard --data sample.csv --output my_standard.yaml
```

#### `adri assess`
Validate data against a standard.
```bash
adri assess --data data.csv --standard my_standard.yaml
```

#### `adri list-standards`
View available standards in the catalog.
```bash
adri list-standards
```

#### `adri validate-standard`
Validate standard YAML syntax and structure.
```bash
adri validate-standard my_standard.yaml
```

#### `adri guide`
Launch interactive setup wizard.
```bash
adri guide
```

---

## Decorator Parameters

### Core Parameters

Use `@adri_protected()` decorator to validate function inputs/outputs.

#### Available Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `standard` | `str` | **Required** | Name of the standard to validate against |
| `data_param` | `str` | `"data"` | Parameter name containing data to validate |
| `min_score` | `float` | `0.8` | Minimum quality score threshold (0.0-1.0) |
| `dimensions` | `Dict[str, float]` | `None` | Dimension-specific score requirements |
| `on_failure` | `str` | `"raise"` | Failure handling: `"raise"`, `"warn"`, or `"continue"` |
| `auto_generate` | `bool` | `False` | Auto-create standard if missing |
| `cache_assessments` | `bool` | `True` | Cache assessment results |
| `verbose` | `bool` | `False` | Show detailed validation logs |

### Parameter Details

#### `standard` (Required)
The name of the YAML standard to validate against.
```python
@adri_protected(standard="invoice_quality")
def process_invoice(data: pd.DataFrame) -> Dict:
    pass
```

#### `data_param`
Specify which function parameter contains the data.
```python
@adri_protected(standard="customer_data", data_param="customers")
def analyze(customers: pd.DataFrame, config: Dict) -> Dict:
    pass
```

#### `min_score`
Set minimum acceptable quality score (0.0 to 1.0).
```python
@adri_protected(standard="sales_data", min_score=0.85)
def process_sales(data: pd.DataFrame) -> Dict:
    pass
```

#### `dimensions`
Set dimension-specific requirements.
```python
@adri_protected(
    standard="financial_data",
    dimensions={
        "completeness": 0.95,  # 95% completeness required
        "validity": 0.90,       # 90% validity required
        "consistency": 0.85     # 85% consistency required
    }
)
def process_financials(data: pd.DataFrame) -> Dict:
    pass
```

Available dimensions:
- `completeness` - Missing/null value checks
- `validity` - Data type and format validation
- `consistency` - Cross-field consistency checks
- `plausibility` - Value range and logic checks
- `accuracy` - Reference data validation

#### `on_failure`
Control behavior when validation fails.
```python
# Raise exception (default)
@adri_protected(standard="critical_data", on_failure="raise")

# Log warning and continue
@adri_protected(standard="optional_check", on_failure="warn")

# Silent continue (log only)
@adri_protected(standard="monitoring", on_failure="continue")
```

#### `auto_generate`
Automatically create standards from data if missing.
```python
@adri_protected(standard="new_dataset", auto_generate=True)
def process_new_data(data: pd.DataFrame) -> Dict:
    # Standard will be generated on first run
    pass
```

#### `cache_assessments`
Enable/disable result caching.
```python
@adri_protected(standard="expensive_check", cache_assessments=True)
def slow_validation(data: pd.DataFrame) -> Dict:
    pass
```

#### `verbose`
Show detailed validation output.
```python
@adri_protected(standard="debug_check", verbose=True)
def debug_process(data: pd.DataFrame) -> Dict:
    pass
```

### Complete Example

```python
import pandas as pd
from adri.validator.decorators import adri_protected

@adri_protected(
    standard="customer_service_quality",
    data_param="tickets",
    min_score=0.8,
    dimensions={
        "completeness": 0.9,
        "validity": 0.85
    },
    on_failure="warn",
    auto_generate=False,
    cache_assessments=True,
    verbose=False
)
def process_tickets(tickets: pd.DataFrame, config: Dict) -> Dict:
    """Process customer service tickets with quality validation."""
    # Your processing logic
    return {"status": "success"}
```

---

## Logging System

### Format: JSONL (JSON Lines)

ADRI logs assessment results in **JSONL format** (newline-delimited JSON).

### Log Location
```
.adri/logs/assessments.jsonl
```

### Log Structure

Each line is a complete JSON object:
```json
{
  "assessment_id": "20250117_143022_abc123",
  "timestamp": "2025-01-17T14:30:22.123456",
  "standard_name": "customer_service_quality",
  "overall_score": 0.87,
  "dimension_scores": {
    "completeness": 0.92,
    "validity": 0.85,
    "consistency": 0.88,
    "plausibility": 0.84,
    "accuracy": 0.86
  },
  "failed_validations": [
    {
      "rule": "email_format",
      "severity": "critical",
      "failed_count": 3
    }
  ],
  "metadata": {
    "function_name": "process_tickets",
    "data_rows": 1500
  }
}
```

### Reading Logs

```python
import json

# Read JSONL logs
with open(".adri/logs/assessments.jsonl", "r") as f:
    assessments = [json.loads(line) for line in f]

# Filter by standard
customer_assessments = [
    a for a in assessments
    if a["standard_name"] == "customer_service_quality"
]

# Analyze scores
import pandas as pd
df = pd.DataFrame(assessments)
print(df["overall_score"].describe())
```

---

## Standards Library

### Catalog Standards (13 Pre-built)

ADRI includes 13 production-ready standards:

1. **Customer Data Standards**
   - `customer_basic_info` - Core customer fields
   - `customer_contact_info` - Contact details validation

2. **Financial Standards**
   - `invoice_data` - Invoice field validation
   - `payment_transaction` - Payment data checks

3. **Geographic Standards**
   - `address_data` - Address field validation
   - `location_coordinates` - GPS/lat-long checks

4. **Product Standards**
   - `product_catalog` - Product information
   - `inventory_data` - Stock/inventory checks

5. **Transaction Standards**
   - `order_data` - Order validation
   - `sales_transaction` - Sales data checks

6. **User Activity Standards**
   - `user_profile` - User account data
   - `activity_log` - Activity tracking
   - `session_data` - Session information

### Standard Structure

```yaml
name: my_standard
description: Data quality standard for X
version: "1.0"
dimensions:
  completeness:
    rules:
      - name: required_fields
        fields: [field1, field2]
        severity: critical
  validity:
    rules:
      - name: email_format
        field: email
        pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        severity: critical
```

---

## Standard Validator

### Validation Features

The standard validator ensures YAML standards are correct:
- Schema validation (required fields, structure)
- Rule syntax checking
- Dimension verification
- Cross-reference validation

### Usage

```bash
# Validate a standard
adri validate-standard my_standard.yaml

# Validate all standards
adri validate-standard standards/*.yaml
```

### Python API

```python
from adri.validator.standards import StandardValidator

validator = StandardValidator()
result = validator.validate_file("my_standard.yaml")

if result.is_valid:
    print("✓ Standard is valid")
else:
    print(f"✗ Validation errors: {result.errors}")
```

---

## Version Information

**Current Version:** 5.0.x
**Documentation Updated:** October 21, 2025

---

## Related Documentation

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [CLI Reference](CLI_REFERENCE.md) - CLI command details
- [Getting Started](GETTING_STARTED.md) - Quick start guide
- [Standards Library](STANDARDS_LIBRARY.md) - Standard catalog details
- [Assessment Logs](ASSESSMENT_LOG_EXPLANATION.md) - Log format details

---

## Questions?

- **GitHub Issues:** [ADRI Issues](https://github.com/adri-standard/adri/issues)
- **Documentation:** [docs/](../docs/)
- **Examples:** [examples/](../examples/)
