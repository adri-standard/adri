# API Reference

This page provides a comprehensive reference for all public APIs in the Agent Data Readiness Index (ADRI) framework.

## Core Classes

### DataSourceAssessor

The main class for assessing data sources.

```python
from adri import DataSourceAssessor
from adri.assessment_modes import AssessmentMode

# Default (Auto mode)
assessor = DataSourceAssessor(config=None, dimensions=None, mode=AssessmentMode.AUTO)

# Explicit Discovery mode
assessor = DataSourceAssessor(mode=AssessmentMode.DISCOVERY)

# Explicit Validation mode  
assessor = DataSourceAssessor(mode=AssessmentMode.VALIDATION)
```

#### Parameters:
- `config` (dict, optional): Configuration dictionary for customizing assessment behavior
- `dimensions` (list, optional): List of dimension names to use (defaults to all registered dimensions)
- `mode` (AssessmentMode or str, optional): Assessment mode - 'auto', 'discovery', or 'validation' (defaults to 'auto')

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
- `assessment_mode` (str): Mode used for assessment ('discovery' or 'validation')
- `mode_config` (dict): Configuration settings used for the assessment mode

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

### Configuration Management

```python
from adri.config import Configuration, get_config, set_config

# Create a custom configuration
config = Configuration({
    "validity": {"weight": 0.25},
    "completeness": {"threshold": 0.95}
})

# Get current global configuration
current_config = get_config()

# Set global configuration
set_config(config)

# Pass configuration to assessor
assessor = DataSourceAssessor(config={
    "validity": {"weight": 0.3},
    "completeness": {"min_score": 80}
})
```

### Configuration Options

- `dimension.weight`: Weight for dimension in overall score (0.0-1.0)
- `dimension.threshold`: Minimum acceptable score for dimension
- `dimension.min_score`: Minimum required score for dimension
- `assessment.parallel`: Enable parallel rule execution
- `assessment.workers`: Number of parallel workers
- `business_logic_enabled`: Enable business-specific rules (Discovery mode)
- `require_explicit_metadata`: Require metadata files (Validation mode)

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
- [Implementation Guide](./implementation_guide.md)
- [Framework Integrations](./INTEGRATIONS.md)
- [Extending ADRI](./EXTENDING.md)

## Purpose & Test Coverage

**Why this file exists**: Provides comprehensive technical reference documentation for all public APIs, classes, methods, and configuration options in the ADRI framework.

**Key responsibilities**:
- Document all public APIs with clear parameter descriptions and return types
- Provide code examples for each major component
- Serve as the authoritative reference for developers
- Maintain consistency with actual implementation

**Test coverage**: This document's examples, claims, and features should be verified by tests documented in [API_REFERENCE_test_coverage.md](./test_coverage/API_REFERENCE_test_coverage.md)
