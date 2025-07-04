# ADRI Validator - Branching & Release Strategy

## 🌳 Branch Structure

### Three-Tier Architecture
```
feature/xyz → main → production
     ↓         ↓         ↓
   Feature   Stable   Production
     Dev      Code     Releases
```

### Branch Descriptions

#### **`feature/*` branches**
- **Purpose**: Individual feature development
- **Access**: Developers can push directly
- **Merge Target**: `main` via Pull Request
- **CI**: Fast feedback with reduced test matrix

#### **`main` branch**
- **Purpose**: Stable development code (default branch)
- **Access**: Protected - no direct pushes
- **Requirements**: PR approval + CI passing
- **CI**: Full test suite + comprehensive checks

#### **`production` branch**
- **Purpose**: Production-ready releases only
- **Access**: Highly protected - automation only
- **Triggers**: Automatic PyPI publication
- **CI**: Release automation + package building

## 🚀 Release Process

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/new-assessment-engine
# Develop and commit changes
git add .
git commit -m "Add new assessment engine"
git push origin feature/new-assessment-engine
```

### 2. Pull Request to Main
- Create PR from `feature/new-assessment-engine` → `main`
- **Automatic Checks**:
  - ✅ Feature CI runs (fast feedback)
  - ✅ Code quality checks (black, isort, flake8)
  - ✅ Security scans (bandit, safety, pip-audit)
  - ✅ Test coverage (90% minimum)
- **Manual Review**: Team approval required
- **Auto-merge**: Available after approvals

### 3. Production Release
Use GitHub Actions "Promote to Production" workflow:

1. **Navigate**: GitHub → Actions → "Promote to Production"
2. **Input**:
   - Version: `0.1.1` (semantic versioning)
   - Release Notes: Brief description of changes
3. **Automation**:
   - ✅ Updates `pyproject.toml` version
   - ✅ Creates git tag `v0.1.1`
   - ✅ Merges `main` → `production`
   - ✅ Updates CHANGELOG.md
   - ✅ Triggers production release workflow
   - ✅ Builds and publishes to PyPI
   - ✅ Creates GitHub release

## 🔧 CI/CD Workflows

### **Feature Branch CI** (`.github/workflows/feature-ci.yml`)
**Triggers**: Push to `feature/*`, PRs to `main`
- **Fast Matrix**: Python 3.9, 3.11, 3.12
- **Quality Checks**: black, isort, flake8
- **Security**: bandit, safety, pip-audit
- **Tests**: Unit + integration with 90% coverage
- **PR Comments**: Automatic status updates

### **Main Branch CI** (`.github/workflows/test.yml`)
**Triggers**: Push to `main`, PRs to `main`
- **Full Matrix**: Python 3.8, 3.9, 3.10, 3.11, 3.12
- **Comprehensive Testing**: All test suites
- **Performance**: Benchmark tracking
- **Coverage**: Strict 90% requirement
- **Artifacts**: Coverage reports, benchmarks

### **Production Release** (`.github/workflows/release.yml`)
**Triggers**: Push to `production` branch
- **Testing**: Full test suite validation
- **Building**: Package creation and validation
- **Publishing**: Automatic PyPI publication
- **Release**: GitHub release with artifacts

### **Promote to Production** (`.github/workflows/promote-to-production.yml`)
**Triggers**: Manual workflow dispatch
- **Version Management**: Automatic version bumping
- **Changelog**: Automatic CHANGELOG.md updates
- **Merging**: `main` → `production` with release commit
- **Tagging**: Semantic version tags

## 🔒 Branch Protection Rules

### **Main Branch Protection**
```yaml
Required Status Checks:
  - Feature Branch CI / test
  - Feature Branch CI / security-scan
  
Required Reviews:
  - 1+ approvals required
  - Dismiss stale reviews: true
  - Require review from code owners: true

Restrictions:
  - Restrict pushes to admins only
  - No force pushes allowed
  - Require branches to be up to date
```

### **Production Branch Protection**
```yaml
Required Status Checks:
  - Main Branch CI / test
  - Main Branch CI / security
  
Required Reviews:
  - 2+ approvals for manual merges
  - Only release automation can push
  
Restrictions:
  - No direct pushes by anyone
  - No force pushes allowed
  - Require signed commits
```

## 📦 Version Management

### **Semantic Versioning**
- **MAJOR**: Breaking changes (1.0.0 → 2.0.0)
- **MINOR**: New features, backward compatible (0.1.0 → 0.2.0)
- **PATCH**: Bug fixes, backward compatible (0.1.0 → 0.1.1)

### **Current Strategy**
- **Beta Releases**: 0.1.x series
- **Stable Releases**: 1.0.0+ when ready for public
- **Pre-releases**: 0.1.0-rc1, 0.1.0-beta1, 0.1.0-alpha1

### **Version Automation**
- **pyproject.toml**: Single source of truth
- **Git Tags**: Automatic `v0.1.1` format
- **PyPI**: Matches git tag versions
- **CHANGELOG**: Automatic updates

## 🎯 Developer Workflow

### **Daily Development**
1. **Start**: `git checkout -b feature/my-feature`
2. **Develop**: Make changes, commit frequently
3. **Test**: Run tests locally before pushing
4. **Push**: `git push origin feature/my-feature`
5. **PR**: Create PR to `main` with description
6. **Review**: Address feedback, CI must pass
7. **Merge**: Auto-merge after approvals

### **Release Workflow**
1. **Prepare**: Ensure `main` is stable and tested
2. **Release**: Use "Promote to Production" workflow
3. **Verify**: Check PyPI publication and GitHub release
4. **Announce**: Update team on new version availability

## 🛡️ Security & Quality Gates

### **Automated Security**
- **Bandit**: Python security linting
- **Safety**: Dependency vulnerability scanning
- **pip-audit**: Package security auditing
- **Dependency Updates**: Automated via Dependabot

### **Code Quality**
- **Black**: Code formatting (88 char line length)
- **isort**: Import sorting
- **flake8**: Linting and style checks
- **Coverage**: 90% minimum requirement

### **Performance Monitoring**
- **Benchmarks**: Automated performance tracking
- **Regression Detection**: Performance comparison
- **Artifact Storage**: Historical benchmark data

## 📋 Manual Setup Required

### **Repository Settings** (GitHub UI)
1. **Default Branch**: Set to `main`
2. **Branch Protection**: Configure rules above
3. **Secrets**: Add `PYPI_API_TOKEN`
4. **Environments**: Create `release` environment (optional)

### **Team Configuration**
1. **Code Owners**: Create `.github/CODEOWNERS`
2. **Issue Templates**: Add contribution guidelines
3. **Discussions**: Enable for community feedback

## 🎉 Benefits

### **For Developers**
- ✅ **Fast Feedback**: Quick CI on feature branches
- ✅ **Safe Merging**: Protected main branch
- ✅ **Automated Quality**: Consistent code standards
- ✅ **Clear Process**: Well-defined workflow

### **For Releases**
- ✅ **Automated Publishing**: No manual PyPI uploads
- ✅ **Version Control**: Semantic versioning
- ✅ **Release Notes**: Automatic changelog generation
- ✅ **Rollback Safety**: Tagged releases for easy rollback

### **For Production**
- ✅ **Stability**: Only tested code reaches production
- ✅ **Traceability**: Clear audit trail
- ✅ **Security**: Automated vulnerability scanning
- ✅ **Performance**: Benchmark tracking

---

**🎯 Result**: Production-ready CI/CD pipeline with automated quality gates, security scanning, and seamless release management for the ADRI Validator package.
