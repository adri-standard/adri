# ADRI Reasoning Mode Guide

## Overview

The Reasoning Mode enhancement adds AI/LLM reasoning step validation support to ADRI's `@adri_protected` decorator. This feature enables comprehensive logging and validation of AI-powered data workflows while maintaining 100% backward compatibility.

## Key Features

### 1. **Prompt & Response Logging**
- Automatic capture of AI prompts and responses to JSONL audit logs
- SHA-256 hash verification for content integrity
- Thread-safe operations with unique ID generation
- Relational linking to quality assessments

### 2. **AI Output Validation**
- Validate AI-generated fields (confidence scores, risk levels, recommendations)
- Enforce business rules on AI outputs
- Integration with ADRI's quality scoring system

### 3. **Meta-Validation Standards**
- Reasoning CSV logs self-validate using ADRI standards
- Ensures audit log quality and completeness
- Enables automated audit verification

### 4. **Complete Audit Trail**
- Links prompts → responses → assessments via IDs
- Tracks processing time and token usage
- Preserves LLM configuration for reproducibility

## Quick Start

### Basic Usage

```python
from adri import adri_protected
import pandas as pd

@adri_protected(
    standard="ai_risk_analysis",
    data_param="projects",
    reasoning_mode=True,
    store_prompt=True,
    store_response=True,
    llm_config={
        "model": "claude-3-5-sonnet",
        "temperature": 0.1,
        "seed": 42
    }
)
def analyze_project_risks(projects):
    """Analyze project risks using AI."""
    # Your AI reasoning logic here
    enhanced_data = ai_model.analyze(projects)
    return enhanced_data

# Execute with automatic reasoning logging
projects = pd.DataFrame([...])
result = analyze_project_risks(projects)
```

### What Happens

1. **Quality Assessment**: Input data assessed against standard
2. **Prompt Logging**: AI prompt captured to `adri_reasoning_prompts.jsonl`
3. **Function Execution**: Your AI processing runs
4. **Response Logging**: AI response captured to `adri_reasoning_responses.jsonl`
5. **Assessment Linking**: All logs linked via `assessment_id`, `prompt_id`, `response_id`

## Configuration

### Decorator Parameters

```python
@adri_protected(
    # Existing parameters (unchanged)
    standard="standard_name",
    data_param="data",
    min_score=80.0,

    # New reasoning parameters
    reasoning_mode=False,        # Enable reasoning workflow
    store_prompt=True,           # Log prompts to JSONL
    store_response=True,          # Log responses to JSONL
    llm_config={                 # LLM configuration
        "model": "model-name",
        "temperature": 0.1,
        "seed": 42,
        "max_tokens": 4000
    }
)
```

### LLM Configuration

```python
llm_config = {
    "model": "claude-3-5-sonnet",     # Required: Model identifier
    "temperature": 0.1,                # Required: Temperature setting
    "seed": 42,                        # Optional: Random seed for reproducibility
    "max_tokens": 4000,                # Optional: Max tokens (default: 4000)
}
```

## CSV Audit Logs

### Log Files Created

```
ADRI/dev/audit-logs/
├── adri_assessment_logs.csv          # Quality assessments (extended)
├── adri_dimension_scores.csv         # Dimension scores (existing)
├── adri_failed_validations.csv       # Failed validations (existing)
├── adri_reasoning_prompts.jsonl        # NEW: AI prompts
└── adri_reasoning_responses.jsonl      # NEW: AI responses
```

### Reasoning Prompts CSV Schema

```csv
prompt_id,assessment_id,run_id,step_id,timestamp,system_prompt,user_prompt,model,temperature,seed,max_tokens,prompt_hash
prompt_20250110_143022_a1b2c3,assess_001,run_001,step_001,2025-01-10T14:30:22,System prompt text,User prompt text,claude-3-5-sonnet,0.1,42,4000,sha256hash...
```

### Reasoning Responses CSV Schema

```csv
response_id,assessment_id,prompt_id,timestamp,response_text,processing_time_ms,token_count,response_hash
response_20250110_143025_d4e5f6,assess_001,prompt_20250110_143022_a1b2c3,2025-01-10T14:30:25,AI response text,3500,250,sha256hash...
```

### Extended Assessment Log Fields

```csv
assessment_id,...,prompt_id,response_id,step_type
assess_001,...,prompt_20250110_143022_a1b2c3,response_20250110_143025_d4e5f6,REASONING
```

## Relational Schema

```
┌─────────────────────────┐
│ assessment_logs         │
│ ─────────────────────── │
│ assessment_id (PK)      │
│ prompt_id (FK) ────────┐│
│ response_id (FK) ──────┼┼───┐
│ step_type               ││   │
└─────────────────────────┘│   │
                           │   │
┌─────────────────────────┐│   │
│ reasoning_prompts       ││   │
│ ─────────────────────── ││   │
│ prompt_id (PK) ◄────────┘│   │
│ assessment_id (FK)       │   │
│ system_prompt            │   │
│ user_prompt              │   │
│ model, temperature, etc  │   │
└─────────────────────────┘   │
           │                   │
           └───────────────────┼───┐
                               │   │
┌─────────────────────────┐   │   │
│ reasoning_responses     │   │   │
│ ─────────────────────── │   │   │
│ response_id (PK) ◄──────┘   │
│ assessment_id (FK)           │
│ prompt_id (FK) ◄─────────────┘
│ response_text                │
│ processing_time_ms           │
│ token_count                  │
└─────────────────────────────┘
```

## AI Output Validation

### Creating a Reasoning Standard

```yaml
metadata:
  name: "AI Risk Analysis Standard"
  version: "1.0.0"
  description: "Standard for AI-generated risk analysis"

requirements:
  overall_minimum: 75.0

  field_requirements:
    # Input fields
    project_id:
      type: "string"
      nullable: false

    # AI-generated fields
    ai_risk_level:
      type: "string"
      nullable: false
      allowed_values: ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    ai_confidence_score:
      type: "number"
      nullable: false
      min_value: 0.0
      max_value: 1.0

    ai_recommendations:
      type: "string"
      nullable: false
      min_length: 10
```

### Validation Rules

```python
from adri.standards.reasoning_validator import ReasoningValidator

validator = ReasoningValidator()

# Validate confidence scores (0-1 or 0-100 ranges)
# Validate risk levels (LOW/MEDIUM/HIGH/CRITICAL)
# Check allowed values for categorical fields
# Enforce min/max constraints for numeric fields
```

## Usage Examples

### Example 1: Customer Service AI

```python
@adri_protected(
    standard="customer_service_quality",
    data_param="tickets",
    reasoning_mode=True,
    llm_config={
        "model": "gpt-4",
        "temperature": 0.2,
        "seed": 123
    }
)
def process_support_tickets(tickets):
    """Process customer support tickets with AI."""
    responses = []
    for ticket in tickets.to_dict('records'):
        ai_response = ai_agent.generate_response(ticket)
        responses.append({
            **ticket,
            "ai_response": ai_response,
            "ai_sentiment": analyze_sentiment(ai_response),
            "ai_confidence": calculate_confidence(ai_response)
        })
    return pd.DataFrame(responses)
```

### Example 2: Financial Risk Analysis

```python
@adri_protected(
    standard="financial_risk_assessment",
    data_param="transactions",
    reasoning_mode=True,
    min_score=90.0,  # Higher threshold for financial data
    llm_config={
        "model": "claude-3-opus",
        "temperature": 0.05,  # Very low for consistency
        "seed": 42
    }
)
def assess_transaction_risk(transactions):
    """Assess transaction risk with AI."""
    risk_analysis = ai_model.analyze_transactions(transactions)
    return risk_analysis
```

### Example 3: Document Processing

```python
@adri_protected(
    standard="document_extraction_quality",
    data_param="documents",
    reasoning_mode=True,
    store_prompt=True,
    store_response=True,
    llm_config={
        "model": "llama-3-70b",
        "temperature": 0.1
    }
)
def extract_document_entities(documents):
    """Extract entities from documents using AI."""
    entities = []
    for doc in documents.to_dict('records'):
        extracted = ai_extractor.extract(doc['text'])
        entities.append({
            "document_id": doc['id'],
            "entities": extracted['entities'],
            "confidence": extracted['confidence']
        })
    return pd.DataFrame(entities)
```

## Meta-Validation

### Validating Reasoning Logs

Reasoning CSV logs can be validated against their meta-standards:

```python
from adri import adri_protected
import pandas as pd

# Read reasoning prompts log
prompts_df = pd.read_csv("ADRI/dev/audit-logs/adri_reasoning_prompts.jsonl")

# Validate against meta-standard
@adri_protected(
    standard="adri_reasoning_prompts",  # Meta-standard
    data_param="prompts"
)
def validate_prompts_log(prompts):
    return prompts

validated = validate_prompts_log(prompts_df)
```

## Backward Compatibility

### Zero Impact When Disabled

```python
# Existing code works unchanged
@adri_protected(
    standard="my_standard",
    data_param="data"
)
def my_function(data):
    return process(data)

# No reasoning features activated
# No CSV overhead
# No behavior changes
```

### Gradual Adoption

```python
# Start with quality checks only
@adri_protected(standard="std", data_param="data")
def process_v1(data):
    return ai_process(data)

# Add reasoning later
@adri_protected(
    standard="std",
    data_param="data",
    reasoning_mode=True  # Enable when ready
)
def process_v2(data):
    return ai_process(data)
```

## Performance Considerations

### Overhead Analysis

- **reasoning_mode=False**: Zero overhead (default)
- **reasoning_mode=True**: ~1-3ms per invocation for logging
- **CSV Writing**: Thread-safe, non-blocking
- **Hash Generation**: ~0.5ms for typical prompts/responses

### Optimization Tips

1. **Selective Storage**: Use `store_prompt=False` or `store_response=False` to reduce I/O
2. **Batch Processing**: Process multiple records per function call
3. **Log Rotation**: Configure `max_log_size_mb` to prevent unbounded growth
4. **Async Logging**: CSV writes are thread-safe and efficient

## Troubleshooting

### CSV Files Not Created

**Issue**: Reasoning CSV files don't exist after execution

**Solutions**:
1. Check `reasoning_mode=True` is set
2. Verify audit logging is enabled in config
3. Check log directory permissions
4. Ensure `store_prompt` and `store_response` are True

### Missing Relational Links

**Issue**: Prompt ID or response ID is empty in assessment log

**Solutions**:
1. Verify function execution completed successfully
2. Check for exceptions during execution
3. Ensure logger configuration is correct
4. Review error logs for details

### Validation Failures

**Issue**: AI outputs fail validation

**Solutions**:
1. Review standard's `allowed_values` and constraints
2. Check AI output format matches expected types
3. Validate confidence scores are in 0-1 or 0-100 range
4. Ensure risk levels use standard categories

## Best Practices

### 1. Standard Design

```yaml
# Include both input and AI-generated fields
field_requirements:
  # Input fields
  input_field:
    type: "string"
    nullable: false

  # AI fields with validation
  ai_risk_level:
    allowed_values: ["LOW", "MEDIUM", "HIGH"]
  ai_confidence:
    min_value: 0.0
    max_value: 1.0
```

### 2. LLM Configuration

```python
# Use consistent config for reproducibility
STANDARD_LLM_CONFIG = {
    "model": "claude-3-5-sonnet",
    "temperature": 0.1,
    "seed": 42,  # For reproducibility
}

@adri_protected(
    standard="std",
    data_param="data",
    reasoning_mode=True,
    llm_config=STANDARD_LLM_CONFIG
)
def my_function(data):
    ...
```

### 3. Error Handling

```python
@adri_protected(
    standard="std",
    data_param="data",
    reasoning_mode=True,
    on_failure="raise"  # Fail fast on quality issues
)
def critical_ai_function(data):
    try:
        return ai_process(data)
    except Exception as e:
        # Error will be logged in response CSV
        raise
```

### 4. Testing

```python
# Test with reasoning disabled first
@adri_protected(standard="std", data_param="data")
def test_function_v1(data):
    return process(data)

# Enable reasoning after validation
@adri_protected(
    standard="std",
    data_param="data",
    reasoning_mode=True
)
def production_function(data):
    return process(data)
```

## Advanced Topics

### Multi-Step Reasoning

```python
@adri_protected(
    standard="step1_standard",
    data_param="data",
    reasoning_mode=True,
    llm_config={"model": "claude", "temperature": 0.1}
)
def reasoning_step1(data):
    return ai_step1(data)

@adri_protected(
    standard="step2_standard",
    data_param="intermediate",
    reasoning_mode=True,
    llm_config={"model": "claude", "temperature": 0.1}
)
def reasoning_step2(intermediate):
    return ai_step2(intermediate)

# Chain steps
result = reasoning_step2(reasoning_step1(data))
# Each step logged separately with unique IDs
```

### Custom Context Extraction

Reasoning mode automatically extracts context from function parameters. For custom extraction, you can pre-process prompts before calling the AI:

```python
@adri_protected(
    standard="custom_std",
    data_param="data",
    reasoning_mode=True
)
def custom_extraction(data):
    # Your custom prompt construction
    prompt = construct_custom_prompt(data)
    response = ai_model.call(prompt)
    return process_response(response)
```

## API Reference

### Decorator Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reasoning_mode` | bool | False | Enable reasoning workflow |
| `store_prompt` | bool | True | Store prompts to JSONL |
| `store_response` | bool | True | Store responses to JSONL |
| `llm_config` | dict | None | LLM configuration |

### LLM Config Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | str | Yes | Model identifier |
| `temperature` | float | Yes | Temperature (0.0-2.0) |
| `seed` | int | No | Random seed |
| `max_tokens` | int | No | Max tokens (default: 4000) |

### CSV Schemas

See the "CSV Audit Logs" section above for complete field listings.

## Migration Guide

### From Non-Reasoning to Reasoning

1. **Add reasoning parameters**:
   ```python
   # Before
   @adri_protected(standard="std", data_param="data")

   # After
   @adri_protected(
       standard="std",
       data_param="data",
       reasoning_mode=True,
       llm_config={"model": "claude", "temperature": 0.1}
   )
   ```

2. **Update standard** to include AI fields
3. **Test** with small dataset
4. **Deploy** to production
5. **Monitor** CSV logs for completeness

## FAQ

**Q: Does reasoning mode affect existing functionality?**
A: No. When `reasoning_mode=False` (default), there is zero impact on existing behavior.

**Q: Can I use reasoning mode without storing prompts/responses?**
A: Yes. Set `store_prompt=False` and/or `store_response=False`.

**Q: How do I query across CSV files?**
A: Use pandas to join on `assessment_id`, `prompt_id`, or `response_id`.

**Q: What happens if the function fails?**
A: The error is logged in the response CSV with processing time, and the exception is re-raised.

**Q: Can I validate the reasoning logs themselves?**
A: Yes! Use the meta-standards at `ADRI/standards/adri_reasoning_prompts_standard.yaml` and `adri_reasoning_responses_standard.yaml`.

## Support

For issues, feature requests, or questions:
- GitHub Issues: [adri-standard/adri](https://github.com/adri-standard/adri)
- Documentation: [docs.adri-standard.org](https://docs.adri-standard.org)
- Examples: See `examples/` directory
