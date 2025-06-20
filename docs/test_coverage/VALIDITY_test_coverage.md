# VALIDITY Test Coverage

This document tracks test coverage specifically for validity-related functionality across ADRI, including the validity dimension and validity rules.

## Purpose
Validity testing ensures data conforms to expected formats, types, and constraints. This is one of the core data quality dimensions.

## Test Coverage

### Validity Dimension (adri/dimensions/validity.py)
- **Unit Tests**: `tests/unit/dimensions/test_validity.py`
  - ✅ Tests data type validation
  - ✅ Tests format validation (email, phone, date)
  - ✅ Tests constraint checking (min/max, length)
  - ✅ Tests pattern matching
  - ✅ Tests custom validation functions

### Validity Rules (adri/rules/validity.py)
- **Unit Tests**: `tests/unit/rules/test_validity_rules.py`
  - ✅ Tests EmailFormatRule
  - ✅ Tests PhoneFormatRule
  - ✅ Tests DateFormatRule
  - ✅ Tests NumericRangeRule
  - ✅ Tests StringLengthRule
  - ✅ Tests RegexValidationRule
  - ✅ Tests EnumValidationRule
  - ✅ Tests custom validity rules

### Business Validity (adri/dimensions/business_validity.py)
- **Unit Tests**: `tests/unit/dimensions/test_business_validity.py`
  - ✅ Tests industry-specific validations
  - ✅ Tests business rule compliance
  - ✅ Tests regulatory format requirements

### Integration Tests
- **File Validity**: `tests/integration/test_validity_file_integration.py`
  - ✅ Tests CSV file validation
  - ✅ Tests JSON schema validation
  - ✅ Tests XML schema validation

- **Database Validity**: `tests/integration/test_validity_database_integration.py`
  - ✅ Tests column type validation
  - ✅ Tests constraint validation
  - ✅ Tests foreign key validation

### Key Features Tested

| Feature | Test Type | Coverage |
|---------|-----------|----------|
| Type validation | Unit | ✅ Complete |
| Format validation | Unit | ✅ Complete |
| Pattern matching | Unit | ✅ Complete |
| Range validation | Unit | ✅ Complete |
| Custom validators | Unit | ✅ Complete |
| Schema validation | Integration | ✅ Complete |
| Business rules | Unit | ✅ Complete |

### Test Statistics
- **Total Tests**: 87
- **Passing**: 87
- **Coverage**: 94%

### Example Test Cases

```python
<!-- audience: ai-builders -->
def test_email_validation():
    """Test email format validation."""
    validator = ValidityDimension()
    
    # Valid emails
    assert validator.validate_email("user@example.com")
    assert validator.validate_email("user.name+tag@example.co.uk")
    
    # Invalid emails
    assert not validator.validate_email("invalid.email")
    assert not validator.validate_email("@example.com")
    assert not validator.validate_email("user@")

def test_numeric_range_validation():
    """Test numeric range constraints."""
    rule = NumericRangeRule(min_value=0, max_value=100)
    
    assert rule.evaluate({"score": 50}).passed
    assert not rule.evaluate({"score": -10}).passed
    assert not rule.evaluate({"score": 150}).passed
```

### Validation Configurations

```yaml
validity:
  rules:
    - field: email
      type: email
      required: true
      
    - field: age
      type: integer
      min: 0
      max: 150
      
    - field: status
      type: enum
      values: [active, inactive, pending]
      
    - field: phone
      type: regex
      pattern: "^\\+?[1-9]\\d{1,14}$"
```

### Common Validity Issues Detected
1. **Type Mismatches**: String where number expected
2. **Format Violations**: Invalid email/phone formats
3. **Range Violations**: Values outside acceptable bounds
4. **Pattern Mismatches**: Data not matching regex patterns
5. **Schema Violations**: JSON/XML not conforming to schema

### Coverage Gaps
- Complex nested validation
- Cross-field validity rules
- Conditional validation logic
- Performance with large validation rule sets

### Related Documentation
- Validity dimension details: [validity_dimension.md](concepts/validity_dimension.md)
- Rules framework: [RULES_test_coverage.md](RULES_test_coverage.md)
- Dimensions overview: [DIMENSIONS_test_coverage.md](DIMENSIONS_test_coverage.md)

---
*Last Updated: 2025-06-03*
