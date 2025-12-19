# ADRI API Reference

Complete API documentation for programmatic usage of ADRI.

## Table of Contents

1. [Decorator API](#decorator-api)
2. [Core Classes](#core-classes)
3. [Standards API](#standards-api)
4. [Configuration API](#configuration-api)
5. [Assessment API](#assessment-api)
6. [CLI API](#cli-api)
7. [Type Hints](#type-hints)
8. [Error Handling](#error-handling)

---

## Decorator API

### @adri_protected

Main decorator for protecting functions with data quality validation.

#### Signature

```python
from adri.validator.decorators import adri_protected

@adri_protected(
    standard: str,                           # Required
    data_param: str = "data",               # Optional
    min_score: float = 0.8,                 # Optional
    dimensions: Optional[Dict[str, float]] = None,  # Optional
    on_failure: str = "raise",              # Optional
    auto_generate: bool = False,            # Optional
    cache_assessments: bool = True,         # Optional
    verbose: bool = False                   # Optional
) -> Callable
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `standard` | `str` | **Required** | Name of the YAML standard to validate against |
| `data_param` | `str` | `"data"` | Function parameter name containing data to validate |
| `min_score` | `float` | `0.8` | Minimum quality score threshold (0.0-1.0) |
| `dimensions` | `Dict[str, float]` | `None` | Dimension-specific score requirements |
| `on_failure` | `str` | `"raise"` | Failure mode: `"raise"`, `"warn"`, or `"continue"` |
| `auto_generate` | `bool` | `False` | Auto-create standard if missing |
| `cache_assessments` | `bool` | `True` | Cache assessment results |
| `verbose` | `bool` | `False` | Show detailed validation logs |

#### Parameter Details

##### standard (Required)
The name of the YAML standard file (without .yaml extension).

```python
@adri_protected(contract="customer_quality")
def process_customers(data: pd.DataFrame) -> Dict:
    return {"processed": len(data)}
```

Standard will be loaded from:
- `.adri/contracts/customer_quality.yaml`
- `adri/contracts/customer_quality.yaml`
- Custom paths in config

##### data_param
Specify which function parameter contains the data to validate.

```python
@adri_protected(contract="sales_data", data_param="sales")
def analyze_sales(config: Dict, sales: pd.DataFrame) -> Dict:
    """Data is in 'sales' parameter, not 'data'."""
    return perform_analysis(sales)
```

##### min_score
Minimum acceptable quality score (0.0 to 1.0 or 0 to 100).

```python
# Require 85% overall quality
@adri_protected(contract="critical_data", min_score=0.85)
def process_critical(data: pd.DataFrame) -> Dict:
    return process(data)

# Also accepts 0-100 scale
@adri_protected(contract="critical_data", min_score=85)
def process_critical_alt(data: pd.DataFrame) -> Dict:
    return process(data)
```

##### dimensions
Set dimension-specific quality requirements.

```python
@adri_protected(
    standard="financial_data",
    dimensions={
        "completeness": 0.95,  # 95% completeness required
        "validity": 0.90,      # 90% validity required
        "consistency": 0.85    # 85% consistency required
    }
)
def process_financials(data: pd.DataFrame) -> Dict:
    return calculate_metrics(data)
```

Available dimensions:
- `completeness` - No missing/null values
- `validity` - Correct data types and formats
- `consistency` - Cross-field consistency
- `plausibility` - Reasonable value ranges
- `accuracy` - Matches reference data

##### on_failure
Control behavior when validation fails.

```python
# Raise exception (default) - stops execution
@adri_protected(contract="critical", on_failure="raise")
def process_critical(data: pd.DataFrame) -> Dict:
    return process(data)

# Log warning and continue - execution continues
@adri_protected(contract="important", on_failure="warn")
def process_important(data: pd.DataFrame) -> Dict:
    return process(data)

# Silent continue - logs to file only
@adri_protected(contract="monitoring", on_failure="continue")
def process_monitoring(data: pd.DataFrame) -> Dict:
    return process(data)
```

##### auto_generate
Automatically create standards from data if missing.

```python
@adri_protected(contract="new_dataset", auto_generate=True)
def process_new_data(data: pd.DataFrame) -> Dict:
    """
    First run: Standard is generated from data
    Future runs: Data validated against generated standard
    """
    return process(data)
```

##### cache_assessments
Enable/disable result caching for performance.

```python
# Cache results (default)
@adri_protected(contract="heavy_check", cache_assessments=True)
def expensive_validation(data: pd.DataFrame) -> Dict:
    return process(data)

# Disable caching for always-fresh validation
@adri_protected(contract="real_time", cache_assessments=False)
def real_time_check(data: pd.DataFrame) -> Dict:
    return process(data)
```

##### verbose
Show detailed validation output.

```python
@adri_protected(contract="debug_data", verbose=True)
def debug_process(data: pd.DataFrame) -> Dict:
    """Will print detailed validation logs."""
    return process(data)
```

#### Returns
Decorated function that validates data before execution.

#### Raises
- `DataQualityException`: When `on_failure="raise"` and quality < threshold
- `StandardNotFoundError`: When standard not found and `auto_generate=False`
- `ValueError`: When `data_param` not in function signature

#### Complete Examples

##### Basic Usage
```python
import pandas as pd
from adri.validator.decorators import adri_protected

@adri_protected(contract="customer_data")
def process_customers(data: pd.DataFrame) -> Dict:
    """Process customer data with quality validation."""
    return {
        "total": len(data),
        "processed": len(data[data['status'] == 'active'])
    }

# Usage
customers = pd.read_csv("customers.csv")
result = process_customers(customers)  # Validates before processing
```

##### Advanced Configuration
```python
@adri_protected(
    standard="customer_service_quality",
    data_param="tickets",
    min_score=0.8,
    dimensions={
        "completeness": 0.9,
        "validity": 0.85
    },
    on_failure="warn",
    auto_generate=False,
    cache_assessments=True,
    verbose=False
)
def process_tickets(tickets: pd.DataFrame, config: Dict) -> Dict:
    """
    Process customer service tickets with:
    - 80% overall quality required
    - 90% completeness required
    - 85% validity required
    - Warns on failure (doesn't block)
    """
    return analyze_tickets(tickets)
```

##### Multiple Validations
```python
@adri_protected(contract="input_validation", data_param="raw_data")
def load_data(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Validate input data."""
    return clean_data(raw_data)

@adri_protected(contract="output_validation", data_param="result")
def save_results(result: pd.DataFrame) -> bool:
    """Validate output data."""
    result.to_csv("output.csv")
    return True

# Chain validations
raw = pd.read_csv("input.csv")
cleaned = load_data(raw)      # Input validation
success = save_results(cleaned)  # Output validation
```

---

## Core Classes

### DataQualityAssessor

Performs multi-dimensional data quality assessment.

#### Usage

```python
from adri.validator.core.assessor import DataQualityAssessor

assessor = DataQualityAssessor()
assessment = assessor.assess(data, standard)
```

#### Methods

##### assess()

```python
def assess(
    self,
    data: Union[pd.DataFrame, dict, list],
    standard: Union[str, dict]
) -> Assessment
```

Assess data quality against a standard.

**Parameters:**
- `data`: Data to assess (DataFrame, dict, or list)
- `standard`: Standard name (str) or standard dict

**Returns:** `Assessment` object with scores and validation details

**Example:**

```python
from adri.validator.core.assessor import DataQualityAssessor
import pandas as pd

assessor = DataQualityAssessor()

data = pd.DataFrame({
    "id": [1, 2, 3],
    "email": ["user@example.com", "test@example.com", "admin@example.com"],
    "age": [25, 30, 35]
})

assessment = assessor.assess(data, "customer_standard")

print(f"Overall: {assessment.overall_score:.2f}")
print(f"Completeness: {assessment.dimension_scores['completeness']:.2f}")
print(f"Validity: {assessment.dimension_scores['validity']:.2f}")
print(f"Passed: {assessment.passed}")
```

### Assessment

Result object from data quality assessment.

#### Attributes

```python
class Assessment:
    assessment_id: str                      # Unique assessment ID
    timestamp: str                          # ISO format timestamp
    standard_name: str                      # Standard used
    overall_score: float                    # Overall score (0.0-1.0)
    dimension_scores: Dict[str, float]      # Per-dimension scores
    passed: bool                            # Whether assessment passed
    failed_validations: List[Dict]          # Failed validation rules
    metadata: Dict[str, Any]                # Additional metadata
```

#### Methods

```python
def to_dict(self) -> Dict
def to_json(self) -> str
```

**Example:**

```python
assessment = assessor.assess(data, standard)

# Check results
if assessment.passed:
    print(f"✅ Quality check passed: {assessment.overall_score:.2%}")
else:
    print(f"❌ Quality check failed: {assessment.overall_score:.2%}")
    for validation in assessment.failed_validations:
        print(f"  - {validation['rule']}: {validation['failed_count']} failures")

# Export results
report = assessment.to_dict()
json_report = assessment.to_json()
```

---

## Standards API

### StandardGenerator

Generate quality standards from sample data.

#### Usage

```python
from adri.validator.standards.generator import StandardGenerator

generator = StandardGenerator()
standard = generator.generate_from_dataframe(data, "my_standard")
```

#### Methods

##### generate_from_dataframe()

```python
def generate_from_dataframe(
    self,
    df: pd.DataFrame,
    standard_name: str,
    description: Optional[str] = None
) -> Dict
```

Generate a quality standard from a pandas DataFrame.

**Parameters:**
- `df`: Sample DataFrame to learn from
- `standard_name`: Name for the generated standard
- `description`: Optional description

**Returns:** Standard dictionary

**Example:**

```python
from adri.validator.standards.generator import StandardGenerator
import pandas as pd

generator = StandardGenerator()

# Sample data
data = pd.DataFrame({
    "customer_id": [1, 2, 3],
    "email": ["a@example.com", "b@example.com", "c@example.com"],
    "age": [25, 30, 35],
    "country": ["US", "UK", "CA"]
})

# Generate standard
standard = generator.generate_from_dataframe(
    df=data,
    standard_name="customer_quality",
    description="Customer data quality standard"
)

# Save to file
import yaml
with open(".adri/contracts/customer_quality.yaml", "w") as f:
    yaml.dump(standard, f)
```

### StandardValidator

Validate standard YAML files.

#### Usage

```python
from adri.validator.standards.validator import StandardValidator

validator = StandardValidator()
is_valid = validator.validate_file("my_standard.yaml")
```

#### Methods

##### validate_file()

```python
def validate_file(
    self,
    file_path: str
) -> bool
```

Validate a standard YAML file.

**Parameters:**
- `file_path`: Path to standard YAML file

**Returns:** True if valid, False otherwise

**Example:**

```python
from adri.validator.standards.validator import StandardValidator

validator = StandardValidator()

if validator.validate_file(".adri/contracts/customer_quality.yaml"):
    print("✅ Standard is valid")
else:
    print("❌ Standard has errors")
    for error in validator.errors:
        print(f"  - {error}")
```

### StandardLoader

Load quality standards from files.

#### Usage

```python
from adri.validator.standards.loader import StandardLoader

loader = StandardLoader()
standard = loader.load("customer_quality")
```

#### Methods

##### load()

```python
def load(
    self,
    standard_name: str
) -> Dict
```

Load a quality standard by name.

**Parameters:**
- `standard_name`: Name of standard (without .yaml)

**Returns:** Standard dictionary

**Raises:** `StandardNotFoundError` if not found

**Example:**

```python
from adri.validator.standards.loader import StandardLoader

loader = StandardLoader()

# Load standard
standard = loader.load("customer_quality")

print(f"Standard: {standard['name']}")
print(f"Version: {standard['version']}")
print(f"Dimensions: {list(standard['dimensions'].keys())}")
```

##### list_available()

```python
def list_available(self) -> List[str]
```

List all available standards.

**Returns:** List of standard names

**Example:**

```python
loader = StandardLoader()

standards = loader.list_available()
print("Available standards:")
for name in standards:
    print(f"  - {name}")
```

---

## Configuration API

### ConfigManager

Manage ADRI configuration.

#### Usage

```python
from adri.validator.config.manager import ConfigManager

config = ConfigManager()
value = config.get("standards_path")
```

#### Methods

##### get()

```python
def get(
    self,
    key: str,
    default: Any = None
) -> Any
```

Get configuration value.

**Example:**

```python
config = ConfigManager()

standards_path = config.get("standards_path")
min_score = config.get("min_score", 0.8)
on_failure = config.get("on_failure", "raise")
```

##### set()

```python
def set(
    self,
    key: str,
    value: Any
) -> None
```

Set configuration value.

**Example:**

```python
config = ConfigManager()

config.set("standards_path", "./my_standards")
config.set("min_score", 0.85)
config.set("on_failure", "warn")
```

---

## Assessment API

### assess_data_quality()

Programmatic assessment function.

#### Usage

```python
from adri.validator.core import assess_data_quality

assessment = assess_data_quality(data, "customer_quality")
```

#### Signature

```python
def assess_data_quality(
    data: Union[pd.DataFrame, dict, list],
    standard: str
) -> Assessment
```

**Parameters:**
- `data`: Data to assess
- `standard`: Standard name

**Returns:** Assessment object

**Example:**

```python
from adri.validator.core import assess_data_quality
import pandas as pd

data = pd.DataFrame({
    "id": [1, 2, 3],
    "email": ["a@example.com", "b@example.com", "c@example.com"]
})

assessment = assess_data_quality(data, "customer_quality")

if assessment.passed:
    print(f"✅ Passed: {assessment.overall_score:.2%}")
else:
    print(f"❌ Failed: {assessment.overall_score:.2%}")
    for issue in assessment.failed_validations:
        print(f"  - {issue['rule']}")
```

---

## CLI API

### Running CLI Commands Programmatically

```python
from adri.validator.cli import cli
from click.testing import CliRunner

runner = CliRunner()
result = runner.invoke(cli, ['assess', 'data.csv', '--standard', 'my_standard'])
```

**Example:**

```python
from adri.validator.cli import cli
from click.testing import CliRunner

runner = CliRunner()

# Assess data
result = runner.invoke(cli, [
    'assess',
    'customers.csv',
    '--standard', 'customer_quality'
])

print(result.output)
print(f"Exit code: {result.exit_code}")

# Generate standard
result = runner.invoke(cli, [
    'generate-standard',
    '--data', 'sample.csv',
    '--output', 'new_standard.yaml'
])

print(result.output)
```

---

## Type Hints

ADRI provides comprehensive type hints for type safety.

### Common Types

```python
from typing import Union, Optional, List, Dict, Any, Callable
import pandas as pd

# Data types
DataType = Union[pd.DataFrame, dict, list]

# Standard types
StandardType = Union[str, dict]

# Score type
ScoreType = float  # 0.0 to 1.0

# Dimension scores
DimensionScores = Dict[str, float]
```

### Decorator Type Hints

```python
from adri.validator.decorators import adri_protected
from typing import Callable, Dict
import pandas as pd

@adri_protected(contract="data_quality")
def process_data(data: pd.DataFrame) -> Dict[str, Any]:
    """Type hints work with decorator."""
    return {"status": "success"}
```

---

## Error Handling

### Exception Types

```python
from adri.validator.exceptions import (
    DataQualityException,      # Quality check failed
    StandardNotFoundError,     # Standard not found
    ValidationError,          # Validation error
    ConfigurationError        # Configuration issue
)
```

### Handling Quality Failures

```python
from adri.validator.exceptions import DataQualityException
from adri.validator.decorators import adri_protected
import pandas as pd

@adri_protected(contract="critical_data", on_failure="raise")
def process_critical(data: pd.DataFrame) -> Dict:
    return {"processed": len(data)}

try:
    result = process_critical(bad_data)
except DataQualityException as e:
    print(f"Quality check failed!")
    print(f"Score: {e.assessment.overall_score:.2%}")
    print(f"Required: {e.min_score:.2%}")
    print("\nFailed validations:")
    for validation in e.assessment.failed_validations:
        print(f"  - {validation['rule']}: {validation['severity']}")
```

### Handling Missing Standards

```python
from adri.validator.exceptions import StandardNotFoundError

try:
    result = process_data(data)
except StandardNotFoundError as e:
    print(f"Standard not found: {e.standard_name}")
    print("Hint: Use auto_generate=True or create the standard")
```

### Graceful Degradation

```python
from adri.validator.exceptions import DataQualityException

@adri_protected(contract="data_quality", on_failure="warn")
def process_with_fallback(data: pd.DataFrame) -> Dict:
    """Logs warning but continues on quality failure."""
    return process(data)

# Or handle exceptions manually
@adri_protected(contract="data_quality", on_failure="raise")
def process_with_manual_handling(data: pd.DataFrame) -> Dict:
    return process(data)

try:
    result = process_with_manual_handling(data)
except DataQualityException:
    # Fallback to less strict processing
    result = process_lenient(data)
```

---

## Complete Working Examples

### Example 1: Basic Decorator Usage

```python
import pandas as pd
from adri.validator.decorators import adri_protected

@adri_protected(contract="customer_data")
def process_customers(data: pd.DataFrame) -> Dict:
    """Process customer data with quality validation."""
    return {
        "total": len(data),
        "active": len(data[data['status'] == 'active'])
    }

# Load and process
customers = pd.read_csv("customers.csv")
result = process_customers(customers)
print(result)
```

### Example 2: Generate and Use Standard

```python
from adri.validator.standards.generator import StandardGenerator
from adri.validator.decorators import adri_protected
import pandas as pd
import yaml

# Step 1: Generate standard from good data
good_data = pd.DataFrame({
    "id": [1, 2, 3],
    "email": ["a@example.com", "b@example.com", "c@example.com"],
    "age": [25, 30, 35]
})

generator = StandardGenerator()
standard = generator.generate_from_dataframe(
    df=good_data,
    standard_name="customer_quality",
    description="Customer data quality standard"
)

# Save standard
with open(".adri/contracts/customer_quality.yaml", "w") as f:
    yaml.dump(standard, f)

# Step 2: Use standard with decorator
@adri_protected(contract="customer_quality")
def process_customers(data: pd.DataFrame) -> Dict:
    return {"processed": len(data)}

# Step 3: Process new data
new_data = pd.read_csv("new_customers.csv")
result = process_customers(new_data)  # Validates against standard
```

### Example 3: Programmatic Assessment

```python
from adri.validator.core.assessor import DataQualityAssessor
from adri.validator.standards.loader import StandardLoader
import pandas as pd

# Load standard
loader = StandardLoader()
standard = loader.load("customer_quality")

# Create assessor
assessor = DataQualityAssessor()

# Assess data
data = pd.read_csv("customers.csv")
assessment = assessor.assess(data, standard)

# Process results
if assessment.passed:
    print(f"✅ Quality passed: {assessment.overall_score:.2%}")
    # Continue with data processing
    process_data(data)
else:
    print(f"❌ Quality failed: {assessment.overall_score:.2%}")
    print("\nDimension Scores:")
    for dim, score in assessment.dimension_scores.items():
        print(f"  {dim}: {score:.2%}")

    print("\nFailed Validations:")
    for validation in assessment.failed_validations:
        print(f"  - {validation['rule']}: {validation['failed_count']} failures")
```

### Example 4: Batch Processing with Quality Checks

```python
from adri.validator.decorators import adri_protected
import pandas as pd
import glob

@adri_protected(
    standard="invoice_data",
    on_failure="warn",  # Continue on failure but log
    min_score=0.85
)
def process_invoice(data: pd.DataFrame, file_name: str) -> Dict:
    """Process single invoice file."""
    return {
        "file": file_name,
        "total_amount": data['amount'].sum(),
        "invoice_count": len(data)
    }

# Process all invoices
results = []
for file_path in glob.glob("invoices/*.csv"):
    data = pd.read_csv(file_path)
    result = process_invoice(data, file_path)
    results.append(result)

# Summary
total_processed = len(results)
total_amount = sum(r['total_amount'] for r in results)
print(f"Processed {total_processed} files")
print(f"Total amount: ${total_amount:,.2f}")
```

---

## Next Steps

- **[Getting Started](GETTING_STARTED.md)** - Hands-on tutorial
- **[Open-Source Features](OPEN_SOURCE_FEATURES.md)** - Complete feature reference
- **[CLI Reference](CLI_REFERENCE.md)** - CLI command details
- **[How It Works](HOW_IT_WORKS.md)** - Quality dimensions explained
- **[Examples](../examples/README.md)** - Working code examples

---

**Questions?** See [FAQ.md](FAQ.md) or open an issue on GitHub.
