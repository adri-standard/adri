# Cross-Platform Development Best Practices

## Problem Statement

The ADRI project runs on **Windows, macOS, and Linux**. Recent CI failures revealed that Python's default text encoding differs by platform:

- **Windows**: cp1252 (Windows-1252)
- **macOS/Linux**: UTF-8

This causes **UnicodeDecodeError** when code written on macOS is tested on Windows CI.

## Root Cause

Python 3's `open()` function uses platform-dependent default encoding:

```python
# This fails on Windows if file contains Unicode:
with open('file.yaml', 'r') as f:  # Uses cp1252 on Windows
    content = f.read()
```

## Solutions

### 1. **Always Specify encoding='utf-8'** (Recommended)

```python
# ✅ CORRECT - Works on all platforms
with open('file.yaml', 'r', encoding='utf-8') as f:
    content = f.read()

# ✅ CORRECT - Writing files
with open('file.yaml', 'w', encoding='utf-8') as f:
    f.write(content)
```

### 2. **Use Python 3.11+ UTF-8 Mode** (Alternative)

Set environment variable:
```bash
export PYTHONUTF8=1
```

Or in code:
```python
import sys
import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
```

### 3. **Add Pre-Commit Hook** (Prevention)

Create `.pre-commit-hooks/check-utf8-encoding.py`:

```python
#!/usr/bin/env python3
"""Check that all file opens specify encoding='utf-8'."""

import re
import sys
from pathlib import Path

def check_file(filepath):
    """Check file for open() calls without encoding."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: open(...) without encoding=
    pattern = r"open\([^)]+\)(?!.*encoding=)"

    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        if re.search(pattern, line):
            # Ignore binary mode opens
            if "'rb'" in line or '"rb"' in line or "'wb'" in line or '"wb"' in line:
                continue
            issues.append((i, line.strip()))

    return issues

def main():
    """Check all Python files."""
    errors = []

    for pyfile in Path('src').rglob('*.py'):
        issues = check_file(pyfile)
        if issues:
            errors.append((pyfile, issues))

    for pyfile in Path('tests').rglob('*.py'):
        issues = check_file(pyfile)
        if issues:
            errors.append((pyfile, issues))

    if errors:
        print("❌ Found open() calls without encoding='utf-8':")
        for filepath, issues in errors:
            print(f"\n{filepath}:")
            for line_num, line in issues:
                print(f"  Line {line_num}: {line}")
        sys.exit(1)

    print("✅ All open() calls specify encoding")
    sys.exit(0)

if __name__ == '__main__':
    main()
```

Add to `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: check-utf8-encoding
      name: Check UTF-8 encoding in file operations
      entry: python .pre-commit-hooks/check-utf8-encoding.py
      language: system
      pass_filenames: false
```

## Affected ADRI Code

### Files That Need UTF-8 Encoding

**Any code that opens text files must use `encoding='utf-8'`:**

1. **YAML file reading**:
   - `src/adri/contracts/parser.py`
   - `src/adri/config/loader.py`
   - `tests/*` (all test files)

2. **CSV file operations**:
   - `src/adri/logging/local.py`
   - `src/adri/logging/reasoning.py`
   - `src/adri/logging/workflow.py`

3. **Standard generation**:
   - `src/adri/analysis/standard_generator.py`
   - `src/adri/cli/commands/generate_standard.py`

## Automated Detection Strategy

### Option A: Ruff Linter Rule (Best)

Add to `pyproject.toml`:

```toml
[tool.ruff]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "SIM", # flake8-simplify
    "PTH", # flake8-use-pathlib
]

# Custom rule to detect open() without encoding
[tool.ruff.lint.flake8-bugbear]
extend-immutable-calls = ["open"]
```

### Option B: Custom pytest Plugin

Create `tests/plugins/encoding_checker.py`:

```python
"""Pytest plugin to check file encoding in tests."""

import pytest
import warnings

class EncodingWarning(UserWarning):
    """Warning for file operations without encoding."""
    pass

def pytest_runtest_setup(item):
    """Hook to run before each test."""
    # Check if test opens files without encoding
    import inspect

    if hasattr(item, 'obj'):
        source = inspect.getsource(item.obj)
        if 'open(' in source and 'encoding=' not in source:
            if "'rb'" not in source and '"rb"' not in source:
                warnings.warn(
                    f"Test {item.name} may have encoding issues",
                    EncodingWarning
                )
```

Register in `conftest.py`:
```python
pytest_plugins = ["tests.plugins.encoding_checker"]
```

### Option C: GitHub Action Linter

Add to `.github/workflows/encoding-check.yml`:

```yaml
name: Encoding Check
on: [push, pull_request]

jobs:
  check-encoding:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check file operations
        run: |
          # Check for open() without encoding in Python files
          if grep -r "open(" --include="*.py" . | \
             grep -v "encoding=" | \
             grep -v "'rb'" | \
             grep -v '"rb"' | \
             grep -v "'wb'" | \
             grep -v '"wb"'; then
            echo "❌ Found open() calls without encoding='utf-8'"
            exit 1
          fi
          echo "✅ All file operations use explicit encoding"
```

## Recommended Implementation Plan

### Phase 1: Fix Existing Code (Immediate)

1. **Audit all `open()` calls**:
   ```bash
   grep -r "open(" --include="*.py" src/ tests/ | \
   grep -v "encoding=" | \
   grep -v "'rb'" | \
   grep -v '"rb"'
   ```

2. **Add `encoding='utf-8'`** to all text file operations

3. **Run Windows CI** to verify fix

### Phase 2: Prevention (This Sprint)

1. **Add pre-commit hook** for encoding checks
2. **Add Ruff linter rule** to catch in development
3. **Document in CONTRIBUTING.md**

### Phase 3: CI Enhancement (Next Sprint)

1. **Add encoding check** to GitHub Actions
2. **Test on Windows, macOS, Linux** in matrix
3. **Add encoding violation** to PR checklist

## Quick Audit Commands

### Find All File Opens Without Encoding

```bash
# Check source code
grep -rn "open(" src/ | grep -v "encoding=" | grep -v "rb" | grep -v "wb"

# Check tests
grep -rn "open(" tests/ | grep -v "encoding=" | grep -v "rb" | grep -v "wb"
```

### Find Unicode Characters in Files

```bash
# Find files with non-ASCII characters
find . -name "*.py" -o -name "*.yaml" | xargs file | grep UTF-8
```

## Standard Code Review Checklist

When reviewing PRs, check:

- [ ] All `open()` calls use `encoding='utf-8'` (except binary mode)
- [ ] CSV operations use `encoding='utf-8'`
- [ ] YAML operations use `encoding='utf-8'`
- [ ] JSON operations use `encoding='utf-8'` (though less critical)
- [ ] Tests pass on Windows CI

## ADRI-Specific Guidelines

### ✅ CORRECT Patterns

```python
# YAML operations
with open('standard.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

with open('standard.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(data, f)

# CSV operations
with open('log.csv', 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(row)

# JSON operations
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
```

### ❌ INCORRECT Patterns

```python
# ❌ Missing encoding
with open('file.yaml', 'r') as f:
    data = yaml.safe_load(f)

# ❌ Missing encoding in CSV
with open('log.csv', 'a', newline='') as f:
    writer = csv.writer(f)
```

## Impact Analysis

**Current Issue**: 1 test failed on Windows CI (out of 896 tests)

**If Not Fixed**: Would fail on:
- Windows development machines
- Windows production servers
- Any system with non-UTF-8 default encoding

**Best Practice**: Always be explicit about text encoding to ensure **deterministic behavior** across platforms.

## Related PEPs

- **PEP 597**: Add optional EncodingWarning (Python 3.10+)
- **PEP 686**: Make UTF-8 mode default (Python 3.15+)

## Summary

**Immediate Fix**: Add `encoding='utf-8'` to test (✅ DONE)

**Long-term Prevention**:
1. Pre-commit hook to detect missing encoding
2. Ruff linter rule
3. Documentation in CONTRIBUTING.md
4. CI check for encoding violations

**Priority**: HIGH - Prevents platform-specific bugs
**Effort**: LOW - Simple code changes, automated checks
**Impact**: HIGH - Ensures cross-platform compatibility
