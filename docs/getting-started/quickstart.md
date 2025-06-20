# ADRI Quickstart Guide

Get up and running with ADRI in minutes.

## Installation

```bash
pip install adri
```

## Basic Usage

```python
<!-- audience: ai-builders -->
from adri import Assessor
from adri.connectors import FileConnector

# Create assessor
assessor = Assessor()

# Load data
connector = FileConnector("data.csv")
data = connector.load()

# Run assessment
results = assessor.assess(data, dimensions=['completeness', 'validity'])

# View results
print(results.summary())
```

## Next Steps

- [Learn about dimensions](../reference/dimensions/index.md)
- [Explore examples](../examples/index.md)
- [Read the implementation guide](../guides/implementation-guide.md)
