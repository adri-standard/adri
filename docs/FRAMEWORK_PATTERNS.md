# Framework Integration Patterns

How to integrate ADRI with popular AI agent frameworks.

## Table of Contents

1. [Overview](#overview)
2. [LangChain](#langchain)
3. [LangGraph](#langgraph)
4. [CrewAI](#crewai)
5. [AutoGen](#autogen)
6. [LlamaIndex](#llamaindex)
7. [Haystack](#haystack)
8. [Semantic Kernel](#semantic-kernel)
9. [Generic Python](#generic-python)
10. [Best Practices](#best-practices)

## Overview

ADRI works the same way across all frameworks:

```python
from adri import adri_protected

@adri_protected(contract="your_data", data_param="your_data")
def your_function(your_data):
    # Your agent logic
    return results
```

The decorator protects any Python function, regardless of the framework. This guide shows framework-specific patterns and best practices.

## LangChain

### Basic Chain Protection

```python
from adri import adri_protected
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

@adri_protected(contract="customer_data", data_param="customer_data")
def process_customers_chain(customer_data):
    """Process customer data through LangChain."""

    llm = ChatOpenAI(temperature=0)

    prompt = PromptTemplate(
        input_variables=["customers"],
        template="Analyze these customers: {customers}"
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(customers=customer_data)
```

### Tool Protection

```python
from langchain.tools import tool

@tool
@adri_protected(contract="search_results", data_param="search_results")
def analyze_search_results(search_results):
    """Analyze search results with data quality protection."""
    return perform_analysis(search_results)
```

### Agent Pipeline

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent

@adri_protected(contract="context_data", data_param="context_data")
def create_protected_agent(context_data, tools):
    """Create agent with protected context."""

    llm = ChatOpenAI(temperature=0)
    agent = create_openai_functions_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True
    )
```

### Multi-Step Chain

```python
@adri_protected(contract="raw_data", data_param="raw_data")
def step_1_extract(raw_data):
    """Step 1: Extract with validation."""
    return extract_features(raw_data)

@adri_protected(contract="features", data_param="features")
def step_2_transform(features):
    """Step 2: Transform with validation."""
    return transform_features(features)

@adri_protected(contract="transformed", data_param="transformed")
def step_3_analyze(transformed):
    """Step 3: Analyze with validation."""
    return run_analysis(transformed)

# Chain them together
def protected_pipeline(raw_data):
    features = step_1_extract(raw_data)
    transformed = step_2_transform(features)
    return step_3_analyze(transformed)
```

## LangGraph

### Graph Node Protection

```python
from adri import adri_protected
from langgraph.graph import Graph

@adri_protected(contract="state", data_param="state")
def research_node(state):
    """Research node with data validation."""
    return perform_research(state)

@adri_protected(contract="state", data_param="state")
def analysis_node(state):
    """Analysis node with data validation."""
    return analyze_results(state)

# Build graph
workflow = Graph()
workflow.add_node("research", research_node)
workflow.add_node("analysis", analysis_node)
workflow.add_edge("research", "analysis")
```

### State Protection

```python
from typing import TypedDict

class AgentState(TypedDict):
    messages: list
    data: dict

@adri_protected(contract="data", data_param="data")
def process_state_data(data):
    """Process state data with validation."""
    return enhanced_data(data)

def workflow_function(state: AgentState):
    # Protect the data portion
    validated_data = process_state_data(state["data"])
    state["data"] = validated_data
    return state
```

## CrewAI

### Task Function Protection

```python
from adri import adri_protected
from crewai import Task, Crew, Agent

@adri_protected(contract="market_data", data_param="market_data")
def analyze_market(market_data):
    """Analyze market data with quality checks."""
    return run_market_analysis(market_data)

# Create task that uses protected function
research_task = Task(
    description="Analyze market trends",
    agent=analyst,
    function=analyze_market
)
```

### Multi-Agent Crew

```python
@adri_protected(contract="customer_data", data_param="customer_feedback")
def analyze_feedback(customer_feedback):
    """Analyze customer feedback."""
    return sentiment_analysis(customer_feedback)

@adri_protected(contract="sales_data", data_param="sales_data")
def analyze_sales(sales_data):
    """Analyze sales performance."""
    return sales_metrics(sales_data)

# Create crew with protected functions
crew = Crew(
    agents=[feedback_agent, sales_agent],
    tasks=[
        Task(
            description="Analyze feedback",
            agent=feedback_agent,
            function=analyze_feedback
        ),
        Task(
            description="Analyze sales",
            agent=sales_agent,
            function=analyze_sales
        )
    ]
)
```

### Context Protection

```python
@adri_protected(contract="context", data_param="context")
def process_crew_context(context):
    """Process crew context with validation."""
    validated_context = validate_and_enrich(context)
    return validated_context

# Use in crew kickoff
def run_crew_with_protection(raw_context):
    validated_context = process_crew_context(raw_context)
    return crew.kickoff(context=validated_context)
```

## AutoGen

### Conversation Protection

```python
from adri import adri_protected
import autogen

@adri_protected(contract="conversation_history", data_param="conversation_history")
def analyze_conversation(conversation_history):
    """Analyze conversation with data quality checks."""
    return extract_insights(conversation_history)

# Use with AutoGen agents
assistant = autogen.AssistantAgent(
    name="assistant",
    llm_config={"model": "gpt-4"}
)

user_proxy = autogen.UserProxyAgent(
    name="user",
    function_map={"analyze_conversation": analyze_conversation}
)
```

### Multi-Agent Discussion

```python
@adri_protected(contract="research_data", data_param="research_data")
def research_function(research_data):
    """Research with data validation."""
    return conduct_research(research_data)

@adri_protected(contract="analysis_data", data_param="analysis_data")
def analysis_function(analysis_data):
    """Analysis with data validation."""
    return perform_analysis(analysis_data)

# Create agents with protected functions
researcher = autogen.AssistantAgent(
    name="researcher",
    function_map={"research": research_function}
)

analyst = autogen.AssistantAgent(
    name="analyst",
    function_map={"analyze": analysis_function}
)
```

## LlamaIndex

### Query Engine Protection

```python
from adri import adri_protected
from llama_index import VectorStoreIndex, Document

@adri_protected(contract="documents", data_param="documents")
def index_documents(documents):
    """Index documents with data validation."""

    # Validate document structure
    validated_docs = [Document(text=doc) for doc in documents]

    # Create index
    index = VectorStoreIndex.from_documents(validated_docs)
    return index

@adri_protected(contract="query_results", data_param="query_results")
def process_query_results(query_results):
    """Process query results with validation."""
    return format_results(query_results)
```

### RAG Pipeline

```python
@adri_protected(contract="source_docs", data_param="source_docs")
def prepare_knowledge_base(source_docs):
    """Prepare knowledge base with data validation."""
    return create_index(source_docs)

@adri_protected(contract="query_response", data_param="query_response")
def validate_rag_output(query_response):
    """Validate RAG output quality."""
    return verified_response(query_response)

# Complete RAG pipeline
def protected_rag_pipeline(docs, query):
    index = prepare_knowledge_base(docs)
    response = index.query(query)
    return validate_rag_output(response)
```

## Haystack

### Pipeline Protection

```python
from adri import adri_protected
from haystack import Pipeline
from haystack.components.retrievers import InMemoryBM25Retriever

@adri_protected(contract="documents", data_param="documents")
def prepare_documents(documents):
    """Prepare documents with data validation."""
    return validated_documents(documents)

@adri_protected(contract="search_results", data_param="search_results")
def process_search_results(search_results):
    """Process search results with validation."""
    return formatted_results(search_results)

# Build pipeline
pipeline = Pipeline()
pipeline.add_component("retriever", InMemoryBM25Retriever())
```

### Document Store Protection

```python
from haystack.document_stores import InMemoryDocumentStore

@adri_protected(contract="raw_documents", data_param="raw_documents")
def load_document_store(raw_documents):
    """Load documents into store with validation."""

    doc_store = InMemoryDocumentStore()
    doc_store.write_documents(raw_documents)
    return doc_store
```

## Semantic Kernel

### Kernel Function Protection

```python
from adri import adri_protected
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

class ProtectedPlugin:
    @kernel_function(name="analyze")
    @adri_protected(contract="data", data_param="input_data")
    def analyze_data(self, input_data: str):
        """Analyze data with validation."""
        return perform_analysis(input_data)

    @kernel_function(name="transform")
    @adri_protected(contract="raw_data", data_param="raw_data")
    def transform_data(self, raw_data: str):
        """Transform data with validation."""
        return transform(raw_data)

# Use with kernel
kernel = Kernel()
kernel.add_plugin(ProtectedPlugin(), plugin_name="data_ops")
```

### Planner Protection

```python
@adri_protected(contract="plan_input", data_param="plan_input")
def validate_plan_input(plan_input):
    """Validate planner input data."""
    return verified_input(plan_input)

@adri_protected(contract="plan_result", data_param="plan_result")
def validate_plan_result(plan_result):
    """Validate planner output data."""
    return verified_result(plan_result)

# Use in planning workflow
def protected_planning(raw_input):
    validated_input = validate_plan_input(raw_input)
    plan = planner.create_plan(validated_input)
    result = plan.invoke()
    return validate_plan_result(result)
```

## Generic Python

### API Response Protection

```python
import requests
from adri import adri_protected

@adri_protected(contract="api_response", data_param="api_response")
def process_api_data(api_response):
    """Process API response with data validation."""
    return transform_api_data(api_response)

# Use with API calls
def fetch_and_process():
    response = requests.get("https://api.example.com/data")
    data = response.json()
    return process_api_data(data)
```

### Data Pipeline

```python
@adri_protected(contract="raw_data", data_param="raw_data")
def stage_1_clean(raw_data):
    """Stage 1: Clean data."""
    return cleaned_data(raw_data)

@adri_protected(contract="clean_data", data_param="clean_data")
def stage_2_enrich(clean_data):
    """Stage 2: Enrich data."""
    return enriched_data(clean_data)

@adri_protected(contract="enriched_data", data_param="enriched_data")
def stage_3_aggregate(enriched_data):
    """Stage 3: Aggregate data."""
    return aggregated_results(enriched_data)

# Complete pipeline
def data_pipeline(raw_data):
    clean = stage_1_clean(raw_data)
    enriched = stage_2_enrich(clean)
    return stage_3_aggregate(enriched)
```

### Multi-Source Integration

```python
@adri_protected(contract="source_a", data_param="source_a")
def process_source_a(source_a):
    """Process data from source A."""
    return transformed_a(source_a)

@adri_protected(contract="source_b", data_param="source_b")
def process_source_b(source_b):
    """Process data from source B."""
    return transformed_b(source_b)

@adri_protected(contract="combined_data", data_param="combined_data")
def merge_sources(combined_data):
    """Merge validated data from multiple sources."""
    return final_dataset(combined_data)

# Integration workflow
def integrate_sources():
    data_a = fetch_source_a()
    data_b = fetch_source_b()

    validated_a = process_source_a(data_a)
    validated_b = process_source_b(data_b)

    combined = {"source_a": validated_a, "source_b": validated_b}
    return merge_sources(combined)
```

## Best Practices

### 1. Validate at Boundaries

Protect data at system boundaries:

```python
# ✅ Good: Validate external data
@adri_protected(contract="api_data", data_param="api_data")
def process_external_data(api_data):
    return analyze(api_data)

# ❌ Skip: Internal transformations
def internal_calculation(x, y):
    return x + y  # No need for protection
```

### 2. Choose Appropriate Guard Modes

```python
# Production: Use block mode (default)
@adri_protected(contract="data", data_param="data", on_failure="raise")
def production_function(data):
    return results

# Development: Use warn mode
@adri_protected(contract="data", data_param="data", on_failure="warn")
def dev_function(data):
    return results
```

### 3. Granular Protection

Protect specific data parameters, not everything:

```python
# ✅ Good: Protect data parameter only
@adri_protected(contract="customer_data", data_param="customer_data")
def process(customer_data, config, api_key):
    return analyze(customer_data)

# ❌ Over-protection: Don't protect config/credentials
```

### 4. Let Standards Evolve

Start with auto-generation, customize as needed:

```python
# First run: Auto-generates standard
@adri_protected(contract="data", data_param="data")
def my_function(data):
    return results

# Then customize ADRI/dev/contracts/my_function_data_standard.yaml
# Add domain-specific rules
# Tighten ranges
# Add cross-field validation
```

### 5. Use Descriptive Names

Name your protected functions clearly:

```python
# ✅ Good: Clear names
@adri_protected(contract="customer_data", data_param="customer_records")
def validate_customer_records(customer_records):
    return processed

# ❌ Unclear: Generic names
@adri_protected(contract="data", data_param="data")
def process(data):
    return result
```

### 6. Document Your Standards

Add descriptions to generated standards:

```yaml
standard:
  name: "customer_data"
  version: "1.0.0"
  description: "Customer records from CRM system. Must include valid contact info and purchase history."

  fields:
    # ... field definitions
```

### 7. Version Your Standards

Update standard versions when changing requirements:

```yaml
standard:
  name: "customer_data"
  version: "2.0.0"  # Bump version on breaking changes
  changelog:
    - "2.0.0: Added email validation"
    - "1.1.0: Added purchase_value field"
    - "1.0.0: Initial version"
```

### 8. Test with Bad Data

Always test your protected functions with bad data:

```python
def test_protection():
    bad_data = {"invalid": "structure"}

    try:
        result = protected_function(bad_data)
        assert False, "Should have raised exception"
    except Exception as e:
        assert "quality" in str(e).lower()
```

## Common Patterns

### Pattern 1: Pre-Processing Protection

```python
@adri_protected(contract="raw_input", data_param="raw_input")
def preprocess(raw_input):
    """Validate input before expensive operations."""
    return cleaned_input
```

### Pattern 2: Post-Processing Verification

```python
@adri_protected(contract="llm_output", data_param="llm_output")
def verify_output(llm_output):
    """Validate LLM output structure."""
    return verified_output
```

### Pattern 3: Pipeline Checkpoints

```python
@adri_protected(contract="data", data_param="data")
def checkpoint_1(data):
    return processed_1

@adri_protected(contract="data", data_param="data")
def checkpoint_2(data):
    return processed_2
```

## Next Steps

- [Getting Started](GETTING_STARTED.md) - Basic tutorial
- [Examples](../examples/README.md) - Framework-specific examples
- [CLI Reference](CLI_REFERENCE.md) - Command-line tools
- [API Reference](API_REFERENCE.md) - Complete API

---

**Protect your agents across any framework with consistent patterns.**
