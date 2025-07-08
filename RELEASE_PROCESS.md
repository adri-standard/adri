# ADRI Validator Release Process 🚀

## Overview

The ADRI Validator uses an automated, GitHub Release-triggered deployment pipeline with pre-filled draft releases that automatically handles TestPyPI → Production PyPI deployment with comprehensive failure recovery.

## 🎯 Key Features

- ✅ **Automated Draft Releases** - Pre-filled release notes on every push
- ✅ **GitHub Release Triggered** - Select and publish from ready drafts
- ✅ **TestPyPI → Production Pipeline** - Automatic safety validation
- ✅ **Failure Recovery** - Automatic rollback and retry capability
- ✅ **Version Auto-Update** - No manual version file editing required
- ✅ **Comprehensive Testing** - Full test suite + smoke tests
- ✅ **Smart Tag Conversion** - Candidate tags automatically converted
- ✅ **Slack Notifications** - Success/failure alerts (configurable)

## 🔄 Release Workflow

### 1. **Automated Draft Preparation**
Every push to `main` automatically:
1. ✅ **Calculates valid next versions** from VERSION.json
2. ✅ **Creates/updates draft releases** with pre-filled notes
3. ✅ **Generates commit summaries** since last release
4. ✅ **Provides ready-to-publish options**

### 2. **Select and Publish Release**
1. Go to [GitHub Releases](https://github.com/ThinkEvolveSolve/adri-validator/releases)
2. **Select from available drafts:**
   - 🚀 **ADRI v0.3.0 - Minor Release (DRAFT)** ← Production release
   - 🧪 **ADRI v0.3.0-beta.1 - Beta Minor (DRAFT)** ← Beta testing
   - 🔧 **ADRI v0.2.1 - Patch Release (DRAFT)** ← Bug fixes
3. **Edit release notes** (add specific changes)
4. **Click "Publish release"** to trigger deployment

### 3. **Automatic Pipeline Execution**
The workflow automatically:
1. ✅ **Converts candidate tag** to proper release format
2. ✅ **Validates version** against VERSION.json rules
3. ✅ **Updates version files** (pyproject.toml, adri/version.py)
4. ✅ **Runs full test suite** (90% coverage requirement)
5. ✅ **Builds package** (source + wheel distributions)
6. ✅ **Publishes to TestPyPI** first
7. ✅ **Runs TestPyPI smoke tests** (installation + functionality)
8. ✅ **Publishes to Production PyPI** (only if TestPyPI succeeds)
9. ✅ **Runs Production smoke tests** (final validation)
10. ✅ **Updates release notes** with deployment status
11. ✅ **Sends notifications** (Slack, if configured)

### 4. **Success Outcome**
- 📦 Package available on PyPI: `pip install adri==0.3.0`
- 🏷️ GitHub release updated with deployment status
- 📝 Installation instructions and links provided
- 🔔 Team notified via Slack
- ✅ VERSION.json automatically updated for next release

## 🎯 Available Release Types

### **Production Releases**
- **🔧 Patch Release** (e.g., v0.2.1) - Bug fixes only
- **🚀 Minor Release** (e.g., v0.3.0) - New features, backward compatible
- **💥 Major Release** (e.g., v1.0.0) - Breaking changes

### **Beta Releases**
- **🧪 Beta Patch** (e.g., v0.2.1-beta.1) - Testing bug fixes
- **🧪 Beta Minor** (e.g., v0.3.0-beta.1) - Testing new features
- **🧪 Beta Major** (e.g., v1.0.0-beta.1) - Testing breaking changes

## 🚨 Failure Recovery

### If Release Fails:
1. **Release marked as draft** automatically
2. **Failure details** added to release notes
3. **Git tag preserved** (no version bump needed)
4. **Team notified** via Slack with failure details

### To Retry Failed Release:
1. **Fix the issues** identified in workflow logs
2. **Push fixes** to repository (if code changes needed)
3. **Re-publish the draft release** (same version number)
4. **Workflow re-runs automatically**

## 📋 Manual Workflow Trigger (Backup)

If needed, you can manually trigger the workflow:

1. Go to **Actions** → **"Release to PyPI (TestPyPI → Production)"**
2. Click **"Run workflow"**
3. Enter **tag name**: `Release.Minor.v0.3.0`
4. Optionally check **force republish** (if version exists)
5. Click **"Run workflow"**

## 🔧 Configuration

### Required Secrets
- `TESTPYPI` - TestPyPI API token
- `PYPI` - Production PyPI API token
- `SLACK_WEBHOOK_URL` - Slack notifications (optional)

### Environment Protection
- **testpypi** environment - For TestPyPI deployment
- **production** environment - For Production PyPI deployment

## 📊 Current Status

### ✅ Completed Setup
- [x] Automated draft release system (`prepare-releases.yml`)
- [x] Enhanced release workflow (`release-to-pypi.yml`)
- [x] Release note templates created
- [x] Candidate tag conversion system
- [x] Version updated to 0.3.0 (ready for release)
- [x] Failure recovery system implemented
- [x] TestPyPI → Production pipeline configured

### 🔄 Ready for Release
- **Version**: 0.3.0
- **Package Name**: `adri`
- **Installation**: `pip install adri==0.3.0`
- **Release Type**: Minor (new features, backward compatible)

## 🚀 Next Steps

### To Release v0.3.0:
1. **Push any final changes** to main branch
2. **Check GitHub Releases** for updated draft releases
3. **Select appropriate draft** (recommend: Minor Release)
4. **Edit release notes** with specific changes
5. **Publish release** to trigger deployment
6. **Monitor workflow** in GitHub Actions

### Future Releases:
- Push code → Draft releases auto-update
- Select appropriate draft → Edit notes → Publish
- Version numbers automatically calculated
- TestPyPI validation ensures production safety
- Failure recovery allows easy retries

## 🎮 User Experience

**Before (Manual):**
1. Manually create tag with complex format
2. Manually write release notes
3. Risk of tag format errors
4. Manual version management

**After (Automated):**
1. Push code → See updated draft releases
2. Select desired release type → Edit notes → Publish
3. Zero tag format errors
4. Automatic version management

## 🔗 Useful Links

- **GitHub Releases**: https://github.com/ThinkEvolveSolve/adri-validator/releases
- **GitHub Actions**: https://github.com/ThinkEvolveSolve/adri-validator/actions
- **PyPI Package**: https://pypi.org/project/adri/
- **TestPyPI Package**: https://test.pypi.org/project/adri/
- **Release Workflow**: `.github/workflows/release-to-pypi.yml`
- **Draft Preparation**: `.github/workflows/prepare-releases.yml`

## 📞 Support

For issues with the release process:
1. Check **GitHub Actions logs** for detailed error information
2. Review **release notes** for failure details
3. Use **manual workflow trigger** as backup
4. Contact team via **Slack** for assistance

## 🧪 Testing the Release Process

### Recommended First Test:
1. **Push a small change** to main branch
2. **Verify draft releases** are created/updated
3. **Publish beta release** (`v0.3.0-beta.1`) for testing
4. **Monitor full pipeline** execution
5. **Test installation** from both TestPyPI and PyPI
6. **Publish production release** (`v0.3.0`) if beta succeeds

---

**ADRI Validator Release Process: Automated, Safe, Reliable** ✅
