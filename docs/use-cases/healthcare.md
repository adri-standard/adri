# Healthcare Use Case

ADRI assessment patterns for healthcare data.

## Common Data Quality Challenges

- Data completeness across multiple systems
- Regulatory compliance requirements
- Real-time data freshness needs

## Recommended Assessment Configuration

```python
<!-- audience: data-providers -->
from adri import Assessor
from adri.templates import TemplateLoader

# Load industry template
loader = TemplateLoader()
template = loader.load('healthcare')
assessor = template.create_assessor()

# Run assessment
results = assessor.assess(data)
```

## Key Metrics

- Completeness: >95%
- Validity: >90%
- Freshness: <24 hours
