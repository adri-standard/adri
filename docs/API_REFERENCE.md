# API Reference

This page provides a comprehensive reference for all public APIs in the Agent Data Readiness Index (ADRI) framework.

## Core Classes

### DataSourceAssessor

The main class for assessing data sources.

```python
from adri import DataSourceAssessor

assessor = DataSourceAssessor(config=None, dimensions=None)
```

#### Parameters:
- `config` (dict, optional): Configuration dictionary for customizing assessment behavior
- `dimensions` (list, optional): List of dimension names to use (defaults to all registered dimensions)

#### Methods:

##### assess_file(file_path, file_type=None)
Assess a file-based data source.

**Parameters:**
- `file_path` (str or Path): Path to the file to assess
- `file_type` (str, optional): File type override (csv, json, etc.)

**Returns:** AssessmentReport

##### assess_database(connection_string, table_name)
Assess a database table.

**Parameters:**
- `connection_string` (str): Database connection string
- `table_name` (str): Name of the table to assess

**Returns:** AssessmentReport

##### assess_api(endpoint, auth=None)
Assess an API endpoint.

**Parameters:**
- `endpoint` (str): API endpoint URL
- `auth` (dict, optional): Authentication details

**Returns:** AssessmentReport

### AssessmentReport

Contains the results of a data source assessment.

#### Attributes:
- `overall_score` (float): Overall data readiness score (0-100)
- `readiness_level` (str): Human-readable readiness level
- `dimension_results` (dict): Detailed results for each dimension
- `source_name` (str): Name of the assessed data source
- `source_type` (str): Type of the data source
- `adri_version` (str): Version of ADRI used for assessment

#### Methods:

##### save_html(filepath)
Save the assessment report as an HTML file with visualizations.

##### save_json(filepath)
Save the assessment report as a JSON file.

##### to_dict()
Convert the report to a dictionary format.

## Dimensions

### Validity

```python
from adri.dimensions import ValidityAssessor

validity = ValidityAssessor(config={})
```

### Completeness

```python
from adri.dimensions import CompletenessAssessor

completeness = CompletenessAssessor(config={})
```

### Freshness

```python
from adri.dimensions import FreshnessAssessor

freshness = FreshnessAssessor(config={})
```

### Consistency

```python
from adri.dimensions import ConsistencyAssessor

consistency = ConsistencyAssessor(config={})
```

### Plausibility

```python
from adri.dimensions import PlausibilityAssessor

plausibility = PlausibilityAssessor(config={})
```

## Rules

### Base Rule Class

All rules inherit from the `DiagnosticRule` base class:

```python
from adri.rules.base import DiagnosticRule

class CustomRule(DiagnosticRule):
    rule_id = "custom.my_rule"
    dimension = "validity"
    name = "My Custom Rule"
    description = "Description of what this rule checks"
    
    def evaluate(self, data):
        # Implementation
        pass
        
    def generate_narrative(self, result):
        # Implementation
        pass
```

### Common Rules

#### TypeConsistencyRule
```python
from adri.rules.validity import TypeConsistencyRule

rule = TypeConsistencyRule({
    'threshold': 0.9,
    'analyze_all_columns': True
})
```

#### RangeValidationRule
```python
from adri.rules.validity import RangeValidationRule

rule = RangeValidationRule({
    'min_value': 0,
    'max_value': 100,
    'columns': ['age', 'score']
})
```

#### FormatConsistencyRule
```python
from adri.rules.validity import FormatConsistencyRule

rule = FormatConsistencyRule({
    'column_formats': {
        'email': 'email',
        'phone': 'phone_us',
        'date': 'date_iso'
    }
})
```

## Guards

### DataQualityGuard

```python
from adri.integrations.guard import DataQualityGuard

guard = DataQualityGuard(
    min_overall_score=70.0,
    dimension_thresholds={
        'validity': 80.0,
        'completeness': 90.0
    }
)

# Check if data meets quality standards
is_acceptable, report = guard.check("data.csv")
```

## Connectors

### FileConnector

```python
from adri.connectors import FileConnector

connector = FileConnector("data.csv", file_type="csv")
```

### DatabaseConnector

```python
from adri.connectors import DatabaseConnector

connector = DatabaseConnector(
    connection_string="postgresql://user:pass@host/db",
    table_name="my_table"
)
```

### APIConnector

```python
from adri.connectors import APIConnector

connector = APIConnector(
    endpoint="https://api.example.com/data",
    auth={"api_key": "your-key"}
)
```

## Configuration

### Default Configuration

```python
from adri.config import Config

# Get default configuration
config = Config.default()

# Customize configuration
config.set("validity.weight", 0.25)
config.set("completeness.threshold", 0.95)
```

### Configuration Options

- `dimension.weight`: Weight for dimension in overall score (0.0-1.0)
- `dimension.threshold`: Minimum acceptable score for dimension
- `assessment.parallel`: Enable parallel rule execution
- `assessment.workers`: Number of parallel workers

## Utility Functions

### load_report(filepath)
Load a previously saved assessment report.

```python
from adri.utils import load_report

report = load_report("assessment_report.json")
```

### compare_reports(report1, report2)
Compare two assessment reports.

```python
from adri.utils import compare_reports

differences = compare_reports(old_report, new_report)
```

## Framework Integrations

### LangChain Integration

```python
from adri.integrations.langchain import ADRIDataValidator

validator = ADRIDataValidator(min_score=75.0)
# Use with LangChain document loaders
```

### CrewAI Integration

```python
from adri.integrations.crewai import ADRIDataSource

data_source = ADRIDataSource(
    source_path="data.csv",
    quality_threshold=80.0
)
```

### DSPy Integration

```python
from adri.integrations.dspy import ADRIQualityConstraint

constraint = ADRIQualityConstraint(
    min_validity=0.9,
    min_completeness=0.95
)
```

---

For more detailed examples and use cases, see:
- [Implementation Guide](./Implementation-Guide.md)
- [Framework Integrations](./INTEGRATIONS.md)
- [Extending ADRI](./EXTENDING.md)
