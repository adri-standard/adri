# Customer Service Agent Example

> **AI Builders**: Protect customer service agents with ADRI

## Overview

Example implementation of ADRI guards for a customer service AI agent.

## Scenario

A customer service agent needs access to:
- Customer profiles and history
- Product information and pricing
- Support ticket data
- Knowledge base articles

## Data Quality Requirements

### Customer Data
- **Completeness**: 90%+ (contact info, account status)
- **Freshness**: < 1 hour (recent interactions)
- **Validity**: 95%+ (email formats, phone numbers)

### Product Data
- **Completeness**: 95%+ (pricing, availability)
- **Freshness**: < 4 hours (inventory updates)
- **Consistency**: 90%+ (cross-system alignment)

## Implementation

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from adri import Guard, Assessor

# Configure guard for customer service agent
guard = Guard(
    name="customer_service_guard",
    thresholds={
        'completeness': 0.90,
        'freshness': 3600,  # 1 hour
        'validity': 0.95,
        'consistency': 0.90
    }
)

# Assess customer data before agent interaction
@guard.protect
def handle_customer_inquiry(customer_id, inquiry):
    customer_data = get_customer_data(customer_id)
    
    # Guard automatically validates data quality
    # Raises exception if thresholds not met
    
    return process_inquiry(customer_data, inquiry)
```

## Next Steps

- [Document Processing Example](document-processing.md)
- [Financial Analysis Example](financial-analysis.md)
- [Implementation Guide](ai-builders/implementing-guards.md)
