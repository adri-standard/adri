# Agent Data Readiness Index (ADRI)

ADRI is a framework for assessing the quality and readiness of data for AI agent consumption and processing. It provides a structured approach to evaluating data quality across multiple dimensions, helping AI systems make informed decisions about the reliability of their data sources.

## Features

- **Multi-dimensional assessment**: Evaluate data quality across Validity, Completeness, Plausibility, Freshness, and Consistency
- **Flexible data sources**: Connect to CSV files, SQL databases, and REST APIs
- **Extensible rule system**: Create custom diagnostic rules for domain-specific requirements
- **Configurable thresholds**: Set appropriate quality thresholds for different dimensions
- **Detailed reporting**: Get comprehensive reports on data quality issues with specific examples
- **Overall quality score**: Calculate a weighted data readiness score

## Installation

```bash
# Basic installation
pip install adri

# With SQL support
pip install adri[sql]

# For development
pip install adri[dev]
```

Alternatively, you can install from the source:

```bash
git clone https://github.com/ThinkEvolveSolve/agent-data-readiness-index.git
cd agent-data-readiness-index
pip install -e .
```

## Quick Start

```python
from adri import ADRIAssessor, Config
from adri.datasource import CSVDataSource
from adri.rules.validity_rules import EmailFormatRule, NumericRangeRule

# Create a data source
data_source = CSVDataSource("data.csv")

# Create a configuration
config = Config.default()

# Create an assessor with custom rules
assessor = ADRIAssessor(config)

# Register some rules
assessor.registry.register(EmailFormatRule(severity=4))
assessor.registry.register(NumericRangeRule(min_value=0, max_value=100))

# Run the assessment
results = assessor.assess(data_source)

# Print the overall score
print(f"Overall Data Readiness Score: {results['overall_score']:.2f}")

# Print dimension scores
for dimension, result in results["dimension_scores"].items():
    print(f"{dimension} Score: {result['score']:.2f}")
```

## Core Concepts

### Dimensions

ADRI evaluates data quality across five key dimensions:

1. **Validity**: Does the data conform to defined formats and types?
2. **Completeness**: Is all expected data present?
3. **Plausibility**: Does the data appear reasonable and likely to be correct?
4. **Freshness**: Is the data timely and current?
5. **Consistency**: Is the data internally coherent and aligned?

### Diagnostic Rules

Rules are specific tests applied to data that check for particular quality aspects. For example:

- Email format validation (Validity)
- Required field checks (Completeness)
- Statistical outlier detection (Plausibility)
- Last update verification (Freshness)
- Cross-field consistency checks (Consistency)

### Data Sources

ADRI supports multiple data sources:

- **CSVDataSource**: For CSV files
- **SQLDataSource**: For SQL databases 
- **APIDataSource**: For REST API endpoints

### Assessment Process

1. Configure the assessor with appropriate rules and settings
2. Connect to a data source
3. Run the assessment
4. Analyze the results and address identified issues

## Advanced Usage

### Creating Custom Rules

```python
from adri.rules.base import DiagnosticRule
from adri.dimensions import Validity
import pandas as pd

class ZipCodeFormatRule(DiagnosticRule):
    def __init__(self, severity=3, weight=1.0, enabled=True):
        super().__init__(
            name="zip_code_format",
            dimension=Validity,
            description="Validates that zip codes follow the correct format",
            severity=severity,
            weight=weight,
            enabled=enabled
        )
        
    def validate(self, data: pd.DataFrame, column: str = "zip_code", **kwargs) -> list:
        results = []
        for idx, value in enumerate(data[column]):
            if pd.isna(value):
                continue
                
            # Simple US zip code validation (5 digits or 5+4)
            if not isinstance(value, str) or not (
                (len(value) == 5 and value.isdigit()) or
                (len(value) == 10 and value[5] == '-' and 
                 value[:5].isdigit() and value[6:].isdigit())
            ):
                results.append({
                    "row": idx,
                    "column": column,
                    "value": str(value),
                    "message": f"Invalid zip code format: {value}"
                })
        
        return results
```

### Using SQL Data Source

```python
from adri import ADRIAssessor
from adri.datasource import SQLDataSource

# Create a SQL data source
data_source = SQLDataSource(
    connection_string="postgresql://user:password@localhost:5432/mydb",
    query="SELECT * FROM customers WHERE registration_date > '2022-01-01'"
)

# Run assessment
assessor = ADRIAssessor()
results = assessor.assess(data_source)
```

### Parallel Rule Execution

```python
from adri import ADRIAssessor, Config

# Create a configuration with parallel processing enabled
config = Config.default()
config.set("assessment.parallel", True)
config.set("assessment.workers", 8)

# Create an assessor with this configuration
assessor = ADRIAssessor(config=config)
```

### Using Plausibility Rules

```python
from adri import ADRIAssessor
from adri.datasource import CSVDataSource
from adri.rules.plausibility import OutlierDetectionRule, RangeCheckRule, PatternFrequencyRule

# Create a data source
data_source = CSVDataSource("customer_data.csv")

# Create and register rules
assessor = ADRIAssessor()

# Detect outliers in numeric data
assessor.registry.register(OutlierDetectionRule(params={
    "column": "transaction_amount",
    "method": "zscore",
    "threshold": 3.0,
    "weight": 1.0
}))

# Check if ages are within plausible range
assessor.registry.register(RangeCheckRule(params={
    "column": "age",
    "min_value": 0,
    "max_value": 120,
    "weight": 1.2
}))

# Analyze frequency distribution of categories
assessor.registry.register(PatternFrequencyRule(params={
    "column": "country",
    "max_categories": 200,
    "min_frequency": 0.001,
    "max_frequency": 0.5,
    "weight": 0.8
}))

# Run the assessment
results = assessor.assess(data_source)
```

## Examples

Check the `examples/` directory for complete working examples:

- `basic_assessment.py`: Shows basic usage with a CSV data source
- `plausibility_assessment.py`: Demonstrates statistical plausibility checks using outlier detection, distribution analysis, range checks, and pattern frequency analysis
- `consistency_assessment.py`: Shows how to validate internal consistency between data elements
- `comprehensive_assessment.py`: Integration of all dimensions in a real-world data quality assessment scenario

## Documentation

For full documentation, visit [our documentation site](https://github.com/ThinkEvolveSolve/agent-data-readiness-index).

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

ADRI is released under the MIT License. See the [LICENSE](LICENSE) file for details.
