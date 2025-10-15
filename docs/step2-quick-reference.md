# Step 2 Quick Reference: Enterprise Repository Setup

## Overview
Set up the private `Verodat/adri-enterprise` repository as a complete fork of the open-source repository.

## Prerequisites Checklist
- [ ] GitHub account with Verodat organization access
- [ ] Admin permissions to create private repositories
- [ ] Git SSH authentication configured
- [ ] Step 1 completed (rollback safety net in place)

## Quick Start

### Option A: Automated Setup (Recommended)
```bash
# Run from ADRI repository root
bash scripts/setup-enterprise-repo.sh
```

### Option B: Manual Setup
Follow the detailed guide: `docs/enterprise-setup-guide.md`

## Step-by-Step Summary

### 2.1: Create Private Repository
```bash
# Using GitHub CLI
gh repo create Verodat/adri-enterprise \
  --private \
  --description "ADRI Enterprise - Advanced AI data quality framework with enterprise features" \
  --confirm
```

Or manually via https://github.com/Verodat

### 2.2-2.3: Clone and Push
```bash
# Clone from open-source
git clone https://github.com/adri-standard/adri.git adri-enterprise-temp
cd adri-enterprise-temp

# Checkout pre-split tag
git checkout v5.0.0-pre-split

# Add enterprise remote
git remote add enterprise git@github.com:Verodat/adri-enterprise.git

# Push everything
git push enterprise --all
git push enterprise --tags
```

### 2.4: Configure Repository Settings
On GitHub (`https://github.com/Verodat/adri-enterprise/settings`):

**Branch Protection (main):**
- ✅ Require pull request before merging (1 approval)
- ✅ Require status checks to pass
- ✅ Require linear history
- ✅ Include administrators

**Security:**
- ✅ Enable Dependabot alerts
- ✅ Enable secret scanning
- ✅ Enable dependency graph

### 2.5-2.6: Verify CI Pipeline
```bash
# Make test commit to trigger CI
echo "" >> README.md
git add README.md && git commit -m "ci: trigger initial CI" && git push enterprise main

# Monitor at https://github.com/Verodat/adri-enterprise/actions
```

## Verification Checklist

After completion, verify:
- [ ] Private repository exists at `Verodat/adri-enterprise`
- [ ] Repository visibility set to Private
- [ ] All commits and tags pushed successfully
- [ ] Branch protection enabled on main
- [ ] Security features enabled
- [ ] CI pipeline runs and passes all tests
- [ ] Repository settings configured

## Expected Results

**Repository State:**
- Commit: 328536f75d96c6c02776fb9ff72b63c47df7fe9e
- Tag: v5.0.0-pre-split
- Tests: ~1135 passing, 8 skipped
- Coverage: ~60%

**CI Matrix (should all pass):**
- Ubuntu + Python 3.10, 3.11, 3.12, 3.13
- Windows + Python 3.12
- macOS + Python 3.12

## Time Estimate
- Automated: ~10 minutes
- Manual: ~20 minutes

## Troubleshooting

### Permission Denied
```bash
# Check SSH
ssh -T git@github.com

# Or use HTTPS with token
git remote set-url enterprise https://TOKEN@github.com/Verodat/adri-enterprise.git
```

### CI Not Running
1. Check Actions are enabled in settings
2. Verify workflow file exists: `.github/workflows/ci.yml`
3. Re-trigger manually from Actions tab

### Branch Protection Blocks Push
- Use pull requests for protected branches
- Or temporarily disable protection for initial setup

## Next Steps

After Step 2 completion:
1. ✅ Enterprise repository is set up
2. ➡️ **Proceed to Step 3:** Refactor Open-Source Repository
3. ➡️ **Then Step 5:** Enhance Enterprise Repository

## Resources

- **Full Guide:** `docs/enterprise-setup-guide.md`
- **Automation Script:** `scripts/setup-enterprise-repo.sh`
- **Implementation Plan:** `implementation_plan.md` (Step 2)
- **Rollback:** `scripts/restore-from-rollback.sh`

---
**Status:** Preparation Complete - Ready for Execution
**Last Updated:** October 15, 2025
