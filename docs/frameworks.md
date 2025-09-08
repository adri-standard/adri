---
layout: default
title: Framework Examples - ADRI
---

# Framework Integration Examples

Copy-paste ready code for protecting your AI agents across all major frameworks.

## LangChain {#langchain}

### Protect LangChain Chains

```python
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from adri import adri_protected

@adri_protected
def langchain_analysis(customer_data):
    """Analyze customer data with LangChain"""

    llm = OpenAI(temperature=0.7)
    prompt = PromptTemplate(
        input_variables=["data"],
        template="Analyze this customer data and provide insights: {data}"
    )

    chain = LLMChain(llm=llm, prompt=prompt)

    # ADRI validates customer_data before processing
    result = chain.run(data=str(customer_data))
    return {"analysis": result, "data_quality": "validated"}

# Usage
customer_records = [
    {"name": "John Doe", "age": 30, "email": "john@example.com"},
    {"name": "Jane Smith", "age": 25, "email": "jane@example.com"}
]

analysis = langchain_analysis(customer_records)
```

### Protect LangChain Agents

```python
from langchain.agents import create_pandas_dataframe_agent
from langchain.llms import OpenAI
import pandas as pd
from adri import adri_protected

@adri_protected
def langchain_agent_query(data, query):
    """Query data using LangChain pandas agent"""

    # Convert to DataFrame (ADRI validates before conversion)
    df = pd.DataFrame(data)

    llm = OpenAI(temperature=0)
    agent = create_pandas_dataframe_agent(llm, df, verbose=True)

    result = agent.run(query)
    return {"query": query, "result": result}

# Usage
result = langchain_agent_query(
    data=[{"sales": 1000, "region": "US"}, {"sales": 1500, "region": "EU"}],
    query="What is the total sales by region?"
)
```

## CrewAI {#crewai}

### Protect CrewAI Tasks

```python
from crewai import Agent, Task, Crew
from adri import adri_protected

@adri_protected
def crewai_data_analysis(market_data):
    """Analyze market data with CrewAI crew"""

    # Define analyst agent
    analyst = Agent(
        role='Data Analyst',
        goal='Analyze market trends and provide insights',
        backstory='Expert in market data analysis',
        verbose=True
    )

    # Create analysis task with validated data
    analysis_task = Task(
        description=f'Analyze this market data: {market_data}',
        agent=analyst
    )

    # Create crew and execute
    crew = Crew(
        agents=[analyst],
        tasks=[analysis_task],
        verbose=2
    )

    result = crew.kickoff()
    return {"crew_analysis": result, "data_validated": True}

# Usage
market_data = [
    {"stock": "AAPL", "price": 150.0, "volume": 1000000},
    {"stock": "GOOGL", "price": 2500.0, "volume": 500000}
]

analysis = crewai_data_analysis(market_data)
```

## AutoGen {#autogen}

### Protect AutoGen Conversations

```python
import autogen
from adri import adri_protected

@adri_protected
def autogen_multi_agent_analysis(financial_data):
    """Multi-agent financial analysis with AutoGen"""

    config_list = [{"model": "gpt-4", "api_key": "your-api-key"}]

    # Create assistant agent
    assistant = autogen.AssistantAgent(
        name="financial_analyst",
        llm_config={"config_list": config_list},
        system_message="You are a financial analyst. Analyze the provided data."
    )

    # Create user proxy
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1
    )

    # ADRI validates financial_data before starting conversation
    message = f"Please analyze this financial data: {financial_data}"

    user_proxy.initiate_chat(assistant, message=message)

    return {"analysis_complete": True, "data_quality": "validated"}

# Usage
financial_data = [
    {"company": "AAPL", "revenue": 365.8, "profit": 94.7},
    {"company": "MSFT", "revenue": 198.3, "profit": 61.3}
]

result = autogen_multi_agent_analysis(financial_data)
```

## LlamaIndex {#llamaindex}

### Protect LlamaIndex Query Engines

```python
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.query_engine import PandasQueryEngine
import pandas as pd
from adri import adri_protected

@adri_protected
def llamaindex_query_analysis(dataset, query):
    """Query analysis using LlamaIndex"""

    # Convert validated data to DataFrame
    df = pd.DataFrame(dataset)

    # Create query engine with validated data
    query_engine = PandasQueryEngine(df=df, verbose=True)

    # Execute query
    response = query_engine.query(query)

    return {
        "query": query,
        "response": str(response),
        "data_rows": len(df)
    }

# Usage
sales_data = [
    {"product": "Laptop", "sales": 1000, "region": "North"},
    {"product": "Mouse", "sales": 500, "region": "South"}
]

result = llamaindex_query_analysis(
    dataset=sales_data,
    query="What are the total sales by region?"
)
```

### Protect Document Processing

```python
from llama_index.core import VectorStoreIndex, Document
from adri import adri_protected

@adri_protected
def llamaindex_document_processing(document_data):
    """Process documents with LlamaIndex"""

    # Create documents from validated data
    documents = [
        Document(text=doc["content"], metadata=doc.get("metadata", {}))
        for doc in document_data
    ]

    # Create index
    index = VectorStoreIndex.from_documents(documents)

    # Create query engine
    query_engine = index.as_query_engine()

    return {
        "index_created": True,
        "document_count": len(documents),
        "query_engine": query_engine
    }
```

## Haystack {#haystack}

### Protect Haystack Pipelines

```python
from haystack import Pipeline
from haystack.components.writers import DocumentWriter
from haystack.dataclasses import Document
from adri import adri_protected

@adri_protected
def haystack_document_processing(raw_documents):
    """Process documents through Haystack pipeline"""

    # Convert validated data to Haystack documents
    documents = [
        Document(content=doc["text"], meta=doc.get("metadata", {}))
        for doc in raw_documents
    ]

    # Create pipeline
    pipeline = Pipeline()
    pipeline.add_component("writer", DocumentWriter())

    # Process documents
    result = pipeline.run({"writer": {"documents": documents}})

    return {
        "documents_processed": len(documents),
        "pipeline_result": result
    }

# Usage
document_data = [
    {"text": "Financial report Q1 2024", "metadata": {"type": "report"}},
    {"text": "Market analysis summary", "metadata": {"type": "analysis"}}
]

result = haystack_document_processing(document_data)
```

## LangGraph {#langgraph}

### Protect LangGraph Nodes

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from adri import adri_protected

class AnalysisState:
    data: list
    analysis: str = ""
    completed: bool = False

@adri_protected
def langgraph_analysis_node(state: AnalysisState):
    """Analysis node with ADRI protection"""

    # Data is validated by ADRI before processing
    data = state["data"]

    # Perform analysis
    analysis = f"Analyzed {len(data)} records"

    return {
        "data": data,
        "analysis": analysis,
        "completed": True
    }

def create_analysis_graph():
    """Create LangGraph with protected nodes"""

    workflow = StateGraph(AnalysisState)

    # Add protected analysis node
    workflow.add_node("analyze", langgraph_analysis_node)
    workflow.add_edge("analyze", END)
    workflow.set_entry_point("analyze")

    # Compile with checkpointer
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    return app

# Usage
app = create_analysis_graph()
config = {"configurable": {"thread_id": "analysis-1"}}

result = app.invoke({
    "data": [{"value": 100}, {"value": 200}]
}, config)
```

## Semantic Kernel {#semantic-kernel}

### Protect Semantic Kernel Functions

```python
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from adri import adri_protected

@adri_protected
def semantic_kernel_analysis(business_data):
    """Analyze business data with Semantic Kernel"""

    # Initialize kernel
    kernel = sk.Kernel()

    # Add AI service
    kernel.add_service(OpenAIChatCompletion(
        service_id="chat-gpt",
        ai_model_id="gpt-3.5-turbo"
    ))

    # Create function from prompt
    analyze_function = kernel.create_function_from_prompt(
        function_name="analyze_data",
        plugin_name="business_analytics",
        prompt="Analyze this business data and provide insights: {{$data}}"
    )

    # Execute with validated data
    result = kernel.invoke(
        analyze_function,
        data=str(business_data)
    )

    return {
        "analysis": str(result),
        "data_validated": True
    }

# Usage
business_data = [
    {"metric": "revenue", "value": 1000000, "period": "Q1"},
    {"metric": "costs", "value": 750000, "period": "Q1"}
]

analysis = semantic_kernel_analysis(business_data)
```

## Configuration for All Frameworks

### Universal Config (`adri-config.yaml`)

```yaml
validation:
  completeness_threshold: 0.9
  validity_checks: true
  consistency_checks: true
  plausibility_checks: true

reporting:
  generate_html_report: true
  log_level: "INFO"

audit:
  enable_logging: true
  log_file: "logs/adri_audit.jsonl"

# Framework-specific settings
frameworks:
  langchain:
    validate_chain_inputs: true
  crewai:
    validate_task_data: true
  autogen:
    validate_conversation_data: true
```

## Common Patterns

### Error Handling

```python
from adri import adri_protected, ADRIValidationError

@adri_protected(fail_fast=True)
def protected_function(data):
    try:
        # Your agent logic
        return process_data(data)
    except ADRIValidationError as e:
        # Handle validation failures
        return {"error": f"Data validation failed: {e}"}
```

### Custom Validation

```python
@adri_protected(
    completeness_threshold=0.8,
    custom_validators=[
        lambda x: len(x) > 0,  # Must have data
        lambda x: all('id' in item for item in x)  # All items need ID
    ]
)
def custom_protected_function(data):
    return {"processed": len(data)}
```

---

## Need More Help?

- [Quick Start Guide](quick-start) - Get up and running
- [API Reference](https://github.com/adri-standard/adri/blob/main/docs/API_REFERENCE.md) - Detailed documentation
- [GitHub Issues](https://github.com/adri-standard/adri/issues) - Report problems or request features
- [GitHub Discussions](https://github.com/adri-standard/adri/discussions) - Ask questions and share ideas

**Ready to protect your agents?** Pick your framework above and start with the copy-paste examples!
