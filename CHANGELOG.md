# Changelog

All notable changes to ADRI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.0.0] - 2025-10-17

**ADRI v5.0.0 - The missing data layer for AI agents**

Initial release of the open-source ADRI framework. Protect your AI agents from bad data with a single decorator.

### Features

**Core Protection**
- `@adri_protected` decorator for automatic data quality validation
- Five-dimension quality assessment (validity, completeness, consistency, accuracy, timeliness)
- Auto-generation of quality standards from your data
- Configurable protection modes: `raise`, `warn`, or `continue`
- Environment-based standard management (dev/prod separation)

**Framework Integration**
- Works with any Python function or AI framework
- Native support for LangChain, CrewAI, AutoGen, LlamaIndex, Haystack, Semantic Kernel
- Zero configuration required - add decorator and go

**CLI Tools**
- `adri setup` - Initialize ADRI in your project with guided setup
- `adri generate-standard` - Create quality standards from your data
- `adri assess` - Validate data quality against standards
- `adri list-standards` - View available quality standards
- `adri validate-standard` - Verify standard file correctness

**Developer Experience**
- 2-minute integration time
- Local logging for debugging and development
- YAML-based standards for transparency and version control
- Comprehensive documentation and examples
- Intelligent CI with docs-only detection

**Advanced Capabilities**
- AI/LLM reasoning mode validation
- Workflow orchestration metadata tracking
- Data provenance tracking
- Assessment result callbacks for custom workflows
- Dimension-specific quality thresholds

### Getting Started

```python
from adri import adri_protected

@adri_protected(standard="customer_data", data_param="data")
def process_customers(data):
    # Your agent logic here - now protected!
    return results
```

First run with good data → ADRI generates quality standard  
Future runs → ADRI validates against that standard  
Bad data → Blocked with detailed quality report

### Documentation

Complete documentation available in the repository:
- **QUICKSTART.md** - 2-minute integration guide
- **docs/GETTING_STARTED.md** - 10-minute detailed tutorial
- **docs/HOW_IT_WORKS.md** - Five quality dimensions explained
- **docs/FRAMEWORK_PATTERNS.md** - Framework-specific integration patterns
- **docs/CLI_REFERENCE.md** - Complete CLI command reference
- **docs/API_REFERENCE.md** - Full programmatic API documentation
- **docs/FAQ.md** - Common questions and answers
- **docs/ARCHITECTURE.md** - Technical architecture details

### Requirements

- Python 3.10+
- Works on Linux, macOS, and Windows

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute to ADRI.

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.
