# ADRI Quality Dimensions Reference

> **Technical Reference**: Complete documentation of ADRI's five quality dimensions for data assessment

## Overview

The Agent Data Readiness Index (ADRI) evaluates data quality across five critical dimensions that directly impact AI agent performance. Each dimension contributes up to 20 points toward the overall 100-point ADRI score.

## Quick Navigation

### 📊 **Quality Dimensions**
- [Validity](#validity) - Data types, formats, and ranges
- [Completeness](#completeness) - Missing data and coverage
- [Freshness](#freshness) - Data currency and timeliness
- [Consistency](#consistency) - Internal data coherence
- [Plausibility](#plausibility) - Real-world reasonableness

### 🔧 **Technical Details**
- [Scoring Methodology](#scoring-methodology) - How scores are calculated
- [Assessment Modes](#assessment-modes) - Discovery vs Validation approaches
- [Configuration Options](#configuration-options) - Customizing dimension behavior

---

## Quality Dimensions

### Validity

**Purpose**: Ensures data adheres to required types, formats, and ranges with explicit communication to agents.

**Key Assessment Areas**:
- **Data Types**: Are field types explicitly defined and consistent?
- **Format Patterns**: Are date formats, ID patterns, and structured data properly formatted?
- **Value Ranges**: Are numeric ranges and allowed values clearly defined?
- **Validation Rules**: Are validation constraints documented and enforced?

**Scoring Components** (20 points total):
- Types Defined (5 points)
- Formats Defined (3 points) 
- Ranges Defined (3 points)
- Validation Performed (3 points)
- Validation Communicated (6 points)

**Common Issues**:
- Inconsistent data types across records
- Invalid date formats or patterns
- Values outside expected ranges
- Missing validation metadata

**Best Practices**:
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Example validation metadata
{
  "rules": [
    {
      "field": "customer_id",
      "type": "string",
      "pattern": "^[A-Z]{2}\\d{4}$"
    },
    {
      "field": "price", 
      "type": "number",
      "min_value": 0,
      "max_value": 10000
    }
  ]
}
```

### Completeness

**Purpose**: Evaluates whether all expected data is present and missing information is properly communicated.

**Key Assessment Areas**:
- **Overall Coverage**: What percentage of expected data is present?
- **Missing Value Handling**: Are missing values distinguished from nulls?
- **Required Fields**: Are mandatory fields properly identified?
- **Section Completeness**: Is completeness tracked at logical data section levels?

**Scoring Components** (20 points total):
- Overall Completeness (5 points)
- Null Distinction (5 points)
- Explicit Metrics (5 points)
- Section Awareness (5 points)

**Common Issues**:
- High percentage of missing values
- Unclear distinction between missing and null
- No explicit completeness metrics
- Missing data in critical fields

**Best Practices**:
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Example completeness metadata
{
  "overall_completeness_percent": 98.5,
  "missing_value_markers": ["N/A", "-999", "NULL"],
  "required_fields": ["customer_id", "name", "email"],
  "section_completeness": {
    "contact_info": {
      "fields": ["email", "phone", "address"],
      "completeness_percent": 83.7
    }
  }
}
```

### Freshness

**Purpose**: Assesses data currency and timeliness to ensure agents work with up-to-date information.

**Key Assessment Areas**:
- **Data Age**: How recent is the data relative to its intended use?
- **Update Frequency**: Is data refreshed at appropriate intervals?
- **Temporal Tracking**: Are timestamps and versioning properly maintained?
- **Staleness Detection**: Are outdated records identified and handled?

**Scoring Components** (20 points total):
- Recency Score (8 points)
- Update Frequency (4 points)
- Temporal Metadata (4 points)
- Staleness Handling (4 points)

**Common Issues**:
- Data older than business requirements
- Irregular or unknown update schedules
- Missing timestamp information
- No mechanism to detect stale data

**Best Practices**:
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Example freshness metadata
{
  "last_updated": "2025-06-20T15:30:00Z",
  "update_frequency": "daily",
  "data_age_hours": 2.5,
  "freshness_requirements": {
    "customer_data": "24_hours",
    "pricing_data": "1_hour",
    "inventory_data": "15_minutes"
  }
}
```

### Consistency

**Purpose**: Evaluates internal data coherence and logical relationships between fields.

**Key Assessment Areas**:
- **Cross-Field Logic**: Do related fields maintain logical relationships?
- **Referential Integrity**: Are foreign key relationships maintained?
- **Business Rules**: Are domain-specific constraints enforced?
- **Format Consistency**: Are similar fields formatted consistently?

**Scoring Components** (20 points total):
- Cross-Field Validation (8 points)
- Referential Integrity (6 points)
- Business Rule Compliance (4 points)
- Format Standardization (2 points)

**Common Issues**:
- Contradictory information between fields
- Broken foreign key relationships
- Violation of business logic rules
- Inconsistent formatting across similar fields

**Best Practices**:
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Example consistency rules
{
  "cross_field_rules": [
    {
      "rule": "end_date_after_start_date",
      "fields": ["start_date", "end_date"],
      "condition": "end_date >= start_date"
    }
  ],
  "referential_integrity": [
    {
      "foreign_key": "customer_id",
      "references": "customers.customer_id"
    }
  ]
}
```

### Plausibility

**Purpose**: Assesses whether data values are reasonable and believable in real-world context.

**Key Assessment Areas**:
- **Statistical Reasonableness**: Are values within expected statistical ranges?
- **Business Logic**: Do values make sense in business context?
- **Outlier Detection**: Are extreme values identified and validated?
- **Domain Knowledge**: Are values consistent with domain expertise?

**Scoring Components** (20 points total):
- Statistical Analysis (8 points)
- Business Logic Validation (6 points)
- Outlier Assessment (4 points)
- Domain Validation (2 points)

**Common Issues**:
- Statistically impossible values
- Business-illogical combinations
- Unvalidated extreme outliers
- Values inconsistent with domain knowledge

**Best Practices**:
```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Example plausibility rules
{
  "statistical_bounds": {
    "age": {"min": 0, "max": 150},
    "salary": {"min": 0, "max": 10000000}
  },
  "business_rules": [
    {
      "rule": "discount_percentage_valid",
      "field": "discount_percent",
      "condition": "0 <= value <= 100"
    }
  ]
}
```

---

## Scoring Methodology

### Default Mode Scoring

In default mode, each dimension contributes exactly 20 points to the total 100-point ADRI score:

```
Total ADRI Score = Validity (20) + Completeness (20) + Freshness (20) + Consistency (20) + Plausibility (20)
```

Each dimension's 20 points are distributed across its specific scoring components as detailed above.

### Template Mode Scoring

When using templates, you can customize the weight distribution:

```yaml
# [STANDARD_CONTRIBUTOR]
dimensions:
  validity:
    weight: 0.25      # 25% of total score
    rules:
      - rule: type_consistency
        weight: 0.60   # 60% of validity score
      - rule: format_validation
        weight: 0.40   # 40% of validity score
  
  completeness:
    weight: 0.30      # 30% of total score
    # ... rules configuration
```

### Explicit vs Implicit Assessment

**Explicit Assessment** (Preferred):
- Awards full points when proper metadata is provided
- Encourages data providers to document quality characteristics
- Enables agents to make informed decisions about data usage

**Implicit Assessment** (Fallback):
- Provides automated analysis when metadata is missing
- Awards partial points (typically 50-90% of maximum)
- Helps identify quality issues but doesn't guarantee agent awareness

---

## Assessment Modes

### Discovery Mode

**Purpose**: Analyze raw data and suggest quality improvements

**Behavior**:
- Performs comprehensive automated analysis
- Identifies potential quality issues
- Suggests metadata and documentation improvements
- Awards points for both explicit and implicit indicators

**Best For**:
- New data sources without established quality processes
- Exploratory data analysis
- Initial quality baseline establishment

### Validation Mode

**Purpose**: Verify compliance with established quality standards

**Behavior**:
- Focuses on explicit metadata and documentation
- Validates against predefined templates and rules
- Emphasizes agent-accessible quality information
- May penalize missing explicit metadata more heavily

**Best For**:
- Production data sources with established standards
- Compliance verification
- Agent deployment readiness assessment

---

## Configuration Options

### Global Configuration

Configure dimension behavior through YAML, environment variables, or Python API:

```yaml
# [STANDARD_CONTRIBUTOR]
# Global dimension configuration
dimensions:
  require_explicit_metadata: true
  implicit_assessment_penalty: 0.5
  
  validity:
    max_types_defined_score: 5
    max_validation_communicated_score: 6
    
  completeness:
    minimum_threshold: 0.80
    require_section_tracking: true
    
  freshness:
    default_max_age_hours: 24
    require_update_frequency: true
    
  consistency:
    enable_cross_field_validation: true
    require_referential_integrity: false
    
  plausibility:
    statistical_outlier_threshold: 3.0
    require_business_rules: true
```

### Environment Variables

```bash
# [STANDARD_CONTRIBUTOR]
export ADRI_REQUIRE_EXPLICIT_METADATA=true
export ADRI_VALIDITY_MAX_SCORE=20
export ADRI_COMPLETENESS_MIN_THRESHOLD=0.80
export ADRI_FRESHNESS_MAX_AGE_HOURS=24
export ADRI_CONSISTENCY_CROSS_FIELD=true
export ADRI_PLAUSIBILITY_OUTLIER_THRESHOLD=3.0
```

### Python API Configuration

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri import configure
from adri.dimensions import DimensionConfig

# Configure all dimensions
configure(
    dimensions=DimensionConfig(
        require_explicit_metadata=True,
        validity={
            "max_validation_score": 6,
            "require_type_definitions": True
        },
        completeness={
            "minimum_threshold": 0.80,
            "require_section_tracking": True
        },
        freshness={
            "max_age_hours": 24,
            "require_update_frequency": True
        }
    )
)
```

---

## Companion Files

ADRI looks for dimension-specific companion files to find explicit quality metadata:

### File Naming Conventions

| Dimension | File Pattern | Purpose |
|-----------|--------------|---------|
| Validity | `{filename}.validity.json` | Validation rules and type definitions |
| Completeness | `{filename}.completeness.json` | Completeness metrics and requirements |
| Freshness | `{filename}.freshness.json` | Update schedules and age requirements |
| Consistency | `{filename}.consistency.json` | Cross-field rules and integrity constraints |
| Plausibility | `{filename}.plausibility.json` | Business rules and statistical bounds |

### Universal Metadata

```json
{
  "data_source": "customer_transactions.csv",
  "assessment_date": "2025-06-20T15:30:00Z",
  "adri_version": "0.3.0",
  "dimensions": {
    "validity": { /* dimension-specific metadata */ },
    "completeness": { /* dimension-specific metadata */ },
    "freshness": { /* dimension-specific metadata */ },
    "consistency": { /* dimension-specific metadata */ },
    "plausibility": { /* dimension-specific metadata */ }
  }
}
```

---

## Integration Patterns

### Framework Integration

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri import DataSourceAssessor
from adri.connectors import FileConnector

# Basic dimension assessment
connector = FileConnector("data.csv")
assessor = DataSourceAssessor(connector)
result = assessor.assess()

# Access dimension-specific results
for dimension, score in result.dimension_scores.items():
    print(f"{dimension}: {score}/20")
    
    # Get dimension-specific issues
    issues = result.get_issues_by_dimension(dimension)
    for issue in issues:
        print(f"  - {issue['description']}")
```

### Custom Dimension Weights

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
# Emphasize certain dimensions for specific use cases
assessor = DataSourceAssessor(
    connector,
    dimension_weights={
        "validity": 0.30,      # 30% - Critical for structured data
        "completeness": 0.25,  # 25% - Important for analytics
        "freshness": 0.20,     # 20% - Important for real-time systems
        "consistency": 0.15,   # 15% - Standard importance
        "plausibility": 0.10   # 10% - Lower priority for this use case
    }
)
```

### Dimension-Specific Assessment

```python
<!-- audience: ai-builders -->
# [STANDARD_CONTRIBUTOR]
from adri.dimensions import ValidityAssessor, CompletenessAssessor

# Assess individual dimensions
validity_assessor = ValidityAssessor(connector)
validity_result = validity_assessor.assess()

completeness_assessor = CompletenessAssessor(connector)
completeness_result = completeness_assessor.assess()

print(f"Validity Score: {validity_result.score}/20")
print(f"Completeness Score: {completeness_result.score}/20")
```

---

## Best Practices

### For Data Providers

1. **Create Explicit Metadata**: Provide companion files for each dimension
2. **Document Quality Requirements**: Define thresholds and expectations clearly
3. **Implement Quality Monitoring**: Track dimension scores over time
4. **Communicate to Agents**: Ensure quality information is machine-readable

### For AI Builders

1. **Set Quality Thresholds**: Define minimum acceptable scores per dimension
2. **Monitor Dimension Trends**: Track quality changes over time
3. **Implement Quality Gates**: Prevent agents from using low-quality data
4. **Handle Quality Degradation**: Define fallback strategies for quality issues

### For Standard Contributors

1. **Extend Dimensions**: Add domain-specific quality assessments
2. **Create Custom Rules**: Implement business-specific validation logic
3. **Contribute Templates**: Share dimension configurations with community
4. **Improve Algorithms**: Enhance automated quality detection

---

## Common Issues and Solutions

### Low Validity Scores

**Symptoms**: Inconsistent data types, invalid formats, missing validation
**Solutions**:
- Define explicit data schemas
- Implement validation rules
- Create format specifications
- Document value ranges and constraints

### Low Completeness Scores

**Symptoms**: High missing value percentages, unclear null handling
**Solutions**:
- Improve data collection processes
- Define missing value markers
- Implement completeness tracking
- Create section-level metrics

### Low Freshness Scores

**Symptoms**: Outdated data, irregular updates, missing timestamps
**Solutions**:
- Implement regular update schedules
- Add timestamp tracking
- Define freshness requirements
- Monitor data age

### Low Consistency Scores

**Symptoms**: Contradictory fields, broken relationships, format inconsistencies
**Solutions**:
- Define cross-field validation rules
- Implement referential integrity checks
- Standardize formatting conventions
- Create business rule validation

### Low Plausibility Scores

**Symptoms**: Unrealistic values, statistical outliers, business logic violations
**Solutions**:
- Define statistical bounds
- Implement business rule validation
- Create outlier detection processes
- Add domain expertise validation

---

## Next Steps

### 📚 **Learn More**
- **[API Reference →](../api/)** - Technical implementation details
- **[Templates →](../templates/)** - Assessment configuration
- **[Examples →](../../examples/)** - Real-world dimension usage

### 🛠️ **Extend Dimensions**
- **[Custom Dimensions Guide →](standard-contributors/extending-dimensions.md)** - Add new quality dimensions
- **[Custom Rules Guide →](standard-contributors/extending-rules.md)** - Create validation rules
- **[Testing Guide →](standard-contributors/testing-guide.md)** - Test dimension implementations

### 🤝 **Get Help**
- **[Community Forum →](https://github.com/adri-ai/adri/discussions)** - Ask questions
- **[Discord Chat →](https://discord.gg/adri)** - Real-time help
- **[Issue Tracker →](https://github.com/adri-ai/adri/issues)** - Report bugs

---

## Purpose & Test Coverage

**Why this file exists**: Provides comprehensive technical reference for all five ADRI quality dimensions, serving as the authoritative guide for understanding how data quality is assessed from an AI agent perspective.

**Key responsibilities**:
- Document all five quality dimensions with scoring methodology
- Explain explicit vs implicit assessment approaches
- Provide configuration options and integration patterns
- Guide best practices for achieving high dimension scores

**Test coverage**: All dimension examples and scoring calculations tested with STANDARD_CONTRIBUTOR audience validation rules, ensuring accurate representation of ADRI's quality assessment capabilities.
