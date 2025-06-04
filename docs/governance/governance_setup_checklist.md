# ADRI GitHub Repository Governance Setup Checklist

This checklist ensures proper governance configuration for the ADRI open source project.

## ✅ Repository Settings

### General Settings (Settings → General)
- [ ] **Description**: "ADRI - Agent Data Readiness Index | Open standard enabling 99% AI agent reliability through universal data quality protocols"
- [ ] **Website**: https://adri-standard.github.io/adri/
- [ ] **Topics**: `data-quality`, `ai-agents`, `data-validation`, `python`, `open-standard`, `interoperability`
- [ ] **Features**:
  - [x] Issues
  - [ ] Discussions
  - [ ] Projects
  - [ ] Wiki (optional)
- [ ] **Pull Requests**:
  - [ ] Allow merge commits
  - [ ] Allow squash merging (preferred)
  - [ ] Allow rebase merging
  - [ ] Automatically delete head branches

### Branch Protection (Settings → Branches)
Create protection rule for `main`:
- [ ] Require a pull request before merging
  - [ ] Require approvals: **2**
  - [ ] Dismiss stale pull request approvals
  - [ ] Require review from CODEOWNERS
- [ ] Require status checks to pass
  - [ ] Required checks: `test`, `type-check`
  - [ ] Require branches to be up to date
- [ ] Require conversation resolution
- [ ] Include administrators (initially)
- [ ] Restrict who can push (add maintainers)

### Security (Settings → Security)
- [ ] Enable Dependency graph
- [ ] Enable Dependabot alerts
- [ ] Enable Dependabot security updates
- [ ] Enable Secret scanning
- [ ] Set up Code scanning (CodeQL)

### Secrets (Settings → Secrets and variables → Actions)
- [ ] Add `PYPI_API_TOKEN` secret

### Pages (Settings → Pages)
- [ ] Source: Deploy from branch
- [ ] Branch: `gh-pages`
- [ ] Folder: / (root)

## ✅ GitHub Organization Settings

### Teams (Organization → Teams)
Create these teams as they form:
- [ ] `@adri-standard/maintainers` - Write + maintain permissions
- [ ] `@adri-standard/steering-committee` - Admin access
- [ ] `@adri-standard/documentation` - Triage access
- [ ] `@adri-standard/template-working-group` - Write access to templates
- [ ] `@adri-standard/contributors` - Triage access

### Organization Settings
- [ ] Set organization display name
- [ ] Add organization description
- [ ] Add organization URL
- [ ] Configure member privileges appropriately

## ✅ Community Setup

### Labels (Issues → Labels)
Create these labels for proper categorization:
- [ ] `breaking-change` (red)
- [ ] `major` (red)
- [ ] `minor` (yellow)
- [ ] `patch` (green)
- [ ] `feature` (blue)
- [ ] `enhancement` (blue)
- [ ] `bug` (red)
- [ ] `documentation` (gray)
- [ ] `dependencies` (gray)
- [ ] `good first issue` (green)
- [ ] `help wanted` (green)
- [ ] `skip-changelog` (gray)

### Milestones
- [ ] Create milestone for v1.0.0
- [ ] Create milestone for next minor release

### Projects (optional)
- [ ] Create "ADRI Roadmap" project
- [ ] Create "Community Contributions" project

## ✅ Release Process Setup

### GitHub Release
- [ ] Create v0.4.2 release with notes from CHANGELOG.md
- [ ] Verify PyPI publication triggered successfully

### Release Automation
Files already created:
- ✅ `.github/release-drafter.yml` - Automates release notes
- ✅ `.github/workflows/release-drafter.yml` - Runs the drafter
- ✅ `.github/CODEOWNERS` - Defines review requirements

## ✅ Communication Channels

### External Setup
- [ ] Create Discord server
- [ ] Set up mailing list
- [ ] Create Twitter/X account (@adri_standard)
- [ ] Schedule monthly community calls

### GitHub Discussions Categories
When enabled, create these categories:
- [ ] 📣 Announcements
- [ ] 💡 Ideas & Feature Requests
- [ ] 🙏 Q&A
- [ ] 🎯 Use Cases & Success Stories
- [ ] 📋 Templates & Contributions
- [ ] 🗳️ Governance & Voting

## ✅ Documentation

### Wiki (if enabled)
- [ ] Create "Getting Started" page
- [ ] Create "Governance" page
- [ ] Create "Roadmap" page
- [ ] Create "Meeting Notes" section

### README Badges
Update badges once features are enabled:
- [ ] Add Discord badge
- [ ] Add discussions badge
- [ ] Add contributors badge

## ✅ First Steps After Setup

1. **Announce the Repository**
   - [ ] Post in relevant AI/data quality forums
   - [ ] Share on social media
   - [ ] Reach out to potential early adopters

2. **Bootstrap Governance**
   - [ ] Call for maintainer nominations
   - [ ] Set up first community call
   - [ ] Create initial working groups

3. **Seed Community**
   - [ ] Create "good first issue" tasks
   - [ ] Write welcoming documentation
   - [ ] Respond promptly to first contributors

## Notes

- Start with minimal restrictions and add as needed
- Focus on being welcoming to new contributors
- Document decisions transparently
- Iterate based on community feedback

---
Last updated: January 2025
