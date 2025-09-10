# ADRI Quick Start - Protect Your AI Agents in 30 Seconds

🛡️ **One decorator. Any framework. Reliable agents.**

Stop your AI agents from breaking on bad data with a single line of code.

## 30-Second Protection

```python
# 1. Install ADRI
pip install adri

# 2. Add the decorator
from adri.decorators.guard import adri_protected

@adri_protected
def your_agent_function(data):
    return your_existing_code(data)  # ✅ Now protected!

# 3. That's it! Your agent is protected.
```

## Framework Examples

ADRI works with **all major AI frameworks**. Copy these examples and run them immediately:

### 🔗 LangChain
```python
from adri.decorators.guard import adri_protected

@adri_protected
def langchain_customer_service(customer_data):
    chain = prompt | model | parser
    return chain.invoke(customer_data)
```
**Try it:** `python langchain_example.py`

### 👥 CrewAI
```python
from adri.decorators.guard import adri_protected

@adri_protected
def crewai_market_analysis(market_data):
    crew = Crew(agents=[analyst, researcher])
    return crew.kickoff(inputs=market_data)
```
**Try it:** `python crewai_example.py`

### 💬 AutoGen
```python
from adri.decorators.guard import adri_protected

@adri_protected
def autogen_research_team(research_data):
    assistant.initiate_chat(user_proxy, message=research_data)
    return conversation_result
```
**Try it:** `python autogen_example.py`

### 🔍 LlamaIndex
```python
from adri.decorators.guard import adri_protected

@adri_protected
def llamaindex_rag_query(query_data):
    engine = index.as_query_engine()
    return engine.query(query_data)
```
**Try it:** `python llamaindex_example.py`

### 🔎 Haystack
```python
from adri.decorators.guard import adri_protected

@adri_protected
def haystack_search_pipeline(search_data):
    results = pipeline.run(search_data)
    return results
```
**Try it:** `python haystack_example.py`

### 🔀 LangGraph
```python
from adri.decorators.guard import adri_protected

@adri_protected
def langgraph_workflow(workflow_data):
    result = graph.invoke(workflow_data)
    return result
```
**Try it:** `python langgraph_example.py`

### 🤖 Semantic Kernel
```python
from adri.decorators.guard import adri_protected

@adri_protected
def semantic_kernel_function(function_data):
    result = kernel.invoke(function_data)
    return result
```
**Try it:** `python semantic_kernel_example.py`

### 🐍 Any Python Function
```python
from adri.decorators.guard import adri_protected

@adri_protected
def any_python_function(data):
    return process_data(data)  # Your existing code!
```
**Try it:** `python basic_example.py`

## What You'll See

### ✅ Good Data (Protection Allows)
```
🛡️ ADRI Protection: ALLOWED ✅
📊 Quality Score: 94.2/100 (Required: 80.0/100)
📋 Standard: customer_data_standard v1.0.0 (NEW)
```

### ❌ Bad Data (Protection Blocks)
```
🛡️ ADRI Protection: BLOCKED ❌
❌ Data quality too low for reliable agent execution
📊 Quality Assessment: 67.3/100 (Required: 80.0/100)

🔧 Fix This Now:
   • customer_id: Should be integer, got string
   • email: Invalid email format
   • age: Value -5 is outside valid range (18-120)
```

## How It Works

1. **Automatic Standards**: ADRI analyzes your function name and generates intelligent data quality standards
2. **Smart Validation**: Checks validity, completeness, consistency, freshness, and plausibility
3. **Instant Feedback**: Shows exactly what's wrong with bad data
4. **Zero Setup**: Works immediately with sensible defaults

## Advanced Usage

### Custom Protection Levels
```python
@adri_protected(min_score=90)  # Strict protection
def financial_analysis(data):
    return high_stakes_analysis(data)

@adri_protected(min_score=60)  # Permissive for development
def experimental_feature(data):
    return prototype_analysis(data)
```

### Custom Standards
```python
@adri_protected(standard_path="my_standard.yaml")
def specialized_agent(data):
    return specialized_analysis(data)
```

### Development Mode
```python
@adri_protected(on_failure="warn")  # Don't break, just warn
def development_pipeline(data):
    return dev_analysis(data)
```

## Real-World Examples

### Customer Service Agent
```python
@adri_protected
def process_customer_request(customer_data):
    # ADRI ensures customer_data has valid email, ID, issue type, etc.
    response = generate_support_response(customer_data)
    return response
```

### Financial Risk Analysis
```python
@adri_protected(min_score=95)  # Extra strict for financial data
def analyze_loan_application(application_data):
    # ADRI validates income, credit score, employment history, etc.
    risk_assessment = calculate_risk(application_data)
    return risk_assessment
```

### Content Generation
```python
@adri_protected
def generate_marketing_content(content_request):
    # ADRI ensures valid target audience, keywords, tone, etc.
    content = ai_content_generator(content_request)
    return content
```

## Installation Options

### Basic Installation
```bash
pip install adri
```

### With Framework Support
```bash
# LangChain
pip install adri langchain

# CrewAI
pip install adri crewai

# AutoGen
pip install adri pyautogen

# LlamaIndex
pip install adri llama-index

# Haystack
pip install adri haystack-ai

# LangGraph
pip install adri langgraph

# Semantic Kernel
pip install adri semantic-kernel
```

### From Source
```bash
git clone https://github.com/adri-standard/adri
cd adri && pip install -e .
```

## Framework Compatibility

| Framework | Status | Example File | Install Command |
|-----------|--------|--------------|-----------------|
| **LangChain** | ✅ Fully Supported | `langchain_example.py` | `pip install adri langchain` |
| **CrewAI** | ✅ Fully Supported | `crewai_example.py` | `pip install adri crewai` |
| **AutoGen** | ✅ Fully Supported | `autogen_example.py` | `pip install adri pyautogen` |
| **LlamaIndex** | ✅ Fully Supported | `llamaindex_example.py` | `pip install adri llama-index` |
| **Haystack** | ✅ Fully Supported | `haystack_example.py` | `pip install adri haystack-ai` |
| **LangGraph** | ✅ Fully Supported | `langgraph_example.py` | `pip install adri langgraph` |
| **Semantic Kernel** | ✅ Fully Supported | `semantic_kernel_example.py` | `pip install adri semantic-kernel` |
| **Any Python** | ✅ Always Supported | `basic_example.py` | `pip install adri` |

## Common Patterns

### Multi-Agent Systems
```python
@adri_protected
def coordinate_agent_team(team_data):
    # Protects multi-agent coordination data
    results = []
    for agent in team_data["agents"]:
        result = agent.execute(team_data["task"])
        results.append(result)
    return results
```

### RAG Applications
```python
@adri_protected
def rag_query_pipeline(query_data):
    # Protects RAG query parameters and context
    documents = retriever.retrieve(query_data["query"])
    answer = generator.generate(query_data["query"], documents)
    return answer
```

### Workflow Orchestration
```python
@adri_protected
def execute_ai_workflow(workflow_data):
    # Protects workflow configuration and inputs
    for step in workflow_data["steps"]:
        result = execute_step(step, workflow_data["context"])
    return result
```

## Troubleshooting

### Common Issues

**Q: "My function still gets bad data"**
A: Check your `min_score` setting. Lower it for development, raise it for production.

**Q: "ADRI is too strict"**
A: Use `@adri_protected(min_score=60)` or `@adri_protected(on_failure="warn")`

**Q: "How do I see what standards ADRI is using?"**
A: ADRI automatically generates standards based on your function name and shows them in the output.

**Q: "Can I use my own data quality rules?"**
A: Yes! Use `@adri_protected(standard_path="your_rules.yaml")`

### Getting Help

- **Run Examples**: All examples work without external dependencies
- **Check Output**: ADRI tells you exactly what's wrong with your data
- **GitHub Issues**: [Report bugs and get help](https://github.com/adri-standard/adri/issues)
- **Documentation**: Full API reference in README.md

## What's Next?

1. **Copy and run** any example above
2. **Add `@adri_protected`** to your agent functions
3. **Test with bad data** to see protection in action
4. **Customize protection levels** for your use case
5. **Share with your team** - one decorator protects everyone

---

## 🎯 Remember: One Line of Code = Bulletproof Agents

```python
@adri_protected  # ← This line prevents production disasters
def your_agent_function(data):
    return your_existing_code(data)
```

**That's it.** Your AI agents are now protected from bad data.

**Questions?** Check the examples, read the output, or [open an issue](https://github.com/adri-standard/adri/issues).
