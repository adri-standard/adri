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
│   ├── version.py            # Version management
│   ├── config/               # Configuration management
│   ├── connectors/           # Data source connectors
│   ├── dimensions/           # Assessment dimensions
│   ├── integrations/         # Framework integrations
│   ├── rules/                # Validation rules
│   ├── templates/            # Report templates
│   └── utils/                # Utility functions
├── config/                   # Configuration files
│   ├── mkdocs.yml            # Documentation configuration
│   └── site_config.yml       # Site configuration
├── docs/                     # Documentation
│   ├── ai_dev_manager/       # AI development management docs
│   ├── data/                 # Documentation data
│   ├── internal/             # Internal development docs
│   ├── test_coverage/        # Test coverage reports
│   ├── API_REFERENCE.md      # API documentation
│   ├── DOCUMENTATION_ALIGNMENT.md
│   ├── GET_STARTED.md        # Getting started guide
│   ├── IMPLEMENTING_GUARDS.md # Guard implementation guide
│   ├── PROJECT_STRUCTURE.md  # This file
│   ├── TESTING.md            # Testing documentation
│   ├── VISION.md             # Project vision
│   └── ...                   # Other documentation files
├── examples/                 # Example code
│   ├── basic_assessment.py   # Basic usage example
│   ├── completeness_files/   # Completeness dimension examples
│   ├── consistency_files/    # Consistency dimension examples
│   ├── crewai/               # CrewAI integration examples
│   ├── dspy/                 # DSPy integration examples
│   ├── freshness_files/      # Freshness dimension examples
│   ├── guard/                # Guard implementation examples
│   ├── interactive/          # Interactive mode examples
│   ├── langchain/            # LangChain integration examples
│   ├── plausibility/         # Plausibility dimension examples
│   └── plausibility_files/   # Plausibility output examples
├── notebooks/                # Jupyter notebooks
│   ├── 01_adri_guard_tutorial.ipynb
│   └── 02_langchain_integration_tutorial.ipynb
├── scripts/                  # Utility scripts
│   ├── publish_pypi.sh       # PyPI publishing script
│   ├── run_financial_market_assessment.py
│   └── verify_version.py     # Version verification
├── tests/                    # All test code and resources
│   ├── conftest.py           # Test configuration
│   ├── data/                 # Test data
│   ├── datasets/             # Test datasets (CSV files, etc.)
│   ├── infrastructure/       # Infrastructure tests
│   ├── integration/          # Integration tests
│   ├── plans/                # Test planning documents
│   ├── results/              # Test execution results
│   └── unit/                 # Unit tests
├── web/                      # Web assets
│   ├── index.html            # Landing page
│   ├── css/                  # CSS files
│   └── js/                   # JavaScript files
├── .github/                  # GitHub-specific files
│   └── workflows/            # GitHub Actions workflows
├── .gitignore                # Git ignore rules
├── CHANGELOG.md              # Version changelog
├── CODE_OF_CONDUCT.md        # Code of conduct
├── CONTRIBUTING.md           # Contribution guidelines
├── LICENSE                   # MIT License
├── MANIFEST.in               # Package manifest
├── mypy.ini                  # MyPy configuration
├── pyproject.toml            # Python project configuration
├── README.md                 # Project readme
├── RELEASING.md              # Release process documentation
└── VERSIONS.md               # Version history
```

## Key Components

### Main Package (`adri/`)

The `adri` directory contains the core Python package implementing the Agent Data Readiness Index functionality:

- **config/**: Configuration management and defaults
- **connectors/**: Interfaces for different data sources (file, database, API)
- **dimensions/**: Implementations of the 5 assessment dimensions
- **integrations/**: Framework-specific integrations (LangChain, DSPy, CrewAI)
- **rules/**: Validation rules for each dimension
- **templates/**: HTML and other templates for report generation
- **utils/**: Shared utility functions

### Configuration (`config/`)

The `config` directory contains centralized configuration files:

- **mkdocs.yml**: MkDocs configuration for documentation generation
- **site_config.yml**: Configuration for the documentation site

### Documentation (`docs/`)

The `docs` directory contains all project documentation:

- **ai_dev_manager/**: AI-assisted development methodology
- **data/**: Documentation data files
- **internal/**: Internal development documentation
- **test_coverage/**: Detailed test coverage reports
- Methodology and usage documentation

### Examples (`examples/`)

The `examples` directory contains example code organized by use case:

- Basic assessment examples
- Dimension-specific examples with output files
- Framework integration examples (LangChain, DSPy, CrewAI)
- Guard implementation examples
- Interactive mode examples

### Tests (`tests/`)

The `tests` directory contains all test code and resources:

- **unit/**: Unit tests for individual components
- **integration/**: Tests for component interactions  
- **infrastructure/**: Tests for build and deployment processes
- **data/**: Test data and fixtures
- **datasets/**: Test dataset files (CSVs, etc.)
- **plans/**: Test planning and strategy documents
- **results/**: Test execution results and reports

### Web Assets (`web/`)

The `web` directory contains all static web assets:

- **index.html**: Community landing page
- **css/**: CSS stylesheets
- **js/**: JavaScript files (including simulator.js)

## Framework Integration Visibility

ADRI provides first-class support for multiple AI agent frameworks. This is reflected in the directory structure:

1. **Framework-specific integration code**: `adri/integrations/{framework}/`
2. **Framework-specific examples**: `examples/{framework}/`
3. **Framework-specific documentation**: `docs/INTEGRATIONS.md`

This consistent organization makes it easy to find all resources related to a specific framework.

## Testing Organization

The testing structure follows Python best practices:

1. **Unit tests**: Testing individual components in isolation
2. **Integration tests**: Testing component interactions
3. **Infrastructure tests**: Testing deployment and configuration
4. **Test resources**: Centralized under `tests/` directory

All test-related resources (datasets, plans, results) are now organized under the `tests/` directory for better maintainability.

## File Naming Conventions

1. **Python files**: Snake case (`file_name.py`)
2. **Documentation files**: Upper case with underscores (`FILE_NAME.md`)
3. **Configuration files**: Lower case with underscores (`file_name.yml`)
4. **Test files**: Prefixed with `test_` (`test_module.py`)

## Recent Changes (May 2025)

1. **Removed dataset catalog**: The public dataset catalog and benchmark functionality has been removed to focus on the core assessment framework
2. **Consolidated test resources**: All test-related directories moved under `tests/`
3. **Moved web assets**: Landing page moved to `web/` directory
4. **Cleaned build artifacts**: Removed old `src/` structure and related files

## Maintenance Guidelines

When adding new files:

1. Follow the established directory structure
2. Use consistent naming conventions
3. Update documentation if the structure changes
4. Add appropriate tests in the `tests/` directory
5. Keep the root directory clean - use subdirectories appropriately
