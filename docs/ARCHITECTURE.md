# ADRI Architecture

Technical architecture and system design.

## Table of Contents

1. [Overview](#overview)
2. [System Components](#system-components)
3. [Data Flow](#data-flow)
4. [Core Modules](#core-modules)
5. [Standards System](#standards-system)
6. [Extension Points](#extension-points)
7. [Design Decisions](#design-decisions)

## Overview

ADRI follows a modular architecture designed for:
- **Simplicity**: One decorator, minimal configuration
- **Performance**: Efficient validation with caching
- **Extensibility**: Plugin system for custom validators
- **Framework Agnostic**: Works with any Python function

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Application                      │
│  ┌────────────────────────────────────────────────┐    │
│  │  @adri_protected(contract="data", data_param="data")            │    │
│  │  def process_data(data):                       │    │
│  │      return results                            │    │
│  └────────────────────────────────────────────────┘    │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  ADRI Core System                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Decorator  │→ │  Protection  │→ │  Assessor    │ │
│  │   Engine     │  │  Engine      │  │  Engine      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│          │                 │                  │         │
│          ▼                 ▼                  ▼         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Standard   │  │   Config     │  │   Report     │ │
│  │   Loader     │  │   Manager    │  │   Generator  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    Storage Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  .adri/      │  │  .adri/      │  │  .adri/      │ │
│  │  standards/  │  │  config.yaml │  │  logs/       │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## System Components

### 1. Decorator Engine

**Location**: `adri/validator/decorators/guard.py`

**Purpose**: Intercepts function calls to apply data protection

**Key Classes**:
- `adri_protected`: Main decorator
- `GuardConfig`: Configuration management

**Flow**:
```python
1. Function decorated with @adri_protected
2. Decorator wraps function
3. On call, extracts data parameter
4. Passes to Protection Engine
5. Returns result or raises exception
```

### 2. Protection Engine

**Location**: `adri/validator/core/protection.py`

**Purpose**: Orchestrates validation workflow

**Key Classes**:
- `DataProtectionEngine`: Main orchestrator
- `ProtectionContext`: Execution context

**Responsibilities**:
- Load or generate standards
- Invoke assessor
- Apply guard mode logic
- Handle exceptions

### 3. Assessor Engine

**Location**: `adri/validator/core/assessor.py`

**Purpose**: Performs multi-dimensional quality assessment

**Key Classes**:
- `DataQualityAssessor`: Main assessment engine
- `DimensionAssessor`: Per-dimension validation

**Validation Dimensions**:
```python
1. Validity: Type and format checks
2. Completeness: Missing data detection
3. Consistency: Cross-field rules
4. Accuracy: Range and pattern validation
5. Timeliness: Data freshness checks
```

### 4. Standard Loader

**Location**: `adri/validator/contracts/loader.py`

**Purpose**: Load and manage quality standards

**Key Classes**:
- `StandardLoader`: Loads YAML standards
- `StandardCache`: Caches loaded standards

**Standard Resolution**:
```
1. Check cache
2. Look in project ADRI/dev/contracts/
3. Look in user ~/ADRI/dev/contracts/
4. Look in bundled standards
5. Auto-generate if enabled
```

### 5. Standard Generator

**Location**: `adri/validator/analysis/standard_generator.py`

**Purpose**: Auto-generate standards from data

**Key Classes**:
- `StandardGenerator`: Main generator
- `DataProfiler`: Analyzes data patterns
- `TypeInference`: Infers data types

**Generation Process**:
```python
1. Profile data structure
2. Infer types and patterns
3. Calculate ranges
4. Detect requirements
5. Generate YAML standard
6. Save to file
```

### 6. Report Generator

**Location**: `adri/validator/core/report_generator.py`

**Purpose**: Generate quality assessment reports

**Key Classes**:
- `ReportGenerator`: Creates reports
- `ReportTemplate`: Report formatting

**Output Formats**:
- Text (console output)
- JSON (machine-readable)
- YAML (human-readable)

### 7. Configuration Manager

**Location**: `adri/validator/config/manager.py`

**Purpose**: Manage ADRI configuration

**Key Classes**:
- `ConfigManager`: Configuration handler
- `ConfigLoader`: Loads config files

**Configuration Hierarchy**:
```
1. Decorator parameters (highest priority)
2. Project ADRI/config.yaml
3. User ~/ADRI/config.yaml
4. Environment variables
5. Default values (lowest priority)
```

### 8. CLI Commands

**Location**: `adri/validator/cli/commands.py`

**Purpose**: Command-line interface

**Key Commands**:
- `assess`: Validate data quality
- `generate-standard`: Create standards
- `validate-standard`: Check standard files
- `list-standards`: Show available standards
- `show-config`: Display configuration
- `setup`: Interactive configuration

## Data Flow

### Validation Flow

```
User Function Call
        │
        ▼
@adri_protected Decorator
        │
        ├─→ Extract data parameter
        │
        ▼
Protection Engine
        │
        ├─→ Load/Generate Standard
        │   │
        │   ├─→ Check cache
        │   ├─→ Load from file
        │   └─→ Auto-generate if needed
        │
        ├─→ Assess Data Quality
        │   │
        │   ├─→ Validity checks
        │   ├─→ Completeness checks
        │   ├─→ Consistency checks
        │   ├─→ Accuracy checks
        │   └─→ Timeliness checks
        │
        ├─→ Calculate Score
        │   │
        │   └─→ Sum dimension scores (0-100)
        │
        ├─→ Apply Guard Mode
        │   │
        │   ├─→ Block: Raise if score < threshold
        │   └─→ Warn: Log if score < threshold
        │
        ├─→ Generate Report
        │   │
        │   └─→ Save to ADRI/dev/logs/
        │
        └─→ Return or Raise
                │
                ▼
        Execute Function
                │
                ▼
        Return Results
```

### Standard Generation Flow

```
Input Data
    │
    ▼
Data Profiler
    │
    ├─→ Analyze Structure
    │   ├─→ Field names
    │   ├─→ Data types
    │   └─→ Nested structures
    │
    ├─→ Infer Types
    │   ├─→ Primitive types
    │   ├─→ Patterns (email, phone)
    │   └─→ Enums
    │
    ├─→ Calculate Ranges
    │   ├─→ Numeric min/max
    │   ├─→ String lengths
    │   └─→ Date ranges
    │
    ├─→ Detect Requirements
    │   ├─→ Always present = required
    │   ├─→ Sometimes missing = optional
    │   └─→ Never null = mandatory
    │
    └─→ Pattern Recognition
        ├─→ Email patterns
        ├─→ Phone patterns
        └─→ Custom regex
    │
    ▼
Standard Generator
    │
    ├─→ Build YAML Structure
    │
    ├─→ Add Metadata
    │   ├─→ Name
    │   ├─→ Version
    │   └─→ Description
    │
    └─→ Save to File
        │
        ▼
ADRI/dev/contracts/function_param_standard.yaml
```

## Core Modules

### Module: adri.validator.decorators

**Purpose**: Decorator implementations

**Files**:
- `guard.py`: Main decorator logic
- `__init__.py`: Exports

**Key Functions**:
```python
def adri_protected(
    data_param: str,
    standard: Optional[str] = None,
    mode: str = "block",
    auto_generate: bool = True,
    min_score: float = 80.0
) -> Callable
```

### Module: adri.validator.core

**Purpose**: Core validation logic

**Files**:
- `protection.py`: Protection engine
- `assessor.py`: Quality assessor
- `loader.py`: Data loader
- `report_generator.py`: Report creation

### Module: adri.validator.analysis

**Purpose**: Data analysis and profiling

**Files**:
- `data_profiler.py`: Data profiling
- `standard_generator.py`: Standard generation
- `type_inference.py`: Type detection

### Module: adri.validator.standards

**Purpose**: Standard management

**Files**:
- `loader.py`: Standard loading
- `yaml_standards.py`: YAML parsing
- `exceptions.py`: Standard errors

### Module: adri.validator.config

**Purpose**: Configuration management

**Files**:
- `manager.py`: Config management
- `loader.py`: Config loading

### Module: adri.validator.cli

**Purpose**: Command-line interface

**Files**:
- `commands.py`: CLI commands
- `__init__.py`: CLI setup

## Standards System

### Standard Format

```yaml
standard:
  name: "standard_name"
  version: "1.0.0"
  description: "Description"

  # Field definitions
  fields:
    field_name:
      type: string|integer|number|date|boolean
      required: true|false
      min_value: number (optional)
      max_value: number (optional)
      min_length: integer (optional)
      max_length: integer (optional)
      pattern: "regex" (optional)
      max_age_days: integer (optional)

  # Cross-field rules
  rules:
    - name: "Rule name"
      expression: "Python expression"
      severity: "critical|warning"
```

### Standard Storage

```
Project Standards:
ADRI/dev/contracts/
    └── custom_standard.yaml

User Standards:
~/ADRI/dev/contracts/
    └── shared_standard.yaml

Bundled Standards:
{package}/validator/contracts/bundled/
    └── high_quality_agent_data_standard.yaml
```

### Standard Caching

```python
class StandardCache:
    """LRU cache for loaded standards"""

    def __init__(self, max_size: int = 100):
        self._cache = {}
        self._max_size = max_size

    def get(self, key: str) -> Optional[Standard]:
        return self._cache.get(key)

    def set(self, key: str, standard: Standard):
        if len(self._cache) >= self._max_size:
            self._evict_oldest()
        self._cache[key] = standard
```

## Extension Points

### Custom Validators

Add custom validation dimensions:

```python
from adri.validator.core.assessor import DimensionAssessor

class CustomDimensionAssessor(DimensionAssessor):
    """Custom validation dimension"""

    def assess(self, data, standard) -> float:
        # Your validation logic
        score = calculate_score(data, standard)
        return score  # Return 0-20

# Register custom assessor
assessor.register_dimension("custom", CustomDimensionAssessor())
```

### Custom Standards Loaders

Support custom standard formats:

```python
from adri.validator.standards.loader import StandardLoader

class CustomStandardLoader(StandardLoader):
    """Load standards from custom source"""

    def load(self, standard_name: str) -> Standard:
        # Load from database, API, etc.
        return standard

# Use custom loader
protection_engine.set_loader(CustomStandardLoader())
```

### Custom Report Formats

Add custom report formats:

```python
from adri.validator.core.report_generator import ReportGenerator

class CustomReportGenerator(ReportGenerator):
    """Generate custom format reports"""

    def generate(self, assessment) -> str:
        # Your format logic
        return formatted_report

# Use custom generator
protection_engine.set_report_generator(CustomReportGenerator())
```

## Design Decisions

### Why Decorator Pattern?

**Chosen**: Decorator-based API
**Alternative**: Context manager, explicit calls

**Reasoning**:
- ✅ Minimal code change (one line)
- ✅ Clear intent (@adri_protected)
- ✅ Composable with other decorators
- ✅ Standard Python pattern

### Why YAML Standards?

**Chosen**: YAML format
**Alternatives**: JSON, TOML, Python

**Reasoning**:
- ✅ Human-readable
- ✅ Supports comments
- ✅ Widely supported
- ✅ Easy to edit

### Why Auto-Generation?

**Chosen**: Auto-generate from data
**Alternative**: Manual standard creation

**Reasoning**:
- ✅ Zero configuration burden
- ✅ Learns from actual data
- ✅ Reduces errors
- ✅ Faster adoption

### Why Local Logging?

**Chosen**: Local file logging
**Alternative**: Remote logging, database

**Reasoning**:
- ✅ No dependencies
- ✅ Developer-friendly
- ✅ Privacy-preserving
- ✅ Easy debugging

### Why Five Dimensions?

**Chosen**: 5 quality dimensions
**Alternatives**: More or fewer dimensions

**Reasoning**:
- ✅ Comprehensive coverage
- ✅ Easy to understand
- ✅ Industry-standard concepts
- ✅ Balanced scoring (20 pts each)

### Why 80/100 Threshold?

**Chosen**: Default minimum score of 80
**Alternatives**: Higher or lower threshold

**Reasoning**:
- ✅ Allows minor issues (one weak dimension)
- ✅ Blocks major problems (multiple failures)
- ✅ Configurable per function
- ✅ Industry standard (B grade)

## Performance Considerations

### Caching Strategy

```python
# Standards cached after first load
standard = load_standard("my_standard")  # File I/O
standard = load_standard("my_standard")  # Cache hit

# Assessment results cached per run
# (Not persisted between runs)
```

### Sampling for Large Datasets

```python
# Auto-samples datasets > 10K rows
if len(data) > 10000:
    sample = data.sample(n=10000)
    assess(sample)  # Faster validation
```

### Lazy Loading

```python
# Standards loaded on-demand
@adri_protected(contract="data", data_param="data")
def process(data):
    pass  # Standard not loaded yet

process(data)  # Standard loaded here
```

## Next Steps

- [Getting Started](GETTING_STARTED.md) - Basic usage
- [How It Works](HOW_IT_WORKS.md) - Quality dimensions
- [API Reference](API_REFERENCE.md) - Complete API
- [Contributing](../CONTRIBUTING.md) - Contribute code

---

**Understanding the architecture enables advanced customization and contributions.**
