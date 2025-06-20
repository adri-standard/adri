# Setting Thresholds

> **AI Builders**: Configure quality thresholds for your agents

## Overview

How to set appropriate quality thresholds for different types of AI agents and use cases.

## Threshold Types

### Completeness Thresholds
- **High Criticality**: 95%+ completeness required
- **Medium Criticality**: 85%+ completeness required  
- **Low Criticality**: 70%+ completeness acceptable

### Freshness Thresholds
- **Real-time Systems**: < 1 hour data age
- **Daily Operations**: < 24 hour data age
- **Analytical Systems**: < 7 days data age

### Validity Thresholds
- **Financial Data**: 99%+ validity required
- **Customer Data**: 95%+ validity required
- **Operational Data**: 90%+ validity acceptable

## Use Case Examples

### Customer Service Agent
```python
<!-- audience: ai-builders -->
thresholds = {
    'completeness': 0.90,
    'freshness': 3600,  # 1 hour
    'validity': 0.95,
    'consistency': 0.85
}
```

### Financial Analysis Agent
```python
<!-- audience: ai-builders -->
thresholds = {
    'completeness': 0.98,
    'freshness': 86400,  # 24 hours
    'validity': 0.99,
    'consistency': 0.95
}
```

## Next Steps

- [Implementing Guards](implementing-guards.md)
- [Troubleshooting](troubleshooting.md)
- [Framework Integration](framework-integration.md)
