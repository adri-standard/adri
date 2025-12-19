# Tier 3: Complete Technical Architecture Diagram

This is the comprehensive technical architecture for contributors who need to understand "how it works" - showing all components, their relationships, and the complete data flow through ADRI.

## Mermaid Diagram Code

```mermaid
flowchart TB
    subgraph CLI["💻 CLI Layer (src/adri/cli.py)"]
        CLI_SETUP[adri setup]
        CLI_GEN[adri generate-standard]
        CLI_ASSESS[adri assess]
        CLI_LIST[adri list-standards]
        CLI_VALIDATE[adri validate-standard]
        CLI_SHOW_STD[adri show-standard]
        CLI_SHOW_CFG[adri show-config]
        CLI_LIST_ASSESS[adri list-assessments]
    end

    subgraph Guard["🛡️ Guard Decorator (src/adri/decorator.py)"]
        DECORATOR[@adri_protected<br/>Main Entry Point]
        PARAM_EXTRACT[Parameter Extraction]
        DATA_RESOLVE[Data Resolution]
    end

    subgraph Config["⚙️ Configuration (src/adri/config/)"]
        CONFIG_LOADER[ConfigurationLoader<br/>loader.py]
        ENV_DETECT[Environment Detection]
        PATH_RESOLVE[Path Resolution]
    end

    subgraph Loaders["📥 Data Loaders (src/adri/validator/loaders.py)"]
        LOAD_CSV[load_csv]
        LOAD_JSON[load_json]
        LOAD_PARQUET[load_parquet]
        LOAD_STANDARD[load_standard]
        TYPE_DETECT[Type Detection]
    end

    subgraph Analysis["🧠 Analysis Engine (src/adri/analysis/)"]
        PROFILER[DataProfiler<br/>data_profiler.py]
        TYPE_INFER[TypeInference<br/>type_inference.py]
        STD_GEN[StandardGenerator<br/>standard_generator.py]
        DIM_BUILDER[DimensionBuilder<br/>dimension_builder.py]
        STD_BUILDER[StandardBuilder<br/>standard_builder.py]
        FIELD_INFER[FieldInference<br/>field_inference.py]
    end

    subgraph Standards["📋 Standards System (src/adri/contracts/)"]
        STD_PARSER[StandardsParser<br/>parser.py]
        STD_VALIDATOR[StandardValidator<br/>validator.py]
        STD_SCHEMA[StandardSchema<br/>schema.py]
        STD_CACHE[Standards Cache<br/>In-Memory]
        STD_EXCEPTIONS[ValidationResult<br/>exceptions.py]
    end

    subgraph Validator["🔍 Validation Engine (src/adri/validator/)"]
        VAL_ENGINE[ValidationEngine<br/>engine.py]
        DATA_ASSESSOR[DataQualityAssessor<br/>engine.py]
        VAL_RULES[Validation Rules<br/>rules.py]
        ASSESS_RESULT[AssessmentResult<br/>engine.py]
        FIELD_VAL[Field Validators<br/>rules.py]
    end

    subgraph Protection["🛡️ Protection System (src/adri/guard/modes.py)"]
        PROT_ENGINE[DataProtectionEngine]
        FAIL_FAST[FailFastMode]
        SELECTIVE[SelectiveMode]
        WARN_ONLY[WarnOnlyMode]
        PROT_RESULT[ProtectionResult]
    end

    subgraph Logging["📝 Logging System (src/adri/logging/)"]
        LOCAL_LOG[LocalLogger<br/>local.py]
        ENT_LOG[EnterpriseLogger<br/>enterprise.py]
        AUDIT_LOGS[Audit Logs<br/>5-File Trail]
        LOG_ROTATION[File Rotation]
    end

    %% CLI Flows
    CLI_SETUP --> CONFIG_LOADER
    CLI_GEN --> LOAD_CSV
    CLI_GEN --> LOAD_JSON
    CLI_GEN --> LOAD_PARQUET
    CLI_ASSESS --> LOAD_STANDARD
    CLI_VALIDATE --> STD_VALIDATOR
    CLI_LIST --> CONFIG_LOADER
    CLI_SHOW_STD --> STD_PARSER

    %% Decorator Flow
    DECORATOR --> PARAM_EXTRACT
    PARAM_EXTRACT --> DATA_RESOLVE
    DATA_RESOLVE --> LOAD_CSV
    DATA_RESOLVE --> LOAD_JSON
    DATA_RESOLVE --> LOAD_PARQUET
    DECORATOR --> CONFIG_LOADER

    %% Configuration Flow
    CONFIG_LOADER --> ENV_DETECT
    CONFIG_LOADER --> PATH_RESOLVE

    %% Data Loading Flow
    LOAD_CSV --> TYPE_DETECT
    LOAD_JSON --> TYPE_DETECT
    LOAD_PARQUET --> TYPE_DETECT
    TYPE_DETECT --> PROFILER

    %% Analysis Flow
    PROFILER --> TYPE_INFER
    TYPE_INFER --> FIELD_INFER
    FIELD_INFER --> DIM_BUILDER
    DIM_BUILDER --> STD_BUILDER
    STD_BUILDER --> STD_GEN
    STD_GEN --> STD_PARSER

    %% Standards Flow - WITH VALIDATOR
    LOAD_STANDARD --> STD_PARSER
    STD_PARSER --> STD_VALIDATOR
    STD_VALIDATOR --> STD_SCHEMA
    STD_VALIDATOR --> STD_EXCEPTIONS
    STD_VALIDATOR --> STD_CACHE
    STD_CACHE --> VAL_RULES

    %% Validation Flow
    TYPE_DETECT --> VAL_ENGINE
    VAL_RULES --> VAL_ENGINE
    VAL_ENGINE --> DATA_ASSESSOR
    DATA_ASSESSOR --> FIELD_VAL
    FIELD_VAL --> ASSESS_RESULT

    %% Protection Flow
    ASSESS_RESULT --> PROT_ENGINE
    PROT_ENGINE --> FAIL_FAST
    PROT_ENGINE --> SELECTIVE
    PROT_ENGINE --> WARN_ONLY
    FAIL_FAST --> PROT_RESULT
    SELECTIVE --> PROT_RESULT
    WARN_ONLY --> PROT_RESULT

    %% Logging Flow
    ASSESS_RESULT --> LOCAL_LOG
    ASSESS_RESULT --> ENT_LOG
    PROT_RESULT --> LOCAL_LOG
    PROT_RESULT --> ENT_LOG
    LOCAL_LOG --> AUDIT_LOGS
    LOCAL_LOG --> LOG_ROTATION
    ENT_LOG --> AUDIT_LOGS

    style CLI fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    style Guard fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    style Config fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    style Loaders fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style Analysis fill:#f1f8e9,stroke:#7cb342,stroke-width:2px
    style Standards fill:#fff8e1,stroke:#ffa726,stroke-width:3px
    style Validator fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style Protection fill:#ffebee,stroke:#f44336,stroke-width:2px
    style Logging fill:#fafafa,stroke:#757575,stroke-width:2px
    style STD_VALIDATOR fill:#ffe0b2,stroke:#ff6f00,stroke-width:4px
```

## Usage Context

This diagram should be used in:
- ARCHITECTURE.md (Primary technical reference)
- Contributor onboarding documentation
- Code review discussions
- Architecture decision records
- Technical deep-dive presentations

## Complete Component List (30+ Components)

### 1. CLI Layer (8 commands)
- `adri setup` - Initialize project structure
- `adri generate-standard` - Create standards from data
- `adri assess` - Validate data against standards
- `adri list-standards` - Show available standards
- `adri validate-standard` - Validate standard files
- `adri show-standard` - Display standard details
- `adri show-config` - Display configuration
- `adri list-assessments` - List assessment history

### 2. Guard Decorator (3 components)
- `@adri_protected` - Main decorator entry point
- Parameter extraction logic
- Data resolution and loading

### 3. Configuration System (3 components)
- `ConfigurationLoader` - Load and manage config
- Environment detection (dev/prod)
- Path resolution utilities

### 4. Data Loaders (5 components)
- `load_csv` - CSV file loading
- `load_json` - JSON file loading
- `load_parquet` - Parquet file loading
- `load_standard` - YAML standard loading
- Type detection and inference

### 5. Analysis Engine (6 components)
- `DataProfiler` - Analyze data patterns
- `TypeInference` - Infer field types
- `StandardGenerator` - Create standards
- `DimensionBuilder` - Build dimension requirements
- `StandardBuilder` - Orchestrate standard creation
- `FieldInference` - Infer field-level rules

### 6. Standards System (5 components) ⭐ **INCLUDES STANDARDVALIDATOR**
- `StandardsParser` - Parse YAML standards
- `StandardValidator` - Validate standard schema (**NEW IN DOCS**)
- `StandardSchema` - Meta-schema definitions
- Standards cache (in-memory)
- `ValidationResult` - Validation result objects

### 7. Validation Engine (5 components)
- `ValidationEngine` - Main validation orchestrator
- `DataQualityAssessor` - 5-dimension assessment
- `ValidationRules` - Field-level validation logic
- `AssessmentResult` - Result objects with scores
- Field validators (type, format, range checks)

### 8. Protection System (5 components)
- `DataProtectionEngine` - Protection orchestrator
- `FailFastMode` - Raise errors on failure
- `SelectiveMode` - Log warnings, continue
- `WarnOnlyMode` - Monitor only, never block
- `ProtectionResult` - Decision result objects

### 9. Logging System (5 components)
- `LocalLogger` - CSV-based audit logging
- `EnterpriseLogger` - Verodat API integration
- 5-file audit trail structure
- File rotation management
- Thread-safe logging operations

## StandardValidator Integration ⭐

**Critical Addition**: The `StandardValidator` component was missing from previous architecture documentation but exists in the codebase at `src/adri/contracts/validator.py`.

**Role in Architecture**:
1. **Validates standards at load time** - Ensures YAML standards conform to schema before use
2. **Smart caching** - Caches validation results with mtime-based invalidation
3. **Thread-safe operation** - Supports concurrent validation requests
4. **Comprehensive checks** - Structure, type, range, and cross-field validation

**Flow Position**:
```
StandardsParser → StandardValidator → StandardSchema
                       ↓
                 StandardCache → ValidationRules
```

**Why It Matters**:
- **Fail fast on bad standards** - Catches schema errors before runtime
- **Performance optimization** - Caching prevents repeated validation
- **Quality assurance** - Ensures standards meet quality requirements
- **Developer feedback** - Clear error messages for standard authors

## Design Rationale

- **Layered architecture** = Clear separation of concerns
- **File references** = Every component maps to actual source files
- **Complete component set** = All 30+ major components shown
- **Data flow clarity** = Arrows show information movement
- **StandardValidator highlighted** = Special emphasis on new component
- **Color coding** = Visual grouping by functional area
- **Subgraph organization** = Logical grouping by module

## Key Data Flows

1. **CLI Generate Flow**:
   ```
   CLI → Load Data → Profile → Infer Types → Build Dimensions →
   Generate Standard → Parse → Validate → Cache
   ```

2. **Decorator Protection Flow**:
   ```
   Decorator → Load Data → Load Standard → Parse → Validate →
   Cache → Assess → Protect → Log
   ```

3. **Standard Validation Flow** (NEW):
   ```
   Load Standard → Parser → StandardValidator → Schema Check →
   ValidationResult → Cache (if valid)
   ```

## Component Status

- ✅ **Production Ready**: CLI, Decorator, Validator, Protection, Config
- 🚧 **In Development**: Analysis, Type Inference, Standard Generator
- 📋 **Planned**: Enterprise Logger, Framework Integrations

## Cross-Module Dependencies

- **Config → All Modules**: Provides paths and settings
- **Loaders → Validator**: Supplies data for assessment
- **Standards → Validator**: Provides rules for assessment
- **Validator → Protection**: Supplies scores for decisions
- **All → Logging**: Records all activities

## Performance Considerations

- **Caching**: Standards cache, validation cache
- **Lazy Loading**: Standards loaded on-demand
- **Thread Safety**: Validation and logging support concurrency
- **File Rotation**: Prevents unbounded log growth
