# CrewAI Integration Guide

Use ADRI with CrewAI for multi-agent data quality assessment.

## Installation

```bash
pip install adri[crewai]
```

## Agent Integration

```python
<!-- audience: ai-builders -->
from crewai import Agent, Task, Crew
from adri.integrations.crewai import QualityAgent

# Create quality assessment agent
quality_agent = QualityAgent(
    role="Data Quality Specialist",
    goal="Ensure all data meets quality standards",
    backstory="Expert in data quality assessment and validation"
)

# Create crew with quality agent
crew = Crew(
    agents=[quality_agent, your_other_agents],
    tasks=[quality_task, your_other_tasks]
)

# Run with quality assessment
result = crew.kickoff()
```
