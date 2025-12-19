# Getting Started with ADRI

A detailed 10-minute tutorial to master ADRI basics.

## Table of Contents

1. [What You'll Learn](#what-youll-learn)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Your First Protected Function](#your-first-protected-function)
5. [Understanding Auto-Generation](#understanding-auto-generation)
6. [Working with Generated Standards](#working-with-generated-standards)
7. [Guard Modes](#guard-modes)
8. [Local Logging and Insights](#local-logging-and-insights)
9. [Configuration](#configuration)
10. [Next Steps](#next-steps)

## What You'll Learn

By the end of this guide, you'll know how to:
- Install and configure ADRI
- Protect functions with the `@adri_protected` decorator
- Understand auto-generation of quality standards
- Customize generated standards
- Choose between block and warn modes
- Access local logs for debugging
- Configure ADRI for your project

**Time**: 10 minutes

## Prerequisites

- Python 3.8 or higher
- Basic Python knowledge
- Pip package manager

## Installation

Install ADRI using pip:

```bash
pip install adri
```

Verify installation:

```bash
adri --version
```

You should see output like:
```
ADRI version 3.2.0
```

## Want an Interactive Tutorial?

**First-time user?** Try the interactive guide for a hands-on walkthrough:

```bash
adri guide
```

The guide will walk you through:
- Setting up your project structure
- Using decorators with sample data
- Generating and viewing standards
- Understanding assessment results

**Time**: 5 minutes
**Recommended for**: First-time users wanting a quick interactive introduction

**Want more depth?** Continue reading this guide for detailed explanations and advanced topics.

## Your First Protected Function

Let's create a simple data processing function and protect it with ADRI.

### Step 1: Create the Function

Create a file called `customer_processor.py`:

```python
from adri import adri_protected
import pandas as pd

@adri_protected(contract="customer_data", data_param="customers")
def process_customers(customers):
    """Process customer data for analysis."""
    print(f"Processing {len(customers)} customers")

    # Your processing logic
    total_value = customers['purchase_value'].sum()
    avg_age = customers['age'].mean()

    return {
        "total_customers": len(customers),
        "total_value": total_value,
        "average_age": avg_age
    }

if __name__ == "__main__":
    # Sample customer data
    customers = pd.DataFrame({
        "customer_id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "email": ["alice@example.com", "bob@example.com", "charlie@example.com"],
        "age": [25, 30, 35],
        "purchase_value": [100.0, 150.0, 200.0],
        "signup_date": ["2024-01-01", "2024-01-02", "2024-01-03"]
    })

    result = process_customers(customers)
    print(f"Result: {result}")
```

### Step 2: Run It

```bash
python customer_processor.py
```

**Output:**
```
✅ Auto-generating quality standard from data...
📋 Standard saved: ADRI/dev/contracts/process_customers_customers_standard.yaml
🛡️ ADRI Protection: ALLOWED ✅
📊 Quality Score: 100.0/100

Processing 3 customers
Result: {'total_customers': 3, 'total_value': 450.0, 'average_age': 30.0}
```

**What happened:**

1. ✅ ADRI analyzed your customer data
2. ✅ Generated a quality standard
3. ✅ Saved the standard to `ADRI/dev/contracts/`
4. ✅ Validated the data (passed)
5. ✅ Executed your function

## Understanding Auto-Generation

ADRI's auto-generation learns from your data on first successful run.

### What Gets Analyzed

For the customer data above, ADRI learned:

- **Field Names**: `customer_id`, `name`, `email`, `age`, `purchase_value`, `signup_date`
- **Data Types**: Integer, string, float, date
- **Required Fields**: All fields present in sample
- **Value Patterns**: Email format, age range, positive values
- **Data Freshness**: Date patterns

### Standard Location

Generated standards are saved to:
```
.adri/
  └── standards/
      └── process_customers_customers_standard.yaml
```

### When Standards Are Generated

- **First run**: Standard doesn't exist → Auto-generates
- **Subsequent runs**: Standard exists → Validates against it
- **Manual override**: Use `standard="my_standard"` parameter

## Working with Generated Standards

Let's examine and customize the generated standard.

### Step 1: View the Generated Standard

```bash
cat ADRI/dev/contracts/process_customers_customers_standard.yaml
```

You'll see something like:

```yaml
standard:
  name: "process_customers_customers"
  version: "1.0.0"
  description: "Auto-generated standard for process_customers function"

  fields:
    customer_id:
      type: integer
      required: true
      min_value: 1

    name:
      type: string
      required: true
      min_length: 1

    email:
      type: string
      required: true
      pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"

    age:
      type: integer
      required: true
      min_value: 0
      max_value: 120

    purchase_value:
      type: number
      required: true
      min_value: 0

    signup_date:
      type: date
      required: true
```

### Step 2: Customize the Standard

Edit the YAML file to match your exact requirements:

```yaml
standard:
  name: "process_customers_customers"
  version: "1.1.0"  # Updated version
  description: "Customer data quality standard"

  fields:
    customer_id:
      type: integer
      required: true
      min_value: 1

    name:
      type: string
      required: true
      min_length: 2  # Names must be at least 2 characters

    email:
      type: string
      required: true
      pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"

    age:
      type: integer
      required: true
      min_value: 18  # Only adults
      max_value: 100

    purchase_value:
      type: number
      required: true
      min_value: 0.01  # Minimum purchase
      max_value: 10000  # Maximum purchase limit

    signup_date:
      type: date
      required: true
      max_age_days: 365  # Data must be less than 1 year old
```

### Step 3: Test with Bad Data

Create `test_bad_data.py`:

```python
from adri import adri_protected
import pandas as pd

@adri_protected(contract="customer_data", data_param="customers")
def process_customers(customers):
    return {"count": len(customers)}

# Bad data - violates our standard
bad_customers = pd.DataFrame({
    "customer_id": [1, 2, None],  # Missing ID
    "name": ["Alice", "B", "Charlie"],  # "B" too short
    "email": ["alice@example.com", "invalid-email", "charlie@example.com"],  # Bad email
    "age": [25, 15, 35],  # 15 is under 18
    "purchase_value": [100.0, 0.0, 200.0],  # 0.0 below minimum
    "signup_date": ["2024-01-01", "2020-01-02", "2024-01-03"]  # 2020 too old
})

try:
    result = process_customers(bad_customers)
except Exception as e:
    print(f"Caught validation error: {e}")
```

Run it:

```bash
python test_bad_data.py
```

**Output:**
```
🛡️ ADRI Protection: BLOCKED ❌
📊 Quality Score: 45.2/100 (Required: 80.0/100)

Quality Issues Found:
- Completeness: Missing value in 'customer_id' (row 3)
- Validity: Invalid email format in 'email' (row 2)
- Accuracy: Value 15 in 'age' below minimum 18 (row 2)
- Accuracy: Value 0.0 in 'purchase_value' below minimum 0.01 (row 2)
- Timeliness: Date in 'signup_date' older than 365 days (row 2)
```

## Guard Modes

ADRI offers two guard modes: **block** (strict) and **warn** (permissive).

### Block Mode (Default)

Raises an exception when data quality fails:

```python
@adri_protected(contract="data", data_param="data", on_failure="raise")
def strict_function(data):
    return results  # Won't execute if data is bad
```

**Use when:**
- Data quality is critical
- Processing bad data would cause errors
- You want to fail fast

### Warn Mode

Logs a warning but continues execution:

```python
@adri_protected(contract="data", data_param="data", on_failure="warn")
def lenient_function(data):
    return results  # Will execute even with bad data
```

**Use when:**
- Developing and testing
- Data quality issues are acceptable
- You want visibility without disruption

### Example: Development vs Production

```python
import os
from adri import adri_protected

# Use warn mode in development, block mode in production
MODE = "warn" if os.getenv("ENV") == "dev" else "block"

@adri_protected(data_param="data", mode=MODE)
def flexible_function(data):
    return process(data)
```

## Local Logging and Insights

ADRI logs all validation activity locally for debugging.

### Log Location

```
.adri/
  └── logs/
      ├── adri_2024_01_15.log
      └── assessments/
          └── process_customers_2024_01_15_14_30_22.json
```

### Reading Logs

**Text Logs:**
```bash
cat ADRI/dev/logs/adri_2024_01_15.log
```

**Assessment Reports:**
```bash
cat ADRI/dev/logs/assessments/process_customers_2024_01_15_14_30_22.json
```

Assessment reports include:
- Overall quality score
- Scores per dimension (validity, completeness, etc.)
- Specific issues found
- Row-level details
- Recommendations

### Using CLI to View Reports

```bash
# List recent assessments
adri list-assessments

# View specific assessment
adri show-assessment process_customers_2024_01_15_14_30_22

# Export assessment to file
adri export-report --latest --output report.json
```

## Configuration

Configure ADRI behavior for your project.

### Method 1: Config File

Create `ADRI/dev/config.yaml`:

```yaml
# Standards configuration
standards_path: ".adri/standards"
bundled_standards_path: "~/.adri/standards"

# Logging configuration
log_level: "INFO"
log_path: ".adri/logs"

# Validation configuration
default_mode: "block"
auto_generate: true
min_score: 80.0

# Development settings
verbose: false
```

### Method 2: Interactive Setup

```bash
adri setup
```

Follow the prompts to configure:
- Standards location
- Log level
- Default guard mode
- Auto-generation preference

### Method 3: Decorator Parameters

Override config per function:

```python
@adri_protected(
    data_param="data",
    on_failure="warn",
    auto_generate=True,
    min_score=85.0
)
def custom_function(data):
    return results
```

### Configuration Priority

1. Decorator parameters (highest priority)
2. Project `ADRI/dev/config.yaml`
3. User `~/ADRI/config.yaml`
4. Default values (lowest priority)

## Next Steps

### Learn the Fundamentals

- [How It Works](HOW_IT_WORKS.md) - Five quality dimensions explained
- [Framework Patterns](FRAMEWORK_PATTERNS.md) - Integrate with your framework
- [CLI Reference](CLI_REFERENCE.md) - Master CLI tools

### Explore Advanced Topics

- [Architecture](ARCHITECTURE.md) - Technical deep dive
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [FAQ](FAQ.md) - Common questions answered

### Try the Examples

- [Generic Examples](../examples/generic_basic.py) - Basic Python functions
- [LangChain Examples](../examples/langchain_basic.py) - LangChain integration
- [All Examples](../examples/README.md) - Complete examples list

### Get Help

- **Issues**: [GitHub Issues](https://github.com/adri-standard/adri/issues)
- **Discussions**: [GitHub Discussions](https://github.com/adri-standard/adri/discussions)
- **Documentation**: [Full Documentation](https://github.com/adri-standard/adri)

---

**You're now ready to protect your AI agents!** Start with the [Quickstart](../QUICKSTART.md) or dive into [Framework Patterns](FRAMEWORK_PATTERNS.md).
