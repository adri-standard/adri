# ADRI Schema Enhancements Documentation

This document describes the schema validation enhancements added to ADRI Enterprise, including pre-commit hooks, schema diff service, and YAML property extensions.

## Table of Contents

1. [Overview](#overview)
2. [Schema Diff Service](#schema-diff-service)
3. [Pre-commit Hooks](#pre-commit-hooks)
4. [Type Patterns (YAML Property)](#type-patterns-yaml-property)
5. [SQL Compatibility (Enterprise YAML Property)](#sql-compatibility-enterprise-yaml-property)
6. [Autotune Integration](#autotune-integration)
7. [Examples](#examples)

## Overview

The schema enhancements provide:

- **Schema Diff Service**: Compare ADRI schema versions and detect breaking/non-breaking changes
- **Pre-commit Hooks**: Validate ADRI schemas before commit to catch issues early
- **Type Patterns**: Domain-specific type validation through YAML configuration
- **SQL Compatibility**: Multi-database reserved word checking (Enterprise)
- **Autotune Integration**: Explain schema changes when autotuning modifies ADRI standards

## Schema Diff Service

### Purpose

The schema diff service compares two versions of an ADRI standard and generates a detailed report of changes, classified by impact level.

### Usage

```python
from adri.utils.schema_diff import compare_schemas, format_diff_report

# Compare two schemas
original_schema = {...}  # Load from file
modified_schema = {...}  # Load from file

diff_result = compare_schemas(
    original_schema,
    modified_schema,
    source_version="v1.0",
    target_version="v1.1"
)

# Check for breaking changes
if diff_result.has_breaking_changes():
    print("⚠️  Warning: Breaking changes detected!")

# Generate report
report = format_diff_report(diff_result)
print(report)
```

### Change Types

- **FIELD_ADDED**: New field added to schema (non-breaking)
- **FIELD_REMOVED**: Field removed from schema (breaking)
- **TYPE_CHANGED**: Field type modified (breaking)
- **CONSTRAINT_CHANGED**: Constraint value modified (depends on direction)
- **VALIDATION_RULE_ADDED**: New validation rule added (breaking)
- **VALIDATION_RULE_REMOVED**: Validation rule removed (non-breaking)
- **DESCRIPTION_CHANGED**: Documentation updated (clarification)
- **METADATA_CHANGED**: Other metadata updated (clarification)

### Impact Levels

- **BREAKING**: Incompatible changes requiring data migration
- **NON_BREAKING**: Backward compatible changes
- **CLARIFICATION**: Documentation-only changes

### Output Formats

- **Text**: Human-readable console output
- **Markdown**: Formatted for documentation
- **Autotune**: Concise format for autotune logs

## Pre-commit Hooks

### Purpose

Pre-commit hooks validate ADRI schemas before they are committed to prevent invalid schemas from entering the codebase.

### Installation

The hook is already configured in `.pre-commit-config.yaml`:

```yaml
- id: validate-adri-schemas
  name: Validate ADRI schema consistency
  entry: python .pre-commit-hooks/validate-adri-schemas.py
  language: system
  files: \.(yaml|yml)$
  pass_filenames: true
```

### What It Validates

- Type/description conflicts
- SQL reserved word usage
- Array type completeness
- Constraint consistency
- Missing or invalid types
- Custom type patterns (if configured)
- SQL dialect compatibility (if configured)

### Usage

The hook runs automatically when you commit YAML files:

```bash
git add ADRI/contracts/my_standard.yaml
git commit -m "Update ADRI standard"
# Hook will validate the schema automatically
```

If validation fails, you'll see:

```
ADRI Schema Validation Report
======================================================================

❌ 1 of 1 schema file(s) failed validation

File: ADRI/contracts/my_standard.yaml
----------------------------------------------------------------------
Found 2 consistency issue(s):

  ERROR Issues (1):
    • customer_id: Field 'customer_id' has type 'string' but description suggests 'integer'
      → Fix the conflict by either:
        1. Changing type from 'string' to 'integer'
        2. Updating the description to match type 'string'

  WARNING Issues (1):
    • ORDER: Field name 'ORDER' is a SQL reserved word
      → Consider renaming to avoid SQL conflicts
```

## Type Patterns (YAML Property)

### Purpose

Domain-specific type validation through YAML configuration. Ensures fields follow naming conventions for their data types.

### Configuration

Add a `type_patterns` section to your ADRI standard:

```yaml
type_patterns:
  # Fields ending with _amount should be float
  float:
    - indicators:
        - "_amount$"
        - "_price$"
        - "_rate$"
      constraints:
        min_value: 0
  
  # Fields ending with _id should be integer
  integer:
    - indicators:
        - "_id$"
        - "_count$"
      constraints:
        min_value: 0
  
  # Fields ending with _date should be date
  date:
    - indicators:
        - "_date$"
        - "_timestamp$"

field_requirements:
  transaction_amount:  # Matches _amount$ pattern
    type: float  # ✅ Correct
    description: Transaction amount
  
  customer_id:  # Matches _id$ pattern
    type: integer  # ✅ Correct
    description: Customer ID
```

### How It Works

1. Validator loads `type_patterns` from YAML
2. For each field, checks if name matches any pattern indicators (regex)
3. If match found, validates that field type matches expected type
4. Reports errors if type doesn't match pattern expectations

### Use Cases

- **Financial Domain**: Ensure _amount, _price, _rate are floats
- **Healthcare Domain**: Ensure patient_id, record_id are integers
- **E-commerce Domain**: Ensure product_code, sku_code are strings

## SQL Compatibility (Enterprise YAML Property)

### Purpose

**Enterprise Feature**: Validates field names against reserved words for multiple SQL dialects to ensure multi-database compatibility.

### Configuration

Add an `sql_compatibility` section to your ADRI standard:

```yaml
sql_compatibility:
  # Target database dialects to validate against
  target_dialects:
    - postgresql
    - mysql
    - oracle
  
  # Strict mode: ERROR on conflicts vs WARNING
  strict_mode: false
  
  # Organization-specific reserved words
  custom_reserved_words:
    - INTERNAL_ID
    - SYSTEM_FLAG

field_requirements:
  customer_id:  # ✅ Safe in all dialects
    type: integer
    description: Customer identifier
  
  # ARRAY:  # ❌ Reserved in PostgreSQL
  #   type: string
```

### Supported Dialects

- **postgresql**: PostgreSQL-specific reserved words
- **mysql**: MySQL-specific reserved words
- **oracle**: Oracle-specific reserved words
- **standard**: ANSI SQL reserved words

### Strict Mode

- **false** (default): Issues are WARNINGs
- **true**: Issues are ERRORs (fails validation)

### Custom Reserved Words

Add organization-specific words to avoid:

```yaml
sql_compatibility:
  custom_reserved_words:
    - INTERNAL_ID  # Your internal naming
    - SYSTEM_FLAG  # Reserved for system use
    - METADATA     # Reserved by your platform
```

## Autotune Integration

### Purpose

When autotune modifies ADRI standards, it now generates and displays a diff report explaining what changed.

### How It Works

1. Before modifying ADRI standard, autotune captures original schema
2. After applying changes, loads modified schema
3. Generates diff using schema diff service
4. Displays concise diff report in console output

### Example Output

```
[AUTO_TUNER] Schema changes applied:
Schema Changes (before_autotune → after_autotune):
  ⚠️  Breaking:
     - email: CONSTRAINT_CHANGED
  ✅ Non-breaking:
     - phone: FIELD_ADDED
  📝 Documentation: 1 update(s)

[AUTO_TUNER] Validating ADRI standard: customer_standard.yaml
[AUTO_TUNER] ✅ ADRI validation passed
```

### Benefits

- **Transparency**: Users see exactly what autotune changed
- **Impact Awareness**: Breaking changes are highlighted
- **Audit Trail**: Changes are logged and can be reviewed
- **Debugging**: Easier to understand tuning behavior

## Divergence Metadata (Workflow Integration)

### Purpose

Field-level divergence metadata enables workflow orchestration systems to distinguish between deterministic fields (stable, rule-based) and AI-generated fields (non-deterministic). This integration helps workflow systems like workflow-runner apply appropriate divergence checking policies.

### Field Properties

Two optional boolean properties can be added to any field requirement:

- **`deterministic`**: Indicates if a field's value should be reproducible across runs with the same inputs
- **`ai_generated`**: Indicates if a field is generated by AI/LLM reasoning

### Usage

```yaml
field_requirements:
  HEALTH_SCORE:
    type: integer
    nullable: false
    is_derived: true
    deterministic: true      # Rule-based derivation (lookup table)
    allowed_values:
      type: categorical
      categories:
        1: {description: "Critical"}
        2: {description: "Poor"}
        3: {description: "Fair"}
        4: {description: "Good"}
        5: {description: "Excellent"}
  
  AI_STATUS_SUMMARY:
    type: string
    nullable: false
    ai_generated: true       # Generated by LLM
    deterministic: false     # Non-deterministic output
    min_length: 50
  
  ITEM_ID:
    type: string
    nullable: false
    # No divergence metadata - default handling
```

### Validation Rules

ADRI validates divergence metadata to catch common issues:

1. **Type Validation**: Both properties must be boolean if present
   ```yaml
   deterministic: "true"  # ❌ ERROR: Must be boolean, not string
   deterministic: true    # ✅ Correct
   ```

2. **Mutual Exclusivity**: Warns if both properties are true
   ```yaml
   deterministic: true    # ⚠️ WARNING: Contradictory
   ai_generated: true     # These should not both be true
   ```

3. **Consistency with is_derived**: Warns if derived field is marked non-deterministic
   ```yaml
   is_derived: true       # ⚠️ WARNING: Derived fields with
   deterministic: false   # explicit rules are typically deterministic
   ```

### Inference Suggestions

ADRI's validator provides helpful suggestions for fields that might benefit from divergence metadata:

**For derived fields with explicit rules:**
```yaml
RISK_LEVEL:
  type: string
  is_derived: true
  allowed_values: ["LOW", "MEDIUM", "HIGH"]
  # Suggestion: Consider adding deterministic=true
```

**For AI-related field names:**
```yaml
AI_SUMMARY:  # Name suggests AI generation
  type: string
  # Suggestion: Consider adding ai_generated=true and deterministic=false

GPT_RECOMMENDATION:  # Name contains "gpt"
  type: string
  # Suggestion: Consider adding ai_generated=true
```

The validator looks for these naming patterns:
- `ai_*`, `llm_*`, `gpt_*` prefixes
- Keywords: `summary`, `rationale`, `recommendation`, `generated`

### Semantic Definitions

**deterministic: true**
- Field value is reproducible given same inputs
- Calculated via explicit rules, formulas, or lookup tables
- Examples: HEALTH_SCORE (lookup), RISK_LEVEL (conditional logic), calculated metrics
- Workflow expectation: Should have 0-5% variance across replay runs

**ai_generated: true**
- Field value generated by AI/LLM reasoning
- Non-reproducible due to model non-determinism and temperature settings
- Examples: AI_STATUS_SUMMARY, AI_RECOMMENDATIONS, RISK_RATIONALE
- Workflow expectation: Can be excluded from divergence checking or use relaxed thresholds

**Neither specified:**
- Default behavior depends on workflow configuration
- Typically uses moderate divergence thresholds (e.g., 10%)

### Integration with Workflow-Runner

This metadata enables workflow-runner's `StepDivergenceChecker` to implement intelligent policies:

```python
# Example: How workflow-runner uses the metadata
def _should_check_field(self, field_name: str, adri_metadata: dict) -> tuple[bool, float]:
    ai_generated = adri_metadata.get('ai_generated', False)
    deterministic = adri_metadata.get('deterministic')
    
    if ai_generated:
        # Policy: Exclude AI fields from divergence checking
        return (False, 0.0)
    elif deterministic is True:
        # Policy: Use strict threshold for deterministic fields
        return (True, 0.05)  # 5% threshold
    elif deterministic is False:
        # Policy: Use relaxed threshold
        return (True, 0.20)  # 20% threshold
    else:
        # Policy: Default moderate threshold
        return (True, 0.10)  # 10% threshold
```

### Benefits

1. **Intelligent Divergence Checking**: Workflows can distinguish field types and apply appropriate policies
2. **Self-Documenting**: Makes field expectations explicit in the standard
3. **Quality Improvement**: Better replay validation for deterministic workflows
4. **Flexibility**: Workflows can implement their own policies based on metadata

### Best Practices

1. **Mark deterministic fields explicitly**: If a field uses a lookup table or explicit formula, mark it `deterministic: true`

2. **Mark AI fields explicitly**: If a field is generated by an LLM, mark it `ai_generated: true` and `deterministic: false`

3. **Be consistent**: Apply metadata consistently across similar fields in your standards

4. **Review inference suggestions**: Pay attention to validator warnings suggesting metadata additions

5. **Document expectations**: Use metadata to communicate replay expectations to workflow teams

### Backward Compatibility

- Both properties are **completely optional**
- Existing standards without divergence metadata continue to work unchanged
- No breaking changes to ADRI validation
- Workflows without divergence checking ignore the metadata

### Example: Product Roadmap Standard

```yaml
contracts:
  id: product-roadmap-v1
  name: Product Roadmap Standard
  version: 1.0.0
  description: Product roadmap with divergence metadata

requirements:
  dimension_requirements:
    validity:
      weight: 5
      field_requirements:
        ITEM_ID:
          type: string
          nullable: false
          description: Unique roadmap item identifier
          # No divergence metadata - default handling
        
        HEALTH_SCORE:
          type: integer
          nullable: false
          is_derived: true
          deterministic: true  # Lookup table - deterministic
          description: Calculated health score
          allowed_values:
            type: categorical
            categories:
              1: {description: "Critical - high risk"}
              2: {description: "Poor - needs attention"}
              3: {description: "Fair - acceptable"}
              4: {description: "Good - on track"}
              5: {description: "Excellent - exceeding goals"}
        
        RISK_LEVEL:
          type: string
          nullable: false
          is_derived: true
          deterministic: true  # Conditional logic - deterministic
          description: Risk assessment level
          allowed_values: ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        
        AI_STATUS_SUMMARY:
          type: string
          nullable: false
          ai_generated: true       # LLM-generated
          deterministic: false     # Non-deterministic
          description: AI-generated status summary
          min_length: 50
          max_length: 500
        
        AI_RISK_RATIONALE:
          type: string
          nullable: true
          ai_generated: true       # LLM-generated
          deterministic: false     # Non-deterministic
          description: AI explanation of risk assessment
        
        OWNER_NAME:
          type: string
          nullable: false
          description: Item owner name
          # No divergence metadata - this is data entry, not derived

  overall_minimum: 70
```

### Testing

ADRI includes comprehensive test coverage for divergence metadata:

```bash
# Run divergence metadata tests
cd /path/to/adri-enterprise
python -m pytest tests/unit/contracts/test_divergence_metadata.py -v
python -m pytest tests/unit/contracts/test_divergence_metadata_integration.py -v
```

### Future Enhancements

Potential future additions:

- **Divergence thresholds**: Allow standards to specify recommended thresholds
- **Replay policies**: Embedded policy recommendations for workflow systems
- **Provenance tracking**: Link to tools/models that generate fields
- **Confidence scores**: Metadata about expected variability ranges

## Examples

### Example 1: Financial Domain Standard

See `examples/financial_domain_standard.yaml`:

```yaml
type_patterns:
  float:
    - indicators:
        - "_amount$"
        - "_price$"
        - "_rate$"

field_requirements:
  transaction_amount:  # Matches _amount$ → must be float
    type: float
    description: Transaction amount in USD
    min_value: 0.01
  
  interest_rate:  # Matches _rate$ → must be float
    type: float
    description: Annual interest rate
    min_value: 0
    max_value: 100
```

### Example 2: Multi-Database Enterprise

See `examples/multi_database_enterprise_standard.yaml`:

```yaml
sql_compatibility:
  target_dialects:
    - postgresql
    - mysql
    - oracle
  strict_mode: false

field_requirements:
  customer_id:  # ✅ Safe in all dialects
    type: integer
    description: Customer identifier
  
  # Examples of conflicts (commented out):
  # ARRAY:  # Reserved in PostgreSQL
  # ACCESSIBLE:  # Reserved in MySQL  
  # MINUS:  # Reserved in Oracle
```

### Example 3: Healthcare Domain

```yaml
type_patterns:
  integer:
    - indicators:
        - "^patient_id$"
        - "^record_number$"
        - "_count$"
      constraints:
        min_value: 1
  
  date:
    - indicators:
        - "admission_date"
        - "discharge_date"
        - "birth_date"
  
  string:
    - indicators:
        - "diagnosis_code"
        - "patient_name"
        - "medical_record_number"

field_requirements:
  patient_id:  # Must be integer (matches pattern)
    type: integer
    description: Unique patient identifier
    min_value: 1
  
  admission_date:  # Must be date (matches pattern)
    type: date
    description: Hospital admission date
  
  diagnosis_code:  # Must be string (matches pattern)
    type: string
    description: ICD-10 diagnosis code
    pattern: "^[A-Z][0-9]{2}(\\.[0-9]{1,2})?$"
```

## Best Practices

### 1. Use Type Patterns for Domain Consistency

Define type patterns at the domain level to ensure consistency across all standards:

```yaml
# Financial domain pattern
type_patterns:
  float:
    - indicators: ["_amount$", "_balance$", "_fee$"]
      constraints:
        min_value: 0
```

### 2. Enable SQL Compatibility for Multi-Database Projects

If your data will be used in multiple databases:

```yaml
sql_compatibility:
  target_dialects: [postgresql, mysql]
  strict_mode: true  # Fail on conflicts
```

### 3. Test with Pre-commit Hooks

Always test your schema changes:

```bash
# Stage your changes
git add ADRI/contracts/my_standard.yaml

# Dry-run the pre-commit hook
pre-commit run validate-adri-schemas --files ADRI/contracts/my_standard.yaml

# Fix any issues, then commit
git commit -m "Update ADRI standard"
```

### 4. Review Schema Diffs After Autotune

When autotune modifies standards, review the diff output:

```
[AUTO_TUNER] Schema changes applied:
Schema Changes (before_autotune → after_autotune):
  ⚠️  Breaking:
     - email: TYPE_CHANGED
```

If breaking changes are unexpected, review and potentially rollback.

## Testing

### Run Schema Diff Tests

```bash
cd /Users/thomas/github/verodat/adri-enterprise
python -m pytest tests/test_schema_diff.py -v
```

### Test Validation with Examples

```bash
# Test type patterns
python3 -c "
import yaml
from src.adri.utils.schema_consistency_validator import SchemaConsistencyValidator

with open('examples/financial_domain_standard.yaml', 'r') as f:
    spec = yaml.safe_load(f)

validator = SchemaConsistencyValidator()
report = validator.validate(spec)
print(f'Issues: {report.issues_found}')
"

# Test SQL compatibility
python3 -c "
import yaml
from src.adri.utils.schema_consistency_validator import SchemaConsistencyValidator

with open('examples/multi_database_enterprise_standard.yaml', 'r') as f:
    spec = yaml.safe_load(f)

validator = SchemaConsistencyValidator()
report = validator.validate(spec)
print(f'Issues: {report.issues_found}')
"
```

## API Reference

### SchemaConsistencyValidator

```python
class SchemaConsistencyValidator:
    def __init__(self, strict_mode: bool = False)
    def validate(self, adri_spec: Dict[str, Any]) -> SchemaConsistencyReport
    def _load_type_patterns(self, adri_spec: Dict[str, Any]) -> None
    def _load_sql_compatibility(self, adri_spec: Dict[str, Any]) -> None
    def _check_custom_type_patterns(...) -> List[ConsistencyIssue]
    def _check_sql_dialect_conflicts(...) -> List[ConsistencyIssue]
```

### SchemaDiffService

```python
class SchemaDiffService:
    def diff_files(source_path, target_path) -> SchemaDiffResult
    def diff_dicts(source, target) -> SchemaDiffResult
    def generate_report(diff_result, format="text") -> str

# Convenience function
def compare_schemas(source, target) -> SchemaDiffResult
```

### Format Functions

```python
def format_diff_report(diff_result) -> str  # Text format
def format_diff_markdown(diff_result) -> str  # Markdown format
def format_diff_for_autotune(diff_result) -> str  # Concise autotune format
```

## Backward Compatibility

All enhancements are **fully backward compatible**:

- Type patterns are optional (if not present, default validation is used)
- SQL compatibility is optional (if not present, standard SQL check is used)
- Existing ADRI standards work without modification
- Pre-commit hooks skip non-ADRI YAML files
- Schema diff is graceful (doesn't crash autotune if unavailable)

## Migration Guide

### Adding Type Patterns to Existing Standard

1. Add `type_patterns` section at root level:

```yaml
type_patterns:
  integer:
    - indicators: ["_id$", "_count$"]

# Existing field_requirements continue unchanged
field_requirements:
  customer_id:
    type: integer
    description: Customer ID
```

2. Validate the standard:

```bash
python .pre-commit-hooks/validate-adri-schemas.py ADRI/contracts/your_standard.yaml
```

### Enabling SQL Compatibility

1. Add `sql_compatibility` section:

```yaml
sql_compatibility:
  target_dialects: [postgresql, mysql]
  strict_mode: false
```

2. Review validation report for conflicts
3. Rename fields if necessary to avoid reserved words

## Troubleshooting

### Pre-commit Hook Not Running

Ensure pre-commit is installed:

```bash
pip install pre-commit
pre-commit install
```

### Schema Diff Not Available in Autotune

Ensure adri-enterprise is in the correct location:

```
/Users/thomas/github/verodat/
  ├── adri-enterprise/
  │   └── src/
  │       └── adri/
  │           └── utils/
  │               └── schema_diff.py
  └── workflow-runner/
      └── runner/
          └── runtime/
              └── auto_tuner.py
```

### Type Pattern Not Matching

Type patterns use regex. Test your pattern:

```python
import re
pattern = "_amount$"
field_name = "transaction_amount"
matches = bool(re.search(pattern, field_name, re.IGNORECASE))
print(f"Pattern '{pattern}' matches '{field_name}': {matches}")
```

### SQL Dialect Not Recognized

Supported dialects:
- `postgresql`
- `mysql`
- `oracle`
- `standard`

Check spelling and lowercase format.

## Performance Considerations

- **Pre-commit hooks**: Run only on changed files (fast)
- **Schema diff**: Compares dictionaries in-memory (very fast)
- **Type patterns**: Regex matching per field (minimal overhead)
- **SQL compatibility**: Set lookups (O(1) per field)

All validation is designed to be fast and non-blocking.

## Future Enhancements

Potential future additions:

- **Schema versioning**: Track schema evolution over time
- **Migration scripts**: Auto-generate migration code for breaking changes
- **Diff visualization**: Web UI for reviewing schema changes
- **Pattern libraries**: Shared type pattern libraries for common domains
- **Custom validators**: Plugin system for domain-specific validation rules

## Support

For issues or questions:

1. Check this documentation
2. Review examples in `examples/` directory
3. Run tests: `pytest tests/test_schema_diff.py -v`
4. Check implementation plan: `schema_enhancements_implementation_plan.md`
