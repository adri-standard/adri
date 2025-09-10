# ADRI - Stop AI Agents Breaking on Bad Data

🛡️ **Based on analysis of 1,998+ documented GitHub issues across AI frameworks**

**Prevents 80% of production agent failures with one decorator**

## 🚨 The Real Problem: Documented GitHub Issues Breaking Production Agents

**AutoGen** - 54+ validation issues causing collaboration failures:
- Issue #6819: "Conversational flow is not working as expected"
- Issue #5736: "Function Arguments as Pydantic Models fail in tool calls"
- Issue #6123: "Internal Message Handling corruption"

**LangChain** - 525+ validation issues breaking customer workflows:
- Chain input validation failures break customer service
- Memory context corruption loses conversation state
- Tool integration failures from malformed data

**CrewAI** - Multiple coordination issues stopping business automation:
- Crew coordination failures from malformed task data
- Agent role mismatches break collaborative workflows

## ✨ The Solution: One Decorator Prevents Real GitHub Issues

```python
# Without ADRI - Your agents break on documented GitHub issues
def research_collaboration(data):
    return autogen_conversation(data)  # 💥 Issue #6819: Flow breaks

# With ADRI - GitHub issues prevented automatically
@adri_protected
def research_collaboration(data):
    return autogen_conversation(data)  # ✅ Issue #6819: Blocked before breaking
```

## 🚀 30-Second Setup - ADRI Works Completely Offline

**ADRI Core: Zero external dependencies, no API keys, works offline**
```python
from adri.decorators.guard import adri_protected

@adri_protected
def your_agent_function(data):
    # Your existing agent code - unchanged!
    # ADRI validates data quality completely offline
    return your_result
```

**Optional: Framework demos use AI services (your choice)**
```bash
python tools/adri-setup.py --framework autogen    # Framework demo dependencies
export OPENAI_API_KEY="your-key"                  # For framework demos only
python examples/autogen-research-collaboration.py  # See real GitHub issues prevented
```

**Note:** ADRI protection works with ANY data - framework demos just show specific GitHub issues

## 📋 Framework Examples - Real GitHub Issue Prevention

**Run any example to see ADRI prevent documented GitHub issues**

### 🤖 AutoGen → [`examples/autogen-research-collaboration.py`](examples/autogen-research-collaboration.py)
```python
@adri_protected
def start_conversation(conversation_data):
    # Prevents GitHub #6819: "Conversational flow breaks"
    # Prevents GitHub #5736: "Function Arguments fail"
    # Prevents GitHub #6123: "Message Handling corruption"
```
**Setup:** `python tools/adri-setup.py --framework autogen`

### 🦜 LangChain → [`examples/langchain-customer-service.py`](examples/langchain-customer-service.py)
```python
@adri_protected
def process_customer_query(customer_data):
    # Prevents chain input validation failures
    # Prevents memory context corruption
    # Prevents tool integration breakdowns
```
**Setup:** `python tools/adri-setup.py --framework langchain`

### 🤝 CrewAI → [`examples/crewai-business-analysis.py`](examples/crewai-business-analysis.py)
```python
@adri_protected
def coordinate_market_crew(crew_data):
    # Prevents crew coordination failures
    # Prevents agent role mismatches
    # Prevents task distribution errors
```
**Setup:** `python tools/adri-setup.py --framework crewai`

### 🦙 LlamaIndex → [`examples/llamaindex-document-processing.py`](examples/llamaindex-document-processing.py)
### 🌾 Haystack → [`examples/haystack-knowledge-management.py`](examples/haystack-knowledge-management.py)
### 🌐 LangGraph → [`examples/langgraph-workflow-automation.py`](examples/langgraph-workflow-automation.py)
### 🧠 Semantic Kernel → [`examples/semantic-kernel-ai-orchestration.py`](examples/semantic-kernel-ai-orchestration.py)

**New to AI agents?** → [`basic_example.py`](basic_example.py) - Generic Python function protection

## What You Get

✅ **Zero Configuration** - Works immediately with 15 built-in standards
✅ **Sub-millisecond Validation** - Intelligent caching for performance
✅ **Framework Agnostic** - Drop into any Python AI workflow
✅ **Offline First** - No external dependencies or network calls
✅ **Automatic Standards** - Generates data quality rules from your function names

## When ADRI Protects Your Agent

```bash
🛡️ ADRI Protection: ALLOWED ✅
📊 Quality Score: 94.2/100 (Required: 80.0/100)
📋 Standard: customer_data_standard v1.0.0
```

## When ADRI Blocks Bad Data

```bash
🛡️ ADRI Protection: BLOCKED ❌
❌ Data quality too low for reliable agent execution
📊 Quality Assessment: 67.3/100 (Required: 80.0/100)

🔧 Fix This:
   adri show-standard customer_data_standard
   adri assess <your-data> --standard customer_data_standard
```

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

## CLI Tools

```bash
# List available standards
adri list-standards

# Assess your data quality
adri assess data.csv

# Generate custom standards
adri generate-standard --input data.csv --output my_standard.yaml

# Profile your data
adri profile data.csv
```

## Built-in Standards

ADRI includes 15 production-ready standards:

- **Customer Data** - Profiles, service records, analytics
- **Financial Data** - Risk analysis, transactions, compliance
- **Agent Communication** - Multi-agent conversation data
- **RAG Documents** - Knowledge base and retrieval data
- **Time Series** - Analytics and forecasting data

[View all standards →](adri-validator/adri/standards/bundled/)

## Installation

```bash
# Basic installation
pip install adri

# With development tools
pip install adri[dev]

# From source
git clone https://github.com/adri-standard/adri
cd adri && pip install -e .
```

## Examples Repository

Complete working examples for every major AI framework:

- **[LangChain Integration](https://adri-standard.github.io/adri/frameworks#langchain)** - Chains, prompts, conversations
- **[CrewAI Integration](https://adri-standard.github.io/adri/frameworks#crewai)** - Multi-agent crews and tasks
- **[AutoGen Integration](https://adri-standard.github.io/adri/frameworks#autogen)** - Agent conversations and coordination
- **[LlamaIndex Integration](https://adri-standard.github.io/adri/frameworks#llamaindex)** - RAG queries and document processing
- **[Haystack Integration](https://adri-standard.github.io/adri/frameworks#haystack)** - Search pipelines and retrievers
- **[LangGraph Integration](https://adri-standard.github.io/adri/frameworks#langgraph)** - Graph workflows and state management
- **[Semantic Kernel Integration](https://adri-standard.github.io/adri/frameworks#semantic-kernel)** - Kernel functions and AI services

## Documentation

### 👤 For Users
- **[AI Engineer Onboarding](https://adri-standard.github.io/adri/ai-engineer-onboarding)** - Complete 60-minute journey from production failures to bulletproof agents
- **[Quick Start Guide](https://adri-standard.github.io/adri/quick-start)** - Get running in 5 minutes
- **[Framework Integration Guide](https://adri-standard.github.io/adri/frameworks)** - Copy-paste ready code for all major frameworks
- **[API Reference](https://adri-standard.github.io/adri/API_REFERENCE)** - Complete decorator and CLI documentation

### 🔧 For Contributors
- **[Architecture Guide](https://adri-standard.github.io/adri/CONTRIBUTOR_DOCS/STANDALONE_ARCHITECTURE)** - Create custom standards and understand internals
- **[Performance Testing](https://adri-standard.github.io/adri/CONTRIBUTOR_DOCS/PERFORMANCE_TESTING)** - Benchmarking and optimization guidelines
- **[Deployment Guide](https://adri-standard.github.io/adri/CONTRIBUTOR_DOCS/DEPLOYMENT_GUIDE)** - Production deployment best practices
- **[PyPI Management](https://adri-standard.github.io/adri/CONTRIBUTOR_DOCS/PYPI_FIRST_VERSION_MANAGEMENT)** - Release and version management

## Support

- **GitHub Issues** - [Report bugs and request features](https://github.com/adri-standard/adri/issues)
- **GitHub Discussions** - [Community support and questions](https://github.com/adri-standard/adri/discussions)
- **Documentation** - [Complete guides and API reference](https://github.com/adri-standard/adri/blob/main/README.md)

## License

MIT License - Use freely in any project. See [LICENSE](LICENSE) for details.

---

## Enterprise Data Governance

For organizations needing centralized data governance across multiple AI systems, [Verodat Enterprise](https://verodat.com/adri-enterprise) provides additional capabilities including centralized audit logging, policy management, and cross-system data quality monitoring.

ADRI works perfectly as a standalone open source tool. Enterprise features are completely optional and don't affect core functionality.
