# ADRI Enterprise Repository Setup Guide

## Overview

This guide provides step-by-step instructions for setting up the private `adri-enterprise` repository as a fork of the open-source `adri` repository.

**Target Repository:** `Verodat/adri-enterprise` (private)
**Source Repository:** `adri-standard/adri`
**Version:** 5.0.0

## Prerequisites

- GitHub account with access to Verodat organization
- Admin permissions to create private repositories
- Git installed and configured locally
- SSH key or personal access token for GitHub authentication

## Step 2.1: Create Private GitHub Repository

### Manual Setup via GitHub Web Interface

1. **Navigate to Verodat Organization:**
   - Go to https://github.com/Verodat
   - Click "New repository" button

2. **Repository Configuration:**
   - **Repository name:** `adri-enterprise`
   - **Description:** "ADRI Enterprise - Advanced AI data quality framework with enterprise features"
   - **Visibility:** ⚠️ **Private** (CRITICAL - must be private)
   - **Initialize repository:** ❌ Do NOT initialize with README, .gitignore, or license
   - Click "Create repository"

3. **Note the Repository URL:**
   ```
   git@github.com:Verodat/adri-enterprise.git
   ```

### Alternative: Using GitHub CLI

If you have GitHub CLI (`gh`) installed:

```bash
# Create private repository
gh repo create Verodat/adri-enterprise \
  --private \
  --description "ADRI Enterprise - Advanced AI data quality framework with enterprise features" \
  --confirm

# Verify repository was created
gh repo view Verodat/adri-enterprise
```

## Step 2.2: Clone Current Repository State

**IMPORTANT:** We're cloning from the `v5.0.0-pre-split` tag to ensure we get the complete pre-split codebase.

```bash
# Navigate to your workspace
cd ~/workspace  # or your preferred location

# Clone the current ADRI repository
git clone https://github.com/adri-standard/adri.git adri-enterprise-temp

# Navigate into the cloned repository
cd adri-enterprise-temp

# Checkout the pre-split tag to ensure we have the complete codebase
git checkout v5.0.0-pre-split

# Verify we're at the correct commit
git log -1 --oneline
# Should show: 328536f chore: trigger full CI tests for PR validation
```

## Step 2.3: Push to Enterprise Repository

```bash
# Still in adri-enterprise-temp directory

# Add enterprise remote
git remote add enterprise git@github.com:Verodat/adri-enterprise.git

# Verify remotes
git remote -v
# Should show both 'origin' (adri-standard) and 'enterprise' (Verodat)

# Push all branches and tags to enterprise repository
git push enterprise --all
git push enterprise --tags

# Verify the push
git ls-remote enterprise
```

## Step 2.4: Configure Repository Settings

### Branch Protection Rules

1. **Navigate to Repository Settings:**
   - Go to `https://github.com/Verodat/adri-enterprise/settings`
   - Click "Branches" in left sidebar

2. **Add Branch Protection Rule for `main`:**
   - Click "Add branch protection rule"
   - **Branch name pattern:** `main`
   - ✅ **Require a pull request before merging**
     - ✅ Require approvals: 1
     - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ **Require status checks to pass before merging**
     - ✅ Require branches to be up to date before merging
     - Add required status checks (after CI is set up):
       - `test-ubuntu-3.10`
       - `test-ubuntu-3.11`
       - `test-ubuntu-3.12`
       - `test-ubuntu-3.13`
       - `test-windows-3.12`
       - `test-macos-3.12`
   - ✅ **Require linear history**
   - ✅ **Include administrators** (enforce for admins too)
   - Click "Create"

3. **Add Branch Protection Rule for Release Branches:**
   - Click "Add branch protection rule"
   - **Branch name pattern:** `release/*`
   - Apply same settings as main branch
   - Click "Create"

### Repository Settings

1. **General Settings:**
   - ✅ Disable "Allow merge commits" (use squash or rebase only)
   - ✅ Enable "Automatically delete head branches"
   - ✅ Enable "Allow auto-merge"

2. **Security Settings:**
   - Navigate to "Security" → "Code security and analysis"
   - ✅ Enable "Dependency graph"
   - ✅ Enable "Dependabot alerts"
   - ✅ Enable "Dependabot security updates"
   - ✅ Enable "Secret scanning"

3. **Actions Settings:**
   - Navigate to "Actions" → "General"
   - ✅ Allow all actions and reusable workflows
   - Set "Workflow permissions" to "Read repository contents permission"

## Step 2.5: Setup GitHub Actions CI/CD Workflows

The workflow files should already be in the repository from the original codebase. If not, create them:

### Create `.github/workflows/ci.yml`

This file should already exist in the repository. If not, it needs to be created. The workflow is defined in a separate file that will be created next.

### Create `.github/workflows/release.yml`

For enterprise releases, create a release workflow (this will be added in Step 5).

### Verify Workflow Files

```bash
# Check if workflow files exist
ls -la .github/workflows/

# Expected files:
# - ci.yml (should exist from open-source)
# - release.yml (will be added in Step 5)
```

## Step 2.6: Verify CI Pipeline

1. **Trigger Initial CI Run:**
   ```bash
   # Make a small test commit to trigger CI
   echo "" >> README.md
   git add README.md
   git commit -m "ci: trigger initial CI pipeline test"
   git push enterprise main
   ```

2. **Monitor CI Execution:**
   - Go to `https://github.com/Verodat/adri-enterprise/actions`
   - Click on the running workflow
   - Verify all jobs complete successfully:
     - ✅ Ubuntu + Python 3.10
     - ✅ Ubuntu + Python 3.11
     - ✅ Ubuntu + Python 3.12
     - ✅ Ubuntu + Python 3.13
     - ✅ Windows + Python 3.12
     - ✅ macOS + Python 3.12

3. **Review Test Results:**
   - Expected: ~1135 tests passing, 8 skipped
   - Coverage: Should be ~60%
   - All lint checks passing

## Verification Checklist

After completing all steps, verify:

- [ ] Private repository created at `Verodat/adri-enterprise`
- [ ] Repository is marked as Private (not Public)
- [ ] All commits and tags pushed from original repository
- [ ] Branch protection enabled on `main` branch
- [ ] Security features enabled (Dependabot, secret scanning)
- [ ] GitHub Actions CI workflow running successfully
- [ ] All test platforms passing (Ubuntu, Windows, macOS)
- [ ] Repository settings configured correctly

## Post-Setup Tasks

1. **Update Repository Description and Topics:**
   - Add topics: `python`, `data-quality`, `ai`, `enterprise`, `validation`
   - Ensure description is clear and professional

2. **Configure Access Permissions:**
   - Add team members with appropriate permissions
   - Verodat team: Write access
   - Select customers: Read access (if needed)

3. **Setup Branch Strategy:**
   - `main` - Production-ready enterprise code
   - `develop` - Integration branch for features
   - `feature/*` - Feature development branches
   - `release/*` - Release preparation branches

4. **Document Enterprise-Specific Setup:**
   - Create `CONTRIBUTING-ENTERPRISE.md`
   - Create `SECURITY-ENTERPRISE.md`
   - Update README with enterprise-specific content

## Troubleshooting

### Issue: Permission Denied When Creating Repository

**Solution:** Ensure you have admin rights in Verodat organization. Contact organization admin if needed.

### Issue: Push to Enterprise Remote Fails

**Solution:**
```bash
# Check authentication
ssh -T git@github.com

# Or use HTTPS with token
git remote set-url enterprise https://TOKEN@github.com/Verodat/adri-enterprise.git
```

### Issue: CI Workflow Not Running

**Solution:**
1. Check if Actions are enabled in repository settings
2. Verify workflow file syntax: `cat .github/workflows/ci.yml`
3. Check workflow run history for errors
4. Re-trigger workflow manually from Actions tab

### Issue: Branch Protection Blocking Pushes

**Solution:**
- Use pull requests instead of direct pushes to protected branches
- Or temporarily disable branch protection for initial setup

## Next Steps

After completing Step 2, proceed to:
- **Step 3:** Refactor Open-Source Repository (remove enterprise features)
- **Step 5:** Enhance Enterprise Repository (add new enterprise features)

## Support and Resources

- **Implementation Plan:** See `implementation_plan.md` for complete details
- **GitHub Documentation:** https://docs.github.com/en/repositories
- **Actions Documentation:** https://docs.github.com/en/actions
- **Verodat Internal:** Contact DevOps team for organization-level access

---

**Last Updated:** October 15, 2025
**Version:** 1.0.0
**Maintained By:** ADRI Development Team
