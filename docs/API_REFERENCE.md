# ADRI API Reference

Complete API documentation for programmatic usage.

## Table of Contents

1. [Decorator API](#decorator-api)
2. [Core Classes](#core-classes)
3. [Standards API](#standards-api)
4. [Configuration API](#configuration-api)
5. [Assessment API](#assessment-api)
6. [CLI API](#cli-api)

## Decorator API

### adri_protected

Main decorator for protecting functions with data quality validation.

```python
from adri import adri_protected

@adri_protected(
    data_param: str,
    standard: Optional[str] = None,
    mode: str = "block",
    auto_generate: bool = True,
    min_score: float = 80.0
) -> Callable
```

**Parameters:**

- `data_param` (str, required): Name of the parameter containing data to validate
- `standard` (str, optional): Name of quality standard to use. If not provided, auto-generates from function and parameter names
- `mode` (str, optional): Guard mode - "block" (raises exception) or "warn" (logs warning). Default: "block"
- `auto_generate` (bool, optional): Auto-generate standard if not found. Default: True
- `min_score` (float, optional): Minimum acceptable quality score (0-100). Default: 80.0

**Returns:** Decorated function

**Raises:**
- `DataQualityException`: When data quality is below threshold (block mode only)
- `StandardNotFoundError`: When standard not found and auto_generate=False
- `ValueError`: When data_param not found in function signature

**Example:**

```python
@adri_protected(standard="customer_data", data_param="customers")
def process_customers(customers):
    """Process customer data."""
    return analyze(customers)

@adri_protected(
    data_param="transactions",
    standard="financial_standard",
    on_failure="warn",
    min_score=90.0
)
def process_transactions(transactions):
    """Process financial transactions."""
    return validate(transactions)
```

## Core Classes

### DataQualityAssessor

Performs multi-dimensional data quality assessment.

```python
from adri.validator.core.assessor import DataQualityAssessor

assessor = DataQualityAssessor()
assessment = assessor.assess(data, standard)
```

**Methods:**

#### assess

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

**Returns:** Assessment object with scores and details

**Example:**

```python
from adri.validator.core.assessor import DataQualityAssessor
import pandas as pd

# Create assessor
assessor = DataQualityAssessor()

# Prepare data
data = pd.DataFrame({
    "id": [1, 2, 3],
    "email": ["user@example.com", "test@example.com", "admin@example.com"]
})

# Assess
assessment = assessor.assess(data, "customer_standard")

# Access results
print(f"Overall score: {assessment.overall_score}")
print(f"Validity: {assessment.validity_score}")
print(f"Completeness: {assessment.completeness_score}")
```

### Assessment

Result of data quality assessment.

**Attributes:**

```python
class Assessment:
    overall_score: float          # 0-100
    validity_score: float         # 0-20
    completeness_score: float     # 0-20
    consistency_score: float      # 0-20
    accuracy_score: float         # 0-20
    timeliness_score: float       # 0-20
    issues: List[Issue]           # List of quality issues
    passed: bool                  # Whether assessment passed
    standard_name: str            # Standard used
    standard_version: str         # Standard version
```

**Methods:**

```python
def to_dict(self) -> dict
def to_json(self) -> str
def to_yaml(self) -> str
```

**Example:**

```python
assessment = assessor.assess(data, standard)

# Check if passed
if assessment.passed:
    print("Quality check passed!")
else:
    print(f"Quality check failed: {assessment.overall_score}/100")

# Get details
for issue in assessment.issues:
    print(f"- {issue.dimension}: {issue.description}")

# Export
report_dict = assessment.to_dict()
report_json = assessment.to_json()
```

### DataProtectionEngine

Orchestrates the protection workflow.

```python
from adri.validator.core.protection import DataProtectionEngine

engine = DataProtectionEngine()
result = engine.protect(func, data, config)
```

**Methods:**

#### protect

```python
def protect(
    self,
    func: Callable,
    data: Any,
    config: ProtectionConfig
) -> Any
```

Protect function execution with quality validation.

**Parameters:**
- `func`: Function to protect
- `data`: Data to validate
- `config`: Protection configuration

**Returns:** Function result if validation passes

**Raises:** DataQualityException if validation fails

## Standards API

### StandardGenerator

Generate quality standards from data.

```python
from adri.validator.analysis.standard_generator import StandardGenerator

generator = StandardGenerator()
standard = generator.generate(data, name="my_standard")
```

**Methods:**

#### generate

```python
def generate(
    self,
    data: Union[pd.DataFrame, dict, list],
    name: str,
    description: Optional[str] = None,
    version: str = "1.0.0",
    strict: bool = False
) -> dict
```

Generate a quality standard from data.

**Parameters:**
- `data`: Sample data to learn from
- `name`: Standard name
- `description`: Optional description
- `version`: Version string (default: "1.0.0")
- `strict`: Generate strict rules (tighter ranges)

**Returns:** Standard dictionary

**Example:**

```python
from adri.validator.analysis.standard_generator import StandardGenerator
import pandas as pd

generator = StandardGenerator()

data = pd.DataFrame({
    "customer_id": [1, 2, 3],
    "email": ["a@example.com", "b@example.com", "c@example.com"],
    "age": [25, 30, 35]
})

standard = generator.generate(
    data=data,
    name="customer_standard",
    description="Customer data quality standard",
    strict=True
)

# Save standard
generator.save(standard, "ADRI/dev/standards/customer_standard.yaml")
```

### StandardLoader

Load quality standards from files.

```python
from adri.validator.standards.loader import StandardLoader

loader = StandardLoader()
standard = loader.load("my_standard")
```

**Methods:**

#### load

```python
def load(
    self,
    standard_name: str,
    paths: Optional[List[str]] = None
) -> dict
```

Load a quality standard.

**Parameters:**
- `standard_name`: Name of standard to load
- `paths`: Optional list of paths to search

**Returns:** Standard dictionary

**Raises:** StandardNotFoundError if standard not found

**Example:**

```python
from adri.validator.standards.loader import StandardLoader

loader = StandardLoader()

# Load from default paths
standard = loader.load("customer_standard")

# Load from custom paths
standard = loader.load("custom_standard", paths=["/custom/path"])

# Access standard
print(f"Standard: {standard['name']} v{standard['version']}")
print(f"Fields: {list(standard['fields'].keys())}")
```

#### list_standards

```python
def list_standards(
    self,
    paths: Optional[List[str]] = None
) -> List[str]
```

List available standards.

**Parameters:**
- `paths`: Optional list of paths to search

**Returns:** List of standard names

**Example:**

```python
loader = StandardLoader()

# List all available standards
standards = loader.list_standards()
for name in standards:
    print(f"- {name}")
```

### DataProfiler

Profile data to extract patterns and statistics.

```python
from adri.validator.analysis.data_profiler import DataProfiler

profiler = DataProfiler()
profile = profiler.profile(data)
```

**Methods:**

#### profile

```python
def profile(
    self,
    data: Union[pd.DataFrame, dict, list]
) -> DataProfile
```

Profile data structure and content.

**Parameters:**
- `data`: Data to profile

**Returns:** DataProfile object

**Example:**

```python
from adri.validator.analysis.data_profiler import DataProfiler
import pandas as pd

profiler = DataProfiler()

data = pd.DataFrame({
    "id": [1, 2, 3],
    "email": ["user@example.com", "test@example.com", "admin@example.com"],
    "age": [25, 30, 35]
})

profile = profiler.profile(data)

# Access profile
print(f"Rows: {profile.row_count}")
print(f"Columns: {profile.column_count}")

for field_name, field_profile in profile.fields.items():
    print(f"{field_name}:")
    print(f"  Type: {field_profile.inferred_type}")
    print(f"  Null rate: {field_profile.null_rate}")
    if field_profile.inferred_type == "integer":
        print(f"  Range: {field_profile.min_value} - {field_profile.max_value}")
```

## Configuration API

### ConfigManager

Manage ADRI configuration.

```python
from adri.validator.config.manager import ConfigManager

config = ConfigManager()
value = config.get("standards_path")
```

**Methods:**

#### get

```python
def get(
    self,
    key: str,
    default: Any = None
) -> Any
```

Get configuration value.

**Parameters:**
- `key`: Configuration key
- `default`: Default value if key not found

**Returns:** Configuration value

**Example:**

```python
from adri.validator.config.manager import ConfigManager

config = ConfigManager()

# Get configuration
standards_path = config.get("standards_path")
log_level = config.get("log_level", "INFO")
min_score = config.get("min_score", 80.0)

print(f"Standards path: {standards_path}")
print(f"Log level: {log_level}")
print(f"Min score: {min_score}")
```

#### set

```python
def set(
    self,
    key: str,
    value: Any
) -> None
```

Set configuration value.

**Parameters:**
- `key`: Configuration key
- `value`: Configuration value

**Example:**

```python
config = ConfigManager()

# Set configuration
config.set("standards_path", "./my_standards")
config.set("log_level", "DEBUG")
config.set("default_mode", "warn")
```

#### load

```python
def load(
    self,
    config_path: str
) -> None
```

Load configuration from file.

**Parameters:**
- `config_path`: Path to configuration file

**Example:**

```python
config = ConfigManager()

# Load from file
config.load(".adri/config.yaml")
```

#### save

```python
def save(
    self,
    config_path: str
) -> None
```

Save configuration to file.

**Parameters:**
- `config_path`: Path to save configuration

**Example:**

```python
config = ConfigManager()

# Modify and save
config.set("min_score", 85.0)
config.save(".adri/config.yaml")
```

## Assessment API

### assess_data_quality

Programmatic assessment function.

```python
from adri import assess_data_quality

assessment = assess_data_quality(data, standard_path)
```

**Parameters:**

```python
def assess_data_quality(
    data: Union[pd.DataFrame, dict, list],
    standard_path: str
) -> Assessment
```

**Parameters:**
- `data`: Data to assess
- `standard_path`: Path to standard file

**Returns:** Assessment object

**Example:**

```python
from adri import assess_data_quality
import pandas as pd

data = pd.DataFrame({
    "id": [1, 2, 3],
    "email": ["a@example.com", "b@example.com", "c@example.com"]
})

assessment = assess_data_quality(
    data,
    "ADRI/dev/standards/customer_standard.yaml"
)

if assessment.passed:
    print("Quality check passed!")
    print(f"Score: {assessment.overall_score}/100")
else:
    print("Quality check failed!")
    for issue in assessment.issues:
        print(f"- {issue}")
```

## CLI API

### Running CLI Commands Programmatically

```python
from adri.validator.cli.commands import cli
from click.testing import CliRunner

runner = CliRunner()
result = runner.invoke(cli, ['assess', 'data.csv', '--standard', 'my_standard'])
```

**Example:**

```python
from adri.validator.cli.commands import cli
from click.testing import CliRunner

runner = CliRunner()

# Run assess command
result = runner.invoke(cli, [
    'assess',
    'customers.csv',
    '--standard', 'customer_standard',
    '--output', 'report.json'
])

if result.exit_code == 0:
    print("Assessment passed")
else:
    print(f"Assessment failed: {result.output}")

# Run generate-standard command
result = runner.invoke(cli, [
    'generate-standard',
    'sample_data.csv',
    '--name', 'new_standard',
    '--strict'
])

print(result.output)
```

## Complete Examples

### Example 1: Programmatic Validation

```python
from adri.validator.core.assessor import DataQualityAssessor
from adri.validator.standards.loader import StandardLoader
import pandas as pd

# Load standard
loader = StandardLoader()
standard = loader.load("customer_standard")

# Prepare data
data = pd.DataFrame({
    "customer_id": [1, 2, 3],
    "email": ["user@example.com", "test@example.com", "admin@example.com"],
    "age": [25, 30, 35]
})

# Assess quality
assessor = DataQualityAssessor()
assessment = assessor.assess(data, standard)

# Process results
if assessment.overall_score >= 80.0:
    print(f"✅ Quality passed: {assessment.overall_score}/100")
    # Proceed with processing
    process_data(data)
else:
    print(f"❌ Quality failed: {assessment.overall_score}/100")
    # Handle quality issues
    for issue in assessment.issues:
        print(f"  - {issue.dimension}: {issue.description}")
```

### Example 2: Generate and Use Standard

```python
from adri.validator.analysis.standard_generator import StandardGenerator
from adri.validator.core.assessor import DataQualityAssessor
import pandas as pd

# Sample good data
good_data = pd.DataFrame({
    "id": [1, 2, 3],
    "email": ["a@example.com", "b@example.com", "c@example.com"],
    "score": [85.5, 92.0, 78.5]
})

# Generate standard
generator = StandardGenerator()
standard = generator.generate(
    data=good_data,
    name="score_standard",
    description="Score data quality standard",
    strict=True
)

# Save standard
generator.save(standard, "ADRI/dev/standards/score_standard.yaml")

# Later: assess new data
new_data = pd.DataFrame({
    "id": [4, 5],
    "email": ["d@example.com", "e@example.com"],
    "score": [88.0, 95.5]
})

assessor = DataQualityAssessor()
assessment = assessor.assess(new_data, standard)

print(f"Quality score: {assessment.overall_score}/100")
```

### Example 3: Custom Configuration

```python
from adri.validator.config.manager import ConfigManager
from adri import adri_protected

# Configure ADRI
config = ConfigManager()
config.set("standards_path", "./custom_standards")
config.set("log_level", "DEBUG")
config.set("default_mode", "warn")
config.set("min_score", 85.0)
config.save(".adri/config.yaml")

# Use with decorator
@adri_protected(standard="data", data_param="data")
def process_data(data):
    """Process data with custom config."""
    return analyze(data)

# Custom config is automatically loaded
result = process_data(my_data)
```

### Example 4: Batch Assessment

```python
from adri.validator.core.assessor import DataQualityAssessor
from adri.validator.standards.loader import StandardLoader
import pandas as pd
import glob

# Load standard once
loader = StandardLoader()
standard = loader.load("customer_standard")

# Create assessor once
assessor = DataQualityAssessor()

# Process multiple files
results = []
for file_path in glob.glob("data/*.csv"):
    data = pd.read_csv(file_path)
    assessment = assessor.assess(data, standard)
    
    results.append({
        "file": file_path,
        "score": assessment.overall_score,
        "passed": assessment.passed,
        "issues": len(assessment.issues)
    })

# Summary
passed = sum(1 for r in results if r["passed"])
failed = len(results) - passed

print(f"Results: {passed} passed, {failed} failed")
for result in results:
    status = "✅" if result["passed"] else "❌"
    print(f"{status} {result['file']}: {result['score']}/100")
```

## Type Hints

ADRI provides comprehensive type hints for all public APIs:

```python
from typing import Union, Optional, List, Dict, Any
import pandas as pd

# Data types
DataType = Union[pd.DataFrame, dict, list]

# Standard types
StandardType = Union[str, dict]

# Assessment result
class Assessment:
    overall_score: float
    passed: bool
    issues: List[Issue]
```

## Error Handling

Common exceptions:

```python
from adri.validator.exceptions import (
    DataQualityException,      # Quality check failed
    StandardNotFoundError,     # Standard not found
    ConfigurationError,        # Configuration issue
    ValidationError           # Validation error
)

try:
    result = process_data(data)
except DataQualityException as e:
    print(f"Quality check failed: {e}")
    print(f"Score: {e.assessment.overall_score}")
    print(f"Issues: {e.assessment.issues}")
except StandardNotFoundError as e:
    print(f"Standard not found: {e.standard_name}")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

## Next Steps

- [Getting Started](GETTING_STARTED.md) - Hands-on tutorial
- [How It Works](HOW_IT_WORKS.md) - Quality dimensions
- [Architecture](ARCHITECTURE.md) - System design
- [Examples](../examples/README.md) - Working examples

---

**Complete API reference for advanced ADRI usage.**
