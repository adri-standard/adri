# Cross-Platform Path Testing Best Practices

## Root Cause Analysis

### The Windows CI Failure

**Test that Failed:**
```python
def test_default_config_path(self):
    reader = ADRILogReader({})
    assert str(reader.log_dir) == "ADRI/dev/audit-logs"  # ❌ FAILS ON WINDOWS
```

**Error on Windows:**
```
AssertionError: assert 'ADRI\\dev\\audit-logs' == 'ADRI/dev/audit-logs'
  - ADRI/dev/audit-logs
  ?     ^   ^
  + ADRI\dev\audit-logs
  ?     ^   ^
```

### Why This Happens

Python's `pathlib.Path` uses platform-specific path separators:
- **Unix/Mac**: `/` (forward slash)
- **Windows**: `\` (backslash)

When you call `str(path_object)`, it returns the platform-native representation, causing test failures when comparing against hardcoded Unix-style paths.

## Solutions

### ✅ Correct Approach: Use `as_posix()`

```python
def test_default_config_path(self):
    reader = ADRILogReader({})
    # Use as_posix() for cross-platform string comparison
    assert reader.log_dir.as_posix() == "ADRI/dev/audit-logs"  # ✅ WORKS EVERYWHERE
```

**Why it works:** `.as_posix()` always returns forward-slash paths regardless of platform.

### ✅ Alternative: Compare Path Objects

```python
def test_default_config_path(self):
    reader = ADRILogReader({})
    # Compare Path objects directly
    assert reader.log_dir == Path("ADRI/dev/audit-logs")  # ✅ WORKS EVERYWHERE
```

**Why it works:** Path objects handle platform differences internally.

### ✅ Safe String Comparisons with `in`

```python
# Substring matching is generally safe
assert str(temp_dir) in str(logger.log_dir)  # ✅ OK - substring matching
```

**Why it works:** Both sides use the same platform separator.

## Prevention Checklist

### Code Review Checklist

When reviewing code that tests paths:

- [ ] Are paths being compared as strings?
- [ ] If yes, is `.as_posix()` used before string comparison?
- [ ] Are hardcoded paths using forward slashes (`/`)?
- [ ] Could this path comparison fail on Windows?
- [ ] Would comparing Path objects directly be better?

### Pre-Commit Hook Enhancement

Our existing pre-commit hooks caught encoding issues but not this. Consider adding:

```yaml
# .pre-commit-config.yaml
- id: check-platform-specific-paths
  name: Check for platform-specific path comparisons
  entry: Check for str(path) comparisons without as_posix()
  language: system
  types: [python]
  # Custom hook to detect: assert str(...Path...) == "..."
```

### Testing Guidelines

**When writing path-related tests:**

1. **Default to Path object comparisons:**
   ```python
   assert actual_path == expected_path  # Both are Path objects
   ```

2. **If string comparison is needed, use `.as_posix()`:**
   ```python
   assert actual_path.as_posix() == "expected/unix/path"
   ```

3. **Never compare `str(path)` directly to hardcoded strings:**
   ```python
   assert str(path) == "some/path"  # ❌ WILL FAIL ON WINDOWS
   ```

4. **Test on multiple platforms or use CI:**
   - Local testing on macOS/Linux won't catch Windows issues
   - Rely on GitHub Actions Windows runners to catch these
   - Consider using `pytest-xdist` with `--dist loadscope` for faster feedback

## Common Pitfalls

### ❌ Pitfall 1: String comparison with platform paths

```python
# BAD: Will fail on Windows
config_path = Path("ADRI/dev/config.yaml")
assert str(config_path) == "ADRI/dev/config.yaml"
```

```python
# GOOD: Cross-platform safe
config_path = Path("ADRI/dev/config.yaml")
assert config_path.as_posix() == "ADRI/dev/config.yaml"
```

### ❌ Pitfall 2: Building paths with string concatenation

```python
# BAD: Hardcodes separators
log_path = base_path + "/logs/audit.log"
```

```python
# GOOD: Use Path operators
log_path = base_path / "logs" / "audit.log"
```

### ❌ Pitfall 3: Splitting paths with hardcoded separators

```python
# BAD: Only works on Unix
parts = path_string.split("/")
```

```python
# GOOD: Use Path.parts
parts = Path(path_string).parts
```

## Detection Strategies

### Automated Detection

Search for potential issues in the codebase:

```bash
# Find str(path) comparisons that might be problematic
grep -r 'assert str(' tests/ --include="*.py" | grep -v "in str(" | cat

# Find hardcoded path separators
grep -r '"\w*/\w*"' tests/ --include="*.py" | cat
```

### Manual Code Review Patterns

Look for:
- `assert str(some_path) == "..."`
- String literals with `/` in path-like contexts
- Path joining with `+` or string formatting
- `.split("/")` or `.split("\\")`

## Mitigation Strategy

### Immediate Actions (Completed)

1. ✅ Fixed `test_default_config_path` to use `.as_posix()`
2. ✅ Verified no other `assert str(` issues in logging tests
3. ✅ Committed and pushed fix to PR

### Long-term Improvements

1. **Add to Contributing Guidelines**
   - Document cross-platform path handling requirements
   - Include examples in contributor documentation

2. **Create Custom Pytest Plugin**
   - Detect platform-specific path assertions
   - Warn developers during local test runs

3. **Enhance CI Pipeline**
   - Ensure all PRs run on Windows, Linux, and macOS
   - Block merges if any platform fails

4. **Add More Test Utilities**
   ```python
   # tests/utils/path_assertions.py
   def assert_paths_equal(actual: Path, expected: str):
       """Cross-platform safe path assertion."""
       assert actual.as_posix() == expected
   ```

## References

- Python pathlib documentation: https://docs.python.org/3/library/pathlib.html
- PEP 428 - The pathlib module: https://peps.python.org/pep-0428/
- Cross-platform file path handling: https://docs.python.org/3/library/os.path.html

## Related Issues

- PR #73: JSONL log reader implementation
- Windows CI test failure in test_default_config_path
- Root cause: Platform-specific path separator comparison

## Summary

**Problem:** String comparison of Path objects fails on Windows due to backslash separators.

**Solution:** Use `.as_posix()` for string comparisons or compare Path objects directly.

**Prevention:** Establish coding standards, enhance pre-commit hooks, and educate contributors about cross-platform path handling.
