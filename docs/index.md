---
layout: default
title: ADRI - Agent Data Reliability Intelligence
---

# ADRI - Agent Data Reliability Intelligence

**Stop AI Agents Breaking on Bad Data**

ADRI is an open-source data quality validation framework designed specifically for AI agents. One decorator protects your agent functions from unreliable data across all major frameworks.

## Quick Start

```python
from adri import adri_protected

@adri_protected
def my_agent_function(data):
    # Your agent logic here
    return processed_data
```

**New to ADRI?** → [**AI Engineer Onboarding Guide**](ai-engineer-onboarding) - Complete 60-minute journey from production failures to bulletproof agents.

## Framework Support

ADRI works seamlessly with:
- **LangChain** - Protect chains and agents
- **CrewAI** - Validate crew inputs
- **AutoGen** - Secure multi-agent conversations
- **LlamaIndex** - Guard query engines
- **Haystack** - Protect pipelines
- **LangGraph** - Validate graph nodes
- **Semantic Kernel** - Secure kernel functions

## Installation

```bash
pip install adri
```

## Key Features

- **One-decorator protection** - Add `@adri_protected` to any function
- **Framework agnostic** - Works with all major AI frameworks
- **Zero configuration** - Smart defaults, customize when needed
- **Comprehensive validation** - Completeness, validity, consistency, plausibility, freshness
- **Detailed reporting** - JSON logs and HTML reports
- **Enterprise ready** - Production-tested validation logic

## Documentation

### 👤 For Users
- [AI Engineer Onboarding](ai-engineer-onboarding) - Complete 60-minute journey from production failures to bulletproof agents
- [Quick Start Guide](quick-start) - Get running in 5 minutes
- [Framework Integration](frameworks) - Copy-paste ready code for all major frameworks
- [API Reference](API_REFERENCE) - Complete decorator and CLI documentation

### 🔧 For Contributors
- [Architecture Guide](CONTRIBUTOR_DOCS/STANDALONE_ARCHITECTURE) - Create custom standards and understand internals
- [Performance Testing](CONTRIBUTOR_DOCS/PERFORMANCE_TESTING) - Benchmarking and optimization guidelines
- [Deployment Guide](CONTRIBUTOR_DOCS/DEPLOYMENT_GUIDE) - Production deployment best practices
- [PyPI Management](CONTRIBUTOR_DOCS/PYPI_FIRST_VERSION_MANAGEMENT) - Release and version management

## Community

- [GitHub Issues](https://github.com/adri-standard/adri/issues) - Report bugs or request features
- [Discussions](https://github.com/adri-standard/adri/discussions) - Ask questions and share ideas

---

Ready to protect your AI agents? [Get started →](quick-start)
