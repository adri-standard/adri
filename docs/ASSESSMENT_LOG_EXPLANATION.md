# ADRI Assessment Log - Complete Explanation

> **📝 NOTE:** This document describes ADRI's open-source JSONL logging system. For complete feature scope, see [OPEN_SOURCE_FEATURES.md](OPEN_SOURCE_FEATURES.md).

**Date:** October 21, 2025
**Format:** JSONL (JSON Lines)
**Purpose:** Comprehensive guide to understanding ADRI's assessment audit logs

---

## Executive Summary

The **Assessment Log** (`.adri/logs/assessments.jsonl`) is ADRI's primary audit trail that records **every single data quality assessment** performed by the system. It provides a complete, immutable record of:

- What data was assessed
- When it was assessed
- What quality score it received
- Whether it passed or failed
- Dimension-specific scores
- Failed validation details
- System context and metadata

Think of it as a **"flight recorder" for AI data quality"** - it captures everything needed to audit, debug, and prove compliance.

---

## Part 1: What Problem Does It Solve?

### The Challenge

When AI systems process data:
- **Accountability:** "Did the AI system validate this data before using it?"
- **Auditability:** "What quality checks were performed on Jan 15th at 3pm?"
- **Traceability:** "Why did this data pass validation when it had errors?"
- **Compliance:** "Can we prove we validated data according to regulations?"

### The Solution

The Assessment Log provides:
1. **Complete Audit Trail:** Every assessment is logged with timestamp
2. **Forensic Details:** Exact scores, validation failures, system info
3. **Decision Record:** What action was taken and why
4. **Performance Metrics:** How assessments performed
5. **Compliance Evidence:** Immutable JSONL record for auditors

---

## Part 2: JSONL Format

### What is JSONL?

JSONL (JSON Lines) is a format where:
- Each line is a complete, valid JSON object
- Lines are separated by newlines (`\n`)
- Easy to stream and process line-by-line
- Human-readable and machine-parseable

### Example Log Entry

Each line in `.adri/logs/assessments.jsonl` is a JSON object like this:

```json
{
  "assessment_id": "20250117_143022_abc123",
  "timestamp": "2025-01-17T14:30:22.123456",
  "standard_name": "customer_service_quality",
  "overall_score": 0.87,
  "passed": true,
  "dimension_scores": {
    "completeness": 0.92,
    "validity": 0.85,
    "consistency": 0.88,
    "plausibility": 0.84,
    "accuracy": 0.86
  },
  "failed_validations": [
    {
      "rule": "email_format",
      "severity": "critical",
      "failed_count": 3,
      "message": "Invalid email format detected"
    }
  ],
  "metadata": {
    "function_name": "process_tickets",
    "data_rows": 1500,
    "data_columns": 12,
    "environment": "production",
    "adri_version": "5.0.1"
  }
}
```

---

## Part 3: Field-by-Field Breakdown

### 🆔 Core Identification Fields

#### `assessment_id` (Required)
- **Format:** `YYYYMMDD_HHMMSS_hexhash`
- **Example:** `"20250117_143022_abc123"`
- **Purpose:** Unique identifier for this assessment
- **Pattern:**
  - Date: `20250117` = January 17, 2025
  - Time: `143022` = 14:30:22 (2:30:22 PM)
  - Hash: `abc123` = unique identifier

**Why It Matters:** Links related log entries and enables correlation

---

#### `timestamp` (Required)
- **Format:** ISO 8601 with microseconds
- **Example:** `"2025-01-17T14:30:22.123456"`
- **Purpose:** Exact moment assessment occurred
- **Precision:** Microseconds for precise ordering

**Why It Matters:** Establishes exact timeline for compliance and debugging

---

### 📊 Assessment Results

#### `standard_name` (Required)
- **Example:** `"customer_service_quality"`
- **Purpose:** Name of the standard used for validation

**Why It Matters:** Shows which quality rules were applied

---

#### `overall_score` (Required)
- **Range:** 0.0 to 1.0 (or 0 to 100 if legacy)
- **Example:** `0.87` (87%)
- **Purpose:** Overall data quality score

**Why It Matters:**
- Main quality metric
- Determines if data passes threshold
- Trends over time show data quality drift

---

#### `passed` (Required)
- **Type:** Boolean
- **Example:** `true`
- **Logic:** `overall_score >= min_score`

**Why It Matters:**
- Clear pass/fail indicator
- Triggers execution decision
- Compliance requirement

---

### 📐 Dimension Scores

#### `dimension_scores` (Required)
- **Type:** Object with dimension names as keys
- **Example:**
```json
{
  "completeness": 0.92,
  "validity": 0.85,
  "consistency": 0.88,
  "plausibility": 0.84,
  "accuracy": 0.86
}
```

**Available Dimensions:**
- `completeness` - No missing/null values
- `validity` - Correct data types and formats
- `consistency` - Cross-field consistency
- `plausibility` - Reasonable value ranges
- `accuracy` - Matches reference data

**Why It Matters:**
- Shows which quality dimensions passed/failed
- Enables dimension-specific analysis
- Helps identify specific data issues

---

### ❌ Failed Validations

#### `failed_validations` (Optional)
- **Type:** Array of validation failure objects
- **Example:**
```json
[
  {
    "rule": "email_format",
    "severity": "critical",
    "failed_count": 3,
    "message": "Invalid email format detected",
    "field": "customer_email"
  },
  {
    "rule": "age_range",
    "severity": "warning",
    "failed_count": 1,
    "message": "Age outside expected range",
    "field": "customer_age"
  }
]
```

**Validation Object Fields:**
- `rule` - Name of the validation rule that failed
- `severity` - "critical" or "warning"
- `failed_count` - Number of records that failed
- `message` - Human-readable description
- `field` - (Optional) Specific field that failed

**Why It Matters:**
- Shows exact validation failures
- Enables targeted data remediation
- Critical for debugging

---

### 💻 Metadata

#### `metadata` (Required)
- **Type:** Object with contextual information
- **Example:**
```json
{
  "function_name": "process_tickets",
  "data_rows": 1500,
  "data_columns": 12,
  "environment": "production",
  "adri_version": "5.0.1",
  "min_score": 0.8,
  "on_failure": "raise"
}
```

**Common Metadata Fields:**
- `function_name` - Function that triggered assessment
- `data_rows` - Number of rows assessed
- `data_columns` - Number of columns assessed
- `environment` - "production", "development", "testing"
- `adri_version` - ADRI version used
- `min_score` - Required threshold
- `on_failure` - Failure handling mode

**Why It Matters:**
- Provides execution context
- Enables filtering and analysis
- Tracks system configuration

---

## Part 4: Reading JSONL Logs

### Python - Basic Reading

```python
import json

# Read all assessments
with open(".adri/logs/assessments.jsonl", "r") as f:
    assessments = [json.loads(line) for line in f]

# Print summary
for assessment in assessments:
    print(f"{assessment['timestamp']}: {assessment['overall_score']:.2%} - {'PASS' if assessment['passed'] else 'FAIL'}")
```

### Python - Filtering

```python
import json

# Read and filter
with open(".adri/logs/assessments.jsonl", "r") as f:
    assessments = [json.loads(line) for line in f]

# Get failed assessments
failed = [a for a in assessments if not a['passed']]

# Get assessments for specific standard
customer_checks = [
    a for a in assessments
    if a['standard_name'] == 'customer_service_quality'
]

# Get recent assessments (last 24 hours)
from datetime import datetime, timedelta
recent = [
    a for a in assessments
    if datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(days=1)
]
```

### Python - Analytics with Pandas

```python
import json
import pandas as pd

# Load into DataFrame
with open(".adri/logs/assessments.jsonl", "r") as f:
    assessments = [json.loads(line) for line in f]

df = pd.DataFrame(assessments)

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Summary statistics
print(df['overall_score'].describe())

# Average score by standard
print(df.groupby('standard_name')['overall_score'].mean())

# Failed assessments
failed_df = df[~df['passed']]
print(f"Failure rate: {len(failed_df) / len(df):.2%}")

# Scores over time
import matplotlib.pyplot as plt
df.set_index('timestamp')['overall_score'].plot()
plt.title('Quality Scores Over Time')
plt.ylabel('Score')
plt.show()
```

### Command Line - jq

```bash
# Count total assessments
jq -s 'length' .adri/logs/assessments.jsonl

# Get average score
jq -s 'map(.overall_score) | add / length' .adri/logs/assessments.jsonl

# Find failed assessments
jq 'select(.passed == false)' .adri/logs/assessments.jsonl

# Get assessments for specific standard
jq 'select(.standard_name == "customer_quality")' .adri/logs/assessments.jsonl

# Extract dimension scores
jq '.dimension_scores' .adri/logs/assessments.jsonl

# Count assessments by standard
jq -s 'group_by(.standard_name) | map({standard: .[0].standard_name, count: length})' .adri/logs/assessments.jsonl
```

---

## Part 5: Real-World Examples

### Example 1: Perfect Score Assessment

```json
{
  "assessment_id": "20250117_143022_abc123",
  "timestamp": "2025-01-17T14:30:22.123456",
  "standard_name": "invoice_data",
  "overall_score": 1.0,
  "passed": true,
  "dimension_scores": {
    "completeness": 1.0,
    "validity": 1.0,
    "consistency": 1.0,
    "plausibility": 1.0,
    "accuracy": 1.0
  },
  "failed_validations": [],
  "metadata": {
    "function_name": "process_invoice",
    "data_rows": 100,
    "data_columns": 8,
    "environment": "production",
    "adri_version": "5.0.1",
    "min_score": 0.8
  }
}
```

**What This Tells Us:**
- ✅ Perfect score (1.0 = 100%)
- ✅ All dimensions perfect
- ✅ No validation failures
- ✅ Passed in production environment
- 📊 100 invoice rows assessed

---

### Example 2: Failed Assessment with Issues

```json
{
  "assessment_id": "20250117_151545_def456",
  "timestamp": "2025-01-17T15:15:45.789012",
  "standard_name": "customer_data",
  "overall_score": 0.72,
  "passed": false,
  "dimension_scores": {
    "completeness": 0.68,
    "validity": 0.75,
    "consistency": 0.85,
    "plausibility": 0.70,
    "accuracy": 0.62
  },
  "failed_validations": [
    {
      "rule": "email_format",
      "severity": "critical",
      "failed_count": 15,
      "message": "Invalid email format",
      "field": "email"
    },
    {
      "rule": "required_fields",
      "severity": "critical",
      "failed_count": 8,
      "message": "Missing required field",
      "field": "phone"
    },
    {
      "rule": "age_range",
      "severity": "warning",
      "failed_count": 3,
      "message": "Age outside plausible range",
      "field": "age"
    }
  ],
  "metadata": {
    "function_name": "import_customers",
    "data_rows": 250,
    "data_columns": 15,
    "environment": "production",
    "adri_version": "5.0.1",
    "min_score": 0.8,
    "on_failure": "raise"
  }
}
```

**What This Tells Us:**
- ❌ Failed (0.72 < 0.8 required)
- ❌ Completeness lowest (0.68) - missing data
- ❌ Accuracy poor (0.62) - invalid values
- 🔴 15 email format violations
- 🔴 8 missing phone numbers
- ⚠️ 3 age range warnings
- 🛑 Function blocked due to "raise" mode

---

### Example 3: Warning Mode Assessment

```json
{
  "assessment_id": "20250117_162030_ghi789",
  "timestamp": "2025-01-17T16:20:30.456789",
  "standard_name": "analytics_data",
  "overall_score": 0.75,
  "passed": false,
  "dimension_scores": {
    "completeness": 0.80,
    "validity": 0.78,
    "consistency": 0.72,
    "plausibility": 0.70,
    "accuracy": 0.75
  },
  "failed_validations": [
    {
      "rule": "date_consistency",
      "severity": "warning",
      "failed_count": 5,
      "message": "Start date after end date",
      "field": "date_range"
    }
  ],
  "metadata": {
    "function_name": "generate_report",
    "data_rows": 1000,
    "data_columns": 20,
    "environment": "development",
    "adri_version": "5.0.1",
    "min_score": 0.8,
    "on_failure": "warn",
    "execution_allowed": true
  }
}
```

**What This Tells Us:**
- ⚠️ Failed (0.75 < 0.8) but execution continued
- ⚠️ "warn" mode - logs warning but doesn't block
- 🔍 Development environment - testing in progress
- 📊 Large dataset - 1000 rows
- ✅ Execution allowed despite failure

---

## Part 6: Common Use Cases

### 1. **Compliance Audit**

**Question:** "Can you prove data validation occurred?"

```python
import json
from datetime import datetime

# Load logs
with open(".adri/logs/assessments.jsonl", "r") as f:
    assessments = [json.loads(line) for line in f]

# Generate audit report
print("ADRI Data Quality Audit Report")
print("="*50)
print(f"Total Assessments: {len(assessments)}")
print(f"Passed: {sum(1 for a in assessments if a['passed'])}")
print(f"Failed: {sum(1 for a in assessments if not a['passed'])}")
print(f"Average Score: {sum(a['overall_score'] for a in assessments) / len(assessments):.2%}")
```

---

### 2. **Debugging Data Issues**

**Question:** "What validation failures occurred today?"

```python
import json
from datetime import datetime, date

with open(".adri/logs/assessments.jsonl", "r") as f:
    today = date.today()
    todays_assessments = [
        json.loads(line) for line in f
        if datetime.fromisoformat(json.loads(line)['timestamp']).date() == today
    ]

# Show failures
for assessment in todays_assessments:
    if not assessment['passed']:
        print(f"\nAssessment: {assessment['assessment_id']}")
        print(f"Standard: {assessment['standard_name']}")
        print(f"Score: {assessment['overall_score']:.2%}")
        print("Failed Validations:")
        for failure in assessment.get('failed_validations', []):
            print(f"  - {failure['rule']}: {failure['message']} ({failure['failed_count']} failures)")
```

---

### 3. **Performance Monitoring**

**Question:** "Is data quality degrading?"

```python
import json
import pandas as pd
import matplotlib.pyplot as plt

# Load and analyze
with open(".adri/logs/assessments.jsonl", "r") as f:
    assessments = [json.loads(line) for line in f]

df = pd.DataFrame(assessments)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['date'] = df['timestamp'].dt.date

# Daily average scores
daily_scores = df.groupby('date')['overall_score'].mean()

# Plot
daily_scores.plot(kind='line', figsize=(12, 6))
plt.title('Data Quality Trend')
plt.ylabel('Average Score')
plt.xlabel('Date')
plt.axhline(y=0.8, color='r', linestyle='--', label='Threshold')
plt.legend()
plt.show()
```

---

### 4. **Standard Effectiveness**

**Question:** "Which standards have the highest failure rate?"

```python
import json
import pandas as pd

with open(".adri/logs/assessments.jsonl", "r") as f:
    assessments = [json.loads(line) for line in f]

df = pd.DataFrame(assessments)

# Calculate failure rates by standard
standard_stats = df.groupby('standard_name').agg({
    'passed': ['count', 'sum', 'mean']
}).round(3)

standard_stats.columns = ['total', 'passed', 'pass_rate']
standard_stats['fail_rate'] = 1 - standard_stats['pass_rate']
standard_stats = standard_stats.sort_values('fail_rate', ascending=False)

print(standard_stats)
```

---

## Part 7: Best Practices

### For Developers

1. **Monitor Regularly:** Check logs daily for failures
2. **Set Alerts:** Alert on failure rate spikes
3. **Archive Properly:** Rotate logs to prevent disk filling
4. **Version Control:** Track log format changes

### For Data Scientists

1. **Validate Training Data:** Check assessments before model training
2. **Track Drift:** Monitor score trends over time
3. **Correlate Metrics:** Link assessments to model performance
4. **Document Thresholds:** Record why specific thresholds are set

### For Compliance Officers

1. **Retention Policy:** Keep logs for required period
2. **Immutable Storage:** Store in append-only systems
3. **Access Control:** Restrict log modification
4. **Regular Audits:** Review logs periodically

---

## Part 8: Log Rotation & Management

### Automatic Rotation

ADRI automatically manages log files:

```
.adri/logs/
├── assessments.jsonl          # Current log
├── assessments.2025-01-16.jsonl  # Previous day
└── assessments.2025-01-15.jsonl  # Older logs
```

### Manual Archiving

```bash
# Archive old logs
cd .adri/logs
gzip assessments.2025-01-*.jsonl

# Upload to S3 for long-term storage
aws s3 cp assessments.2025-01-15.jsonl.gz s3://my-bucket/adri-logs/
```

### Cleanup Script

```python
import os
from datetime import datetime, timedelta
from pathlib import Path

# Delete logs older than 90 days
log_dir = Path(".adri/logs")
cutoff = datetime.now() - timedelta(days=90)

for log_file in log_dir.glob("assessments.*.jsonl"):
    # Extract date from filename
    date_str = log_file.stem.split('.')[-1]
    try:
        file_date = datetime.strptime(date_str, "%Y-%m-%d")
        if file_date < cutoff:
            log_file.unlink()
            print(f"Deleted old log: {log_file}")
    except ValueError:
        continue  # Skip if filename doesn't match pattern
```

---

## Part 9: Integration Examples

### Elasticsearch

```python
import json
from elasticsearch import Elasticsearch

# Connect to Elasticsearch
es = Elasticsearch(['localhost:9200'])

# Index assessments
with open(".adri/logs/assessments.jsonl", "r") as f:
    for line in f:
        assessment = json.loads(line)
        es.index(
            index='adri-assessments',
            id=assessment['assessment_id'],
            document=assessment
        )

# Search for failures
results = es.search(
    index='adri-assessments',
    body={
        'query': {
            'term': {'passed': False}
        }
    }
)
```

### Splunk

```bash
# Forward logs to Splunk
tail -f .adri/logs/assessments.jsonl | \
  splunk add forward-server splunk-server:9997
```

### CloudWatch

```python
import json
import boto3

cloudwatch = boto3.client('logs')

with open(".adri/logs/assessments.jsonl", "r") as f:
    for line in f:
        assessment = json.loads(line)
        cloudwatch.put_log_events(
            logGroupName='/adri/assessments',
            logStreamName='production',
            logEvents=[{
                'timestamp': int(datetime.fromisoformat(assessment['timestamp']).timestamp() * 1000),
                'message': json.dumps(assessment)
            }]
        )
```

---

## Part 10: Summary

The Assessment Log provides:

✅ **Complete Audit Trail** - Every assessment recorded
✅ **Machine-Readable** - JSONL format for easy parsing
✅ **Rich Context** - Dimension scores and validation failures
✅ **Flexible Analysis** - Use Python, jq, or any JSON tool
✅ **Compliance Ready** - Immutable append-only format

**Key Takeaway:** JSONL format makes logs both human-readable and machine-parseable, enabling powerful analytics while maintaining a complete audit trail.

---

## Related Documentation

- **[Open-Source Features](OPEN_SOURCE_FEATURES.md)** - Complete feature reference
- **[API Reference](API_REFERENCE.md)** - Programmatic access
- **[Getting Started](GETTING_STARTED.md)** - Quick start guide
- **[CLI Reference](CLI_REFERENCE.md)** - Command line tools

---

**Document Version:** 2.0
**Last Updated:** October 21, 2025
**Format:** JSONL
**Location:** `.adri/logs/assessments.jsonl`
