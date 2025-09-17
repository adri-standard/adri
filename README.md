# ADRI - Stop AI Agents Breaking on Bad Data

**Prevent AI agent failures with one decorator**

## 30-Second Setup

```bash
pip install adri
```

```python
from adri import adri_protected

@adri_protected(standard="customer_data")
def your_agent_function(data):
    # Your existing code - now protected!
    return result
```

**ADRI automatically creates standards from your data patterns and protects your agents from bad data.**

## Key Features

- **🛡️ One-Decorator Protection** - Add `@adri_protected` to any function
- **🤖 Framework Agnostic** - Works with LangChain, CrewAI, AutoGen, LlamaIndex, etc.
- **🚀 Zero Configuration** - Smart defaults, customize when needed
- **📊 5-Dimension Validation** - Completeness, validity, consistency, plausibility, freshness
- **📋 Detailed Reporting** - JSON logs and actionable error messages
- **⚡ Enterprise Ready** - Production-tested with optional enterprise features

## Quick Example

```bash
# Test data quality
adri assess customer_data.csv

# Protect any agent function
@adri_protected(standard="customer_data")
def process_customers(data):
    return ai_analysis(data)  # Only runs on quality data
```

## Documentation

📖 **[FAQ](FAQ.md)** - Complete guide covering everything you need to know  
🏗️ **[Architecture](ARCHITECTURE.md)** - How ADRI works  
📋 **[Examples](examples/)** - Ready-to-run use cases and standards  
🤝 **[Contributing](CONTRIBUTING.md)** - Join the community

## Framework Support

ADRI works seamlessly with all major AI frameworks:
- **LangChain** - Protect chains and agents
- **CrewAI** - Validate crew inputs  
- **AutoGen** - Secure multi-agent conversations
- **LlamaIndex** - Guard query engines
- **Any Python Function** - Universal protection

See [docs/frameworks.md](docs/frameworks.md) for copy-paste examples.

## Support

- **[GitHub Issues](https://github.com/adri-standard/adri/issues)** - Report bugs and request features
- **[GitHub Discussions](https://github.com/adri-standard/adri/discussions)** - Community support

---

## ADRI Enterprise

The open-source edition of ADRI is complete and free for all users.

For organizations that need advanced compliance logging, managed data supply, and enterprise support, see [ADRI Enterprise](https://verodat.com/adri-enterprise/).

---

**MIT License** - Use freely in any project. See [LICENSE](LICENSE) for details.
