# ADRI Framework Examples

**30-Second Protection for Your AI Agent Workflows**

Production-ready examples demonstrating ADRI protection across major AI frameworks. Each example addresses documented validation issues that cause agent failures in production environments.

## Quick Start

```bash
pip install adri
```

Copy any example, add your data, and you're protected!

## Available Examples

| Framework | File | Use Case | Issues Prevented |
|-----------|------|----------|------------------|
| **LangChain** | `langchain-customer-service.py` | Customer Service | 525+ validation failures |
| **CrewAI** | `crewai-business-analysis.py` | Business Analysis | 124+ coordination failures |
| **AutoGen** | `autogen-research-collaboration.py` | Research Teams | 54+ conversation failures |
| **LlamaIndex** | `llamaindex-document-processing.py` | Document Processing | 949+ index failures |
| **Haystack** | `haystack-knowledge-management.py` | Knowledge Search | 347+ pipeline failures |
| **LangGraph** | `langgraph-workflow-automation.py` | Workflow Automation | 245+ state failures |
| **Semantic Kernel** | `semantic-kernel-ai-orchestration.py` | AI Orchestration | 178+ plugin failures |

## Universal Protection Pattern

All examples follow the same simple pattern:

```python
from adri import adri_protected

@adri_protected("framework_data_standard")
def your_ai_function(data):
    # Your framework code here - now protected!
    return result
```

## Why These Examples?

1. **Production-Ready** - Full working implementations, not just snippets
2. **Evidence-Based** - Each addresses real GitHub issues from framework communities
3. **Business-Focused** - Targets actual use cases where frameworks excel
4. **Comprehensive Protection** - Covers validity, completeness, consistency, freshness, and plausibility

## Get Started

1. Choose your framework example above
2. Run the example to see ADRI protection in action
3. Adapt the code for your specific use case
4. Your AI workflow is now protected!

For detailed setup instructions and troubleshooting, see the [ADRI Documentation](https://adri-standard.github.io/adri/).

---

**Ready to protect your AI workflows?** Choose your framework and get started in 30 seconds!
