# ADRI Framework Examples

This directory contains working examples demonstrating how to use ADRI to protect your AI agents from bad data.

## Available Examples

### 1. Framework-Specific Examples

#### LangChain
**File**: `langchain_basic.py`
- Basic LangChain agent protection
- High-priority customer service with strict requirements
- Mock LangChain components for testing without dependencies

#### CrewAI
**File**: `crewai_basic.py`
- Market analysis crew protection
- Customer support crew workflows
- Multi-agent conversation protection

#### AutoGen
**File**: `autogen_basic.py`
- Multi-agent conversation protection
- Research team workflows
- Assistant and UserProxy agent examples

#### LlamaIndex
**File**: `llamaindex_basic.py`
- RAG query engine protection
- Enterprise knowledge base with strict requirements
- Document indexing and retrieval

#### Haystack
**File**: `haystack_basic.py`
- Document search pipeline protection
- BM25 retriever examples
- In-memory document store usage

#### Semantic Kernel
**File**: `semantic_kernel_basic.py`
- Kernel function protection
- Semantic function creation
- AI service integration

#### LangGraph
**File**: `langgraph_basic.py`
- Graph workflow protection
- Multi-node workflow examples
- State management in graphs

#### Generic Python
**File**: `generic_basic.py`
- Basic data processor protection
- Sales data analyzer
- User profile analyzer with strict requirements

### 2. Comprehensive Decorator Examples
**File**: `adri_protected_decorator_example.py`

Shows all decorator features and options:
- Basic protection with auto-generated standards
- Custom standards and explicit requirements
- Development-friendly configurations
- Convenience decorators (strict, permissive, financial)

## Running the Examples

### Prerequisites
```bash
# Install ADRI
pip install adri

# Optional: Install framework dependencies
pip install langchain      # For LangChain examples
pip install crewai         # For CrewAI examples
pip install pyautogen      # For AutoGen examples
pip install llama-index    # For LlamaIndex examples
pip install haystack-ai    # For Haystack examples
pip install semantic-kernel # For Semantic Kernel examples
pip install langgraph      # For LangGraph examples
```

### Run Individual Examples
```bash
# Framework-specific examples
python langchain_basic.py
python crewai_basic.py
python autogen_basic.py
python llamaindex_basic.py
python haystack_basic.py
python semantic_kernel_basic.py
python langgraph_basic.py
python generic_basic.py

# Comprehensive decorator examples
python adri_protected_decorator_example.py
```

### Run All Examples
```bash
# Run all framework examples
for example in langchain_basic.py crewai_basic.py autogen_basic.py llamaindex_basic.py haystack_basic.py semantic_kernel_basic.py langgraph_basic.py generic_basic.py; do
    echo "Running $example..."
    python $example
    echo "---"
done
```

## Example Patterns

### Basic Protection Pattern
```python
from adri.decorators.guard import adri_protected

@adri_protected(data_param="your_data")
def your_agent_function(your_data):
    # Your existing agent code - unchanged!
    return process_data(your_data)
```

### Custom Requirements Pattern
```python
@adri_protected(
    data_param="financial_data",
    min_score=90,
    dimensions={"validity": 19, "completeness": 18},
    verbose=True
)
def financial_risk_agent(financial_data):
    return assess_risk(financial_data)
```

### Development-Friendly Pattern
```python
@adri_protected(
    data_param="test_data",
    min_score=70,
    on_failure="warn",  # Don't stop execution, just warn
    verbose=True
)
def development_pipeline(test_data):
    return process_test_data(test_data)
```

## What Each Example Demonstrates

| Framework | File | Shows | Use Case |
|-----------|------|-------|----------|
| **LangChain** | `langchain_basic.py` | Chain protection, prompt templates | Customer service agents |
| **CrewAI** | `crewai_basic.py` | Multi-agent crews, task coordination | Market analysis, support teams |
| **AutoGen** | `autogen_basic.py` | Conversation protection, agent coordination | Research teams, data analysis |
| **LlamaIndex** | `llamaindex_basic.py` | RAG protection, document indexing | Knowledge bases, Q&A systems |
| **Haystack** | `haystack_basic.py` | Search pipeline protection | Document search, retrieval |
| **Semantic Kernel** | `semantic_kernel_basic.py` | Kernel function protection | Task automation, AI orchestration |
| **LangGraph** | `langgraph_basic.py` | Graph workflow protection | Complex multi-step workflows |
| **Generic** | `generic_basic.py` | Any Python function protection | Data processing, analysis |
| **Comprehensive** | `adri_protected_decorator_example.py` | All decorator features | Learning ADRI capabilities |

## Expected Output

When you run the examples, you'll see:

**Good Data (Protection Allows):**
```
🛡️ ADRI Protection: ALLOWED ✅
📊 Quality Score: 94.2/100 (Required: 80.0/100)
📋 Standard: your_function_data v1.0.0 (NEW)
```

**Bad Data (Protection Blocks):**
```
🛡️ ADRI Protection: BLOCKED ❌
❌ Data quality too low for reliable agent execution
📊 Quality Assessment: 67.3/100 (Required: 80.0/100)

🔧 Fix This Now:
   1. adri export-report --latest
   2. adri show-standard your_function_data
   3. adri assess <fixed-data> --standard your_function_data
```

## Next Steps

After running the examples:

1. **Try with your own data**: Replace the sample data with your real data
2. **Customize protection**: Adjust `min_score` and other parameters
3. **Add to your agents**: Copy the decorator pattern to your agent functions
4. **Explore CLI tools**: Use `adri list-standards`, `adri list-assessments`, etc.

## Need Help?

- **Configuration**: See [../docs/configuration.md](../docs/configuration.md)
- **Custom Rules**: See [../docs/custom-rules.md](../docs/custom-rules.md)
- **CLI Tools**: Run `adri --help` for available commands

---

**One line. Any framework. Reliable agents.**
