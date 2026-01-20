# GitHub Tag Protection Configuration

## Problem Statement

Tags can bypass branch protection rules, allowing commits to be pushed to the repository without going through the PR review process. This creates "orphaned" commits that exist in the repository but aren't on any protected branch.

## Solution: Protected Tag Rules

GitHub provides tag protection rules to prevent unauthorized tag creation and ensure tags can only be created from approved commits.

## Configuration Steps

### 1. Navigate to Repository Settings

1. Go to your repository: https://github.com/adri-standard/adri
2. Click **Settings** tab
3. In the left sidebar, click **Tags** under "Code and automation"

### 2. Add Tag Protection Rule

Click **"Add rule"** or **"New rule"** button

### 3. Configure Version Tag Protection

**Pattern:** `v*.*.*`

This pattern will match all version tags like:
- `v5.0.0`
- `v5.1.0`
- `v5.2.0-beta`

**Options to Enable:**

✅ **Require signed commits**
- Ensures tags are only created by authorized users with GPG keys
- Recommended for production releases

✅ **Restrict tag creation**
- Only repository admins and specific users can create tags matching this pattern
- Prevents accidental tag pushes from contributors

**Who can create tags:**
- Select: **Repository administrators only**
- OR add specific users/teams who manage releases

### 4. Save Rule

Click **"Create"** or **"Save"** to activate the rule

### 5. Additional Recommended Protections

#### Branch Protection for Main

Ensure `main` branch has these protections enabled:

1. **Require pull request reviews before merging**
   - ✅ Required approvals: 1+
   - ✅ Dismiss stale reviews when new commits are pushed
   - ✅ Require review from Code Owners

2. **Require status checks to pass**
   - ✅ Require branches to be up to date
   - ✅ CI/CD checks must pass

3. **Require signed commits**
   - ✅ Ensure commit authenticity

4. **Do not allow bypassing settings**
   - ✅ Include administrators
   - This prevents even admins from pushing directly

5. **Restrict who can push**
   - ✅ Restrict to pull requests only

## Workflow After Configuration

### Creating a Release Tag (Proper Workflow)

1. **Create feature/fix branch:**
   ```bash
   git checkout -b hotfix/issue-description
   ```

2. **Make changes and commit:**
   ```bash
   git add .
   git commit -m "fix: description"
   ```

3. **Push branch:**
   ```bash
   git push origin hotfix/issue-description
   ```

4. **Create PR:**
   ```bash
   gh pr create --base main --head hotfix/issue-description
   ```

5. **Get approval and merge PR**

6. **After merge, create tag from main:**
   ```bash
   git checkout main
   git pull origin main
   git tag v5.1.0
   git push origin v5.1.0
   ```

   With tag protection enabled, this will:
   - ✅ Only work if you're an authorized user
   - ✅ Require GPG signature (if configured)
   - ✅ Create tag on the approved, merged commit

## Benefits

1. **No orphaned commits** - Tags can only be created by authorized users
2. **Audit trail** - All code goes through PR review before tagging
3. **Quality gates** - CI/CD must pass before merge, then tag
4. **Security** - Signed tags ensure authenticity
5. **Consistency** - Enforces release workflow across team

## Verification

Test the configuration:

```bash
# This should FAIL for non-admin users:
git tag v9.9.9
git push origin v9.9.9

# Expected error:
# remote: error: GH013: Repository rule violations found for refs/tags/v9.9.9
# remote: - Tag name pattern: Only repository administrators can create tags matching this pattern
```

## Additional Resources

- [GitHub Tag Protection Documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/configuring-tag-protection-rules)
- [Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Signed Commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification)

## Emergency Fix Procedure (if tag bypass happens)

If an unauthorized tag is created:

1. **Delete the remote tag:**
   ```bash
   git push origin :refs/tags/v5.1.0
   ```

2. **Create proper PR for review**

3. **After PR merge, recreate tag properly:**
   ```bash
   git checkout main
   git pull origin main
   git tag v5.1.0
   git push origin v5.1.0
