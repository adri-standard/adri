# Basic Usage Tutorial

Learn the fundamentals of ADRI through hands-on examples.

## Step 1: Load Data

```python
<!-- audience: ai-builders -->
import pandas as pd
from adri import Assessor

# Load sample data
data = pd.read_csv('customer_data.csv')
print(data.head())
```

## Step 2: Create Assessor

```python
<!-- audience: ai-builders -->
assessor = Assessor()
```

## Step 3: Run Assessment

```python
<!-- audience: ai-builders -->
results = assessor.assess(data, dimensions=['completeness', 'validity'])
```

## Step 4: Analyze Results

```python
<!-- audience: ai-builders -->
print(f"Overall Score: {results.overall_score}")
print(f"Completeness: {results.completeness.score}")
print(f"Validity: {results.validity.score}")
```
