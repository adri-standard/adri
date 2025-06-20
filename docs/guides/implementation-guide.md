# Implementation Guide

This guide covers advanced implementation patterns for ADRI.

## Architecture Overview

ADRI follows a modular architecture with these key components:

- **Assessors** - Core assessment engine
- **Connectors** - Data source integrations
- **Dimensions** - Quality measurement categories
- **Rules** - Specific quality checks
- **Templates** - Reusable configurations

## Custom Rules

```python
<!-- audience: standard-contributors -->
from adri.rules.base import Rule

class CustomValidityRule(Rule):
    def evaluate(self, data):
        # Custom validation logic
        return self.create_result(passed=True, score=0.95)
```

## Integration Patterns

### With Pandas

```python
<!-- audience: ai-builders -->
import pandas as pd
from adri import Assessor

df = pd.read_csv("data.csv")
assessor = Assessor()
results = assessor.assess(df)
```

### With Databases

```python
<!-- audience: data-providers -->
from adri.connectors import DatabaseConnector

connector = DatabaseConnector(
    connection_string="postgresql://user:pass@host/db"
)
data = connector.query("SELECT * FROM customer_data")
```
