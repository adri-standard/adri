# Getting Started with ADRI

## What is ADRI?

The Agent Data Readiness Index (ADRI) helps you ensure your AI agents are working with reliable data. Think of it as a "health check" for your data sources that:

- Prevents your agents from making decisions based on flawed data
- Gives you confidence in your agent workflows
- Helps you communicate data quality requirements to data providers
- Protects AI systems from unreliable data inputs

## Choose Your Path

```mermaid
flowchart TD
    Start([Want to use ADRI?])
    
    Q1{Are you<br/>building an<br/>AI agent?}
    Q2{Do you have<br/>existing data?}
    Q3{Need to assess<br/>data quality?}
    
    A1[Install ADRI<br/>pip install adri]
    A2[Define Requirements<br/>Create template.yaml]
    A3[Run Assessment<br/>adri assess data.csv]
    A4[Add Guards<br/>@adri_guarded decorator]
    
    B1[Generate Metadata<br/>adri generate data.csv]
    B2[Review Scores<br/>Check reports]
    B3[Improve Data<br/>Fix issues]
    
    C1[Explore Examples<br/>examples/]
    C2[Read Docs<br/>docs/GET_STARTED.md]
    
    Start --> Q1
    Q1 -->|Yes| A1
    Q1 -->|No| Q2
    
    A1 --> A2
    A2 --> A3
    A3 --> A4
    
    Q2 -->|Yes| Q3
    Q2 -->|No| C1
    
    Q3 -->|Yes| B1
    Q3 -->|No| C2
    
    B1 --> B2
    B2 --> B3
    
    C1 --> A1
    C2 --> A1
    
    style Start fill:#1e293b,stroke:#0f172a,stroke-width:3px,color:#fff
    style A1 fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    style A2 fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    style A3 fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    style A4 fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    style B1 fill:#3b82f6,stroke:#2563eb,stroke-width:2px,color:#fff
    style B2 fill:#3b82f6,stroke:#2563eb,stroke-width:2px,color:#fff
    style B3 fill:#3b82f6,stroke:#2563eb,stroke-width:2px,color:#fff
    style C1 fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff
    style C2 fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff
```

## Quick Installation

```bash
pip install adri
```

## 5-Minute Assessment Example

Let's check a sample dataset. Here's how ADRI works:

```mermaid
graph LR
    subgraph "Input"
        DS[Data Source<br/>CSV/JSON/DB/API]
        T[Template<br/>Requirements]
    end
    
    subgraph "ADRI Assessment Process"
        C[Connector<br/>Loads Data]
        D1[Validity Check<br/>Format & Types]
        D2[Completeness Check<br/>Required Fields]
        D3[Freshness Check<br/>Timeliness]
        D4[Consistency Check<br/>Logical Coherence]
        D5[Plausibility Check<br/>Domain Sense]
        
        S[Score Calculation<br/>0-100 per dimension]
        A[Aggregate Results]
    end
    
    subgraph "Output"
        R[Assessment Report]
        M[Metadata Files<br/>.validity.json<br/>.completeness.json<br/>etc.]
        G[Guard Decision<br/>Pass/Fail]
    end
    
    DS --> C
    T --> C
    C --> D1
    C --> D2
    C --> D3
    C --> D4
    C --> D5
    
    D1 --> S
    D2 --> S
    D3 --> S
    D4 --> S
    D5 --> S
    
    S --> A
    A --> R
    A --> M
    A --> G
    
    style DS fill:#ffd43b,stroke:#fab005
    style T fill:#74c0fc,stroke:#339af0
    style C fill:#8ce99a,stroke:#51cf66
    style D1 fill:#ff8cc3,stroke:#e64980
    style D2 fill:#ff8cc3,stroke:#e64980
    style D3 fill:#ff8cc3,stroke:#e64980
    style D4 fill:#ff8cc3,stroke:#e64980
    style D5 fill:#ff8cc3,stroke:#e64980
    style S fill:#a5d8ff,stroke:#74c0fc
    style A fill:#a5d8ff,stroke:#74c0fc
    style R fill:#d0ebff,stroke:#a5d8ff
    style M fill:#d0ebff,stroke:#a5d8ff
    style G fill:#d0ebff,stroke:#a5d8ff
```

Now let's run an assessment:

```python
from adri import DataSourceAssessor

# Create an assessor
assessor = DataSourceAssessor()

# Analyze a data file
report = assessor.assess_file("customer_data.csv")

# See the results
print(f"Overall score: {report.overall_score}/100")
print(f"Readiness level: {report.readiness_level}")

# Get specific dimension scores
for dimension, results in report.dimension_results.items():
    print(f"{dimension}: {results['score']}/20")

# View key findings
for finding in report.summary_findings[:5]:
    print(f"- {finding}")

# Save the report
report.save_json("customer_data_assessment.json")
```

## Understanding Your Results

Your assessment gives you:

1. **Overall score** (0-100): How ready your data is for agent use
2. **Readiness level**: Plain-language assessment (e.g., "Proficient - Suitable for most production agent uses")
3. **Dimension scores**: Breakdown across 5 key reliability areas
4. **Findings**: Specific insights about your data
5. **Recommendations**: Actions to improve reliability

### The Five Dimensions

```mermaid
graph TB
    subgraph wheel [" "]
        V[Validity<br/>✓ Correct formats<br/>✓ Proper types<br/>✓ Valid ranges]
        C[Completeness<br/>✓ Required fields<br/>✓ No missing data<br/>✓ Adequate coverage]
        F[Freshness<br/>✓ Recent data<br/>✓ Timely updates<br/>✓ Not stale]
        CO[Consistency<br/>✓ Logical coherence<br/>✓ No contradictions<br/>✓ Referential integrity]
        P[Plausibility<br/>✓ Makes sense<br/>✓ Domain appropriate<br/>✓ Realistic values]
        
        CENTER[ADRI<br/>Data Quality<br/>Dimensions]
        
        CENTER -.->|Score 0-100| V
        CENTER -.->|Score 0-100| C
        CENTER -.->|Score 0-100| F
        CENTER -.->|Score 0-100| CO
        CENTER -.->|Score 0-100| P
        
        V -.-> C
        C -.-> F
        F -.-> CO
        CO -.-> P
        P -.-> V
    end
    
    style V fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px,color:#fff
    style C fill:#4ecdc4,stroke:#0ca678,stroke-width:3px,color:#fff
    style F fill:#a78bfa,stroke:#7c3aed,stroke-width:3px,color:#fff
    style CO fill:#fbbf24,stroke:#f59e0b,stroke-width:3px
    style P fill:#60a5fa,stroke:#3b82f6,stroke-width:3px,color:#fff
    style CENTER fill:#1e293b,stroke:#0f172a,stroke-width:4px,color:#fff,font-weight:bold
    
    classDef wheelStyle fill:none,stroke:none
    class wheel wheelStyle
```

### Readiness Levels

| Score Range | Level | Description |
|-------------|-------|-------------|
| 80-100 | Advanced | Ready for critical agentic applications |
| 60-79 | Proficient | Suitable for most production agent uses |
| 40-59 | Basic | Requires caution in agent applications |
| 20-39 | Limited | Significant agent blindness risk |
| 0-19 | Inadequate | Not recommended for agentic use |

## Visualizing Results

ADRI makes it easy to visualize your assessment results:

```python
# Generate a radar chart
report.generate_radar_chart("data_readiness_radar.png")

# Create an HTML report with detailed findings
report.save_html("data_readiness_report.html")
```

## Protecting Your Agent with Guards

Add safeguards to your agent workflows to ensure they only process sufficiently reliable data:

```python
from adri import adri_guarded

# Apply a guard that requires an overall score of at least 70
# and a plausibility score of at least 15
@adri_guarded(min_score=70, dimensions={"plausibility": 15})
def process_data(data_source):
    # Your agent workflow here
    results = analyze_with_agent(data_source)
    return results

# Use the protected function
try:
    results = process_data("customer_data.csv")
    print("Success! Data was reliable enough for processing.")
except Exception as e:
    print(f"Data reliability guard prevented processing: {e}")
```

### Framework-Specific Guards

ADRI provides integrations for popular agent frameworks:

#### LangChain Example

```python
from adri.integrations.langchain import create_adri_tool
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI

# Create ADRI tool with reliability requirements
adri_tool = create_adri_tool(min_score=70)

# Create an agent with the ADRI tool
llm = OpenAI(temperature=0)
agent = initialize_agent(
    [adri_tool], 
    llm, 
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

# Use the agent to assess data quality
result = agent.run("Assess the quality of customer_data.csv")
```

## Next Steps

- Learn about the [five dimensions](./UNDERSTANDING_DIMENSIONS.md) of data reliability
- Explore configuration options in the [API reference](./API_REFERENCE.md#configuration)
- See how to [enhance your data sources](./ENHANCING_DATA_SOURCES.md) with explicit metadata
- Check out [framework integrations](./INTEGRATIONS.md) for LangChain, CrewAI, and more
- View the full [API reference](./API_REFERENCE.md) for complete details

## Purpose & Test Coverage

**Why this file exists**: Provides a quick, practical introduction to ADRI, enabling new users to install the tool and run their first data quality assessment within minutes.

**Key responsibilities**:
- Guide users through installation process
- Demonstrate basic usage with simple examples
- Show how to interpret assessment results
- Provide clear next steps for deeper exploration

**Test coverage**: Verified by tests documented in [GET_STARTED_test_coverage.md](./test_coverage/GET_STARTED_test_coverage.md)
