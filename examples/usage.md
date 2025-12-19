# ADRI Usage Examples

This directory contains practical examples of using ADRI in real AI agent workflows.

Note: Our canonical example variable name in user docs is `invoice_rows`. See docs: [Core Concepts](../docs/users/core-concepts.md).

## Quick Start

### 1. Basic Protection
```python
from adri import adri_protected

@adri_protected(contract="customer_data_standard", data_param="invoice_rows")
def process_customer_data(invoice_rows):
    # Your AI agent logic here
    return analyze_customer_sentiment(invoice_rows)
```

### 2. Strict Financial Protection
```python
from adri import adri_protected

@adri_protected(
    standard="financial_data_standard",
    min_score=95,
    dimensions={"validity": 19, "completeness": 19},
    on_failure="raise"
)
def process_financial_transactions(transaction_data):
    return execute_trading_strategy(transaction_data)
```

### 3. Development-Friendly Protection
```python
from adri import adri_protected

@adri_protected(
    standard="user_profile_standard",
    min_score=70,
    on_failure="warn",
    verbose=True
)
def update_user_profiles(user_data):
    return personalization_engine(user_data)
```

## Available Examples

### Use Cases
- `use_cases/customer_support_agent.md` - Customer service agent with data protection
- `use_cases/finance_invoice_agent.md` - Financial invoice processing agent

### Framework Integrations
- LangChain integration examples (coming soon)
- CrewAI integration examples (coming soon)
- LlamaIndex integration examples (coming soon)

### Data Standards
- `datasets/` - Sample datasets for testing
- Example YAML standards for common data types

## CLI Examples

### Initialize ADRI
```bash
adri setup --project-name "my-ai-project"
```

### Generate Standards
```bash
adri generate-standard customer_data.csv
adri generate-standard financial_transactions.json --force
```

### Run Assessments
```bash
adri assess customer_data.csv --standard customer_data_standard
adri assess transactions.json --standard financial_standard --output report.json
```

### Validate Standards
```bash
adri validate-standard customer_data_standard
adri list-standards
```

## Best Practices

1. **Start with Standards**: Always generate standards from your actual data
2. **Environment-Specific Thresholds**: Use different score requirements for dev vs prod
3. **Dimension-Specific Requirements**: Set higher requirements for critical dimensions
4. **Gradual Adoption**: Start with `warn` mode, move to `raise` for production
5. **Monitor and Iterate**: Use audit logs to understand your data quality patterns

## Framework Integration Patterns

### LangChain
```python
from langchain.tools import BaseTool
from adri import adri_protected

class CustomerAnalysisTool(BaseTool):
    name = "customer_analysis"
    description = "Analyze customer data for insights"

    @adri_protected(contract="customer_data_standard", data_param="invoice_rows")
    def _run(self, invoice_rows):
        return self.analyze_customers(invoice_rows)
```

### CrewAI
```python
from crewai import Agent, Task
from adri import adri_protected

class DataAnalystAgent:
    @adri_protected(
        standard="market_data_standard",
        min_score=85,
        on_failure="raise",
        data_param="invoice_rows",
    )
    def analyze_market_trends(self, invoice_rows):
        return self.perform_analysis(invoice_rows)
```

## Troubleshooting

### Common Issues
1. **Standard Not Found**: Run `adri generate-standard <your-data>` to create one
2. **Low Quality Scores**: Check `adri assess <data> --standard <standard>` for details
3. **Import Errors**: Ensure ADRI is installed: `pip install adri`

### Environment Variables
- `ADRI_STANDARDS_PATH`: Path to your standards directory
- `ADRI_ENV`: Environment name (DEVELOPMENT, PRODUCTION, TEST)

For more detailed examples, see the individual use case files in this directory.
