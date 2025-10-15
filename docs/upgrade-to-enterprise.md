# Upgrading from ADRI Open-Source to Enterprise

This guide helps you migrate from the open-source `adri` package to the enterprise `adri-enterprise` package.

## Overview

**ADRI v5.0.0** is split into two packages:
- **`adri`** (open-source) - Core data quality features
- **`adri-enterprise`** (private) - All open-source features PLUS advanced logging, workflow automation, and analytics

Both packages share the same version number (5.0.0) for clear upgrade paths.

## Why Upgrade to Enterprise?

Upgrade to `adri-enterprise` if you need:

- ✅ **ReasoningLogger** - Track AI prompts and responses for debugging
- ✅ **WorkflowLogger** - Capture workflow execution and data provenance  
- ✅ **Analytics Dashboards** - Visualize quality metrics over time
- ✅ **Workflow Automation** - Approval workflows and orchestration
- ✅ **Advanced Verodat Integration** - Batch processing, retry logic, authentication
- ✅ **Enterprise Support** - Priority support from Verodat team

## Feature Comparison

| Capability | Open-Source | Enterprise |
|------------|-------------|------------|
| **Core Protection** | | |
| @adri_protected decorator | ✅ | ✅ |
| 3 protection modes (FailFast, Selective, WarnOnly) | ✅ | ✅ |
| 5-dimension quality assessment | ✅ | ✅ |
| Automatic standard generation | ✅ | ✅ |
| **CLI Tools** | | |
| 8 CLI commands | ✅ | ✅ |
| Standard generation and validation | ✅ | ✅ |
| Assessment execution | ✅ | ✅ |
| **Logging & Audit** | | |
| LocalLogger (3-file JSONL) | ✅ | ✅ |
| ADRILogReader (programmatic access) | ✅ | ✅ |
| ReasoningLogger (AI prompts/responses) | ❌ | ✅ |
| WorkflowLogger (execution/provenance) | ❌ | ✅ |
| **Integration** | | |
| Basic Verodat bridge (send_to_verodat) | ✅ | ✅ |
| Advanced Verodat (batch, retry, auth) | ❌ | ✅ |
| **Advanced Features** | | |
| Analytics dashboards | ❌ | ✅ |
| Workflow automation | ❌ | ✅ |
| Orchestration | ❌ | ✅ |
| **Support** | | |
| Community (GitHub) | ✅ | ✅ |
| Enterprise SLA | ❌ | ✅ |

## Installation

### Prerequisites

1. **Access to Private Repository**
   - GitHub account with access to https://github.com/Verodat/adri-enterprise
   - SSH key or personal access token configured
   - Contact adri@verodat.com for access

2. **Python Environment**
   - Python 3.10, 3.11, 3.12, or 3.13
   - Virtual environment recommended

### Step 1: Uninstall Open-Source Version

```bash
pip uninstall adri
```

### Step 2: Install Enterprise Version

**Via SSH (recommended):**
```bash
pip install git+ssh://git@github.com/Verodat/adri-enterprise.git
```

**Via HTTPS with token:**
```bash
pip install git+https://<TOKEN>@github.com/Verodat/adri-enterprise.git
```

**Specific version:**
```bash
pip install git+ssh://git@github.com/Verodat/adri-enterprise.git@v5.0.0
```

### Step 3: Verify Installation

```bash
python -c "from adri_enterprise import adri_protected, ReasoningLogger, WorkflowLogger; print('✅ Enterprise installation successful')"
```

## Code Migration

Most code will work without changes! The enterprise package includes all open-source features.

### No Changes Needed

If you're using core features, your code works as-is:

```python
# These imports work in both versions
from adri import adri_protected, LocalLogger, DataQualityAssessor

@adri_protected(standard="my_standard")
def my_function(data):
    return process(data)
```

### Enterprise-Only Features

To use enterprise features, update your imports:

```python
# Open-Source (v5.0.0)
from adri.logging import LocalLogger, send_to_verodat

# Enterprise (v5.0.0)  
from adri_enterprise.logging import (
    LocalLogger,           # Same as open-source
    ReasoningLogger,       # Enterprise-only
    WorkflowLogger,        # Enterprise-only
    EnterpriseLogger       # Full Verodat integration
)

# Enable AI reasoning logging
from adri_enterprise import adri_protected

@adri_protected(
    standard="my_standard",
    reasoning_mode=True,      # Enterprise-only
    store_prompt=True,        # Enterprise-only
    store_response=True       # Enterprise-only
)
def ai_agent_function(data):
    return llm.generate(data)
```

### Breaking Changes from v4.4.0

If you were using enterprise features in v4.4.0 open-source, update your code:

**1. EnterpriseLogger → Use enterprise package**

```python
# Old (v4.4.0 open-source)
from adri.logging import EnterpriseLogger
logger = EnterpriseLogger(config)
logger.upload(records, "assessment_logs")

# New (v5.0.0 open-source) - Simplified
from adri.logging import send_to_verodat
send_to_verodat(assessment_data, api_url, api_key)

# New (v5.0.0 enterprise) - Full features
from adri_enterprise.logging import EnterpriseLogger
logger = EnterpriseLogger(config)
logger.upload(records, "assessment_logs")
```

**2. ReasoningLogger → Use enterprise package**

```python
# Old (v4.4.0 open-source)
from adri.logging import ReasoningLogger
logger = ReasoningLogger(config)

# New (v5.0.0 enterprise)
from adri_enterprise.logging import ReasoningLogger
logger = ReasoningLogger(config)
```

**3. WorkflowLogger → Use enterprise package**

```python
# Old (v4.4.0 open-source)
from adri.logging import WorkflowLogger
logger = WorkflowLogger(config)

# New (v5.0.0 enterprise)
from adri_enterprise.logging import WorkflowLogger
logger = WorkflowLogger(config)
```

## Configuration Updates

### Open-Source Configuration (v5.0.0)

```yaml
adri:
  version: "5.0.0"
  default_environment: production
  environments:
    production:
      paths:
        standards: ./ADRI/prod/standards
        audit_logs: ./ADRI/prod/audit-logs
      audit:
        enabled: true
        log_dir: ./ADRI/prod/audit-logs
        sync_writes: true
      protection:
        default_min_score: 80
        default_failure_mode: raise
```

### Enterprise Configuration (v5.0.0)

```yaml
adri:
  version: "5.0.0"
  default_environment: production
  environments:
    production:
      paths:
        standards: ./ADRI/prod/standards
        audit_logs: ./ADRI/prod/audit-logs
        reasoning_logs: ./ADRI/prod/reasoning-logs
        workflow_logs: ./ADRI/prod/workflow-logs
      audit:
        enabled: true
        log_dir: ./ADRI/prod/audit-logs
        sync_writes: true
      reasoning:
        enabled: true
        log_dir: ./ADRI/prod/reasoning-logs
        store_prompts: true
        store_responses: true
      workflow:
        enabled: true
        log_dir: ./ADRI/prod/workflow-logs
      verodat:
        enabled: true
        api_key: ${VERODAT_API_KEY}
        workspace_id: your_workspace_id
        batch_settings:
          batch_size: 100
          flush_interval_seconds: 60
      protection:
        default_min_score: 80
        default_failure_mode: raise
```

## Testing Your Migration

### 1. Verify Core Features

```bash
# Test decorator
python -c "from adri_enterprise import adri_protected; print('✅ Decorator works')"

# Test CLI
adri --version
adri list-standards

# Test logging
python -c "from adri_enterprise.logging import LocalLogger; print('✅ Logging works')"
```

### 2. Verify Enterprise Features

```python
from adri_enterprise.logging import ReasoningLogger, WorkflowLogger, EnterpriseLogger

# Test reasoning logger
reasoning_logger = ReasoningLogger({"enabled": True, "log_dir": "./logs"})
print("✅ ReasoningLogger available")

# Test workflow logger  
workflow_logger = WorkflowLogger({"enabled": True, "log_dir": "./logs"})
print("✅ WorkflowLogger available")

# Test enterprise logger
enterprise_logger = EnterpriseLogger({"enabled": True, "api_key": "test"})
print("✅ EnterpriseLogger available")
```

### 3. Run Your Test Suite

```bash
pytest tests/
```

## Common Migration Issues

### Issue: Import Errors

**Problem:** `ImportError: cannot import name 'ReasoningLogger'`

**Solution:** Check you're importing from `adri_enterprise`, not `adri`

```python
# Wrong
from adri.logging import ReasoningLogger

# Correct
from adri_enterprise.logging import ReasoningLogger
```

### Issue: Package Not Found

**Problem:** `pip install adri-enterprise` fails

**Solution:** Use Git installation method:

```bash
pip install git+ssh://git@github.com/Verodat/adri-enterprise.git
```

### Issue: Authentication Failed

**Problem:** SSH authentication fails when installing

**Solution:** Use HTTPS with personal access token:

```bash
pip install git+https://<YOUR_TOKEN>@github.com/Verodat/adri-enterprise.git
```

### Issue: Both Packages Installed

**Problem:** Both `adri` and `adri-enterprise` are installed

**Solution:** Uninstall open-source first:

```bash
pip uninstall adri
pip install git+ssh://git@github.com/Verodat/adri-enterprise.git
```

## Rollback to Open-Source

If you need to rollback to open-source:

```bash
# Uninstall enterprise
pip uninstall adri-enterprise

# Install open-source
pip install adri==5.0.0

# Update imports back to open-source
# Remove enterprise-only features from code
```

## Getting Help

### Community Support (Open-Source)
- GitHub Issues: https://github.com/adri-standard/adri/issues
- GitHub Discussions: https://github.com/adri-standard/adri/discussions

### Enterprise Support
- Email: adri@verodat.com
- Private repository issues: https://github.com/Verodat/adri-enterprise/issues
- SLA-based support for enterprise customers

## Version Compatibility

Both open-source and enterprise use the same version numbers:

| Version | Open-Source | Enterprise | Notes |
|---------|-------------|------------|-------|
| 5.0.0   | ✅ PyPI     | ✅ Private | Current - Split version |
| 4.4.0   | ✅ PyPI     | ❌         | Last unified version |
| 4.3.0   | ✅ PyPI     | ❌         | Unified version |

**Recommendation:** Always keep enterprise and open-source at the same version number.

## Next Steps

After upgrading to enterprise:

1. **Enable Advanced Logging**
   - Configure ReasoningLogger for AI debugging
   - Set up WorkflowLogger for provenance tracking

2. **Configure Verodat Integration**
   - Set up API credentials
   - Configure batch settings
   - Test data uploads

3. **Explore Analytics**
   - Set up quality dashboards
   - Configure metric tracking
   - Generate trend reports

4. **Implement Workflows**
   - Define approval workflows
   - Configure orchestration
   - Set up automation rules

See [ADRI Enterprise Documentation](https://github.com/Verodat/adri-enterprise/blob/main/README.md) for detailed guides.

---

**Last Updated:** October 15, 2025  
**Version:** 5.0.0  
**Maintained By:** Verodat
