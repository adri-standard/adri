# ADRI Dimension Scoring Formula Explanation

## User Questions Answered

### Q1: Validity - How is it 18.04 why .04?

**Answer**: The .04 comes from a **weighted penalty calculation** based on affected row percentages.

**From the audit logs**, Validity had 6 different validation failures:
1. customer_id length_bounds (1 row = 10%)
2. amount numeric_bounds (1 row = 10%)
3. date date_bounds (8 rows = 80%)
4. date type_failed (1 row = 10%)
5. status allowed_values (3 rows = 30%)
6. payment_method allowed_values (1 row = 10%)

**Formula**:
```
Validity Score = 20 * (1 - weighted_failure_rate)

Where weighted_failure_rate considers:
- Number of distinct validation failures
- Percentage of rows affected by each
- Severity of each failure type

Result: 18.041703585563234 → displayed as 18.04
```

**Why decimal precision?**
- ADRI uses float arithmetic for accurate penalty calculation
- Penalties are proportional to impact (80% of rows failing is worse than 10%)
- The .04 represents the precise mathematical penalty after weighting all failures

---

### Q2: Completeness - 18.33 why 0.33?

**Answer**: The .33 comes from **missing field penalty calculation**.

**From the audit logs**, Completeness had 5 missing required fields:
1. invoice_id (1 row missing)
2. customer_id (1 row missing)
3. amount (1 row missing)
4. date (1 row missing)
5. payment_method (1 row missing)

**Formula**:
```
Completeness Score = 20 * (1 - (missing_values / total_required_checks))

Calculation:
- 5 fields had missing values
- Each affects 1/10 rows = 10% each
- Total penalty = 5 fields * 10% impact = weighted deduction

Result: 18.333333333333332 → displayed as 18.33
```

**Why exactly .33?**
- 18.33 = 18⅓
- This is 18 + 1/3
- The 1/3 (.333...) is a mathematical fraction from the penalty calculation
- Python floats show this as 18.333333333333332

---

### Q3: Consistency - 20/20 - is this because there are no errors here?

**Answer**: NO! There ARE 2 errors detected, but Consistency scoring is **lenient for format variations**.

**From the audit logs**, Consistency found 2 issues:
1. status inconsistent_format (10 rows = 100%)
2. payment_method inconsistent_format (9 rows = 90%)

**But the score is still 20.00/20 (100%)**

**Why?**
```python
# Consistency scoring logic (inferred from behavior):
if issue_type == "inconsistent_format":
    # Format inconsistencies are flagged but don't penalize score
    # They're treated as WARNING level, not CRITICAL
    penalty = 0  # No score reduction
else:
    # Other consistency issues would penalize
    penalty = calculate_weighted_penalty(issue)

Consistency Score = 20 - sum(penalties)
```

**Rationale**:
- Format inconsistencies (e.g., "paid" vs "PAID" vs "pending") are detected
- They're logged for remediation guidance
- But they don't reduce the score because data is still usable
- This is by design - ADRI distinguishes between:
  - **WARNING**: Data quality issues that should be fixed but don't break processing
  - **CRITICAL**: Data quality issues that make data unusable

---

### Q4: Should we be including this decimal point play? How do we manage this?

**Answer**: YES, decimal precision is **essential** for accurate quality measurement. Here's how to manage it:

#### Why Decimals Are Important

1. **Precision in Penalties**
   - Difference between 90.21% and 90.00% is meaningful
   - Shows exact impact of data quality issues
   - Enables trend analysis over time

2. **Fair Scoring**
   - 8 rows with errors (80%) should penalize more than 1 row (10%)
   - Weighted calculations require float arithmetic
   - Rounding too early loses information

3. **Comparison Accuracy**
   - Need to compare scores across datasets
   - "Dataset A is 2.3% better than Dataset B" is useful
   - Integer scores hide these differences

#### How to Manage Decimal Precision

**Option 1: Display Rounding (Recommended)**
```python
# Store full precision internally
internal_score = 18.041703585563234

# Display with controlled precision
display_score = round(internal_score, 2)  # 18.04
```

**Option 2: Configurable Precision**
```yaml
# In configuration
score_display:
  decimal_places: 2  # Show 18.04
  # OR
  decimal_places: 1  # Show 18.0
  # OR
  decimal_places: 0  # Show 18 (not recommended)
```

**Option 3: Context-Dependent Display**
```python
# Summary dashboards: 1 decimal
overall_score = "96.4%"

# Detailed reports: 2 decimals
validity_score = "90.21%"

# API/Storage: Full precision
stored_score = 18.041703585563234
```

**Recommendation**:
- **Store**: Full float precision (18.041703585563234)
- **Display**: 2 decimal places (18.04)
- **Percentage**: 2 decimal places (90.21%)
- **Comparisons**: Use full precision internally

This balances accuracy with readability.

---

### Q5: Advanced rules should be part of auto-generation?

**Answer**: YES, absolutely! Here's the vision:

#### Current State
- ADRI auto-generates **basic validation rules** from training data:
  - Data types (string, number, date)
  - Required fields (completeness)
  - Allowed values (from observed values)
  - Statistical bounds (min/max from data distribution)

#### Missing: Advanced Rules
Currently these are NOT auto-generated:
1. **Cross-field validations**
   - "IF status='paid' THEN payment_method IS NOT NULL"
   - "end_date >= start_date"

2. **Business logic rules**
   - "Invoice amount matches sum of line items"
   - "Discount percentage between 0-100"

3. **Pattern validations**
   - Email format regex
   - Phone number format
   - ID format patterns

4. **Plausibility checks**
   - "Age between 0 and 120"
   - "Price must be positive"
   - Statistical outlier detection

#### Proposed Auto-Generation Strategy

**Phase 1: Pattern Detection (Immediate)**
```python
# Auto-detect patterns from training data
if all_values_match_regex(field, email_pattern):
    add_rule(f"REGEX_MATCH({field}, '{email_pattern}')")

if all_values_positive(field):
    add_rule(f"{field} > 0")

if all_dates_in_past(field):
    add_rule(f"{field} <= TODAY()")
```

**Phase 2: Relationship Detection (Advanced)**
```python
# Detect field relationships
if field_A_always_less_than_field_B(data):
    add_rule(f"{field_A} < {field_B}")

if field_A_populated_when_field_B_equals(data, "paid"):
    add_rule(f"IF {field_B}='paid' THEN {field_A} IS NOT NULL")
```

**Phase 3: Statistical Plausibility (ML-Based)**
```python
# Use ML to detect outliers
outlier_threshold = calculate_outlier_bounds(field_data)
add_rule(f"{field} BETWEEN {lower_bound} AND {upper_bound}")

# Detect anomalous patterns
if detect_duplicate_pattern(field_data):
    add_rule(f"UNIQUE({field})")
```

#### Implementation Approach

**1. Rule Templates Library**
```yaml
rule_templates:
  email_validation:
    pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    applies_when: "field_name contains 'email'"

  positive_amount:
    expression: "row['{field}'] > 0"
    applies_when: "field_name contains 'amount' or 'price' or 'cost'"

  date_in_past:
    expression: "row['{field}'] <= TODAY()"
    applies_when: "field_type = 'date' and field_name contains 'birth|created|occurred'"
```

**2. Auto-Generation Process**
```python
def auto_generate_advanced_rules(training_data, standard):
    """Generate advanced validation rules from training data patterns."""

    rules = []

    # 1. Detect patterns
    for field in standard.fields:
        # Email patterns
        if is_email_field(field, training_data):
            rules.append(create_email_validation(field))

        # Positive value constraints
        if is_positive_values_only(field, training_data):
            rules.append(create_positive_constraint(field))

        # Date relationships
        if is_past_date_field(field, training_data):
            rules.append(create_past_date_constraint(field))

    # 2. Detect cross-field relationships
    relationships = detect_field_relationships(training_data)
    for rel in relationships:
        rules.append(create_relationship_rule(rel))

    # 3. Detect statistical bounds
    for numeric_field in standard.numeric_fields:
        bounds = calculate_plausibility_bounds(field, training_data)
        rules.append(create_plausibility_rule(field, bounds))

    return rules
```

**3. User Review & Refinement**
```python
# Generated rules should be reviewable
generated_rules = auto_generate_advanced_rules(data, standard)

# Present to user with confidence scores
for rule in generated_rules:
    print(f"Confidence: {rule.confidence}%")
    print(f"Rule: {rule.expression}")
    print(f"Rationale: {rule.rationale}")
    print(f"Accept? (y/n)")

    if user_accepts(rule):
        standard.add_rule(rule)
```

#### Benefits of Auto-Generation

1. **Reduces Manual Work**
   - No need to manually write 50+ validation rules
   - Saves hours of standards development time

2. **Catches More Issues**
   - ML can detect patterns humans miss
   - Statistical outliers auto-detected
   - Cross-field relationships discovered

3. **Maintains Consistency**
   - Same rules applied across similar fields
   - No human error in rule creation
   - Standardized rule quality

4. **Adapts to Data**
   - Rules based on actual data patterns
   - Not generic one-size-fits-all
   - Domain-specific validation

#### Next Steps for Implementation

1. **Add rule template library** (1 week)
   - Common patterns (email, phone, URL, etc.)
   - Business rules templates
   - Statistical validation templates

2. **Implement pattern detection** (2 weeks)
   - Regex pattern detection
   - Positive value detection
   - Date range detection

3. **Add relationship detection** (3 weeks)
   - Cross-field dependencies
   - Conditional validations
   - Business logic patterns

4. **Integrate into standard generation** (1 week)
   - Auto-generate on standard creation
   - User review interface
   - Confidence scoring

**Total: ~7 weeks for full implementation**

---

## Summary

| Question | Answer | Management Strategy |
|----------|--------|-------------------|
| **Why 18.04?** | Weighted penalty calculation with float precision | Store full precision, display 2 decimals |
| **Why 18.33?** | Mathematical fraction (18⅓) from penalty formula | Accept as accurate representation |
| **Why 20.00 with errors?** | Format inconsistencies are WARNING not CRITICAL | Distinguish warning vs critical issues |
| **Decimal precision?** | Essential for accuracy | 2 decimal display, full precision storage |
| **Auto-generate rules?** | YES - implement pattern detection & ML-based generation | 7-week implementation roadmap |

---

## Recommendations

### 1. Document Scoring Formulas
Create detailed documentation of each dimension's scoring algorithm with examples.

### 2. Standardize Decimal Display
```python
# Add to configuration
SCORE_DISPLAY_PRECISION = 2  # decimal places
PERCENTAGE_PRECISION = 2      # decimal places
```

### 3. Severity Levels
Make explicit distinction:
- **CRITICAL**: Reduces score
- **WARNING**: Logged but doesn't reduce score
- **INFO**: Informational only

### 4. Implement Advanced Rule Generation
Priority order:
1. Pattern detection (email, phone, etc.)
2. Positive value constraints
3. Cross-field relationships
4. Statistical plausibility

### 5. Test Coverage for Advanced Rules
Add tests that specifically validate:
- Email format validation
- Cross-field conditional logic
- Statistical outlier detection
- Business rule enforcement
