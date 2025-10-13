# Tier 2: Medium System Flow Diagram

This diagram shows ADRI's main processing paths for package consumers who need to understand "how to use it" - about 10-15 components showing both entry points and key processing stages.

## Mermaid Diagram Code

```mermaid
flowchart TB
    subgraph Entry["🚪 Entry Points"]
        CLI[CLI Commands<br/>assess, generate, setup]
        DEC[@adri_protected<br/>Decorator]
    end

    subgraph Data["📊 Data Ingestion"]
        LOAD[Data Loaders<br/>CSV, JSON, Parquet]
        PROF[Data Profiler<br/>Pattern Analysis]
    end

    subgraph Standards["📋 Standards System"]
        PARSE[Standards Parser<br/>YAML Loading]
        VALID[StandardValidator<br/>Schema Validation]
        GEN[Standard Generator<br/>Auto-Creation]
        CACHE[Standards Cache]
    end

    subgraph Validation["🔍 Validation Engine"]
        RULES[Validation Rules<br/>Field-Level Checks]
        ENGINE[Assessment Engine<br/>5-Dimension Scoring]
        RESULT[Assessment Result<br/>Score + Failures]
    end

    subgraph Protection["🛡️ Protection Layer"]
        MODES[Protection Modes<br/>raise/warn/continue]
        DECIDE{Decision<br/>Allow or Block?}
    end

    subgraph Output["📝 Output & Logging"]
        LOGS[Audit Logs<br/>5-File Trail]
        REPORT[Assessment Reports<br/>JSON/CSV]
    end

    %% CLI Flow
    CLI --> LOAD
    CLI --> GEN
    LOAD --> PROF
    PROF --> GEN
    GEN --> PARSE

    %% Decorator Flow
    DEC --> LOAD
    DEC --> PARSE

    %% Common Flow
    PARSE --> VALID
    VALID --> CACHE
    CACHE --> RULES
    LOAD --> ENGINE
    RULES --> ENGINE
    ENGINE --> RESULT

    %% Protection Decision
    RESULT --> MODES
    MODES --> DECIDE
    DECIDE -->|Score ≥ min| ALLOW[✅ Function Runs]
    DECIDE -->|Score < min| BLOCK[❌ Protection Error]

    %% Logging
    RESULT --> LOGS
    RESULT --> REPORT
    ALLOW --> LOGS
    BLOCK --> LOGS

    style Entry fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    style Data fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    style Standards fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    style Validation fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style Protection fill:#ffebee,stroke:#f44336,stroke-width:2px
    style Output fill:#fafafa,stroke:#757575,stroke-width:2px
    style ALLOW fill:#c8e6c9,stroke:#4caf50,stroke-width:3px
    style BLOCK fill:#ffcdd2,stroke:#f44336,stroke-width:3px
```

## Usage Context

This diagram should be used in:
- docs/docs/intro.md (Documentation landing page)
- Architecture overview sections
- Integration guides for developers
- Technical presentations for package consumers

## Key Components Shown

1. **Entry Points** (2)
   - CLI commands for standalone usage
   - Decorator for function protection

2. **Data Ingestion** (2)
   - Multi-format data loaders
   - Data profiling for pattern analysis

3. **Standards System** (4)
   - YAML parsing and loading
   - StandardValidator for schema validation
   - Automatic standard generation
   - Smart caching for performance

4. **Validation Engine** (3)
   - Field-level validation rules
   - 5-dimension assessment engine
   - Comprehensive result objects

5. **Protection Layer** (2)
   - Configurable protection modes
   - Allow/block decision making

6. **Output & Logging** (2)
   - 5-file audit trail
   - JSON/CSV assessment reports

## Design Rationale

- **Grouped by function** = Clear separation of concerns
- **Two entry points** = Shows both CLI and decorator usage
- **Complete flow** = From input to decision to output
- **Color coding** = Visual grouping of related components
- **~13 components** = Right level of detail for understanding without overwhelming
- **StandardValidator included** = Shows validation happens at standard loading time

## Key Flows Illustrated

1. **CLI Generate Flow**: CLI → Load Data → Profile → Generate Standard → Parse → Validate
2. **Decorator Protection Flow**: Decorator → Load Data → Parse Standard → Validate → Assess → Decide → Log
3. **Common Assessment Path**: Data + Standards → Rules → Engine → Result → Decision
