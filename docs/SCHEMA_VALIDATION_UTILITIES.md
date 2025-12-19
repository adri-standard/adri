# ADRI Schema Validation Utilities

**Version**: 1.0.0  
**Status**: Production Ready  
**Location**: `src/adri/utils/`

## Overview

This document describes the new schema validation utilities added to ADRI Enterprise in Phase 2 of the JSON Reliability Enhancement project. These utilities provide design-time validation and runtime JSON Schema conversion for ADRI specifications.

## Background

During Phase 1 of JSON Reliability Enhancement, we discovered that LLM JSON output issues were caused by ADRI schema design conflicts (type: string but description: "JSON array"). This revealed the need for:

1. **Design-time validation** - Catch schema conflicts when schemas are created
2. **Runtime conversion** - Convert ADRI specs to JSON Schema for structural validation

These utilities implement both capabilities as reusable components for any framework using ADRI.

## Components

### 1. ADRI-to-JSON-Schema Converter

**Module**: `adri.utils.json_schema_converter`

#### Purpose
Converts ADRI `field_requirements` to JSON Schema format for structural validation of data/output.

#### Key Features
- Type mapping: ADRI types → JSON Schema types
- Array handling: items, minItems, maxItems
- String constraints: pattern, minLength, maxLength
- Numeric constraints: minimum, maximum
- Enum support: valid_values → enum
- Nullable handling: anyOf with null type

#### Usage

```python
from adri.utils.json_schema_converter import convert_adri_to_json_schema

# ADRI specification
adri_spec = {
    "field_requirements": {
        "customer_name": {
            "type": "string",
            "min_length": 1,
            "max_length": 100,
            "description": "Customer full name"
        },
        "risk_factors": {
            "type": "array",
            "min_items": 1,
            "max_items": 20,
            "items": {
                "type": "string",
                "min_length": 10,
                "max_length": 200
            },
            "description": "List of risk factors"
        }
    }
}

# Convert to JSON Schema
json_schema = convert_adri_to_json_schema(adri_spec)

# Use with jsonschema library for validation
from jsonschema import Draft7Validator

validator = Draft7Validator(json_schema)
errors = list(validator.iter_errors(data))
```

#### Type Mapping

| ADRI Type | JSON Schema Type | Notes |
|-----------|------------------|-------|
| string | string | Direct mapping |
| integer | integer | Direct mapping |
| float | number | JSON Schema uses "number" for floats |
| boolean | boolean | Direct mapping |
| date | string | Dates represented as ISO strings |
| array | array | Requires items specification |

#### Advanced Usage

```python
from adri.utils.json_schema_converter import ADRIToJSONSchemaConverter

# Create converter with options
converter = ADRIToJSONSchemaConverter(strict_arrays=True)

# Convert
json_schema = converter.convert(adri_spec)

# Check for warnings
warnings = converter.get_warnings()
for warning in warnings:
    print(f"Warning: {warning}")
```

### 2. Schema Consistency Validator

**Module**: `adri.utils.schema_consistency_validator`

#### Purpose
Validates ADRI schema definitions at design-time to catch conflicts and issues before runtime.

#### Key Features
- **Type/Description Conflicts**: Detects when type and description don't match
- **SQL Reserved Words**: Warns about field names that are SQL keywords
- **Constraint Consistency**: Validates min/max value relationships
- **Array Completeness**: Ensures array types have proper specifications
- **Invalid Values**: Catches non-numeric constraints, negative mins, etc.

#### Usage

```python
from adri.utils.schema_consistency_validator import validate_schema_consistency

# ADRI specification (with issues)
adri_spec = {
    "field_requirements": {
        "risk_factors": {
            "type": "string",  # Wrong! 
            "description": "JSON array of risk factors"  # Suggests array type
        }
    }
}

# Validate
report = validate_schema_consistency(adri_spec)

# Check results
if report.has_errors():
    print(f"Found {report.issues_found} issue(s)")
    for issue in report.issues:
        print(f"[{issue.severity.value}] {issue.field_name}: {issue.message}")
        print(f"Remediation: {issue.remediation}")
```

#### Issue Types

| Issue Type | Severity | Description |
|------------|----------|-------------|
| TYPE_DESCRIPTION_CONFLICT | ERROR | Type and description suggest different types |
| SQL_RESERVED_WORD | WARNING/ERROR | Field name is SQL keyword |
| INCOMPLETE_ARRAY_SPEC | WARNING/ERROR | Array missing items or bounds |
| CONFLICTING_CONSTRAINTS | ERROR | min > max constraints |
| INVALID_CONSTRAINT_VALUE | ERROR/WARNING | Invalid constraint types or values |
| MISSING_TYPE | CRITICAL | Field missing type attribute |
| INVALID_TYPE | CRITICAL | Invalid ADRI type |

#### Severity Levels

- **CRITICAL**: Will cause runtime failures, blocks validation
- **ERROR**: Will likely cause issues, should be fixed
- **WARNING**: Best practice violation, review recommended

#### Advanced Usage

```python
from adri.utils.schema_consistency_validator import (
    SchemaConsistencyValidator,
    ConsistencyIssueSeverity
)

# Create validator with strict mode
validator = SchemaConsistencyValidator(strict_mode=True)

# Validate
report = validator.validate(adri_spec)

# Filter issues by severity
criticals = report.get_issues_by_severity(ConsistencyIssueSeverity.CRITICAL)
errors = report.get_issues_by_severity(ConsistencyIssueSeverity.ERROR)
warnings = report.get_issues_by_severity(ConsistencyIssueSeverity.WARNING)

# Export to dict for logging
report_dict = report.to_dict()
```

## Integration Examples

### Example 1: Schema Design Validation

```python
# When creating a new ADRI standard
from adri.utils.schema_consistency_validator import validate_schema_consistency

def validate_new_standard(standard_yaml: dict) -> bool:
    """Validate standard before saving."""
    report = validate_schema_consistency(standard_yaml)
    
    if report.has_critical_issues():
        raise ValueError("Critical schema issues found - cannot save")
    
    if report.has_errors():
        print(f"Warning: {report.issues_found} errors found")
        for issue in report.issues:
            print(f"  - {issue.field_name}: {issue.message}")
        return False
    
    return True
```

### Example 2: LLM Output Validation

```python
# When validating LLM-generated JSON
from adri.utils.json_schema_converter import convert_adri_to_json_schema
from jsonschema import Draft7Validator, ValidationError

def validate_llm_output(adri_spec: dict, llm_output: dict) -> tuple[bool, list]:
    """Validate LLM output against ADRI spec."""
    # Convert ADRI to JSON Schema
    json_schema = convert_adri_to_json_schema(adri_spec)
    
    # Validate
    validator = Draft7Validator(json_schema)
    errors = list(validator.iter_errors(llm_output))
    
    return len(errors) == 0, errors
```

### Example 3: Full Pipeline

```python
from adri.utils.schema_consistency_validator import validate_schema_consistency
from adri.utils.json_schema_converter import convert_adri_to_json_schema
from jsonschema import Draft7Validator

def validate_data_against_standard(standard: dict, data: dict):
    """Complete validation pipeline."""
    # Step 1: Validate schema design
    schema_report = validate_schema_consistency(standard)
    if schema_report.has_critical_issues():
        raise ValueError("Standard has critical schema issues")
    
    # Step 2: Convert to JSON Schema
    json_schema = convert_adri_to_json_schema(standard)
    
    # Step 3: Validate data
    validator = Draft7Validator(json_schema)
    errors = list(validator.iter_errors(data))
    
    return len(errors) == 0, errors
```

## Real-World Use Case: Phase 1 Issue Resolution

### The Problem
```yaml
# BEFORE: Caused 99% failure rate
AI_RISK_FACTORS:
  type: string  # WRONG
  description: "JSON array of identified project risks"
```

LLM correctly generated arrays but validation expected strings.

### The Solution

1. **Design-Time Detection**:
```python
report = validate_schema_consistency(adri_spec)
# Detects: TYPE_DESCRIPTION_CONFLICT
# Message: "Field 'AI_RISK_FACTORS' has type 'string' but description suggests 'array'"
```

2. **Schema Fix**:
```yaml
# AFTER: Achieved 100% success rate
AI_RISK_FACTORS:
  type: array  # CORRECT
  min_items: 1
  max_items: 20
  items:
    type: string
    min_length: 10
    max_length: 200
  description: "JSON array of identified project risks"
```

3. **Runtime Validation**:
```python
json_schema = convert_adri_to_json_schema(adri_spec)
# Now validates arrays correctly with proper structure
```

## SQL Reserved Words Reference

The validator checks for these common SQL reserved words:
- SELECT, FROM, WHERE, ORDER, GROUP, BY
- INSERT, UPDATE, DELETE, JOIN
- CREATE, DROP, ALTER, TABLE
- And 40+ more...

If a field name matches a reserved word, the validator suggests alternatives:
- `{field_name}_value`
- `{field_name}_field`
- `{field_name}_data`

## Testing

Comprehensive test suites are provided:

```bash
# Run converter tests
pytest tests/test_json_schema_converter.py -v

# Run validator tests  
pytest tests/test_schema_consistency_validator.py -v

# Run all schema validation tests
pytest tests/test_*schema*.py -v
```

## Performance

- **Conversion**: ~0.1ms per field (O(n) where n = number of fields)
- **Validation**: ~0.2ms per field (O(n) with pattern matching)
- **Memory**: Minimal overhead, suitable for large schemas

## Best Practices

1. **Run consistency validation during schema design**
   - Catch issues before deployment
   - Use in CI/CD pipelines for standard validation

2. **Convert to JSON Schema once, reuse many times**
   - Cache converted schemas for repeated validation
   - Reduces overhead in high-throughput scenarios

3. **Use strict mode for production schemas**
   - Escalates warnings to errors for stricter validation
   - Ensures highest quality standards

4. **Log all validation warnings**
   - Even non-critical warnings can indicate design issues
   - Track patterns across standards for improvements

## Future Enhancements

Potential additions in future versions:
- Custom type indicator patterns
- Extended SQL dialect support
- Schema diff/migration tools
- Auto-fix suggestions for common issues
- Integration with schema versioning

## Support

For issues or questions:
- GitHub Issues: [verodat/adri-enterprise](https://github.com/verodat/adri-enterprise)
- Documentation: [ADRI Enterprise Docs](https://docs.verodat.com/adri-enterprise)

## Changelog

### Version 1.0.0 (2025-01-28)
- Initial release
- ADRI-to-JSON-Schema converter
- Schema consistency validator
- Comprehensive test suites
- Production-ready for Phase 2 integration
