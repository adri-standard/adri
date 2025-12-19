# ADRI Mode System

## Overview

The ADRI Mode System provides automatic detection and validation of three distinct ADRI template types based on their structure and intended use case:

1. **REASONING Mode**: AI-driven analysis and decision-making steps
2. **CONVERSATION Mode**: Interactive user dialogues and approvals
3. **DETERMINISTIC Mode**: Structured data transformations

## Why Modes Matter

Different VeroPlay step types require different ADRI template structures:

- **Reasoning steps** transform context into outputs through AI analysis
- **Conversation steps** interact with users and may collect structured data
- **Deterministic steps** perform predictable transformations with explicit input/output contracts

The mode system ensures templates are structured correctly for their intended use case, providing:
- **Type safety**: Guarantee correct data flow between steps
- **Clear errors**: Mode-specific validation messages for template authors
- **Auto-detection**: No manual mode declaration required

## Mode Detection

Modes are automatically detected based on template structure:

### REASONING Mode Detection

**Indicators** (checked in order):
- Has `context_requirements` (top-level or in `requirements`)
- Has `field_requirements` (top-level or in `requirements`)

**Example**:
```yaml
contracts:
  id: roadmap_analysis

requirements:
  context_requirements:
    projects_data:
      type: string
      
  field_requirements:
    EXECUTIVE_SUMMARY:
      type: string
      nullable: false
```

### CONVERSATION Mode Detection

**Indicators**:
- Has `schema.context` section

**Example**:
```yaml
specification:
  name: conversation_approval_input

schema:
  context:
    error_type:
      type: string
    proposed_changes:
      type: array
  
  can_modify:
    type: boolean
    allowed_values: [true]
  
  required_outputs:  # Optional
    approval_decision:
      type: string
      required: true
```

### DETERMINISTIC Mode Detection

**Indicators**:
- Has `input_requirements`
- Has `output_requirements`

**Example**:
```yaml
contracts:
  id: data_transform

input_requirements:
  raw_data:
    type: string
    nullable: false

output_requirements:
  processed_data:
    type: string
    nullable: false
```

### NONE Mode

Templates without mode-specific sections are classified as `NONE` mode (generic configuration files).

## Template Structure Requirements

### REASONING Mode Structure

**Required Sections**: None (flexible)

**Optional Sections**:
- `context_requirements` - Input data requirements
- `field_requirements` - Output data requirements  
- `requirements.context_requirements` - Nested input
- `requirements.field_requirements` - Nested output

**Notes**:
- Must have at least one of context or field requirements
- Most common pattern: both input and output defined

### CONVERSATION Mode Structure

**Required Sections**:
- `schema.context` - Context data available to conversation

**Optional Sections**:
- `schema.required_outputs` - Structured data to collect from user
- `schema.can_modify` - Whether AI can propose changes

**Notes**:
- `schema.context` must be non-empty dictionary
- `required_outputs` enables data collection from conversations
- `can_modify` typically `true` for approval flows

### DETERMINISTIC Mode Structure

**Required Sections**: None (flexible)

**Optional Sections**:
- `input_requirements` - Input data contract
- `output_requirements` - Output data contract

**Notes**:
- Must have at least one of input or output requirements
- Supports input-only (validation), output-only (generation), or both (transformation)

## Using Modes in Code

### Loading Templates with Mode Detection

```python
from src.adri.validator.loaders import load_contract
from src.adri.validator.modes import ADRIMode

# Auto-detect mode
template = load_contract("path/to/template.yaml", validate=False)
print(f"Detected mode: {template['_adri_mode']}")

# Enforce expected mode
template = load_contract(
    "path/to/template.yaml",
    validate=False,
    expected_mode=ADRIMode.CONVERSATION
)
# Raises ValueError if detected mode doesn't match
```

### Manual Mode Detection

```python
from src.adri.validator.modes import detect_mode
import yaml

with open("template.yaml") as f:
    template = yaml.safe_load(f)

mode = detect_mode(template)
print(f"Mode: {mode.value}")  # 'reasoning', 'conversation', 'deterministic', or 'none'
```

### Structure Validation

```python
from src.adri.validator.modes import detect_mode
from src.adri.validator.structure import validate_structure, format_validation_report

# Validate template structure
mode = detect_mode(template)
result = validate_structure(template, mode)

if not result.is_valid:
    print(format_validation_report(result))
    # Shows mode-specific errors and warnings
```

## VeroPlay Integration

### Declaring Step Modes

VeroPlay playbooks can specify mode for validation:

```yaml
steps:
  - name: gather_requirements
    type: reasoning
    input_standard: ADRI_requirements_context.yaml    # mode=reasoning
    output_standard: ADRI_requirements_output.yaml    # mode=reasoning
    
  - name: approval_request
    type: conversation
    input_standard: ADRI_conversation_approval_input.yaml   # mode=conversation
    output_standard: ADRI_conversation_outcome.yaml         # mode=conversation
    
  - name: transform_data
    type: deterministic
    input_standard: ADRI_transform_input.yaml         # mode=deterministic
    output_standard: ADRI_transform_output.yaml       # mode=deterministic
```

### Type-Safe Data Flow

The mode system ensures outputs from Step N match inputs to Step N+1:

```yaml
steps:
  - name: analyze
    type: reasoning
    output_standard: ADRI_analysis_output.yaml
    # Output validated against analysis_output mode/structure
    
  - name: transform
    type: deterministic
    input_standard: ADRI_transform_input.yaml
    # Input validated - must match analysis_output structure
    output_standard: ADRI_transform_output.yaml
```

## Auto-Generation with Modes

When AI generates ADRI templates, mode is specified as a parameter:

```python
from src.adri.generator import generate_adri_template
from src.adri.validator.modes import ADRIMode

# Generate conversation template
template = generate_adri_template(
    data=sample_data,
    mode=ADRIMode.CONVERSATION
)
# Generates schema.context and schema.required_outputs

# Generate reasoning template
template = generate_adri_template(
    data=sample_data,
    mode=ADRIMode.REASONING
)
# Generates context_requirements and field_requirements

# Generate without mode (generic template)
template = generate_adri_template(
    data=sample_data,
    mode=None
)
# No mode-specific sections generated
```

## Migration Guide

### Existing Templates

**No migration required!** Existing templates continue working:

- Reasoning templates already use `context_requirements`/`field_requirements` ✓
- Conversation templates already use `schema.context` ✓
- Mode detection is automatic ✓

### Upgrading Templates

To add mode awareness to VeroPlay playbooks:

1. **Identify step type**: reasoning, conversation, or deterministic
2. **Verify template structure**: Ensure it matches mode requirements
3. **Optional**: Add explicit mode validation in playbook

**Before** (implicit):
```yaml
steps:
  - name: analysis_step
    input_standard: ADRI_context.yaml
    output_standard: ADRI_output.yaml
```

**After** (explicit mode checking):
```yaml
steps:
  - name: analysis_step
    type: reasoning  # VeroPlay can validate mode matches
    input_standard: ADRI_context.yaml
    output_standard: ADRI_output.yaml
```

### Common Issues

**Issue**: Template detected as wrong mode

**Solution**: Check template structure matches intended mode:
- Conversation: Must have `schema.context`
- Reasoning: Must have `context_requirements` or `field_requirements`
- Deterministic: Must have `input_requirements` or `output_requirements`

**Issue**: Structure validation warnings

**Solution**: Warnings indicate cross-mode contamination (sections from other modes). Either:
1. Remove unexpected sections, or
2. Use `strict_structure=False` (default) to allow warnings

## Best Practices

### 1. Let Mode Detection Work

Don't add explicit `mode:` field to templates - detection is automatic.

### 2. Use Consistent Patterns

- **Reasoning**: Always use `requirements` section
- **Conversation**: Always use `schema` section  
- **Deterministic**: Use top-level `input_requirements`/`output_requirements`

### 3. Test Templates

```python
# Quick validation
from src.adri.validator.loaders import load_contract

try:
    template = load_contract("my_template.yaml", validate=False)
    print(f"✓ Valid {template['_adri_mode']} template")
except ValueError as e:
    print(f"✗ Invalid template: {e}")
```

### 4. Document Template Purpose

Add clear descriptions indicating template mode:

```yaml
contracts:
  id: my_template
  description: "Conversation template for approval workflows"
  # Mode will be auto-detected as CONVERSATION

schema:
  context:
    # ...
```

## FAQ

**Q: Do I need to declare mode in templates?**

A: No! Mode is automatically detected from structure.

**Q: What if I have both `schema` and `field_requirements`?**

A: Conversation mode takes priority (detection order). This indicates mixed structure - consider splitting into separate templates.

**Q: Can I create custom modes?**

A: No. The three modes cover all VeroPlay step types. If you need different validation, use NONE mode (generic template).

**Q: How do I know which mode my template is?**

A: Load it and check `_adri_mode` field, or use `detect_mode()` function.

**Q: What about backwards compatibility?**

A: Fully compatible! Existing templates work without changes. Mode system is additive.

## Implementation Details

### Files

- `src/adri/validator/modes.py` - Mode detection and enum
- `src/adri/validator/structure.py` - Structure validation
- `src/adri/validator/loaders.py` - Integration with load_contract

### Mode Metadata

Templates loaded with `load_contract()` include `_adri_mode` field:

```python
template = load_contract("template.yaml")
assert '_adri_mode' in template
assert template['_adri_mode'] in ['reasoning', 'conversation', 'deterministic', 'none']
```

### Error Messages

Mode-specific errors provide clear guidance:

```
Structure validation failed for template.yaml:
ADRI Structure Validation Report
Mode: conversation
Description: Conversation mode for interactive user dialogues
Status: ✗ INVALID

Errors:
  ✗ Required section 'schema.context' is missing

(Template detected as conversation but missing required context section)
```

## Support

For issues or questions about the ADRI mode system:

1. Check this documentation
2. Review template examples in `playbooks/platform/conversation/standards/`
3. Run validation to get specific error messages
4. Consult VeroPlay documentation for step type requirements
