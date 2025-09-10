# PyPI-First Version Management System

## Overview

The ADRI Validator now uses a **PyPI-first version management system** that eliminates manual version coordination errors by using PyPI as the single source of truth for version decisions.

## Key Benefits

✅ **Eliminates Version Drift**: No more out-of-sync VERSION.json files
✅ **Automated Version Calculation**: Change type selection instead of manual version numbers
✅ **PyPI Reality**: Always based on current PyPI deployment status
✅ **Error Prevention**: Prevents duplicate versions and synchronization issues
✅ **Audit Trail**: VERSION.json becomes an audit log rather than source of truth

## System Components

### 1. PyPI Manager (`scripts/pypi_manager.py`)
Core module that handles PyPI API integration:
- **Status Checking**: Retrieves current PyPI versions
- **Synchronization**: Aligns VERSION.json with PyPI reality
- **Version Calculation**: Computes next versions based on change types

```bash
# Check PyPI status and sync status
python scripts/pypi_manager.py --status

# Synchronize VERSION.json with PyPI
python scripts/pypi_manager.py --sync

# Get next version for specific change type
python scripts/pypi_manager.py --next-version minor
```

### 2. Enhanced Version Validation (`scripts/validate_version.py`)
Updated validation that integrates PyPI checking:
- **PyPI-First Validation**: Uses live PyPI data as primary source
- **Fallback Mode**: Uses VERSION.json when PyPI unavailable
- **Enhanced Error Messages**: Clear guidance on version conflicts

### 3. Release Preparation (`scripts/prepare_releases.py`)
Transformed for change-type-based workflow:
- **PyPI-Aware**: Automatically syncs and calculates versions
- **Change Types**: `--type patch/minor/major` instead of manual versions
- **Beta Support**: `--beta` flag for pre-releases

```bash
# Prepare minor production release
python scripts/prepare_releases.py --type minor

# Prepare beta minor release
python scripts/prepare_releases.py --type minor --beta

# Check status and sync before preparation
python scripts/prepare_releases.py --status --sync
```

## Workflows

### 1. Prepare Release Workflow (`.github/workflows/prepare-release.yml`)
**Purpose**: Automated release preparation with change type selection

**Triggers**: Manual workflow dispatch with inputs:
- `change_type`: patch/minor/major (required)
- `is_beta`: Create beta pre-release (optional)
- `force_sync`: Force VERSION.json sync (optional)
- `target_branch`: Release branch (optional, default: main)

**Process**:
1. **PyPI Status Check**: Verifies current PyPI versions
2. **Synchronization**: Syncs VERSION.json if needed
3. **Version Calculation**: Computes next version from PyPI + change type
4. **File Updates**: Updates pyproject.toml and version.py
5. **Quick Tests**: Runs fast validation tests
6. **Draft Creation**: Creates GitHub draft release
7. **Summary**: Provides comprehensive next steps

**Usage**:
1. Go to Actions → "Prepare Release (PyPI-First Version Management)"
2. Click "Run workflow"
3. Select change type and options
4. Review generated draft release
5. Publish when ready

### 2. Release Deployment Workflow (`.github/workflows/release-to-pypi.yml`)
**Purpose**: Automated deployment with PyPI-first validation

**Enhanced Features**:
- **PyPI Status Integration**: Checks current PyPI state
- **Automatic Sync**: Syncs VERSION.json before deployment
- **Enhanced Validation**: Uses PyPI data for version validation
- **Comprehensive Testing**: TestPyPI staging before production

## Migration from Manual System

### Old Workflow
```bash
# Manual version selection (error-prone)
vim VERSION.json  # Manually set version
python scripts/prepare_releases.py Release.Minor.v3.1.0
git tag Release.Minor.v3.1.0
```

### New Workflow
```bash
# Automated PyPI-first approach
python scripts/prepare_releases.py --type minor
# Automatically: checks PyPI, syncs, calculates 3.1.0, creates draft
```

## Version Calculation Logic

The system calculates next versions based on current PyPI state:

### Current PyPI: 3.0.0

| Change Type | Next Version | Tag Format |
|-------------|--------------|------------|
| `patch`     | 3.0.1        | `Release.Patch.v3.0.1` |
| `minor`     | 3.1.0        | `Release.Minor.v3.1.0` |
| `major`     | 4.0.0        | `Release.Major.v4.0.0` |
| `minor --beta` | 3.1.0-beta.1 | `Pre-release.Minor.v3.1.0-beta.1` |

### Beta Version Handling
- **First Beta**: `3.1.0-beta.1`
- **Subsequent Betas**: `3.1.0-beta.2`, `3.1.0-beta.3`
- **Production After Beta**: `3.1.0` (removes beta suffix)

## Common Use Cases

### 1. Regular Minor Release
```bash
# GitHub Actions approach (recommended)
1. Actions → "Prepare Release" → "minor" → Run
2. Review draft release
3. Publish release (triggers deployment)

# Command line approach
python scripts/prepare_releases.py --type minor
```

### 2. Hotfix Patch Release
```bash
# For urgent bug fixes
python scripts/prepare_releases.py --type patch
```

### 3. Beta Release for Testing
```bash
# Create beta for user testing
python scripts/prepare_releases.py --type minor --beta
```

### 4. Major Breaking Changes
```bash
# For API breaking changes
python scripts/prepare_releases.py --type major
```

### 5. Manual Sync and Status Check
```bash
# Check current status
python scripts/pypi_manager.py --status

# Force synchronization
python scripts/pypi_manager.py --sync
```

## Error Handling

### Version Conflicts
**Problem**: Attempting to create version that already exists
**Solution**: System automatically detects and suggests next available version

### PyPI Sync Issues
**Problem**: VERSION.json out of sync with PyPI reality
**Solution**: Run `python scripts/pypi_manager.py --sync`

### Network Issues
**Problem**: Cannot reach PyPI API
**Solution**: System falls back to VERSION.json with warnings

## Validation Rules

1. **PyPI Priority**: Live PyPI data takes precedence over local tracking
2. **Semantic Versioning**: Enforces proper semantic version increments
3. **No Duplicates**: Prevents creating versions that already exist
4. **Beta Sequences**: Ensures proper beta version sequences

## Best Practices

### 1. Always Use Change Types
```bash
# ✅ Good - descriptive and automated
python scripts/prepare_releases.py --type minor

# ❌ Avoid - manual and error-prone
python scripts/prepare_releases.py Release.Minor.v3.1.0
```

### 2. Regular Synchronization
```bash
# Run periodically to stay aligned
python scripts/pypi_manager.py --sync
```

### 3. Beta Testing for Major Changes
```bash
# Test significant changes first
python scripts/prepare_releases.py --type minor --beta
# After validation
python scripts/prepare_releases.py --type minor
```

### 4. Use GitHub Actions for Production
- Manual scripts for development/testing
- GitHub Actions for production releases
- Ensures consistent environment and logging

## Troubleshooting

### Issue: "Version already exists"
```bash
# Check what's currently on PyPI
python scripts/pypi_manager.py --status

# Sync if VERSION.json is wrong
python scripts/pypi_manager.py --sync

# Use appropriate change type
python scripts/prepare_releases.py --type patch  # if minor exists
```

### Issue: "PyPI sync failed"
```bash
# Check network connectivity
curl https://pypi.org/pypi/adri/json

# Try manual sync with verbose output
python scripts/pypi_manager.py --sync --verbose
```

### Issue: "Version mismatch in files"
```bash
# Check all version locations
grep -r "version.*=" pyproject.toml adri/version.py VERSION.json

# Use prepare script to fix consistency
python scripts/prepare_releases.py --type minor
```

## Integration Points

### CI/CD Integration
The system integrates with:
- **GitHub Actions**: Automated workflows
- **PyPI/TestPyPI**: Version checking and deployment
- **Git Tags**: Automated tag creation
- **Release Notes**: Auto-generated draft releases

### Development Tools
- **Pre-commit Hooks**: Version consistency checks
- **Test Suites**: Version validation in tests
- **Documentation**: Auto-updated version references

## Future Enhancements

- **Slack Integration**: Real-time release notifications
- **Release Notes Automation**: CHANGELOG.md generation
- **Multiple Package Support**: Multi-package version coordination
- **Release Scheduling**: Time-based release automation

## Security Considerations

- **Token Management**: PyPI tokens stored as GitHub secrets
- **Validation**: Multiple verification steps before deployment
- **Rollback**: Automated rollback on deployment failures
- **Audit Trail**: Complete logging of all version decisions

---

For support or questions about the PyPI-first version management system, please create an issue in the repository or contact the development team.
