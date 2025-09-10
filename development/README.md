# ADRI Development Directory

This directory contains all development tools, documentation, and infrastructure needed for contributing to ADRI. It is organized to hide complexity from AI engineers who just want to use ADRI for data protection.

## Directory Structure

### 🧪 testing/
Complete test suite for ADRI functionality
- **unit/**: Unit tests for individual components
- **integration/**: End-to-end workflow tests
- **performance/**: Stress testing and benchmarks
- **enterprise/**: Enterprise feature tests
- **fixtures/**: Test data and mock objects

### 🔧 tools/
Development and build tools
- **core/**: Core build utilities and scripts
- **release/**: Release management and PyPI publishing
- **testing/**: Test automation and validation

### 📚 docs/
Contributor documentation
- Development workflow guides
- Issue-driven development process
- PyPI version management
- Quick contribution guide

### ⚙️ config/
Development configuration files
- `.flake8`: Python code quality settings
- `.commitlintrc.json`: Commit message standards
- `.pre-commit-config.yaml`: Pre-commit hook configuration

### 📋 templates/
Release note templates and documentation templates

### 📦 catalogue/
Open source standard catalogues and examples

### 🤖 ai-docs/
AI development documentation and implementation plans

### 📊 logs/
Development logs and output files

### 🎯 reference_examples/
Original example implementations (moved from root for simplicity)

## Getting Started for Contributors

1. **Quick Setup**: Run `development/tools/core/setup-dev-environment.sh`
2. **Run Tests**: `cd development/testing && python -m pytest`
3. **Check Code Quality**: `development/tools/core/check_code_quality.py`
4. **Read Docs**: Start with `development/docs/QUICK_CONTRIBUTION_GUIDE.md`

## For AI Engineers (Simple Usage)

If you're an AI engineer who just wants to protect your agent workflows, you don't need this directory. Everything you need is in the root:

- Framework examples: `langchain_example.py`, `crewai_example.py`, etc.
- Quick start guide: `QUICK_START.md`
- Basic example: `basic_example.py`

## Contributing

This directory maintains all the professional tooling and processes needed for:
- Code quality assurance
- Automated testing
- Release management
- Documentation generation
- Performance monitoring

All development complexity is contained here to keep the root directory clean and approachable for new users.
