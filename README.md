# ADRI - Stop AI Agents Breaking on Bad Data

**Prevent 80% of production agent failures with one decorator**

## 10-Second Setup

```bash
pip install adri
```

```python
from adri.decorators.guard import adri_protected

@adri_protected
def your_agent_function(data):
    # Your existing code - now protected!
    return result
```

**That's it.** Your AI agents are now protected from bad data.

## What You Get

✅ **Zero Configuration** - Works immediately with built-in standards  
✅ **Framework Agnostic** - Protects any Python function  
✅ **Offline First** - No external dependencies or API keys  
✅ **Sub-millisecond** - Intelligent caching for performance  

## Protection in Action

### ✅ Good Data (Protection Allows)
```
🛡️ ADRI Protection: ALLOWED ✅
📊 Quality Score: 94.2/100 (Required: 80.0/100)
```

### ❌ Bad Data (Protection Blocks)
```
🛡️ ADRI Protection: BLOCKED ❌
❌ Data quality too low for reliable agent execution
📊 Quality Assessment: 67.3/100 (Required: 80.0/100)

🔧 Fix This:
   • customer_id: Should be integer, got string
   • email: Invalid email format
   • age: Value -5 is outside valid range (18-120)
```

## Real Examples

### 🟢 Zero-Configuration (Auto-Generated Standards)

```python
# Customer service agent - ADRI automatically selects customer_data_standard
@adri_protected
def process_customer_request(customer_data):
    # ADRI infers: customer data → customer_data_standard.yaml
    response = generate_support_response(customer_data)
    return response

# Financial analysis - ADRI automatically selects financial standard  
@adri_protected(min_score=95)  # Extra strict
def analyze_loan_application(application_data):
    # ADRI infers: loan/financial → financial_risk_analyzer_standard.yaml
    risk_assessment = calculate_risk(application_data)
    return risk_assessment

# Any Python function - ADRI generates standard from data patterns
@adri_protected
def my_function(data):
    # ADRI analyzes data structure at runtime → creates custom standard
    return process_data(data)
```

### 🎯 Explicit Standard References

```python
# Use specific bundled standard
@adri_protected(standard_file="customer_data_standard.yaml")
def process_customer_request(customer_data):
    response = generate_support_response(customer_data)
    return response

# Use custom standard with strict requirements
@adri_protected(
    standard_file="my_loan_validation.yaml",
    min_score=95,
    auto_generate=False  # Don't auto-generate if standard missing
)
def analyze_loan_application(application_data):
    risk_assessment = calculate_risk(application_data)
    return risk_assessment

# Reference by standard name instead of file
@adri_protected(standard_name="high_quality_agent_data_standard")
def my_function(data):
    return process_data(data)
```

**Choose Your Approach:**
- **Zero-Config**: Just add `@adri_protected` - ADRI handles everything automatically
- **Explicit**: Specify exact standards when you need precise control over validation rules

## Enhanced Protection Examples

### 🛡️ Real Production Scenarios

```python
# Prevents common data issues that break agents
@adri_protected
def process_user_data(user_data):
    # ADRI automatically catches:
    # ❌ Missing required fields: customer_id, email
    # ❌ Invalid email formats: "invalid@email" 
    # ❌ Age outside realistic range: -5, 999
    # ❌ Malformed JSON structures
    # ❌ SQL injection attempts in text fields
    return ai_agent_pipeline(user_data)

# Real failure prevented:
# Input: {"customer_id": "abc", "age": -5, "email": "invalid"}
# Result: BLOCKED before reaching your expensive AI calls
```

## Auto-Generated Standards

ADRI automatically creates intelligent data quality standards from your function names and data:

```yaml
standards:
  id: "customer-data-v1"
  name: "Customer Data Quality Standard"
  
requirements:
  overall_minimum: 75.0
  
  field_requirements:
    customer_id:
      type: "integer"
      nullable: false
    email:
      pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    age:
      min_value: 18
      max_value: 120
      
  dimension_requirements:
    validity: 15.0      # Format compliance
    completeness: 14.0  # Required fields populated  
    consistency: 12.0   # Cross-field validation
    freshness: 15.0     # Data recency
    plausibility: 12.0  # Realistic values
```

**Why This Matters:** Instead of writing validation rules manually, ADRI learns from your data patterns and creates comprehensive standards automatically.

## Audit Logs for Every Team

### 🚀 For AI Engineers
Focus on execution performance and debugging:

```json
{
  "execution_context": {
    "function_name": "process_customer_request",
    "function_executed": true,
    "execution_decision": "ALLOWED"
  },
  "performance_metrics": {
    "assessment_duration_ms": 12,
    "rows_per_second": 8333.3,
    "cache_used": true
  },
  "assessment_results": {
    "overall_score": 94.2,
    "passed": true
  }
}
```

**Benefits for AI Engineers:**
- **Faster Debugging** - See exactly why functions fail or succeed
- **Performance Optimization** - Track validation overhead and caching efficiency  
- **Execution Confidence** - Know your agents ran with quality data

### 📊 For Data Engineers  
Focus on data quality details and pipeline reliability:

```json
{
  "data_fingerprint": {
    "row_count": 1000,
    "column_count": 8,
    "columns": ["customer_id", "email", "age", "registration_date"],
    "data_checksum": "a1b2c3d4e5f6"
  },
  "assessment_results": {
    "dimension_scores": {
      "validity": 18.5,
      "completeness": 16.2,
      "consistency": 14.8
    },
    "failed_checks": [
      "email: 23 records with invalid format",
      "age: 5 records outside range (18-120)",
      "customer_id: 2 duplicate values found"
    ]
  }
}
```

**Benefits for Data Engineers:**
- **Root Cause Analysis** - Identify exactly which data quality issues occur
- **Pipeline Reliability** - Monitor data quality trends over time
- **Data Quality Improvements** - Get specific remediation guidance

### 📋 For Compliance Teams
Focus on audit trails and regulatory requirements:

```json
{
  "assessment_metadata": {
    "assessment_id": "adri_20240315_143022_a1b2c3",
    "timestamp": "2024-03-15T14:30:22.123Z",
    "adri_version": "4.0.0",
    "standard_id": "customer-data-v1",
    "standard_checksum": "sha256:abc123..."
  },
  "action_taken": {
    "decision": "BLOCK",
    "failure_mode": "raise",
    "function_executed": false,
    "remediation_suggested": ["Fix email formats", "Validate age ranges"]
  }
}
```

**Benefits for Compliance:**
- **Complete Audit Trails** - Every data quality decision is logged with full context
- **Regulatory Compliance** - Demonstrate data quality controls for audits
- **Risk Management** - Track and prevent data quality incidents before they impact systems

## Framework Solutions

ADRI solves documented production issues across every major AI framework:

| Framework | GitHub Issues Prevented | What ADRI Solves |
|-----------|------------------------|-------------------|
| **🦜 LangChain** | 525+ validation failures | Chain input validation failures, memory context corruption, tool integration breakdowns |
| **🤝 CrewAI** | 124+ coordination failures | Crew coordination failures, agent role mismatches, task distribution errors |
| **💬 AutoGen** | 54+ conversation failures | Conversational flow breaks, function argument failures, message handling corruption |
| **🦙 LlamaIndex** | 949+ index failures | Document indexing errors, query processing failures, retrieval pipeline breaks |
| **🌾 Haystack** | 347+ pipeline failures | Search pipeline errors, document processing failures, retriever breakdowns |
| **🌐 LangGraph** | 245+ state failures | Workflow state corruption, graph execution errors, node processing failures |
| **🧠 Semantic Kernel** | 178+ plugin failures | Plugin execution errors, kernel function failures, AI service integration issues |

**Universal Pattern:** Add `@adri_protected` to any framework function and prevent the documented GitHub issues that break production agents.

## Next Steps

- **[Quick Start Guide](QUICK_START.md)** - Comprehensive examples for all frameworks
- **[Framework Examples](DETAILED_EXAMPLES.md)** - LangChain, CrewAI, AutoGen, LlamaIndex, etc.
- **[CLI Tools](QUICK_START.md#cli-tools)** - `adri assess`, `adri generate-standard`, etc.

## Support

- **[GitHub Issues](https://github.com/adri-standard/adri/issues)** - Report bugs and request features
- **[GitHub Discussions](https://github.com/adri-standard/adri/discussions)** - Community support

---

**MIT License** - Use freely in any project. See [LICENSE](LICENSE) for details.
