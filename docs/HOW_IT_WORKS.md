# How ADRI Works

Understanding ADRI's five-dimensional quality validation system.

## Table of Contents

1. [Overview](#overview)
2. [The Five Quality Dimensions](#the-five-quality-dimensions)
3. [Auto-Generation Mechanics](#auto-generation-mechanics)
4. [Guard Modes](#guard-modes)
5. [Quality Scoring](#quality-scoring)
6. [Validation Flow](#validation-flow)
7. [Standards System](#standards-system)

## Overview

ADRI validates data quality across **five dimensions**, each measuring a different aspect of data reliability:

1. **Validity** - Data types and formats
2. **Completeness** - Required fields and missing data
3. **Consistency** - Cross-field relationships
4. **Accuracy** - Value ranges and patterns
5. **Timeliness** - Data freshness

Each dimension contributes to an **overall quality score** (0-100). If the score is too low, ADRI blocks execution or warns based on your guard mode.

## The Five Quality Dimensions

### 1. Validity

**What it checks**: Data conforms to expected types and formats.

**Examples**:
- Email must match email pattern
- Age must be an integer, not a string
- Date must be in ISO format
- Phone must match phone number pattern

**Common Issues**:
```python
# ❌ Invalid type
{"age": "twenty-five"}  # Expected: int, got: str

# ❌ Invalid format
{"email": "notanemail"}  # Expected: valid email format

# ❌ Invalid date
{"signup": "01/15/2024"}  # Expected: ISO format (2024-01-15)
```

**ADRI Standard Example**:
```yaml
fields:
  email:
    type: string
    pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"

  age:
    type: integer

  signup_date:
    type: date
```

**Scoring**: Based on percentage of fields with correct types and formats.

### 2. Completeness

**What it checks**: All required fields are present with non-null values.

**Examples**:
- Customer ID must not be null
- All required columns must exist
- No missing values in required fields
- Arrays must have minimum length

**Common Issues**:
```python
# ❌ Missing field
{"name": "Alice"}  # Missing required 'email' field

# ❌ Null value
{"customer_id": None, "email": "alice@example.com"}  # ID is null

# ❌ Empty array
{"items": []}  # Required minimum 1 item
```

**ADRI Standard Example**:
```yaml
fields:
  customer_id:
    type: integer
    required: true  # Must be present and non-null

  email:
    type: string
    required: true

  items:
    type: array
    required: true
    min_length: 1
```

**Scoring**: Based on percentage of required fields that are present and non-null.

### 3. Consistency

**What it checks**: Data relationships and cross-field rules are satisfied.

**Examples**:
- End date must be after start date
- Total must equal sum of line items
- Discount must not exceed price
- Foreign keys must reference valid records

**Common Issues**:
```python
# ❌ Date inconsistency
{
    "start_date": "2024-01-15",
    "end_date": "2024-01-10"  # End before start
}

# ❌ Calculation inconsistency
{
    "subtotal": 100,
    "tax": 10,
    "total": 105  # Should be 110
}

# ❌ Logical inconsistency
{
    "age": 15,
    "has_drivers_license": true  # Too young to drive
}
```

**ADRI Standard Example**:
```yaml
fields:
  start_date:
    type: date
    required: true

  end_date:
    type: date
    required: true

  # Cross-field validation
  rules:
    - name: "End after start"
      expression: "end_date > start_date"
      severity: "critical"
```

**Scoring**: Based on percentage of cross-field rules that pass.

### 4. Accuracy

**What it checks**: Values are within expected ranges and patterns.

**Examples**:
- Age between 0 and 120
- Price is positive
- Percentage between 0 and 100
- String length within limits

**Common Issues**:
```python
# ❌ Out of range
{"age": -5}  # Negative age

# ❌ Impossible value
{"percentage": 150}  # Over 100%

# ❌ Too long
{"name": "A" * 1000}  # Exceeds max length

# ❌ Negative when positive required
{"price": -10.50}  # Price must be positive
```

**ADRI Standard Example**:
```yaml
fields:
  age:
    type: integer
    min_value: 0
    max_value: 120

  percentage:
    type: number
    min_value: 0
    max_value: 100

  price:
    type: number
    min_value: 0.01

  name:
    type: string
    min_length: 1
    max_length: 100
```

**Scoring**: Based on percentage of values within acceptable ranges.

### 5. Timeliness

**What it checks**: Data is current and not stale.

**Examples**:
- Record created within last 30 days
- Transaction not older than 1 year
- Cache data not expired
- Real-time feed data is recent

**Common Issues**:
```python
# ❌ Stale data
{
    "customer_id": 123,
    "last_updated": "2020-01-01"  # 4+ years old
}

# ❌ Future date
{
    "transaction_date": "2030-01-01"  # In the future
}

# ❌ Expired
{
    "cache_timestamp": "2024-01-01",
    "ttl_seconds": 3600  # Expired hours ago
}
```

**ADRI Standard Example**:
```yaml
fields:
  created_at:
    type: date
    required: true
    max_age_days: 30  # Must be within last 30 days

  transaction_date:
    type: date
    required: true
    max_age_days: 365
    future_allowed: false  # No future dates
```

**Scoring**: Based on percentage of date fields within acceptable age.

## Auto-Generation Mechanics

ADRI automatically generates quality standards on first successful run.

### What Gets Analyzed

**1. Field Discovery**
- Identifies all fields/columns
- Determines field names
- Detects nested structures

**2. Type Inference**
- Detects data types (int, float, string, date, bool)
- Identifies patterns (email, phone, URL)
- Recognizes enums and categories

**3. Range Detection**
- Calculates min/max for numeric fields
- Determines string length ranges
- Identifies date ranges

**4. Completeness Analysis**
- Identifies which fields always have values
- Marks consistently populated fields as required
- Detects optional fields

**5. Pattern Recognition**
- Email formats
- Phone number formats
- Date formats
- URL patterns
- Custom regex patterns

### Generation Process

```python
# Step 1: First run with good data
@adri_protected(contract="customer_data", data_param="customers")
def process_customers(customers):
    return analyze(customers)

# Step 2: ADRI profiles the data
# - Analyzes field types
# - Detects patterns
# - Calculates ranges
# - Identifies requirements

# Step 3: Generates standard
# Saved to: ADRI/dev/contracts/process_customers_customers_standard.yaml

# Step 4: Future runs validate against standard
```

### Customization After Generation

Generated standards are starting points. Edit the YAML to:

- Tighten or loosen ranges
- Add cross-field validation
- Include domain-specific rules
- Adjust timeliness requirements

## Guard Modes

ADRI offers two operational modes:

### Block Mode (Default)

**Behavior**: Raises exception on quality failure

```python
@adri_protected(contract="data", data_param="data", on_failure="raise")
def strict_function(data):
    return results
```

**Use when**:
- Data quality is mission-critical
- Bad data would cause downstream errors
- Fail-fast approach is preferred
- Production environments

**Exception Details**:
```python
adri.validator.exceptions.DataQualityException:
Data quality too low for reliable execution

Quality Score: 67.3/100 (Required: 80.0/100)

Issues:
- Validity: 3 fields with invalid types
- Completeness: 2 required fields missing
- Accuracy: 5 values out of range
```

### Warn Mode

**Behavior**: Logs warning, continues execution

```python
@adri_protected(contract="data", data_param="data", on_failure="warn")
def lenient_function(data):
    return results
```

**Use when**:
- Developing and testing
- Quality issues are acceptable
- Visibility without disruption desired
- Graceful degradation preferred

**Warning Output**:
```
⚠️  ADRI Protection: WARNING
📊 Quality Score: 67.3/100 (Target: 80.0/100)
⚠️  Executing despite quality issues (warn mode)
```

## Quality Scoring

### Score Calculation

Each dimension receives a score from 0-20:

```
Overall Score = Validity + Completeness + Consistency + Accuracy + Timeliness
              = 20      + 20           + 20          + 20       + 20
              = 100 (maximum)
```

### Dimension Scoring

**Validity** (0-20):
```
score = (valid_fields / total_fields) * 20
```

**Completeness** (0-20):
```
score = (present_required_fields / total_required_fields) * 20
```

**Consistency** (0-20):
```
score = (passing_rules / total_rules) * 20
```

**Accuracy** (0-20):
```
score = (values_in_range / total_values) * 20
```

**Timeliness** (0-20):
```
score = (fresh_dates / total_dates) * 20
```

### Default Threshold

Minimum acceptable score: **80/100**

This means:
- ✅ All dimensions perfect (20+20+20+20+20) = 100 → Pass
- ✅ One dimension weak (15+20+20+20+20) = 95 → Pass
- ✅ Two dimensions weak (15+15+20+20+20) = 90 → Pass
- ⚠️  Three dimensions weak (15+15+15+20+20) = 85 → Pass
- ❌ Four dimensions weak (15+15+15+15+20) = 80 → Pass (barely)
- ❌ Multiple issues (15+15+15+15+15) = 75 → Fail

### Custom Thresholds

Adjust per function:

```python
# More strict
@adri_protected(data_param="data", min_score=90.0)
def critical_function(data):
    return results

# More lenient
@adri_protected(data_param="data", min_score=70.0)
def flexible_function(data):
    return results
```

## Validation Flow

### Step-by-Step Process

1. **Function Called**
   ```python
   result = process_customers(customer_data)
   ```

2. **Decorator Intercepts**
   - Extracts data parameter
   - Looks for standard

3. **Standard Resolution**
   - Check for existing standard
   - If none, auto-generate from data
   - Load standard definition

4. **Quality Assessment**
   - Run validity checks
   - Run completeness checks
   - Run consistency checks
   - Run accuracy checks
   - Run timeliness checks

5. **Score Calculation**
   - Calculate dimension scores
   - Calculate overall score
   - Compare to threshold

6. **Decision Point**
   - Score ≥ threshold → Allow execution
   - Score < threshold:
     - Block mode → Raise exception
     - Warn mode → Log warning, continue

7. **Logging**
   - Log assessment results
   - Save detailed report
   - Record for audit

8. **Function Execution**
   - If allowed, execute function
   - Return results

### Caching

ADRI caches standards for performance:
- Standards loaded once per session
- Assessments reuse validation logic
- No redundant file I/O

## Standards System

### Standard Structure

```yaml
standard:
  name: "customer_data"
  version: "1.0.0"
  description: "Customer data quality standard"

  # Field definitions (validity, completeness, accuracy)
  fields:
    customer_id:
      type: integer
      required: true
      min_value: 1

  # Cross-field rules (consistency)
  rules:
    - name: "End after start"
      expression: "end_date > start_date"

  # Timeliness requirements
  timeliness:
    max_age_days: 30
```

### Standard Location

**Project standards**:
```
ADRI/dev/contracts/
```

**User standards**:
```
~/ADRI/dev/contracts/
```

**Bundled standards** (shipped with ADRI):
```
~/.adri/bundled/
```

### Standard Versioning

Standards support semantic versioning:

```yaml
standard:
  name: "customer_data"
  version: "2.1.0"  # major.minor.patch
```

**Version compatibility**:
- Major version changes: Breaking changes
- Minor version changes: Backward compatible additions
- Patch version changes: Bug fixes

## Next Steps

- [Getting Started](GETTING_STARTED.md) - Hands-on tutorial
- [Framework Patterns](FRAMEWORK_PATTERNS.md) - Framework integration
- [CLI Reference](CLI_REFERENCE.md) - Command-line tools
- [Architecture](ARCHITECTURE.md) - System architecture
- [FAQ](FAQ.md) - Common questions

---

**Protect your agents with five-dimensional quality validation.**
