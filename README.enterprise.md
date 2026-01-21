# verodat-adri – Enterprise Data Quality for Production AI

**Enterprise-grade data quality protection for production AI workflows.**

Built on the proven open source [ADRI framework](https://github.com/adri-standard/adri) with enterprise extensions for team collaboration, compliance, and production reliability.

```python
# Same code works in both editions - zero migration effort
from adri import adri_protected

@adri_protected(contract="customer_data")
def process_customers(data):
    return enhanced_data
```

## Why Upgrade to Enterprise?

### For Production Teams
- **Centralized Monitoring**: Optional upload of assessment logs to Verodat (requires API key)
- **Audit Logs**: Local JSONL audit logs (Verodat-compatible schema)
- **Environment Separation**: Dev/test/prod config via `ADRI/config.yaml` + `ADRI_ENV`
- **Same API**: Same `@adri_protected` usage as open source

### For AI/ML Engineers
- **Workflow Context**: Accepts `workflow_context` metadata (logged when verbose)
- **Reasoning Mode**: `reasoning_mode=True` enables reasoning-oriented behavior + optional local JSONL prompt/response logs
- **Data Provenance**: Accepts `data_provenance` metadata (logged when verbose)
- **Performance Options**: Fast-path assessment manifest storage (memory/file/redis backends)

### For Engineering Managers
- **License Gate**: API key validation + 24h cache on first use
- **Operational Visibility**: Centralized logs when Verodat upload is enabled
- **Developer Productivity**: No code changes needed beyond installing enterprise package and setting `VERODAT_API_KEY`
- **Team Adoption**: Same decorator + CLI patterns

---

## Enterprise vs Open Source Comparison

| Feature Category | Open Source ADRI | verodat-adri Enterprise | Enterprise Value |
|------------------|:----------------:|:----------------------:|-----------------|
| **Core Data Quality** | ✅ | ✅ | **Identical reliability** |
| Data contracts & validation | ✅ | ✅ | Same proven algorithms |
| 5-dimension quality scoring | ✅ | ✅ | Same assessment engine |
| Local JSONL audit logs | ✅ | ✅ | File-based development logging |
| CLI tools and contract generation | ✅ | ✅ | Full feature compatibility |
| **Enterprise Add-ons** |  |  |  |
| API key (license) validation | ❌ | ✅ | Enforces enterprise access on first use |
| Optional Verodat API upload | ❌ | ✅ | Centralize assessments outside local files |
| **Configuration** |  |  |  |
| Environment-aware config (`ADRI_ENV`) | ✅ | ✅ | Dev/test/prod behavior via config + env var |
| **Workflow & LLM Context** |  |  |  |
| `workflow_context` parameter | ✅ | ✅ | Attach workflow metadata to assessments |
| `data_provenance` parameter | ❌ | ✅ | Attach provenance metadata (enterprise wrapper) |
| Local reasoning JSONL logs | ❌ | ✅ | Stores prompt/response JSONL when enabled |
| **Performance** |  |  |  |
| Fast-path manifest store (memory/file/redis) | ✅ | ✅ | Faster assessment-id availability via local store |

---

## Zero-Effort Migration

### Step 1: Install Enterprise Edition
```bash
# If you already have the open source `adri` package installed,
# uninstall it first to avoid import conflicts (both ship an `adri` module).
pip uninstall -y adri

pip install verodat-adri
```

### Step 2: Add API Key
```bash
export VERODAT_API_KEY="your-api-key-here"
```

### Step 3: Your Code Already Works!
```python
# This exact code works in both editions - no changes needed
from adri import adri_protected
import pandas as pd

@adri_protected(
    contract="customer_data",
    min_score=85,
    on_failure="raise"
)
def process_customer_data(data):
    # Your existing data processing logic
    enhanced_data = data.copy()
    enhanced_data['processed_at'] = pd.Timestamp.now()
    return enhanced_data

# Optional enterprise add-ons:
# ✅ License validation and access control
# ✅ Optional Verodat upload (when configured)
# ✅ Environment-aware contract resolution
# ✅ Optional reasoning logs (when enabled)
```

---

## Enterprise Feature Deep Dive

### 1. Centralized Logging (Optional)

**Problem Solved**: Local-only logs are hard to aggregate across projects/environments.

**Enterprise Solution**: When Verodat upload is enabled, assessments can be sent to Verodat via API.

```python
from adri import adri_protected

# Optional centralized logging (when Verodat upload is configured)
@adri_protected(contract="sales_data")
def analyze_sales_performance(data):
    return analysis_results

# The assessment can be uploaded to Verodat (depending on your logging configuration)
```

**Customer Value**:
- **Visibility**: Aggregate quality signals across environments
- **Operational debugging**: Access logs outside local machines/containers
- **Auditability**: Preserve verifiable assessment artifacts

### 2. Environment-Aware Configuration

**Problem Solved**: Same data quality rules in dev and production can cause issues.

**Enterprise Solution**: Environment-specific configurations with automatic environment detection.

```python
# ADRI/config.yaml - Enterprise environment configuration
adri:
  project_name: "customer_analytics"
  default_environment: "development"
  environments:
    development:
      paths:
        contracts: "./dev/contracts"
        assessments: "./dev/assessments"
      protection:
        default_min_score: 70      # Relaxed for development
        default_failure_mode: "warn"  # Non-blocking for development
    production:
      paths:
        contracts: "./prod/contracts"
        assessments: "./prod/assessments"
      protection:
        default_min_score: 85      # Strict for production
        default_failure_mode: "raise"  # Blocking for production

# Runtime environment switching
export ADRI_ENV=production  # Automatically uses prod config

@adri_protected(
    contract="customer_data",
    environment="production"  # Explicit environment override
)
def process_production_data(data):
    return processed_data
```

**Customer Value**:
- **Safety**: Prevents accidentally deploying development-grade quality rules to production
- **Consistency**: Standardized quality requirements across environments
- **DevOps Integration**: Works with GitOps and infrastructure-as-code workflows

### 3. Reasoning Logs (Local JSONL)

**Problem Solved**: AI decision-making processes are often black boxes with no audit trail.

**Enterprise Solution**: Optional local JSONL logging of prompt/response metadata.

```python
from adri import adri_protected

@adri_protected(
    contract="credit_decisions",
    reasoning_mode=True,           # Enable AI reasoning logging
    store_prompt=True,             # Log AI prompts
    store_response=True,           # Log AI responses
    llm_config={
        "model": "claude-3-5-sonnet",
        "temperature": 0.1,
        "seed": 42
    }
)
def assess_credit_risk(customer_data):
    # AI reasoning steps are automatically logged
    risk_assessment = ai_model.analyze_credit_risk(customer_data)
    return risk_assessment

# Optional JSONL audit logs:
# - adri_reasoning_prompts.jsonl
# - adri_reasoning_responses.jsonl
```

**Customer Value**:
- **Debugging**: Retain prompts/responses alongside quality results
- **Traceability**: Persist per-run artifacts in JSONL for later review

### 4. Workflow Context Metadata

**Problem Solved**: Data quality assessments are isolated from broader workflow context.

**Enterprise Solution**: Attach workflow context metadata to an assessment.

```python
from adri import adri_protected

# Example workflow context
@adri_protected(
    contract="transaction_processing",
    workflow_context={
        "run_id": "run_20250116_143022_abc123",
        "workflow_id": "payment_processing_pipeline",
        "workflow_version": "2.1.0",
        "step_id": "fraud_detection",
        "step_sequence": 3,
        "run_at_utc": "2025-01-16T14:30:22Z"
    },
    data_provenance={
        "source_type": "database",
        "database": "transactions_prod",
        "table": "payment_events",
        "extracted_at": "2025-01-16T14:25:00Z",
        "record_count": 15000
    }
)
def detect_transaction_fraud(transaction_data):
    fraud_scores = ml_model.predict_fraud(transaction_data)
    return fraud_scores

# Metadata is available to logging / callbacks for downstream correlation.
```

**Customer Value**:
- **Correlation**: Link assessments to workflow runs and steps
- **Debugging**: Carry “what run/step produced this data?” through logs

### 5. Production-Grade Performance

**Problem Solved**: Open source logging can be too slow for high-throughput production systems.

**Enterprise Solution**: Optimized performance with batching, caching, and async processing.

```python
from adri import adri_protected

# Performance optimizations are automatic:
@adri_protected(contract="high_volume_processing")
def process_high_volume_data(data):
    return processed_data

# Behind the scenes:
# ✅ License validation cached for 24 hours
# ✅ Fast-path manifest storage provides faster assessment-id availability
```

**Performance Benchmarks**: See test suite for performance checks and thresholds.

---

## Enterprise Deployment Patterns

### Pattern 1: Team Development Workflow
```python
# Development team using shared Verodat workspace
from adri import adri_protected

@adri_protected(
    contract="user_behavior_analysis",
    environment="development",     # Uses dev quality thresholds
    reasoning_mode=True           # Enables reasoning-mode behavior
)
def analyze_user_behavior(user_data):
    insights = ai_model.analyze_behavior(user_data)
    return insights

# Benefits:
# - Consistent dev environment config
# - Optional reasoning logs
```

### Pattern 2: Production AI Pipeline
```python
# Production deployment with strict quality controls
from adri import adri_protected

@adri_protected(
    contract="risk_assessment",
    environment="production",      # Uses prod quality thresholds
    reasoning_mode=True,          # Required for compliance
    min_score=95,                 # Strict production requirements
    on_failure="raise",           # Block processing on quality failure
    workflow_context=workflow_metadata,
    data_provenance=data_source_info
)
def assess_financial_risk(customer_portfolio_data):
    risk_scores = risk_model.predict_risk(customer_portfolio_data)
    return risk_scores

# Benefits:
# - Strict quality enforcement protects production systems
# - Complete audit trail for regulatory compliance
# - Workflow integration provides operational visibility
# - Data lineage tracking for compliance and debugging
```

### Pattern 3: Regulated Industry Compliance
```python
# Healthcare/Finance with full audit requirements
from adri import adri_protected

@adri_protected(
    contract="patient_data_processing",
    reasoning_mode=True,          # Required: AI reasoning audit trail
    store_prompt=True,            # Required: Store all AI prompts
    store_response=True,          # Required: Store all AI responses
    data_provenance={
        "source_type": "ehr_system",
        "patient_consent_id": "consent_12345",
        "data_classification": "phi",
        "retention_policy": "7_years"
    },
    min_score=98,                # Very strict for patient data
    on_failure="raise"           # Block processing on any quality issue
)
def process_patient_diagnosis_data(patient_data):
    diagnosis_insights = medical_ai.analyze_symptoms(patient_data)
    return diagnosis_insights

# Notes:
# This shows parameterization for stricter controls; any compliance posture depends on your
# own policies and how you retain/secure these logs.
```

---

## Installation & Setup

### Requirements
- **Python**: 3.10+ (same as open source)
- **Verodat API Key**: Required for enterprise features
- **Dependencies**: Same as open source + `requests` for API integration

### Get Your API Key
1. Create account at [verodat.com](https://verodat.com)
2. Navigate to Account Settings → API Keys
3. Generate new API key for your organization
4. Set environment variable: `export VERODAT_API_KEY="your-key"`

### Install Enterprise Edition
```bash
# Remove open source version (if installed)
pip uninstall adri

# Install enterprise edition
pip install verodat-adri

# With optional backends
pip install verodat-adri[redis]      # Redis backend for fast-path logging
```

### Verify Installation
```python
from adri import adri_protected
import pandas as pd

# Test with sample data
test_data = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})

@adri_protected(contract="installation_test")
def test_installation(data):
    return len(data)

result = test_installation(test_data)
print(f"✅ Enterprise ADRI working! Processed {result} records")
```

---

## Configuration

### Environment Variables
```bash
# Required
export VERODAT_API_KEY="your-enterprise-api-key"

# Optional
export VERODAT_API_URL="https://api.verodat.com/api/v1"  # Custom API endpoint
export ADRI_ENV="production"                            # Environment selection
```

### Enterprise Configuration File

**ADRI/config.yaml** (Environment-aware structure):
```yaml
adri:
  project_name: "customer_analytics_platform"
  default_environment: "development"

  environments:
    development:
      paths:
        contracts: "./dev/contracts"
        assessments: "./dev/assessments"
        training_data: "./dev/training-data"
        audit_logs: "./dev/audit-logs"
      protection:
        default_min_score: 70
        default_failure_mode: "warn"

    production:
      paths:
        contracts: "./prod/contracts"
        assessments: "./prod/assessments"
        training_data: "./prod/training-data"
        audit_logs: "./prod/audit-logs"
      protection:
        default_min_score: 85
        default_failure_mode: "raise"
```

### Usage with Configuration
```python
from adri import adri_protected

# Automatically uses production config when ADRI_ENV=production
@adri_protected(
    contract="customer_data",
    environment="production"  # Explicit production environment
)
def process_production_customers(data):
    return enhanced_data
```

---

## Advanced Enterprise Features

### 1. AI Reasoning Validation and Logging

Track every AI decision for compliance and debugging:

```python
@adri_protected(
    contract="ai_credit_decisions",
    reasoning_mode=True,           # Enable AI reasoning tracking
    store_prompt=True,             # Log all AI prompts for audit
    store_response=True,           # Log all AI responses for audit
    llm_config={
        "model": "claude-3-5-sonnet",
        "temperature": 0.1,
        "seed": 42,                 # Reproducible AI decisions
        "max_tokens": 2000
    }
)
def ai_credit_assessment(applicant_data):
    # Optional logs (depending on configuration):
    # - Local JSONL files
    credit_decision = ai_model.assess_creditworthiness(applicant_data)
    return credit_decision
```

**Compliance Notes**:
This package provides logging hooks and audit artifacts, but regulatory compliance is
program/process dependent and must be validated by your organization.

### 2. Data Provenance and Lineage Tracking

Track data sources through complex processing pipelines:

```python
@adri_protected(
    contract="cross_platform_analytics",
    data_provenance={
        "source_type": "verodat_query",        # Data source type
        "verodat_query_id": 12345,             # Source query ID
        "verodat_account_id": 91,              # Source account
        "verodat_workspace_id": 161,           # Source workspace
        "dataset_id": 4203,                    # Source dataset
        "record_count": 15000,                 # Expected record count
        "extracted_at": "2025-01-16T14:30:00Z", # Extraction timestamp
        "data_classification": "confidential"  # Security classification
    }
)
def cross_platform_analysis(multi_source_data):
    # Data lineage automatically tracked to Verodat
    combined_insights = complex_analytics.process(multi_source_data)
    return combined_insights
```

**Operational Benefits**:
- **Root Cause Analysis**: Trace quality issues back to specific data sources
- **Impact Assessment**: Understand downstream effects of data source changes
- **Compliance Reporting**: Automated data lineage reports for auditors
- **Quality Attribution**: Identify which data sources contribute to quality issues

### 3. Workflow Orchestration Context

Integrate seamlessly with enterprise workflow platforms:

```python
# Workflow example (pseudo-code)
# from prefect import flow, task
from adri import adri_protected

@task
@adri_protected(
    contract="payment_processing_step",
    workflow_context={
        "run_id": "{{run_id}}",               # Prefect run ID
        "workflow_id": "payment_pipeline",    # Workflow identifier
        "workflow_version": "2.1.0",          # Version tracking
        "step_id": "fraud_detection",         # Current step
        "step_sequence": 3,                   # Step number in workflow
        "run_at_utc": "{{run_timestamp}}"     # Execution timestamp
    }
)
def detect_payment_fraud(payment_transactions):
    fraud_scores = fraud_model.predict(payment_transactions)
    return fraud_scores

@flow(name="payment_processing_pipeline")
def payment_pipeline():
    raw_data = extract_payment_data()
    validated_data = detect_payment_fraud(raw_data)  # Enterprise ADRI protection
    process_validated_payments(validated_data)
```

**Workflow Benefits**:
- **End-to-End Visibility**: See data quality in context of complete business process
- **Failure Attribution**: Identify whether failures are data quality or business logic issues
- **Performance Analytics**: Understand data quality impact on overall workflow performance
- **Operational Debugging**: Trace issues across complex multi-step workflows

---

## Performance & Reliability

### Performance (Tested)

| Metric | Open Source | Enterprise | Improvement |
|--------|:-----------:|:----------:|:-----------:|
| **Assessment ID availability** | 30-60 seconds | <10ms | Faster assessment-id availability |
| **License validation** | N/A | <5 seconds (cached: <0.1s) | **Enterprise security** |
| **Reasoning log writes** | N/A | <0.5 seconds per step | **Real-time audit** |
| **Memory overhead** | Baseline | +<100MB | **Production acceptable** |

### Reliability Features

**Fault Tolerance**:
- Network failures don't block data processing
- API timeouts are handled gracefully with retries
- Local logging continues even if cloud integration fails
- License validation cached to handle temporary API outages

**Scalability**:
- Batch processing for high-volume operations
- Concurrent workflow support with shared license caching
- Memory-efficient logging with configurable retention
- Horizontal scaling with Redis backend support

---

## Getting Started

### 1. Quick Win: Centralized Logging
```bash
# Install and configure
pip install verodat-adri
export VERODAT_API_KEY="your-key"

# Your existing code gets centralized logging **when Verodat upload is enabled**
# No code changes needed!
```

### 2. Enable Environment Separation
```bash
# Create ADRI/config.yaml with dev/prod environments
# Set ADRI_ENV=production in production deployment
# Automatic environment-aware contract resolution
```

### 3. Add AI Reasoning Audit Trail
```python
# Add reasoning_mode=True to AI processing functions
@adri_protected(contract="ai_decisions", reasoning_mode=True)
def ai_processing_function(data):
    return ai_results
```

### 4. Integrate with Workflows
```python
# Add workflow_context to track end-to-end data flow
@adri_protected(
    contract="workflow_step",
    workflow_context={"run_id": run_id, "step": "validation"}
)
def workflow_step(data):
    return results
```

---

## Support & Resources

### Documentation
- **[Complete Documentation](docs/)** - Comprehensive feature documentation
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[Enterprise Setup Guide](docs/enterprise-setup-guide.md)** - Detailed deployment guide
- **[Migration Guide](docs/MIGRATION.md)** - Step-by-step upgrade instructions

### Community & Support
- **Issues**: [GitHub Issues](https://github.com/Verodat/verodat-adri/issues)
- **Enterprise Support**: [support@verodat.com](mailto:support@verodat.com)
- **Community**: [ADRI Standard Community](https://github.com/adri-standard/adri)

### Training & Onboarding
- **Free Onboarding Session**: Schedule with Verodat Customer Success
- **Best Practices Guide**: [docs/BEST_PRACTICES.md](docs/BEST_PRACTICES.md)
- **Workshop Materials**: Contact enterprise support for team training

---

## License & Pricing

- **Package License**: Apache-2.0
- **Enterprise Features**: Verodat cloud upload and licensed enterprise capabilities require a valid Verodat API key
- **Open Source**: Always free at [github.com/adri-standard/adri](https://github.com/adri-standard/adri)
- **Enterprise Pricing**: Contact [Verodat Sales](https://verodat.com/contact) for enterprise pricing

### When to Choose Enterprise vs Open Source

**Choose Open Source ADRI when**:
- Individual developer or small team (≤3 people)
- Development/testing environments only
- Basic data quality validation needs
- Cost is primary concern
- No compliance requirements

**Choose Enterprise verodat-adri when**:
- Production AI workflows requiring reliability
- Team collaboration and centralized monitoring needs
- Regulated industry with compliance requirements
- Complex workflows requiring integration with orchestration platforms
- Need for audit trails and data provenance tracking
- Enterprise security and access control requirements

---

**Ready to upgrade your data quality infrastructure?**

Get started: [verodat.com/adri-enterprise](https://verodat.com/adri-enterprise/)

---

*Built by [Verodat](https://verodat.com) - Enterprise data infrastructure for AI workflows*
