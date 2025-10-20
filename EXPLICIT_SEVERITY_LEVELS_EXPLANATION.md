# Explicit Severity Levels in ADRI Validation Rules

## User Question: "What do you mean by adding explicit severity levels to validation rules?"

## Current State (Implicit Behavior)

Right now, ADRI **infers** severity based on the type of validation rule, but this is **not explicitly configured**. The behavior is:

### Implicit Severity (Current)
```python
# ADRI internally decides severity based on rule type
if rule_type == "inconsistent_format":
    severity = WARNING  # Doesn't penalize score
elif rule_type == "missing_required":
    severity = CRITICAL  # Penalizes score
elif rule_type == "type_failed":
    severity = CRITICAL  # Penalizes score
```

**Problem**: Users can't see or control this behavior. It's hardcoded in the validation engine.

---

## Proposed State (Explicit Severity)

Make severity a **configurable property** of each validation rule so users can:
1. See what impact a rule has on scoring
2. Customize severity based on business needs
3. Understand why scores are what they are

### Explicit Severity (Proposed)
```yaml
validation_rules:
  - name: "Email format validation"
    field: "customer_email"
    rule: "REGEX_MATCH(row['customer_email'], '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$')"
    severity: CRITICAL  # <-- EXPLICIT: This rule WILL reduce score if failed
    dimension: validity

  - name: "Status format consistency"
    field: "status"
    rule: "VALUE_IN(['paid', 'pending', 'cancelled'])"
    severity: WARNING  # <-- EXPLICIT: This rule WON'T reduce score, just logs
    dimension: consistency

  - name: "Amount must be positive"
    field: "amount"
    rule: "row['amount'] > 0"
    severity: CRITICAL  # <-- EXPLICIT: Business rule that MUST pass
    dimension: plausibility
```

---

## Severity Levels Defined

### 1. CRITICAL
**Impact**: Reduces dimension score when rule fails

**Use Cases**:
- Data that makes processing impossible
- Business rules that must be enforced
- Type mismatches, missing required fields
- Out-of-bounds values that break logic

**Example**:
```yaml
- name: "Invoice ID is required"
  field: "invoice_id"
  rule: "row['invoice_id'] IS NOT NULL"
  severity: CRITICAL
  rationale: "Cannot process invoice without ID"
```

### 2. WARNING
**Impact**: Logged for remediation but doesn't reduce score

**Use Cases**:
- Format inconsistencies that don't break processing
- Recommended but not mandatory fields
- Style guide violations
- Data quality suggestions

**Example**:
```yaml
- name: "Email format should be lowercase"
  field: "customer_email"
  rule: "row['customer_email'] == LOWER(row['customer_email'])"
  severity: WARNING
  rationale: "Uppercase emails work but lowercase is convention"
```

### 3. INFO (Future)
**Impact**: Logged for information only, no action needed

**Use Cases**:
- Statistical observations
- Data profiling information
- Pattern detection results
- Anomaly notifications that may or may not be issues

**Example**:
```yaml
- name: "Unusually high order amount"
  field: "amount"
  rule: "row['amount'] > PERCENTILE(amount, 95)"
  severity: INFO
  rationale: "Flagging outliers for review, not necessarily errors"
```

---

## How It Works in Practice

### Example: Invoice Processing Standard

**Current (Implicit)**:
```yaml
# In current ADRI standard files
target_fields:
  - name: "status"
    type: "string"
    mandatory: true
    allowed_values: ["paid", "pending"]
    # Severity is implicit - ADRI decides internally
```

**Proposed (Explicit)**:
```yaml
# In enhanced ADRI standard files
target_fields:
  - name: "status"
    type: "string"
    mandatory: true
    allowed_values: ["paid", "pending"]
    validation_rules:
      - name: "Status must be allowed value"
        rule: "VALUE_IN(['paid', 'pending'])"
        severity: CRITICAL  # <-- EXPLICIT
        error_message: "Status must be 'paid' or 'pending'"

      - name: "Status should be lowercase"
        rule: "row['status'] == LOWER(row['status'])"
        severity: WARNING  # <-- EXPLICIT
        error_message: "Status should use lowercase for consistency"
```

---

## Real-World Scenario

### Scenario: Customer Email Field

**Business Requirements**:
1. Email MUST be present (CRITICAL)
2. Email MUST match email format (CRITICAL)
3. Email SHOULD be lowercase (WARNING - nice to have)
4. Email SHOULD be from business domain (WARNING - preference)

**Configuration with Explicit Severity**:
```yaml
target_fields:
  - name: "customer_email"
    type: "string"
    mandatory: true
    validation_rules:
      # CRITICAL - Must pass or score reduced
      - name: "Email is required"
        rule: "row['customer_email'] IS NOT NULL"
        severity: CRITICAL
        dimension: completeness
        penalty_weight: 1.0  # Full penalty if fails

      - name: "Valid email format"
        rule: "REGEX_MATCH(row['customer_email'], '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$')"
        severity: CRITICAL
        dimension: validity
        penalty_weight: 1.0

      # WARNING - Nice to have, doesn't affect score
      - name: "Email should be lowercase"
        rule: "row['customer_email'] == LOWER(row['customer_email'])"
        severity: WARNING
        dimension: consistency
        penalty_weight: 0.0  # No penalty

      - name: "Prefer company domain emails"
        rule: "ENDS_WITH(row['customer_email'], '@company.com')"
        severity: WARNING
        dimension: consistency
        penalty_weight: 0.0
```

---

## Configuration File Example

### Current ADRI Standard (Simplified)
```yaml
# adri/standards/invoice_standard.yaml
version: "1.0"
name: "Invoice Processing Standard"

target_fields:
  - name: "invoice_id"
    type: "string"
    mandatory: true

  - name: "amount"
    type: "number"
    mandatory: true
    min: 0
    max: 1000000

  - name: "status"
    type: "string"
    mandatory: true
    allowed_values: ["paid", "pending"]
```

### Enhanced with Explicit Severity
```yaml
# adri/standards/invoice_standard_enhanced.yaml
version: "2.0"
name: "Invoice Processing Standard (Enhanced)"

target_fields:
  - name: "invoice_id"
    type: "string"
    mandatory: true
    validation_rules:
      - name: "Invoice ID required"
        rule: "IS_NOT_NULL"
        severity: CRITICAL
        dimension: completeness
        error_message: "Every invoice must have an ID"

      - name: "Invoice ID format"
        rule: "REGEX_MATCH(row['invoice_id'], '^INV-[0-9]{6}$')"
        severity: CRITICAL
        dimension: validity
        error_message: "Invoice ID must match format INV-XXXXXX"

  - name: "amount"
    type: "number"
    mandatory: true
    validation_rules:
      - name: "Amount required"
        rule: "IS_NOT_NULL"
        severity: CRITICAL
        dimension: completeness

      - name: "Amount must be positive"
        rule: "row['amount'] > 0"
        severity: CRITICAL
        dimension: plausibility
        error_message: "Invoice amounts must be positive"

      - name: "Amount within normal range"
        rule: "row['amount'] < 100000"
        severity: WARNING
        dimension: plausibility
        error_message: "Unusually high amount - please verify"

  - name: "status"
    type: "string"
    mandatory: true
    validation_rules:
      - name: "Status allowed values"
        rule: "VALUE_IN(['paid', 'pending', 'cancelled'])"
        severity: CRITICAL
        dimension: validity
        error_message: "Status must be paid, pending, or cancelled"

      - name: "Status format consistency"
        rule: "row['status'] == LOWER(row['status'])"
        severity: WARNING
        dimension: consistency
        error_message: "Status should be lowercase for consistency"
```

---

## Benefits of Explicit Severity

### 1. Transparency
Users can see exactly which rules affect scores:
```bash
$ adri validate data.csv --show-rules

CRITICAL Rules (affect score):
  ✓ Invoice ID required (completeness)
  ✓ Invoice ID format (validity)
  ✓ Amount must be positive (plausibility)
  ✗ Status allowed values (validity) - 3 failures

WARNING Rules (logged only):
  ✗ Status format consistency (consistency) - 10 warnings
  ✗ Amount within normal range (plausibility) - 2 warnings

Score Impact:
  - CRITICAL failures: -1.96 points
  - WARNING issues: 0 points (logged only)

Final Score: 18.04 / 20 (90.2%)
```

### 2. Customization
Different organizations have different needs:
```yaml
# Conservative Organization (strict)
- name: "Date format consistency"
  rule: "MATCHES_FORMAT(row['date'], 'YYYY-MM-DD')"
  severity: CRITICAL  # They require strict format

# Lenient Organization (flexible)
- name: "Date format consistency"
  rule: "MATCHES_FORMAT(row['date'], 'YYYY-MM-DD')"
  severity: WARNING  # They accept any valid date
```

### 3. Progressive Enforcement
Start lenient, become stricter over time:
```yaml
# Phase 1: New field, just warn
- name: "VAT number format"
  severity: WARNING
  rollout_date: "2025-Q1"

# Phase 2: After 3 months, make critical
- name: "VAT number format"
  severity: CRITICAL
  effective_date: "2025-Q2"
```

### 4. Better Error Messages
Connect rules to business impact:
```yaml
- name: "Payment method required for paid invoices"
  rule: "row['status'] != 'paid' OR row['payment_method'] IS NOT NULL"
  severity: CRITICAL
  dimension: completeness
  error_message: "Paid invoices must specify payment method for accounting audit trail"
  business_impact: "Cannot reconcile payments without this information"
  remediation: "Add payment method: credit_card, bank_transfer, or cash"
```

---

## Implementation Steps

### Step 1: Add Severity to Standard Schema
```yaml
# adri/standards/templates/field_template.yaml
validation_rule_schema:
  name: string (required)
  rule: string (required)
  severity: enum [CRITICAL, WARNING, INFO] (required)  # <-- NEW
  dimension: enum [validity, completeness, consistency, freshness, plausibility] (required)
  error_message: string (optional)
  penalty_weight: float (optional, default: 1.0 for CRITICAL, 0.0 for WARNING)
```

### Step 2: Update Validation Engine
```python
# adri/validator/core/rule_evaluator.py

class ValidationRule:
    def __init__(self, name, rule, severity, dimension):
        self.name = name
        self.rule = rule
        self.severity = severity  # <-- NEW: CRITICAL, WARNING, INFO
        self.dimension = dimension

    def calculate_penalty(self, failure_rate):
        """Calculate score penalty based on severity."""
        if self.severity == "CRITICAL":
            return self.penalty_weight * failure_rate
        elif self.severity == "WARNING":
            return 0  # No score penalty
        elif self.severity == "INFO":
            return 0  # Informational only
        else:
            raise ValueError(f"Unknown severity: {self.severity}")
```

### Step 3: Update Score Calculation
```python
# adri/validator/core/dimension_scorer.py

def calculate_dimension_score(dimension, rules, results):
    """Calculate dimension score considering severity levels."""
    max_score = 20
    total_penalty = 0

    for rule in rules:
        if rule.dimension != dimension:
            continue

        failure_rate = results[rule.name]['failure_rate']

        # Only CRITICAL rules affect score
        if rule.severity == "CRITICAL":
            penalty = rule.calculate_penalty(failure_rate)
            total_penalty += penalty
        elif rule.severity == "WARNING":
            # Log but don't penalize
            log_warning(rule.name, failure_rate)

    return max(0, max_score - total_penalty)
```

### Step 4: Update Reporting
```python
# adri/validator/reporting/report_generator.py

def generate_validation_report(results):
    """Generate report showing severity levels."""
    report = {
        'critical_failures': [],
        'warnings': [],
        'info': []
    }

    for rule_name, result in results.items():
        rule = get_rule_by_name(rule_name)

        if result['failed']:
            if rule.severity == "CRITICAL":
                report['critical_failures'].append({
                    'rule': rule_name,
                    'failures': result['failure_count'],
                    'impact': f"-{result['penalty']:.2f} points"
                })
            elif rule.severity == "WARNING":
                report['warnings'].append({
                    'rule': rule_name,
                    'issues': result['failure_count'],
                    'impact': "No score penalty"
                })

    return report
```

---

## Summary

**What "adding explicit severity levels" means**:

| Aspect | Current (Implicit) | Proposed (Explicit) |
|--------|-------------------|-------------------|
| **Configuration** | Hardcoded in engine | Configurable in YAML |
| **Visibility** | Hidden from users | Clear in standard definition |
| **Customization** | Not possible | Per-organization control |
| **Transparency** | Users don't know why score is what it is | Clear cause-and-effect |

**Three Severity Levels**:
1. **CRITICAL**: Reduces score, must be fixed
2. **WARNING**: Logged only, no score impact
3. **INFO**: Informational, no action needed

**Key Benefit**: Users can SEE and CONTROL which rules affect scoring vs which just provide guidance.

---

## Quick Example

**Before (Implicit)**:
```yaml
# User can't tell if this will affect score
- name: "Status format"
  rule: "LOWER(status)"
```

**After (Explicit)**:
```yaml
# Crystal clear - this is just a warning
- name: "Status format"
  rule: "LOWER(status)"
  severity: WARNING  # <-- No score impact

# This one is critical - will reduce score
- name: "Status allowed values"
  rule: "VALUE_IN(['paid', 'pending'])"
  severity: CRITICAL  # <-- Affects score
```

This makes ADRI's behavior **transparent**, **customizable**, and **understandable**.
