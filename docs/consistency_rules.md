# Consistency Rules for ADRI

This document describes the consistency dimension rules implemented for the ADRI system.

## Overview

Consistency rules examine data for internal coherence and alignment, focusing on:

- Cross-field validation
- Referential integrity
- Uniform representation
- Calculation consistency

These rules help identify contradictions, inconsistencies, and violations of relationships between data elements.

### Template Mode Scoring

When using templates, the Consistency dimension scoring works differently:

1. **Rule Weights**: Each rule has a weight parameter that determines its contribution to the dimension score
2. **20-Point Total**: All rule weights within the consistency dimension must sum to 20 points
3. **Flexible Distribution**: You can allocate more weight to critical consistency checks

Example template configuration:
```yaml
dimensions:
  consistency:
    rules:
      - type: cross_field
        params:
          weight: 12  # 12 out of 20 points - critical validation
          validation_type: "expression"
          fields: ["start_date", "end_date"]
          expression: "pd.to_datetime(subset_df['start_date']) <= pd.to_datetime(subset_df['end_date'])"
      - type: uniform_representation
        params:
          weight: 8   # 8 out of 20 points
          column: "status"
          format_type: "categorical"
          allowed_values: ["active", "inactive", "pending"]
```

## Implemented Rules

### CrossFieldConsistencyRule

**Purpose**: Validates consistency between related fields within records.

**Key Parameters**:
- `validation_type`: Type of validation - 'expression', 'comparison', or 'custom'
- `fields`: List of field names to validate together
- `expression`: Python expression that should evaluate to True (when validation_type='expression')
- `comparisons`: List of comparison operations between fields (when validation_type='comparison')
- `custom_validation`: Name of a custom validation function (when validation_type='custom')

**Example**:

```python
# Example configuration for CrossFieldConsistencyRule
cross_field_params = {
    "validation_type": "expression",
    "fields": ["age", "birth_date"],
    "expression": "(pd.to_datetime('today') - pd.to_datetime(subset_df['birth_date'])).dt.days / 365 - subset_df['age'] < 1.0"
}
```

### UniformRepresentationRule

**Purpose**: Validates consistent formatting and representation of values.

**Key Parameters**:
- `column`: Column to validate for uniform representation
- `format_type`: Type of format check - 'pattern', 'categorical', 'length'
- `pattern`: Regex pattern that values should match (when format_type='pattern')
- `allowed_values`: List of allowed values (when format_type='categorical')
- `max_variations`: Maximum number of different formats allowed (when format_type='length')
- `case_sensitive`: Whether to treat text values as case-sensitive

**Example**:

```python
# Example configuration for UniformRepresentationRule
uniform_params = {
    "column": "birth_date",
    "format_type": "pattern",
    "pattern": r"^\d{4}-\d{2}-\d{2}$"
}
```

### CalculationConsistencyRule

**Purpose**: Validates consistency of calculated values.

**Key Parameters**:
- `result_column`: Column containing the calculated result to validate
- `calculation_type`: Type of calculation - 'expression' or 'custom'
- `expression`: Python expression for recalculating expected values (when calculation_type='expression')
- `input_columns`: Columns used as inputs to the calculation
- `tolerance`: Tolerance for floating-point comparisons
- `custom_calculation`: Name of a custom calculation function (when calculation_type='custom')

**Example**:

```python
# Example configuration for CalculationConsistencyRule
calc_rule_params = {
    "result_column": "total_price",
    "calculation_type": "expression",
    "expression": "subset_df['quantity'] * subset_df['unit_price']",
    "input_columns": ["quantity", "unit_price"],
    "tolerance": 0.01
}
```

## Usage Examples

### Basic Usage

```python
from adri import DataSourceAssessor
from adri.connectors.file import CSVConnector
from adri.rules.consistency import CrossFieldConsistencyRule, UniformRepresentationRule, CalculationConsistencyRule
from adri.rules.registry import RuleRegistry

# Create data source
data_source = CSVConnector(filepath="data.csv")

# Create and register rules
registry = RuleRegistry()
registry.register(CrossFieldConsistencyRule(params={
    "validation_type": "expression",
    "fields": ["start_date", "end_date"],
    "expression": "pd.to_datetime(subset_df['start_date']) <= pd.to_datetime(subset_df['end_date'])"
}))

# Create assessor and run assessment
assessor = DataSourceAssessor()
report = assessor.assess(data_source)
```

### Common Consistency Checks

1. **Date Range Validation**:
   ```python
# Parameters for CrossFieldConsistencyRule
date_range_params = {
    "validation_type": "expression", 
    "fields": ["start_date", "end_date"],
    "expression": "pd.to_datetime(subset_df['start_date']) <= pd.to_datetime(subset_df['end_date'])"
}
   ```

2. **Consistent Date Formats**:
   ```python
# Parameters for UniformRepresentationRule
date_format_params = {
    "column": "transaction_date",
    "format_type": "pattern",
    "pattern": r"^\d{4}-\d{2}-\d{2}$"
}
   ```

3. **Calculated Field Validation**:
   ```python
# Parameters for CalculationConsistencyRule
calculation_params = {
    "result_column": "total",
    "calculation_type": "expression",
    "expression": "subset_df['price'] * subset_df['quantity']",
    "input_columns": ["price", "quantity"],
    "tolerance": 0.01
}
   ```

4. **Categorical Value Consistency**:
   ```python
# Parameters for UniformRepresentationRule
categorical_params = {
    "column": "status",
    "format_type": "categorical",
    "allowed_values": ["active", "inactive", "pending"],
    "case_sensitive": False
}
   ```

## Full Example

See `examples/consistency_assessment.py` for a complete example that demonstrates:

1. Creating synthetic data with consistency issues
2. Configuring multiple consistency rules
3. Running the assessment
4. Interpreting and displaying the results

## Best Practices

1. **Combine with other dimensions**: Consistency rules work best alongside validity, completeness, and plausibility checks for comprehensive data quality assessment.

2. **Set appropriate tolerances**: For numerical calculations, consider the level of precision required for your use case.

3. **Consider performance**: For large datasets, complex expressions might be computationally expensive. Consider sampling for initial assessments.

4. **Handle nulls appropriately**: Ensure your expressions and rules handle null values correctly to avoid false positives.

## Purpose & Test Coverage

**Why this file exists**: Provides detailed documentation on consistency rules that examine data for internal coherence and alignment, helping identify contradictions and violations of relationships between data elements.

**Key responsibilities**:
- Document consistency rule implementations
- Provide usage examples for each rule type
- Show common consistency checks patterns
- Guide best practices for consistency validation
- Demonstrate integration with ADRI assessor

**Test coverage**: This document's examples, claims, and features should be verified by tests documented in [consistency_rules_test_coverage.md](./test_coverage/consistency_rules_test_coverage.md)
