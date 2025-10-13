---
sidebar_position: 6
---

# Configuration Precedence and Logging

This guide explains ADRI's configuration precedence rules, environment variable overrides, and the new JSONL-based durable logging system for headless/CI workflows.

> **📝 Note:** This page covers **how** to configure logging. For details on **what** gets logged (log file contents, schemas, and query examples), see [Audit Trail & Logging](audit-and-logging.md).

## Configuration Precedence

ADRI resolves configuration from multiple sources with a clear precedence order (highest to lowest):

### 1. Inline YAML (Highest Precedence)

Set configuration directly via environment variable:

```bash
export ADRI_CONFIG='
adri:
  project_name: my_project
  default_environment: production
  ...
'
```

This overrides all other configuration sources.

### 2. Explicit File Path

Specify configuration file via environment variables:

```bash
export ADRI_CONFIG_PATH=/path/to/adri-config.yaml
# or
export ADRI_CONFIG_FILE=/path/to/adri-config.yaml
```

### 3. Parameter-Provided Path

Pass configuration path directly to functions:

```python
from adri.config.loader import ConfigurationLoader

loader = ConfigurationLoader()
config = loader.get_active_config("/path/to/config.yaml")
```

### 4. Auto-Discovery

ADRI searches for configuration files in standard locations:

- `ADRI/config.yaml` (recommended)
- `adri-config.yaml`
- `.adri.yaml`

### 5. Defaults (Lowest Precedence)

If no configuration is found, ADRI uses sensible defaults.

## Environment Variable Overrides

ADRI supports environment variable overrides for key settings, enabling predictable headless/CI deployments:

### ADRI_ENV - Environment Selection

Override the active environment:

```bash
export ADRI_ENV=production
# Overrides config default_environment
```

This affects:
- Standards directory resolution
- Audit log locations
- Protection settings

### ADRI_STANDARDS_DIR - Standards Location

Override standards directory:

```bash
export ADRI_STANDARDS_DIR=/custom/standards/path
# Overrides all config-based standards paths
```

All standard lookups will use this directory.

### ADRI_LOG_DIR - Audit Log Location

Override audit log directory and enable logging:

```bash
export ADRI_LOG_DIR=/var/log/adri
# Enables audit logging if not configured
```

When set, ADRI automatically:
- Enables audit logging
- Sets sync_writes=True for durability
- Creates the directory if needed

### ADRI_CONFIG_PATH - Configuration File

Override configuration file location:

```bash
export ADRI_CONFIG_PATH=/etc/adri/config.yaml
# Overrides auto-discovery
```

## JSONL-Based Durable Logging

ADRI now uses JSONL (JSON Lines) format for audit logging, providing:

- **Atomic writes**: Each line is a complete, independent record
- **Durability**: fsync after writes ensures data is on disk
- **Monotonic sequencing**: write_seq field for stable ordering
- **Verodat compatibility**: On-demand conversion to Verodat format

### File Structure

ADRI creates five log files for each assessment:

**Audit Logs (JSONL format):**
1. `adri_assessment_logs.jsonl` - Main assessment records with write_seq
2. `adri_dimension_scores.jsonl` - Dimension breakdown per assessment
3. `adri_failed_validations.jsonl` - Validation failures per assessment

**AI Reasoning Logs (JSONL format):**
4. `adri_reasoning_prompts.jsonl` - AI prompts sent to LLM with cryptographic hashes
5. `adri_reasoning_responses.jsonl` - AI responses with performance metrics

> For detailed field descriptions and query examples, see [Audit Trail & Logging](audit-and-logging.md).

### Synchronous Writes (Default)

By default, ADRI uses fsync for durability:

```python
config = {
    "audit": {
        "enabled": True,
        "log_dir": "./logs",
        "sync_writes": True,  # Default: True
    }
}
```

**Benefits for CI/Headless Workflows:**
- Assessment IDs are immediately capturable
- No race conditions when polling logs
- Guaranteed write durability

**Performance Impact:**
- Slightly slower writes (~10-20ms per assessment)
- Can disable via `sync_writes=False` if not critical

### Write Sequence (write_seq)

Each assessment log includes a monotonic `write_seq` field:

```json
{"write_seq": 1, "assessment_id": "adri_...", ...}
{"write_seq": 2, "assessment_id": "adri_...", ...}
{"write_seq": 3, "assessment_id": "adri_...", ...}
```

**Benefits:**
- Stable ordering without timestamp precision issues
- Persists across process restarts
- Ideal for "get new rows since last poll" queries

### Polling for New Assessments

Example: Read assessments since last known sequence:

```python
import json
from pathlib import Path

def get_new_assessments(log_file, last_seq=0):
    """Get assessments with write_seq > last_seq."""
    new_assessments = []

    with open(log_file, 'r') as f:
        for line in f:
            record = json.loads(line)
            if record['write_seq'] > last_seq:
                new_assessments.append(record)

    return new_assessments

# Usage
log_path = Path("./logs/adri_assessment_logs.jsonl")
new = get_new_assessments(log_path, last_seq=42)
```

### Verodat Export

Convert JSONL logs to Verodat JSON format on-demand:

```python
from adri.logging.local import LocalLogger

logger = LocalLogger({
    "enabled": True,
    "log_dir": "./logs",
})

# Export to Verodat format
verodat_data = logger.to_verodat_format("assessment_logs")

# Upload to Verodat
# POST to Verodat API with verodat_data
```

The export produces the required Verodat structure:

```json
{
  "data": [
    {"header": [
      {"name": "write_seq", "type": "numeric"},
      {"name": "assessment_id", "type": "string"},
      ...
    ]},
    {"rows": [
      [1, "adri_20251007_180430_a1b2c3", ...],
      [2, "adri_20251007_180435_d4e5f6", ...]
    ]}
  ]
}
```

## Effective Configuration Diagnostics

ADRI logs effective configuration on first assessment for debugging:

```python
import logging

logging.basicConfig(level=logging.INFO)

# First assessment will log:
# INFO:adri.validator.engine:ADRI Effective Configuration: {
#   "environment": "production",
#   "audit_logging": {
#     "enabled": true,
#     "log_dir": "/var/log/adri",
#     "sync_writes": true
#   },
#   "env_vars": {
#     "ADRI_ENV": "production",
#     "ADRI_LOG_DIR": "/var/log/adri",
#     "ADRI_STANDARDS_DIR": null,
#     "ADRI_CONFIG_PATH": null
#   }
# }
```

## Headless/CI Workflow Example

Complete example for CI/CD pipeline:

```bash
#!/bin/bash
# CI pipeline script

# Set environment overrides
export ADRI_ENV=production
export ADRI_LOG_DIR=/tmp/adri-ci-logs
export ADRI_STANDARDS_DIR=/app/standards

# Run assessment
python -c "
from adri import adri_protected
import pandas as pd

@adri_protected(
    standard='customer_data',
    min_score=85,
)
def process_data(df):
    return df

df = pd.read_csv('data.csv')
result = process_data(df)
"

# Poll logs for assessment ID
ASSESSMENT_ID=$(python -c "
import json
from pathlib import Path

log_file = Path('/tmp/adri-ci-logs/adri_assessment_logs.jsonl')
with open(log_file, 'r') as f:
    lines = f.readlines()
    last = json.loads(lines[-1])
    print(last['assessment_id'])
")

echo "Assessment ID: $ASSESSMENT_ID"

# Export to Verodat
python -c "
from adri.logging.local import LocalLogger

logger = LocalLogger({'enabled': True, 'log_dir': '/tmp/adri-ci-logs'})
verodat_data = logger.to_verodat_format('assessment_logs')

# Upload to Verodat (implement your upload logic)
# requests.post('https://verodat.io/api/v3/...', json=verodat_data)
"
```

## Best Practices

### For Development

```bash
export ADRI_ENV=development
export ADRI_LOG_DIR=./logs
# Sync writes enabled by default for reliability
```

### For Production

```bash
export ADRI_ENV=production
export ADRI_LOG_DIR=/var/log/adri
export ADRI_STANDARDS_DIR=/etc/adri/standards
# Sync writes enabled by default for compliance
```

### For High-Throughput (Optional)

If write performance is critical and you can tolerate potential data loss on crash:

```python
config = {
    "audit": {
        "enabled": True,
        "log_dir": "./logs",
        "sync_writes": False,  # Disable fsync
    }
}
```

⚠️ **Warning**: Only disable sync_writes if you understand the durability trade-offs.

## Summary

| Feature | Benefit |
|---------|---------|
| **JSONL Format** | Atomic writes, no CSV escaping complexity |
| **Sync Writes** | Guaranteed durability, no race conditions |
| **write_seq** | Stable ordering, no timestamp precision issues |
| **Environment Overrides** | Predictable CI/headless deployments |
| **Verodat Export** | On-demand conversion to required format |
| **Effective Config Logging** | Easy debugging and governance |

## Related Documentation

- **[Audit Trail & Logging](audit-and-logging.md)** - Detailed documentation on all 5 log files, schemas, query examples, and use cases
- **[Core Concepts](core-concepts.md)** - Overview of ADRI's core concepts including audit trails
- **[Feature Benefits](feature-benefits.md)** - High-level feature overview
