# ADRI Validator Release Process

This document describes the streamlined release process for ADRI Validator. The process is designed to be simple, reliable, and easy to rollback if needed.

## Overview

The release process follows these principles:
- **Simple**: Minimal steps, clear instructions
- **Reliable**: Automated testing and validation
- **Transparent**: All changes are visible in git history
- **Rollback-friendly**: Easy to undo if something goes wrong

## Release Workflow

```
Development (main) → Prepare Release → GitHub Release → Automated Pipeline → PyPI
```

## Step-by-Step Process

### 1. Prepare the Release

Use the automated preparation script:

```bash
# Navigate to project root
cd adri-validator

# Prepare release (replace 0.1.1 with your target version)
python scripts/prepare_release.py 0.1.1

# Or with custom changelog entry
python scripts/prepare_release.py 0.1.1 --changelog "Added new validation features"
```

This script will:
- ✅ Update version in `pyproject.toml`
- ✅ Update `CHANGELOG.md` with new version
- ✅ Create a commit with the changes
- ✅ Provide next steps

### 2. Push Changes

```bash
git push origin main
```

### 3. Create GitHub Release

1. Go to [GitHub Releases](https://github.com/ThinkEvolveSolve/adri-validator/releases/new)
2. Fill in the details:
   - **Tag**: `v0.1.1` (must match the version you prepared)
   - **Title**: `Release v0.1.1`
   - **Description**: Copy from CHANGELOG.md or write custom notes
3. Click **"Publish release"**

### 4. Monitor the Pipeline

The GitHub Release will automatically trigger the release workflow:

1. **Test**: Run full test suite
2. **Build**: Build the package and verify version matches tag
3. **TestPyPI**: Publish to TestPyPI and run smoke tests
4. **PyPI**: Publish to production PyPI
5. **Validation**: Run final smoke tests
6. **Complete**: Update release notes with PyPI links

Monitor progress at: https://github.com/ThinkEvolveSolve/adri-validator/actions

## Pipeline Details

### Automated Steps

1. **Version Verification**: Ensures tag version matches `pyproject.toml`
2. **Full Testing**: Runs complete test suite with coverage requirements
3. **Package Building**: Creates wheel and source distributions
4. **TestPyPI Publishing**: Publishes to test environment first
5. **TestPyPI Validation**: Installs and tests from TestPyPI
6. **Production Publishing**: Only proceeds if TestPyPI tests pass
7. **Production Validation**: Final verification from production PyPI
8. **Release Updates**: Adds installation instructions and links

### Safety Features

- **Version Mismatch Detection**: Fails if tag doesn't match pyproject.toml
- **Test Gate**: Won't publish if tests fail
- **TestPyPI Gate**: Won't publish to production if TestPyPI tests fail
- **Rollback Instructions**: Provides clear rollback steps on failure

## Rollback Procedures

If something goes wrong during or after release:

### 1. If Pipeline Fails

The pipeline will provide rollback instructions in the logs:

```bash
# Delete the GitHub release
gh release delete v0.1.1

# Delete the git tag
git tag -d v0.1.1
git push origin :refs/tags/v0.1.1

# Revert the version commit (if needed)
git revert HEAD
git push origin main
```

### 2. If Package is Published but Broken

```bash
# Delete GitHub release and tag (as above)
gh release delete v0.1.1
git tag -d v0.1.1
git push origin :refs/tags/v0.1.1

# Contact PyPI support to remove the package
# (PyPI doesn't allow automatic deletion of published packages)
```

### 3. Emergency Hotfix

For critical issues in a published release:

```bash
# Create hotfix version
python scripts/prepare_release.py 0.1.2 --changelog "Critical bug fix"
git push origin main

# Create emergency release
# Follow normal release process with new version
```

## Version Management

### Semantic Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backwards compatible
- **PATCH** (0.0.1): Bug fixes, backwards compatible

### Version Examples

```bash
# Patch release (bug fixes)
python scripts/prepare_release.py 0.1.1

# Minor release (new features)
python scripts/prepare_release.py 0.2.0

# Major release (breaking changes)
python scripts/prepare_release.py 1.0.0

# Pre-release versions
python scripts/prepare_release.py 0.2.0-rc1
python scripts/prepare_release.py 0.2.0-beta1
```

## Troubleshooting

### Common Issues

#### "Version already exists"
- Check if tag already exists: `git tag -l`
- Delete existing tag if needed: `git tag -d v0.1.1`

#### "Git working directory not clean"
- Commit or stash changes: `git status`
- Use `--skip-git-check` flag if intentional

#### "TestPyPI timeout"
- TestPyPI can be slow to update
- Pipeline waits up to 4.5 minutes
- Check TestPyPI manually if needed

#### "Production smoke tests fail"
- Usually indicates a real issue with the package
- Follow rollback procedures
- Investigate and fix before retrying

### Getting Help

1. **Check the logs**: GitHub Actions provides detailed logs
2. **Check the issues**: Look for similar problems in GitHub issues
3. **Manual verification**: Test the package locally before releasing

## Best Practices

### Before Releasing

- [ ] All tests pass locally
- [ ] Documentation is updated
- [ ] CHANGELOG.md reflects all changes
- [ ] Version number follows semantic versioning
- [ ] No uncommitted changes

### During Release

- [ ] Monitor the GitHub Actions workflow
- [ ] Verify TestPyPI installation works
- [ ] Check production PyPI after completion

### After Release

- [ ] Test installation from PyPI
- [ ] Update any dependent projects
- [ ] Announce the release if significant

## Scripts Reference

### prepare_release.py

```bash
# Basic usage
python scripts/prepare_release.py 0.1.1

# With custom changelog
python scripts/prepare_release.py 0.1.1 --changelog "Added new features"

# Skip git status check (use with caution)
python scripts/prepare_release.py 0.1.1 --skip-git-check
```

### Manual Commands

```bash
# Check current version
grep 'version = ' pyproject.toml

# List existing tags
git tag -l

# Check release status
gh release list

# View workflow runs
gh run list --workflow="release.yml"
```

## Security Notes

- PyPI tokens are stored as GitHub secrets
- TestPyPI and production use separate tokens
- Releases are only triggered by GitHub Releases (not pushes)
- All steps are logged and auditable

---

For questions or issues with the release process, please create an issue in the repository.
