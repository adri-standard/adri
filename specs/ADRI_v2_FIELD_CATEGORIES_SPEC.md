# ADRI v2.0 Enhancement Specification
## Optional Field Metadata for AI Reasoning

**Version**: 2.0.0  
**Date**: 2025-01-11  
**Status**: Draft  
**Author**: ADRI Development Team  

---

## Executive Summary

ADRI v2.0 adds **three optional field properties** to support AI reasoning use cases:

1. `field_category` - Classify fields as `ai_decision`, `ai_narrative`, or `standard`
2. `derivation` - Specify logic for how decision field values are derived
3. `reasoning_guidance` - Provide templates for narrative field generation

**Key Principle**: This is a **backward-compatible extension**. Existing ADRI standards work unchanged. New properties are entirely optional.

**ADRI's Role**: Store and validate this metadata. Consumers (like Veroplay) use it for prompt generation and quality tracking.

---

## 1. Motivation

### 1.1 The Use Case

AI reasoning steps produce two types of outputs:
- **Decisions**: Enum values that should be deterministic (e.g., `RISK_LEVEL: "High"`)
- **Narratives**: Explanations that can vary semantically (e.g., `RISK_RATIONALE: "Project shows high risk due to..."`)

Currently, ADRI has no way to capture this distinction in the standard.

### 1.2 Solution: Optional Metadata

Add optional properties to annotate fields with metadata that consumers can use:

```yaml
field_requirements:
  RISK_LEVEL:
    type: string
    field_category: ai_decision  # NEW: Optional metadata
    derivation:                  # NEW: Optional logic spec
      strategy: ordered_precedence
      rules: [...]
    constraints:
      - type: allowed_values
        values: ["Critical", "High", "Medium", "Low"]
    
  RISK_RATIONALE:
    type: string
    field_category: ai_narrative # NEW: Optional metadata
    reasoning_guidance: |        # NEW: Optional template
      Explain risk factors...
    constraints:
      - type: min_length
        value: 20
```

**What ADRI does**: Validates these properties are well-formed (if present)
**What consumers do**: Use metadata for their purposes (prompts, divergence testing, etc.)

---

## 2. Schema Enhancements

### 2.1 New Field Properties

#### 2.1.1 Field Category

**Property**: `field_category`  
**Type**: Enum  
**Values**: `"ai_decision"` | `"ai_narrative"` | `"standard"`  
**Default**: `"standard"`  
**Required**: No (backward compatible)

**Semantics**:
- `"ai_decision"`: Field produced by AI with deterministic logic (enum/calculated)
- `"ai_narrative"`: Field produced by AI with free-form reasoning (text explanations)
- `"standard"`: Regular field without special AI behavior

**Example**:
```yaml
field_requirements:
  RISK_LEVEL:
    type: string
    field_category: ai_decision
    allowed_values: ["Critical", "High", "Medium", "Low"]
```

#### 2.1.2 Derivation Rules

**Property**: `derivation`  
**Type**: Object  
**Required**: No  
**Applicable**: Only for `field_category: ai_decision`

**Structure**:
```yaml
derivation:
  strategy: <strategy_name>
  inputs: [field1, field2, ...]
  rules: <strategy_specific>
  metadata:
    auto_generated: true | false
    confidence: high | medium | low
    note: "Human-readable explanation"
```

**Supported Strategies**:
1. `ordered_precedence`: Rules evaluated in order, first match wins
2. `explicit_lookup`: Direct input→output table mapping
3. `direct_mapping`: Simple 1:1 or 1:many field mapping
4. `calculated`: Formula-based computation

#### 2.1.3 Reasoning Guidance

**Property**: `reasoning_guidance`  
**Type**: String (multi-line)  
**Required**: No  
**Applicable**: Only for `field_category: ai_narrative`

**Purpose**: Provide template or instructions for AI when generating narrative content.

**Example**:
```yaml
field_requirements:
  RISK_RATIONALE:
    type: string
    field_category: ai_narrative
    reasoning_guidance: |
      Explain specific risk factors from project data.
      Template: "Project shows [RISK_LEVEL] risk due to [specific factors from NOTES]."
    constraints:
      - type: min_length
        value: 20
      - type: max_length
        value: 500
```

---

## 3. Derivation Strategies

### 3.1 Strategy: Ordered Precedence

**Use Case**: Mutually exclusive conditions evaluated in priority order.

**Structure**:
```yaml
derivation:
  strategy: ordered_precedence
  inputs: [field1, field2, ...]
  rules:
    - precedence: 1
      condition: "<boolean expression>"
      value: "<output value>"
      note: "Optional explanation"
    - precedence: 2
      condition: "<boolean expression>"
      value: "<output value>"
    - precedence: N
      is_default: true
      value: "<fallback value>"
      note: "Catch-all rule"
```

**Evaluation Logic**:
1. Sort rules by `precedence` (ascending)
2. Evaluate conditions in order
3. Return `value` of first matching condition
4. If no condition matches, use rule with `is_default: true`

**Condition Syntax**:
- Field references: `field_name`
- Operators: `=`, `!=`, `<`, `>`, `<=`, `>=`
- Logical: `AND`, `OR`, `NOT`
- String contains: `CONTAINS`, `MATCHES`
- Set membership: `IN [...]`

**Example**:
```yaml
RISK_LEVEL:
  field_category: ai_decision
  type: string
  allowed_values: ["Critical", "High", "Medium", "Low"]
  derivation:
    strategy: ordered_precedence
    inputs: [priority_order, project_status]
    rules:
      - precedence: 1
        condition: "priority_order = 1 AND project_status = 'At Risk'"
        value: "Critical"
        note: "Highest priority explicitly at risk"
      - precedence: 2
        condition: "priority_order = 1 OR project_status = 'At Risk'"
        value: "High"
      - precedence: 3
        condition: "project_status = 'In Progress' AND priority_order >= 2"
        value: "Medium"
      - precedence: 4
        is_default: true
        value: "Low"
```

### 3.2 Strategy: Explicit Lookup

**Use Case**: Deterministic table lookup from 2-3 input fields.

**Structure**:
```yaml
derivation:
  strategy: explicit_lookup
  inputs: [field1, field2, ...]
  lookup_table:
    - keys: {field1: value1, field2: value2}
      value: <output>
      note: "Optional explanation"
    - keys: {field1: value3, field2: value4}
      value: <output>
    - is_default: true
      value: <fallback>
      note: "Default when no match"
```

**Evaluation Logic**:
1. For each row in `lookup_table`:
   - Check if ALL keys match input values
   - If match, return `value`
2. If no match, use row with `is_default: true`

**Example**:
```yaml
HEALTH_SCORE:
  field_category: ai_decision
  type: integer
  derivation:
    strategy: explicit_lookup
    inputs: [TIMELINE_STATUS, priority_order]
    lookup_table:
      - keys: {TIMELINE_STATUS: "On Track", priority_order: 1}
        value: 100
        note: "Optimal health"
      - keys: {TIMELINE_STATUS: "On Track", priority_order: 2}
        value: 95
      - keys: {TIMELINE_STATUS: "On Track", priority_order: 3}
        value: 90
      - keys: {TIMELINE_STATUS: "At Risk", priority_order: 1}
        value: 60
        note: "Moderate concern"
      - keys: {TIMELINE_STATUS: "At Risk", priority_order: 2}
        value: 55
      - keys: {TIMELINE_STATUS: "At Risk", priority_order: 3}
        value: 50
      - is_default: true
        value: 50
        note: "Default fallback"
```

### 3.3 Strategy: Direct Mapping

**Use Case**: Simple 1:1 or 1:many field transformation.

**Structure**:
```yaml
derivation:
  strategy: direct_mapping
  source_field: <field_name>
  mappings:
    "<source_value1>": "<target_value1>"
    "<source_value2>": "<target_value2>"
    "*": "<wildcard_target>"  # Catch-all
```

**Evaluation Logic**:
1. Look up `source_field` value in `mappings`
2. Return matching target value
3. If no match, use `"*"` wildcard mapping

**Example**:
```yaml
TIMELINE_STATUS:
  field_category: ai_decision
  type: string
  derivation:
    strategy: direct_mapping
    source_field: project_status
    mappings:
      "At Risk": "At Risk"
      "Delayed": "At Risk"
      "Behind Schedule": "At Risk"
      "*": "On Track"  # Everything else
```

### 3.4 Strategy: Calculated

**Use Case**: Numeric computation from multiple inputs using formula.

**Structure**:
```yaml
derivation:
  strategy: calculated
  formula: "<arithmetic expression>"
  variables:
    VAR1: <constant or lookup>
    VAR2:
      lookup: <field_name>
      values:
        "<field_value1>": <number>
        "<field_value2>": <number>
    VAR3:
      condition_based:
        - condition: "<boolean>"
          value: <number>
        - is_default: true
          value: <number>
  constraints:
    min: <minimum value>
    max: <maximum value>
    round: true | false
```

**Evaluation Logic**:
1. Resolve all variables
2. Evaluate formula
3. Apply constraints (clamp to min/max, round if needed)

**Example**:
```yaml
HEALTH_SCORE:
  field_category: ai_decision
  type: integer
  derivation:
    strategy: calculated
    formula: "BASE + TIMELINE_FACTOR + STATUS_FACTOR + PRIORITY_FACTOR"
    variables:
      BASE: 50
      TIMELINE_FACTOR:
        lookup: TIMELINE_STATUS
        values:
          "Ahead": 20
          "On Track": 10
          "At Risk": -10
          "Delayed": -20
      STATUS_FACTOR:
        lookup: project_status
        values:
          "Completed": 20
          "In Progress": 5
          "Planning": 0
          "At Risk": -15
      PRIORITY_FACTOR:
        condition_based:
          - condition: "priority_order <= 10"
            value: 10
          - condition: "priority_order > 40"
            value: -5
          - is_default: true
            value: 0
    constraints:
      min: 0
      max: 100
      round: true
```

---

## 4. Schema Validation

ADRI's role is to validate that the new properties are **well-formed** (if present). ADRI does NOT change how it validates actual data records - that remains unchanged.

### 4.1 Validating field_category

If `field_category` is present:
- ✅ Must be one of: `"ai_decision"`, `"ai_narrative"`, `"standard"`
- ❌ Invalid values rejected during schema validation

### 4.2 Validating derivation

If `derivation` is present:
- ✅ Must have `strategy` field with valid strategy name
- ✅ Must have required fields for that strategy (e.g., `rules` for ordered_precedence)
- ✅ Structure must match strategy specification
- ❌ Mal-formed derivation objects rejected during schema validation

### 4.3 Validating reasoning_guidance

If `reasoning_guidance` is present:
- ✅ Must be a string
- ❌ Non-string values rejected during schema validation

### 4.4 Data Validation (Unchanged)

**Important**: ADRI's data validation behavior is **unchanged**. ADRI validates records against the constraints as before:
- `allowed_values` constraints are enforced
- `min_length`/`max_length` constraints are enforced
- All existing constraint types work exactly as before

The new properties are **metadata only** - they don't change how ADRI validates data records.

---

## 5. Auto-Generation

### 5.1 Strategy Inference

ADRI Enterprise should attempt to infer derivation strategies from training data.

#### 5.1.1 Inference Heuristics

**Direct Mapping Detection**:
```python
def infer_direct_mapping(source_field, target_field, data):
    """Detect 1:1 or 1:many mappings"""
    mapping = {}
    for record in data:
        source_val = record[source_field]
        target_val = record[target_field]
        
        if source_val in mapping:
            if mapping[source_val] != target_val:
                return None  # Not deterministic
        else:
            mapping[source_val] = target_val
    
    # Check if most values map to one catch-all
    value_counts = Counter(mapping.values())
    if len(value_counts) > 1:
        most_common = value_counts.most_common(1)[0][0]
        # Use wildcard for most common
        return {"strategy": "direct_mapping", "mappings": mapping, "wildcard": most_common}
    
    return {"strategy": "direct_mapping", "mappings": mapping}
```

**Lookup Table Detection**:
```python
def infer_lookup_table(target_field, candidate_inputs, data):
    """Detect perfect deterministic multi-field lookup"""
    # Try combinations of 2-3 input fields
    for input_combo in combinations(candidate_inputs, min_len=2, max_len=3):
        lookup = {}
        deterministic = True
        
        for record in data:
            key = tuple(record[field] for field in input_combo)
            value = record[target_field]
            
            if key in lookup and lookup[key] != value:
                deterministic = False
                break
            lookup[key] = value
        
        if deterministic:
            return {
                "strategy": "explicit_lookup",
                "inputs": list(input_combo),
                "table": lookup
            }
    
    return None
```

**Ordered Precedence Inference**:
```python
def infer_ordered_precedence(target_field, candidate_inputs, data):
    """Infer mutually exclusive conditional rules"""
    # Use decision tree algorithm to find optimal splits
    from sklearn.tree import DecisionTreeClassifier
    
    X = data[candidate_inputs]
    y = data[target_field]
    
    tree = DecisionTreeClassifier(max_depth=4)
    tree.fit(X, y)
    
    # Extract rules from tree
    rules = extract_rules_from_tree(tree, candidate_inputs, y.unique())
    
    # Order by priority (most specific first)
    rules = order_rules_by_specificity(rules)
    
    return {
        "strategy": "ordered_precedence",
        "inputs": candidate_inputs,
        "rules": rules
    }
```

#### 5.1.2 Confidence Scoring

```python
def calculate_confidence(strategy_spec, training_data):
    """Score confidence in auto-generated derivation"""
    
    # Test derivation against training data
    correct = 0
    total = len(training_data)
    
    for record in training_data:
        predicted = evaluate_derivation(strategy_spec, record)
        actual = record[target_field]
        if predicted == actual:
            correct += 1
    
    accuracy = correct / total
    
    # Confidence levels
    if accuracy >= 0.95:
        return "high"
    elif accuracy >= 0.80:
        return "medium"
    else:
        return "low"
```

### 5.2 Review Workflow

Auto-generated rules should include confidence metadata:

```yaml
derivation:
  strategy: ordered_precedence
  metadata:
    auto_generated: true
    confidence: medium  # high | medium | low
    accuracy: 0.89
    training_records: 35
    note: "Review recommended - 89% accuracy on training data"
  rules: [...]
```

**Recommended Actions**:
- `confidence: high` (≥95%): ✅ Auto-accept, monitor in production
- `confidence: medium` (80-95%): ⚡ Flag for review, suggest acceptance
- `confidence: low` (<80%): ⚠️ Require manual review before use

---

## 6. How Consumers Use This Metadata

While ADRI only stores and validates the metadata, consumers (like Veroplay) can use it for various purposes:

### 6.1 Prompt Generation

Consumers can read `derivation` rules and generate prompt instructions:

```python
# Veroplay example
def generate_prompt_for_field(field_name, field_spec):
    if field_spec.get('field_category') == 'ai_decision':
        derivation = field_spec.get('derivation')
        # Generate instructions from derivation rules
        return format_derivation_as_prompt(derivation)
    
    elif field_spec.get('field_category') == 'ai_narrative':
        guidance = field_spec.get('reasoning_guidance', '')
        # Include guidance in prompt
        return f"For {field_name}: {guidance}"
```

### 6.2 Divergence Testing

Consumers can use `field_category` to decide which fields to test:

```python
# Veroplay example
def should_test_for_divergence(field_name, adri_standard):
    field_spec = adri_standard['field_requirements'][field_name]
    category = field_spec.get('field_category', 'standard')
    
    # Skip narrative fields - they naturally vary
    return category != 'ai_narrative'
```

### 6.3 Quality Tracking

Consumers can track different metrics for different field types:

```python
# Veroplay example
def track_quality(field_name, field_spec, values):
    category = field_spec.get('field_category', 'standard')
    
    if category == 'ai_decision':
        # Track consistency (should be deterministic)
        return calculate_consistency_score(values)
    elif category == 'ai_narrative':
        # Track structural quality only
        return calculate_length_distribution(values)
```

---

## 7. Migration Guide

### 7.1 Backward Compatibility

**Default Behavior**:
- Fields without `field_category` default to `"standard"`
- Existing ADRI standards continue to work unchanged
- Validation behavior unchanged for standard fields

### 7.2 Migration Strategy

**Step 1: Identify Field Types**
```python
# Analyze existing standard
for field_name, field_spec in standard['field_requirements'].items():
    if has_allowed_values(field_spec) and has_derivation_logic(field_spec):
        # Candidate for ai_decision
        field_spec['field_category'] = 'ai_decision'
    elif is_long_text_field(field_spec) and field_name.endswith('_RATIONALE'):
        # Candidate for ai_narrative
        field_spec['field_category'] = 'ai_narrative'
    else:
        # Remains standard (or set explicitly)
        field_spec['field_category'] = 'standard'
```

**Step 2: Extract Derivation Rules**
```python
# Convert old format to new format
if field_spec.get('allowed_values') and isinstance(field_spec['allowed_values'], dict):
    # Old format with embedded derivation
    derivation = extract_derivation_from_allowed_values(field_spec['allowed_values'])
    
    # New format - separate sections
    field_spec['allowed_values'] = list(field_spec['allowed_values'].keys())
    field_spec['derivation'] = derivation
```

**Step 3: Add Reasoning Guidance**
```python
# For narrative fields, add guidance
if field_spec['field_category'] == 'ai_narrative':
    field_spec['reasoning_guidance'] = generate_guidance_template(field_name)
```

### 7.3 Migration Script

See `migrate_adri_standards.py` for automated migration tool.

---

## 8. Implementation Checklist

### 8.1 Schema Extension
- [ ] Add `field_category` enum to field spec schema (optional property)
- [ ] Add `derivation` object schema with all strategies (optional property)
- [ ] Add `reasoning_guidance` string property (optional property)
- [ ] Update schema validator to accept and validate new properties
- [ ] Ensure backward compatibility (fields without properties still work)

### 8.2 Schema Validation
- [ ] Validate `field_category` enum values if present
- [ ] Validate `derivation` structure matches strategy spec if present
- [ ] Validate `reasoning_guidance` is string if present
- [ ] Reject mal-formed metadata during schema validation

### 8.3 Auto-Generator (Optional)
- [ ] Implement strategy inference heuristics
- [ ] Add confidence scoring calculation
- [ ] Create review workflow for low-confidence rules
- [ ] Generate metadata for auto-generated rules

### 8.4 Migration Tools
- [ ] Create migration script for existing standards
- [ ] Add validation for migrated standards
- [ ] Create test suite for migration accuracy

### 8.5 Documentation
- [ ] Update ADRI specification documentation
- [ ] Create examples for each field category
- [ ] Document each derivation strategy
- [ ] Write migration guide for users
- [ ] Document how consumers should use the metadata

---

## 9. Examples

See accompanying files:
- `ADRI_roadmap_clean_v2.yaml` - Migrated roadmap standard
- `ADRI_decision_examples.yaml` - Decision field examples
- `ADRI_narrative_examples.yaml` - Narrative field examples

---

## 10. Future Enhancements

### 10.1 Additional Derivation Strategies

**Fuzzy Matching**:
```yaml
derivation:
  strategy: fuzzy_match
  source_field: user_input
  mappings:
    "high": ["high", "hi", "h", "critical", "urgent"]
    "low": ["low", "lo", "l", "minor"]
```

**ML Model Reference**:
```yaml
derivation:
  strategy: ml_model
  model_id: "risk-classifier-v2"
  inputs: [project_budget, timeline_variance, team_size]
  confidence_threshold: 0.85
```

### 10.2 Validation Enhancements

- **Cross-field validation**: Check consistency between decision fields
- **Temporal validation**: Validate sequences of decisions over time
- **Confidence scoring**: Track AI confidence in decision fields

---

## Appendix A: Complete Example

See `ADRI_roadmap_clean_v2.yaml` for a complete working example demonstrating all field categories and derivation strategies.

---

## Appendix B: Glossary

- **AI Decision Field**: Field with deterministic logic that AI must follow
- **AI Narrative Field**: Free-form text field allowing semantic variation
- **Derivation Strategy**: Algorithm for computing field value from inputs
- **Field Category**: Explicit classification of field type
- **Divergence Testing**: Measuring consistency of field values over time

---

**Document Status**: Draft for Review  
**Next Review Date**: 2025-01-18  
**Approval Required**: ADRI Architecture Review Board
