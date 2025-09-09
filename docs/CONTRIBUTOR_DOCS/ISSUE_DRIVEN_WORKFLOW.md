# Issue-Driven Development Workflow

## Overview

ADRI follows an **issue-driven development workflow** to ensure complete feature-to-issue traceability and maintain community transparency. This approach means that all development work must originate from a GitHub issue, enabling better project governance, community input, and progress tracking.

## 🎯 Core Principles

1. **Issue-First Development**: Every feature, enhancement, or bug fix must have a corresponding GitHub issue
2. **Community Visibility**: All development decisions and progress are visible to the community
3. **Structured Process**: Clear templates and automation guide contributors through the workflow
4. **Quality Assurance**: Automated validation ensures adherence to standards

## 📋 Workflow Steps

### 1. Create an Issue

**Before writing any code**, create an issue using the appropriate template:

- **🚀 Feature Request**: For completely new functionality
- **⚡ Enhancement**: For improvements to existing features  
- **🐛 Bug Reports**: For data quality, framework integration, or general bugs
- **💬 Discussion**: For architectural decisions or community input

#### Issue Creation Best Practices

- Use descriptive titles with appropriate prefixes (`[Feature]`, `[Enhancement]`, `[Bug]`, etc.)
- Fill out all template sections completely
- Include clear acceptance criteria for features/enhancements
- Reference related issues if applicable
- Add relevant labels and assign team members if needed

### 2. Plan Your Implementation

- Review the issue requirements thoroughly
- Consider framework compatibility and breaking changes
- Plan your testing approach
- Identify documentation needs
- Estimate scope and complexity

### 3. Create a Branch

Use the **standardized branch naming convention**:

```bash
# Format: type/issue-{number}-brief-description
git checkout -b feat/issue-123-user-authentication
git checkout -b fix/issue-456-memory-leak
git checkout -b docs/issue-789-api-documentation
git checkout -b enhance/issue-321-performance-improvement
```

#### Valid Branch Types

- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `chore/` - Maintenance tasks
- `refactor/` - Code restructuring
- `test/` - Test improvements
- `style/` - Code style changes
- `perf/` - Performance improvements
- `enhance/` - Feature enhancements
- `hotfix/` - Critical fixes

### 4. Develop Your Solution

- Follow ADRI's coding standards and conventions
- Write comprehensive tests for new functionality
- Update documentation as needed
- Ensure framework compatibility requirements are met
- Test against all supported Python versions if applicable

### 5. Create a Pull Request

When your code is ready, create a PR using the provided template:

#### Required PR Elements

- **Issue Link**: Must reference the issue using `Closes #123` or `Related to #123`
- **Description**: Clear explanation of changes made
- **Type of Change**: Check appropriate categories
- **Framework Compatibility**: Specify affected frameworks
- **Testing**: Document all testing performed
- **Documentation**: Confirm updates were made
- **Checklist**: Complete all validation items

### 6. Automated Validation

GitHub Actions will automatically validate your PR:

- ✅ **Issue Link Validation**: Ensures PR references valid, open issues
- ✅ **Branch Naming**: Confirms branch follows naming convention
- ✅ **Template Completion**: Verifies required sections are filled
- ✅ **CI/CD Pipeline**: Runs tests, code quality, and security checks

### 7. Review and Merge

- Address any validation failures
- Respond to reviewer feedback
- Make necessary changes
- Maintain issue reference consistency
- Celebrate when merged! 🎉

## 🔧 Automation Features

### Branch Naming Validation

The workflow automatically validates branch names against the pattern:
```
type/issue-{number}-brief-description
```

**Examples of valid branch names:**
- `feat/issue-123-data-validation-feature`
- `fix/issue-456-pandas-compatibility-bug`
- `docs/issue-789-contributor-guide-update`

### Issue Link Validation

PRs must reference issues using these formats:
- `Closes #123` - For issues that will be resolved
- `Fixes #123` - For bug fixes
- `Resolves #123` - For general resolutions
- `Related to #123` - For related but non-closing references

### Auto-Labeling

Issues and PRs are automatically labeled based on:
- Issue type (feature, enhancement, bug, discussion)
- Framework affected (langchain, crewai, autogen, etc.)
- Change scope (breaking-change, documentation, etc.)

## 📚 Templates Reference

### Issue Templates

| Template | Use Case | Branch Prefix |
|----------|----------|---------------|
| Feature Request | New functionality | `feat/` |
| Enhancement | Improve existing features | `enhance/` or `feat/` |
| Data Quality Bug | Data validation issues | `fix/` |
| Framework Integration Bug | Framework-specific issues | `fix/` |
| Discussion | Architecture/community topics | N/A |

### PR Template Sections

- **Linked Issue** (Required)
- **Description** 
- **Type of Change**
- **Framework Compatibility**
- **Testing Performed**
- **Documentation Updates**
- **Breaking Changes Assessment**
- **Validation Checklist**

## 🎯 Example Workflows

### Adding a New Feature

1. **Create Issue**: Use Feature Request template
   ```
   Title: [Feature] Add support for custom data quality rules
   ```

2. **Create Branch**: 
   ```bash
   git checkout -b feat/issue-123-custom-quality-rules
   ```

3. **Develop**: Implement feature with tests and documentation

4. **Create PR**: Reference issue with `Closes #123`

5. **Validation**: Automated checks pass

6. **Review**: Address feedback and merge

### Fixing a Bug

1. **Create Issue**: Use appropriate bug template
   ```
   Title: [Bug] LangChain decorator fails with async functions
   ```

2. **Create Branch**:
   ```bash
   git checkout -b fix/issue-456-langchain-async-bug
   ```

3. **Fix**: Resolve issue with regression tests

4. **Create PR**: Reference with `Fixes #456`

5. **Merge**: After validation and review

### Starting a Discussion

1. **Create Issue**: Use Discussion template
   ```
   Title: [Discussion] Should we support Python 3.12?
   ```

2. **Community Input**: Gather feedback and consensus

3. **Action Items**: Create specific Feature/Enhancement issues as needed

4. **Implementation**: Follow normal workflow for action items

## 🚫 Common Pitfalls

### ❌ What NOT to Do

- Create PRs without corresponding issues
- Use non-standard branch naming
- Skip template sections or validation checklists
- Forget to link issues in PR descriptions
- Create overly broad issues covering multiple features

### ✅ Best Practices

- Create focused, single-purpose issues
- Use descriptive branch names
- Complete all template sections thoroughly
- Test across supported frameworks when applicable
- Update documentation proactively
- Engage with community feedback

## 🔄 Retroactive Issues

For existing work that predates this workflow:

1. **Create Retroactive Issue**: Document completed work
2. **Link to Existing PR**: Reference in issue description
3. **Update PR**: Add issue reference if still open
4. **Documentation**: Ensure proper traceability

Example retroactive issue:
```
Title: [Feature] Retroactive: ADRI Core Simplification (Completed)
Body: This issue tracks the completed ADRI core simplification work...
Links: Related to PR #789
Status: Closed (completed)
```

## 🛠️ Repository Configuration

### Branch Protection Rules

- Require PR reviews
- Require status checks (including issue validation)
- Require up-to-date branches
- Restrict force pushes

### Auto-Assignment

- PRs automatically assign issue assignees as reviewers
- Framework-specific changes trigger relevant team members
- Documentation changes notify docs maintainers

## 🎮 Getting Started

### For New Contributors

1. **Browse Issues**: Look for `good first issue` or `help wanted` labels
2. **Comment on Issue**: Express interest and ask questions
3. **Follow Workflow**: Use this guide for your first contribution
4. **Ask for Help**: Use Discussions for questions

### For Maintainers

1. **Review Templates**: Ensure they meet project needs
2. **Monitor Automation**: Check GitHub Actions are working
3. **Guide Contributors**: Help community follow workflow
4. **Update Process**: Improve workflow based on feedback

## 📞 Support

- **Questions**: Use [GitHub Discussions Q&A](https://github.com/adri-standard/adri/discussions/categories/q-a)
- **Issues**: Create an issue using Discussion template
- **Documentation**: Check [docs.adri-standard.org](https://docs.adri-standard.org)
- **Community**: Join broader discussions in [Community Discussions](https://github.com/adri-standard/adri/discussions)

## 📈 Success Metrics

This workflow aims to achieve:

- **100% Feature-to-Issue Traceability**: Every change has an issue
- **Improved Community Engagement**: More participation in planning
- **Better Quality**: Structured process reduces bugs
- **Enhanced Transparency**: Clear development visibility
- **Streamlined Contributions**: Easier onboarding for new contributors

---

*This workflow transforms ADRI from having excellent technical governance to having complete community-visible project governance, enabling better collaboration and ensuring all development work has proper tracking and community input.*
