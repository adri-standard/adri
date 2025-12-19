# ADRI Quickstart

Get data quality protection for your AI agents in 2 minutes.

## Install

```bash
pip install adri
```

## Basic Usage

### Step 1: Add the Decorator

```python
from adri import adri_protected

@adri_protected(standard="customer_data", data_param="data")
def process_customers(data):
    # Your agent logic here
    return results
```

### Step 2: Run With Good Data

```python
import pandas as pd

# Good data - clean, complete, valid
customers = pd.DataFrame({
    "id": [1, 2, 3],
    "email": ["user1@example.com", "user2@example.com", "user3@example.com"],
    "signup_date": ["2024-01-01", "2024-01-02", "2024-01-03"]
})

process_customers(customers)  # ✅ Runs successfully
```

**What happened:**
- Function executed
- ADRI analyzed data structure
- Generated standard at `ADRI/dev/standards/customer_data.yaml`
- Future runs validate against this standard

### Step 3: Protection Kicks In

```python
# Bad data - missing fields, invalid formats
bad_customers = pd.DataFrame({
    "id": [1, 2, None],  # ❌ Missing ID
    "email": ["user1@example.com", "invalid", "user3@example.com"],  # ❌ Bad format
    # ❌ Missing signup_date column
})

process_customers(bad_customers)  # ❌ Raises exception with quality report
```

**Protection output:**
```
🛡️ ADRI Protection: BLOCKED ❌
📊 Quality Score: 67.3/100 (Required: 80.0/100)

Quality Issues:
✗ Completeness: Missing required field 'signup_date'
✗ Validity: Field 'email' has invalid format in 1 row
✗ Validity: Field 'id' contains null value
```

## Done! 🎉

Your function is now protected. Bad data is blocked before it reaches your logic.

## Want an Interactive Tutorial?

New to ADRI? Try the interactive guide:

```bash
adri guide
```

This 3-minute walkthrough will:
- Set up your project
- Show decorator usage
- Generate a standard
- Assess sample data
- Review audit logs

**Highly recommended for first-time users!**

## What's Next?

### Choose Protection Mode

```python
# Raise mode (default) - blocks bad data
@adri_protected(standard="data", data_param="data", on_failure="raise")

# Warn mode - logs warning but continues
@adri_protected(standard="data", data_param="data", on_failure="warn")

# Continue mode - silently continues
@adri_protected(standard="data", data_param="data", on_failure="continue")
```

### Set Quality Thresholds

```python
@adri_protected(
    standard="critical_data",
    data_param="data",
    min_score=90,  # Require 90/100 quality
    on_failure="raise"
)
```

### Use CLI Tools

```bash
# Initialize ADRI in your project
adri setup --guide

# Generate a standard from good data
adri generate-standard customers.csv --output customer_standard.yaml

# Assess data quality
adri assess test_data.csv --standard customer_standard

# List available standards
adri list-standards

# Validate a standard file
adri validate-standard customer_standard.yaml
```

### View Logs

Check assessment details:
```bash
cat ADRI/dev/logs/adri_assessments.log
```

### Framework Integration

Works the same across all frameworks:

**LangChain:**
```python
@adri_protected(standard="chain_input", data_param="input_data")
def langchain_tool(input_data):
    return chain.invoke(input_data)
```

**CrewAI:**
```python
@adri_protected(standard="crew_context", data_param="context")
def crew_task(context):
    return crew.kickoff(context)
```

**AutoGen:**
```python
@adri_protected(standard="messages", data_param="messages")
def autogen_function(messages):
    return agent.generate_reply(messages)
```

## Common Patterns

### Pattern 1: API Data
```python
@adri_protected(standard="api_response", data_param="response")
def process_api_data(response):
    return transform(response)
```

### Pattern 2: Multi-Parameter Functions
```python
@adri_protected(standard="customer_data", data_param="customers")
def process_with_config(customers, config, api_key):
    # Only 'customers' is validated
    return results
```

### Pattern 3: Development vs Production
```python
# Development - warn on issues
@adri_protected(
    standard="dev_data",
    data_param="data",
    on_failure="warn",
    min_score=70
)

# Production - strict validation
@adri_protected(
    standard="prod_data",
    data_param="data",
    on_failure="raise",
    min_score=90
)
```

## Troubleshooting

### "Standard not found"
Run your function once with good data. ADRI will auto-generate the standard.

### "Quality score too low"
1. Check logs: `cat ADRI/dev/logs/adri_assessments.log`
2. Fix data issues OR adjust `on_failure` to "warn"
3. Lower `min_score` if needed

### "Import errors"
```bash
pip install adri --upgrade
```

## Learn More

- **[Getting Started](docs/GETTING_STARTED.md)** - Detailed 10-minute tutorial
- **[How It Works](docs/HOW_IT_WORKS.md)** - Five quality dimensions
- **[Framework Patterns](docs/FRAMEWORK_PATTERNS.md)** - Framework-specific examples
- **[CLI Reference](docs/CLI_REFERENCE.md)** - All CLI commands
- **[API Reference](docs/API_REFERENCE.md)** - All decorator options
- **[FAQ](docs/FAQ.md)** - Common questions

## Examples

Check out [examples/](examples/) for real-world examples:
- `generic_basic.py` - Basic Python usage
- `langchain_basic.py` - LangChain integration
- `crewai_basic.py` - CrewAI multi-agent
- `autogen_basic.py` - AutoGen conversations
- And more...

---

**One decorator. Any framework. Reliable agents.**
