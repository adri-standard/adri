# LangChain Integration Guide

Integrate ADRI with LangChain for real-time data quality assessment.

## Installation

```bash
pip install adri[langchain]
```

## Basic Integration

```python
<!-- audience: ai-builders -->
from langchain.chains import LLMChain
from adri.integrations.langchain import ADRIGuard

# Create ADRI guard
guard = ADRIGuard(
    dimensions=['completeness', 'validity', 'freshness'],
    thresholds={'completeness': 0.8, 'validity': 0.9}
)

# Integrate with LangChain
chain = LLMChain(
    llm=your_llm,
    prompt=your_prompt,
    input_guard=guard  # Validate input data
)

# Use with quality checking
result = chain.run(input_data)
```

## Advanced Patterns

```python
<!-- audience: ai-builders -->
from adri.integrations.langchain import QualityCallback

# Add quality monitoring callback
callback = QualityCallback(
    alert_threshold=0.7,
    log_all_assessments=True
)

chain = LLMChain(
    llm=your_llm,
    prompt=your_prompt,
    callbacks=[callback]
)
```
