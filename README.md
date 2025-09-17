# ADRI - Stop AI Agents Breaking on Bad Data

**Prevent 80% of production agent failures with one decorator**

## 10-Second Setup

```bash
pip install adri
export ADRI_STANDARDS_PATH="./standards"
```

```python
from adri.decorators.guard import adri_protected

@adri_protected(standard="customer_data_standard")
def your_agent_function(data):
    # Your existing code - now protected!
    return result
```

**First run:** ADRI creates `standards/customer_data_standard.yaml` from your data patterns  
**Second run:** ADRI uses the existing standard - fast and transparent!

## What You Get

✅ **Smart Defaults** - Auto-generates standards from your data patterns  
✅ **Full Transparency** - See exactly what rules protect your functions  
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

### 🟢 Smart Auto-Generation (Transparent Standards)

```python
# Customer service agent - creates customer_data_standard.yaml first run
@adri_protected(standard="customer_data_standard")
def process_customer_request(customer_data):
    # First run: Creates standards/customer_data_standard.yaml from your data
    # Second run: Uses existing standards/customer_data_standard.yaml
    response = generate_support_response(customer_data)
    return response

# Financial analysis - strict requirements with auto-generation
@adri_protected(standard="financial_data_standard", min_score=95)
def analyze_loan_application(application_data):
    # Creates standards/financial_data_standard.yaml with strict validation rules
    risk_assessment = calculate_risk(application_data)
    return risk_assessment

# Custom data parameter - ADRI generates standard from actual data patterns
@adri_protected(standard="user_profile_standard", data_param="profile_data")
def update_user_profile(profile_data, settings):
    # Creates standards/user_profile_standard.yaml analyzing profile_data structure
    return process_profile(profile_data)
```

### 🎯 Using Template Standards

```python
# Copy from examples/standards/ to your standards/ directory
# cp examples/standards/customer_data_standard.yaml standards/

@adri_protected(standard="customer_data_standard")
def process_customer_request(customer_data):
    # Uses your copied and customized standard
    response = generate_support_response(customer_data)
    return response

# Use template with strict requirements
@adri_protected(
    standard="financial_risk_analyzer_financial_data_standard",
    min_score=95,
    auto_generate=False  # Don't auto-generate, use exact template
)
def analyze_loan_application(application_data):
    risk_assessment = calculate_risk(application_data)
    return risk_assessment
```

**Two-Run Approach:**
- **First run**: ADRI creates `standards/your_standard.yaml` from your data patterns
- **Second run**: ADRI uses the existing standard - fast, cached, and transparent
- **Templates**: Copy from `examples/standards/` if you want pre-built standards

## How It Works - Step by Step

Let me break down exactly what happens when you add `@adri_protected` to your functions:

### Example 1: Customer Service Agent (Basic Protection)
```python
@adri_protected(standard="customer_data_standard")
def process_customer_request(customer_data):
    response = generate_support_response(customer_data)
    return response
```

**What ADRI does on first and subsequent runs:**
1. **🎯 Standard Check**: Looks for `standards/customer_data_standard.yaml`
2. **📝 Auto-Generation (First Run)**: If missing, analyzes `customer_data` to create the standard:
   - ✅ Detects customer_id as integer type
   - ✅ Creates email format validation rules
   - ✅ Sets age range validation (18-120)
   - ✅ Identifies required vs optional fields
3. **🔍 Data Validation (Every Run)**: Before `generate_support_response()` runs:
   - ✅ Validates against the created/existing standard
   - ✅ Checks data quality across 5 dimensions
4. **🛡️ Protection Decision**: 
   - If data quality ≥ 75/100 → Function executes normally
   - If data quality < 75/100 → Function blocked, detailed error raised

### Example 2: Financial Analysis (Strict Protection)
```python
@adri_protected(standard="financial_data_standard", min_score=95)
def analyze_loan_application(application_data):
    risk_assessment = calculate_risk(application_data)
    return risk_assessment
```

**What the strict protection does:**
1. **🎯 Standard Management**: Uses `standards/financial_data_standard.yaml`
2. **📝 Smart Generation**: Creates financial-specific validation rules from your data patterns
3. **🔍 Enhanced Validation**: Same validation process but with **min_score=95** (vs default 75)
4. **🛡️ High-Stakes Protection**: 
   - Only executes if data quality ≥ 95/100 (very strict)
   - Perfect for financial functions where bad data = big problems

### Example 3: Custom Data Parameter
```python
@adri_protected(standard="user_profile_standard", data_param="profile_data")
def update_user_profile(profile_data, settings):
    return process_profile(profile_data)
```

**How custom parameter protection works:**
1. **🎯 Standard Location**: `standards/user_profile_standard.yaml`
2. **🔍 Parameter Analysis**: Examines `profile_data` specifically (not `settings`)
3. **📝 Targeted Generation**: Creates validation rules based on profile data structure
4. **🛡️ Selective Protection**: Only validates the specified parameter

### The Transparency Behind the Scenes

**❌ Before ADRI (Your function is vulnerable):**
```python
def process_customer_request(customer_data):
    # ❌ What if customer_data is {"id": "abc", "age": -5}?
    # ❌ Your expensive AI call fails with cryptic errors
    # ❌ No logging, no protection, no guidance
    response = generate_support_response(customer_data)
    return response
```

**✅ With ADRI (Your function is protected):**
```python
@adri_protected(standard="customer_data_standard")
def process_customer_request(customer_data):
    # ✅ ADRI validates against standards/customer_data_standard.yaml
    # ✅ You can see and edit the exact validation rules
    # ✅ Clear error messages tell you exactly what's wrong
    # ✅ Audit logs track every decision for compliance
    response = generate_support_response(customer_data)
    return response
```

**Key Benefits Demonstrated:**
- **📋 Explicit Standards**: Always see which standard protects your function
- **🔍 Full Transparency**: Standards are visible files you can inspect and modify
- **⚙️ Configurable Strictness**: Use `min_score` to set validation requirements
- **🌐 Universal Protection**: Works on any Python function, any data type
- **🚀 Smart Generation**: Auto-creates standards from your actual data patterns

The decorator wraps your function with a **"data quality gate"** using transparent, editable standards.

## Enhanced Protection Examples

### 🛡️ Real Production Scenarios

```python
# Prevents common data issues that break agents
@adri_protected(standard="user_data_standard")
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

# Production-ready examples with explicit standards
@adri_strict(standard="financial_transaction_standard")
def process_payment(transaction_data):
    # High-security payment processing with 90% quality requirement
    return payment_gateway.process(transaction_data)

@adri_permissive(standard="dev_test_data_standard") 
def development_function(test_data):
    # Development-friendly with 70% quality requirement and warnings
    return experimental_processing(test_data)
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

ADRI solves documented production issues across major AI frameworks:

| Framework | GitHub Issues Prevented | What ADRI Solves |
|-----------|------------------------|-------------------|
| **🦜 LangChain** | 525+ validation failures | Chain input validation failures, memory context corruption, tool integration breakdowns |
| **🤝 CrewAI** | 124+ coordination failures | Crew coordination failures, agent role mismatches, task distribution errors |
| **🦙 LlamaIndex** | 949+ index failures | Document indexing errors, query processing failures, retrieval pipeline breaks |

**Universal Pattern:** Add `@adri_protected` to any framework function and prevent the documented GitHub issues that break production agents.

## Next Steps

- **[Architecture Guide](ARCHITECTURE.md)** - Simple explanation of how ADRI works
- **[Quick Start Guide](QUICK_START.md)** - Comprehensive examples for core frameworks
- **[CLI Tools](QUICK_START.md#cli-tools)** - `adri assess`, `adri generate-standard`, etc.

## Support

- **[GitHub Issues](https://github.com/adri-standard/adri/issues)** - Report bugs and request features
- **[GitHub Discussions](https://github.com/adri-standard/adri/discussions)** - Community support

---

**MIT License** - Use freely in any project. See [LICENSE](LICENSE) for details.
