# ADRI Workflow Orchestration - Compliance-Grade Audit Trails

## Overview

ADRI's workflow orchestration feature provides **compliance-grade audit trails** for multi-step AI workflows. It logs workflow execution metadata and data provenance to CSV files, enabling:

- **Workflow Lineage Tracking**: Link data quality assessments to workflow runs
- **Data Provenance**: Track where data came from (Verodat queries, files, APIs, previous steps)
- **Compliance Auditing**: Full audit trail for regulatory compliance (GDPR, SOC2, etc.)
- **Root Cause Analysis**: Trace data quality issues back to their source
- **Workflow Debugging**: Understand execution flow and data dependencies

## Architecture

### CSV Audit Trail Files

ADRI creates three interlinked CSV files for comprehensive audit trails:

```
adri_workflow_executions.csv
├── execution_id (PK) ──────┐
├── run_id                  │
├── workflow_id             │
├── workflow_version        │
├── step_id                 │
├── step_sequence           │
├── run_at_utc              │
├── data_source_type        │
├── timestamp               │
├── assessment_id (FK) ─────┼──> adri_assessment_logs.csv
└── data_checksum           │       ├── assessment_id (PK)
                             │       ├── execution_id (FK) ◄───┘
adri_data_provenance.csv    │       ├── prompt_id (FK) ──┐
├── execution_id (FK) ◄─────┘       ├── response_id (FK) ─┼─┐
├── source_type                     └── ...                │ │
├── verodat_* fields                                       │ │
├── file_* fields                                          │ │
├── api_* fields            adri_reasoning_prompts.csv     │ │
├── previous_step_* fields  ├── prompt_id (PK) ◄──────────┘ │
└── ...                     ├── execution_id (FK)           │
                            └── ...                          │
                                                             │
                            adri_reasoning_responses.csv     │
                            ├── response_id (PK) ◄───────────┘
                            ├── execution_id (FK)
                            └── ...
```

### Relational Integrity

- **execution_id**: Links workflow → assessment → reasoning
- **assessment_id**: Links workflow executions to quality assessments
- **prompt_id/response_id**: Links assessments to AI reasoning (when enabled)

## Usage

### Basic Workflow Step

```python
from adri import adri_protected
from datetime import datetime
import pandas as pd

@adri_protected(
    data_param="customer_data",
    standard_name="customer_data_standard",
    workflow_context={
        "run_id": "run_20250110_153000_abc123",
        "workflow_id": "customer_onboarding_v2",
        "workflow_version": "2.1.0",
        "step_id": "validate_customer_info",
        "step_sequence": 1,
        "run_at_utc": datetime.utcnow().isoformat() + "Z",
        "data_source_type": "verodat_query",
    },
    data_provenance={
        "source_type": "verodat_query",
        "verodat_query_id": 12345,
        "verodat_account_id": 91,
        "verodat_workspace_id": 161,
        "verodat_run_at_utc": "2025-01-10T14:30:00Z",
        "verodat_query_sql": "SELECT * FROM customers WHERE status='active'",
        "data_retrieved_at_utc": datetime.utcnow().isoformat() + "Z",
        "record_count": 150,
    },
)
def validate_customer_data(customer_data: pd.DataFrame) -> pd.DataFrame:
    """Validate customer data in workflow step 1."""
    return customer_data
```

### Workflow Context Fields

All fields are validated against `ADRI/standards/adri_execution_standard.yaml`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | string | Yes | Unique identifier for this workflow run |
| `workflow_id` | string | Yes | Identifier for the workflow type |
| `workflow_version` | string | Yes | Version of the workflow (semver recommended) |
| `step_id` | string | Yes | Identifier for this step in the workflow |
| `step_sequence` | integer | Yes | Execution order (1, 2, 3, ...) |
| `run_at_utc` | date | Yes | When workflow run started (ISO 8601 UTC) |
| `data_source_type` | string | Yes | Type of data source (verodat_query, file, api, previous_step) |

### Data Provenance by Source Type

All fields are validated against `ADRI/standards/adri_provenance_standard.yaml`:

#### Verodat Query Provenance

```python
data_provenance={
    "source_type": "verodat_query",
    "verodat_query_id": 12345,
    "verodat_account_id": 91,
    "verodat_workspace_id": 161,
    "verodat_run_at_utc": "2025-01-10T14:30:00Z",
    "verodat_query_sql": "SELECT * FROM customers WHERE status='active'",
    "data_retrieved_at_utc": "2025-01-10T15:30:00Z",
    "record_count": 150,
}
```

#### File Provenance

```python
data_provenance={
    "source_type": "file",
    "file_path": "/data/invoices/batch_2025_01.csv",
    "file_size_bytes": 524288,
    "file_hash": "sha256:abc123...",
    "data_retrieved_at_utc": "2025-01-10T15:30:00Z",
    "record_count": 1000,
}
```

#### API Provenance

```python
data_provenance={
    "source_type": "api",
    "api_endpoint": "https://api.market-data.com/v1/quotes",
    "api_http_method": "GET",
    "api_response_hash": "sha256:def456...",
    "data_retrieved_at_utc": "2025-01-10T15:30:00Z",
    "record_count": 500,
    "notes": "Real-time market data from primary feed",
}
```

#### Previous Step Provenance

```python
data_provenance={
    "source_type": "previous_step",
    "previous_step_id": "validate_customer_info",
    "previous_execution_id": "exec_20250110_153045_xyz789",
    "data_retrieved_at_utc": "2025-01-10T15:30:00Z",
    "record_count": 150,
    "notes": "Enriched with demographic data",
}
```

## Configuration

Enable workflow logging in `adri-config.yaml`:

```yaml
adri:
  audit:
    enabled: true
    log_location: "./logs"
    log_prefix: "adri"
    max_log_size_mb: 100
```

Or via environment variables:

```bash
export ADRI_AUDIT_ENABLED=true
export ADRI_AUDIT_LOG_LOCATION=./logs
```

## CSV File Schemas

### adri_workflow_executions.csv

| Column | Type | Description |
|--------|------|-------------|
| `execution_id` | string | Unique execution identifier (PK) |
| `run_id` | string | Workflow run identifier |
| `workflow_id` | string | Workflow type identifier |
| `workflow_version` | string | Workflow version |
| `step_id` | string | Step identifier |
| `step_sequence` | integer | Step execution order |
| `run_at_utc` | datetime | Workflow run start time (UTC) |
| `data_source_type` | string | Data source type |
| `timestamp` | datetime | When execution was logged (UTC) |
| `assessment_id` | string | Associated assessment ID (FK) |
| `data_checksum` | string | Checksum of assessed data |

### adri_data_provenance.csv

| Column | Type | Description |
|--------|------|-------------|
| `execution_id` | string | Links to workflow execution (FK) |
| `source_type` | string | verodat_query, file, api, previous_step |
| `verodat_query_id` | integer | Verodat query ID (if applicable) |
| `verodat_account_id` | integer | Verodat account ID (if applicable) |
| `verodat_workspace_id` | integer | Verodat workspace ID (if applicable) |
| `verodat_run_at_utc` | datetime | When Verodat query ran (if applicable) |
| `verodat_query_sql` | string | SQL query text (if applicable) |
| `file_path` | string | File path (if applicable) |
| `file_size_bytes` | integer | File size (if applicable) |
| `file_hash` | string | File hash (if applicable) |
| `api_endpoint` | string | API endpoint (if applicable) |
| `api_http_method` | string | HTTP method (if applicable) |
| `api_response_hash` | string | Response hash (if applicable) |
| `previous_step_id` | string | Previous step ID (if applicable) |
| `previous_execution_id` | string | Previous execution ID (if applicable) |
| `data_retrieved_at_utc` | datetime | When data was retrieved |
| `record_count` | integer | Number of records |
| `notes` | string | Additional notes |
| `timestamp` | datetime | When provenance was logged (UTC) |

### Enhanced adri_assessment_logs.csv

Added columns for workflow linking:

| Column | Type | Description |
|--------|------|-------------|
| `execution_id` | string | Links to workflow execution (FK) |
| `prompt_id` | string | Links to reasoning prompt (FK, if reasoning enabled) |
| `response_id` | string | Links to reasoning response (FK, if reasoning enabled) |
| ...existing columns... | | |

## Querying Audit Trails

### Example: Find all assessments for a workflow run

```python
import pandas as pd

# Load workflow executions
executions = pd.read_csv("logs/adri_workflow_executions.csv")

# Filter by run_id
run_executions = executions[executions["run_id"] == "run_20250110_153000_abc123"]

# Get assessment IDs
assessment_ids = run_executions["assessment_id"].tolist()

# Load assessments
assessments = pd.read_csv("logs/adri_assessment_logs.csv")
run_assessments = assessments[assessments["assessment_id"].isin(assessment_ids)]

print(f"Found {len(run_assessments)} assessments for this workflow run")
```

### Example: Trace data lineage

```python
# Load provenance
provenance = pd.read_csv("logs/adri_data_provenance.csv")

# Find all Verodat queries used
verodat_sources = provenance[provenance["source_type"] == "verodat_query"]
print(f"Verodat queries used: {len(verodat_sources)}")

# Find data dependencies between steps
step_dependencies = provenance[provenance["source_type"] == "previous_step"]
print(f"Step dependencies: {len(step_dependencies)}")
```

## Best Practices

### 1. Use Consistent run_id Format

```python
from datetime import datetime

# Recommended format: run_YYYYMMDD_HHMMSS_<identifier>
run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_customer_onboarding"
```

### 2. Use Semantic Versioning for Workflows

```python
workflow_version = "2.1.0"  # MAJOR.MINOR.PATCH
```

### 3. Provide Meaningful step_id Values

```python
step_id = "validate_customer_info"  # Not "step1"
```

### 4. Always Log Data Provenance

Even for simple cases:

```python
data_provenance={
    "source_type": "file",
    "file_path": "/path/to/data.csv",
    "data_retrieved_at_utc": datetime.utcnow().isoformat() + "Z",
    "record_count": len(df),
}
```

### 5. Include Checksums and Hashes

For data integrity verification:

```python
import hashlib

file_hash = hashlib.sha256(open("data.csv", "rb").read()).hexdigest()
data_provenance = {
    "source_type": "file",
    "file_hash": f"sha256:{file_hash}",
    # ...
}
```

## Compliance Use Cases

### GDPR Data Lineage

Track where personal data came from and how it was processed:

```python
# Step 1: Data ingestion
@adri_protected(
    data_param="customer_data",
    workflow_context={...},
    data_provenance={
        "source_type": "verodat_query",
        "verodat_query_id": 12345,
        "notes": "Personal data: GDPR Article 6(1)(b) - Contract performance",
    }
)
def ingest_customer_data(customer_data):
    return customer_data
```

### SOC 2 Compliance

Demonstrate data quality controls:

```python
# All workflow steps automatically create audit trail
# proving data was validated against quality standards
@adri_protected(
    data_param="financial_data",
    standard_name="financial_data_standard",
    min_score=95.0,  # High threshold for financial data
    workflow_context={...},
    data_provenance={...}
)
def process_financial_data(financial_data):
    return financial_data
```

### ISO 27001 Data Handling

Track data transformations and access:

```python
@adri_protected(
    data_param="sensitive_data",
    workflow_context={
        "workflow_id": "secure_processing_v1",
        "notes": "ISO 27001 Annex A.8.2 - Information Classification",
    },
    data_provenance={...}
)
def handle_sensitive_data(sensitive_data):
    return sensitive_data
```

## See Also

- [Workflow Orchestration Example](../examples/workflow_orchestration_example.py)
- [ADRI Execution Standard](../ADRI/standards/adri_execution_standard.yaml)
- [ADRI Provenance Standard](../ADRI/standards/adri_provenance_standard.yaml)
- [CSV Audit Logging Documentation](./AUDIT_LOGGING.md)
