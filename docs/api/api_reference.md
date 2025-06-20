# API Reference

This page provides a comprehensive reference for all public APIs in the Agent Data Readiness Index (ADRI) framework.

## Core Classes

### DataSourceAssessor

The main class for assessing data sources.

```python
<!-- audience: ai-builders -->
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

##### assess_file(file_path, file_type=None, template=None)
Assess a file-based data source using template-based scoring.

**Parameters:**
- `file_path` (str or Path): Path to the file to assess
- `file_type` (str, optional): File type override (csv, json, etc.)
- `template` (str or BaseTemplate, optional): Template to use for assessment (defaults to general/default-v1.0.0)

**Returns:** AssessmentReport

**Note:** All assessments now use templates internally. The default template provides balanced scoring with each dimension's rules weighted to sum to 20 points, normalized to 0-100.

##### assess_with_template(file_path, template_path)
Assess a file-based data source against a specific template.

**Parameters:**
- `file_path` (str or Path): Path to the file to assess
- `template_path` (str or Path): Path to the template YAML file

**Returns:** Tuple[AssessmentReport, TemplateEvaluation]
- AssessmentReport: Standard assessment results with weighted scoring
- TemplateEvaluation: Template compliance status and gaps

**Note**: When using templates, each dimension's rules are weighted and sum to 20 points. The overall score is normalized to 0-100.

##### assess_database(connection_string, table_name, template=None)
Assess a database table using template-based scoring.

**Parameters:**
- `connection_string` (str): Database connection string
- `table_name` (str): Name of the table to assess
- `template` (str or BaseTemplate, optional): Template to use for assessment (defaults to general/default-v1.0.0)

**Returns:** AssessmentReport

##### assess_api(endpoint, auth=None, template=None)
Assess an API endpoint using template-based scoring.

**Parameters:**
- `endpoint` (str): API endpoint URL
- `auth` (dict, optional): Authentication details
- `template` (str or BaseTemplate, optional): Template to use for assessment (defaults to general/default-v1.0.0)

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

All dimension classes support template-based rule configuration through the `set_template_rules()` method.

### Validity

```python
<!-- audience: ai-builders -->
from adri.dimensions import ValidityAssessor

validity = ValidityAssessor(config={})

# Set template rules with weights
validity.set_template_rules([
    {
        'type': 'type_consistency',
        'params': {'weight': 10, 'threshold': 0.95}
    },
    {
        'type': 'range_validation',
        'params': {'weight': 10, 'min_value': 0, 'max_value': 1000}
    }
])
```

### Completeness

```python
<!-- audience: ai-builders -->
from adri.dimensions import CompletenessAssessor

completeness = CompletenessAssessor(config={})

# Set template rules with weights
completeness.set_template_rules([
    {
        'type': 'required_fields',
        'params': {'weight': 15, 'required_columns': ['id', 'name']}
    },
    {
        'type': 'population_density',
        'params': {'weight': 5, 'threshold': 0.9}
    }
])
```

### Freshness

```python
<!-- audience: ai-builders -->
from adri.dimensions import FreshnessAssessor

freshness = FreshnessAssessor(config={})

# Set template rules with weights
freshness.set_template_rules([
    {
        'type': 'timestamp_recency',
        'params': {'weight': 10, 'timestamp_column': 'date', 'max_age_days': 30}
    },
    {
        'type': 'update_frequency',
        'params': {'weight': 10, 'timestamp_column': 'modified', 'expected_frequency_days': 1}
    }
])
```

### Consistency

```python
<!-- audience: ai-builders -->
from adri.dimensions import ConsistencyAssessor

consistency = ConsistencyAssessor(config={})

# Set template rules with weights
consistency.set_template_rules([
    {
        'type': 'cross_field',
        'params': {'weight': 12, 'validation_type': 'comparison', 'fields': ['start', 'end']}
    },
    {
        'type': 'uniform_representation',
        'params': {'weight': 8, 'column': 'currency', 'pattern': '^[A-Z]{3}$'}
    }
])
```

### Plausibility

```python
<!-- audience: ai-builders -->
from adri.dimensions import PlausibilityAssessor

plausibility = PlausibilityAssessor(config={})

# Set template rules with weights
plausibility.set_template_rules([
    {
        'type': 'range',
        'params': {'weight': 15, 'column': 'amount', 'min_value': 0.01, 'max_value': 10000}
    },
    {
        'type': 'outlier',
        'params': {'weight': 5, 'column': 'amount', 'method': 'iqr', 'threshold': 3.0}
    }
])
```

### Template Rule Weights

When using templates:
- Each dimension's rules must have weights that sum to 20 points
- Weights represent the importance of each rule within the dimension
- The overall score is normalized to 0-100 for consistency
- Dimension scores are calculated as: `(earned_points / 20) * 100`

## Rules

### Base Rule Class

All rules inherit from the `DiagnosticRule` base class:

```python
<!-- audience: ai-builders -->
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
<!-- audience: ai-builders -->
from adri.rules.validity import TypeConsistencyRule

rule = TypeConsistencyRule({
    'threshold': 0.9,
    'analyze_all_columns': True
})
```

#### RangeValidationRule
```python
<!-- audience: ai-builders -->
from adri.rules.validity import RangeValidationRule

rule = RangeValidationRule({
    'min_value': 0,
    'max_value': 100,
    'columns': ['age', 'score']
})
```

#### FormatConsistencyRule
```python
<!-- audience: ai-builders -->
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

### adri_guarded Decorator

```python
<!-- audience: ai-builders -->
# Example of using the adri_guarded decorator (not meant to be executed)
from adri.integrations.guard import adri_guarded

# Apply as a decorator to functions that process data
@adri_guarded(
    min_score=70.0, 
    dimensions={
        'validity': 15.0,
        'completeness': 18.0
    },
    use_cached_reports=True
)
def process_data(data_source, other_param):
    # This function will only run if data quality is sufficient
    # Otherwise, it will raise a ValueError
    pass

# In your actual code:
# process_data("data.csv", "other_value")
```

## Connectors

### FileConnector

```python
<!-- audience: ai-builders -->
from adri.connectors import FileConnector

connector = FileConnector("data.csv", file_type="csv")
```

### DatabaseConnector

```python
<!-- audience: ai-builders -->
from adri.connectors import DatabaseConnector

connector = DatabaseConnector(
    connection_string="postgresql://user:pass@host/db",
    table_name="my_table"
)
```

### APIConnector

```python
<!-- audience: ai-builders -->
from adri.connectors import APIConnector

connector = APIConnector(
    endpoint="https://api.example.com/data",
    auth={"api_key": "your-key"}
)
```

## Configuration

### Configuration Management

```python
<!-- audience: ai-builders -->
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
<!-- audience: ai-builders -->
from adri.utils import load_report

report = load_report("assessment_report.json")
```

### compare_reports(report1, report2)
Compare two assessment reports.

```python
<!-- audience: ai-builders -->
from adri.utils import compare_reports

differences = compare_reports(old_report, new_report)
```

## Framework Integrations

### LangChain Integration

```python
<!-- audience: ai-builders -->
from adri.integrations.langchain import ADRIDataValidator

validator = ADRIDataValidator(min_score=75.0)
# Use with LangChain document loaders
```

### CrewAI Integration

```python
<!-- audience: ai-builders -->
from adri.integrations.crewai import ADRIDataSource

data_source = ADRIDataSource(
    source_path="data.csv",
    quality_threshold=80.0
)
```

### DSPy Integration

```python
<!-- audience: ai-builders -->
from adri.integrations.dspy import ADRIQualityConstraint

constraint = ADRIQualityConstraint(
    min_validity=0.9,
    min_completeness=0.95
)
```

---

For more detailed examples and use cases, see:
- [Implementation Guide](guides/implementation-guide.md)
- [Framework Integrations](INTEGRATIONS.md)
- [Extending ADRI](EXTENDING.md)

## Purpose & Test Coverage

**Why this file exists**: Provides comprehensive technical reference documentation for all public APIs, classes, methods, and configuration options in the ADRI framework.

**Key responsibilities**:
- Document all public APIs with clear parameter descriptions and return types
- Provide code examples for each major component
- Serve as the authoritative reference for developers
- Maintain consistency with actual implementation

**Test coverage**: This document's examples, claims, and features should be verified by tests documented in [API_REFERENCE_test_coverage.md](test_coverage/API_REFERENCE_test_coverage.md)
