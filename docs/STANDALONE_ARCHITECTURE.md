# ADRI - Architecture Guide

**Stop AI Agents Breaking on Bad Data**
One line of code. Any framework. Bulletproof agents.

## Overview

ADRI is designed as a **zero-dependency data quality framework** that protects AI agents from bad data. This guide explains how ADRI works under the hood and why it's built for reliability.

**Key Benefits**:
- ✅ **Zero Dependencies**: Works offline, no network calls
- ✅ **Framework Agnostic**: Protects any Python function
- ✅ **Production Ready**: Built for enterprise reliability
- ✅ **Developer Friendly**: One decorator, instant protection

## Core Principles

### 1. Zero External Dependencies
- **No runtime network calls**: All functionality works offline
- **Bundled standards**: 15+ YAML standards included in the package
- **Self-contained validation**: Complete validation logic within the component
- **Optional integrations**: External features are opt-in, not required

### 2. Clear Component Boundaries
- **Protocol-based interfaces**: Uses Python protocols for loose coupling
- **Dependency injection**: External services injected, not hardcoded
- **Facade pattern**: ComponentBoundary manages all external interactions
- **Context isolation**: StandaloneMode context manager for pure isolation

### 3. Extensible Architecture
- **Plugin system**: Support for external audit loggers and data providers
- **Configuration-driven**: Behavior controlled via configuration files
- **Environment overrides**: Standards path and settings via environment variables
- **Graceful degradation**: Functions without optional components

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     Public API Layer                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  @adri_protected decorator  │  CLI Commands           │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                     Core Engine Layer                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AssessmentEngine  │  DataProtectionEngine            │  │
│  │  StandardsLoader   │  ConfigManager                   │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                   Boundary Control Layer                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ComponentBoundary │  ExternalIntegration (Protocol)  │  │
│  │  DataProvider      │  AuditSink                       │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Standards Layer                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Bundled Standards (15 YAML files)                    │  │
│  │  Standards Validation │ Standards Metadata            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Dependencies

### Internal Dependencies (Required)
```python
# Core Python libraries only
pandas >= 1.5.0      # Data manipulation
pyyaml >= 6.0        # YAML parsing
click >= 8.0         # CLI interface
pyarrow >= 14.0.0    # Parquet support
```

### External Dependencies (Optional)
```python
# Development and testing
pytest >= 7.0        # Testing framework
black >= 23.0        # Code formatting
flake8 >= 6.0        # Linting
mypy >= 1.0          # Type checking

# Optional features
requests             # Verodat integration (optional)
```

## Key Components

### 1. Standards Loader
**Location**: `adri/standards/loader.py`

**Purpose**: Loads and validates YAML standards from bundled directory

**Key Features**:
- Thread-safe loading with caching
- Standards validation on load
- No external path fallbacks in standalone mode
- Environment variable override for testing

**Interface**:
```python
class StandardsLoader:
    def load_standard(self, standard_name: str) -> Dict[str, Any]
    def list_available_standards(self) -> List[str]
    def get_standard_metadata(self, standard_name: str) -> Dict[str, Any]
```

### 2. Assessment Engine
**Location**: `adri/core/assessor.py`

**Purpose**: Performs data quality assessments against standards

**Key Features**:
- Five-dimensional assessment (validity, completeness, freshness, consistency, plausibility)
- Configurable scoring thresholds
- Detailed failure reporting
- Performance metrics tracking

**Interface**:
```python
class AssessmentEngine:
    def assess(self, data: pd.DataFrame, standard: Dict) -> AssessmentResult
    def validate_schema(self, data: pd.DataFrame, schema: Dict) -> bool
```

### 3. Data Protection Engine
**Location**: `adri/core/protection.py`

**Purpose**: Enforces data quality gates via decorator pattern

**Key Features**:
- Function call interception
- Quality score enforcement
- Audit logging integration
- Configurable failure modes (raise, warn, log)

**Interface**:
```python
class DataProtectionEngine:
    def protect_function_call(self, func, *args, **kwargs) -> Any
    def assess_data_quality(self, data: Any) -> AssessmentResult
```

### 4. Component Boundary
**Location**: `adri/core/boundary.py`

**Purpose**: Manages interfaces with external systems

**Key Features**:
- Protocol-based integration points
- Health checking for external services
- Graceful degradation
- Standalone mode enforcement

**Interface**:
```python
class ComponentBoundary:
    def register_integration(name: str, integration: ExternalIntegration) -> bool
    def register_data_provider(name: str, provider: DataProvider) -> bool
    def register_audit_sink(name: str, sink: AuditSink) -> bool
    def shutdown_all() -> bool
```

### 5. Audit Logger
**Location**: `adri/core/audit_logger.py`

**Purpose**: Comprehensive audit trail for assessments

**Key Features**:
- Structured audit records
- Multiple output formats (JSON, CSV, Verodat)
- Configurable via ConfigManager
- Optional external sink support

**Interface**:
```python
class AuditLogger:
    def log_assessment(
        assessment_result: Any,
        execution_context: Dict,
        data_info: Dict,
        performance_metrics: Dict
    ) -> AuditRecord
```

## Bundled Standards

The validator includes 15 pre-validated YAML standards:

| Standard | Purpose | Version |
|----------|---------|---------|
| `data_validation_standard` | General data validation | 1.0.0 |
| `agent_input_standard` | AI agent input validation | 1.0.0 |
| `agent_output_standard` | AI agent output validation | 1.0.0 |
| `customer_data_standard` | Customer data quality | 1.0.0 |
| `financial_data_standard` | Financial data validation | 1.0.0 |
| `healthcare_data_standard` | Healthcare data compliance | 1.0.0 |
| `inventory_data_standard` | Inventory management | 1.0.0 |
| `marketing_analytics_standard` | Marketing data quality | 1.0.0 |
| `product_catalog_standard` | Product catalog validation | 1.0.0 |
| `sales_data_standard` | Sales data validation | 1.0.0 |
| `sensor_data_standard` | IoT sensor data | 1.0.0 |
| `supply_chain_standard` | Supply chain data | 1.0.0 |
| `test_standard` | Testing and development | 1.0.0 |
| `transaction_data_standard` | Transaction validation | 1.0.0 |
| `user_activity_standard` | User activity tracking | 1.0.0 |

## Configuration Management

### Configuration Hierarchy
1. **Default Configuration**: Built-in defaults
2. **File Configuration**: `adri-config.yaml`
3. **Environment Variables**: Runtime overrides
4. **Function Parameters**: Call-time overrides

### Key Configuration Options
```yaml
# adri-config.yaml
adri:
  protection:
    min_score: 75.0
    failure_mode: "raise"  # raise | warn | log
    cache_duration: 300

  audit:
    enabled: false
    log_location: "./logs/adri_audit.jsonl"
    include_data_samples: false

  standards:
    path: null  # Uses bundled by default
    cache_enabled: true
```

## Verification Utilities

### Standalone Verification
**Location**: `adri/utils/verification.py`

**Purpose**: Verify standalone operation

**Checks**:
1. No external dependencies installed
2. Bundled standards available
3. Core modules importable
4. No external integration active
5. System compatibility

**Usage**:
```python
from adri.utils.verification import run_full_verification

# Run verification
success = run_full_verification(verbose=True)
```

### Boundary Validation
**Location**: `adri/core/boundary.py`

**Purpose**: Validate component boundaries

**Features**:
- StandaloneMode context manager
- Integration health checks
- Graceful shutdown procedures

**Usage**:
```python
from adri.core.boundary import StandaloneMode, validate_standalone_operation

# Force standalone mode
with StandaloneMode():
    # All external integrations disabled
    result = validate_data(df)

# Validate standalone capability
is_standalone = validate_standalone_operation()
```

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock external dependencies
- Verify boundary enforcement

### Integration Tests
- Test component interactions
- Verify standalone operation
- Test with bundled standards

### Performance Tests
- Large dataset handling
- Concurrent assessment
- Memory efficiency

### Standalone Tests
- No network calls
- No external dependencies
- Bundled standards only

## Deployment Scenarios

### 1. Standalone Package
```bash
pip install adri-validator
python -m adri.utils.verification
```

### 2. Docker Container
```dockerfile
FROM python:3.10-slim
COPY adri-validator /app
WORKDIR /app
RUN pip install .
CMD ["python", "-m", "adri.utils.verification"]
```

### 3. Air-Gapped Environment
```bash
# Download wheel file
pip download adri-validator --no-deps

# Transfer to air-gapped system
# Install from wheel
pip install adri_validator-3.0.1-py3-none-any.whl
```

### 4. Embedded in Application
```python
from adri.decorators import adri_protected

@adri_protected(standard="customer_data_standard")
def process_customer_data(df):
    # Your processing logic
    return df
```

## Security Considerations

### Input Validation
- All YAML standards validated on load
- Schema validation for data inputs
- Type checking for function parameters

### Isolation
- No automatic network connections
- No file system access outside package
- No execution of external code

### Audit Trail
- Comprehensive logging of assessments
- Tamper-evident audit records
- Optional encryption for audit logs

## Performance Characteristics

### Memory Usage
- Standards cached after first load
- Assessment results cached (configurable)
- Efficient pandas operations

### CPU Usage
- Vectorized operations via pandas
- Parallel assessment for large datasets
- Optimized validation algorithms

### Startup Time
- Fast initialization (< 1 second)
- Lazy loading of standards
- Pre-compiled regex patterns

## Extensibility Points

### Custom Standards
```python
# Via environment variable
export ADRI_STANDARDS_PATH=/path/to/custom/standards
```

### Custom Audit Sinks
```python
from adri.core.boundary import get_boundary_manager, AuditSink

class CustomAuditSink:
    def write_record(self, record): ...
    def flush(self): ...
    def close(self): ...

boundary = get_boundary_manager()
boundary.register_audit_sink("custom", CustomAuditSink())
```

### Custom Data Providers
```python
from adri.core.boundary import get_boundary_manager, DataProvider

class CustomDataProvider:
    def get_data(self): ...
    def get_metadata(self): ...
    def validate_schema(self): ...

boundary = get_boundary_manager()
boundary.register_data_provider("custom", CustomDataProvider())
```

## Migration Guide

### From External Standards
```python
# Before (with external dependency)
from adri_standards import load_standard
standard = load_standard("customer_data")

# After (standalone)
from adri.standards.loader import StandardsLoader
loader = StandardsLoader()
standard = loader.load_standard("customer_data_standard")
```

### From Network-Based Validation
```python
# Before (network call)
result = validate_with_api(data, standard_url)

# After (local validation)
from adri.core.assessor import AssessmentEngine
engine = AssessmentEngine()
result = engine.assess(data, standard)
```

## Troubleshooting

### Common Issues

1. **Standards Not Found**
   - Verify bundled standards directory exists
   - Check ADRI_STANDARDS_PATH environment variable
   - Run verification: `python -m adri.utils.verification`

2. **Import Errors**
   - Ensure all required packages installed
   - Check Python version (>= 3.10)
   - Verify no conflicting packages

3. **Performance Issues**
   - Enable caching in configuration
   - Use appropriate batch sizes
   - Consider data sampling for large datasets

### Diagnostic Commands

```bash
# Verify installation
python -m adri.utils.verification

# List available standards
python -c "from adri.standards.loader import list_bundled_standards; print(list_bundled_standards())"

# Check component boundaries
python -c "from adri.core.boundary import validate_standalone_operation; print(validate_standalone_operation())"

# Test assessment
python -c "
import pandas as pd
from adri.decorators import adri_protected

@adri_protected(standard='test_standard')
def test(df): return df

df = pd.DataFrame({'id': [1,2,3], 'value': [10,20,30]})
result = test(df)
print('Success!')
"
```

## Support and Resources

- **GitHub Repository**: https://github.com/ThinkEvolveSolve/adri-validator
- **Documentation**: https://github.com/ThinkEvolveSolve/adri-validator/docs
- **Issue Tracker**: https://github.com/ThinkEvolveSolve/adri-validator/issues
- **Changelog**: https://github.com/ThinkEvolveSolve/adri-validator/blob/main/CHANGELOG.md

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0.1 | 2024-08 | Made fully standalone, removed external dependencies |
| 3.0.0 | 2024-07 | Major refactor, added audit logging |
| 2.0.0 | 2024-06 | Added component boundaries |
| 1.0.0 | 2024-05 | Initial release |

---

*This document describes the ADRI Validator version 3.0.1 standalone architecture.*
