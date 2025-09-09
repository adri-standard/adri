---
layout: default
title: Quick Start - ADRI
---

# Quick Start Guide

Get ADRI protecting your AI agents in under 5 minutes.

**Want the full story?** → [**AI Engineer Onboarding Guide**](ai-engineer-onboarding) - Complete journey from production failures to bulletproof agents (60 minutes).

## Installation

```bash
pip install adri
```

## Basic Usage

### 1. Import and Protect

```python
from adri import adri_protected

@adri_protected
def process_customer_data(data):
    # Your agent logic here
    return {"processed": True, "records": len(data)}

# Test with sample data
result = process_customer_data([
    {"name": "John Doe", "email": "john@example.com"},
    {"name": "Jane Smith", "email": "jane@example.com"}
])
print(result)  # {'processed': True, 'records': 2}
```

### 2. See Validation in Action

```python
# This will trigger validation warnings
bad_data = [
    {"name": "", "email": "invalid-email"},  # Empty name, invalid email
    {"name": "Bob", "email": None}           # Missing email
]

result = process_customer_data(bad_data)
# Check logs/adri_audit.jsonl for detailed validation results
```

### 3. Customize Validation (Optional)

```python
from adri import adri_protected

@adri_protected(
    completeness_threshold=0.8,  # Allow 20% missing values
    validity_checks=True,         # Enable format validation
    generate_report=True          # Create HTML report
)
def advanced_agent_function(data):
    return {"status": "processed"}
```

## Configuration

Create `adri-config.yaml` in your project root:

```yaml
validation:
  completeness_threshold: 0.9
  validity_checks: true
  consistency_checks: true
  plausibility_checks: true
  freshness_checks: false

reporting:
  generate_html_report: true
  log_level: "INFO"

audit:
  enable_logging: true
  log_file: "logs/adri_audit.jsonl"
```

## What Gets Validated

ADRI automatically checks your data for:

- **Completeness** - Missing values, empty fields
- **Validity** - Format validation (emails, dates, etc.)
- **Consistency** - Data type consistency across records
- **Plausibility** - Reasonable value ranges
- **Freshness** - Data age and relevance

## Output and Reports

### JSON Audit Logs
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "function_name": "process_customer_data",
  "validation_results": {
    "completeness_score": 0.85,
    "validity_score": 0.92,
    "overall_score": 0.88
  },
  "issues_found": [
    {"field": "email", "issue": "invalid_format", "count": 2}
  ]
}
```

### HTML Reports
When enabled, ADRI generates detailed HTML reports in `reports/` showing:
- Data quality scores
- Field-by-field analysis
- Issue summaries
- Recommendations

## Framework Integration

Ready to protect specific frameworks? Check our [framework examples](frameworks) for copy-paste ready code for:

- LangChain chains and agents
- CrewAI crew functions
- AutoGen multi-agent conversations
- LlamaIndex query engines
- Haystack pipelines
- LangGraph nodes
- Semantic Kernel functions

## Troubleshooting

### Common Issues

**Q: No validation logs appearing?**
A: Ensure the `logs/` directory exists or configure a custom path in `adri-config.yaml`

**Q: Too many validation warnings?**
A: Adjust thresholds in your config or decorator parameters

**Q: Performance concerns?**
A: ADRI is optimized for production use. For large datasets, consider sampling with `sample_size` parameter

## Next Steps

- [See framework-specific examples →](frameworks)
- [Read the full API reference →](https://github.com/adri-standard/adri/blob/main/docs/API_REFERENCE.md)
- [Report issues or request features →](https://github.com/adri-standard/adri/issues)

---

**Need help?** Join our [GitHub Discussions](https://github.com/adri-standard/adri/discussions) or [open an issue](https://github.com/adri-standard/adri/issues).
