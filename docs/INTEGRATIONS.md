# ADRI Integrations

This guide explains how to use the Agent Data Readiness Index (ADRI) integrations with popular AI agent frameworks.

## Table of Contents

- [ADRI Guard Decorator](#adri-guard-decorator)
- [LangChain Integration](#langchain-integration)
- [DSPy Integration](#dspy-integration)
- [CrewAI Integration](#crewai-integration)
- [Installation Requirements](#installation-requirements)
- [Examples](#examples)

## ADRI Guard Decorator

The `adri_guarded` decorator allows you to enforce data quality standards in any function that works with data sources. It assesses the quality of a data source before allowing the decorated function to proceed.

### Usage

```python
from adri.integrations import adri_guarded

@adri_guarded(min_score=70)
def analyze_customer_data(data_source, analysis_type):
    """
    This function will only run if data_source meets
    the minimum quality score of 70
    """
    print(f"Analyzing {data_source} for {analysis_type}")
    # ... analysis code ...
    return results
```

### Parameters

- `min_score`: Minimum ADRI score required to proceed (0-100)
- `data_source_param`: Name of the parameter containing the data source path (default: "data_source")

### Behavior

1. The decorator assesses the data source using ADRI
2. If the quality score is below the minimum, it raises a ValueError with details about the issues
3. If the quality is sufficient, it proceeds with the function call

## LangChain Integration

The LangChain integration provides tools that can be used by LangChain agents to assess data quality.

### Usage

```python
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI
from adri.integrations.langchain import create_adri_tool

# Create LangChain agent with ADRI tool
llm = OpenAI(temperature=0)
adri_tool = create_adri_tool(min_score=70)
agent = initialize_agent(
    [adri_tool], 
    llm, 
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

# Use the agent
agent.run("Assess the quality of customer_data.csv for use in a recommendation system")
```

### Functions

- `create_adri_tool(min_score=None)`: Creates a LangChain Tool for data quality assessment

## DSPy Integration

The DSPy integration provides modules that can be used in DSPy pipelines to assess data quality.

### Usage

```python
import dspy
from adri.integrations.dspy import ADRIModule

# Create a DSPy pipeline with ADRI assessment
class DataQualityPipeline(dspy.Module):
    def __init__(self):
        super().__init__()
        self.adri = ADRIModule(min_score=70)
        self.analyzer = dspy.ChainOfThought("data_analysis")
        
    def forward(self, data_path):
        # First assess data quality
        quality_report = self.adri(data_path)
        
        # Only proceed if quality is sufficient
        if quality_report.score >= 70:
            analysis = self.analyzer(
                data=data_path,
                quality_report=quality_report
            )
            return analysis
        else:
            return f"Data quality insufficient: {quality_report.readiness_level}"
```

### Classes

- `ADRIModule(min_score=None)`: DSPy module for data quality assessment

## CrewAI Integration

The CrewAI integration provides agents and tools that can be used in CrewAI workflows to assess data quality.

### Usage

```python
from crewai import Crew, Task
from adri.integrations.crewai import create_data_quality_agent

# Create a data quality agent
data_quality_agent = create_data_quality_agent(min_score=70)

# Create a task for the agent
assess_task = Task(
    description="Assess the quality of customer_data.csv",
    expected_output="A detailed assessment of data quality",
    agent=data_quality_agent
)

# Create a crew with the agent and task
crew = Crew(
    agents=[data_quality_agent],
    tasks=[assess_task]
)

# Run the crew
result = crew.kickoff()
```

### Functions

- `assess_data_quality(data_source_path, min_score=None)`: Assesses the quality of a data source
- `create_data_quality_agent(min_score=None)`: Creates a CrewAI agent for data quality assessment

## Installation Requirements

Each integration requires the corresponding framework to be installed:

```bash
# For LangChain integration
pip install langchain

# For DSPy integration
pip install dspy

# For CrewAI integration
pip install crewai
```

The ADRI Guard decorator doesn't require any additional dependencies.

## Examples

For complete examples of each integration, see the `examples` directory in the [GitHub repository](https://github.com/verodat/agent-data-readiness-index/tree/main/examples):

- [Guard Decorator Example](https://github.com/verodat/agent-data-readiness-index/blob/main/examples/guard/decorator_example.py)
- [LangChain Example](https://github.com/verodat/agent-data-readiness-index/blob/main/examples/langchain/langchain_example.py)
- [DSPy Example](https://github.com/verodat/agent-data-readiness-index/blob/main/examples/dspy/dspy_example.py)
- [CrewAI Example](https://github.com/verodat/agent-data-readiness-index/blob/main/examples/crewai/crewai_example.py)
- [Interactive Mode Example](https://github.com/verodat/agent-data-readiness-index/blob/main/examples/interactive/interactive_example.py)
