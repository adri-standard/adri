# ADRI Examples

Real-world examples of protecting AI agents with ADRI's `@adri_protected` decorator.

## Quick Reference

All examples follow the same pattern:

```python
from adri import adri_protected

@adri_protected(contract="your_data", data_param="your_data")
def your_function(your_data):
    # Your logic here
    return results
```

## Available Examples

### By Framework

| Framework | File | Description |
|-----------|------|-------------|
| **LangChain** | `langchain_basic.py` | Protect LangChain chains and tools |
| **LangGraph** | `langgraph_basic.py` | Protect LangGraph workflows |
| **CrewAI** | `crewai_basic.py` | Protect multi-agent crews |
| **AutoGen** | `autogen_basic.py` | Protect agent conversations |
| **LlamaIndex** | `llamaindex_basic.py` | Protect RAG pipelines |
| **Haystack** | `haystack_basic.py` | Protect document search |
| **Semantic Kernel** | `semantic_kernel_basic.py` | Protect kernel functions |
| **Generic Python** | `generic_basic.py` | Protect any Python function |

### By Pattern

| Pattern | File | Use Case |
|---------|------|----------|
| **Full Decorator Demo** | `adri_protected_decorator_example.py` | Learn all decorator features |
| **API Data** | `generic_basic.py` | Validate API responses |
| **Multi-Agent** | `crewai_basic.py`, `autogen_basic.py` | Coordinate agent teams |
| **RAG/Search** | `llamaindex_basic.py`, `haystack_basic.py` | Protect retrieval systems |
| **Workflows** | `langgraph_basic.py`, `langchain_basic.py` | Protect complex pipelines |

## Running Examples

### Install ADRI

```bash
pip install adri
```

### Run an Example

```bash
python langchain_basic.py
```

### Install Framework Dependencies (Optional)

Examples work without framework installs (using mocks), but you can install real frameworks:

```bash
pip install langchain crewai autogen llama-index haystack-ai semantic-kernel langgraph
```

## Common Patterns

### Pattern 1: Basic Protection

Simplest usage - auto-generates standard from data:

```python
from adri import adri_protected

@adri_protected(contract="data", data_param="data")
def process_data(data):
    return results
```

### Pattern 2: Guard Mode Selection

Choose block (strict) or warn (permissive):

```python
# Block mode - raises exception on bad data (default)
@adri_protected(contract="data", data_param="data", on_failure="raise")
def strict_function(data):
    return results

# Warn mode - logs warning but continues
@adri_protected(contract="data", data_param="data", on_failure="warn")
def lenient_function(data):
    return results
```

### Pattern 3: Custom Standard

Use a specific pre-defined standard:

```python
@adri_protected(data_param="data", standard="customer_data")
def process_customers(data):
    return results
```

### Pattern 4: Multi-Parameter

Protect multiple data parameters:

```python
@adri_protected(contract="customer_data", data_param="customers")
def process_with_context(customers, config, api_key):
    # Only 'customers' is validated
    return results
```

### Pattern 5: Framework Integration

Works the same across all frameworks:

```python
# LangChain
@adri_protected(contract="data", data_param="input_data")
def langchain_tool(input_data):
    return chain.invoke(input_data)

# CrewAI
@adri_protected(contract="context", data_param="context")
def crewai_task(context):
    return crew.kickoff(context)

# AutoGen
@adri_protected(contract="messages", data_param="messages")
def autogen_function(messages):
    return agent.generate_reply(messages)
```

## What You'll Learn

### From `generic_basic.py`
- Basic decorator usage
- Auto-generation workflow
- Guard modes (block vs warn)
- Working with DataFrames

### From `adri_protected_decorator_example.py`
- All decorator parameters
- Custom requirements
- Verbose logging
- Development patterns

### From Framework Examples
- Integration patterns for your framework
- Real-world use cases
- Best practices per framework

## Expected Output

### ✅ Good Data (Passes Validation)

```
🛡️ ADRI Protection: ALLOWED ✅
📊 Quality Score: 94.2/100
📋 Standard: your_function_data_standard (auto-generated)
```

### ❌ Bad Data (Fails Validation)

```
🛡️ ADRI Protection: BLOCKED ❌
📊 Quality Score: 67.3/100 (Required: 80.0/100)

Quality Issues:
- Completeness: Missing required field 'email'
- Validity: Field 'age' has invalid type (expected: int, got: str)
- Accuracy: Field 'age' value -5 outside valid range [0, 120]
```

## Troubleshooting

### "Standard not found"
Run your function once with good data. ADRI will auto-generate the standard.

### "Import errors"
Examples use mocks by default. Install frameworks if you want real integrations:
```bash
pip install langchain  # or crewai, autogen, etc.
```

### "Quality score too low"
Check `ADRI/dev/logs/` for detailed assessment. Fix data issues or adjust `mode` to "warn".

## Next Steps

1. **Run an example**: Start with `generic_basic.py`
2. **Check generated standards**: Look in `ADRI/dev/contracts/`
3. **Read the logs**: Check `ADRI/dev/logs/` for insights
4. **Try with your data**: Replace sample data with your own
5. **Add to your agents**: Copy the decorator pattern

## Learn More

- [Quickstart Guide](../QUICKSTART.md) - 2-minute integration
- [Getting Started](../docs/GETTING_STARTED.md) - Detailed tutorial
- [Framework Patterns](../docs/FRAMEWORK_PATTERNS.md) - Framework-specific guides
- [API Reference](../docs/API_REFERENCE.md) - All decorator options

---

**One decorator. Any framework. Reliable agents.**
