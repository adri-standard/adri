---
sidebar_position: 8
---

# Reliable Development Workflow

**How to ensure local testing catches all issues before GitHub CI**

## The Problem We Solved

Previously, our local testing was incomplete:
- ✅ We tested functionality (builds, ACT, local server)
- ❌ We skipped formatting checks (pre-commit hooks)
- **Result**: Local tests passed, GitHub CI failed on formatting

## The Solution

### **1. Comprehensive Local CI Script**

Run the complete GitHub CI pipeline locally:

```bash
./scripts/local-ci-test.sh
```

This script mirrors **exactly** what GitHub Actions runs:
- All pre-commit hooks (formatting, linting, security)
- Python tests and build verification
- Documentation build testing
- ACT workflow simulation

### **2. Automated Pre-commit Hooks**

Pre-commit hooks now run automatically on every commit:

```bash
# One-time setup (done for you)
pre-commit install

# Now every git commit automatically runs:
# - Trailing whitespace removal
# - End-of-file fixes
# - YAML/TOML validation
# - Black formatting
# - Import sorting
# - Flake8 linting
# - Security scanning
```

## **Improved Development Workflow**

### **Before Making Changes**
```bash
# 1. Create feature branch
git checkout -b feat/my-feature

# 2. Make your changes
# ... edit files ...
```

### **Before Committing**
```bash
# 3. Run comprehensive local CI
./scripts/local-ci-test.sh

# If it passes:
✅ ALL CHECKS PASSED - Ready for GitHub!

# If it fails:
❌ X CHECK(S) FAILED
🔧 Fix issues above before committing
```

### **Committing Changes**
```bash
# 4. Commit (pre-commit hooks run automatically)
git add .
git commit -m "feat: your feature description"

# 5. Push with confidence
git push origin feat/my-feature
```

### **Creating PR**
```bash
# 6. Create PR
gh pr create --title "feat: Your Feature" --body "Description"

# 7. CI will pass because local testing was comprehensive
```

## **What This Prevents**

### **Before (Unreliable)**
```
Local Test → "Looks good!" → Push → GitHub CI Fails → Fix → Push Again
```

### **After (Reliable)**
```
Local CI Script → Fix Issues → Commit → Push → GitHub CI Passes ✅
```

## **Emergency Workflows**

### **If GitHub CI Still Fails**
```bash
# 1. Check what GitHub CI ran
gh pr checks PR_NUMBER

# 2. Get detailed logs
gh run view RUN_ID --log-failed

# 3. Reproduce locally
./scripts/local-ci-test.sh

# 4. Fix and retry
git add . && git commit -m "fix: address CI issues"
git push
```

### **Quick Pre-commit Fix**
```bash
# Run only pre-commit checks
pre-commit run --all-files

# Auto-fix formatting
git add . && git commit -m "fix: pre-commit formatting"
```

## **Key Lessons**

### **Why Local Testing Failed Before**
1. **Incomplete testing** - Only tested functionality, not formatting
2. **Missing pre-commit** - Hooks weren't installed or run
3. **No CI simulation** - Didn't mirror GitHub Actions environment

### **Why It's Reliable Now**
1. **Complete coverage** - Tests everything GitHub CI tests
2. **Automated hooks** - Pre-commit runs on every commit
3. **Exact mirroring** - Same commands, same environment
4. **Early feedback** - Catch issues before they reach GitHub

## **Best Practices**

### **For All Contributors**
```bash
# Run before any commit
./scripts/local-ci-test.sh

# Trust the output - if it passes locally, GitHub CI will pass
```

### **For New Contributors**
```bash
# One-time setup
pre-commit install

# Then follow the workflow above
```

### **For Complex Changes**
```bash
# Test specific components
cd docs && npm run build              # Test docs only
pre-commit run flake8 --all-files    # Test Python linting only
pytest tests/ -v                     # Test Python functionality only
```

## **Technical Details**

### **Pre-commit Hook Configuration**
- **Formatting**: trailing-whitespace, end-of-file-fixer
- **Validation**: check-yaml, check-toml, check-merge-conflict
- **Python**: black, isort, flake8, bandit
- **Security**: bandit security scanning

### **CI Pipeline Mirroring**
- **Node.js**: Same version (18) as GitHub Actions
- **Python**: Tests across multiple versions like CI
- **ACT**: Simulates actual GitHub Actions containers
- **Build**: Same npm commands as production workflow

**This workflow ensures 100% reliability between local testing and GitHub CI.** 🎯
