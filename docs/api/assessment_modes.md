# Understanding ADRI Assessment Modes

ADRI provides two distinct assessment modes that embody the philosophy of "facilitation, not enforcement." Rather than penalizing data for lacking metadata, ADRI helps you understand your data quality and generates the metadata needed for agent communication.

## Quick Overview

| Mode | Purpose | When to Use | What it Does |
|------|---------|-------------|--------------|
| **Discovery** | Analyze quality & generate metadata | Raw data without metadata | Scores on intrinsic quality, creates metadata |
| **Validation** | Verify compliance with claims | Data with ADRI metadata | Checks if data meets declared standards |
| **Auto** (default) | Intelligently choose mode | Always recommended | Picks the right mode automatically |

## The Philosophy Shift

### Old Approach (Enforcement)
❌ "Your data scores 8/100 because it lacks metadata files"

### New Approach (Facilitation)
✅ "Your data scores 72/100 based on quality. Here are the metadata files to help agents understand it better!"

## Discovery Mode: Your Data Quality Helper

Discovery mode analyzes your actual data quality and **automatically generates** the ADRI metadata files that enable agent communication.

### What Discovery Mode Does

1. **Analyzes intrinsic quality** - Looks at your actual data
2. **Finds real issues** - Missing values, invalid formats, stale data
3. **Generates metadata** - Creates `.validity.json`, `.completeness.json`, etc.
4. **Scores fairly** - Based only on data quality, not metadata presence
5. **Suggests improvements** - Actionable recommendations

### Example Discovery Assessment

```bash
$ adri assess --source customer_data.csv

ADRI Assessment Report - Discovery Mode
======================================
Overall Score: 72/100 (Good)

Quality Issues Found:
💰 12 customers missing credit limits
📧 23 customers with invalid email formats
⏰ 45 records haven't been updated in 90+ days

✅ Generated Metadata Files:
- customer_data.validity.json
- customer_data.completeness.json
- customer_data.freshness.json
- customer_data.consistency.json
- customer_data.plausibility.json

Next Steps:
1. Review generated metadata files
2. Customize them for your specific needs
3. Use them to communicate quality to agents
```

### Generated Metadata Example

```json
// customer_data.validity.json (auto-generated)
{
  "_comment": "Auto-generated validity metadata. Please review and adjust.",
  "has_explicit_validity_info": true,
  "type_definitions": {
    "email": {
      "type": "string",
      "format": "email",
      "_detected_type": "text",
      "_confidence": 0.95
    },
    "credit_limit": {
      "type": "number",
      "range": [100.0, 50000.0],
      "_comment": "TODO: Verify if this range is correct"
    }
  }
}
```

## Validation Mode: Trust but Verify

Validation mode activates when ADRI metadata exists and verifies that your data meets its declared standards.

### What Validation Mode Does

1. **Requires metadata** - Only runs when ADRI metadata exists
2. **Verifies claims** - Checks data against declarations
3. **Scores compliance** - How well does data meet its promises?
4. **No penalties** - Just verification of claims

### Example Validation Assessment

```bash
$ adri assess --source customer_data.csv

ADRI Assessment Report - Validation Mode
========================================
Overall Score: 94/100 (Excellent)

Metadata Compliance:
✅ Data matches validity declarations
✅ Completeness meets stated requirements
⚠️  2 fields slightly below freshness claims
✅ Consistency rules all pass
✅ Plausibility checks satisfied

Verification Details:
- Claimed email format compliance: 100% (verified)
- Claimed completeness >95%: 97% (verified)
- Claimed update frequency <24h: 22h average (verified)
```

## Mode Selection Logic

ADRI's Auto mode intelligently selects the appropriate assessment mode:

```python
<!-- audience: ai-builders -->
# Example of mode selection logic (not meant to be executed directly)
def select_assessment_mode(data_path):
    """Determine which assessment mode to use based on data characteristics"""
    if has_adri_metadata_files(data_path):
        return "VALIDATION"  # Verify claims
    elif has_comprehensive_schema(data_path):
        return "VALIDATION"  # Schema acts as claims
    else:
        return "DISCOVERY"   # Analyze and generate
```

## Key Differences

| Aspect | Discovery Mode | Validation Mode |
|--------|---------------|-----------------|
| **Focus** | Intrinsic data quality | Claims compliance |
| **Metadata Required** | No | Yes |
| **Generates Metadata** | Yes | No |
| **Business Logic** | Enabled | Disabled |
| **Scoring Basis** | Actual quality | Meeting declarations |
| **Use Case** | First assessment | Ongoing verification |

## Practical Workflows

### Workflow 1: New Data Source

```python
<!-- audience: ai-builders -->
# First time - Discovery mode analyzes and generates
assessor = DataSourceAssessor()  # Auto → Discovery
report = assessor.assess_file("sales_data.csv")

print(f"Quality score: {report.overall_score}")
print(f"Generated files: {report.generated_metadata}")
```

### Workflow 2: CI/CD Pipeline

```python
<!-- audience: ai-builders -->
# With metadata - Validation mode verifies
assessor = DataSourceAssessor()  # Auto → Validation
report = assessor.assess_file("sales_data.csv")

if report.overall_score < 90:
    raise ValueError("Data quality below threshold")
```

### Workflow 3: Template Compliance

```python
<!-- audience: ai-builders -->
# Templates always trigger validation (example - not meant to be executed)
from adri import DataSourceAssessor

def assess_with_template(data_path, template_name):
    """Assess data against a template"""
    assessor = DataSourceAssessor()
    report, evaluation = assessor.assess_file_with_template(
        data_path, 
        template_name
    )
    return report, evaluation

# Example usage:
# report, evaluation = assess_with_template("data.csv", "financial-basel-iii-v1")
```

## Why This Approach?

### 1. **Helpful, Not Punitive**
Instead of penalizing missing metadata, we generate it for you.

### 2. **Clear Communication**
Generated metadata provides the ADRI protocol layer for agent communication.

### 3. **Progressive Enhancement**
Start with raw data → Get metadata → Verify compliance → Improve over time

### 4. **Aligned with Vision**
Embodies ADRI's principle of "facilitation, not enforcement"

## Common Questions

### "Why did my score improve without changing data?"
You're now being scored on actual data quality (Discovery) rather than metadata presence.

### "When should I create custom metadata?"
After Discovery generates starter metadata, customize it to:
- Add business-specific rules
- Set stricter thresholds
- Document domain knowledge

### "How do I enforce quality standards?"
1. Run Discovery to understand baseline
2. Customize generated metadata with requirements
3. Use Validation mode in CI/CD to verify

## Best Practices

### For Initial Assessment
```python
<!-- audience: ai-builders -->
# Example of initial assessment (not meant to be executed)
from adri import DataSourceAssessor

def initial_assessment(data_path):
    """Run initial discovery assessment and review metadata"""
    # Let Discovery mode help you understand
    assessor = DataSourceAssessor()
    report = assessor.assess_file(data_path)
    
    # Review generated metadata
    for dimension, filepath in report.generated_metadata.items():
        print(f"Review {dimension}: {filepath}")
    
    return report

# Example usage:
# report = initial_assessment("customer_data.csv")
```

### For Production Guards
```python
<!-- audience: ai-builders -->
# Ensure metadata exists and validate
@adri_guarded(min_score=85)
def process_data(filepath):
    # Your agent code here
    pass
```

### For Continuous Improvement
1. Start with Discovery mode baseline
2. Enhance metadata with business rules
3. Use Validation mode to track progress
4. Iterate based on agent needs

## Next Steps

- Try the [metadata generation example](../../examples/advanced/06_metadata_generation.py)
- Learn about [Enhancing Data Sources](ENHANCING_DATA_SOURCES.md)
- Explore [Templates](templates/README.md) for standardization

## Purpose & Test Coverage

**Why this file exists**: Explains ADRI's facilitation-focused assessment philosophy and how the two modes work together to help users improve data quality rather than penalize them.

**Key responsibilities**:
- Clarify the "facilitation, not enforcement" philosophy
- Explain Discovery mode's metadata generation
- Describe Validation mode's verification role
- Provide practical workflows and examples

**Test coverage**: Mode functionality is tested in tests/unit/test_assessment_modes.py
