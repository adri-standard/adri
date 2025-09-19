---
sidebar_position: 2
---

# Getting Started with ADRI

**Stop AI agents from breaking on bad data in 5 minutes**

## Installation

```bash
pip install adri
```

## Basic Usage

### 1. Protect Any Function

```python
from adri import adri_protected

@adri_protected(standard="customer_data")
def process_customers(customer_data):
    # Your existing agent logic
    return ai_analysis(customer_data)
```

### 2. Test with CLI

```bash
# Validate data quality
adri assess customer_data.csv

# See available commands
adri --help
```

## How ADRI Works

1. **First Run**: ADRI analyzes your data and auto-generates a YAML standard
2. **Subsequent Runs**: ADRI validates data against the existing standard
3. **Protection**: Only quality data reaches your agent functions
4. **Logging**: Every decision is logged for transparency and compliance

## Configuration Modes

ADRI offers flexible protection levels:

### **Fail-Fast Mode** (Default)
```python
@adri_protected(standard="customer_data")  # Blocks entire dataset if critical issues
```

### **Selective Blocking**
```python
@adri_protected(standard="customer_data", mode="selective")  # Removes only dirty records
```

### **Warn-Only Mode**
```python
@adri_protected(standard="customer_data", mode="warn")  # Logs issues but doesn't block
```

## Framework Examples

### LangChain
```python
from langchain.chains import LLMChain
from adri import adri_protected

@adri_protected(standard="customer_support_data")
def langchain_support_agent(customer_data):
    chain = prompt | model | parser
    return chain.invoke(customer_data)
```

### CrewAI
```python
from crewai import Agent, Task, Crew
from adri import adri_protected

@adri_protected(standard="market_analysis_data")
def crewai_market_analysis(market_data):
    crew = Crew(agents=[analyst], tasks=[analysis_task])
    return crew.kickoff(inputs=market_data)
```

### Any Framework
```python
@adri_protected(standard="your_data_standard")
def your_agent_function(data):
    return your_ai_framework(data)  # Protected automatically
```

## Common Use Cases

### Customer Support Agent
```python
@adri_protected(standard="customer_data")
def handle_support_ticket(customer_data):
    # ADRI ensures valid emails, customer IDs, and recent data
    return generate_response(customer_data)
```

### Invoice Processing
```python
@adri_protected(standard="invoice_data", min_score=90)
def process_invoices(invoice_data):
    # ADRI validates totals > 0, valid IDs, and proper formats
    return automate_payment(invoice_data)
```

### Financial Analysis
```python
@adri_protected(standard="financial_data", min_score=95)
def risk_analysis(financial_data):
    # ADRI ensures high-quality data for critical decisions
    return calculate_risk(financial_data)
```

## Configuration

Create `adri-config.yaml` for project-wide settings:

```yaml
validation:
  default_min_score: 80
  failure_mode: "raise"  # raise, warn, or log

audit:
  enabled: true
  log_file: "logs/adri_audit.jsonl"

standards:
  auto_generate: true
  path: "./standards"
```

## What Gets Validated

ADRI automatically checks your data across **5 dimensions**:

- **Validity** - Format compliance (emails, dates, patterns)
- **Completeness** - Required fields populated
- **Consistency** - Data types and formats aligned
- **Plausibility** - Realistic value ranges
- **Freshness** - Data recency and relevance

## Output and Logs

### Console Output
```
🛡️ ADRI Protection: ALLOWED ✅
📊 Quality Score: 94.2/100 (Required: 80.0/100)
```

### JSON Audit Logs
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "function_name": "process_customers",
  "overall_score": 94.2,
  "passed": true,
  "issues_found": []
}
```

## Troubleshooting

### Common Issues

**Q: No standards directory found**
```bash
mkdir standards
# ADRI will auto-create standards here on first run
```

**Q: Too strict validation**
```python
@adri_protected(standard="your_data", min_score=60)  # More permissive
```

**Q: Want to see what ADRI checks**
```bash
adri show-standard customer_data_standard
```

## Next Steps

1. **[Read the FAQ](faq)** - Complete information about ADRI
2. **[Try Framework Examples](frameworks)** - Copy-paste code for your framework
3. **[Explore Use Cases](https://github.com/adri-standard/adri/tree/main/examples/use_cases)** - Business scenarios and walkthroughs
4. **[Join the Community](https://github.com/adri-standard/adri/blob/main/CONTRIBUTING.md)** - Help improve ADRI

---

**Need help?** Check the [FAQ](faq) or [open an issue](https://github.com/adri-standard/adri/issues).
