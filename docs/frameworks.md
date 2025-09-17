# Framework Examples

**Copy-paste ready code for protecting your AI agents across all major frameworks.**

## LangChain

```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from adri import adri_protected

@adri_protected(standard="customer_data")
def langchain_analysis(customer_data):
    """Analyze customer data with LangChain"""
    llm = OpenAI(temperature=0.7)
    prompt = PromptTemplate.from_template(
        "Analyze this customer data: {data}"
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(data=str(customer_data))

# Usage
customer_data = [
    {"name": "John Doe", "age": 30, "email": "john@example.com"},
    {"name": "Jane Smith", "age": 25, "email": "jane@example.com"}
]
analysis = langchain_analysis(customer_data)
```

## CrewAI

```python
from crewai import Agent, Task, Crew
from adri import adri_protected

@adri_protected(standard="market_data")
def crewai_analysis(market_data):
    """Analyze market data with CrewAI crew"""
    analyst = Agent(
        role='Data Analyst',
        goal='Analyze market trends',
        backstory='Expert in market data analysis'
    )
    
    task = Task(
        description=f'Analyze this data: {market_data}',
        agent=analyst
    )
    
    crew = Crew(agents=[analyst], tasks=[task])
    return crew.kickoff()

# Usage
market_data = [
    {"stock": "AAPL", "price": 150.0, "volume": 1000000},
    {"stock": "GOOGL", "price": 2500.0, "volume": 500000}
]
analysis = crewai_analysis(market_data)
```

## AutoGen

```python
import autogen
from adri import adri_protected

@adri_protected(standard="financial_data")
def autogen_analysis(financial_data):
    """Multi-agent financial analysis with AutoGen"""
    assistant = autogen.AssistantAgent(
        name="analyst",
        llm_config={"model": "gpt-4"}
    )
    
    user_proxy = autogen.UserProxyAgent(
        name="user",
        human_input_mode="NEVER"
    )
    
    user_proxy.initiate_chat(
        assistant, 
        message=f"Analyze: {financial_data}"
    )
    return {"analysis_complete": True}

# Usage  
financial_data = [
    {"company": "AAPL", "revenue": 365.8, "profit": 94.7}
]
result = autogen_analysis(financial_data)
```

## LlamaIndex

```python
from llama_index.core.query_engine import PandasQueryEngine
import pandas as pd
from adri import adri_protected

@adri_protected(standard="sales_data")
def llamaindex_query(dataset, query):
    """Query analysis using LlamaIndex"""
    df = pd.DataFrame(dataset)
    query_engine = PandasQueryEngine(df=df)
    response = query_engine.query(query)
    return {"query": query, "response": str(response)}

# Usage
sales_data = [
    {"product": "Laptop", "sales": 1000, "region": "North"}
]
result = llamaindex_query(sales_data, "What are total sales?")
```

## Any Python Function

```python
from adri import adri_protected

@adri_protected(standard="your_data")
def your_agent_function(data):
    """Works with any Python function"""
    return your_ai_framework(data)  # Protected automatically
```

## Configuration

### Protection Modes
```python
# Strict protection (high-stakes workflows)
@adri_protected(standard="financial_data", min_score=95, mode="fail-fast")

# Selective blocking (removes only dirty records)  
@adri_protected(standard="customer_data", mode="selective")

# Warn-only (logs issues but doesn't block)
@adri_protected(standard="test_data", mode="warn")
```

### Custom Configuration
```yaml
# adri-config.yaml
validation:
  default_min_score: 80
  failure_mode: "raise"

audit:
  enabled: true
  log_file: "logs/adri_audit.jsonl"
```

---

**Need more examples?** Check [examples/use_cases/](../examples/use_cases/) for business scenarios or the [FAQ](../FAQ.md) for detailed information.
