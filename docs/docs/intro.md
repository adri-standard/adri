---
sidebar_position: 1
slug: /
---

# ADRI Documentation

**Agent Data Reliability Intelligence - Stop AI agents from breaking on bad data**

ADRI is an open-source data quality validation framework designed specifically for AI agents. One decorator protects your agent functions from unreliable data across all major frameworks.

## Choose Your Path

### 🚀 **Put ADRI to Work**
*Package consumer documentation - Get started with ADRI*

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

**📚 User Documentation:**
- **[Getting Started](users/getting-started)** - Installation and first steps
- **[FAQ](users/faq)** - Complete guide covering everything you need
- **[Framework Examples](users/frameworks)** - LangChain, CrewAI, AutoGen integration
- **[API Reference](users/API_REFERENCE)** - Complete technical reference
- **[Why Open Source](users/WHY_OPEN_SOURCE)** - Our open source philosophy

### 🛠️ **Contribute to ADRI Community**
*Developer documentation - Help improve ADRI*

**🔧 Contributor Documentation:**
- **[Development Workflow](contributors/development-workflow)** - Local testing and CI setup
- **[Framework Extension Pattern](contributors/framework-extension-pattern)** - Adding new framework support
- **[Code Style Guide](https://github.com/adri-standard/adri/blob/main/CONTRIBUTING.md)** - Contribution guidelines
- **[GitHub Repository](https://github.com/adri-standard/adri)** - Source code and issues

## Key Features

- **🛡️ One-Decorator Protection** - Add `@adri_protected` to any function
- **🤖 Framework Agnostic** - Works with LangChain, CrewAI, AutoGen, LlamaIndex, etc.
- **🚀 Zero Configuration** - Smart defaults, customize when needed
- **📊 5-Dimension Validation** - Completeness, validity, consistency, plausibility, freshness
- **📋 Flexible Modes** - Fail-fast, selective blocking, or warn-only
- **⚡ Enterprise Ready** - Production-tested with optional enterprise features

---

**Ready to start?** Choose your path above - whether you want to **use ADRI** or **contribute to ADRI**.
