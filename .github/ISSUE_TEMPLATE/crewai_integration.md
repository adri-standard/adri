---
name: CrewAI Integration Issue
about: Report issues with CrewAI framework integration
title: '[CrewAI] '
labels: ['crewai', 'framework-integration']
assignees: ''
---

## CrewAI Integration Issue

**Describe the issue**
A clear and concise description of what the problem is with CrewAI integration.

**CrewAI Version**
- CrewAI version: [e.g. 0.1.0]
- ADRI version: [e.g. 4.0.0]

**Code Example**
```python
from crewai import Agent, Task, Crew
from adri.decorators.guard import adri_protected

@adri_protected(data_param='data', min_score=70)
def my_crewai_function(data):
    # Your CrewAI code here
    pass

# Provide minimal reproduction case
```

**Expected Behavior**
A clear description of what you expected to happen.

**Actual Behavior**
A clear description of what actually happened.

**Error Messages**
```
Paste any error messages here
```

**Environment**
- Python version: [e.g. 3.11]
- Operating System: [e.g. macOS 13.0]
- Installation method: [e.g. pip, conda]

**Additional Context**
Add any other context about the problem here.
