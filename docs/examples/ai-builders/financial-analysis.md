# Financial Analysis Agent Example

> **AI Builders**: Protect financial analysis agents with ADRI

## Overview

Example implementation of ADRI guards for a financial analysis AI agent.

## Scenario

A financial analysis agent processes:
- Market data and pricing information
- Financial statements and reports
- Trading data and transaction history
- Risk metrics and compliance data

## Data Quality Requirements

### Market Data
- **Completeness**: 98%+ (all required fields)
- **Freshness**: < 15 minutes (real-time requirements)
- **Validity**: 99%+ (price ranges, data formats)
- **Consistency**: 95%+ (cross-source validation)

### Financial Reports
- **Completeness**: 95%+ (key financial metrics)
- **Validity**: 99%+ (calculation accuracy)
- **Plausibility**: 90%+ (reasonable financial ratios)

## Implementation

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from adri import Guard, Assessor

# Configure guard for financial analysis
guard = Guard(
    name="financial_analysis_guard",
    thresholds={
        'completeness': 0.98,
        'freshness': 900,  # 15 minutes
        'validity': 0.99,
        'consistency': 0.95,
        'plausibility': 0.90
    }
)

# Assess financial data before analysis
@guard.protect
def analyze_portfolio(portfolio_id):
    market_data = get_market_data()
    portfolio_data = get_portfolio_data(portfolio_id)
    
    # Guard ensures data quality for financial decisions
    # Critical for regulatory compliance
    
    return perform_risk_analysis(market_data, portfolio_data)
```

## Next Steps

- [Customer Service Example](customer-service.md)
- [Document Processing Example](document-processing.md)
- [Implementation Guide](ai-builders/implementing-guards.md)
