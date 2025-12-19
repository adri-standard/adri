# Schema Validation in ADRI

## Overview

ADRI's schema validation ensures data field names match contract requirements **before** quality assessment begins. This prevents silent failures where validation rules don't execute due to field name mismatches.

## How It Works

### The Problem
When data field names don't match contract field requirements exactly, validation rules cannot execute:

```python
# Contract expects:
field_requirements:
  customer_id: {type: string}
  email: {type: string}

# But data has:
pd.DataFrame({'CUSTOMER_ID': [...], 'EMAIL': [...]})

# Result: Validation rules DON'T run → Perfect score but no validation! ❌
```

### The Solution

ADRI automatically detects and fixes field name mismatches:

**DEFAULT Behavior (strict_case_matching: false)**
- Auto-renames data columns to match contract case
- Validation rules execute successfully
- User-friendly and flexible

**STRICT Mode (strict_case_matching: true)**
- Requires exact case match
- Raises CRITICAL errors on case mismatch
- Enforces strict data governance

## Configuration

### In ADRI/config.yaml

```yaml
adri:
  environments:
    development:
      schema_validation:
        strict_case_matching: false  # Default: auto-fix case mismatches
    
    production:
      schema_validation:
        strict_case_matching: false  # Can enable strict mode per environment
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `strict_case_matching` | boolean | `false` | When `false`, auto-fixes case mismatches. When `true`, requires exact match. |

## Behavior Modes

### Mode 1: Auto-Fix (Default)

**When:** `strict_case_matching: false` (default)

**Behavior:**
- Detects case-insensitive matches automatically
- Renames DATA columns to match CONTRACT case
- No warnings generated for case mismatches
- Validation rules execute successfully

**Example:**
```python
# Contract defines:
field_requirements:
  project_id: {type: string}
  client: {type: string}

# User sends data with wrong case:
data = pd.DataFrame({
    'PROJECT_ID': ['P001'],
    'CLIENT': ['ClientA']
})

# ADRI auto-fixes internally:
# data becomes: {'project_id': ['P001'], 'client': ['ClientA']}

# Result:
# ✅ Validation rules run on correctly-named fields
# ✅ Quality assessment proceeds normally
# ✅ No errors or warnings
```

### Mode 2: Strict Matching

**When:** `strict_case_matching: true`

**Behavior:**
- Requires exact case match between data and contract
- Generates CRITICAL errors on case mismatch
- Blocks execution with detailed error message
- Enforces strict data governance

**Example:**
```python
# With strict_case_matching: true

# Contract defines:
field_requirements:
  project_id: {type: string}

# User sends:
data = pd.DataFrame({'PROJECT_ID': ['P001']})

# Result:
# ❌ CRITICAL: Field case mismatch detected
# ❌ Validation blocked
# ℹ️ Error shows: "PROJECT_ID should be project_id"
```

## What Gets Changed?

**IMPORTANT:** ADRI changes the **DATA**, NOT the **CONTRACT**.

- **Contract = Source of Truth**: Defines the standard field names (unchanged)
- **Data = Variable**: Gets normalized to match the contract
- **Result**: Validation rules execute on correctly-named fields

```python
# Flow visualization:

┌─────────────────────────┐
│ CONTRACT (Unchanged)    │
│ - project_id            │ ← Standard definition
│ - client                │
└─────────────────────────┘
           ↓
     (Auto-fix applies)
           ↓
┌─────────────────────────┐
│ DATA (Auto-renamed)     │
│ Was: PROJECT_ID, CLIENT │ → Gets normalized
│ Now: project_id, client │
└─────────────────────────┘
           ↓
    ✅ Validation runs
```

## Integration Points

### 1. Assessment Engine
Schema validation runs automatically in `DataQualityAssessor.assess()`:
- Runs BEFORE dimension assessments
- Auto-fix applied if enabled
- Results stored in `result.metadata['schema_validation']`

### 2. Decorator
The `@adri_protected` decorator leverages schema validation:
```python
@adri_protected(contract='customer_data')
def process_customers(data):
    # Auto-fix ensures validation runs successfully
    return processed_data
```

### 3. Audit Logging
Schema validation results logged to `adri_failed_validations.jsonl`:
- Dimension: `schema`
- Issue Type: `FIELD_CASE_MISMATCH` (in strict mode)
- Includes auto-fix suggestions

## Metadata Structure

Schema validation results are stored in assessment metadata:

```python
result.metadata['schema_validation'] = {
    'exact_matches': 4,
    'case_insensitive_matches': 0,  # 0 after auto-fix
    'total_standard_fields': 4,
    'total_data_fields': 4,
    'match_percentage': 100.0,  # 100% after auto-fix
    'warnings': [],  # Empty after auto-fix
    'matched_fields': ['project_id', 'client', 'status', 'amount'],
    'unmatched_standard_fields': [],
    'unmatched_data_fields': []
}
```

## User Experience

### Before Schema Validation (Old Behavior)
```
User sends: {'PROJECT_ID': 'P001'}
Contract expects: {'project_id': ...}
Result: Validity: 0.0/20 (no validation ran)
User confusion: "Why 0.0? My data looks fine!"
```

### After Schema Validation (New Behavior)
```
User sends: {'PROJECT_ID': 'P001'}
Contract expects: {'project_id': ...}
Auto-fix: Renames to {'project_id': 'P001'}
Result: Validity: 20.0/20 (validation ran successfully)
User happy: "It just works!"
```

## When to Use Strict Mode

Enable `strict_case_matching: true` when:

1. **Regulatory Compliance**: Financial/healthcare data with strict governance
2. **API Contracts**: Enforcing exact field names for system integration
3. **Data Quality Training**: Teaching users proper field naming conventions
4. **Production Rigor**: Requiring exact adherence to data contracts

## Examples

### Example 1: Flexible Development

```yaml
# ADRI/config.yaml - Development environment
development:
  schema_validation:
    strict_case_matching: false  # Allow any case
```

```python
# Users can send data in any case format
data1 = pd.DataFrame({'customer_id': ['C001']})  # ✅ Works
data2 = pd.DataFrame({'CUSTOMER_ID': ['C001']})  # ✅ Works  
data3 = pd.DataFrame({'Customer_Id': ['C001']})  # ✅ Works

# All get auto-normalized to contract case
```

### Example 2: Strict Production

```yaml
# ADRI/config.yaml - Production environment
production:
  schema_validation:
    strict_case_matching: true  # Enforce exact case
```

```python
# Only exact match allowed
data1 = pd.DataFrame({'customer_id': ['C001']})  # ✅ Works
data2 = pd.DataFrame({'CUSTOMER_ID': ['C001']})  # ❌ CRITICAL ERROR
data3 = pd.DataFrame({'Customer_Id': ['C001']})  # ❌ CRITICAL ERROR
```

## Migration Guide

### Updating Existing Code

**No changes required!** Schema validation is enabled by default with auto-fix.

Existing code will automatically benefit from:
- Case-insensitive field matching
- Clear error messages when fields don't match
- Validation rules executing successfully

### Testing Considerations

If you have tests that depend on field case:
1. Tests expecting strict matching: Set `strict_case_matching: true` in test config
2. Tests expecting flexible matching: No changes needed (default behavior)

## Troubleshooting

### Issue: "Validity score is 0.0 with no errors"

**Cause:** Field names don't match contract (and auto-fix didn't work)

**Solution:**
1. Check `result.metadata['schema_validation']` for details
2. Review `warnings` list for mismatch information
3. Verify contract field names match your data

### Issue: "CRITICAL error in strict mode"

**Cause:** Exact case match required but not provided

**Solution:**
1. Rename data columns to match contract exactly
2. OR disable strict mode: `strict_case_matching: false`
3. Check error message for specific field corrections needed

## Best Practices

1. **Development**: Use `strict_case_matching: false` for flexibility
2. **Production**: Consider your governance requirements
3. **Contracts**: Use clear, consistent field naming (e.g., snake_case)
4. **Monitoring**: Review `schema_validation` metadata in audit logs
5. **Training**: Start flexible, enable strict mode as teams mature

## See Also

- [Data Contracts](DATA_CONTRACTS.md) - Contract structure and requirements
- [Configuration Guide](GETTING_STARTED.md) - Environment setup
- [Audit Logging](VALIDATION_REPORT.md) - Log structure and analysis
