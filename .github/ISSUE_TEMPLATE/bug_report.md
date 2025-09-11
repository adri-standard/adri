---
name: Bug Report
about: Report a general bug or unexpected behavior in ADRI
title: '[Bug] '
labels: ['bug', 'needs-triage']
assignees: ''
---

## Bug Report

**Describe the bug**
A clear and concise description of what the bug is.

**Steps to Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
A clear and concise description of what you expected to happen.

**Actual Behavior**
A clear and concise description of what actually happened.

**Code Example (if applicable)**
```python
from adri.decorators.guard import adri_protected
import pandas as pd

# Minimal code example that demonstrates the bug
@adri_protected(data_param='data', min_score=70)
def example_function(data):
    # Your code here
    return data

# Sample data or usage that triggers the bug
df = pd.DataFrame({
    # Your test data here
})

result = example_function(df)
```

**Error Messages**
```
Paste any error messages, stack traces, or logs here
```

**Environment**
- ADRI version: [e.g. 4.0.0]
- Python version: [e.g. 3.11.0]
- Operating System: [e.g. macOS 13.0, Windows 11, Ubuntu 22.04]
- Installation method: [e.g. pip install adri, conda install adri]

**Framework Integration (if applicable)**
<!-- Check if this bug occurs with specific frameworks -->
- [ ] LangChain
- [ ] CrewAI
- [ ] AutoGen
- [ ] Haystack
- [ ] LlamaIndex
- [ ] LangGraph
- [ ] Semantic Kernel
- [ ] Generic/Framework-agnostic
- [ ] Not applicable

**Additional Context**
Add any other context about the problem here, including screenshots if helpful.

**Workaround (if any)**
If you've found a temporary workaround, please describe it here.

---
**Linking Instructions**: Once this issue is created, reference it in your branch name using the format: `fix/issue-{number}-brief-description` (e.g., `fix/issue-123-decorator-crash-bug`) when creating a PR to fix this bug.

**Note**: For data quality specific bugs, please use the [Data Quality Bug Report](https://github.com/adri-standard/adri/issues/new?assignees=&labels=bug%2Cdata-quality&template=data_quality_bug.md&title=%5BBug%5D+) template instead.
