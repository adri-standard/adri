---
sidebar_position: 1
slug: /
---

# ADRI - Agent Data Reliability Intelligence

**Stop AI agents from breaking on bad data**

ADRI is an open-source data quality validation framework designed specifically for AI agents. One decorator protects your agent functions from unreliable data across all major frameworks.

## Quick Start

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

## Documentation

📖 **[FAQ](faq)** - Complete guide covering everything you need to know
🚀 **[Getting Started](getting-started)** - Step-by-step setup and usage
🤖 **[Framework Examples](frameworks)** - Copy-paste code for LangChain, CrewAI, AutoGen, etc.
📋 **[API Reference](API_REFERENCE)** - Technical reference

## Key Features

- **🛡️ One-Decorator Protection** - Add `@adri_protected` to any function
- **🤖 Framework Agnostic** - Works with LangChain, CrewAI, AutoGen, LlamaIndex, etc.
- **🚀 Zero Configuration** - Smart defaults, customize when needed
- **📊 5-Dimension Validation** - Completeness, validity, consistency, plausibility, freshness
- **📋 Flexible Modes** - Fail-fast, selective blocking, or warn-only
- **⚡ Enterprise Ready** - Production-tested with optional enterprise features

## Framework Support

ADRI works seamlessly with all major AI frameworks:
- **LangChain** - Protect chains and agents
- **CrewAI** - Validate crew inputs
- **AutoGen** - Secure multi-agent conversations
- **LlamaIndex** - Guard query engines
- **Any Python Function** - Universal protection

## Community

- **[GitHub Repository](https://github.com/adri-standard/adri)** - Source code and issues
- **[Contributing Guide](https://github.com/adri-standard/adri/blob/main/CONTRIBUTING.md)** - Help improve ADRI
- **[GitHub Discussions](https://github.com/adri-standard/adri/discussions)** - Ask questions and share ideas

---

**Ready to get started?** Check out the [FAQ](faq) for comprehensive information or jump into [Getting Started](getting-started) for hands-on examples.
