# ADRI API Reference

**Stop AI Agents Breaking on Bad Data**  
One line of code. Any framework. Bulletproof agents.

## Quick Reference

```python
# Basic protection (most common)
@adri_protected(data_param="your_data")
def your_agent(your_data):
    return process_data(your_data)

# Custom requirements
@adri_protected(data_param="data", min_score=90)
def strict_agent(data):
    return analyze_data(data)
```

## Table of Contents
1. [Essential Decorator](#essential-decorator) ⭐ **Start Here**
2. [Framework Examples](#framework-examples)
3. [Configuration](#configuration)
4. [CLI Commands](#cli-commands)
5. [Advanced Usage](#advanced-usage)
6. [Core Classes](#core-classes)
7. [Utilities](#utilities)

---

## Essential Decorator

### `@adri_protected` ⭐

The one decorator you need to protect any AI agent.

```python
from adri.decorators.guard import adri_protected

@adri_protected(
    data_param: str,           # Which parameter contains your data
    min_score: float = 80.0,   # Quality threshold (0-100)
    on_failure: str = "raise", # What to do if data is bad
    verbose: bool = False      # Show protection messages
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `standard` | `str` | Required | Name of the YAML standard to use for validation |
| `data_arg` | `str` | Auto-detect | Name of the argument containing data to validate |
| `min_score` | `float` | 75.0 | Minimum quality score required (0-100) |
| `failure_mode` | `str` | "raise" | Action on failure: "raise", "warn", or "log" |
| `cache_duration` | `int` | 300 | Cache duration in seconds |
| `audit_enabled` | `bool` | False | Enable audit logging for this function |

#### Example

```python
import pandas as pd
from adri.decorators import adri_protected

@adri_protected(
    standard="customer_data_standard",
    min_score=80.0,
    failure_mode="raise",
    audit_enabled=True
)
def process_customer_data(df: pd.DataFrame) -> pd.DataFrame:
    # Your data processing logic
    return df

# Usage
df = pd.DataFrame({
    'customer_id': [1, 2, 3],
    'email': ['user1@example.com', 'user2@example.com', 'user3@example.com'],
    'age': [25, 30, 35]
})

result = process_customer_data(df)  # Validates before processing
```

---

## Core Classes

### AssessmentEngine

Performs data quality assessments against ADRI standards.

```python
from adri.core.assessor import AssessmentEngine
```

#### Methods

##### `__init__(config: Optional[Dict[str, Any]] = None)`

Initialize the assessment engine with optional configuration.

##### `assess(data: pd.DataFrame, standard: Dict[str, Any]) -> AssessmentResult`

Perform a comprehensive data quality assessment.

**Parameters:**
- `data`: DataFrame to assess
- `standard`: ADRI standard dictionary

**Returns:** `AssessmentResult` object with scores and details

**Example:**
```python
from adri.core.assessor import AssessmentEngine
from adri.standards.loader import StandardsLoader

engine = AssessmentEngine()
loader = StandardsLoader()

standard = loader.load_standard("customer_data_standard")
result = engine.assess(df, standard)

print(f"Overall Score: {result.overall_score}")
print(f"Passed: {result.passed}")
```

### AssessmentResult

Result object from data quality assessment.

```python
from adri.core.assessor import AssessmentResult
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `overall_score` | `float` | Overall quality score (0-100) |
| `dimension_scores` | `Dict[str, DimensionScore]` | Scores for each dimension |
| `passed` | `bool` | Whether assessment passed minimum threshold |
| `timestamp` | `datetime` | When assessment was performed |
| `standard_id` | `str` | ID of standard used |
| `metadata` | `Dict[str, Any]` | Additional assessment metadata |

#### Methods

##### `to_dict() -> Dict[str, Any]`
Convert result to dictionary format.

##### `to_json() -> str`
Convert result to JSON string.

### DataProtectionEngine

Enforces data quality gates on function calls.

```python
from adri.core.protection import DataProtectionEngine
```

#### Methods

##### `__init__(config: Optional[Dict[str, Any]] = None)`
Initialize the protection engine.

##### `protect_function_call(func: Callable, *args, **kwargs) -> Any`
Protect a function call with data quality validation.

**Parameters:**
- `func`: Function to protect
- `*args`: Positional arguments for the function
- `**kwargs`: Keyword arguments for the function

**Returns:** Function result if validation passes

**Example:**
```python
from adri.core.protection import DataProtectionEngine

engine = DataProtectionEngine({
    "min_score": 75.0,
    "failure_mode": "raise"
})

def process_data(df):
    return df.describe()

result = engine.protect_function_call(
    process_data,
    df,
    standard="test_standard"
)
```

---

## Standards Management

### StandardsLoader

Manages loading and caching of YAML standards.

```python
from adri.standards.loader import StandardsLoader
```

#### Methods

##### `__init__()`
Initialize the standards loader.

##### `load_standard(standard_name: str) -> Dict[str, Any]`
Load a standard by name.

**Parameters:**
- `standard_name`: Name of the standard (without .yaml extension)

**Returns:** Dictionary containing the standard definition

**Raises:** `StandardNotFoundError` if standard doesn't exist

##### `list_available_standards() -> List[str]`
Get list of all available standards.

**Returns:** List of standard names

##### `get_standard_metadata(standard_name: str) -> Dict[str, Any]`
Get metadata for a standard without loading full content.

**Returns:** Dictionary with name, version, description, file_path

##### `standard_exists(standard_name: str) -> bool`
Check if a standard exists.

##### `clear_cache()`
Clear the internal cache of loaded standards.

#### Example

```python
from adri.standards.loader import StandardsLoader

loader = StandardsLoader()

# List available standards
standards = loader.list_available_standards()
print(f"Available standards: {standards}")

# Load a specific standard
standard = loader.load_standard("customer_data_standard")
print(f"Standard version: {standard['standards']['version']}")

# Get metadata only
metadata = loader.get_standard_metadata("customer_data_standard")
print(f"Description: {metadata['description']}")
```

### Convenience Functions

```python
from adri.standards.loader import load_bundled_standard, list_bundled_standards

# Quick access to standards
standard = load_bundled_standard("test_standard")
all_standards = list_bundled_standards()
```

---

## Configuration

### ConfigManager

Manages configuration with hierarchy: defaults → file → environment → runtime.

```python
from adri.config.manager import ConfigManager
```

#### Methods

##### `__init__(config_path: Optional[str] = None)`
Initialize with optional config file path.

##### `get_config(section: Optional[str] = None) -> Dict[str, Any]`
Get configuration for a section or all config.

##### `get_protection_config() -> Dict[str, Any]`
Get data protection configuration.

##### `get_audit_config() -> Dict[str, Any]`
Get audit logging configuration.

##### `update_config(updates: Dict[str, Any], section: Optional[str] = None)`
Update configuration at runtime.

#### Configuration Structure

```yaml
adri:
  protection:
    min_score: 75.0              # Minimum quality score (0-100)
    failure_mode: "raise"        # raise | warn | log
    cache_duration: 300          # Seconds to cache results
    cache_enabled: true

  audit:
    enabled: false               # Enable audit logging
    log_location: "./logs/adri_audit.jsonl"
    log_level: "INFO"           # INFO | DEBUG | ERROR
    include_data_samples: false  # Include data in logs
    max_log_size_mb: 100        # Rotate after size
    batch_mode: false           # Batch audit records
    batch_size: 100

  standards:
    path: null                  # Custom standards path
    cache_enabled: true         # Cache loaded standards

  verodat:                     # Optional Verodat integration
    enabled: false
    api_url: "https://api.verodat.com"
    api_key: null
    workspace_id: null
    account_id: null
```

---

## Audit Logging

### AuditLogger

Records comprehensive audit trail for assessments.

```python
from adri.core.audit_logger import AuditLogger
```

#### Methods

##### `__init__(config: Optional[Dict[str, Any]] = None)`
Initialize audit logger with configuration.

##### `log_assessment(...) -> Optional[AuditRecord]`
Log an assessment to audit trail.

**Parameters:**
- `assessment_result`: Assessment result object
- `execution_context`: Context about function execution
- `data_info`: Information about assessed data
- `performance_metrics`: Performance metrics
- `failed_checks`: List of failed validation checks

**Returns:** `AuditRecord` if logging enabled, None otherwise

### AuditRecord

Structured audit record for assessments.

```python
from adri.core.audit_logger import AuditRecord
```

#### Methods

##### `to_dict() -> Dict[str, Any]`
Convert to dictionary format.

##### `to_json() -> str`
Convert to JSON string.

##### `to_verodat_format() -> Dict[str, Any]`
Convert to Verodat-compatible format.

### AuditLoggerCSV

CSV-based audit logger for file output.

```python
from adri.core.audit_logger_csv import AuditLoggerCSV
```

#### Example

```python
from adri.core.audit_logger_csv import AuditLoggerCSV

logger = AuditLoggerCSV({
    "enabled": True,
    "output_path": "./audit_logs",
    "rotation": "daily"
})

# Logger automatically used by @adri_protected when configured
```

---

## Utilities

### Verification Utilities

Verify standalone installation and operation.

```python
from adri.utils.verification import (
    verify_standalone_installation,
    list_bundled_standards,
    check_system_compatibility,
    verify_audit_logging,
    run_full_verification
)
```

#### Functions

##### `verify_standalone_installation() -> Tuple[bool, List[str]]`
Verify standalone installation.

**Returns:** (success: bool, messages: List[str])

##### `list_bundled_standards() -> List[Dict[str, str]]`
List all bundled standards with metadata.

##### `check_system_compatibility() -> Dict[str, Any]`
Check system compatibility.

##### `verify_audit_logging(enabled: bool = False) -> Tuple[bool, List[str]]`
Verify audit logging functionality.

##### `run_full_verification(verbose: bool = True) -> bool`
Run complete verification suite.

#### Example

```python
from adri.utils.verification import run_full_verification

# Run full verification
if run_full_verification(verbose=True):
    print("✅ All verifications passed")
else:
    print("❌ Some verifications failed")
```

### Component Boundary

Manage boundaries with external systems.

```python
from adri.core.boundary import (
    ComponentBoundary,
    StandaloneMode,
    get_boundary_manager,
    validate_standalone_operation
)
```

#### StandaloneMode Context Manager

```python
from adri.core.boundary import StandaloneMode

# Force standalone operation
with StandaloneMode():
    # All external integrations disabled
    result = process_data(df)
```

#### ComponentBoundary Methods

##### `register_integration(name: str, integration: ExternalIntegration, config: IntegrationConfig) -> bool`
Register an external integration.

##### `register_data_provider(name: str, provider: DataProvider) -> bool`
Register a data provider.

##### `register_audit_sink(name: str, sink: AuditSink) -> bool`
Register an audit sink.

##### `health_check() -> Dict[str, bool]`
Check health of all integrations.

##### `shutdown_all() -> bool`
Shutdown all integrations.

---

## CLI Commands

### Main Command

```bash
adri [OPTIONS] COMMAND [ARGS]...
```

### Commands

#### `validate`
Validate data file against a standard.

```bash
adri validate --data data.csv --standard customer_data_standard
```

**Options:**
- `--data PATH`: Path to data file (CSV/Parquet)
- `--standard TEXT`: Standard name
- `--min-score FLOAT`: Minimum score (default: 75.0)
- `--output PATH`: Output report path

#### `list-standards`
List all available standards.

```bash
adri list-standards
```

#### `show-standard`
Display details of a specific standard.

```bash
adri show-standard customer_data_standard
```

#### `verify`
Verify standalone installation.

```bash
adri verify
```

#### `config`
Display current configuration.

```bash
adri config [--section SECTION]
```

---

## Exceptions

### Standard Exceptions

```python
from adri.standards.exceptions import (
    StandardNotFoundError,
    InvalidStandardError,
    StandardsDirectoryNotFoundError
)
```

#### StandardNotFoundError
Raised when a requested standard doesn't exist.

```python
try:
    standard = loader.load_standard("nonexistent")
except StandardNotFoundError as e:
    print(f"Standard not found: {e}")
```

#### InvalidStandardError
Raised when a standard has invalid structure.

#### StandardsDirectoryNotFoundError
Raised when standards directory is missing.

### Assessment Exceptions

```python
from adri.core.exceptions import (
    AssessmentError,
    DataQualityError,
    ConfigurationError
)
```

#### AssessmentError
Base exception for assessment failures.

#### DataQualityError
Raised when data fails quality checks.

```python
try:
    result = engine.assess(df, standard)
except DataQualityError as e:
    print(f"Quality check failed: {e}")
```

#### ConfigurationError
Raised for configuration issues.

---

## Advanced Usage

### Custom Standards Path

```python
import os
os.environ['ADRI_STANDARDS_PATH'] = '/path/to/custom/standards'

from adri.standards.loader import StandardsLoader
loader = StandardsLoader()  # Will use custom path
```

### Programmatic Configuration

```python
from adri.config.manager import ConfigManager

config = ConfigManager()
config.update_config({
    "min_score": 90.0,
    "failure_mode": "warn"
}, section="protection")
```

### Batch Processing

```python
import pandas as pd
from adri.decorators import adri_protected

@adri_protected(
    standard="transaction_data_standard",
    cache_duration=3600  # Cache for 1 hour
)
def process_batch(df: pd.DataFrame) -> pd.DataFrame:
    return df

# Process multiple batches
for batch_file in batch_files:
    df = pd.read_csv(batch_file)
    result = process_batch(df)
    save_result(result)
```

### Custom Audit Sink

```python
from adri.core.boundary import get_boundary_manager

class CustomAuditSink:
    def write_record(self, record):
        # Custom implementation
        send_to_siem(record)
        return True

    def flush(self):
        return True

    def close(self):
        return True

boundary = get_boundary_manager()
boundary.register_audit_sink("siem", CustomAuditSink())
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ADRI_STANDARDS_PATH` | Custom standards directory | Bundled standards |
| `ADRI_CONFIG_PATH` | Configuration file path | `./adri-config.yaml` |
| `ADRI_ENV` | Environment name | `PRODUCTION` |
| `ADRI_LOG_LEVEL` | Logging level | `INFO` |
| `ADRI_AUDIT_ENABLED` | Enable audit logging | `false` |
| `ADRI_CACHE_ENABLED` | Enable caching | `true` |

---

## Performance Tips

1. **Enable Caching**: Use `cache_duration` parameter for repeated validations
2. **Batch Processing**: Process data in batches for large datasets
3. **Selective Validation**: Use `data_arg` to validate specific columns
4. **Async Processing**: Use thread pools for parallel validation
5. **Memory Management**: Clear cache periodically with `loader.clear_cache()`

---

## Migration from v2.x

### Breaking Changes
- `adri-standards` package no longer required
- Standards now bundled with validator
- New audit logging system
- Component boundary management

### Migration Steps

1. Remove `adri-standards` dependency
2. Update standard names (add `_standard` suffix)
3. Update configuration format
4. Add audit configuration if needed
5. Test with `adri verify`

---

*API Reference for ADRI Validator v3.0.1*
