# Severity Levels in ADRI Validation Rules

**Version:** 1.0.0
**Last Updated:** October 2025

## Overview

ADRI now supports **explicit severity levels** in validation rules, giving you fine-grained control over which rule failures affect dimension scores. This makes scoring behavior transparent and customizable.

## Severity Levels

### CRITICAL (Score Impact)
**Effect:** Failures reduce dimension scores
**Use For:** Data quality issues that truly matter
- Type validation (data must be correct type)
- Required fields (data must be present)
- Allowed values (enums must be valid)
- Numeric/date/length bounds (values within range)
- Primary key uniqueness

**Example:**
```yaml
validation_rules:
  - name: "Email is required"
    dimension: "completeness"
    severity: "CRITICAL"
    rule_type: "not_null"
    rule_expression: "IS_NOT_NULL"
```

### WARNING (Logged Only)
**Effect:** Logged but doesn't affect scores
**Use For:** Style preferences and best practices
- Format consistency (lowercase, case)
- Pattern matching for style (not correctness)
- Cross-field logic (non-critical)
- Rare category detection

**Example:**
```yaml
validation_rules:
  - name: "Email should be lowercase"
    dimension: "consistency"
    severity: "WARNING"
    rule_type: "format"
    rule_expression: "IS_LOWERCASE"
```

### INFO (Informational)
**Effect:** Minimal logging, no score impact
**Use For:** Statistical observations
- Outlier detection (95th percentile)
- Recency notifications
- Staleness warnings

**Example:**
```yaml
validation_rules:
  - name: "Statistical outlier detected"
    dimension: "plausibility"
    severity: "INFO"
    rule_type: "statistical_outlier"
    rule_expression: "Z_SCORE < 3"
```

## Standard Format

### New Format (Explicit Severity)

```yaml
field_requirements:
  status:
    type: string
    nullable: false
    allowed_values: ["paid", "pending", "cancelled"]
    validation_rules:
      # CRITICAL - affects score
      - name: "Status is required"
        dimension: "completeness"
        severity: "CRITICAL"
        rule_type: "not_null"
        rule_expression: "IS_NOT_NULL"
        error_message: "Status field must not be empty"

      - name: "Status must be valid value"
        dimension: "validity"
        severity: "CRITICAL"
        rule_type: "allowed_values"
        rule_expression: "VALUE_IN(['paid', 'pending', 'cancelled'])"
        error_message: "Status must be one of: paid, pending, cancelled"

      # WARNING - logged only, no score penalty
      - name: "Status should be lowercase"
        dimension: "consistency"
        severity: "WARNING"
        rule_type: "format"
        rule_expression: "IS_LOWERCASE"
        error_message: "Status values should use lowercase"
```

## Auto-Generated Standards

Auto-generated standards automatically assign appropriate severity levels based on `src/adri/config/severity_defaults.yaml`:

**Default CRITICAL Rules:**
- Data type validation
- Required field validation (not_null)
- Allowed values (enum constraints)
- Numeric bounds, date bounds, length bounds
- Primary key uniqueness

**Default WARNING Rules:**
- Format consistency (lowercase, case)
- Pattern matching (often style-based)
- Cross-field logic (context-dependent)
- Age checks, range checks
- Categorical frequency

**Default INFO Rules:**
- Recency notifications
- Staleness warnings
- Statistical outlier flagging

### Customizing Defaults

Edit `src/adri/config/severity_defaults.yaml` or set `ADRI_SEVERITY_CONFIG` environment variable:

```bash
export ADRI_SEVERITY_CONFIG=/path/to/custom/severity_config.yaml
```

## Migration Guide

### For Existing Standards

Use the migration script:

```bash
python scripts/migrate_standards_to_severity.py
```

This automatically converts old-style field constraints to validation_rules with appropriate severity levels.

### Manual Conversion

**Old Format:**
```yaml
field_requirements:
  email:
    type: string
    nullable: false
    pattern: '^[a-z]+@[a-z]+\.[a-z]+$'
```

**New Format:**
```yaml
field_requirements:
  email:
    type: string
    nullable: false
    validation_rules:
      - name: "Email is required"
        dimension: "completeness"
        severity: "CRITICAL"
        rule_type: "not_null"
        rule_expression: "IS_NOT_NULL"

      - name: "Email type validation"
        dimension: "validity"
        severity: "CRITICAL"
        rule_type: "type"
        rule_expression: "IS_STRING"

      - name: "Email pattern validation"
        dimension: "validity"
        severity: "WARNING"  # Pattern often style preference
        rule_type: "pattern"
        rule_expression: "REGEX_MATCH('^[a-z]+@[a-z]+\.[a-z]+$')"
```

## Impact on Scoring

### Before (Implicit Severity)
All validation failures reduced scores equally.

### After (Explicit Severity)

**Scenario 1: All CRITICAL Failures**
- 100 values, 20 fail CRITICAL rules
- Score: (80/100) * 20 = 16.0/20

**Scenario 2: All WARNING Failures**
- 100 values, 20 fail WARNING rules
- Score: 20.0/20 (perfect - no score penalty)

**Scenario 3: Mixed Severity**
- 100 values, 5 fail CRITICAL, 20 fail WARNING
- Score: (95/100) * 20 = 19.0/20
- WARNING failures logged but don't affect score

## Best Practices

### 1. Use CRITICAL for Data Quality
Mark rules as CRITICAL when failures indicate actual data quality problems:
- Wrong data type (string instead of number)
- Missing required information
- Values outside valid range
- Duplicate primary keys

### 2. Use WARNING for Style Preferences
Mark rules as WARNING when failures are stylistic or preferential:
- Lowercase vs uppercase formatting
- Date format preferences (ISO vs US format)
- Pattern matching for aesthetics
- Minor cross-field inconsistencies

### 3. Use INFO for Observations
Mark rules as INFO for statistical or informational notices:
- Outlier detection (might be valid extreme values)
- Data recency notifications
- Rare category flagging

### 4. Document Rule Intent
Always include clear `error_message` and `remediation` fields:

```yaml
- name: "Amount must be positive"
  dimension: "validity"
  severity: "CRITICAL"
  rule_type: "numeric_bounds"
  rule_expression: "VALUE >= 0"
  error_message: "Transaction amount cannot be negative"
  remediation: "Check data source for negative amounts and correct"
```

## Common Patterns

### Required Enum Field
```yaml
field_requirements:
  status:
    type: string
    nullable: false
    allowed_values: ["active", "inactive", "pending"]
    validation_rules:
      - name: "Status required"
        severity: "CRITICAL"  # Must have value
        dimension: "completeness"
        rule_type: "not_null"

      - name: "Status must be valid"
        severity: "CRITICAL"  # Must be in enum
        dimension: "validity"
        rule_type: "allowed_values"

      - name: "Status lowercase preference"
        severity: "WARNING"  # Style only
        dimension: "consistency"
        rule_type: "format"
```

### Numeric Field with Bounds
```yaml
field_requirements:
  amount:
    type: float
    nullable: false
    min_value: 0.0
    max_value: 1000000.0
    validation_rules:
      - name: "Amount required"
        severity: "CRITICAL"
        dimension: "completeness"
        rule_type: "not_null"

      - name: "Amount numeric bounds"
        severity: "CRITICAL"  # Must be in range
        dimension: "validity"
        rule_type: "numeric_bounds"

      - name: "Amount outlier check"
        severity: "INFO"  # Just FYI
        dimension: "plausibility"
        rule_type: "statistical_outlier"
```

## FAQs

**Q: Can I change severity for a specific rule?**
A: Yes! Just edit the `severity` field in your standard's validation_rules.

**Q: Will WARNING rules still appear in logs?**
A: Yes! WARNING failures are logged for visibility, they just don't reduce scores.

**Q: Do I need to update existing standards?**
A: No - old format still works. But we recommend migrating for transparency.

**Q: Can I make all format rules CRITICAL?**
A: Yes! Edit `src/adri/config/severity_defaults.yaml` and set `consistency.format: CRITICAL`

**Q: What happens if I have no CRITICAL rules?**
A: You get a perfect score (20/20) for that dimension - no penalties possible.

## See Also

- [Implementation Plan](../severity_levels_implementation_plan.md)
- [Severity Defaults Config](../src/adri/config/severity_defaults.yaml)
- [Getting Started Guide](GETTING_STARTED.md)
