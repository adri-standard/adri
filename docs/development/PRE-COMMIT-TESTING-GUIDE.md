# Pre-commit Testing Guide

## Two-Layer Test Validation Strategy

ADRI uses a two-layer testing strategy to catch failures early while keeping development workflow fast:

### Layer 1: Pre-commit (Fast, ~8.5s)

**Purpose**: Catch syntax errors and critical functionality issues immediately

**What runs**:
- ✅ Linters (Black, flake8, isort, etc.)
- ✅ 75 critical smoke tests:
  - Config tests (23) - Configuration system
  - Decorator tests (21) - Core protection functionality
  - Guard modes (26) - Protection engine
  - CLI imports (9) - Integration basics

**When**: Runs automatically before each commit

**Time**: ~8.5 seconds

**What it catches**:
- Syntax errors (Python compilation)
- Config file issues
- Basic decorator/guard functionality
- Import breakages

### Layer 2: Pre-push (Comprehensive, ~50s)

**Purpose**: Ensure ALL tests pass before code reaches GitHub

**What runs**:
- ✅ ALL 1185 tests
- ✅ Full coverage analysis
- ✅ Performance benchmarks

**When**: Runs automatically before each push

**Time**: ~50 seconds

**What it catches**:
- Integration issues
- Edge cases
- Component interactions
- Performance regressions
- ALL test failures

## Workflow

```bash
# 1. Make changes
vim src/adri/some_file.py

# 2. Commit (runs pre-commit: linters + 75 smoke tests)
git commit -m "feat: my changes"
# ✅ Fast feedback (~8.5s)

# 3. Push (runs pre-push: ALL 1185 tests)
git push origin my-branch
# ✅ Comprehensive validation (~50s)
# ❌ Push BLOCKED if any test fails
```

## Benefits

✅ **No failures reach GitHub**: Pre-push catches everything locally
✅ **Fast commits**: Pre-commit stays under 10 seconds
✅ **Clear feedback**: Failures caught at appropriate time
✅ **Prevents CI waste**: No iteration delays from GitHub CI failures
✅ **Maintains quality**: 100% test pass rate before push

## Bypassing (Not Recommended)

If you absolutely must bypass the checks:

```bash
# Skip pre-commit hooks
git commit --no-verify

# Skip pre-push hook
git push --no-verify
```

⚠️ **Warning**: Only use --no-verify for emergency hotfixes. All code should pass tests before merging.

## Expected Failures (xfail)

Some tests are marked as `@pytest.mark.xfail` due to known issues under investigation:

- 5 tests in `test_tutorial_cli_decorator_parity.py`: Decorator audit logging
- 2 tests in `test_issue_35_cli_decorator_parity.py`: CLI command integration

These are documented issues that don't block the test suite but need separate investigation.

## Troubleshooting

### Pre-commit fails
```bash
# See what failed
git commit -m "message"

# Fix the issue, then commit again
```

### Pre-push fails
```bash
# See full test details
pytest tests/ -v --tb=short

# Fix failures, commit, then push again
```

### Hook not running
```bash
# Ensure hooks are executable
chmod +x .git/hooks/pre-push

# Reinstall pre-commit hooks
pre-commit install
```

## For Maintainers

### Updating Smoke Tests

Edit `.pre-commit-config.yaml`:
```yaml
- id: pytest-smoke-test
  args:
    - tests/test_config.py          # Add or remove test files
    - tests/test_decorator.py       # to adjust coverage
    - -x                             # Keep fail-fast flag
    - -q                             # Keep quiet mode
```

### Updating Pre-push Hook

Edit `.git/hooks/pre-push`:
```bash
# Modify test command or output
python -m pytest tests/ -q --tb=short --maxfail=5
```

## Performance Targets

- **Pre-commit**: < 10 seconds (currently ~8.5s) ✅
- **Pre-push**: < 60 seconds (currently ~50s) ✅
- **Coverage**: > 10% minimum (currently 57.7%) ✅

## See Also

- [Local CI Guide](local-ci-guide.md) - Running full CI checks locally
- [Testing Framework](../testing-framework.md) - Test organization
- [CI Validation Guide](ci-validation-guide.md) - GitHub Actions CI
