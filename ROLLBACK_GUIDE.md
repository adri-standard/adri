# ADRI Release Rollback Guide

This guide provides comprehensive instructions for rolling back ADRI releases using the automated rollback system.

## Overview

The ADRI release system includes comprehensive rollback capabilities to handle failures at any stage of the release process. The rollback system can automatically clean up failed releases or provide manual intervention guidance for complex scenarios.

## Rollback Types

### 1. Clean Rollback (Pre-PyPI)
- **When**: Failures before PyPI publication (test, build, TestPyPI stages)
- **Actions**: Complete cleanup including Git tags, GitHub releases, and draft releases
- **Automation**: Fully automated
- **Recovery**: Can retry with same version number

### 2. Partial Rollback (TestPyPI Published)
- **When**: Failures after TestPyPI but before PyPI publication
- **Actions**: Cleanup Git tags and GitHub releases, TestPyPI package remains
- **Automation**: Fully automated
- **Recovery**: Can retry with same version number

### 3. Yank Rollback (PyPI Published)
- **When**: Failures after PyPI publication
- **Actions**: Requires yanking the PyPI package (irreversible)
- **Automation**: Manual intervention required
- **Recovery**: Must increment version number for new release

## Automated Rollback

### Workflow Integration

The release workflow automatically triggers rollback for pre-PyPI failures:

```yaml
- name: Trigger automated rollback (pre-PyPI failures)
  if: steps.failure-stage.outputs.can_rollback == 'true'
  uses: ./.github/workflows/rollback-release.yml
  with:
    tag_name: ${{ needs.validate-version.outputs.tag_name }}
    rollback_reason: "Automated rollback due to failure"
    failure_stage: ${{ steps.failure-stage.outputs.stage }}
    force_rollback: false
```

### Automatic Triggers

Rollback is automatically triggered for failures in:
- ✅ Test suite execution
- ✅ Package building
- ✅ TestPyPI publication
- ✅ TestPyPI smoke tests
- ⚠️ PyPI publication (manual intervention required)
- ⚠️ PyPI smoke tests (manual intervention required)

## Manual Rollback

### Using the Rollback Workflow

1. **Navigate to Actions**: Go to GitHub Actions → Rollback Release
2. **Run Workflow**: Click "Run workflow"
3. **Provide Parameters**:
   - **Tag Name**: The release tag to rollback (e.g., `Pre-release.Minor.v0.3.0-beta.1`)
   - **Rollback Reason**: Descriptive reason for the rollback
   - **Force Rollback**: Check if PyPI package needs yanking

### Using the Rollback Script

```bash
# Clean rollback (pre-PyPI)
python scripts/rollback_release.py candidate-beta-minor-v0.3.0 \
  --reason "Test failures detected"

# Force rollback with yanking (post-PyPI)
python scripts/rollback_release.py Pre-release.Minor.v0.3.0-beta.1 \
  --force --reason "Critical security vulnerability"

# Dry run to see what would be done
python scripts/rollback_release.py candidate-minor-v0.3.0 \
  --dry-run
```

## Rollback Scenarios

### Scenario 1: Test Failures

**Problem**: Unit tests fail during release workflow

**Automatic Response**:
1. ✅ Automated rollback triggered
2. ✅ Git tags cleaned up
3. ✅ Draft releases removed
4. ✅ Clean state restored

**Next Steps**:
1. Fix failing tests
2. Push fixes to repository
3. Run prepare-releases workflow
4. Retry release with same version

### Scenario 2: Build Failures

**Problem**: Package build fails

**Automatic Response**:
1. ✅ Automated rollback triggered
2. ✅ Git tags cleaned up
3. ✅ Draft releases removed
4. ✅ Clean state restored

**Next Steps**:
1. Fix build configuration
2. Test build locally
3. Push fixes to repository
4. Retry release with same version

### Scenario 3: TestPyPI Failures

**Problem**: TestPyPI publication or smoke tests fail

**Automatic Response**:
1. ✅ Automated rollback triggered
2. ✅ Git tags cleaned up
3. ✅ Draft releases removed
4. ➖ TestPyPI package remains (harmless)

**Next Steps**:
1. Fix identified issues
2. Test fixes thoroughly
3. Retry release with same version

### Scenario 4: PyPI Publication Failures

**Problem**: PyPI publication fails

**Manual Intervention Required**:
1. ⚠️ Check if package was actually published
2. ⚠️ If published and broken, consider yanking
3. ⚠️ Manual rollback workflow execution needed

**Steps**:
1. Check PyPI: https://pypi.org/project/adri/VERSION/
2. If published and broken:
   ```bash
   python scripts/rollback_release.py TAG_NAME --force --reason "REASON"
   ```
3. If not published, safe to retry

### Scenario 5: PyPI Smoke Test Failures

**Problem**: PyPI smoke tests fail after successful publication

**Critical Situation**:
- Package is live on PyPI
- Users can install broken version
- Immediate action required

**Steps**:
1. **Immediate**: Consider yanking the package
   ```bash
   twine yank adri VERSION --reason "Smoke tests failed"
   ```
2. **Communicate**: Notify users about the issue
3. **Fix**: Prepare hotfix release
4. **Release**: Deploy fixed version with incremented version number

## Recovery Procedures

### After Clean Rollback

1. **Identify Root Cause**: Review workflow logs
2. **Implement Fixes**: Address the identified issues
3. **Test Locally**: Verify fixes work in development
4. **Retry Release**: Use same version number
   - Run prepare-releases workflow
   - Publish the generated draft release

### After Partial Rollback

1. **Fix Issues**: Address the problems that caused failure
2. **Test Thoroughly**: Ensure fixes are comprehensive
3. **Retry Release**: Same version number can be reused
4. **Monitor**: Watch TestPyPI and PyPI stages carefully

### After Yank Rollback

1. **Communicate**: Inform users about yanked version
2. **Hotfix Development**: Create fix for the critical issue
3. **Version Increment**: Bump version number (yanked versions can't be reused)
4. **Expedited Release**: Fast-track the hotfix release
5. **Documentation**: Update changelog with incident details

## Best Practices

### Prevention

1. **Comprehensive Testing**: Run full test suite locally before release
2. **Staging Environment**: Test in environment similar to production
3. **Gradual Rollout**: Use beta releases for major changes
4. **Monitoring**: Watch release workflows closely

### During Rollback

1. **Document Everything**: Record what happened and why
2. **Communicate Early**: Notify team about rollback immediately
3. **Preserve Evidence**: Keep logs and error messages
4. **Follow Process**: Use established rollback procedures

### After Rollback

1. **Post-Mortem**: Analyze what went wrong
2. **Process Improvement**: Update procedures to prevent recurrence
3. **Testing Enhancement**: Add tests to catch similar issues
4. **Documentation Update**: Improve release documentation

## Troubleshooting

### Common Issues

#### "Release not found" Error
```bash
# Check if release exists
gh release list

# Check if tag exists
git tag -l | grep TAG_NAME

# Manual cleanup if needed
gh release delete TAG_NAME --yes
git tag -d TAG_NAME
git push origin :refs/tags/TAG_NAME
```

#### "Permission denied" for PyPI Operations
```bash
# Check PyPI token permissions
twine check dist/*

# Verify token has yank permissions (for force rollback)
# Contact PyPI maintainers if needed
```

#### Workflow Permissions Issues
```bash
# Check GitHub token permissions
# Ensure GITHUB_TOKEN has:
# - contents: write
# - actions: write
```

### Manual Cleanup Commands

If automated rollback fails, use these manual commands:

```bash
# Delete GitHub release
gh release delete TAG_NAME --yes

# Delete Git tags
git tag -d TAG_NAME
git push origin :refs/tags/TAG_NAME

# Yank PyPI package (if needed)
twine yank adri VERSION --reason "REASON"

# List and clean candidate releases
gh release list | grep candidate
gh release delete candidate-TAG --yes
```

## Monitoring and Alerts

### Workflow Monitoring

- Monitor GitHub Actions for release workflow status
- Set up notifications for workflow failures
- Review rollback summaries in workflow logs

### PyPI Monitoring

- Check PyPI package status after releases
- Monitor download statistics for anomalies
- Set up alerts for package yanking events

### Communication Channels

- Slack/Teams notifications for rollback events
- Email alerts for critical rollback scenarios
- Status page updates for user-facing issues

## Emergency Contacts

### Internal Team
- Release Manager: [Contact Info]
- DevOps Lead: [Contact Info]
- Security Team: [Contact Info]

### External Services
- PyPI Support: https://pypi.org/help/
- GitHub Support: https://support.github.com/

## Related Documentation

- [Release Process Guide](RELEASE_PROCESS.md)
- [Version Management](VERSION.md)
- [Workflow Documentation](.github/workflows/README.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

---

**Last Updated**: January 2025
**Version**: 1.0
**Maintainer**: ADRI Release Team
