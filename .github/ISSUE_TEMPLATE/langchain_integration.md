---
name: LangChain Integration Issue
about: Report issues with LangChain framework integration
title: '[LangChain] '
labels: ['langchain', 'framework-integration']
assignees: ''
---

## LangChain Integration Issue

**Describe the issue**
A clear and concise description of what the problem is with LangChain integration.

**LangChain Version**
- LangChain version: [e.g. 0.1.0]
- ADRI version: [e.g. 4.0.0]

**Code Example**
```python
from langchain import LLMChain
from adri.decorators.guard import adri_protected

@adri_protected(data_param='data', min_score=70)
def my_langchain_function(data):
    # Your LangChain code here
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

---
**Linking Instructions**: Once this issue is created, reference it in your branch name using the format: `fix/issue-{number}-brief-description` or `feat/issue-{number}-brief-description` (e.g., `fix/issue-456-langchain-decorator-bug` or `feat/issue-789-langchain-new-feature`) when creating a PR to address this issue.
