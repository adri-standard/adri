# Audit Trail & Logging

## Why Logging Matters

ADRI maintains comprehensive audit trails for every data quality assessment, providing:

- **Compliance & Governance** - Complete lineage for regulatory audits and data governance requirements
- **AI Transparency & Accountability** - Full visibility into AI decisions with prompts, responses, and cryptographic verification
- **Debugging & Troubleshooting** - Detailed failure tracking with remediation suggestions
- **Performance Monitoring** - Token usage, processing times, and system resource metrics
- **Continuous Improvement** - Historical data for refining validation rules and quality standards

Every assessment creates a complete audit trail across 5 interconnected log files, ensuring nothing is lost and everything is traceable.

---

## The 5 Log Files

ADRI generates five log files for each assessment, organized into two categories:

| File Name | Format | Purpose | Records Per Assessment |
|-----------|--------|---------|----------------------|
| `adri_assessment_logs.jsonl` | JSONL | Main audit trail | 1 |
| `adri_dimension_scores.jsonl` | JSONL | Quality dimension breakdown | 5 (one per dimension) |
| `adri_failed_validations.jsonl` | JSONL | Specific validation failures | N (variable) |
| `adri_reasoning_prompts.jsonl` | JSONL | AI prompts sent to LLM | M (variable) |
| `adri_reasoning_responses.jsonl` | JSONL | AI responses from LLM | M (matches prompts) |

All files are linked via `assessment_id`, creating a complete lineage from assessment to dimension scores to specific failures to AI reasoning.

---

## 1. Assessment Logs (adri_assessment_logs.jsonl)

**Purpose:** The primary audit trail containing comprehensive information about each assessment.

### Key Fields (30+ total)

**Identity & Linking:**
- `assessment_id` - Unique identifier linking all log files
- `dataset_name` - Name of the assessed dataset
- `standard_name` - Applied quality standard

**Results:**
- `overall_score` - Aggregate quality score (0-100)
- `passed` - Boolean indicating if assessment passed
- `execution_decision` - Action taken (ALLOW/BLOCK/WARN)

**Quality Dimensions:**
- `validity_score` - Data type and format correctness
- `completeness_score` - Presence of required data
- `consistency_score` - Internal logical consistency
- `freshness_score` - Data recency and timeliness
- `plausibility_score` - Reasonableness of values

**Validation Details:**
- `total_validations_run` - Number of validation checks performed
- `validations_passed` - Number of successful validations
- `validations_failed` - Number of failed validations
- `critical_failures` - Number of critical (blocking) failures
- `validation_failure_rate` - Percentage of failures

**AI Reasoning:**
- `ai_reason` - AI-generated explanation of the assessment
- `ai_recommendation` - AI-suggested actions
- `ai_model_used` - LLM model identifier
- `ai_token_count` - Total tokens consumed
- `ai_processing_time_ms` - AI processing duration

**System Information:**
- `timestamp` - When assessment was performed
- `adri_version` - ADRI framework version
- `python_version` - Python interpreter version
- `system_info` - Operating system details

**Performance Metrics:**
- `assessment_duration_ms` - Total assessment time
- `row_count` - Number of rows assessed
- `column_count` - Number of columns assessed

### Example Record

```json
{
  "assessment_id": "2025-01-15T10:30:45_invoice_data",
  "dataset_name": "invoice_data",
  "standard_name": "invoice_processing_standard",
  "overall_score": 87.5,
  "passed": true,
  "execution_decision": "ALLOW",
  "validity_score": 95.0,
  "completeness_score": 85.0,
  "consistency_score": 90.0,
  "freshness_score": 80.0,
  "plausibility_score": 88.0,
  "total_validations_run": 45,
  "validations_passed": 42,
  "validations_failed": 3,
  "critical_failures": 0,
  "validation_failure_rate": 6.67,
  "ai_reason": "Invoice data quality is acceptable with minor completeness issues in optional fields",
  "ai_recommendation": "Review missing tax_id values for international transactions",
  "ai_model_used": "gpt-4",
  "ai_token_count": 1247,
  "ai_processing_time_ms": 3421,
  "timestamp": "2025-01-15T10:30:45.123456Z",
  "adri_version": "0.6.0",
  "python_version": "3.11.7",
  "assessment_duration_ms": 5678,
  "row_count": 1000,
  "column_count": 12
}
```

---

## 2. Dimension Scores (adri_dimension_scores.jsonl)

**Purpose:** Detailed breakdown of the five quality dimensions for each assessment.

### Structure

Each assessment generates **exactly 5 records** (one per dimension):

**Fields:**
- `assessment_id` - Links to parent assessment
- `dimension_name` - One of: validity, completeness, consistency, freshness, plausibility
- `dimension_score` - Score for this specific dimension (0-100)
- `rules_evaluated` - Number of rules checked for this dimension
- `rules_passed` - Number of rules that passed
- `rules_failed` - Number of rules that failed
- `critical_failures` - Number of critical failures in this dimension
- `timestamp` - When dimension was evaluated

### Example Records

```json
{"assessment_id": "2025-01-15T10:30:45_invoice_data", "dimension_name": "validity", "dimension_score": 95.0, "rules_evaluated": 10, "rules_passed": 10, "rules_failed": 0, "critical_failures": 0}
{"assessment_id": "2025-01-15T10:30:45_invoice_data", "dimension_name": "completeness", "dimension_score": 85.0, "rules_evaluated": 8, "rules_passed": 7, "rules_failed": 1, "critical_failures": 0}
{"assessment_id": "2025-01-15T10:30:45_invoice_data", "dimension_name": "consistency", "dimension_score": 90.0, "rules_evaluated": 12, "rules_passed": 11, "rules_failed": 1, "critical_failures": 0}
{"assessment_id": "2025-01-15T10:30:45_invoice_data", "dimension_name": "freshness", "dimension_score": 80.0, "rules_evaluated": 5, "rules_passed": 4, "rules_failed": 1, "critical_failures": 0}
{"assessment_id": "2025-01-15T10:30:45_invoice_data", "dimension_name": "plausibility", "dimension_score": 88.0, "rules_evaluated": 10, "rules_passed": 10, "rules_failed": 0, "critical_failures": 0}
```

### Use Cases
- Identify which dimensions are weakest
- Track dimension-specific improvements over time
- Diagnose quality issues by category
- Set dimension-specific thresholds

---

## 3. Failed Validations (adri_failed_validations.jsonl)

**Purpose:** Detailed records of specific validation failures with remediation guidance.

### Key Fields

**Identification:**
- `assessment_id` - Links to parent assessment
- `validation_id` - Unique identifier for this failure
- `field_name` - Name of the field that failed validation
- `rule_name` - Name of the validation rule that failed

**Failure Details:**
- `issue_type` - Category of the issue (e.g., "missing_value", "invalid_format", "out_of_range")
- `severity` - CRITICAL or WARNING
- `affected_rows` - List of row indices with this issue
- `affected_row_count` - Number of rows affected
- `failure_percentage` - Percentage of total rows affected

**Remediation:**
- `remediation_suggestion` - AI-generated fix recommendation
- `example_invalid_value` - Sample of the problematic data
- `expected_format` - What the data should look like

**Context:**
- `dimension` - Which quality dimension this relates to
- `timestamp` - When the failure was detected

### Example Records

```json
{
  "assessment_id": "2025-01-15T10:30:45_invoice_data",
  "validation_id": "val_001",
  "field_name": "tax_id",
  "rule_name": "tax_id_required_for_international",
  "issue_type": "missing_value",
  "severity": "WARNING",
  "affected_rows": [45, 67, 89, 123],
  "affected_row_count": 4,
  "failure_percentage": 0.4,
  "remediation_suggestion": "Collect tax_id for international transactions or mark as domestic",
  "example_invalid_value": "null",
  "expected_format": "XX-1234567 (country code + number)",
  "dimension": "completeness",
  "timestamp": "2025-01-15T10:30:45.234567Z"
}
```

### Use Cases
- Prioritize data cleaning efforts
- Generate data quality reports
- Track remediation progress
- Identify systemic data issues

---

## 4. AI Reasoning Prompts (adri_reasoning_prompts.jsonl)

**Purpose:** Complete transparency into AI decision-making by logging every prompt sent to the LLM.

### Key Fields

**Identity:**
- `prompt_id` - Unique identifier for this prompt
- `assessment_id` - Links to parent assessment
- `timestamp` - When prompt was sent

**Model Configuration:**
- `model` - LLM model used (e.g., "gpt-4", "claude-3-opus")
- `temperature` - Randomness setting (0.0 = deterministic, 1.0 = creative)
- `seed` - Random seed for reproducibility
- `max_tokens` - Maximum response length

**Prompt Content:**
- `system_prompt` - System-level instructions to the AI
- `user_prompt` - Specific question or request
- `prompt_hash` - SHA-256 hash for tamper detection

**Context:**
- `prompt_type` - Category (e.g., "assessment_reasoning", "remediation_suggestion")
- `quality_dimension` - Which dimension this relates to (if applicable)

### Example Record

```csv
prompt_id,assessment_id,timestamp,model,temperature,seed,max_tokens,system_prompt,user_prompt,prompt_hash,prompt_type,quality_dimension
prompt_2025-01-15T10:30:45_001,2025-01-15T10:30:45_invoice_data,2025-01-15T10:30:45.345678Z,gpt-4,0.7,42,500,"You are a data quality expert analyzing invoice data.","Explain why this invoice dataset scored 87.5 overall with 3 validation failures. Dataset has 1000 rows, 12 columns.",a3f5d8b9c2e1f4a7d6c8b5e9f2a4d7c1b6e8f3a9d5c2e7f1b4a8d6c9e3f5a2,assessment_reasoning,overall
```

### Use Cases
- **AI Transparency** - See exactly what ADRI asked the AI
- **Reproducibility** - Recreate AI decisions using same prompts
- **Audit Compliance** - Prove AI decisions are based on stated criteria
- **Debugging** - Understand why AI made certain recommendations
- **Prompt Engineering** - Refine prompts based on response quality

### Cryptographic Verification

The `prompt_hash` field contains a SHA-256 hash of the complete prompt (system + user). This enables:
- Tamper detection: Verify prompts haven't been altered
- Deduplication: Identify repeated prompts
- Compliance: Prove exact prompts used in decisions

---

## 5. AI Reasoning Responses (adri_reasoning_responses.jsonl)

**Purpose:** Complete record of AI-generated responses with performance metrics and cryptographic verification.

### Key Fields

**Identity:**
- `response_id` - Unique identifier for this response
- `prompt_id` - Links to the prompt that generated this response
- `assessment_id` - Links to parent assessment
- `timestamp` - When response was received

**Response Content:**
- `response_text` - Complete AI-generated text
- `response_hash` - SHA-256 hash for tamper detection
- `response_status` - SUCCESS or ERROR

**Performance Metrics:**
- `processing_time_ms` - How long AI took to respond
- `token_count` - Number of tokens in response
- `cost_estimate_usd` - Estimated API cost (if available)

**Model Information:**
- `model_used` - Actual model that responded
- `finish_reason` - Why AI stopped (e.g., "stop", "length", "error")

### Example Record

```csv
response_id,prompt_id,assessment_id,timestamp,response_text,response_hash,response_status,processing_time_ms,token_count,cost_estimate_usd,model_used,finish_reason
resp_2025-01-15T10:30:45_001,prompt_2025-01-15T10:30:45_001,2025-01-15T10:30:45_invoice_data,2025-01-15T10:30:45.789012Z,"The invoice dataset demonstrates strong overall quality (87.5/100) with minor issues. The 3 validation failures are non-critical, affecting only 0.4% of records. Primary concern is missing tax_id values for international transactions. Recommendation: Implement tax_id collection for cross-border invoices or clearly flag domestic-only transactions.",b7e9f3a1d5c8e2f6a9d4b7c1e8f5a3d9c6e2f7b4a1d8e5c9f3a6b2e7d4f1c8,SUCCESS,3421,147,0.0088,gpt-4,stop
```

### Use Cases
- **AI Decision Review** - See exactly what AI recommended
- **Performance Analysis** - Track AI response times and costs
- **Quality Assurance** - Verify AI responses meet standards
- **Cost Optimization** - Identify expensive operations
- **Compliance** - Prove AI decisions with cryptographic verification

### Cryptographic Verification

The `response_hash` field enables:
- **Tamper Detection** - Verify responses haven't been altered post-generation
- **Audit Trail** - Prove exact AI output used in decisions
- **Dispute Resolution** - Definitively show what AI actually said

---

## File Relationships

All log files are interconnected through `assessment_id`, creating a complete lineage:

```
adri_assessment_logs.jsonl (PARENT)
├── assessment_id: "2025-01-15T10:30:45_invoice_data"
├── overall_score: 87.5
└── passed: true
    │
    ├─→ adri_dimension_scores.jsonl (CHILDREN)
    │   ├── validity: 95.0
    │   ├── completeness: 85.0
    │   ├── consistency: 90.0
    │   ├── freshness: 80.0
    │   └── plausibility: 88.0
    │
    ├─→ adri_failed_validations.jsonl (CHILDREN)
    │   ├── validation_001: missing tax_id (4 rows)
    │   ├── validation_002: old invoice_date (2 rows)
    │   └── validation_003: inconsistent amounts (1 row)
    │
    └─→ adri_reasoning_prompts.csv (CHILDREN)
        ├── prompt_001: "Explain overall score..."
        │   └─→ adri_reasoning_responses.jsonl
        │       └── response_001: "Dataset demonstrates strong quality..."
        │
        ├── prompt_002: "Suggest remediation for tax_id..."
        │   └─→ adri_reasoning_responses.jsonl
        │       └── response_002: "Implement tax_id collection..."
        │
        └── prompt_003: "Analyze freshness issues..."
            └─→ adri_reasoning_responses.jsonl
                └── response_003: "Invoice dates are outdated..."
```

### Querying Across Files

**Example: Get complete assessment with all failures**
```python
import pandas as pd
import json

# Load assessment
with open('adri_assessment_logs.jsonl') as f:
    assessment = json.loads(f.readline())

# Load dimension scores
dims = pd.read_json('adri_dimension_scores.jsonl', lines=True)
dims = dims[dims['assessment_id'] == assessment['assessment_id']]

# Load failures
failures = pd.read_json('adri_failed_validations.jsonl', lines=True)
failures = failures[failures['assessment_id'] == assessment['assessment_id']]

# Load AI reasoning
prompts = pd.read_csv('adri_reasoning_prompts.csv')
prompts = prompts[prompts['assessment_id'] == assessment['assessment_id']]

responses = pd.read_csv('adri_reasoning_responses.jsonl')
responses = responses[responses['prompt_id'].isin(prompts['prompt_id'])]
```

---

## Common Use Cases

### 1. Compliance Audits

**Scenario:** Prove data quality checks were performed for regulatory audit.

```python
# Get all assessments in date range
import json
from datetime import datetime

assessments = []
with open('adri_assessment_logs.jsonl') as f:
    for line in f:
        record = json.loads(line)
        if '2025-01-01' <= record['timestamp'] <= '2025-01-31':
            assessments.append(record)

# Generate compliance report
for a in assessments:
    print(f"Assessment: {a['assessment_id']}")
    print(f"  Passed: {a['passed']}")
    print(f"  Critical Failures: {a['critical_failures']}")
    print(f"  AI Justification: {a['ai_reason']}")
```

### 2. Debugging Failed Assessments

**Scenario:** Understand why an assessment failed and how to fix it.

```python
# Find failed assessment
with open('adri_assessment_logs.jsonl') as f:
    for line in f:
        record = json.loads(line)
        if record['assessment_id'] == 'problematic_assessment_id':
            print(f"Overall Score: {record['overall_score']}")
            print(f"Execution Decision: {record['execution_decision']}")

# Get specific failures
import pandas as pd
failures = pd.read_json('adri_failed_validations.jsonl', lines=True)
failures = failures[failures['assessment_id'] == 'problematic_assessment_id']

for _, f in failures.iterrows():
    print(f"\nField: {f['field_name']}")
    print(f"Issue: {f['issue_type']}")
    print(f"Severity: {f['severity']}")
    print(f"Affected Rows: {f['affected_row_count']}")
    print(f"Fix: {f['remediation_suggestion']}")
```

### 3. AI Decision Review

**Scenario:** Review what AI recommended and verify its reasoning.

```python
# Load AI reasoning for an assessment
prompts = pd.read_csv('adri_reasoning_prompts.csv')
responses = pd.read_csv('adri_reasoning_responses.jsonl')

assessment_prompts = prompts[prompts['assessment_id'] == 'target_assessment_id']

for _, prompt in assessment_prompts.iterrows():
    response = responses[responses['prompt_id'] == prompt['prompt_id']].iloc[0]

    print(f"\nPrompt Type: {prompt['prompt_type']}")
    print(f"Question: {prompt['user_prompt'][:100]}...")
    print(f"AI Response: {response['response_text'][:200]}...")
    print(f"Processing Time: {response['processing_time_ms']}ms")
    print(f"Tokens Used: {response['token_count']}")
```

### 4. Performance Analysis

**Scenario:** Identify slow assessments and optimize performance.

```python
# Analyze assessment performance
assessments = []
with open('adri_assessment_logs.jsonl') as f:
    for line in f:
        assessments.append(json.loads(line))

df = pd.DataFrame(assessments)

# Find slowest assessments
slow = df.nlargest(10, 'assessment_duration_ms')
print("Slowest Assessments:")
print(slow[['assessment_id', 'assessment_duration_ms', 'row_count', 'ai_processing_time_ms']])

# Find most expensive AI operations
expensive = df.nlargest(10, 'ai_token_count')
print("\nMost Expensive AI Operations:")
print(expensive[['assessment_id', 'ai_token_count', 'ai_model_used']])
```

### 5. Quality Trend Analysis

**Scenario:** Track quality improvements over time.

```python
# Load all assessments for a dataset
assessments = []
with open('adri_assessment_logs.jsonl') as f:
    for line in f:
        record = json.loads(line)
        if record['dataset_name'] == 'invoice_data':
            assessments.append(record)

df = pd.DataFrame(assessments)
df['date'] = pd.to_datetime(df['timestamp']).dt.date

# Plot trend
import matplotlib.pyplot as plt

trend = df.groupby('date')['overall_score'].mean()
plt.plot(trend.index, trend.values)
plt.title('Invoice Data Quality Trend')
plt.xlabel('Date')
plt.ylabel('Average Quality Score')
plt.show()
```

---

## Querying Logs

### Using Python (pandas)

```python
import pandas as pd
import json

# JSONL files (assessment logs, dimension scores, failed validations)
with open('adri_assessment_logs.jsonl') as f:
    assessments = [json.loads(line) for line in f]
df_assessments = pd.DataFrame(assessments)

# CSV files (AI reasoning)
df_prompts = pd.read_csv('adri_reasoning_prompts.csv')
df_responses = pd.read_csv('adri_reasoning_responses.jsonl')

# Filter and analyze
high_quality = df_assessments[df_assessments['overall_score'] >= 90]
failed_assessments = df_assessments[df_assessments['passed'] == False]
```

### Using jq (JSONL command-line tool)

```bash
# Get all failed assessments
jq 'select(.passed == false)' adri_assessment_logs.jsonl

# Get assessments with critical failures
jq 'select(.critical_failures > 0)' adri_assessment_logs.jsonl

# Extract specific fields
jq '{id: .assessment_id, score: .overall_score, passed: .passed}' adri_assessment_logs.jsonl

# Get average score
jq -s 'map(.overall_score) | add / length' adri_assessment_logs.jsonl
```

### Using SQL (DuckDB)

```sql
-- Load JSONL files into DuckDB
CREATE TABLE assessments AS
SELECT * FROM read_json_auto('adri_assessment_logs.jsonl', format='newline_delimited');

CREATE TABLE dimension_scores AS
SELECT * FROM read_json_auto('adri_dimension_scores.jsonl', format='newline_delimited');

CREATE TABLE failures AS
SELECT * FROM read_json_auto('adri_failed_validations.jsonl', format='newline_delimited');

-- Load CSV files
CREATE TABLE prompts AS SELECT * FROM 'adri_reasoning_prompts.csv';
CREATE TABLE responses AS SELECT * FROM 'adri_reasoning_responses.jsonl';

-- Query: Find assessments with low completeness scores
SELECT
    a.assessment_id,
    a.overall_score,
    d.dimension_score as completeness_score,
    a.ai_recommendation
FROM assessments a
JOIN dimension_scores d ON a.assessment_id = d.assessment_id
WHERE d.dimension_name = 'completeness'
  AND d.dimension_score < 80
ORDER BY d.dimension_score ASC;

-- Query: Analyze AI response performance
SELECT
    p.prompt_type,
    COUNT(*) as prompt_count,
    AVG(r.processing_time_ms) as avg_response_time,
    AVG(r.token_count) as avg_tokens,
    SUM(r.cost_estimate_usd) as total_cost
FROM prompts p
JOIN responses r ON p.prompt_id = r.prompt_id
GROUP BY p.prompt_type
ORDER BY total_cost DESC;
```

### Using CSV Tools

```bash
# Count AI prompts by type
csvcut -c prompt_type adri_reasoning_prompts.csv | sort | uniq -c

# Calculate average response time
csvstat adri_reasoning_responses.jsonl -c processing_time_ms

# Filter high-cost responses
csvgrep -c cost_estimate_usd -r "^0\.[1-9]" adri_reasoning_responses.jsonl
```

---

## Configuration

### Log Location

By default, ADRI writes logs to:
```
ADRI/
  prod/
    audit-logs/
      adri_assessment_logs.jsonl
      adri_dimension_scores.jsonl
      adri_failed_validations.jsonl
      adri_reasoning_prompts.csv
      adri_reasoning_responses.jsonl
```

### Customizing Log Paths

Configure log locations in `adri-config.yaml`:

```yaml
logging:
  audit_log_dir: "custom/path/to/logs"
  sync_writes: true
  write_seq_file: true
```

See [Configuration & Logging](config-precedence-and-logging.md) for detailed configuration options.

### Log Format Standards

Each log file has a corresponding YAML standard defining its schema:

**Audit Logs (JSONL):**
- `src/adri/audit_logs/adri_assessment_logs_standard.yaml`
- `src/adri/audit_logs/adri_dimension_scores_standard.yaml`
- `src/adri/audit_logs/adri_failed_validations_standard.yaml`

**AI Reasoning (CSV):**
- `ADRI/standards/adri_reasoning_prompts_standard.yaml`
- `ADRI/standards/adri_reasoning_responses_standard.yaml`

These standards ensure consistent schema across all logs and enable validation of log integrity.

---

## Best Practices

### 1. Regular Log Rotation

JSONL and CSV files grow over time. Implement log rotation:

```python
# Archive logs older than 90 days
import os
import shutil
from datetime import datetime, timedelta

cutoff_date = datetime.now() - timedelta(days=90)

# Read and filter assessments
recent = []
with open('adri_assessment_logs.jsonl') as f:
    for line in f:
        record = json.loads(line)
        if datetime.fromisoformat(record['timestamp']) > cutoff_date:
            recent.append(record)

# Write to new file and archive old
shutil.move('adri_assessment_logs.jsonl', 'archive/adri_assessment_logs_old.jsonl')
with open('adri_assessment_logs.jsonl', 'w') as f:
    for record in recent:
        f.write(json.dumps(record) + '\n')
```

### 2. Hash Verification

Verify AI reasoning logs haven't been tampered with:

```python
import hashlib
import pandas as pd

def verify_prompt_hash(prompt_row):
    """Verify prompt hash matches content"""
    content = prompt_row['system_prompt'] + prompt_row['user_prompt']
    computed_hash = hashlib.sha256(content.encode()).hexdigest()
    return computed_hash == prompt_row['prompt_hash']

prompts = pd.read_csv('adri_reasoning_prompts.csv')
prompts['hash_valid'] = prompts.apply(verify_prompt_hash, axis=1)

if not prompts['hash_valid'].all():
    print("WARNING: Some prompts have invalid hashes!")
    print(prompts[~prompts['hash_valid']])
```

### 3. Backup Critical Logs

AI reasoning logs are especially important for compliance:

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="backups/$DATE"

mkdir -p $BACKUP_DIR
cp ADRI/prod/audit-logs/*.jsonl $BACKUP_DIR/
cp ADRI/prod/audit-logs/*.csv $BACKUP_DIR/

# Compress and upload to S3 (example)
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
aws s3 cp $BACKUP_DIR.tar.gz s3://my-bucket/adri-logs/
```

### 4. Monitor Log Growth

Track log file sizes and record counts:

```python
import os
import json

def get_log_stats(filepath):
    """Get file size and record count"""
    size_mb = os.path.getsize(filepath) / (1024 * 1024)

    with open(filepath) as f:
        if filepath.endswith('.jsonl'):
            count = sum(1 for _ in f)
        else:  # CSV
            count = sum(1 for _ in f) - 1  # Exclude header

    return {'size_mb': size_mb, 'records': count}

logs = [
    'adri_assessment_logs.jsonl',
    'adri_dimension_scores.jsonl',
    'adri_failed_validations.jsonl',
    'adri_reasoning_prompts.csv',
    'adri_reasoning_responses.jsonl'
]

for log in logs:
    stats = get_log_stats(f'ADRI/prod/audit-logs/{log}')
    print(f"{log}: {stats['size_mb']:.2f} MB, {stats['records']:,} records")
```

---

## Integration Examples

### Verodat Integration

Send ADRI audit logs to Verodat for centralized governance:

```python
from verodat_client import VerodatClient

client = VerodatClient(api_key="your_key")

# Upload assessment log to Verodat
with open('adri_assessment_logs.jsonl') as f:
    for line in f:
        assessment = json.loads(line)
        client.upload_record(
            dataset="adri_assessments",
            record=assessment
        )
```

### Database Integration

Load logs into PostgreSQL for advanced analytics:

```sql
-- Create tables
CREATE TABLE assessments (
    assessment_id TEXT PRIMARY KEY,
