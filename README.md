# ADRI - Agent Data Readiness Index

**AI Workflow Protection** - Reliable data quality protection for agent-driven business workflows.

🚀 **Production Ready** - Enterprise-grade data validation for AI systems.

## Overview

ADRI provides Python decorators and tools to protect AI agent workflows from data quality issues. With built-in standards and zero-configuration setup, ADRI ensures your agent functions receive reliable, high-quality data.

**Note**: This package contains proprietary validation algorithms and is distributed as a compiled package. The source code is intellectual property of ThinkEvolveSolve.

## Quick Start

```bash
pip install adri
```

```python
from adri.decorators.guard import adri_protected

@adri_protected(data_param="customer_data", min_score=80)
def process_customer_data(customer_data):
    # Your agent logic here - protected by ADRI
    return processed_results
```

## Features

- 🛡️ **Zero-Configuration Protection** - Works out of the box with 15 built-in standards
- ⚡ **High Performance** - Sub-millisecond validation with intelligent caching
- 🔧 **Framework Agnostic** - Works with any Python AI framework
- 📊 **Built-in Standards** - Customer data, financial data, and more
- 🎯 **Intelligent Matching** - Automatic standard selection based on function names
- 🚫 **Offline First** - No external dependencies or network calls

## Architecture

```
adri/
├── decorators/     # @adri_protected decorator
├── core/          # Protection engine and assessor
├── standards/     # Built-in YAML standards (15 included)
├── analysis/      # Data profiling and standard generation
├── config/        # Configuration management
├── cli/           # Command-line interface
└── utils/         # Utility functions
```

## Dependencies

- **pandas** - Data manipulation and analysis
- **numpy** - Numerical computations
- **pyyaml** - YAML processing
- **jsonschema** - Schema validation
- **click** - CLI interface
- **rich** - Beautiful terminal output

## Key Components

### Core Decorator
The `@adri_protected` decorator is the main interface for protecting agent functions:

```python
from adri.decorators.guard import adri_protected

@adri_protected(data_param="data", min_score=80)
def my_agent_function(data):
    # Agent logic here
    return processed_data
```

### Protection Engine
The `DataProtectionEngine` handles the core validation logic:
- Data quality assessment
- Standard loading and validation
- Failure mode handling
- Caching and performance optimization

### Analysis Tools
- **Data Profiler** - Analyzes data characteristics and quality
- **Standard Generator** - Auto-generates standards from sample data
- **Type Inference** - Determines data types and constraints

### Configuration Management
- Environment-specific configurations (dev/prod)
- Standard paths and caching settings
- Performance and timeout configurations

## Development Setup

```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

## Testing

The test suite includes:
- **Unit tests** - Individual component testing
- **Integration tests** - End-to-end workflow testing
- **Fixture data** - Sample datasets for testing
- **Performance tests** - Validation speed and memory usage

## Built-in Standards

ADRI includes 15 production-ready standards:

- **Customer Data Standards** - Customer profiles, service data, analytics
- **Financial Data Standards** - Risk analysis, transaction data
- **Agent Data Standards** - High-quality agent requirements
- **Development Standards** - Testing and development workflows

## Advanced Usage

### Custom Standards
```python
@adri_protected(
    data_param="data",
    standard_path="path/to/custom_standard.yaml",
    min_score=85
)
def my_function(data):
    return processed_data
```

### Configuration
```python
# Environment-specific settings
import os
os.environ['ADRI_DEFAULT_MIN_SCORE'] = '80'
os.environ['ADRI_CACHE_DURATION'] = '3600'
```

### CLI Tools
```bash
# Profile your data
adri-profile data.csv

# Generate custom standards
adri-generate --input data.csv --output my_standard.yaml

# Protect existing functions
adri-protect my_script.py
```

## Performance

- ⚡ **Sub-millisecond validation** with LRU caching
- 📈 **Scales to large datasets** with intelligent sampling
- 🔄 **Thread-safe** for concurrent applications
- 💾 **Memory efficient** with optimized data structures

## Support

- 📖 **Documentation** - [GitHub Wiki](https://github.com/ThinkEvolveSolve/adri-validator/wiki)
- 🐛 **Issues** - [GitHub Issues](https://github.com/ThinkEvolveSolve/adri-validator/issues)
- 💬 **Discussions** - [GitHub Discussions](https://github.com/ThinkEvolveSolve/adri-validator/discussions)

## Release Process

For maintainers releasing new versions:

```bash
# Prepare a new release
python scripts/prepare_release.py 0.1.1

# Push changes and create GitHub Release
git push origin main
# Then create release at: https://github.com/ThinkEvolveSolve/adri-validator/releases/new
```

See [RELEASE_PROCESS.md](RELEASE_PROCESS.md) for detailed release instructions.

## License

MIT License - see [LICENSE](LICENSE) for details.
