# ADRI Implementation Guide

This guide provides practical instructions for implementing and extending the Agent Data Readiness Index (ADRI) system.

## Getting Started

### Installation

```bash
# Install from PyPI
pip install adri

# Or install from source
git clone https://github.com/verodat/agent-data-readiness-index.git
cd agent-data-readiness-index
pip install -e .
```

### Basic Usage

```python
from adri import DataSourceAssessor

# Initialize the assessor
assessor = DataSourceAssessor()

# Assess a CSV file
report = assessor.assess_file("path/to/your/data.csv")

# Output the report
report.print_summary()

# Save detailed report
report.save_json("assessment_report.json")
report.save_html("assessment_report.html")
```

## Assessment Modes

ADRI supports different assessment modes:

```python
from adri import DataSourceAssessor
from adri.assessment_modes import AssessmentMode

# Discovery mode - for new data without metadata
assessor = DataSourceAssessor(mode=AssessmentMode.DISCOVERY)
report = assessor.assess_file("new_data.csv")

# Validation mode - for data with existing metadata
assessor = DataSourceAssessor(mode=AssessmentMode.VALIDATION)
report = assessor.assess_file("data_with_metadata.csv")

# Auto mode (default) - automatically detects the appropriate mode
assessor = DataSourceAssessor()  # or mode=AssessmentMode.AUTO
report = assessor.assess_file("any_data.csv")
```

## Using Templates

Templates define quality requirements for specific use cases:

```python
from adri import DataSourceAssessor

# Use default template
assessor = DataSourceAssessor()
report = assessor.assess_file("data.csv")  # Uses general/default-v1.0.0

# Use specific template
report, evaluation = assessor.assess_file_with_template(
    "invoice_data.csv",
    "financial/invoice-processing-v1.0.0"
)

# Check template compliance
if evaluation.is_compliant:
    print("✅ Data meets template requirements")
else:
    print("❌ Data quality issues found:")
    for gap in evaluation.gaps:
        print(f"  - {gap.dimension}: {gap.message}")
```

## Working with Different Data Sources

### CSV Files

```python
from adri import DataSourceAssessor

assessor = DataSourceAssessor()

# Basic CSV assessment
report = assessor.assess_file("data.csv")

# With specific file type
report = assessor.assess_file("data.tsv", file_type="tsv")
```

### Database Tables

```python
# Requires: pip install adri[database]
from adri import DataSourceAssessor

assessor = DataSourceAssessor()

# PostgreSQL example
connection_string = "postgresql://user:password@localhost:5432/mydb"
report = assessor.assess_database(connection_string, "users_table")

# MySQL example
connection_string = "mysql://user:password@localhost:3306/mydb"
report = assessor.assess_database(connection_string, "orders_table")
```

### API Endpoints

```python
# Requires: pip install adri[api]
from adri import DataSourceAssessor

assessor = DataSourceAssessor()

# Basic API assessment
report = assessor.assess_api("https://api.example.com/data")

# With authentication
auth = {"headers": {"Authorization": "Bearer token123"}}
report = assessor.assess_api("https://api.example.com/data", auth=auth)
```

## Using the ADRI Guard

Protect your agents from bad data:

```python
from adri.integrations.guard import adri_guarded

@adri_guarded(min_score=80)
def process_customer_data(data_file):
    """This function only runs if data quality >= 80"""
    # Your agent logic here
    return process_data(data_file)

# Advanced guard with specific requirements
@adri_guarded(
    min_score=85,
    required_dimensions={
        'validity': 18,
        'completeness': 17,
        'freshness': 16
    }
)
def process_financial_data(data_file):
    """Stricter requirements for financial data"""
    return process_sensitive_data(data_file)
```

## Framework Integrations

### LangChain Integration

```python
# Requires: pip install adri[langchain]
from adri.integrations.langchain import create_adri_tool

# Create ADRI tool for LangChain
adri_tool = create_adri_tool(min_score=80)

# Add to your agent's tools
tools = [adri_tool, other_tools...]
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT)

# Agent will check data quality before processing
result = agent.run("Process the customer data file")
```

### CrewAI Integration

```python
# Requires: pip install adri[crewai]
from adri.integrations.crewai import ADRICrewAITool

# Create tool with quality requirements
adri_tool = ADRICrewAITool(
    min_overall_score=85,
    min_dimension_scores={
        'validity': 18,
        'completeness': 17
    }
)

# Add to your crew
crew = Crew(
    agents=[data_analyst],
    tasks=[analysis_task],
    tools=[adri_tool]
)
```

## Customizing Assessment

### Custom Configuration

```python
from adri import DataSourceAssessor

# Custom dimension weights
config = {
    'validity': {'weight': 1.5},      # More important
    'completeness': {'weight': 1.0},
    'freshness': {'weight': 0.8},     # Less important
    'consistency': {'weight': 1.0},
    'plausibility': {'weight': 1.2}
}

assessor = DataSourceAssessor(config=config)
report = assessor.assess_file("data.csv")
```

### Specific Dimensions Only

```python
# Assess only specific dimensions
assessor = DataSourceAssessor(
    dimensions=['validity', 'completeness', 'freshness']
)
report = assessor.assess_file("data.csv")
```

## Working with Metadata

ADRI uses companion metadata files to communicate quality information:

```python
from adri.utils.metadata_generator import MetadataGenerator
from adri.connectors import FileConnector

# Generate metadata for your data
connector = FileConnector("data.csv")
generator = MetadataGenerator(connector)

# Generate all metadata files
metadata_files = generator.generate_all_metadata()
# Creates: data.validity.json, data.completeness.json, etc.

# Generate specific metadata
validity_metadata = generator.generate_validity_metadata()
freshness_metadata = generator.generate_freshness_metadata()
```

## Batch Assessment

Assess multiple data sources from configuration:

```yaml
# assessment_config.yaml
sources:
  - name: "Customer Data"
    type: "file"
    path: "customers.csv"
    
  - name: "Orders Database"
    type: "database"
    connection: "postgresql://localhost/orders"
    table: "orders_2024"
    
  - name: "Product API"
    type: "api"
    endpoint: "https://api.example.com/products"
```

```python
from adri import DataSourceAssessor

assessor = DataSourceAssessor()
reports = assessor.assess_from_config("assessment_config.yaml")

for source_name, report in reports.items():
    print(f"{source_name}: {report.overall_score}/100")
```

## Performance Optimization

For large datasets:

```python
from adri import DataSourceAssessor

# Use sampling for large files
assessor = DataSourceAssessor(
    config={
        'sampling': {
            'enabled': True,
            'sample_size': 10000,
            'random_state': 42
        }
    }
)

report = assessor.assess_file("large_dataset.csv")
```

## Extending ADRI

### Custom Connectors

```python
from adri.connectors import BaseConnector, register_connector

@register_connector("custom_source")
class CustomConnector(BaseConnector):
    """Connector for custom data source"""
    
    def __init__(self, source_path):
        self.source_path = source_path
        
    def get_name(self):
        return f"custom:{self.source_path}"
        
    def get_type(self):
        return "custom"
        
    def get_data(self):
        # Return pandas DataFrame
        return load_custom_format(self.source_path)
        
    def get_metadata(self):
        # Return metadata dict
        return {"format": "custom", "version": "1.0"}

# Use the custom connector
assessor = DataSourceAssessor()
report = assessor.assess_with_connector("custom_source", "my_data.custom")
```

### Custom Dimensions

```python
from adri.dimensions import BaseDimensionAssessor, register_dimension

@register_dimension("custom_quality")
class CustomQualityAssessor(BaseDimensionAssessor):
    """Custom quality dimension"""
    
    def assess(self, connector):
        score = 0
        findings = []
        recommendations = []
        
        # Custom assessment logic
        data = connector.get_data()
        
        # Calculate score (0-20)
        if check_custom_quality(data):
            score = 18
        else:
            score = 10
            findings.append("Custom quality check failed")
            recommendations.append("Improve custom quality")
            
        return score, findings, recommendations

# Use with custom dimension
assessor = DataSourceAssessor(
    dimensions=['validity', 'completeness', 'custom_quality']
)
```

## Error Handling

```python
from adri import DataSourceAssessor
from adri.exceptions import AssessmentError

try:
    assessor = DataSourceAssessor()
    report = assessor.assess_file("data.csv")
except FileNotFoundError:
    print("Data file not found")
except AssessmentError as e:
    print(f"Assessment failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Next Steps

- Explore [example scripts](https://github.com/verodat/agent-data-readiness-index/tree/main/examples)
- Read about [creating templates](./CONTRIBUTING_TEMPLATES.md)
- Learn about [assessment modes](./ASSESSMENT_MODES.md)
- See [API Reference](./API_REFERENCE.md) for detailed documentation

## Purpose & Test Coverage

**Why this file exists**: Provides practical, hands-on guidance for implementing and extending ADRI, with code examples and best practices for various use cases.

**Key responsibilities**:
- Guide installation and basic usage
- Show assessment modes and template usage
- Demonstrate framework integrations
- Explain data source connections
- Provide extension patterns

**Test coverage**: This document's code examples, implementation patterns, and features should be verified by tests documented in [implementation_guide_test_coverage.md](./test_coverage/implementation_guide_test_coverage.md)
