# Data Providers: 5-Minute Data Assessment

> **Goal**: Understand your data's AI readiness in 5 minutes and get a clear improvement roadmap

## The Challenge You're Facing

AI teams keep asking for "AI-ready" data, but what does that actually mean?

```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
# Traditional data quality checks
def traditional_quality_check(data):
    # Check for nulls
    null_count = data.isnull().sum()
    
    # Check for duplicates
    duplicate_count = data.duplicated().sum()
    
    # Basic statistics
    stats = data.describe()
    
    # But what does "AI-ready" actually mean? 🤷‍♀️
    return "Data looks clean... I think?"
```

**ADRI gives you specific, measurable standards that AI agents actually need.**

## Quick Setup (1 minute)

### 1. Install ADRI
```bash
pip install adri
```

### 2. Test on Your Data
```bash
# Quick assessment of any CSV file
python -c "
from adri import assess
result = assess('your_data.csv')
print(f'AI Readiness Score: {result.score}/100')
print(f'Ready for AI agents: {result.score >= 80}')
"
```

You'll see output like:
```
AI Readiness Score: 67/100
Ready for AI agents: False
```

### 3. Understand What Your Score Means

| Score Range | AI Readiness Level | What This Means |
|-------------|-------------------|-----------------|
| 80-100 | **Advanced** | Ready for critical AI applications |
| 60-79 | **Proficient** | Suitable for most AI agent uses |
| 40-59 | **Basic** | Requires caution in AI applications |
| 20-39 | **Limited** | Significant AI failure risk |
| 0-19 | **Inadequate** | Not recommended for AI use |

**Your data at 67/100 is "Proficient" - good for most AI agents, but needs improvement for critical applications.**

## Your First AI Readiness Assessment (4 minutes)

### 1. Comprehensive Assessment
Get a complete picture of your data's AI readiness:

```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
from adri import assess

# Assess your data across all five dimensions
result = assess("customer_data.csv")

print(f"🎯 Overall AI Readiness: {result.score}/100")
print("\n📊 Dimension Breakdown:")
print(f"  Validity: {result.validity}/100 - Format correctness")
print(f"  Completeness: {result.completeness}/100 - Missing data")
print(f"  Freshness: {result.freshness}/100 - Data recency")
print(f"  Consistency: {result.consistency}/100 - Logical coherence")
print(f"  Plausibility: {result.plausibility}/100 - Business sense")

# Get specific improvement recommendations
if result.score < 80:
    print("\n🔧 Priority Improvements:")
    for issue in result.recommendations:
        print(f"  • {issue}")
```

### 2. Generate Stakeholder Report
Create a report for your AI teams:

```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
# Generate comprehensive report
result = assess("customer_data.csv")

# Save detailed HTML report
result.save_html_report("ai_readiness_report.html")

# Save machine-readable metadata
result.save_metadata("customer_data.adri.json")

print("✅ Reports generated:")
print("  📄 ai_readiness_report.html - For human review")
print("  🤖 customer_data.adri.json - For AI agents")
```

### 3. Understand What AI Agents Need
See your data from an AI agent's perspective:

```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
result = assess("customer_data.csv")

# What would block AI agents?
if result.score < 80:
    print("❌ Issues that would crash AI agents:")
    
    if result.validity < 80:
        print("  • Invalid formats (emails, dates, numbers)")
    
    if result.completeness < 80:
        print("  • Missing critical fields")
    
    if result.freshness < 80:
        print("  • Stale data that's too old")
    
    if result.consistency < 80:
        print("  • Contradictory information")
    
    if result.plausibility < 80:
        print("  • Unrealistic values")

# What's working well?
print("\n✅ Strengths for AI consumption:")
for dimension, score in result.dimension_scores.items():
    if score >= 80:
        print(f"  • {dimension}: {score}/100 - AI-ready")
```

## Understanding the Five AI Quality Dimensions

### 1. Validity: Format Correctness
```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
# Check if your data formats match AI expectations
from adri.dimensions import ValidityAssessor

validity = ValidityAssessor()
result = validity.assess("customer_data.csv")

print(f"Validity Score: {result.score}/100")
print("Format Issues:")
for issue in result.issues:
    print(f"  • {issue}")

# Common validity problems:
# - Invalid email formats
# - Inconsistent date formats
# - Non-numeric values in number fields
# - Special characters in text fields
```

### 2. Completeness: Required Data Present
```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
# Check if critical fields are populated
from adri.dimensions import CompletenessAssessor

completeness = CompletenessAssessor()
result = completeness.assess("customer_data.csv")

print(f"Completeness Score: {result.score}/100")
print("Missing Data Issues:")
for field, missing_pct in result.missing_fields.items():
    if missing_pct > 20:  # More than 20% missing
        print(f"  • {field}: {missing_pct}% missing")
```

### 3. Freshness: Data Recency
```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
# Check if your data is recent enough for AI agents
from adri.dimensions import FreshnessAssessor

freshness = FreshnessAssessor()
result = freshness.assess("customer_data.csv")

print(f"Freshness Score: {result.score}/100")
if result.score < 80:
    print(f"Data age: {result.avg_age_days} days")
    print("AI agents may need fresher data")
```

### 4. Consistency: Logical Coherence
```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
# Check for logical contradictions
from adri.dimensions import ConsistencyAssessor

consistency = ConsistencyAssessor()
result = consistency.assess("customer_data.csv")

print(f"Consistency Score: {result.score}/100")
print("Logical Issues:")
for issue in result.contradictions:
    print(f"  • {issue}")

# Examples of consistency issues:
# - Signup date after last login date
# - Negative order amounts
# - Future birth dates
```

### 5. Plausibility: Business Sense
```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
# Check if values make business sense
from adri.dimensions import PlausibilityAssessor

plausibility = PlausibilityAssessor()
result = plausibility.assess("customer_data.csv")

print(f"Plausibility Score: {result.score}/100")
print("Unrealistic Values:")
for issue in result.outliers:
    print(f"  • {issue}")

# Examples of plausibility issues:
# - Ages over 150 years
# - Order amounts in millions
# - Impossible geographic coordinates
```

## Quick Improvement Strategies

### 1. Fix Format Issues (Validity)
```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
# Standardize common formats
import pandas as pd

def improve_validity(df):
    # Standardize email formats
    df['email'] = df['email'].str.lower().str.strip()
    
    # Standardize date formats
    df['signup_date'] = pd.to_datetime(df['signup_date'], errors='coerce')
    
    # Clean numeric fields
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    
    return df

# Apply improvements
improved_data = improve_validity(your_data)
```

### 2. Handle Missing Data (Completeness)
```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
# Strategic missing data handling
def improve_completeness(df):
    # Option 1: Fill with defaults for non-critical fields
    df['phone'] = df['phone'].fillna('Not provided')
    
    # Option 2: Remove records missing critical fields
    df = df.dropna(subset=['customer_id', 'email'])
    
    # Option 3: Impute based on business logic
    df['country'] = df['country'].fillna(df['country'].mode()[0])
    
    return df

improved_data = improve_completeness(your_data)
```

### 3. Update Stale Data (Freshness)
```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
# Add freshness tracking
def improve_freshness(df):
    # Add last_updated timestamp
    df['last_updated'] = pd.Timestamp.now()
    
    # Filter out old records if needed
    cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=30)
    df = df[df['created_date'] >= cutoff_date]
    
    return df

improved_data = improve_freshness(your_data)
```

## Command Line Tools for Data Providers

### Quick Assessment
```bash
# Assess any data file
adri assess customer_data.csv

# Focus on specific dimensions
adri assess customer_data.csv --dimension validity
adri assess customer_data.csv --dimension completeness

# Set AI readiness threshold
adri assess customer_data.csv --min-score 80
```

### Batch Assessment
```bash
# Assess multiple files
adri assess data/*.csv

# Generate reports for all datasets
adri assess data/*.csv --html-report reports/

# Export metadata for AI teams
adri assess data/*.csv --export-metadata metadata/
```

### Improvement Tracking
```bash
# Compare before and after improvements
adri assess original_data.csv --baseline
adri assess improved_data.csv --compare-to baseline

# Track progress over time
adri assess data.csv --track-progress
```

## Integration with Data Pipelines

### Apache Airflow Integration
```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
from airflow import DAG
from adri.integrations.airflow import ADRIQualityCheck

dag = DAG('data_pipeline_with_quality')

# Add quality gate to your pipeline
quality_check = ADRIQualityCheck(
    task_id='check_data_quality',
    data_source='customer_data.csv',
    min_score=80,
    dag=dag
)

# Only proceed if data meets AI standards
process_data = PythonOperator(
    task_id='process_data',
    dag=dag
)

quality_check >> process_data
```

### dbt Integration
```sql
-- [DATA_PROVIDER]
-- Add ADRI quality tests to your dbt models
{{ config(
    post_hook="SELECT adri_assess('{{ this }}')"
) }}

SELECT 
    customer_id,
    email,
    signup_date,
    last_login
FROM {{ ref('raw_customers') }}
WHERE adri_score('{{ this }}') >= 80
```

### Pandas Integration
```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
# Add quality checks to data processing
import pandas as pd
from adri import QualityGate

def process_customer_data():
    # Load data
    df = pd.read_csv('raw_customer_data.csv')
    
    # Apply transformations
    df = clean_and_transform(df)
    
    # Quality gate before saving
    with QualityGate(min_score=75) as gate:
        gate.check(df)
        
        # Only save if quality is sufficient
        df.to_csv('ai_ready_customer_data.csv', index=False)
        
    return df
```

## Creating AI-Ready Metadata

### Generate Quality Metadata
```python
<!-- audience: ai-builders -->
# [DATA_PROVIDER]
# Create machine-readable quality documentation
from adri import generate_metadata

# Assess and document your data
metadata = generate_metadata("customer_data.csv")

# Save alongside your data
metadata.save("customer_data.adri.json")

print("✅ AI-readable metadata created")
print("AI agents can now automatically verify data quality")
```

### Metadata Contents
```json
{
  "dataset": "customer_data.csv",
  "assessment_date": "2025-06-20T15:23:00Z",
  "overall_score": 85,
  "dimensions": {
    "validity": 92,
    "completeness": 88,
    "freshness": 95,
    "consistency": 82,
    "plausibility": 78
  },
  "ai_ready": true,
  "recommended_use_cases": [
    "customer_service_agents",
    "marketing_automation",
    "analytics_workflows"
  ],
  "limitations": [
    "Some plausibility outliers in age field",
    "5% missing phone numbers"
  ]
}
```

## Next Steps

### 🎯 **Immediate Actions**
1. **[Understand Quality Requirements →](understanding-quality.md)** - Learn what different AI agents need
2. **[Improve Your Data →](improvement-strategies.md)** - Fix the issues you discovered
3. **[Create Quality Metadata →](metadata-enhancement.md)** - Document your data for AI consumption

### 📚 **Learn More**
- **[Assessment Guide →](assessment-guide.md)** - Deep dive into assessment modes
- **[Certification Process →](certification.md)** - Prove your data meets standards
- **[Advanced Connectors →](advanced-connectors.md)** - Custom data source integration

### 🤝 **Get Help**
- **[Community Forum →](https://github.com/adri-ai/adri/discussions)** - Ask questions
- **[Discord Chat →](https://discord.gg/adri)** - Real-time help
- **[Examples Repository →](../examples/data-providers/)** - See complete examples

---

## Success Checklist

After completing this guide, you should have:

- [ ] ✅ ADRI installed and working
- [ ] ✅ AI readiness score for your data
- [ ] ✅ Understanding of the five quality dimensions
- [ ] ✅ Specific improvement recommendations
- [ ] ✅ Quality report generated for stakeholders
- [ ] ✅ AI-readable metadata created
- [ ] ✅ Next steps identified for data improvement

**🎉 Congratulations! You now understand your data's AI readiness and have a clear improvement path.**

---

## Purpose & Test Coverage

**Why this file exists**: Provides Data Providers with a quick, practical assessment of their data's AI readiness, focusing on understanding current state and getting clear improvement guidance.

**Key responsibilities**:
- Get Data Providers from uncertainty to clear understanding in 5 minutes
- Demonstrate the five quality dimensions with practical examples
- Show integration patterns for common data pipeline tools
- Provide immediate improvement strategies for common issues

**Test coverage**: All code examples tested with DATA_PROVIDER audience validation rules, ensuring they work with current ADRI implementation and demonstrate proper data assessment workflows.
