# ADRI Implementation Guide

This guide provides practical instructions for implementing and extending the Agent Data Readiness Index (ADRI) system.

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/ThinkEvolveSolve/agent-data-readiness-index.git
cd agent-data-readiness-index

# Install dependencies
pip install -e .
```

### Basic Usage

```python
from adri import ADRIAssessor
from adri.datasource import CSVDataSource

# Create a data source
data_source = CSVDataSource("path/to/your/data.csv")

# Initialize the assessor
assessor = ADRIAssessor()

# Run the assessment
report = assessor.assess(data_source)

# Output the report
print(report.summary())
report.save_html("assessment_report.html")
```

## Creating Custom Rules

### Basic Rule Structure

Create a new rule by extending the `DiagnosticRule` base class:

```python
from adri.rules import DiagnosticRule
from adri.dimensions import Validity

class EmailFormatRule(DiagnosticRule):
    """Rule to check if email addresses follow correct format."""
    
    def __init__(self):
        super().__init__(
            name="email_format",
            dimension=Validity,
            description="Validates email format",
            severity=2  # 1-5 scale, 5 being most severe
        )
    
    def validate(self, data, column_name="email"):
        """Apply validation rule to the specified column."""
        import re
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        
        # Check each value in the column
        results = []
        for idx, value in enumerate(data[column_name]):
            if not isinstance(value, str) or not re.match(email_pattern, value):
                results.append({
                    "row": idx,
                    "value": value,
                    "message": f"Invalid email format: {value}"
                })
        
        return results
```

### Registering Custom Rules

Register your custom rules with the rule registry:

```python
from adri.registry import RuleRegistry
from custom_rules import EmailFormatRule

# Get the registry
registry = RuleRegistry()

# Register your custom rule
registry.register(EmailFormatRule())

# Use the registry with the assessor
assessor = ADRIAssessor(registry=registry)
```

## Working with Dimensions

Each dimension has specific characteristics:

### Validity Rules

Validity rules check whether data conforms to specific formats or constraints.

```python
from adri.rules import DiagnosticRule
from adri.dimensions import Validity

class NumericRangeRule(DiagnosticRule):
    """Ensures numeric values are within specified range."""
    
    def __init__(self, min_value, max_value):
        super().__init__(
            name="numeric_range",
            dimension=Validity,
            description=f"Validates values between {min_value} and {max_value}"
        )
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, data, column_name):
        results = []
        for idx, value in enumerate(data[column_name]):
            try:
                num_value = float(value)
                if num_value < self.min_value or num_value > self.max_value:
                    results.append({
                        "row": idx,
                        "value": value,
                        "message": f"Value {value} outside range [{self.min_value}, {self.max_value}]"
                    })
            except (ValueError, TypeError):
                results.append({
                    "row": idx,
                    "value": value,
                    "message": f"Value {value} is not numeric"
                })
        
        return results
```

### Plausibility Rules

Plausibility rules identify statistically unlikely or logically improbable values.

### Completeness Rules

Completeness rules check for missing values or insufficient data coverage.

### Freshness Rules

Freshness rules evaluate the timeliness of data.

### Consistency Rules

Consistency rules validate relationships between data points.

## Customizing the Configuration

The configuration system allows for flexible adjustments:

```python
from adri import Config

# Load existing configuration
config = Config.load("config.yaml")

# Modify configuration
config.set("threshold.validity", 0.95)
config.set("rules.email_format.severity", 3)

# Save modified configuration
config.save("custom_config.yaml")

# Use custom configuration
assessor = ADRIAssessor(config=config)
```

## Working with Different Data Sources

ADRI supports various data sources:

### CSV Files

```python
from adri.datasource import CSVDataSource

data_source = CSVDataSource("data.csv", delimiter=",", encoding="utf-8")
```

### Database Connections

```python
from adri.datasource import SQLDataSource

connection_string = "postgresql://username:password@localhost:5432/mydatabase"
data_source = SQLDataSource(connection_string, query="SELECT * FROM users")
```

### API Endpoints

```python
from adri.datasource import APIDataSource

data_source = APIDataSource(
    url="https://api.example.com/data",
    headers={"Authorization": "Bearer token"},
    method="GET"
)
```

## Extending Assessment Reports

Customize report generation:

```python
from adri.report import ReportGenerator

class CustomReportGenerator(ReportGenerator):
    """Custom report generator with additional visualizations."""
    
    def generate_html(self, results):
        """Generate HTML report with custom visualizations."""
        # Custom report generation logic
        html = super().generate_html(results)
        
        # Add custom visualizations
        import matplotlib.pyplot as plt
        import io
        import base64
        
        # Create visualization
        plt.figure(figsize=(10, 6))
        # ... plotting code ...
        
        # Convert plot to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        # Insert into HTML
        custom_visual = f'<img src="data:image/png;base64,{img_str}" />'
        html = html.replace('</body>', f'{custom_visual}</body>')
        
        return html
```

## Advanced Configuration

### Rule Weights and Thresholds

Configure how different rules contribute to dimension scores:

```yaml
# config.yaml
dimensions:
  validity:
    threshold: 0.9
    rules:
      email_format:
        weight: 2.0
      numeric_range:
        weight: 1.0
        
  completeness:
    threshold: 0.95
```

### Environment-Specific Settings

Configure different settings for development, testing, and production:

```python
from adri import Config

# Load environment-specific configuration
env = os.getenv("ENVIRONMENT", "development")
config = Config.load(f"config.{env}.yaml")

# Initialize with environment-specific configuration
assessor = ADRIAssessor(config=config)
```

## Performance Optimization

For large datasets, optimize performance:

```python
# Enable parallel processing
assessor = ADRIAssessor(parallel=True, workers=4)

# Use sampling for initial assessment
report = assessor.assess(data_source, sample_size=1000)

# Get problematic areas and focus detailed assessment
problem_columns = report.get_problematic_columns()
detailed_report = assessor.assess(data_source, columns=problem_columns)

## Purpose & Test Coverage

**Why this file exists**: Provides practical, hands-on guidance for implementing and extending ADRI, with code examples and best practices for various use cases.

**Key responsibilities**:
- Guide installation and basic usage
- Show how to create custom rules for each dimension
- Demonstrate configuration customization
- Explain integration with different data sources
- Provide performance optimization strategies

**Test coverage**: This document's code examples, implementation patterns, and features should be verified by tests documented in [implementation_guide_test_coverage.md](./test_coverage/implementation_guide_test_coverage.md)
