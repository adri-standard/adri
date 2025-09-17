---
name: Bug report
about: Create a report to help us improve ADRI
title: "[BUG] "
labels: bug
assignees: ''

---

## Bug Description
A clear and concise description of what the bug is.

## Steps to Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

## Actual Behavior
A clear and concise description of what actually happened.

## Code Sample
If applicable, provide a minimal code sample that reproduces the issue:

```python
# Your code here
from adri import adri_protected

@adri_protected(standard="your_standard")
def your_function(data):
    return data
```

## Environment Information
Please complete the following information:
- **ADRI Version**: [e.g., 4.0.0]
- **Python Version**: [e.g., 3.11.0]
- **Operating System**: [e.g., macOS, Ubuntu 22.04, Windows 11]
- **Installation Method**: [e.g., pip, conda, from source]

## Data Information
If the issue is related to data processing:
- **Data Type**: [e.g., CSV, Parquet, DataFrame]
- **Data Size**: [e.g., 1000 rows, 50MB]
- **Data Source**: [e.g., file, database, API]

## Error Output
If applicable, paste the full error traceback:

```
Paste error traceback here
```

## ADRI Configuration
If using custom configuration, please share relevant parts:

```yaml
# Your adri-config.yaml or relevant configuration
```

## Additional Context
Add any other context about the problem here, such as:
- Screenshots (if applicable)
- Related issues or discussions
- Workarounds you've tried
- Impact on your workflow

## Checklist
- [ ] I have searched existing issues to make sure this is not a duplicate
- [ ] I have provided all the requested information above
- [ ] I can reproduce this issue consistently
- [ ] This issue is specific to ADRI (not a general Python/pandas issue)
