# ADRI v5.0.0 Pre-Split Rollback Instructions

## Overview

This directory contains backup files and restoration instructions for rolling back the ADRI v5.0.0 open-source/enterprise split if needed.

**Created:** Before splitting ADRI v4.4.0 into open-source and enterprise packages
**Purpose:** Safety net to restore repository to pre-split state
**Repository:** https://github.com/adri-standard/adri

## What's Included

This backup contains:
- **Git Tag:** `v5.0.0-pre-split` - Complete repository state before split
- **File Backups:** Critical files that will be modified during split
- **Metadata:** Information about backup creation and repository state
- **Restoration Scripts:** Automated scripts to restore from backup

## When to Use This Rollback

Use this rollback if:
- ✓ The split process fails or encounters errors
- ✓ Tests fail after splitting and issues cannot be resolved
- ✓ Critical functionality is broken after split
- ✓ Need to abort the split and return to unified codebase
- ✓ Discovered major issues during integration testing
- ✓ Need to re-plan the split approach

Do NOT use if:
- ✗ Minor bugs that can be fixed with patches
- ✗ Documentation issues only
- ✗ Split is complete and packages are already released
- ✗ Just exploring backup contents

## Restoration Methods

### Method 1: Git Tag Restoration (RECOMMENDED)

**What it does:** Resets entire repository to pre-split commit state

**Advantages:**
- Complete and clean restoration
- Guarantees exact pre-split state
- Fast and reliable
- Preserves full Git history

**Requirements:**
- Git tag `v5.0.0-pre-split` exists
- No uncommitted changes (or willing to lose them)

**Steps:**

```bash
# 1. Navigate to repository root
cd /path/to/adri

# 2. Check current state
git status
git log -1 --oneline

# 3. Run restoration script
bash scripts/restore-from-rollback.sh

# 4. Select option 1 (Restore from Git tag)

# 5. Confirm restoration when prompted

# 6. Verify restoration
git log -1 --oneline
git status
```

**Manual restoration (if script fails):**

```bash
# Reset to tag
git reset --hard v5.0.0-pre-split

# Verify
git log -1 --oneline
```

### Method 2: File Backup Restoration

**What it does:** Restores only backed up files from this directory

**Advantages:**
- Preserves other changes not related to split
- More selective restoration
- Can be used if Git tag is lost

**Requirements:**
- Backup directory `backup/pre-split/` exists
- Files to restore are present in backup

**Steps:**

```bash
# 1. Navigate to repository root
cd /path/to/adri

# 2. Run restoration script
bash scripts/restore-from-rollback.sh

# 3. Select option 2 (Restore from file backup)

# 4. Confirm restoration when prompted

# 5. Review changes
git status
git diff

# 6. Commit restored files
git add .
git commit -m "chore: Restore files from pre-split backup"
```

**Manual restoration (if script fails):**

```bash
# Copy files from backup
cp backup/pre-split/src/adri/logging/reasoning.py src/adri/logging/
cp backup/pre-split/src/adri/logging/workflow.py src/adri/logging/
# ... repeat for all backed up files

# Review and commit
git status
git add .
git commit -m "chore: Restore files from pre-split backup"
```

## Backup Contents

### Git Tag Information

- **Tag Name:** `v5.0.0-pre-split`
- **Description:** Pre-split rollback point for ADRI v5.0.0
- **Commit:** See `rollback-metadata.json` for commit SHA
- **Branch:** Usually `main` or active development branch

### Backed Up Files

Critical files that will be modified during split:

**Source Code:**
- `src/adri/logging/reasoning.py` - ReasoningLogger (removed in open-source)
- `src/adri/logging/workflow.py` - WorkflowLogger (removed in open-source)
- `src/adri/logging/enterprise.py` - Full EnterpriseLogger (simplified in open-source)
- `src/adri/guard/reasoning_mode.py` - ReasoningProtectionMode (removed in open-source)
- `src/adri/__init__.py` - Package exports (modified)
- `src/adri/logging/__init__.py` - Logging exports (modified)
- `src/adri/validator/engine.py` - ValidationEngine imports (modified)
- `src/adri/logging/local.py` - LocalLogger imports (modified)

**Configuration:**
- `pyproject.toml` - Package metadata and version (modified)

**Documentation:**
- `README.md` - Main documentation (modified)
- `ARCHITECTURE.md` - Architecture documentation (modified)
- `CHANGELOG.md` - Change history (modified)

### Metadata File

The `rollback-metadata.json` file contains:
- Backup creation timestamp
- Git commit SHA
- Branch name
- Python version
- Git remote URL
- Number of files backed up
- User and hostname

## Verification Steps

After restoration, verify the rollback was successful:

### 1. Check Git State

```bash
# Verify commit
git log -1 --oneline

# Should show pre-split commit
# Tag annotation should reference pre-split state
git show v5.0.0-pre-split

# Check for uncommitted changes
git status
```

### 2. Verify File Contents

```bash
# Check enterprise features are present
ls -la src/adri/logging/reasoning.py  # Should exist
ls -la src/adri/logging/workflow.py   # Should exist
ls -la src/adri/guard/reasoning_mode.py  # Should exist

# Check version
grep version pyproject.toml  # Should show 4.4.0 or original version
```

### 3. Run Tests

```bash
# Install dependencies
pip install -e ".[dev]"

# Run test suite
pytest

# Expected: All tests passing
# If using v4.4.0: 1135 tests passing, 8 skipped
```

### 4. Verify Functionality

```bash
# Test CLI
adri --version
adri list-standards

# Test decorator
python -c "from adri import adri_protected; print('Import successful')"

# Test logging
python -c "from adri.logging import ReasoningLogger; print('ReasoningLogger available')"
```

## Troubleshooting

### Issue: Git tag not found

**Symptom:** `ERROR: Tag v5.0.0-pre-split not found`

**Solution:**
1. Check if tag exists: `git tag -l | grep pre-split`
2. Check remote: `git ls-remote --tags origin | grep pre-split`
3. If on remote but not local: `git fetch --tags`
4. If not on remote: Use Method 2 (file backup restoration)

### Issue: Backup directory not found

**Symptom:** `ERROR: Backup directory not found: backup/pre-split`

**Solution:**
1. Check if directory exists: `ls -la backup/`
2. If missing: Cannot use Method 2, must use Method 1 (Git tag)
3. If files deleted: Check if tag exists and use Git tag restoration

### Issue: Uncommitted changes blocking restoration

**Symptom:** `ERROR: You have uncommitted changes`

**Solution:**
```bash
# Option A: Stash changes
git stash
# ... run restoration ...
git stash pop  # Restore changes after

# Option B: Commit changes
git add .
git commit -m "WIP: Save before rollback"
# ... run restoration ...

# Option C: Discard changes
git reset --hard HEAD
```

### Issue: Restoration script fails

**Symptom:** Script errors or doesn't complete

**Solution:**
Use manual restoration steps provided in each method section above.

### Issue: Tests fail after restoration

**Symptom:** Pytest shows failures after rollback

**Solution:**
1. Clean Python cache: `find . -type d -name __pycache__ -exec rm -rf {} +`
2. Reinstall package: `pip uninstall adri && pip install -e ".[dev]"`
3. Clear pytest cache: `rm -rf .pytest_cache`
4. Run tests again: `pytest`
5. If still failing, may indicate incomplete restoration

## After Successful Restoration

Once you've verified the restoration was successful:

1. **Assess the situation:**
   - Document what went wrong during the split
   - Identify issues that need to be addressed
   - Update implementation plan if needed

2. **Clean up (optional):**
   - Keep the backup and tag until you're confident
   - Don't delete rollback artifacts until v5.0.0 is stable

3. **Plan next steps:**
   - Fix issues identified during failed split
   - Update test suite if needed
   - Re-run rollback point creation before next attempt

4. **Communicate:**
   - Notify team of rollback
   - Document lessons learned
   - Update project timeline if needed

## Important Notes

⚠️ **WARNING:**
- Restoration is DESTRUCTIVE - changes after the backup point will be lost
- Always verify you have uncommitted work saved before restoring
- Test thoroughly after restoration before continuing work

✓ **BEST PRACTICES:**
- Review changes carefully before restoring
- Keep the v5.0.0-pre-split tag until split is verified stable
- Document any issues encountered during rollback
- Don't delete backup files until v5.0.0 is released and stable

## Support

If you encounter issues not covered in this guide:

1. Check script help: `bash scripts/restore-from-rollback.sh` and select option 3
2. Review Git logs: `git log --oneline -20`
3. Check backup integrity: `ls -la backup/pre-split/`
4. Review implementation plan: `implementation_plan.md`

## Version Information

- **ADRI Pre-Split Version:** 4.4.0
- **Target Version:** 5.0.0
- **Split Date:** See `rollback-metadata.json`
- **Backup Script Version:** 1.0.0

---

**Last Updated:** October 15, 2025
**Maintained By:** ADRI Development Team
**Repository:** https://github.com/adri-standard/adri
