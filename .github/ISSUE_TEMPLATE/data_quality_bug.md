---
name: Data Quality Bug Report
about: Report issues with data quality assessment or validation
title: '[Bug] '
labels: ['bug', 'data-quality']
assignees: ''
---

## Data Quality Bug Report

**Describe the bug**
A clear and concise description of what the bug is with data quality assessment.

**Data Quality Dimension**
Which dimension is affected? (check all that apply)
- [ ] Validity
- [ ] Completeness
- [ ] Freshness
- [ ] Consistency
- [ ] Plausibility

**Code Example**
```python
from adri.decorators.guard import adri_protected
import pandas as pd

@adri_protected(data_param='data', min_score=70)
def my_function(data):
    # Your code here
    return data

# Sample data that triggers the bug
df = pd.DataFrame({
    # Your test data here
})

result = my_function(df)
```

**Expected Behavior**
A clear description of what you expected to happen.

**Actual Behavior**
A clear description of what actually happened.

**ADRI Assessment Output**
```
Paste the ADRI assessment output here
```

**Environment**
- ADRI version: [e.g. 4.0.0]
- Python version: [e.g. 3.11]
- Pandas version: [e.g. 2.0.0]
- Operating System: [e.g. macOS 13.0]

**Additional Context**
Add any other context about the problem here, including data characteristics that might be relevant.

---
**Linking Instructions**: Once this issue is created, reference it in your branch name using the format: `fix/issue-{number}-brief-description` (e.g., `fix/issue-123-validity-dimension-bug`) when creating a PR to fix this bug.
