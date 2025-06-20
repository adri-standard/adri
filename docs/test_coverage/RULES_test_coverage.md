# RULES Test Coverage

This document tracks test coverage for the ADRI rules module, including diagnostic rules, rule evaluation, and the rule registry system.

## Purpose
The rules module provides a framework for defining and applying diagnostic rules that identify specific data quality issues within each dimension.

## Test Coverage

### adri/rules/base.py
- **Unit Tests**: `tests/unit/rules/test_base.py`
  - ✅ Tests DiagnosticRule abstract interface
  - ✅ Tests rule metadata handling
  - ✅ Tests rule evaluation framework
  - ✅ Tests severity levels

### adri/rules/validity.py
- **Unit Tests**: `tests/unit/rules/test_validity_rules.py`
  - ✅ Tests EmailFormatRule
  - ✅ Tests DateFormatRule
  - ✅ Tests NumericRangeRule
  - ✅ Tests RegexValidationRule
  - ✅ Tests custom validity rules

### adri/rules/completeness.py
- **Unit Tests**: `tests/unit/rules/test_completeness_rules.py`
  - ✅ Tests RequiredFieldRule
  - ✅ Tests MinimumFieldsRule
  - ✅ Tests ConditionalRequiredRule
  - ✅ Tests completeness threshold rules

### adri/rules/freshness.py
- **Unit Tests**: `tests/unit/rules/test_freshness_rules.py`
  - ✅ Tests MaxAgeRule
  - ✅ Tests UpdateFrequencyRule
  - ✅ Tests StaleDataRule
  - ✅ Tests time-based rules

### adri/rules/consistency.py
- **Unit Tests**: `tests/unit/rules/test_consistency_rules.py`
  - ✅ Tests CrossFieldConsistencyRule
  - ✅ Tests ReferentialIntegrityRule
  - ✅ Tests DuplicateDetectionRule
  - ✅ Tests consistency validation rules

### adri/rules/plausibility.py
- **Unit Tests**: `tests/unit/rules/test_plausibility_rules.py`
  - ✅ Tests StatisticalOutlierRule
  - ✅ Tests BusinessLogicRule
  - ✅ Tests ValueRangeRule
  - ✅ Tests pattern-based rules

### adri/rules/registry.py
- **Unit Tests**: `tests/unit/rules/test_registry.py`
  - ✅ Tests rule registration
  - ✅ Tests rule discovery by dimension
  - ✅ Tests rule loading and instantiation
  - ✅ Tests custom rule plugins

### adri/rules/expiration_rule.py
- **Unit Tests**: `tests/unit/rules/test_expiration_rule.py`
  - ✅ Tests expiration date checking
  - ✅ Tests warning periods
  - ✅ Tests different date formats
  - ✅ Tests timezone handling

### adri/rules/demo.py
- **Unit Tests**: `tests/unit/rules/test_demo_rules.py`
  - ✅ Tests demonstration rules
  - ✅ Tests example implementations

### Key Features Tested

| Feature | Test Type | Coverage |
|---------|-----------|----------|
| Rule base interface | Unit | ✅ Complete |
| Validity rules | Unit | ✅ Complete |
| Completeness rules | Unit | ✅ Complete |
| Freshness rules | Unit | ✅ Complete |
| Consistency rules | Unit | ✅ Complete |
| Plausibility rules | Unit | ✅ Complete |
| Rule registry | Unit | ✅ Complete |
| Custom rule loading | Unit | ✅ Complete |
| Rule severity handling | Unit | ✅ Complete |

### Test Statistics
- **Total Tests**: 124
- **Passing**: 124
- **Coverage**: 91%

### Example Test Cases

```python
<!-- audience: ai-builders -->
def test_email_format_rule():
    """Test EmailFormatRule identifies invalid email formats."""
    rule = EmailFormatRule()
    
    # Valid email
    result = rule.evaluate({"email": "user@example.com"})
    assert result.passed
    
    # Invalid email
    result = rule.evaluate({"email": "invalid.email"})
    assert not result.passed
    assert "Invalid email format" in result.message

def test_required_field_rule():
    """Test RequiredFieldRule detects missing fields."""
    rule = RequiredFieldRule(field="customer_id")
    
    # Field present
    result = rule.evaluate({"customer_id": "12345"})
    assert result.passed
    
    # Field missing
    result = rule.evaluate({"name": "John"})
    assert not result.passed
    assert result.severity == Severity.ERROR
```

### Rule Configuration

Rules can be configured through YAML:

```yaml
rules:
  validity:
    - type: EmailFormatRule
      field: email_address
      severity: error
    - type: DateFormatRule
      field: created_date
      format: "%Y-%m-%d"
      
  completeness:
    - type: RequiredFieldRule
      fields: [id, name, email]
      severity: critical
```

### Coverage Gaps
- Complex rule combinations
- Performance impact of many rules
- Rule conflict resolution
- Dynamic rule generation

### Dependencies
This module is used by:
- Dimensions module (see DIMENSIONS_test_coverage.md)
- Templates module (see TEMPLATES_test_coverage.md)
- Assessor module (see CORE_test_coverage.md)

---
*Last Updated: 2025-06-03*
