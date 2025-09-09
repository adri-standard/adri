# 🧪 Issue-Driven Workflow Verification Test

## ✅ **Setup Verification Checklist**

### GitHub Configuration Status
- [ ] **Rulesets**: Only one active ruleset targeting `main` branch
- [ ] **Teams**: `@adri-standard/maintainers` team created and configured
- [ ] **CODEOWNERS**: References correct team `@adri-standard/maintainers`
- [ ] **Branch Protection**: All status checks enabled and required
- [ ] **GitHub Actions**: Both validation workflows active

## 🎯 **Test Scenarios to Execute**

### **Test 1: High-Risk Change (Core Module) - Full Enforcement**
**Objective**: Verify strict enforcement for critical ADRI functionality

**Steps:**
1. Create issue: "Test Core Module Change"
2. Create branch: `feat/issue-[NUMBER]-test-core-validation`
3. Modify file: `adri/core/assessor.py` (add comment)
4. Create PR with proper issue reference
5. **Expected**: ✅ All validations pass, review required

**Expected Validation Results:**
- ✅ Issue link validation: PASS (required and enforced)
- ✅ Branch naming validation: PASS (required and enforced)
- ✅ CODEOWNERS review: Required from @adri-standard/maintainers
- ✅ All status checks: Must pass before merge

### **Test 2: Low-Risk Change (Documentation) - Friendly Guidance**
**Objective**: Verify growth-friendly approach for documentation

**Steps:**
1. Create branch with any name: `update-readme-typo`
2. Modify file: `README.md` (fix typo or add sentence)
3. Create PR without issue reference
4. **Expected**: 💡 Friendly suggestions, no blocking

**Expected Validation Results:**
- 💡 Issue link validation: GUIDANCE (suggested but not enforced)
- 💡 Branch naming validation: GUIDANCE (suggested but not enforced)
- ✅ CODEOWNERS review: Required from @adri-standard/maintainers
- ✅ Status checks: Must pass (CI/quality checks)

### **Test 3: Medium-Risk Change (CLI) - Guided Enhancement**
**Objective**: Verify balanced approach for important but non-critical changes

**Steps:**
1. Create issue: "Test CLI Enhancement"
2. Create branch: `enhance/issue-[NUMBER]-cli-improvement`
3. Modify file: `adri/cli/commands.py` (add comment)
4. Create PR with proper issue reference
5. **Expected**: ⚠️ Helpful warnings, guidance but no hard blocking

### **Test 4: Violation Testing - Error Handling**
**Objective**: Verify helpful error messages and guidance

**Steps:**
1. Create branch: `bad-branch-name-format`
2. Modify file: `adri/core/protection.py` (high-risk change)
3. Create PR without issue reference
4. **Expected**: ❌ Clear error with helpful guidance

## 🤖 **Automated Validation Points**

### GitHub Actions Behavior
- **High-risk files**: `adri/core/`, `adri/decorators/`, `adri/standards/`
- **Medium-risk files**: `adri/cli/`, `adri/config/`, `adri/analysis/`, `tests/`
- **Low-risk files**: `docs/`, `examples/`, `README.md`, `*.md`

### Status Checks Required
- `Validate PR has linked issue`
- `Validate branch naming convention`
- `code quality`
- `test`
- `security`
- `performance`
- `conventional-commits`
- `pre-commit`

## 📊 **Success Criteria**

### ✅ **Quality Protection (High-Risk)**
- Core changes MUST have issue links (blocked if missing)
- Core changes MUST follow branch naming (blocked if wrong)
- All status checks MUST pass
- Review from maintainers REQUIRED

### 🚀 **Growth Enablement (Low-Risk)**
- Documentation changes get friendly suggestions
- No blocking for missing issue links on docs
- No blocking for branch naming on docs
- Review still required but process is welcoming

### 🤖 **Smart Automation**
- Different messages for different risk levels
- Helpful explanations of why requirements exist
- Clear guidance on how to fix issues
- Progressive enforcement based on file changes

## 🧪 **Ready to Test**

Once verified, we can execute these tests to prove:
1. **Quality is protected** where it matters (core functionality)
2. **Growth is enabled** where it helps (documentation)
3. **Developer experience is excellent** with helpful automation
4. **Community adoption is maximized** with tiered approach

This demonstrates the first-ever **adaptive repository governance** system!
