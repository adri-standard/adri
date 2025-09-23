---
sidebar_position: 1
slug: /
---

# ADRI Documentation

**Agent Data Reliability Intelligence – Stop AI agents from breaking on bad data**

ADRI is an open-source data quality validation framework built for AI agents. Generate a standard from good data once, wrap your functions with `@adri_protected`, and block dirty payloads before they crash your agents.

## ADRI in your stack

ADRI is a data quality gate for agent workflows. It complements related standards you may already use:

- ADRI: Validate inputs and enforce a quality contract before tools/actions run (fail-fast, warn, or continue).
- MCP: Agent-to-tool connectivity (standard way to connect agents to tools, APIs, and resources). See https://modelcontextprotocol.io/
- A2A: Agent-to-agent interoperability (standard messaging between agents across frameworks/vendors). See https://a2a-protocol.org/latest/

Use ADRI with or without MCP/A2A — the goal is to stop bad data from breaking agents right at the boundary.


## Choose Your Path

### 🚀 **Put ADRI to Work**
*Package consumer documentation – ship reliable agents fast*

```bash
pip install adri
adri setup --guide
adri generate-standard examples/data/invoice_data.csv \
  --output examples/standards/invoice_data_ADRI_standard.yaml
adri assess examples/data/test_invoice_data.csv \
  --standard examples/standards/invoice_data_ADRI_standard.yaml
```

```python
from adri import adri_protected

@adri_protected(standard="invoice_data_standard", data_param="invoice_rows")
def your_agent_function(invoice_rows):
    return agent_pipeline(invoice_rows)
```

**📚 User Documentation:**
- **[Getting Started](users/getting-started)** – Installation, walkthrough, and first success
- **[FAQ](users/faq)** – Answers for agent engineers, data teams, and compliance
- **[Framework Playbooks](users/frameworks)** – LangChain, CrewAI, LlamaIndex, LangGraph, Semantic Kernel
- **[Adoption Journey](users/adoption-journey)** – When to switch on Verodat-managed data supply
- **[API Reference](users/API_REFERENCE)** – Complete decorator, CLI, and configuration details
- **[Why Open Source](users/WHY_OPEN_SOURCE)** – Strategy and licensing

### 🛠️ **Contribute to ADRI Community**
*Developer documentation – improve ADRI itself*

**🔧 Contributor Documentation:**
- **[Development Workflow](contributors/development-workflow)** – Local testing and CI setup
- **[Framework Extension Pattern](contributors/framework-extension-pattern)** – Adding new framework support
- **[Code Style Guide](https://github.com/adri-standard/adri/blob/main/CONTRIBUTING.md)** – Contribution guidelines
- **[GitHub Repository](https://github.com/adri-standard/adri)** – Source code and issues

## Key Features

- **🛡️ One-Decorator Protection** – Add `@adri_protected` to any function
- **🤖 Framework Agnostic** – Works with LangChain, CrewAI, AutoGen, LlamaIndex, etc.
- **🚀 Smart Defaults** – Zero-config start with optional tuning
- **📊 Five Dimensions** – Validity, completeness, consistency, plausibility, freshness
- **📋 Flexible Modes** – Fail-fast, warn, or continue for selective flows
- **⚡ Enterprise Ready** – Local-first with a clear path to Verodat MCP

---

**Ready to start?** Hit the getting started guide, then follow the adoption journey when you need shared compliance logging and managed data supply.
