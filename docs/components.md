# ADRI Component Descriptions

## Core Components

### Data Source Connectors
The entry points for data that will be assessed by the ADRI system. Connectors provide a uniform interface for different data sources:
- **FileConnector**: CSV, Excel, JSON, and other file formats
- **DatabaseConnector**: SQL databases (PostgreSQL, MySQL, SQLite)
- **APIConnector**: RESTful API endpoints
- **Custom Connectors**: Extensible for proprietary formats

### Configuration System
Manages application settings and customization options for the ADRI assessment process:
- Configures dimension weights and scoring thresholds
- Sets assessment modes (Discovery, Validation, Auto)
- Manages template selection and compliance
- Provides environment-specific settings

### Template System
Defines quality requirements for specific use cases:
- YAML-based template definitions
- Industry-specific quality standards
- Compliance thresholds per dimension
- Business logic rules and validations

### Dimension Registry
Central registry that manages the assessment dimensions:
- Dynamically loads dimension assessors
- Maps dimensions to their implementations
- Enables custom dimension registration
- Manages dimension configurations

## Assessment Dimensions

### Validity
Assesses whether data adheres to defined syntax and format rules:
- Validates data types (string, numeric, date, etc.)
- Checks format patterns (email, phone, postal codes)
- Verifies value ranges and boundaries
- Enforces required fields and constraints
- Template-specific validation rules

### Completeness
Measures the extent to which expected data is present:
- Checks for null or missing values
- Evaluates required field population
- Assesses optional field coverage
- Calculates completeness percentages
- Template-defined completeness requirements

### Freshness
Determines whether data is sufficiently recent for its intended use:
- Tracks data creation and modification timestamps
- Evaluates update frequency against requirements
- Identifies stale or outdated records
- Assesses temporal validity of time-sensitive data
- Template-based freshness thresholds

### Consistency
Examines data for internal coherence and alignment:
- Checks for contradictions within records
- Verifies calculated field accuracy
- Ensures uniform representation of values
- Validates business logic consistency
- Template-specific consistency rules

### Plausibility
Evaluates whether data appears reasonable and likely to be correct:
- Analyzes statistical distributions for outliers
- Checks for logical relationships between fields
- Validates against domain knowledge
- Identifies improbable data patterns
- Template-defined plausibility checks

## Assessment Components

### DataSourceAssessor
The central orchestration component that coordinates the assessment process:
- Manages assessment modes (Discovery/Validation/Auto)
- Coordinates dimension assessments
- Applies template requirements
- Aggregates scores across dimensions
- Generates metadata in Discovery mode

### ADRIScoreReport
The comprehensive assessment output:
- Overall readiness score (0-100)
- Individual dimension scores (0-20)
- Detailed findings and recommendations
- Template compliance evaluation
- Multiple output formats (JSON, HTML, text)

### Template Evaluation
Evaluates data against template requirements:
- Checks compliance with thresholds
- Identifies quality gaps
- Provides actionable recommendations
- Tracks template version compatibility

### Metadata Generator
Creates companion metadata files in Discovery mode:
- Infers data types and constraints
- Generates validity rules
- Creates freshness requirements
- Produces completeness expectations
- Builds consistency validations

## Integration Components

### ADRI Guard
Protects agent functions from poor quality data:
- Decorator-based implementation
- Configurable quality thresholds
- Dimension-specific requirements
- Automatic data validation
- Error handling and logging

### Framework Integrations
Native support for AI agent frameworks:
- **LangChain**: Tool and chain integration
- **CrewAI**: Task and tool support
- **DSPy**: Module integration
- **Custom**: Extensible integration patterns

## Architecture Flow

```
Data Source → Connector → DataSourceAssessor → Dimensions → Report
                              ↓                    ↑
                          Templates ———————————————→
```

The assessment flow:
1. Data source is accessed via appropriate connector
2. DataSourceAssessor orchestrates the assessment
3. Each dimension evaluates the data independently
4. Template requirements are applied to dimension results
5. ADRIScoreReport aggregates all findings
6. Report is generated in requested format(s)

## Extension Points

ADRI is designed for extensibility:
- **Custom Connectors**: Add support for new data sources
- **Custom Dimensions**: Implement domain-specific quality checks
- **Custom Templates**: Define industry-specific requirements
- **Custom Integrations**: Add support for new frameworks

## Purpose & Test Coverage

**Why this file exists**: Provides detailed documentation of ADRI's core components, their responsibilities, and how they interact within the current system architecture.

**Key responsibilities**:
- Document current system components and their functions
- Explain the five assessment dimensions in detail
- Describe assessment orchestration and reporting
- Show data flow through the system
- Guide understanding of extension points

**Test coverage**: This document's descriptions and component behaviors are verified by tests documented in [components_test_coverage.md](./test_coverage/components_test_coverage.md)
