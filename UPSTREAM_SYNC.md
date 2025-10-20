# Upstream Synchronization Guide

This document describes how to synchronize core functionality from the community ADRI repository (adri-standard/adri) into verodat-adri while protecting enterprise-specific features.

## Overview

**verodat-adri** is an enterprise fork of the community ADRI project. We maintain:
- **Core functionality**: Synced periodically from upstream (adri-standard/adri)
- **Enterprise features**: Protected modules unique to Verodat integration

## Repository Configuration

### Remotes

```bash
# Origin: Verodat enterprise repository
origin    https://github.com/Verodat/verodat-adri.git

# Upstream: Community ADRI repository
upstream  https://github.com/adri-standard/adri.git
```

### Verify Configuration

```bash
git remote -v
git fetch upstream
git log HEAD..upstream/main --oneline
```

## Modules to Sync from Upstream

These core modules should be periodically synchronized from adri-standard/adri:

### Core Decorator System
- `src/adri/decorator.py` - Core @adri_protected decorator

### Validation Engine
- `src/adri/validator/` - Complete validation engine
  - `src/adri/validator/engine.py`
  - `src/adri/validator/rules.py`
  - `src/adri/validator/pipeline.py`
  - `src/adri/validator/loaders.py`
  - `src/adri/validator/dimensions/` - All dimension validators

### Guard Modes
- `src/adri/guard/` - Guard mode implementations
  - `src/adri/guard/modes.py`
  - `src/adri/guard/reasoning_mode.py`

### Analysis Framework
- `src/adri/analysis/` - Data profiling and analysis

### Configuration System
- `src/adri/config/` - Configuration loading and validation
  - `src/adri/config/loader.py`

### Standards Framework
- `src/adri/standards/` - YAML standards parsing
  - `src/adri/standards/parser.py`
  - `src/adri/standards/validator.py`
  - `src/adri/standards/schema.py`
  - `src/adri/standards/reasoning_validator.py`

### Utilities
- `src/adri/utils/` - Shared utility functions
  - `src/adri/utils/path_utils.py`
  - `src/adri/utils/serialization.py`
  - `src/adri/utils/validation_helpers.py`

## Modules Protected as Enterprise-Only

These modules contain Verodat-specific features and should **NOT** be synced from upstream:

### Enterprise Logging
- `src/adri/logging/enterprise.py` - Verodat API integration
- `src/adri/logging/unified.py` - Dual-write coordinator (enterprise extension)
- `src/adri/logging/fast_path.py` - Fast path logging (enterprise extension)

### Event System (Enterprise Extension)
- `src/adri/events/` - Event-driven architecture
  - `src/adri/events/event_bus.py`
  - `src/adri/events/types.py`

### Async Callbacks (Enterprise Extension)
- `src/adri/callbacks/` - Async callback infrastructure
  - `src/adri/callbacks/async_handler.py`
  - `src/adri/callbacks/types.py`
  - `src/adri/callbacks/workflow_adapters.py`

### Shared Logging Components
- `src/adri/logging/local.py` - Shared but may have enterprise modifications
- `src/adri/logging/workflow.py` - Workflow logging (check for enterprise extensions)
- `src/adri/logging/reasoning.py` - Reasoning logger (check for enterprise extensions)

## Synchronization Workflow

### Step 1: Check for Upstream Updates

```bash
# Fetch latest from upstream
git fetch upstream

# View commits since our last sync
git log HEAD..upstream/main --oneline

# View file-level changes
git log HEAD..upstream/main --name-only

# Check specific module changes
git log HEAD..upstream/main -- src/adri/decorator.py
git log HEAD..upstream/main -- src/adri/validator/
git log HEAD..upstream/main -- src/adri/guard/
```

### Step 2: Create Sync Branch

```bash
# Create feature branch for sync
git checkout -b sync/upstream-YYYY-MM-DD

# Example
git checkout -b sync/upstream-2025-04-01
```

### Step 3: Selective Sync Strategy

**Option A: Cherry-Pick Specific Commits (Recommended)**

```bash
# Cherry-pick specific commits that affect core modules
git cherry-pick <commit-hash>

# Cherry-pick a range
git cherry-pick <start-commit>..<end-commit>

# Cherry-pick with conflict resolution
git cherry-pick <commit-hash>
# Resolve conflicts
git add <resolved-files>
git cherry-pick --continue
```

**Option B: Merge with Path Filtering**

```bash
# Merge only specific paths
git merge upstream/main --no-commit --no-ff

# Reset enterprise-only modules
git reset HEAD src/adri/logging/enterprise.py
git reset HEAD src/adri/logging/unified.py
git reset HEAD src/adri/logging/fast_path.py
git reset HEAD src/adri/events/
git reset HEAD src/adri/callbacks/

# Checkout our versions of protected files
git checkout HEAD -- src/adri/logging/enterprise.py
git checkout HEAD -- src/adri/logging/unified.py
git checkout HEAD -- src/adri/logging/fast_path.py
git checkout HEAD -- src/adri/events/
git checkout HEAD -- src/adri/callbacks/

# Commit the merge
git commit -m "sync: merge upstream changes (excluding enterprise modules)"
```

**Option C: Manual File Sync (Most Control)**

```bash
# Checkout specific files from upstream
git checkout upstream/main -- src/adri/decorator.py
git checkout upstream/main -- src/adri/validator/engine.py
git checkout upstream/main -- src/adri/guard/modes.py

# Review changes
git diff --cached

# Commit
git commit -m "sync: update core modules from upstream"
```

### Step 4: Resolve Conflicts

When conflicts occur during sync:

1. **Identify conflict type**:
   - Import conflicts: Enterprise modules may import things not in community edition
   - API conflicts: Enterprise features may extend community APIs
   - Integration conflicts: Event system hooks may not exist upstream

2. **Resolution strategy**:
   ```bash
   # View conflict
   git status

   # Edit conflicting files
   # Keep enterprise extensions marked with comments:
   # # ENTERPRISE EXTENSION: Description
   # <enterprise code>
   # # END ENTERPRISE EXTENSION

   # Mark resolved
   git add <resolved-file>
   ```

3. **Common conflict patterns**:
   - **Import additions**: Keep enterprise imports, merge upstream imports
   - **Function parameters**: Enterprise may add optional parameters
   - **Event hooks**: Enterprise adds event publishing, keep both
   - **Logging calls**: Enterprise may use UnifiedLogger vs LocalLogger

### Step 5: Test After Sync

```bash
# Install package locally
pip install -e .

# Run full test suite
pytest tests/ -v

# Run enterprise-specific tests
pytest tests/logging/test_enterprise.py -v
pytest tests/events/ -v
pytest tests/callbacks/ -v
pytest tests/integration/test_event_driven_logging.py -v

# Verify import still works
python -c "import adri; print(adri.__version__)"

# Test decorator functionality
pytest tests/test_decorator.py -v

# Test validation engine
pytest tests/test_validator_engine.py -v
```

### Step 6: Update Documentation

After successful sync:

```bash
# Update CHANGELOG.md
# Add entry under "Upstream Sync" section:
# - Synced decorator.py from upstream v5.0.1
# - Synced validation engine from upstream v5.0.1
# - Applied enterprise integration patches

# Update this file with sync date
echo "Last sync: $(date +%Y-%m-%d) from upstream commit $(git rev-parse upstream/main)" >> UPSTREAM_SYNC.md
```

### Step 7: Create Pull Request

```bash
# Push sync branch
git push origin sync/upstream-YYYY-MM-DD

# Create PR
gh pr create --title "sync: Upstream synchronization from community ADRI vX.Y.Z" \
  --body "## Upstream Sync

- Source: adri-standard/adri @ $(git rev-parse upstream/main)
- Version: vX.Y.Z
- Modules synced: decorator, validator, guard, analysis, config
- Enterprise modules protected: logging/enterprise, events, callbacks
- Tests: All passing ✓
- Conflicts resolved: <describe any conflicts>

## Changes
<paste git log output>

## Testing
- [x] Full test suite passes
- [x] Enterprise tests pass
- [x] Manual import verification
- [x] Decorator functionality verified"
```

### Step 8: Merge and Tag

```bash
# After PR approval, merge to main
gh pr merge --squash

# Pull latest
git checkout main
git pull origin main

# Tag with sync version if needed
git tag -a sync/upstream-vX.Y.Z -m "Sync from upstream community ADRI vX.Y.Z"
git push origin --tags
```

## Conflict Resolution Guidelines

### Imports
```python
# KEEP: Enterprise imports
from adri.events import EventBus
from adri.callbacks import AsyncCallbackManager
from adri.logging.unified import UnifiedLogger

# MERGE: Add new upstream imports
from adri.standards import StandardValidator  # New in upstream
```

### Function Signatures

```python
# Upstream version
def assess_quality(data, standard_path):
    pass

# Enterprise version (with backward compatibility)
def assess_quality(data, standard_path, fast_path_logger=None, event_bus=None):
    # Enterprise extensions
    if event_bus:
        event_bus.publish(...)

    # Core logic (synced from upstream)
    result = _core_assessment(data, standard_path)

    return result
```

### Event Hooks

```python
# Add enterprise event hooks around upstream code
def _perform_validation(self, data):
    # ENTERPRISE EXTENSION: Pre-validation event
    if self.event_bus:
        self.event_bus.publish(AssessmentEvent.STARTED, ...)
    # END ENTERPRISE EXTENSION

    # UPSTREAM CORE LOGIC
    result = self._validate_data(data)
    # END UPSTREAM CORE LOGIC

    # ENTERPRISE EXTENSION: Post-validation event
    if self.event_bus:
        self.event_bus.publish(AssessmentEvent.COMPLETED, ...)
    # END ENTERPRISE EXTENSION

    return result
```

## Testing Strategy

### Pre-Sync Tests
```bash
# Capture baseline
pytest tests/ -v > pre-sync-tests.log

# Note version
git describe --tags > pre-sync-version.txt
```

### Post-Sync Tests
```bash
# Full test suite
pytest tests/ -v

# Compare coverage
pytest tests/ --cov=src/adri --cov-report=html

# Enterprise-specific
pytest tests/logging/test_enterprise.py -v
pytest tests/events/ -v
pytest tests/callbacks/ -v

# Integration tests
pytest tests/integration/ -v

# Performance tests (if applicable)
pytest tests/performance/ -v
```

### Compatibility Tests
```bash
# Test backward compatibility
python tests/test_package_metadata.py
python tests/test_upstream_compatibility.py

# Test import compatibility
python -c "import adri; assert adri.__version__"

# Test decorator still works
python -c "from adri import adri_protected; print('Decorator OK')"
```

## Sync Frequency

### Recommended Schedule
- **Weekly check**: Automated workflow checks for upstream updates
- **Monthly review**: Manual review of upstream changes
- **Quarterly sync**: Full synchronization of core modules
- **Ad-hoc sync**: Critical bug fixes or security patches

### Automated Check
The `.github/workflows/upstream-sync-check.yml` workflow:
- Runs weekly on Monday 9 AM UTC
- Fetches upstream main branch
- Compares commits since last sync
- Creates GitHub issue if updates available
- No automatic merging - manual review required

## Version Coordination

### Version Strategy
- **Community ADRI**: vX.Y.Z (open source)
- **verodat-adri**: vX.Y.Z (enterprise, same major.minor)
- **Sync tracking**: sync/upstream-vX.Y.Z tags

### Example
```
Community:    v5.0.0, v5.0.1, v5.1.0
Enterprise:   v5.0.0, v5.0.1, v5.1.0
Sync tags:    sync/upstream-v5.0.1, sync/upstream-v5.1.0
```

## Rollback Procedure

If sync causes issues:

```bash
# Create rollback branch
git checkout -b rollback/sync-YYYY-MM-DD

# Revert the sync merge commit
git revert <sync-merge-commit>

# Or reset to before sync
git reset --hard <commit-before-sync>

# Force push (only on feature branch!)
git push origin rollback/sync-YYYY-MM-DD --force

# Create PR to revert
gh pr create --title "rollback: Revert upstream sync due to <issue>"
```

## Sync History

### Last Sync
- **Date**: 2025-10-20
- **Source**: adri-standard/adri @ v5.0.1 (commit 6a06422)
- **Status**: Sync checkpoint - no core changes to merge
- **Notes**: Upstream v5.0.1 is "open-source split" release (16 commits) that only removed enterprise features. No core bug fixes or improvements found. Enterprise fork maintains all features on v5.0.1 base.

### Sync Log
| Date | Source Version | Modules Synced | Conflicts | Notes |
|------|---------------|----------------|-----------|-------|
| 2025-04-05 | v4.4.0 | All | None | Initial fork |
| 2025-10-20 | v5.0.1 | None (version bump only) | None | Upstream only removed enterprise features, no core improvements. All enterprise modules preserved. Version updated to v5.0.1 base. |

---

## Support

For questions about upstream synchronization:
- Create an issue in verodat-adri repository
- Tag with `upstream-sync` label
- Contact: Verodat engineering team

## References

- Community ADRI: https://github.com/adri-standard/adri
- Enterprise Features: See ENTERPRISE_FEATURES.md
- Version Strategy: See implementation_plan.md
