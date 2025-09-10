# ADRI - Stop AI Agents Breaking on Bad Data

🛡️ **One decorator. Any framework. Reliable agents.**

Works with **LangChain**, **CrewAI**, **AutoGen**, **LlamaIndex**, **Haystack**, **LangGraph**, **Semantic Kernel**

## The Problem

Your AI agents work perfectly in testing, then break in production when they get bad data.

```python
# Without ADRI - Agent breaks randomly
def analyze_customer(data):
    return risky_analysis(data)  # 💥 Bad data = broken agent
```

```python
# With ADRI - Agent protected automatically
@adri_protected
def analyze_customer(data):
    return risky_analysis(data)  # ✅ Bad data blocked automatically
```

## 30-Second Quick Start

```bash
pip install adri
```

```python
from adri.decorators.guard import adri_protected

@adri_protected
def your_agent_function(data):
    # Your existing agent code - unchanged!
    return your_result
```

**That's it.** Your agent is now protected from bad data.

**New to ADRI?** → [**Complete AI Engineer Onboarding Guide**](https://adri-standard.github.io/adri/ai-engineer-onboarding) - From production failures to bulletproof agents in 60 minutes.

## Framework Examples

### LangChain
```python
@adri_protected
def langchain_customer_service(customer_data):
    chain = prompt | model | parser
    return chain.invoke(customer_data)
```

### CrewAI
```python
@adri_protected
def crewai_market_analysis(market_data):
    crew = Crew(agents=[analyst, researcher])
    return crew.kickoff(inputs=market_data)
```

### AutoGen
```python
@adri_protected
def autogen_research_team(research_data):
    assistant.initiate_chat(user_proxy, message=research_data)
    return conversation_result
```

### LlamaIndex
```python
@adri_protected
def llamaindex_rag_query(query_data):
    engine = index.as_query_engine()
    return engine.query(query_data)
```

**Need more examples?** Check our [complete framework guide](https://adri-standard.github.io/adri/frameworks) with copy-paste ready code.

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
