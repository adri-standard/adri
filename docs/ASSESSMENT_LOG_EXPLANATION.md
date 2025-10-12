# ADRI Assessment Log - Complete Explanation

> **📝 IMPORTANT:** This document provides detailed field-level documentation for the assessment logs. For the most current and comprehensive logging documentation covering all 5 log files (including AI reasoning logs), see:
>
> **[Audit Trail & Logging](docs/users/audit-and-logging.md)** - Complete guide to ADRI's logging system
>
> The new documentation includes:
> - All 5 log files (3 JSONL + 2 CSV)
> - AI reasoning logs (prompts & responses)
> - Query examples (Python, SQL, jq)
> - Integration patterns
> - Use cases and best practices

**Date:** January 8, 2025
**Purpose:** Comprehensive guide to understanding ADRI's assessment audit logs

---

## Executive Summary

The **Assessment Log** (`adri_assessment_logs.csv`) is ADRI's primary audit trail that records **every single data quality assessment** performed by the system. It provides a complete, immutable record of:

- What data was assessed
- When it was assessed
- What quality score it received
- Whether it passed or failed
- What action was taken (allowed, blocked, warned)
- System context and performance metrics

Think of it as a **"flight recorder" for AI data quality** - it captures everything needed to audit, debug, and prove compliance.

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
2. **Forensic Details:** Exact data checksums, versions, system info
3. **Decision Record:** What action was taken and why
4. **Performance Metrics:** How fast assessments ran
5. **Compliance Evidence:** Immutable CSV record for regulators

---

## Part 2: Structure Overview

The Assessment Log is a **CSV file** with 25 columns organized into 6 logical groups:

```
📋 ASSESSMENT LOG STRUCTURE
├── 🆔 Core Identification (4 fields)
├── 📍 Assessment Context (4 fields)
├── 💻 System Information (3 fields)
├── 📊 Standard & Data Details (9 fields)
├── ✅ Assessment Results (3 fields)
└── ⚡ Performance Metrics (4 fields)
```

---

## Part 3: Field-by-Field Breakdown

### 🆔 Core Identification Fields

These uniquely identify each assessment and when it occurred.

#### 1. `assessment_id` (REQUIRED)
- **Format:** `adri_YYYYMMDD_HHMMSS_hexhash`
- **Example:** `adri_20251003_175905_780ea9`
- **Purpose:** Unique identifier for this specific assessment
- **Pattern:**
  - `adri_` prefix
  - Date: `20251003` = October 3, 2025
  - Time: `175905` = 17:59:05 (5:59:05 PM)
  - Hash: `780ea9` = unique 6-character hex identifier

**Why It Matters:** Links this assessment to related logs (dimension scores, failed validations)

---

#### 2. `timestamp` (REQUIRED)
- **Format:** ISO 8601 with microseconds
- **Example:** `2025-10-03T17:59:05.897069`
- **Purpose:** Exact moment assessment started
- **Precision:** Down to microseconds for ordering

**Why It Matters:** Establishes exact timeline for compliance and debugging

---

#### 3. `adri_version` (REQUIRED)
- **Format:** Semantic version with git metadata
- **Example:** `4.0.1.post128+gdac52c588.d20251003`
- **Breakdown:**
  - `4.0.1` = Base version
  - `post128` = 128 commits after release
  - `+gdac52c588` = Git commit hash
  - `.d20251003` = Dirty build from Oct 3, 2025

**Why It Matters:** Tracks which ADRI version performed assessment (for bug tracking, behavior changes)

---

#### 4. `assessment_type` (REQUIRED)
- **Valid Values:**
  - `QUALITY_CHECK` = Standard data quality assessment
  - `VALIDATION` = Validation-only check
  - `PROFILING` = Data profiling operation
- **Example:** `QUALITY_CHECK`

**Why It Matters:** Different assessment types have different compliance requirements

---

### 📍 Assessment Context Fields

These show where and how the assessment was triggered.

#### 5. `function_name` (REQUIRED)
- **Examples:**
  - `assess` = Direct engine call
  - `adri_protected` = Decorator wrapper
  - `validate_data` = CLI command
- **Purpose:** Which function triggered the assessment

**Why It Matters:** Helps trace assessment back to source code location

---

#### 6. `module_path` (REQUIRED)
- **Examples:**
  - `adri.validator.engine` = Engine module
  - `adri.cli` = CLI module
  - `my_app.data_pipeline` = User code
- **Purpose:** Python module path where assessment originated

**Why It Matters:** Shows if assessment came from ADRI internals or user code

---

#### 7. `environment` (REQUIRED)
- **Valid Values:**
  - `PRODUCTION` = Live production system
  - `DEVELOPMENT` = Dev/test environment
  - `TESTING` = Automated test run
  - `STAGING` = Pre-production staging
- **Example:** `PRODUCTION`

**Why It Matters:** Critical for compliance - distinguishes production vs. dev assessments

---

#### 8. `hostname` (REQUIRED)
- **Example:** `Thomass-MacBook-Air.local`
- **Purpose:** Name of the machine that ran the assessment

**Why It Matters:** Identifies which server/container performed assessment

---

### 💻 System Information Fields

These provide forensic details about the execution environment.

#### 9. `process_id` (REQUIRED)
- **Example:** `49803`
- **Type:** Integer (0 or greater)
- **Purpose:** Operating system process ID

**Why It Matters:** Helps correlate with system logs, distinguish parallel assessments

---

#### 10. `standard_id` (REQUIRED)
- **Example:** `invoice_data_ADRI_standard`
- **Purpose:** Identifier of the standard used for assessment

**Why It Matters:** Links assessment to specific quality rules that were applied

---

#### 11. `standard_version` (REQUIRED)
- **Examples:**
  - `1.0.0` = Explicit version from standard file
  - `unknown` = Version not specified in standard
- **Purpose:** Version of the standard used

**Why It Matters:** Standards evolve - this tracks which version of rules were applied

---

#### 12. `standard_checksum` (OPTIONAL)
- **Example:** `e5f2a1b9c3d4e7f8` (SHA-256 truncated)
- **Purpose:** Cryptographic hash of standard file content
- **Can be null:** `""` when not calculated

**Why It Matters:** Proves exact standard content (file wasn't modified after assessment)

---

### 📊 Standard & Data Details

These describe the data that was assessed.

#### 13. `data_row_count` (REQUIRED)
- **Example:** `10`
- **Type:** Integer (0 or greater)
- **Purpose:** Number of rows in the assessed dataset

**Why It Matters:** Shows scale of data assessment

---

#### 14. `data_column_count` (REQUIRED)
- **Example:** `6`
- **Type:** Integer (0 or greater)
- **Purpose:** Number of columns in the assessed dataset

**Why It Matters:** Helps understand data dimensionality

---

#### 15. `data_columns` (REQUIRED)
- **Format:** JSON array as string
- **Example:** `["invoice_id", "customer_id", "amount", "date", "status", "payment_method"]`
- **Purpose:** Exact list of column names in assessment order

**Why It Matters:**
- Shows what fields were assessed
- Critical for debugging field mapping issues
- Proves which data was examined

---

#### 16. `data_checksum` (REQUIRED)
- **Example:** `e46214176cf78804`
- **Type:** Hexadecimal string (MD5 or SHA-256)
- **Purpose:** Cryptographic hash of the data content

**Why It Matters:**
- **Immutability Proof:** Data hasn't changed since assessment
- **Deduplication:** Detect identical datasets
- **Cache Key:** Reuse assessment results for same data

---

### ✅ Assessment Results

These show the quality scores and pass/fail decision.

#### 17. `overall_score` (REQUIRED)
- **Range:** 0.0 to 100.0
- **Example:** `88.5`
- **Purpose:** Overall data quality score (0 = worst, 100 = perfect)

**Why It Matters:**
- Main quality metric
- Determines if data passes threshold
- Trends over time show data quality drift

---

#### 18. `required_score` (REQUIRED)
- **Range:** 0.0 to 100.0
- **Example:** `75.0`
- **Purpose:** Minimum score required to pass

**Why It Matters:**
- Threshold for acceptance
- Shows quality bar for this assessment
- Can vary by environment or use case

---

#### 19. `passed` (REQUIRED)
- **Type:** Boolean (TRUE/FALSE)
- **Example:** `TRUE`
- **Logic:** `overall_score >= required_score`

**Why It Matters:**
- Clear pass/fail indicator
- Triggers execution decision
- Compliance requirement

---

#### 20. `execution_decision` (REQUIRED)
- **Valid Values:**
  - `ALLOWED` = Data passed, function executed
  - `BLOCKED` = Data failed, function not executed
  - `WARNED` = Data failed but function executed anyway (warning mode)
- **Example:** `ALLOWED`

**Why It Matters:**
- Shows what action ADRI took
- Critical for accountability
- Proves enforcement

---

#### 21. `failure_mode` (REQUIRED)
- **Valid Values:**
  - `raise` = Raise exception on failure (strict)
  - `warn` = Log warning on failure (lenient)
  - `log` = Only log, no warning (silent)
- **Example:** `raise`

**Why It Matters:**
- Shows enforcement policy
- Affects system behavior
- Compliance requirement

---

#### 22. `function_executed` (REQUIRED)
- **Type:** Boolean (TRUE/FALSE)
- **Example:** `TRUE`
- **Purpose:** Whether the protected function actually ran

**Why It Matters:**
- Confirms enforcement
- Proves function was blocked if data failed
- Audit requirement

---

### ⚡ Performance Metrics

These track how fast the assessment ran.

#### 23. `assessment_duration_ms` (REQUIRED)
- **Example:** `29` (milliseconds)
- **Type:** Integer (0 or greater)
- **Purpose:** How long the assessment took

**Why It Matters:**
- Performance monitoring
- SLA compliance
- Optimization opportunities

---

#### 24. `rows_per_second` (REQUIRED)
- **Example:** `344.8275862068965`
- **Type:** Float (0.0 or greater)
- **Calculation:** `data_row_count / (assessment_duration_ms / 1000)`
- **Purpose:** Processing throughput

**Why It Matters:**
- Performance benchmarking
- Capacity planning
- Bottleneck detection

---

#### 25. `cache_used` (REQUIRED)
- **Type:** Boolean (TRUE/FALSE)
- **Example:** `FALSE`
- **Purpose:** Whether cached assessment results were used

**Why It Matters:**
- Performance optimization tracking
- Explains why some assessments are instant
- Cache hit rate analytics

---

## Part 4: Real-World Examples

### Example 1: Successful Production Assessment

```csv
assessment_id: adri_20251003_175905_780ea9
timestamp: 2025-10-03T17:59:05.897069
adri_version: 4.0.1.post128+gdac52c588.d20251003
assessment_type: QUALITY_CHECK
function_name: assess
module_path: adri.validator.engine
environment: development
hostname: Thomass-MacBook-Air.local
process_id: 49803
standard_id: invoice_data
standard_version: unknown
standard_checksum:
data_row_count: 10
data_column_count: 6
data_columns: ["invoice_id", "customer_id", "amount", "date", "status", "payment_method"]
data_checksum: e46214176cf78804
overall_score: 100.0
required_score: 75.0
passed: TRUE
execution_decision: ALLOWED
failure_mode: raise
function_executed: TRUE
assessment_duration_ms: 29
rows_per_second: 344.83
cache_used: FALSE
```

**What This Tells Us:**
- ✅ Perfect score (100.0) - data is excellent quality
- ✅ Well above threshold (75.0) - passed easily
- ✅ Function executed - processing was allowed
- ⚡ Fast assessment - 29ms for 10 rows (345 rows/sec)
- 🔍 Development environment - not production
- 📊 6 invoice fields assessed

---

### Example 2: Large Dataset Assessment

```csv
assessment_id: adri_20251003_143614_3554d1
overall_score: 91.53
required_score: 75.0
data_row_count: 35
data_column_count: 20
assessment_duration_ms: 29
rows_per_second: 1206.90
```

**What This Tells Us:**
- ✅ Good score (91.53) - minor issues but acceptable
- ✅ Passed threshold
- 📊 Larger dataset - 35 rows, 20 columns
- ⚡ Very fast - 1,207 rows/sec throughput

---

## Part 5: How It's Used

### 1. **Compliance & Audit**

**Question:** "Can you prove this AI system validates data quality?"

**Answer:** Show assessment log entries:
```
✅ Assessment performed on 2025-10-03 at 17:59:05
✅ Used standard: invoice_data
✅ Score: 100.0/100.0 - PASSED
✅ Function ALLOWED to execute
✅ Environment: PRODUCTION
```

---

### 2. **Debugging & Forensics**

**Question:** "Why did my data fail validation yesterday?"

**Answer:** Look up assessment by timestamp:
1. Find `assessment_id` for that time
2. Check `overall_score` and `passed` fields
3. Link to `failed_validations.csv` using same `assessment_id`
4. Review specific failures

---

### 3. **Performance Monitoring**

**Question:** "Is our data quality degrading over time?"

**Answer:** Query assessment log:
```sql
SELECT
  DATE(timestamp) as date,
  AVG(overall_score) as avg_score,
  COUNT(*) as assessments,
  AVG(assessment_duration_ms) as avg_ms
FROM adri_assessment_logs
WHERE environment = 'PRODUCTION'
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

---

### 4. **System Health**

**Question:** "Are assessments running too slow?"

**Answer:** Check performance metrics:
- `assessment_duration_ms` > 1000ms = potential issue
- `rows_per_second` trending down = performance degradation
- `cache_used = FALSE` always = cache not working

---

## Part 6: Integration with Other Logs

The Assessment Log is the **anchor** that links to other audit files:

```
📋 Assessment Log (ANCHOR)
  ├─ assessment_id: adri_20251003_175905_780ea9
  │
  ├─➡️ Dimension Scores Log
  │    └─ Detailed breakdown by dimension (validity, completeness, etc.)
  │
  └─➡️ Failed Validations Log
       └─ Specific validation failures with field details
```

**Example Query:**
```sql
-- Get assessment with all related details
SELECT
  a.assessment_id,
  a.overall_score,
  a.passed,
  d.dimension_name,
  d.dimension_score,
  f.field,
  f.issue,
  f.remediation
FROM adri_assessment_logs a
LEFT JOIN adri_dimension_scores d ON a.assessment_id = d.assessment_id
LEFT JOIN adri_failed_validations f ON a.assessment_id = f.assessment_id
WHERE a.assessment_id = 'adri_20251003_175905_780ea9';
```

---

## Part 7: Validation Rules

The standard itself (`ADRI_audit_log.yaml`) validates that assessment logs are complete and correct:

### Key Validations:

1. **Required Fields:** All 25 fields must be present
2. **Data Types:** Strings, integers, floats, booleans must match
3. **Ranges:** Scores must be 0-100, process_id >= 0, etc.
4. **Patterns:** assessment_id must match `adri_YYYYMMDD_HHMMSS_[hex]`
5. **Enums:** environment, assessment_type, etc. must be valid values

### Why Validate the Validator?

**Meta-Quality:** ADRI validates its own audit logs to ensure:
- No data corruption
- Complete audit trail
- Compliance-grade quality
- System integrity

---

## Part 8: Common Questions

### Q1: "Why are there duplicate assessment_ids?"
**A:** Each assessment ID is unique. If you see what looks like duplicates, check the full log - they're different assessments at slightly different timestamps.

### Q2: "What if assessment_duration_ms is 0?"
**A:** This can happen for:
- Very fast assessments (< 1ms)
- Cached results (instant return)
- Timing precision limitations

### Q3: "Why is standard_version 'unknown'?"
**A:** The standard YAML file didn't include a version field. Consider adding:
```yaml
standards:
  version: 1.0.0
```

### Q4: "Can I query this with SQL?"
**A:** Yes! Import CSV into SQLite, PostgreSQL, or any database:
```bash
sqlite3 audit.db
.mode csv
.import adri_assessment_logs.csv assessments
SELECT * FROM assessments WHERE passed = 'FALSE';
```

---

## Part 9: Best Practices

### For Developers

1. **Always Review Logs:** Check assessment logs after deployment
2. **Monitor Trends:** Track score changes over time
3. **Performance Alerts:** Alert if assessment_duration_ms > threshold
4. **Archive Properly:** Keep logs for compliance period (often 7 years)

### For Data Scientists

1. **Validate Training Data:** Check assessment logs for training datasets
2. **Track Data Drift:** Monitor overall_score trends
3. **Correlate with Model Performance:** Link assessments to model metrics

### For Compliance Officers

1. **Audit Trail:** Assessment logs prove validation occurred
2. **Retention:** Keep in immutable storage (append-only)
3. **Access Control:** Restrict modification of audit logs
4. **Regular Review:** Periodically audit the logs themselves

---

## Part 10: Summary

The Assessment Log is ADRI's **permanent record** of every data quality check performed. It provides:

✅ **Complete Accountability** - Every assessment is logged
✅ **Forensic Details** - Enough info to recreate assessment
✅ **Compliance Evidence** - Immutable audit trail
✅ **Performance Metrics** - Track system health
✅ **Integration Point** - Links to other audit logs

**Key Takeaway:** If it's not in the assessment log, it didn't happen. This log is your proof that data quality validation occurred and what the results were.

---

**Document Version:** 1.0
**Last Updated:** January 8, 2025
**Related Standards:** ADRI_audit_log.yaml
**Related Logs:** adri_dimension_scores.csv, adri_failed_validations.csv
