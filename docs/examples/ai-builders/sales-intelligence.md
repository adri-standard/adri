# Sales Intelligence Agent Example

> **AI Builders**: Protect sales intelligence agents with ADRI

## Overview

Example implementation of ADRI guards for a sales intelligence AI agent.

## Scenario

A sales intelligence agent analyzes:
- Lead scoring and qualification data
- Customer interaction history
- Sales pipeline and forecasting data
- Market intelligence and competitor data

## Data Quality Requirements

### Lead Data
- **Completeness**: 85%+ (contact info, company details)
- **Freshness**: < 24 hours (recent interactions)
- **Validity**: 90%+ (email, phone validation)
- **Consistency**: 85%+ (cross-platform alignment)

### Sales Pipeline
- **Completeness**: 90%+ (opportunity details)
- **Validity**: 95%+ (deal values, dates)
- **Plausibility**: 80%+ (realistic projections)

## Implementation

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from adri import Guard, Assessor

# Configure guard for sales intelligence
guard = Guard(
    name="sales_intelligence_guard",
    thresholds={
        'completeness': 0.85,
        'freshness': 86400,  # 24 hours
        'validity': 0.90,
        'consistency': 0.85,
        'plausibility': 0.80
    }
)

# Assess sales data before intelligence generation
@guard.protect
def generate_sales_insights(territory_id):
    lead_data = get_lead_data(territory_id)
    pipeline_data = get_pipeline_data(territory_id)
    
    # Guard ensures reliable sales intelligence
    # Improves forecast accuracy
    
    return analyze_sales_performance(lead_data, pipeline_data)
```

## Next Steps

- [Customer Service Example](customer-service.md)
- [Document Processing Example](document-processing.md)
- [Implementation Guide](ai-builders/implementing-guards.md)
