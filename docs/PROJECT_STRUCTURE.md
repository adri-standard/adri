# ADRI Project Structure

This document outlines the directory structure and organization of the Agent Data Readiness Index (ADRI) project.

## Directory Structure Overview

```
agent-data-readiness-index/
├── adri/                     # Main Python package
│   ├── __init__.py
│   ├── assessor.py           # Core assessment logic
│   ├── cli.py                # Command-line interface
│   ├── interactive.py        # Interactive CLI mode
│   ├── report.py             # Report generation
│   ├── connectors/           # Data source connectors
│   ├── dimensions/           # Assessment dimensions
│   ├── integrations/         # Framework integrations
│   ├── templates/            # Report templates
│   └── utils/                # Utility functions
├── config/                   # Configuration files
│   ├── site_config.yml       # Site configuration
│   └── mkdocs.yml            # Documentation configuration
├── datasets/                 # Dataset assessments and catalog
│   ├── catalog/              # Dataset catalog data
│   ├── financial/            # Financial datasets
│   ├── healthcare/           # Healthcare datasets
│   └── ...                   # Other domain-specific datasets
├── docs/                     # Documentation
│   ├── assets/               # Documentation assets
│   ├── datasets/             # Dataset documentation
│   ├── integrations/         # Framework integration docs
│   ├── PROJECT_STRUCTURE.md  # This file
│   ├── TESTING.md            # Testing documentation
│   └── ...                   # Other documentation files
├── examples/                 # Example code
│   ├── quickstart/           # Quick start examples
│   ├── langchain/            # LangChain integration examples
│   ├── dspy/                 # DSPy integration examples
│   ├── crewai/               # CrewAI integration examples
│   └── ...                   # Other examples
├── tests/                    # Test code
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   ├── infrastructure/       # Infrastructure tests
│   └── data/                 # Test data
├── web/                      # Web assets
│   ├── css/                  # CSS files
│   └── js/                   # JavaScript files
├── scripts/                  # Utility scripts
├── .github/                  # GitHub-specific files
│   └── workflows/            # GitHub Actions workflows
└── [root files]              # README.md, LICENSE, etc.
```

## Key Components

### Main Package (`adri/`)

The `adri` directory contains the core Python package implementing the Agent Data Readiness Index functionality:

- **Connectors**: Interfaces for different data sources
- **Dimensions**: Implementations of assessment dimensions
- **Integrations**: Framework-specific integrations (LangChain, DSPy, CrewAI)
- **Templates**: HTML and other templates for report generation
- **Utils**: Shared utility functions

### Configuration (`config/`)

The `config` directory contains centralized configuration files:

- **site_config.yml**: Configuration for the documentation site, including URL settings
- **mkdocs.yml**: MkDocs configuration for documentation generation

### Datasets (`datasets/`)

The `datasets` directory contains assessments of public datasets:

- **catalog/**: The central catalog of dataset assessments
- **[domain]/**: Domain-specific datasets organized by field (financial, healthcare, etc.)
- Each dataset includes metadata, assessment results, and documentation

### Documentation (`docs/`)

The `docs` directory contains all project documentation:

- **datasets/**: Documentation specific to assessed datasets
- **integrations/**: Documentation for framework integrations
- **TESTING.md**: Comprehensive testing approach
- Other methodology and usage documentation

### Examples (`examples/`)

The `examples` directory contains example code organized by framework:

- **quickstart/**: Framework-agnostic quick start examples
- **langchain/**: LangChain-specific examples
- **dspy/**: DSPy-specific examples
- **crewai/**: CrewAI-specific examples

This organization makes it easy to find examples for a specific framework.

### Tests (`tests/`)

The `tests` directory contains all test code:

- **unit/**: Unit tests for individual components
- **integration/**: Tests for component interactions
- **infrastructure/**: Tests for build and deployment processes
- **data/**: Test datasets and fixtures

### Web Assets (`web/`)

The `web` directory contains static web assets:

- **css/**: CSS stylesheets
- **js/**: JavaScript files

## Framework Integration Visibility

ADRI provides first-class support for multiple AI agent frameworks. This is reflected in the directory structure:

1. **Framework-specific integration code**: `adri/integrations/{framework}/`
2. **Framework-specific examples**: `examples/{framework}/`
3. **Framework-specific documentation**: `docs/integrations/{framework}.md`

This consistent organization makes it easy to find all resources related to a specific framework.

## Dataset Organization

Public datasets assessed with ADRI are organized by domain in the `datasets/` directory:

1. **Catalog data**: `datasets/catalog/` contains the central registry
2. **Domain-specific directories**: `datasets/{domain}/` organized by field
3. **Individual dataset directories**: `datasets/{domain}/{dataset}/` containing:
   - `metadata.yaml`: Dataset metadata
   - `report.json`: Assessment results
   - `README.md`: Dataset-specific documentation

## Configuration Centralization

Configuration files are centralized in the `config/` directory to:

1. Provide a single location for all configuration
2. Standardize configuration access patterns
3. Simplify deployment and CI/CD processes

## Testing Organization

The testing structure follows the Python standard with:

1. **Unit tests**: Following the same structure as the main package
2. **Integration tests**: Organized by interaction patterns
3. **Infrastructure tests**: Testing deployment and configuration

## File Naming Conventions

1. **Python files**: Snake case (`file_name.py`)
2. **Documentation files**: Upper case with underscores (`FILE_NAME.md`)
3. **Configuration files**: Lower case with underscores (`file_name.yml`)
4. **Test files**: Prefixed with `test_` (`test_module.py`)

## Maintenance Guidelines

When adding new files:

1. Follow the established directory structure
2. Use consistent naming conventions
3. Update documentation if the structure changes
4. Add appropriate tests in the `tests/` directory
