# GitHub Actions CI Configuration

## Overview

This repository uses an intelligent CI system that automatically detects documentation-only changes and skips expensive test runs when appropriate.

## How It Works

### 1. Change Detection (`check-changes` job)

The CI first analyzes what files were changed in the PR or push:

**Documentation files** (triggers lightweight validation only):
- `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `QUICKSTART.md`
- All files in `docs/`
- `examples/README.md`
- GitHub templates (`.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`)
- `implementation_plan.md`
- `LICENSE`, `CODE_OF_CONDUCT.md`

**Code files** (triggers full test suite):
- Anything in `adri/` (Python source code)
- `pyproject.toml`, `setup.py`
- `requirements.txt`
- Test files in `tests/`

### 2. Documentation Validation (`validate-docs` job)

**Runs only for docs-only changes**

Fast, lightweight checks:
- ✅ Validates all required documentation files exist
- ✅ Checks Markdown syntax
- ✅ Validates internal links
- ✅ Checks for broken references

**Duration**: ~30 seconds

### 3. Full Test Suite (`test` job)

**Runs only when code is changed**

Comprehensive testing:
- ✅ Tests on Ubuntu, macOS, and Windows
- ✅ Tests Python 3.8, 3.9, 3.10, 3.11, 3.12
- ✅ Runs full test suite with coverage
- ✅ Checks code style (flake8)
- ✅ Validates formatting (black)
- ✅ Uploads coverage to Codecov

**Duration**: ~10-15 minutes per matrix combination

## Benefits

### For Documentation PRs
- ⚡ **Fast feedback** - Results in ~30 seconds instead of 10-15 minutes
- 💰 **Saves CI minutes** - No unnecessary test matrix runs
- 🎯 **Focused validation** - Only checks what matters for docs

### For Code PRs
- 🔒 **No shortcuts** - Full test suite always runs
- 🌍 **Cross-platform** - Tests on all major operating systems
- 🐍 **Multi-version** - Tests on all supported Python versions

## Usage

### Creating a Documentation-Only PR

1. Make your documentation changes
2. Commit and push
3. CI will automatically detect it's docs-only
4. PR will show "Documentation validation passed" status

### Creating a Code PR

1. Make your code changes
2. Commit and push
3. CI will run full test suite
4. PR will show test results for all platforms/versions

### Mixed Changes (Docs + Code)

If your PR includes both documentation and code changes, the **full test suite will run**. This is intentional to ensure code quality.

## Configuration Files

### `.github/workflows/ci.yml`
Main CI workflow definition with intelligent change detection.

### `.github/markdown-link-check-config.json`
Configuration for the Markdown link checker:
- Ignores repository links (to avoid circular checks)
- Sets timeouts and retry logic
- Configures HTTP headers for external link checks

## Customization

### Adding New Documentation Patterns

Edit the `check-changes` job in `ci.yml`:

```yaml
if [[ "$file" =~ ^(README\.md|NEW_PATTERN\.md)$ ]] || \
```

### Adjusting Test Matrix

Edit the `test` job matrix:

```yaml
matrix:
  os: [ubuntu-latest, macos-latest, windows-latest]
  python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
```

### Modifying Doc Validation

Edit the `validate-docs` job steps to add/remove checks.

## Troubleshooting

### "Both jobs skipped" Error

This shouldn't happen. If it does, the change detection logic may need adjustment.

### Docs Validation Failing

Check the validation logs for:
- Missing required files
- Broken internal links
- Markdown syntax errors

### Test Suite Failing

This means code changes have issues. Check:
- Test failures in specific Python versions
- Code style violations (flake8)
- Formatting issues (black)

## Branch Protection

Recommended branch protection rules for `main`:

1. ✅ Require status checks to pass before merging
2. ✅ Require `ci-status` check
3. ✅ Require branches to be up to date
4. ❌ Don't require all matrix jobs (ci-status is sufficient)

This way, docs-only PRs can merge after lightweight validation, while code PRs must pass full tests.

## Examples

### Documentation-Only PR
```
✅ check-changes (docs-only: true)
✅ validate-docs (30s)
⏭️ test (skipped)
✅ ci-status (passed)
```

### Code PR
```
✅ check-changes (docs-only: false)
⏭️ validate-docs (skipped)
✅ test (matrix: 15 jobs, 10-15 min each)
✅ ci-status (passed)
```

### Mixed PR
```
✅ check-changes (docs-only: false)
⏭️ validate-docs (skipped)
✅ test (full suite runs)
✅ ci-status (passed)
```

## Future Enhancements

Possible improvements:
- Add spell checking for documentation
- Validate code examples in documentation
- Check documentation coverage
- Add performance benchmarking for code changes
- Deploy documentation to GitHub Pages on merge

---

**Questions?** Open an issue or check the [Contributing Guide](../../CONTRIBUTING.md).
