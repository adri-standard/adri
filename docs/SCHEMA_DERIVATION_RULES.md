# Schema-Based Category Derivation Rules

## Overview

ADRI Enterprise now supports **enhanced allowed_values** with schema-based derivation rules. This feature transforms categorical field definitions from simple lists into rich business logic specifications that enable deterministic AI categorizations.

## Problem Statement

Traditional ADRI standards define categorical fields using simple `allowed_values` lists:

```yaml
RISK_LEVEL:
  type: string
  allowed_values: [Critical, High, Medium, Low]
```

**Limitation:** This only defines *what* values are valid, not *how* to derive them. Categorization logic ends up scattered across:
- Prompt instructions (duplicated, inconsistent)
- Metadata sections (not enforceable)
- External documentation (disconnected from schema)

**Result:** Non-deterministic AI outputs with 20%+ divergence rates.

## Solution: Enhanced Allowed Values

Enhanced allowed_values transform categorical definitions into first-class schema elements with:

1. **Category Definitions** - Business logic descriptions of what each category means
2. **Precedence** - Evaluation order for mutually exclusive categories
3. **Derivation Rules** - Explicit logic for when to apply each category
4. **Backward Compatibility** - Simple list format still supported

## Schema Structure

### Enhanced Format

```yaml
RISK_LEVEL:
  type: string
  is_derived: true  # Marks field as using derivation logic
  allowed_values:
    Critical:
      definition: "Regulatory/compliance risk with execution challenges"
      precedence: 1  # Evaluated first (lower = higher priority)
      derivation_rule:
        type: ordered_conditions
        inputs: [project_status, priority_order]
        logic: "IF project_status = 'At Risk' AND priority_order = 1"
      examples:
        - "Top priority project that is behind schedule"
      metadata:
        severity: critical
    
    High:
      definition: "Highest priority OR at risk project"
      precedence: 2
      derivation_rule:
        type: ordered_conditions
        inputs: [priority_order, project_status]
        logic: "IF priority_order = 1 OR project_status = 'At Risk'"
    
    Medium:
      definition: "Active project not in top priority or at risk"
      precedence: 3
      derivation_rule:
        type: ordered_conditions
        inputs: [project_status]
        logic: "IF project_status = 'Active'"
    
    Low:
      definition: "Default category for other statuses"
      precedence: 4
      derivation_rule:
        type: ordered_conditions
        inputs: []
        logic: "DEFAULT"
```

### Simple Format (Backward Compatible)

```yaml
RISK_LEVEL:
  type: string
  allowed_values: [Critical, High, Medium, Low]  # Still supported
```

## Field Structure Reference

### is_derived (optional)
- **Type:** boolean
- **Purpose:** Marks field as using derivation logic
- **Rules:** 
  - If `true`, `allowed_values` must use enhanced dict format
  - If `false` or omitted, simple list format is allowed

### allowed_values
- **Type:** `List[str]` OR `Dict[str, CategoryDefinition]`
- **Purpose:** Define valid categorical values and their derivation logic

### CategoryDefinition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `definition` | string | Yes | Human-readable description of what this category means |
| `precedence` | integer | Yes | Evaluation order (lower = higher priority, must be >= 1) |
| `derivation_rule` | DerivationRule | No | Logic for deriving this category value |
| `examples` | List[string] | No | Example scenarios for this category |
| `metadata` | dict | No | Additional context or metadata |

### DerivationRule

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Type of derivation logic (e.g., "ordered_conditions", "formula") |
| `inputs` | List[string] | Yes | Input field names this rule depends on |
| `logic` | string | Yes | Condition expression or formula |
| `metadata` | dict | No | Additional context or metadata |

## Derivation Rule Types

### ordered_conditions
Evaluates categories in precedence order until a condition matches:

```yaml
derivation_rule:
  type: ordered_conditions
  inputs: [status, priority]
  logic: "IF status = 'Critical' AND priority = 1"
```

### formula
Mathematical or logical formula:

```yaml
derivation_rule:
  type: formula
  inputs: [field1, field2]
  logic: "field1 + field2 > 100"
```

### direct_mapping
Direct value-to-category mapping:

```yaml
derivation_rule:
  type: direct_mapping
  inputs: [source_field]
  logic: "MAP source_field TO category"
```

## Usage Examples

### Example 1: Project Risk Classification

```yaml
requirements:
  field_requirements:
    RISK_LEVEL:
      type: string
      is_derived: true
      nullable: false
      allowed_values:
        Critical:
          definition: "Top priority project with active risks"
          precedence: 1
          derivation_rule:
            type: ordered_conditions
            inputs: [project_status, priority_order]
            logic: "IF project_status = 'At Risk' AND priority_order = 1"
        
        High:
          definition: "Either top priority or at risk"
          precedence: 2
          derivation_rule:
            type: ordered_conditions
            inputs: [priority_order, project_status]
            logic: "IF priority_order = 1 OR project_status = 'At Risk'"
        
        Medium:
          definition: "Active projects with normal priority"
          precedence: 3
          derivation_rule:
            type: ordered_conditions
            inputs: [project_status]
            logic: "IF project_status = 'Active'"
        
        Low:
          definition: "Default for inactive or completed projects"
          precedence: 4
          derivation_rule:
            type: ordered_conditions
            inputs: []
            logic: "DEFAULT"
```

### Example 2: Customer Tier (Simple Backward Compatible)

```yaml
requirements:
  field_requirements:
    CUSTOMER_TIER:
      type: string
      nullable: false
      allowed_values: [Platinum, Gold, Silver, Bronze]
```

## Python API

### Working with Enhanced Allowed Values

```python
from adri.contracts.derivation import (
    DerivationRule,
    CategoryDefinition,
    validate_enhanced_allowed_values,
    get_category_values,
    get_categories_by_precedence,
)

# Create a derivation rule
rule = DerivationRule(
    type="ordered_conditions",
    inputs=["status", "priority"],
    logic="IF status = 'Critical' AND priority = 1"
)

# Create a category definition
category = CategoryDefinition(
    definition="High priority critical issues",
    precedence=1,
    derivation_rule=rule
)

# Validate enhanced allowed_values
errors = validate_enhanced_allowed_values(
    allowed_values={
        "High": {"definition": "...", "precedence": 1},
        "Low": {"definition": "...", "precedence": 2}
    },
    field_path="RISK_LEVEL"
)

# Extract valid category values (works with both formats)
values = get_category_values(allowed_values)
# Returns: ["High", "Low"]

# Get categories sorted by precedence
categories = get_categories_by_precedence(allowed_values)
# Returns: [(name, CategoryDefinition), ...] sorted by precedence
```

### Schema Validation

```python
from adri.contracts.schema import StandardSchema

# Validate field requirement with enhanced allowed_values
errors = StandardSchema.validate_field_requirement(
    field_name="RISK_LEVEL",
    field_req={
        "type": "string",
        "is_derived": True,
        "allowed_values": {
            "High": {"definition": "...", "precedence": 1},
            "Low": {"definition": "...", "precedence": 2}
        }
    },
    field_path="requirements.field_requirements"
)
```

## Validation Rules

### Required Fields
- **CategoryDefinition:** `definition`, `precedence`
- **DerivationRule:** `type`, `inputs`, `logic`

### Constraints
- `precedence` must be integer >= 1
- `precedence` values must be unique within a field
- `is_derived=true` requires enhanced dict format (not simple list)
- `inputs` must be a list (can be empty for DEFAULT rules)
- `type` and `logic` cannot be empty strings

### Validation Errors

```python
# Missing required field
{
    "High": {
        "precedence": 1
        # ERROR: Missing 'definition'
    }
}

# Duplicate precedence
{
    "High": {"definition": "...", "precedence": 1},
    "Critical": {"definition": "...", "precedence": 1}  # ERROR: Duplicate
}

# Invalid is_derived usage
{
    "type": "string",
    "is_derived": True,
    "allowed_values": ["High", "Low"]  # ERROR: Must use dict format
}
```

## Migration Guide

### Migrating Existing Standards

**Before (Simple Format):**
```yaml
RISK_LEVEL:
  type: string
  allowed_values: [Critical, High, Medium, Low]
```

**After (Enhanced Format):**
```yaml
RISK_LEVEL:
  type: string
  is_derived: true
  allowed_values:
    Critical:
      definition: "Highest risk level requiring immediate action"
      precedence: 1
      derivation_rule:
        type: ordered_conditions
        inputs: [risk_score]
        logic: "IF risk_score >= 90"
    High:
      definition: "High risk requiring attention"
      precedence: 2
      derivation_rule:
        type: ordered_conditions
        inputs: [risk_score]
        logic: "IF risk_score >= 70"
    # ... etc
```

### Gradual Migration

1. **Phase 1:** Keep simple format, add metadata documentation
2. **Phase 2:** Convert to enhanced format for critical fields
3. **Phase 3:** Add derivation rules incrementally
4. **Phase 4:** Use derivation rules in AI prompts for deterministic outputs

## Benefits

### 1. Deterministic AI Categorization
- **Before:** Prompt-based categorization yields 20% divergence
- **After:** Schema-based rules yield <5% divergence (certification level)

### 2. Single Source of Truth
- Categorization logic lives in enforceable schema
- No duplication across prompts, docs, or code
- Version-controlled with the standard

### 3. Auto-Tunable
- Derivation rules can be automatically refined
- A/B testing of different categorization strategies
- Continuous improvement based on real data

### 4. Human-Readable Documentation
- `definition` field provides clear business logic
- `examples` help users understand categories
- `precedence` shows evaluation order explicitly

### 5. Backward Compatible
- Existing simple list format still works
- Gradual migration path
- No breaking changes for existing standards

## Testing

Comprehensive test coverage in `tests/test_enhanced_allowed_values.py`:

```bash
# Run tests
pytest tests/test_enhanced_allowed_values.py -v

# Coverage: 35 tests, 89.38% coverage on derivation.py
```

Test categories:
- DerivationRule validation (7 tests)
- CategoryDefinition validation (7 tests)
- Enhanced allowed_values validation (10 tests)
- Utility functions (5 tests)
- Schema integration (5 tests)
- Real-world use case (1 test)

## Future Enhancements

### 1. Derivation Rule Execution Engine
- Evaluate rules against actual data
- Validate that derived values match schema
- Auto-fix data based on rules

### 2. ContractGenerator Auto-Detection
- Analyze data to detect derived fields
- Generate placeholder derivation rules
- Suggest input fields based on correlation

### 3. Visual Derivation Rule Builder
- GUI for creating derivation rules
- Test rules against sample data
- Visualize precedence order

### 4. Advanced Rule Types
- Machine learning models as rules
- External API calls
- Complex multi-step derivations

## Related Documentation

- [ADRI Schema Validation](SCHEMA_VALIDATION.md)
- [Contract Generation Guide](../examples/README.md)
- [Workflow Integration](WORKFLOW_ORCHESTRATION_INTEGRATION.md)

## Support

For questions or issues with schema derivation rules:
- GitHub Issues: [adri-enterprise/issues](https://github.com/verodat/adri-enterprise/issues)
- Documentation: [docs.adri.ai](https://docs.adri.ai)
