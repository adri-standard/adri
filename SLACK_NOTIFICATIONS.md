# ADRI Release System - Slack Notifications

This document explains how to set up and use Slack notifications for the ADRI release system, providing real-time updates about release status, failures, and required actions.

## 🔧 Setup Instructions

### 1. Create a Slack Webhook

1. **Go to your Slack workspace** and navigate to the ADRI channel
2. **Create an Incoming Webhook**:
   - Visit https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - Name: "ADRI Release Notifications"
   - Select your workspace
3. **Configure Incoming Webhooks**:
   - Go to "Incoming Webhooks" in the sidebar
   - Toggle "Activate Incoming Webhooks" to On
   - Click "Add New Webhook to Workspace"
   - Select the ADRI channel
   - Copy the webhook URL (starts with `https://hooks.slack.com/services/...`)

### 2. Add Webhook to GitHub Secrets

1. **Go to your GitHub repository**
2. **Navigate to Settings → Secrets and variables → Actions**
3. **Add a new repository secret**:
   - Name: `SLACK_WEBHOOK_URL`
   - Value: Your webhook URL from step 1

### 3. Test the Setup

Run any workflow to verify notifications are working. If `SLACK_WEBHOOK_URL` is not configured, workflows will skip notifications with a warning message.

## 📢 Notification Types

### 🎉 Success Notifications

**Triggered when**: Release completes successfully
**Appearance**: Green attachment with success details
**Contains**:
- ✅ Release tag and version
- 📦 Direct link to PyPI package
- 🔗 Link to GitHub release
- 🎯 Release type (patch/minor/major, beta/production)

**Example**:
```
🎉 ADRI Release Pre-release.Minor.v0.3.0-beta.1 Successfully Deployed!
Version: 0.3.0-beta.1
Type: Pre-release Minor
PyPI Package: https://pypi.org/project/adri/0.3.0-beta.1/
[View on PyPI] [View Release]
```

### ⚠️ Automated Rollback Notifications

**Triggered when**: Release fails before PyPI publication
**Appearance**: Orange/warning attachment
**Contains**:
- 🚨 Failed stage identification
- ✅ Confirmation of automated rollback
- 🔧 Next steps for retry
- 🔗 Link to failed workflow

**Example**:
```
⚠️ Release Failed - Rollback Completed: ADRI Release candidate-beta-minor-v0.3.0
Failed Stage: test
Status: ✅ Automated rollback completed
Error Message: Test suite failed
Next Steps: Fix issues and retry release
[View Workflow]
```

### 🚨 Critical Failure Notifications

**Triggered when**: Release fails after PyPI publication
**Appearance**: Red/danger attachment with urgent styling
**Contains**:
- 🚨 Critical failure alert
- ⚠️ Manual intervention required
- 📋 Specific actions needed
- 🔗 Links to workflow and PyPI package

**Example**:
```
🚨 URGENT: Release Failed - Manual Action Required: ADRI Release Release.Minor.v0.3.0
Failed Stage: pypi-smoke
Status: 🚨 Manual intervention required
Error Message: Production PyPI smoke tests failed
Next Steps: Check PyPI status and manual cleanup
[View Workflow]
```

### 🔄 Rollback Completion Notifications

**Triggered when**: Manual or automated rollback completes
**Appearance**: Orange/warning attachment for automated, red for manual yanking
**Contains**:
- 🔄 Rollback type and reason
- ✅ Actions completed
- 📋 Next steps for recovery
- 🔗 Links to relevant workflows

**Example**:
```
🚨 URGENT ACTION REQUIRED: ADRI Release Rollback
Tag: Pre-release.Minor.v0.3.0-beta.1
Type: yank
Reason: Critical security vulnerability
Action Required: Manual PyPI package yanking required
[View Workflow]
```

## 🎯 Notification Scenarios

### Scenario 1: Test Failure (Automated Recovery)
1. **Release starts** → No notification (normal progress)
2. **Tests fail** → ⚠️ Automated rollback notification
3. **Developer fixes** → No notification
4. **Retry succeeds** → 🎉 Success notification

### Scenario 2: PyPI Smoke Test Failure (Manual Intervention)
1. **Release progresses** → No notification
2. **PyPI published** → No notification (success so far)
3. **Smoke tests fail** → 🚨 Critical failure notification
4. **Manual investigation** → Team checks PyPI package status
5. **Manual rollback** → 🔄 Rollback completion notification

### Scenario 3: Successful Release
1. **Release starts** → No notification
2. **All stages pass** → 🎉 Success notification with PyPI links

### Scenario 4: Manual Rollback
1. **Issue discovered** → Team triggers manual rollback
2. **Rollback executes** → 🔄 Rollback completion notification
3. **If yanking required** → 🚨 Urgent action notification

## 🔔 Notification Content Details

### Rich Attachments
All notifications use Slack's rich attachment format with:
- **Color coding**: Green (success), Orange (warning), Red (critical)
- **Structured fields**: Key information in easy-to-scan format
- **Action buttons**: Direct links to relevant resources
- **Timestamps**: Automatic timestamping for tracking

### Key Information Included
- **Release identification**: Tag name, version, type
- **Status information**: Current state, actions taken
- **Error details**: Specific failure messages when applicable
- **Next steps**: Clear guidance on required actions
- **Quick access**: Direct links to workflows, PyPI, GitHub releases

## 🛠️ Troubleshooting

### No Notifications Received
1. **Check webhook URL**: Verify `SLACK_WEBHOOK_URL` secret is set correctly
2. **Test webhook**: Use curl to test the webhook directly
3. **Check channel**: Ensure the webhook is configured for the correct channel
4. **Verify permissions**: Ensure the Slack app has permission to post

### Partial Notifications
1. **Check workflow logs**: Look for "Failed to send Slack notification" messages
2. **Verify JSON format**: Malformed JSON will cause failures
3. **Check rate limits**: Slack has rate limits for webhook calls

### Testing Webhooks
```bash
# Test your webhook URL directly
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test notification from ADRI release system"}' \
  YOUR_WEBHOOK_URL
```

## 📋 Configuration Examples

### Basic Setup
```yaml
# In GitHub Actions workflow
- name: Send notification
  run: |
    if [[ -n "${{ secrets.SLACK_WEBHOOK_URL }}" ]]; then
      curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"Release completed"}' \
        "${{ secrets.SLACK_WEBHOOK_URL }}"
    fi
```

### Rich Attachment Example
```json
{
  "attachments": [{
    "color": "good",
    "title": "🎉 ADRI Release Successfully Deployed!",
    "fields": [
      {"title": "Version", "value": "0.3.0", "short": true},
      {"title": "Type", "value": "Minor Release", "short": true}
    ],
    "actions": [{
      "type": "button",
      "text": "View on PyPI",
      "url": "https://pypi.org/project/adri/0.3.0/"
    }]
  }]
}
```

## 🔐 Security Considerations

### Webhook URL Protection
- **Never commit webhook URLs** to version control
- **Use GitHub Secrets** for secure storage
- **Rotate webhooks** periodically for security
- **Limit webhook scope** to specific channels

### Information Disclosure
- **No sensitive data** in notifications (passwords, tokens, etc.)
- **Public links only** (PyPI, GitHub releases are public anyway)
- **Error messages** are sanitized and safe to share

## 📈 Monitoring and Analytics

### Notification Tracking
- All notifications include timestamps
- Workflow run IDs for traceability
- Clear correlation between notifications and releases

### Success Metrics
- Track notification delivery success/failure
- Monitor team response times to critical notifications
- Measure rollback effectiveness through notification patterns

## 🔄 Maintenance

### Regular Tasks
1. **Test notifications** monthly to ensure they're working
2. **Review webhook permissions** quarterly
3. **Update documentation** when notification formats change
4. **Monitor Slack app health** in your workspace

### Webhook Rotation
```bash
# When rotating webhooks:
# 1. Create new webhook in Slack
# 2. Update GitHub secret
# 3. Test with a manual workflow run
# 4. Delete old webhook in Slack
```

This notification system ensures the ADRI team stays informed about all release activities and can respond quickly to any issues that require manual intervention.
