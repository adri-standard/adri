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
- **Centralized Monitoring**: All team members see quality metrics in unified Verodat dashboard
- **Audit Compliance**: Complete audit trails required for regulated industries (finance, healthcare)
- **Environment Isolation**: Separate dev/test/prod configurations prevent production mistakes
- **Zero Downtime Migration**: Existing `@adri_protected` code works unchanged

### For AI/ML Engineers
- **Workflow Integration**: Native support for Prefect, Airflow, and enterprise orchestration platforms
- **Reasoning Audit Logs**: Track AI decision-making processes for explainable AI compliance
- **Data Provenance**: Automatic lineage tracking through complex data processing pipelines
- **Performance at Scale**: Optimized for enterprise workloads with batch processing and caching

### For Engineering Managers
- **Risk Mitigation**: License validation ensures only authorized users access enterprise features
- **Operational Excellence**: Real-time quality monitoring across all production AI workflows
- **Developer Productivity**: Zero learning curve - same APIs, enhanced capabilities
- **ROI Tracking**: Comprehensive analytics on data quality impact across projects

---

## Enterprise vs Open Source Comparison

| Feature Category | Open Source ADRI | verodat-adri Enterprise | Enterprise Value |
|------------------|:----------------:|:----------------------:|-----------------|
| **Core Data Quality** | ✅ | ✅ | **Identical reliability** |
| Data contracts & validation | ✅ | ✅ | Same proven algorithms |
| 5-dimension quality scoring | ✅ | ✅ | Same assessment engine |
| Local JSONL audit logs | ✅ | ✅ | File-based development logging |
| CLI tools and contract generation | ✅ | ✅ | Full feature compatibility |
| **Enterprise Operations** | **Limited** | **Full Enterprise** | **Production Ready** |
| Centralized team dashboards | ❌ | ✅ | Team collaboration and visibility |
| Environment-aware configuration | ❌ | ✅ | Dev/test/prod separation and safety |
| AI reasoning audit logs | ❌ | ✅ | Explainable AI compliance and debugging |
| License validation and access control | ❌ | ✅ | Enterprise security and compliance |
| Workflow orchestration integration | ❌ | ✅ | Production pipeline integration |
| Data provenance tracking | ❌ | ✅ | Data lineage and compliance |
| **Performance & Scale** | **Development** | **Production** | **Enterprise Grade** |
| Assessment ID availability | 30-60 seconds | <10ms | Real-time workflow orchestration |
| Batch API processing | ❌ | ✅ | Efficient high-volume operations |
| Multi-environment support | ❌ | ✅ | Production deployment safety |
| Enterprise SLA support | ❌ | ✅ | Production reliability guarantees |

---

## Zero-Effort Migration

### Step 1: Install Enterprise Edition
```bash
pip install verodat-adri  # Replaces 'adri' package
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

# Automatically gets enterprise benefits:
# ✅ Centralized logging to Verodat cloud
# ✅ License validation and access control
# ✅ Environment-aware contract resolution
# ✅ AI reasoning audit trails (if enabled)
```

---

## Implementation Status

### Current Implementation (v7.2.0)

The following features are **fully implemented** and production-ready:
- ✅ **License Validation**: Full API key validation with caching and error handling
- ✅ **Centralized Logging**: Complete Verodat API integration with batch processing and retry logic
- ✅ **Environment-Aware Configuration**: Full dev/test/prod environment separation with automatic detection
- ✅ **Production Performance**: Optimized caching, batching, and fast-path logging (<10ms assessment ID)

### Features with Basic Logging (Development Stage)

The following features currently provide **basic console/file logging** with full API integration planned for future releases:

**Workflow Context Integration** (Basic Logging Only)
- ✅ Accepts workflow_context parameters in decorator
- ✅ Logs workflow metadata to console
- 🔄 **Planned**: Full integration with Prefect, Airflow, and Verodat workflow APIs

**Data Provenance Tracking** (Basic Logging Only)
- ✅ Accepts data_provenance parameters in decorator
- ✅ Logs data source metadata to console
- 🔄 **Planned**: Full data lineage API integration with Verodat platform

**AI Reasoning Audit Logs** (Local JSONL Only)
- ✅ Logs AI prompts and responses to local JSONL files
- ✅ Links reasoning to assessment IDs for traceability
- 🔄 **Planned**: Reasoning validation engine and centralized reasoning analytics

**Migration Path**: When full API integration is released, existing code will automatically gain enhanced capabilities with zero code changes required.

---

## Enterprise Feature Deep Dive

### 1. Centralized Team Collaboration

**Problem Solved**: Individual developers can't see what's happening with data quality across the team.

**Enterprise Solution**: Unified Verodat dashboard showing all quality assessments across your organization.

```python
from adri import adri_protected

# Automatic centralized logging - no extra code needed
@adri_protected(contract="sales_data")
def analyze_sales_performance(data):
    return analysis_results

# All team members see this assessment in Verodat dashboard
# Managers get real-time visibility into data quality across projects
# Quality trends and patterns are tracked automatically
```

**Customer Value**:
- **Visibility**: Engineering managers see real-time quality metrics across all AI projects
- **Collaboration**: Data engineers can see quality patterns and share insights
- **Accountability**: Clear audit trail of who processed what data and when

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

### 3. AI Reasoning Audit Logs

**Problem Solved**: AI decision-making processes are often black boxes with no audit trail.

**Enterprise Solution**: Comprehensive logging of AI reasoning steps for compliance and debugging.

```python
from adri_enterprise import adri_protected

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

# Automatic JSONL audit logs created:
# - adri_reasoning_prompts.jsonl  (all AI prompts)
# - adri_reasoning_responses.jsonl (all AI responses)
# - Linked by assessment ID for traceability
```

**Customer Value**:
- **Compliance**: Meet explainable AI requirements for regulated industries
- **Debugging**: Trace AI decisions when assessments produce unexpected results
- **Quality Improvement**: Analyze AI reasoning patterns to improve model performance

### 4. Workflow Orchestration Integration

**Problem Solved**: Data quality assessments are isolated from broader workflow context.

**Enterprise Solution**: Deep integration with enterprise workflow orchestration platforms.

```python
from adri_enterprise import adri_protected

# Prefect workflow integration
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

# Automatic benefits:
# ✅ Workflow context logged to Verodat for end-to-end traceability
# ✅ Data provenance tracked for compliance and debugging
# ✅ Assessment linked to specific workflow run for operational visibility
```

**Customer Value**:
- **Operational Visibility**: See data quality in context of broader business processes
- **Root Cause Analysis**: Trace quality issues back to specific data sources and workflow steps
- **Process Optimization**: Identify data quality bottlenecks in production workflows

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
# ✅ Assessment data batched for efficient API calls
# ✅ Fast-path logging provides <10ms assessment ID availability
# ✅ Background upload to Verodat cloud
```

**Performance Benchmarks** (Validated by Test Suite):
- **License validation**: <5 seconds (cached: <0.1 seconds)
- **Reasoning log writes**: <0.5 seconds per step
- **Verodat API calls**: <10 seconds (batched)
- **Decorator overhead**: <0.1 seconds per call

---

## Enterprise Deployment Patterns

### Pattern 1: Team Development Workflow
```python
# Development team using shared Verodat workspace
from adri import adri_protected

@adri_protected(
    contract="user_behavior_analysis",
    environment="development",     # Uses dev quality thresholds
    reasoning_mode=True           # Enables team debugging
)
def analyze_user_behavior(user_data):
    insights = ai_model.analyze_behavior(user_data)
    return insights

# Benefits:
# - All developers see quality trends in shared dashboard
# - AI reasoning logs help debug model issues across team
# - Development-appropriate quality thresholds prevent blocking
```

### Pattern 2: Production AI Pipeline
```python
# Production deployment with strict quality controls
from adri_enterprise import adri_protected

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
from adri_enterprise import adri_protected

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

# Compliance benefits:
# ✅ Complete AI reasoning audit trail (GDPR, HIPAA)
# ✅ Data provenance tracking (regulatory requirements)
# ✅ Quality enforcement (patient safety)
# ✅ Centralized compliance reporting via Verodat
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
from adri_enterprise import adri_protected

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
    # All AI reasoning automatically logged to:
    # - Local JSONL files (immediate access)
    # - Verodat cloud (team access and analytics)
    credit_decision = ai_model.assess_creditworthiness(applicant_data)
    return credit_decision
```

**Compliance Benefits**:
- GDPR Article 22 (automated decision-making) compliance
- SOX compliance for financial AI decisions
- HIPAA compliance for healthcare AI processing
- Complete audit trail for regulatory inquiries

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
# Prefect workflow with ADRI enterprise integration
from prefect import flow, task
from adri_enterprise import adri_protected

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

### Proven Performance (Validated by Test Suite)

| Metric | Open Source | Enterprise | Improvement |
|--------|:-----------:|:----------:|:-----------:|
| **Assessment ID availability** | 30-60 seconds | <10ms | **300x faster** |
| **License validation** | N/A | <5 seconds (cached: <0.1s) | **Enterprise security** |
| **Batch API processing** | N/A | <10 seconds for 50 assessments | **High-volume efficiency** |
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

## Customer Success Stories

### Fintech: Regulatory Compliance
*"The AI reasoning audit logs were exactly what our compliance team needed for SOX audits. We can prove every AI decision in our fraud detection pipeline."* - Lead Data Engineer, Major Bank

### Healthcare: Patient Data Protection
*"Environment separation prevented us from accidentally using development-grade quality rules on patient data. The audit trail helps with HIPAA compliance."* - Senior ML Engineer, Health Tech Company

### E-commerce: Team Collaboration
*"Our entire data science team now sees quality metrics in one dashboard. We caught data drift issues 2 weeks earlier than we would have otherwise."* - Head of Data Science, E-commerce Platform

---

## Getting Started

### 1. Quick Win: Centralized Logging
```bash
# Install and configure
pip install verodat-adri
export VERODAT_API_KEY="your-key"

# Your existing code automatically gets centralized logging
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

- **Enterprise License**: Apache 2.0 + Valid Verodat API Key Required
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

Get started: [verodat.com/enterprise](https://verodat.com/enterprise)

---

*Built by [Verodat](https://verodat.com) - Enterprise data infrastructure for AI workflows*
